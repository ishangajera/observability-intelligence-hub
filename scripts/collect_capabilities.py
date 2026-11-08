#!/usr/bin/env python3
"""Collect versioned capability inventories and opt-in feature flags."""
import hashlib,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"data"; NOW=datetime.now(timezone.utc)
def get(url):
 req=urllib.request.Request(url,headers={"User-Agent":"SignalDesk-Observability-Intelligence/3.0","Accept":"application/vnd.github+json"})
 with urllib.request.urlopen(req,timeout=45) as r:return r.read()
def ident(s):return hashlib.sha256(s.encode()).hexdigest()[:20]
def clean(s):return re.sub(r"\\s+"," ",re.sub(r"<[^>]+>"," ",s or "")).strip()
archive=json.loads((OUT/"updates.json").read_text());items=archive.get("items",[])
# Prometheus feature flags are a living capability reference, not just a release-note event.
try:
 doc=get("https://raw.githubusercontent.com/prometheus/prometheus/main/docs/feature_flags.md").decode()
 parts=re.split(r"(?m)^##\\s+",doc)
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
# Compare the component directory inventory at a pinned Collector release and current main.
# This catches components that are not mentioned in the latest release notes.
for owner,repo,project in [("open-telemetry","opentelemetry-collector","OpenTelemetry Collector core"),
                           ("open-telemetry","opentelemetry-collector-contrib","OpenTelemetry Collector contrib")]:
 for ref,label in [("v0.145.0","0.145.0"),("main","main")]:
  try:
   tree=json.loads(get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"))
   if tree.get("truncated"):print("Tree truncated:",repo,ref)
   paths={x.get("path","") for x in tree.get("tree",[])}
   found=set()
   for path in paths:
    m=re.match(r"^(receiver|processor|exporter|connector|extension)/([^/]+)/README\\.md$",path)
    if m:found.add((m.group(1),m.group(2)))
   for kind,name in sorted(found):
    url=f"https://github.com/{owner}/{repo}/tree/{ref}/{kind}/{name}"
    items.append({"id":ident(f"otel-inventory:{owner}/{repo}:{ref}:{kind}:{name}"),
     "title":f"Collector {kind}: {name} · inventory {label}",
     "summary":f"Component directory is present in {project} at ref {label}. This is an inventory signal, not proof that it is included in a particular distribution or enabled in a running Collector. Check component documentation for stability, supported signals, configuration, and feature gates.",
     "url":url,"date":None,"project":project,"source":f"OpenTelemetry component inventory · {owner}/{repo}",
     "category":"Component inventory","component_type":kind,"component_name":name,"collector_ref":label,
     "inventory":"versioned source tree"})
   print(f"{repo} {label}: {len(found)} component directories")
  except Exception as e:print("OTel inventory error:",repo,ref,str(e)[:160])
# Stable IDs prevent the capability inventory from multiplying on each daily run.
unique={x["id"]:x for x in items}
archive["items"]=sorted(unique.values(),key=lambda x:x.get("date") or "",reverse=True)
archive["generated_at"]=NOW.isoformat()
(OUT/"updates.json").write_text(json.dumps(archive,indent=2,ensure_ascii=False))
print("Capability-enriched archive:",len(archive["items"]),"items")
