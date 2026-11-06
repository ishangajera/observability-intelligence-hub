#!/usr/bin/env python3
"""Create transparent, rules-based editorial triage from collected public signals.

This deliberately does not invent product-specific impact. It detects explicit
release-note language, records evidence, and suggests a review checklist.
"""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
items = json.loads((ROOT / "data/updates.json").read_text()).get("items", [])

RULES = [
    ("security", "Security", "high", [r"\\bsecurity\\b", r"\\bcve-\\d{4}-\\d+\\b", r"\\bvulnerabilit(?:y|ies)\\b", r"\\bauthentication bypass\\b", r"\\bremote code execution\\b"]),
    ("breaking", "Breaking change", "high", [r"breaking changes?", r"\\bremoved?\\b.{0,55}\\b(config|flag|option|api|component|feature)\\b", r"\\bincompatible\\b", r"\\bno longer supported\\b"]),
    ("deprecation", "Deprecation", "medium", [r"\\bdeprecated?\\b", r"\\bwill be removed\\b", r"\\bsunset(?:ting)?\\b"]),
    ("compatibility", "Compatibility", "medium", [r"\\bcompatib(?:le|ility)\\b", r"\\bupgrade(?:d|s)?\\b", r"\\bmigration\\b", r"\\bschema change\\b", r"\\bapi change\\b"]),
    ("performance", "Performance", "medium", [r"\\bperformance\\b", r"\\blatency\\b", r"\\bthroughput\\b", r"\\bmemory usage\\b", r"\\bCPU usage\\b", r"\\b优化\\b"]),
    ("configuration", "Configuration", "medium", [r"\\bconfiguration\\b", r"\\bconfig(?:uration)? option\\b", r"\\bdefault(?:s)? changed\\b", r"\\bflag\\b", r"\\bparameter\\b"]),
    ("feature", "Feature", "low", [r"\\bnew feature\\b", r"\\badded support\\b", r"\\bintroduc(?:e|es|ed|ing)\\b", r"\\bnew component\\b"]),
    ("bugfix", "Bug fix", "low", [r"\\bbug fix(?:es)?\\b", r"\\bfix(?:es|ed)?\\b", r"\\bresolve(?:s|d)?\\b"]),
]
ACTIONS = {
    "security": "Check whether the affected component/version is deployed; review the advisory and plan a patched-version rollout if applicable.",
    "breaking": "Compare the change with your pinned version and configuration; test upgrade and rollback paths in staging before rollout.",
    "deprecation": "Search configs and manifests for the deprecated surface; identify an owner and migration deadline.",
    "compatibility": "Validate version and protocol compatibility across producers, collectors, backends, and dashboards.",
    "performance": "Review the benchmark or workload context; validate resource usage and latency with representative traffic.",
    "configuration": "Diff defaults and configuration semantics; test rendered config and alerting behavior before upgrading.",
    "feature": "Assess whether the capability solves an active use case; prototype in a non-production environment.",
    "bugfix": "Check whether the affected bug exists in your deployed version and whether the fix warrants an upgrade.",
}
def evidence(text, patterns):
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            start, end = max(0, m.start()-75), min(len(text), m.end()+115)
            return re.sub(r"\\s+", " ", text[start:end]).strip()
    return None

result = {}
for item in items:
    text = f"{item.get('title','')} {item.get('summary','')}"
    tags, excerpts = [], []
    for key, label, priority, patterns in RULES:
        snippet = evidence(text, patterns)
        if snippet:
            tags.append({"id": key, "label": label, "priority": priority})
            if len(excerpts) < 4:
                excerpts.append({"theme": label, "text": snippet})
    priorities = [x["priority"] for x in tags]
    priority = "high" if "high" in priorities else ("medium" if "medium" in priorities else "low")
    actions = [ACTIONS[x["id"]] for x in tags if x["id"] in ACTIONS][:4]
    if not actions:
        actions = ["Open the primary source and decide whether the change affects a component or workflow you operate."]
    if priority == "high":
        why = "The source text contains explicit security or breaking-change language. Verify applicability before taking action."
    elif priority == "medium":
        why = "The source text suggests a compatibility, lifecycle, performance, or configuration consideration worth checking against your deployment."
    else:
        why = "No explicit high-risk language was detected. Treat this as an awareness item until the primary source shows a concrete operational impact."
    result[item.get("id", item.get("url",""))] = {
        "priority": priority,
        "themes": tags,
        "why_it_matters": why,
        "review_actions": actions,
        "evidence": excerpts,
        "confidence": "rule-based: explicit phrase match" if tags else "rule-based: no risk phrase matched",
        "method": "heuristic"
    }
out = {
    "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    "method": "transparent-rule-based-triage",
    "disclaimer": "Heuristic triage of source text, not AI editorial verification. Priority is an attention cue, not product severity. Confirm all impact and applicability in the primary source.",
    "item_count": len(result),
    "items": result
}
(ROOT / "data/intelligence.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(f"Triaged {len(result)} signals")
