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
# Compare component inventories and declarative feature gates at a pinned
# Collector release and current main. metadata.yaml is the source of truth.
from concurrent.futures import ThreadPoolExecutor,as_completed
def parse_gate_blocks(text):
 match=re.search(r"(?m)^feature_gates:\s*$",text)
 if not match:return []
 tail=text[match.end():]
 starts=list(re.finditer(r"(?m)^  - (?:id|name):\s*(.+)$",tail))
 out=[]
 for i,m in enumerate(starts):
  stop=starts[i+1].start() if i+1<len(starts) else len(tail)
  chunk=tail[m.start():stop]
  gate=m.group(1).strip().strip(chr(34)+chr(39))
  def field(name):
   x=re.search(r"(?m)^    "+re.escape(name)+r":\s*(.*)$",chunk)
   return x.group(1).strip().strip(chr(34)+chr(39)) if x else ""
  out.append({"id":gate,"description":field("description"),"stage":field("stage"),
              "from_version":field("from_version"),"to_version":field("to_version"),
              "reference_url":field("reference_url")})
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
print("Capability-enriched archive:",len(archive["items"]),"items")
