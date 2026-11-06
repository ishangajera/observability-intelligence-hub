#!/usr/bin/env python3
"""Collect observability releases, component additions, articles, community posts and videos."""
import hashlib, html, json, os, re, urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/sources.json").read_text())
OUT = ROOT / "data"; OUT.mkdir(exist_ok=True)
NOW = datetime.now(timezone.utc)

def request(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent":"SignalDesk-Observability-Intelligence/2.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as response: return response.read()

def clean(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", value)
    value = re.sub(r"\`{1,3}", "", value)
    value = re.sub(r"[*_~#]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def node_text(node):
    return "" if node is None else "".join(node.itertext()).strip()

def parse_date(value):
    if not value: return None
    try: return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except Exception:
        try:
            parsed = datetime.fromisoformat(value.replace("Z","+00:00"))
            if parsed.tzinfo is None: parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        except Exception: return None

def stable_id(value): return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]

def rss_items(source):
    try:
        root = ET.fromstring(request(source["url"]))
        entries = root.findall(".//item") or root.findall(".//{*}entry")
        results = []
        for entry in entries[:40]:
            def find(*names):
                for name in names:
                    node = entry.find(name)
                    if node is None: node = entry.find("{*}"+name)
                    if node is not None: return node
                return None
            title_node, link_node = find("title"), find("link")
            summary_node = find("description","summary","content","encoded")
            date_node, guid_node = find("pubDate","published","updated","date"), find("guid","id")
            link = ""
            if link_node is not None: link = link_node.attrib.get("href") or (link_node.text or "").strip()
            if not link and guid_node is not None and (guid_node.text or "").startswith("http"): link = guid_node.text.strip()
            title = clean(node_text(title_node))
            if not title or not link: continue
            results.append({
                "id":stable_id(link),"title":title,"summary":clean(node_text(summary_node))[:1100],
                "url":link,"date":parse_date(node_text(date_node)),"project":source["project"],
                "source":source["name"],"category":source.get("category","Article"),
                "content_type":source.get("kind","blog")
            })
        return results
    except Exception as error:
        print("Feed error:",source["name"],str(error)[:180]); return []

def parse_release_sections(body):
    sections, heading, bullets = [], "Release notes", []
    for raw in (body or "").splitlines():
        line = raw.strip()
        match = re.match(r"^#{1,6}\s+(.+)",line)
        if match:
            if bullets: sections.append({"heading":clean(heading),"items":bullets[:12]})
            heading, bullets = match.group(1), []
        elif re.match(r"^(?:[-*+]|\d+[.)])\s+",line):
            item = clean(re.sub(r"^(?:[-*+]|\d+[.)])\s+","",line))
            if item: bullets.append(item[:500])
    if bullets: sections.append({"heading":clean(heading),"items":bullets[:12]})
    return sections[:18]

COMPONENT_RE = re.compile(r"\b(receiver|processor|exporter|connector|extension)/([a-zA-Z0-9_-]+)\b")
def find_new_components(body):
    found = {}
    in_new_section = False
    for raw in (body or "").splitlines():
        line = raw.strip()
        heading = re.match(r"^#{1,6}\s+(.+)",line)
        if heading:
            h = heading.group(1).lower()
            in_new_section = any(token in h for token in ("new component","new receiver","new processor","new exporter","new connector","new extension"))
        hits = list(COMPONENT_RE.finditer(line))
        if not hits: continue
        is_new = in_new_section or bool(re.search(r"\b(new|add(?:ed)?|introduc(?:e|ed|ing)|initial implementation)\b",line,re.I))
        if is_new:
            for hit in hits: found[(hit.group(1).lower(),hit.group(2))] = clean(line)[:500]
    return [{"type":kind,"name":name,"evidence":evidence} for (kind,name),evidence in sorted(found.items())]

def releases(repo):
    url=f"https://api.github.com/repos/{repo['owner']}/{repo['repo']}/releases?per_page=10"
    headers={"Accept":"application/vnd.github+json"}
    if os.getenv("GITHUB_TOKEN"): headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
    try:
        data=json.loads(request(url,headers)); results=[]
        for release in data:
            if release.get("draft"): continue
            href=release.get("html_url",""); tag=release.get("tag_name","release"); body=release.get("body") or ""
            sections=parse_release_sections(body)
            components=find_new_components(body) if "opentelemetry-collector" in repo["repo"] else []
            first=next((clean(line) for line in body.splitlines() if clean(line) and not clean(line).startswith("#")),"")
            results.append({
                "id":stable_id(href),"title":f"{repo['project']} {tag}",
                "summary":(first or "Open upstream release notes for changes, compatibility notes, and upgrade guidance.")[:1100],
                "url":href,"date":release.get("published_at") or release.get("created_at"),
                "project":repo["project"],"source":f"GitHub · {repo['owner']}/{repo['repo']}",
                "category":"Release","version":tag,"release_notes":body[:50000],
                "change_sections":sections,"new_components":components
            })
            for component in components:
                component_url=href+"#component-"+component["type"]+"-"+component["name"]
                results.append({
                    "id":stable_id(component_url),"title":f"New OTel Collector {component['type']}: {component['name']}",
                    "summary":component["evidence"] or f"New {component['type']} component identified in {tag}.",
                    "url":href,"date":release.get("published_at") or release.get("created_at"),
                    "project":"OpenTelemetry Collector","source":f"Component announcement · {repo['owner']}/{repo['repo']}",
                    "category":"Component","version":tag,"component_type":component["type"],
                    "component_name":component["name"],"parent_release":f"{repo['project']} {tag}"
                })
        return results
    except Exception as error:
        print("GitHub release error:",repo["owner"]+"/"+repo["repo"],str(error)[:180]); return []

items=[]
for source in CONFIG.get("rss",[]): items.extend(rss_items(source))
for repo in CONFIG.get("repos",[]): items.extend(releases(repo))
unique={item["id"]:item for item in items}
items=sorted(unique.values(),key=lambda item:item.get("date") or "",reverse=True)[:2000]
(OUT/"updates.json").write_text(json.dumps({"generated_at":NOW.isoformat(),"items":items},indent=2,ensure_ascii=False))
sources=[{"name":s["name"],"project":s["project"],"type":s.get("kind","rss"),"url":s["url"]} for s in CONFIG.get("rss",[])]
sources += [{"name":f"{r['owner']}/{r['repo']} releases","project":r["project"],"type":"github","url":f"https://github.com/{r['owner']}/{r['repo']}/releases"} for r in CONFIG.get("repos",[])]
(OUT/"meta.json").write_text(json.dumps({"generated_at":NOW.isoformat(),"item_count":len(items),"sources":sources},indent=2))
print(f"Collected {len(items)} unique signals from {len(sources)} sources at {NOW.isoformat()}")
