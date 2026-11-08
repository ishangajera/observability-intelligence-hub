#!/usr/bin/env python3
"""Discover emerging observability tools from ecosystem directories and launch signals.

Candidates are leads, not endorsements. First runs seed baselines; later runs
emit only new entries. Confirm every candidate against its primary source.
"""
import hashlib,json,os,re,urllib.parse,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data";NOW=datetime.now(timezone.utc)
STATE=OUT/"discovery_state.json";ARCHIVE=OUT/"updates.json"
def ident(s):return hashlib.sha256(s.encode()).hexdigest()[:20]
def fetch(url,accept="application/json"):
 headers={"User-Agent":"SignalDesk-Observability-Intelligence/1.0","Accept":accept}
 if os.getenv("GITHUB_TOKEN") and "api.github.com" in url:headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
 req=urllib.request.Request(url,headers=headers)
 with urllib.request.urlopen(req,timeout=35) as r:return r.read()
def clean(s):return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",str(s or ""))).strip()
state=json.loads(STATE.read_text()) if STATE.exists() else {"cncf":{},"github":{},"hn":{}}
first=not STATE.exists();events=[];archive=json.loads(ARCHIVE.read_text());items=archive.get("items",[])
def add(key,title,summary,url,project,source,date=None,extra=None):
 rec={"id":ident(key),"title":title,"summary":summary[:1100],"url":url,"date":date,
      "project":project,"source":source,"category":"Tool discovery","discovery_status":"candidate"}
 if extra:rec.update(extra)
 events.append(rec)
# 1. CNCF landscape: a maintained, machine-readable map of cloud-native projects/products.
try:
 import yaml
 raw=fetch("https://raw.githubusercontent.com/cncf/landscape/master/landscape.yml","text/plain").decode(errors="replace")
 doc=yaml.safe_load(raw) or {}
 current={}
 def walk(node):
  if isinstance(node,dict):
   if node.get("name") and (node.get("repo_url") or node.get("website_url")):
    name=str(node["name"]);url=str(node.get("repo_url") or node.get("website_url"))
    current[name.lower()]={"name":name,"url":url,"description":clean(node.get("description","")),
      "category":str(node.get("category","")),"subcategory":str(node.get("subcategory",""))}
   for v in node.values():walk(v)
  elif isinstance(node,list):
   for v in node:walk(v)
 walk(doc)
 old=state.get("cncf",{})
 if not first:
  for k,v in current.items():
   if k not in old:
    add("cncf:"+k,"New CNCF Landscape entry: "+v["name"],
      (v["description"] or "New project/product entry added to the CNCF Landscape.")+
      f" Landscape category: {v['category']} / {v['subcategory']}. Treat as a discovery lead; verify project maturity and observability relevance.",
      v["url"],"CNCF ecosystem","CNCF Landscape",NOW.isoformat(),{"landscape_category":v["category"],"landscape_subcategory":v["subcategory"]})
 state["cncf"]=current
 print("CNCF Landscape entries:",len(current),"new events:",len(events))
except Exception as e:print("CNCF Landscape discovery error:",str(e)[:180])
# 2. GitHub repository discovery across relevant topics. Only recent repositories,
# and newly surfaced repos, are candidates; topic search is not proof of a launch.
since=(NOW-timedelta(days=60)).date().isoformat()
queries=["topic:observability created:>="+since+" stars:>=2",
         "topic:opentelemetry created:>="+since+" stars:>=2",
         "topic:prometheus created:>="+since+" stars:>=2",
         "topic:monitoring created:>="+since+" stars:>=5",
         "topic:telemetry created:>="+since+" stars:>=2"]
known=state.setdefault("github",{})
for q in queries:
 try:
  url="https://api.github.com/search/repositories?"+urllib.parse.urlencode({"q":q,"sort":"updated","order":"desc","per_page":60})
  data=json.loads(fetch(url))
  for repo in data.get("items",[]):
   full=repo.get("full_name","").lower()
   if not full:continue
   record={"name":repo.get("name"),"full_name":repo.get("full_name"),"url":repo.get("html_url"),
     "description":clean(repo.get("description","")),"created_at":repo.get("created_at"),
     "pushed_at":repo.get("pushed_at"),"stars":repo.get("stargazers_count",0),
     "topics":repo.get("topics",[])}
   if full not in known and (not first or (record["created_at"] and datetime.fromisoformat(record["created_at"].replace("Z","+00:00"))>=NOW-timedelta(days=14))):
    add("github-discovery:"+full,"New observability project candidate: "+record["full_name"],
      f"{record['description']} Created {record['created_at']}; {record['stars']} GitHub stars. Discovered via repository topics/search. This is a candidate, not confirmation of a product launch.",
      record["url"],"Emerging observability tools","GitHub repository discovery",record["created_at"],
      {"repository":record["full_name"],"stars":record["stars"],"topics":record["topics"],"discovery_method":"GitHub topic search"})
   known[full]=record
 except Exception as e:print("GitHub discovery query error:",q,str(e)[:130])
print("GitHub discovery candidates tracked:",len(known))
# 3. Hacker News launch/announcement signals. Only newly observed stories over a
# modest engagement threshold are surfaced; source posts must be reviewed.
hn=state.setdefault("hn",{})
for term in ["observability","OpenTelemetry","Prometheus monitoring","Grafana plugin","metrics telemetry"]:
 try:
  url="https://hn.algolia.com/api/v1/search_by_date?"+urllib.parse.urlencode({"query":term,"tags":"story","numericFilters":"points>4","hitsPerPage":80})
  data=json.loads(fetch(url))
  for hit in data.get("hits",[]):
   oid=hit.get("objectID");title=clean(hit.get("title",""))
   if not oid or not title:continue
   old=hn.get(oid)
   if old is None and (not first or (hit.get("created_at_i") and int(hit["created_at_i"])>=int((NOW-timedelta(days=7)).timestamp()))):
    link=hit.get("url") or "https://news.ycombinator.com/item?id="+oid
    add("hn-discovery:"+oid,"Community launch signal: "+title,
      f"Hacker News discussion with {hit.get('points',0)} points and {hit.get('num_comments',0)} comments. Treat as a discovery lead; verify the product and its primary repository/site before adding it to the tracked ecosystem.",
      link,"Observability community","Hacker News / Algolia",hit.get("created_at"),
      {"hn_id":oid,"points":hit.get("points",0),"comments":hit.get("num_comments",0),"discovery_method":"Hacker News"})
   hn[oid]={"title":title,"points":hit.get("points",0),"url":hit.get("url")}
 except Exception as e:print("Hacker News discovery error:",term,str(e)[:130])
# 4. Product Hunt category is included as a launch radar. Its page is dynamic;
# retain a source record even if its HTML representation changes.
try:
 html=fetch("https://www.producthunt.com/categories/observability-tools?order=recent_launches","text/html").decode(errors="replace")
 names=set(re.findall(r'"name"\s*:\s*"([^"]{2,100})"[^{}]{0,500}?"url"\s*:\s*"(/posts/[^"]+)"',html))
 ph=state.setdefault("producthunt",{})
 for name,path in names:
  slug=path.rsplit("/",1)[-1];key=slug.lower()
  if key not in ph and not first:
   add("producthunt:"+key,"Product Hunt observability launch: "+clean(name),
     "New listing surfaced in Product Hunt's Observability Tools category. Validate launch date, product status, technical scope, and primary source before adding to the tracked project set.",
     "https://www.producthunt.com"+path,"Emerging observability tools","Product Hunt · Observability Tools",NOW.isoformat(),
     {"discovery_method":"Product Hunt"})
  ph[key]=clean(name)
 print("Product Hunt listings parsed:",len(names))
except Exception as e:print("Product Hunt discovery page error:",str(e)[:140])
# Keep a bounded, deduplicated archive. Persist state only after successful parsing.
unique={x["id"]:x for x in items}
for x in events:unique[x["id"]]=x
archive["items"]=sorted(unique.values(),key=lambda x:x.get("date") or "",reverse=True)[:3000]
archive["generated_at"]=NOW.isoformat();ARCHIVE.write_text(json.dumps(archive,indent=2,ensure_ascii=False))
STATE.write_text(json.dumps(state,indent=2,ensure_ascii=False))
meta_path=OUT/"meta.json"
meta=json.loads(meta_path.read_text()) if meta_path.exists() else {"sources":[]}
sources=meta.setdefault("sources",[])
extras=[
 {"name":"CNCF Landscape change discovery","project":"CNCF ecosystem","type":"ecosystem-directory","url":"https://github.com/cncf/landscape"},
 {"name":"GitHub observability topic discovery","project":"Emerging observability tools","type":"repository-discovery","url":"https://github.com/topics/observability"},
 {"name":"GitHub OpenTelemetry topic discovery","project":"Emerging observability tools","type":"repository-discovery","url":"https://github.com/topics/opentelemetry"},
 {"name":"Hacker News launch and discussion discovery","project":"Observability community","type":"community-discovery","url":"https://hn.algolia.com/?q=observability"},
 {"name":"Product Hunt observability launches (weekly research source)","project":"Emerging observability tools","type":"product-launch-directory","url":"https://www.producthunt.com/categories/observability-tools?order=recent_launches"},
 {"name":"Grafana Labs What’s New","project":"Grafana","type":"product-updates","url":"https://grafana.com/whats-new/"},
 {"name":"OpenTelemetry Collector component catalog","project":"OpenTelemetry","type":"component-catalog","url":"https://opentelemetry.io/docs/collector/components/"},
 {"name":"OpenTelemetry Registry (frozen reference)","project":"OpenTelemetry ecosystem","type":"historical-registry","url":"https://opentelemetry.netlify.app/ecosystem/registry/"}
 {"name":"Observability Wiki tools directory","project":"Observability ecosystem","type":"ecosystem-directory","url":"https://observability.wiki/tools/"},
 {"name":"Awesome Observability curated repository","project":"Observability ecosystem","type":"curated-directory","url":"https://github.com/adriannovegil/awesome-observability"}]
known_names={x.get("name") for x in sources};sources.extend(x for x in extras if x["name"] not in known_names)
meta["generated_at"]=NOW.isoformat();meta["item_count"]=len(archive["items"])
meta_path.write_text(json.dumps(meta,indent=2,ensure_ascii=False))
print("Discovery events:",len(events),"total archive:",len(archive["items"]))
