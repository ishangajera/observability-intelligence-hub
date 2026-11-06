# Signal Desk — Observability Intelligence Hub

Public, automatically refreshed observability engineering intelligence dashboard.

## Coverage
- Upstream releases across Prometheus, OpenTelemetry, Grafana, Loki, Tempo, Mimir, Alloy, VictoriaMetrics, Thanos, Jaeger, Fluent Bit, Vector, Cilium, OpenSearch and related projects.
- OpenTelemetry Collector core, contrib, distribution, and operator releases.
- New Collector receivers, processors, exporters, connectors, and extensions identified in release-note sections.
- Technical articles, blog posts, product updates, and security bulletins from Prometheus, OpenTelemetry, Grafana Labs, CNCF, Datadog, New Relic, Honeycomb, Elastic, VictoriaMetrics, Isovalent/Cilium, and Splunk.
- Grafana plugin-development community announcements, plus daily catalog-diff detection for newly listed plugins and version changes.
- The public Grafana plugin catalog, with a daily baseline and subsequent new-plugin/version-change detection.
- Videos from the official OpenTelemetry and CNCF YouTube channels.

## Editorial triage
This is a focused review queue, not a duplicate feed. It shows only releases, component additions, plugin changes, and security advisories with explicit source-text matches, with item-specific matched themes, source excerpts, and theme-specific review actions. Articles, videos, and community discussions remain in the main feed. Priority is an attention cue, not product severity or verified deployment impact.

## Release parsing
GitHub release entries retain a bounded raw release-note excerpt and a parsed heading/bullet outline; the primary-source link opens the complete upstream notes. For OpenTelemetry Collector releases, the collector looks for component paths under receiver/, processor/, exporter/, connector/, and extension/, especially in sections labelled as new components. Detected additions are surfaced as separate signals linked to the parent release. This is best-effort parsing; confirm each result in the upstream notes.

## Collection
The daily GitHub Actions workflow runs scripts/collect.py and scripts/enrich.py, updates data/updates.json, data/meta.json, and data/intelligence.json, then deploys GitHub Pages. RSS/Atom sources, GitHub releases, community posts, and videos are public. No LLM, external AI API, credentials, or private repository data are used. Feed/API errors are logged in workflow output; one failed source does not stop the others.
