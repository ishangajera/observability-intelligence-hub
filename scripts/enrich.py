#!/usr/bin/env python3
"""Generate item-specific, evidence-backed editorial triage cues."""
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
items=json.loads((ROOT/"data/updates.json").read_text()).get("items",[])
RULES=[
("security","Security","high",[r"\bsecurity\b",r"\bcve-\d{4}-\d+\b",r"\bvulnerabilit(?:y|ies)\b",r"\bauthentication bypass\b",r"\bremote code execution\b"]),
("breaking","Breaking change","high",[r"\bbreaking changes?\b",r"\bincompatible\b",r"\bno longer supported\b",r"\bremoved?\b.{0,65}\b(config|flag|option|api|component|feature)\b"]),
("deprecation","Deprecation","medium",[r"\bdeprecated?\b",r"\bwill be removed\b",r"\bsunset(?:ting)?\b"]),
("compatibility","Compatibility","medium",[r"\bcompatib(?:le|ility)\b",r"\bmigration\b",r"\bschema change\b",r"\bapi change\b"]),
("performance","Performance","medium",[r"\bperformance\b",r"\blatency\b",r"\bthroughput\b",r"\bmemory usage\b",r"\bcpu usage\b"]),
("configuration","Configuration","medium",[r"\bconfiguration\b",r"\bconfig(?:uration)? option\b",r"\bdefault(?:s)? changed\b",r"\bfeature gate\b"]),
("component","New component","low",[r"\bnew (?:receiver|processor|exporter|connector|extension|component)\b",r"\bnew otel collector\b"]),
("plugin","Plugin","low",[r"\bplugin\b",r"\bdata source plugin\b",r"\bpanel plugin\b"]),
("feature","Feature","low",[r"\bnew feature\b",r"\badded support\b",r"\bintroduc(?:e|es|ed|ing)\b",r"\bnew capability\b"]),
("bugfix","Bug fix","low",[r"\bbug fix(?:es)?\b",r"\bfix(?:es|ed)?\b",r"\bresolve(?:s|d)?\b"])
]
ACTIONS={
"security":"Check whether the affected component and version are deployed; review the upstream advisory and patch guidance.",
"breaking":"Compare the change with pinned versions and configuration; test upgrade and rollback paths in staging.",
"deprecation":"Search configurations and manifests for the affected surface; identify an owner and migration deadline.",
"compatibility":"Validate version and protocol compatibility across producers, collectors, backends, and dashboards.",
"performance":"Check the workload and benchmark context; validate resource usage and latency with representative traffic.",
"configuration":"Diff defaults and configuration semantics; test rendered config and alerting behavior before upgrading.",
"component":"Check component type, maturity, distribution availability, and whether it is included in your Collector build.",
"plugin":"Check plugin ownership, Grafana compatibility, signature status, and release cadence before adoption.",
"feature":"Assess whether the capability solves an active use case; prototype outside production first.",
"bugfix":"Check whether the affected bug exists in your deployed version and whether the fix warrants an upgrade."
}
WHY={
"security":"The source explicitly mentions a security issue; verify whether the affected product and version are in use.",
"breaking":"The release notes identify an incompatible or removed surface that may affect upgrades or configuration.",
"deprecation":"The source identifies a deprecated surface that may need a planned migration.",
"compatibility":"The source calls out a compatibility or migration concern across versions or integrations.",
"performance":"The source discusses runtime performance, latency, throughput, or resource use.",
"configuration":"The source mentions configuration semantics or defaults that may change operational behavior.",
"component":"A new Collector component appears in upstream release notes; confirm its maturity and distribution support.",
"plugin":"The source mentions a Grafana plugin or plugin ecosystem change; verify compatibility and maintenance status.",
"feature":"The source describes a new capability; assess whether it fills a current operational gap.",
"bugfix":"The source describes a fix; check whether the affected behavior exists in your deployed version."
}
def excerpt(text,pattern):
    match=re.search(pattern,text,re.I)
    if not match:return None
    start,end=max(0,match.start()-90),min(len(text),match.end()+150)
    return re.sub(r"\s+"," ",text[start:end]).strip()
result={}
for item in items:
    text=" ".join([item.get("title",""),item.get("summary",""),item.get("release_notes","")[:12000]," ".join(x.get("evidence","") for x in item.get("new_components",[]))])
    tags,evidence=[],[]
    for key,label,priority,patterns in RULES:
        matched=None
        for pattern in patterns:
            matched=excerpt(text,pattern)
            if matched:break
        if item.get("category")=="Component" and key=="component":matched=item.get("summary","")[:260]
        if matched:
            tags.append({"id":key,"label":label,"priority":priority})
            if len(evidence)<5:evidence.append({"theme":label,"text":matched[:420]})
    priorities=[tag["priority"] for tag in tags]
    priority="high" if "high" in priorities else ("medium" if "medium" in priorities else "low")
    primary=next((tag["id"] for tag in tags if tag["priority"]==priority),tags[0]["id"] if tags else None)
    actions=list(dict.fromkeys(ACTIONS[tag["id"]] for tag in tags))[:4]
    result[item.get("id",item.get("url",""))]={
      "priority":priority,"themes":tags,
      "why_it_matters":WHY.get(primary,"No explicit operational-risk phrase matched; this item stays in the general feed rather than the editorial review queue."),
      "review_actions":actions,"evidence":evidence,
      "confidence":"explicit source phrase match" if tags else "no matching editorial rule","method":"transparent-rules"
    }
out={"generated_at":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
"method":"transparent-rule-based-triage",
"disclaimer":"Priority is an attention cue based on source wording, not verified product severity or deployment-specific impact. Confirm applicability in the primary source.",
"item_count":len(result),"items":result}
(ROOT/"data/intelligence.json").write_text(json.dumps(out,indent=2,ensure_ascii=False))
print(f"Generated item-specific triage for {len(result)} signals")
