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
The daily GitHub Actions workflow runs scripts/collect.py, scripts/collect_capabilities.py, and scripts/enrich.py, updates the public archive and editorial index, then deploys GitHub Pages. Sources are public. The workflow uses GitHub's built-in GITHUB_TOKEN for public API access/rate limits; it does not access private repository data or call an external AI API. Feed/API errors are logged in workflow output; one failed source does not stop the others.

 
## Capability inventories
- Prometheus feature flags are collected from the official feature-flag documentation, including the `memory-snapshot-on-shutdown` flag (a startup-time optimization enabled at shutdown to accelerate subsequent startup).
- Deckhouse Prom++ is tracked as its own upstream GitHub project and release stream, in addition to the Deckhouse module release notes.
- OpenTelemetry Collector core and contrib component inventories and declarative `feature_gates` from `metadata.yaml` are captured for the pinned `v0.145.0` source ref and current `main`. This surfaces processors, receivers, exporters, connectors, extensions, and per-component gates even when they are not mentioned in the newest release notes.
- Component inventory is not a claim that a component ships in every distribution or is enabled at runtime. Review component stability, signal support, distribution manifests, configuration and gate lifecycle in the linked upstream metadata. Alpha gates are generally disabled by default; beta gates are generally enabled by default but can still be overridden; stable gates should no longer be explicitly configured. Presence in source does not prove inclusion in a specific distribution or activation in a running Collector.
