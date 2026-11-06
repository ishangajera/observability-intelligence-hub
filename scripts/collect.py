#!/usr/bin/env python3
"""Collect public RSS/Atom items and GitHub releases into a deduplicated JSON archive."""
import json, os, re, hashlib, urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/"config/sources.json").read_text())
OUT=ROOT/"data"; OUT.mkdir(exist_ok=True)
NOW=datetime.now(timezone.utc)
def request(url, headers=None):
    req=urllib.request.Request(url,headers={"User-Agent":"SignalDesk-Observability-Intelligence/1.0",**(headers or {})})
    with urllib.request.urlopen(req,timeout=25) as r:return r.read()
def clean(s): return re.sub(r"\\s+"," ",re.sub(r"<[^>]+>"," ",s or "")).strip()
def parse_date(s):
    if not s:return None
    try:return parsedate_to_datetime(s).astimezone(timezone.utc).isoformat()
    except Exception:
        try:return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc).isoformat()
        except Exception:return None
def rss_items(src):
    try:
        root=ET.fromstring(request(src["url"]))
        entries=root.findall(".//item") or root.findall(".//{*}entry")
        out=[]
        for e in entries[:30]:
            def find(*names):
                for n in names:
                    x=e.find(n)
                    if x is None:x=e.find("{*}"+n)
                    if x is not None:return x
                return None
            title,link,desc,dt,guid=find("title"),find("link"),find("description","summary","content"),find("pubDate","published","updated","date"),find("guid","id")
            href=(link.attrib.get("href") if link is not None else None) or (link.text if link is not None else "")
            if not href and guid is not None and (guid.text or "").startswith("http"):href=guid.text
            title=clean(title.text if title is not None else "")
            if not title or not href:continue
            uid=hashlib.sha256(href.encode()).hexdigest()[:20]
            out.append({"id":uid,"title":title,"summary":clean(desc.text if desc is not None else "")[:420],"url":href,"date":parse_date(dt.text if dt is not None else None),"project":src["project"],"source":src["name"],"category":"Engineering"})
        return out
    except Exception as e:print("RSS error:",src["name"],str(e)[:160]);return []
def releases(repo):
    url=f"https://api.github.com/repos/{repo['owner']}/{repo['repo']}/releases?per_page=8"
    headers={"Accept":"application/vnd.github+json"}
    if os.getenv("GITHUB_TOKEN"):headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
    try:
        data=json.loads(request(url,headers))
        out=[]
        for x in data:
            if x.get("draft"):continue
            href=x.get("html_url","")
            out.append({"id":hashlib.sha256(href.encode()).hexdigest()[:20],"title":f"{repo['project']} {x.get('tag_name','release')}","summary":clean(x.get("body",""))[:420] or "Upstream GitHub release. Review release notes for changes and compatibility details.","url":href,"date":x.get("published_at") or x.get("created_at"),"project":repo["project"],"source":f"GitHub · {repo['owner']}/{repo['repo']}","category":"Release","version":x.get("tag_name")})
        return out
    except Exception as e:print("GitHub error:",repo["owner"]+"/"+repo["repo"],str(e)[:160]);return []
items=[]
for s in CONFIG["rss"]:items.extend(rss_items(s))
for r in CONFIG["repos"]:items.extend(releases(r))
unique={x["id"]:x for x in items};items=sorted(unique.values(),key=lambda x:x.get("date") or "",reverse=True)[:1500]
(OUT/"updates.json").write_text(json.dumps({"generated_at":NOW.isoformat(),"items":items},indent=2,ensure_ascii=False))
sources=[{"name":s["name"],"project":s["project"],"type":"rss","url":s["url"]} for s in CONFIG["rss"]]+[{"name":f"{r['owner']}/{r['repo']} releases","project":r["project"],"type":"github","url":f"https://github.com/{r['owner']}/{r['repo']}/releases"} for r in CONFIG["repos"]]
(OUT/"meta.json").write_text(json.dumps({"generated_at":NOW.isoformat(),"item_count":len(items),"sources":sources},indent=2))
print(f"Collected {len(items)} unique signals at {NOW.isoformat()}")
