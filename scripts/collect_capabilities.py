#!/usr/bin/env python3
"""Collect versioned capability inventories and opt-in feature flags."""
import hashlib,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"; NOW=datetime.now(timezone.utc)
def get(url):
 req=urllib.request.Request(url,headers={"User-Agent":"SignalDesk-Observability-Intelligence/3.0","Accept":"application/vnd.github+json",**({"Authorization":"Bearer "+__import__("os").environ["GITHUB_TOKEN"]} if __import__("os").environ.get("GITHUB_TOKEN") else {})})
 with urllib.request.urlopen(req,timeout=45) as r:return r.read()
def ident(s):return hashlib.sha256(s.encode()).hexdigest()[:20]
def clean(s):return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",s or "")).strip()
archive=json.loads((OUT/"updates.json").read_text());items=archive.get("items",[])
# Prometheus feature flags are a living capability reference, not just a release-note event.
try:
 doc=get("https://raw.githubusercontent.com/prometheus/prometheus/main/docs/feature_flags.md").decode()
 parts=re.split(r"(?m)^##\s+",doc)
 for part in parts[1:]:
  title=part.splitlines()[0].strip()
  flag=re.search(r"`--enable-feature=([^,`]+)`",part)
  if not flag:continue
  name=flag.group(1).strip()
  desc=clean(re.sub(r"(?m)^>.*$"," ",part))
  desc=re.sub(r"`[^\`]*`"," ",desc)
  items.append({"id":ident("prometheus-feature:"+name),"title":"Prometheus feature flag: "+name,
   "summary":(desc[:950] or "See the official feature-flag documentation for behavior and lifecycle.") ,
   "url":"https://prometheus.io/docs/prometheus/latest/feature_flags/","date":None,
   "project":"Prometheus","source":"Prometheus official feature flag documentation","category":"Feature flag",
   "feature_flag":name,"flag_scope":"--enable-feature","inventory":"current documentation"})
 print("Prometheus feature flags inventoried")
except Exception as e:print("Prometheus feature flag inventory error:",str(e)[:180])
# Prom++ publishes its own changelog on the pp branch; do not rely solely on
# GitHub Releases objects, which may not mirror every tagged changelog entry.
try:
 changelog=get("https://raw.githubusercontent.com/deckhouse/prompp/pp/CHANGELOG.md").decode(errors="replace")
 heads=list(re.finditer(r"(?m)^## (v[0-9][^ /]*)(?:\s*/\s*(\d{4}-\d{2}-\d{2}))?\s*$",changelog))
 for i,h in enumerate(heads[:20]):
  end=heads[i+1].start() if i+1<len(heads) else len(changelog)
  body=changelog[h.end():end].strip()
  version,date=h.group(1),h.group(2)
  first=next((clean(line.lstrip(" -*")) for line in body.splitlines() if clean(line) and not clean(line).startswith("#")),"")
  href=f"https://github.com/deckhouse/prompp/blob/pp/CHANGELOG.md"
  items.append({"id":ident("prompp-changelog:"+version),"title":f"Deckhouse Prom++ {version}",
   "summary":first[:950] or "See the upstream Prom++ changelog for release details.",
   "url":href,"date":date+"T00:00:00+00:00" if date else None,"project":"Deckhouse Prom++",
   "source":"Deckhouse Prom++ upstream CHANGELOG.md","category":"Release","version":version,
   "release_notes":body[:5000],"inventory":"upstream changelog"})
  flags=set(re.findall(r"(?i)PROMPP_FEATURES\s*=\s*([A-Za-z0-9_,-]+)",body))
  for flag_list in flags:
   for flag in re.findall(r"[A-Za-z][A-Za-z0-9_]+",flag_list):
    items.append({"id":ident("prompp-feature:"+version+":"+flag),
     "title":f"Prom++ feature flag: {flag} · {version}",
     "summary":f"Flag referenced in Prom++ {version} release notes. Verify whether it is opt-in, default-on, experimental, or deprecated before enabling.",
     "url":href,"date":date+"T00:00:00+00:00" if date else None,"project":"Deckhouse Prom++",
     "source":"Deckhouse Prom++ upstream CHANGELOG.md","category":"Feature flag",
     "feature_flag":flag,"flag_scope":"PROMPP_FEATURES","version":version})
 print(f"Prom++ changelog: {len(heads[:20])} releases parsed")
except Exception as e:print("Prom++ changelog error:",str(e)[:180])
# Compare component inventories and declarative feature gates at a pinned
# Collector release and current main. metadata.yaml is the source of truth.
from concurrent.futures import ThreadPoolExecutor,as_completed
def parse_gate_blocks(text):
 match=re.search(r"(?m)^feature_gates:\s*$",text)
 if not match:return []
 out=[];current=None;active=""
 def finish():
  if current and current.get("id"):out.append(current.copy())
 for line in text[match.end():].splitlines():
  item=re.match(r"^\s*-\s*(?:id|name):\s*(.+)$",line)
  if item:
   finish();current={"id":item.group(1).strip().strip(chr(34)+chr(39))};active="";continue
  if current is None:continue
  field=re.match(r"^\s+(stage|description|from_version|to_version|reference_url):\s*(.*)$",line)
  if field:
   active=field.group(1);value=field.group(2).strip().strip(chr(34)+chr(39))
   current[active]=value if value not in (">-","|","") else ""
  elif active=="description" and line.strip():
   current["description"]=(current.get("description","")+" "+line.strip()).strip()
  elif line.strip() and not line.startswith(" "):
   active=""
 finish()
 return out
for owner,repo,project in [("open-telemetry","opentelemetry-collector","OpenTelemetry Collector core"),
                           ("open-telemetry","opentelemetry-collector-contrib","OpenTelemetry Collector contrib")]:
 for ref,label in [("v0.145.0","0.145.0"),("main","main")]:
  try:
   tree=json.loads(get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"))
   if tree.get("truncated"):print("Tree truncated:",repo,ref)
   paths={x.get("path","") for x in tree.get("tree",[])}
   metadata=sorted(p for p in paths if re.match(r"^(receiver|processor|exporter|connector|extension)/[^/]+/metadata\.yaml$",p))
   components=set()
   for path in metadata:
    m=re.match(r"^(receiver|processor|exporter|connector|extension)/([^/]+)/metadata\.yaml$",path)
    if m:components.add((m.group(1),m.group(2)))
   for kind,name in sorted(components):
    url=f"https://github.com/{owner}/{repo}/tree/{ref}/{kind}/{name}"
    items.append({"id":ident(f"otel-inventory:{owner}/{repo}:{ref}:{kind}:{name}"),
     "title":f"Collector {kind}: {name} · inventory {label}",
     "summary":f"Component metadata exists in {project} at ref {label}. This confirms source-tree presence, not inclusion in a particular distribution or activation in a running Collector. Review signal support and stability in the component documentation.",
     "url":url,"date":None,"project":project,"source":f"OpenTelemetry component inventory · {owner}/{repo}",
     "category":"Component inventory","component_type":kind,"component_name":name,"collector_ref":label,
     "inventory":"versioned metadata.yaml"})
   def read_metadata(path):
    return path,get(f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}").decode(errors="replace")
   gates=[]
   with ThreadPoolExecutor(max_workers=12) as pool:
    futures=[pool.submit(read_metadata,p) for p in metadata]
    for future in as_completed(futures):
     try:
      path,content=future.result()
      for gate in parse_gate_blocks(content):gates.append((path,gate))
     except Exception as e:print("metadata read error:",repo,ref,str(e)[:100])
   for path,gate in gates:
    stage=gate["stage"] or "unspecified"
    desc=gate["description"] or "See the component metadata and linked reference for gate behavior."
    summary=f"{stage.upper()} gate; introduced {gate['from_version'] or 'version unspecified'}. {desc}"
    if gate["to_version"]:summary+=f" Stage transition/removal version: {gate['to_version']}."
    gate_url=gate["reference_url"] or f"https://github.com/{owner}/{repo}/blob/{ref}/{path}"
    items.append({"id":ident(f"otel-gate:{owner}/{repo}:{ref}:{gate['id']}"),
     "title":f"OTel feature gate: {gate['id']} · {label}",
     "summary":summary[:1000],"url":gate_url,"date":None,"project":project,
     "source":f"OpenTelemetry feature-gate metadata · {owner}/{repo}",
     "category":"Feature gate","feature_gate":gate["id"],"gate_stage":stage,
     "from_version":gate["from_version"],"to_version":gate["to_version"],
     "component_metadata":f"https://github.com/{owner}/{repo}/blob/{ref}/{path}",
     "flag_scope":"--feature-gates","collector_ref":label,"inventory":"versioned metadata.yaml"})
   print(f"{repo} {label}: {len(components)} components; {len(gates)} feature gates")
  except Exception as e:print("OTel inventory error:",repo,ref,str(e)[:160])
# Stable IDs prevent the capability inventory from multiplying on each daily run.
unique={x["id"]:x for x in items}
archive["items"]=sorted(unique.values(),key=lambda x:x.get("date") or "",reverse=True)
archive["generated_at"]=NOW.isoformat()
(OUT/"updates.json").write_text(json.dumps(archive,indent=2,ensure_ascii=False))
meta_path=OUT/"meta.json"
if meta_path.exists():
 meta=json.loads(meta_path.read_text());meta["generated_at"]=NOW.isoformat();meta["item_count"]=len(archive["items"])
 sources=meta.setdefault("sources",[])
 extras=[
  {"name":"Prometheus feature flag documentation","project":"Prometheus","type":"feature-flags","url":"https://prometheus.io/docs/prometheus/latest/feature_flags/"},
  {"name":"Deckhouse Prom++ upstream changelog","project":"Deckhouse Prom++","type":"changelog","url":"https://github.com/deckhouse/prompp/blob/pp/CHANGELOG.md"},
  {"name":"OpenTelemetry Collector component and feature-gate inventory","project":"OpenTelemetry Collector","type":"component-inventory","url":"https://github.com/open-telemetry/opentelemetry-collector/tree/v0.145.0"},
  {"name":"OpenTelemetry Collector Contrib component and feature-gate inventory","project":"OpenTelemetry Collector Contrib","type":"component-inventory","url":"https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/v0.145.0"}]
 known={x.get("name") for x in sources}
 sources.extend(x for x in extras if x["name"] not in known)
 meta["item_count"]=len(archive["items"]);(meta_path).write_text(json.dumps(meta,indent=2,ensure_ascii=False))
print("Capability-enriched archive:",len(archive["items"]),"items")
