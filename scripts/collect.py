#!/usr/bin/env python3
"""Collect releases, new components, Grafana plugins, articles, community posts and videos."""
import hashlib, html, json, os, re, urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/"config/sources.json").read_text())
OUT=ROOT/"data"; OUT.mkdir(exist_ok=True)
NOW=datetime.now(timezone.utc)

def request(url,headers=None):
    req=urllib.request.Request(url,headers={"User-Agent":"SignalDesk-Observability-Intelligence/2.1",**(headers or {})})
    with urllib.request.urlopen(req,timeout=30) as response:return response.read()

def clean(value):
    value=html.unescape(value or "")
    value=re.sub(r"<[^>]+>"," ",value)
    value=re.sub(r"!\[([^\]]*)\]\([^)]*\)",r"\1",value)
    value=re.sub(r"\[([^\]]+)\]\(([^)]+)\)",r"\1",value)
    value=re.sub(r"\`{1,3}","",value)
    value=re.sub(r"[*_~#]+"," ",value)
    return re.sub(r"\s+"," ",value).strip()

def node_text(node):
    return "" if node is None else "".join(node.itertext()).strip()

def parse_date(value):
    if not value:return None
    try:return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except Exception:
        try:
            parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
            if parsed.tzinfo is None:parsed=parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        except Exception:return None

def stable_id(value):return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]

def rss_items(source):
    try:
        root=ET.fromstring(request(source["url"]))
        entries=root.findall(".//item") or root.findall(".//{*}entry")
        results=[]
        for entry in entries[:40]:
            def find(*names):
                for name in names:
                    node=entry.find(name)
                    if node is None:node=entry.find("{*}"+name)
                    if node is not None:return node
                return None
            title_node,link_node=find("title"),find("link")
            summary_node=find("description","summary","content","encoded")
            date_node,guid_node=find("pubDate","published","updated","date"),find("guid","id")
            link=""
            if link_node is not None:link=link_node.attrib.get("href") or (link_node.text or "").strip()
            if not link and guid_node is not None and (guid_node.text or "").startswith("http"):link=guid_node.text.strip()
            title=clean(node_text(title_node))
            if not title or not link:continue
            results.append({"id":stable_id(link),"title":title,"summary":clean(node_text(summary_node))[:1100],
              "url":link,"date":parse_date(node_text(date_node)),"project":source["project"],"source":source["name"],
              "category":source.get("category","Article"),"content_type":source.get("kind","blog")})
        return results
    except Exception as error:
        print("Feed error:",source["name"],str(error)[:180]);return []

def parse_release_sections(body):
    sections,heading,bullets=[],"Release notes",[]
    for raw in (body or "").splitlines():
        line=raw.strip()
        match=re.match(r"^#{1,6}\s+(.+)",line)
        if match:
            if bullets:sections.append({"heading":clean(heading),"items":bullets[:4]})
            heading,bullets=match.group(1),[]
        elif re.match(r"^(?:[-*+]|\d+[.)])\s+",line):
            item=clean(re.sub(r"^(?:[-*+]|\d+[.)])\s+","",line))
            if item:bullets.append(item[:220])
    if bullets:sections.append({"heading":clean(heading),"items":bullets[:4]})
    return sections[:6]

COMPONENT_RE=re.compile(r"\b(receiver|processor|exporter|connector|extension)/([a-zA-Z0-9_-]+)\b")
def find_new_components(body):
    found={};in_new_section=False
    for raw in (body or "").splitlines():
        line=raw.strip();heading=re.match(r"^#{1,6}\s+(.+)",line)
        if heading:
            h=heading.group(1).lower()
            in_new_section=any(token in h for token in ("new component","new receiver","new processor","new exporter","new connector","new extension"))
        hits=list(COMPONENT_RE.finditer(line))
        if not hits:continue
        prefix=line[:hits[0].start()]
        is_new=in_new_section or bool(re.search(r"\b(new|add(?:ed)?|introduc(?:e|ed|ing)|initial implementation)\b",prefix,re.I))
        if is_new:
            for hit in hits:found[(hit.group(1).lower(),hit.group(2))]=clean(line)[:350]
    return [{"type":kind,"name":name,"evidence":evidence} for (kind,name),evidence in sorted(found.items())]

def releases(repo):
    url=f"https://api.github.com/repos/{repo['owner']}/{repo['repo']}/releases?per_page=5"
    headers={"Accept":"application/vnd.github+json"}
    if os.getenv("GITHUB_TOKEN"):headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
    try:
        data=json.loads(request(url,headers));results=[]
        for release in data:
            if release.get("draft"):continue
            href=release.get("html_url","");tag=release.get("tag_name","release");body=release.get("body") or ""
            if repo["repo"]=="opentelemetry-collector-releases" and not re.match(r"^v\d",tag):continue
            sections=parse_release_sections(body)
            components=find_new_components(body) if repo["repo"] in ("opentelemetry-collector","opentelemetry-collector-contrib") else []
            first=next((clean(line) for line in body.splitlines() if clean(line) and not clean(line).startswith("#")),"")
            results.append({"id":stable_id(href),"title":f"{repo['project']} {tag}",
              "summary":(first or "Open upstream release notes for changes, compatibility notes, and upgrade guidance.")[:900],
              "url":href,"date":release.get("published_at") or release.get("created_at"),
              "project":repo["project"],"source":f"GitHub · {repo['owner']}/{repo['repo']}",
              "category":"Release","version":tag,"release_notes":body[:3000],
              "change_sections":sections,"new_components":components})
            for component in components:
                component_url=href+"#component-"+component["type"]+"-"+component["name"]
                results.append({"id":stable_id(component_url),"title":f"New OTel Collector {component['type']}: {component['name']}",
                  "summary":component["evidence"] or f"New {component['type']} component identified in {tag}.",
                  "url":href,"date":release.get("published_at") or release.get("created_at"),
                  "project":"OpenTelemetry Collector","source":f"Component announcement · {repo['owner']}/{repo['repo']}",
                  "category":"Component","version":tag,"component_type":component["type"],
                  "component_name":component["name"],"parent_release":f"{repo['project']} {tag}"})
        return results
    except Exception as error:
        print("GitHub release error:",repo["owner"]+"/"+repo["repo"],str(error)[:180]);return []

def grafana_plugin_changes():
    """Seed a compact catalog snapshot once, then emit new-plugin and version-change events."""
    state_path=OUT/"plugin_catalog.json"
    previous={}
    baseline_exists=state_path.exists()
    if baseline_exists:
        try:previous=json.loads(state_path.read_text()).get("plugins",{})
        except Exception:previous={}
    try:
        payload=json.loads(request("https://grafana.com/api/plugins"))
        current={};events=[]
        for plugin in payload.get("items",[]):
            slug=plugin.get("slug")
            if not slug or plugin.get("status") not in ("active","enterprise"):continue
            record={"name":plugin.get("name") or slug,"version":plugin.get("version") or "",
              "type":plugin.get("typeName") or plugin.get("typeCode") or "Plugin",
              "description":clean(plugin.get("description",""))[:500],
              "url":f"https://grafana.com/grafana/plugins/{slug}/",
              "repository":plugin.get("url") or "",
              "created_at":plugin.get("createdAt"),"updated_at":plugin.get("updatedAt")}
            current[slug]=record
            old=previous.get(slug)
            if not baseline_exists:continue
            if old is None:
                title=f"New Grafana plugin: {record['name']}"
                summary=f"{record['type']} plugin added to the public catalog. {record['description']}".strip()
                event_date=record["created_at"] or NOW.isoformat()
            elif old.get("version")!=record["version"]:
                title=f"Grafana plugin update: {record['name']} {record['version']}"
                summary=f"Catalog version changed from {old.get('version') or 'unknown'} to {record['version']}. {record['description']}".strip()
                event_date=record["updated_at"] or NOW.isoformat()
            else:continue
            events.append({"id":stable_id("grafana-plugin:"+slug+":"+record["version"]+":"+title),
              "title":title,"summary":summary[:1000],"url":record["url"],"date":parse_date(event_date) or event_date,
              "project":"Grafana plugins","source":"Grafana public plugin catalog","category":"Plugin",
              "version":record["version"],"plugin_slug":slug,"plugin_type":record["type"],
              "repository":record["repository"]})
        state_path.write_text(json.dumps({"generated_at":NOW.isoformat(),"plugins":current},indent=2,ensure_ascii=False))
        print(f"Catalog snapshot: {len(current)} Grafana plugins; {len(events)} new/version-change events")
        return events
    except Exception as error:
        print("Grafana plugin catalog error:",str(error)[:180]);return []

items=[]
for source in CONFIG.get("rss",[]):items.extend(rss_items(source))
for repo in CONFIG.get("repos",[]):items.extend(releases(repo))
items.extend(grafana_plugin_changes())
unique={item["id"]:item for item in items}
items=sorted(unique.values(),key=lambda item:item.get("date") or "",reverse=True)[:2000]
(OUT/"updates.json").write_text(json.dumps({"generated_at":NOW.isoformat(),"items":items},indent=2,ensure_ascii=False))
sources=[{"name":s["name"],"project":s["project"],"type":s.get("kind","rss"),"url":s["url"]} for s in CONFIG.get("rss",[])]
sources += [{"name":f"{r['owner']}/{r['repo']} releases","project":r["project"],"type":"github","url":f"https://github.com/{r['owner']}/{r['repo']}/releases"} for r in CONFIG.get("repos",[])]
sources.append({"name":"Grafana public plugin catalog","project":"Grafana plugins","type":"plugin-catalog","url":"https://grafana.com/grafana/plugins/search/"})
(OUT/"meta.json").write_text(json.dumps({"generated_at":NOW.isoformat(),"item_count":len(items),"sources":sources},indent=2))
print(f"Collected {len(items)} unique signals from {len(sources)} sources at {NOW.isoformat()}")
