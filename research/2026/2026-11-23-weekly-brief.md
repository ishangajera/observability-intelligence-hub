# Weekly Observability Intelligence Brief — 2026-11-23

**Reporting window:** 2026-11-16 through 2026-11-23  
**Research cutoff:** 2026-11-23 10:05 PT  
**Tags:** #weekly-brief #release-notes #security #licensing #pricing #prometheus #opentelemetry #collector #semantic-conventions #grafana #loki #mimir #alloy #victoriametrics #vector #cilium #splunk #elastic #tool-discovery #ai-observability

## Executive summary

1. **OpenTelemetry Collector security deserves immediate attention.** Three advisories published Nov 18–19 affect optional but realistic Collector configurations. The critical OpAMP Supervisor issue is fixed in 0.165.0; the YANG gRPC receiver issue is fixed in 0.163.0; the high-severity zstd decoder allocation issue is fixed in 0.165.0. The example v0.145.0 baseline falls inside the affected ranges for the zstd, OpAMP Supervisor and YANG issues, subject to each advisory's configuration conditions.
2. **Elastic is moving further into AI observability.** On Nov 19 it announced an agreement to acquire HoneyHive. On Nov 23, Elasticsearch 9.6 brought GA PromQL support to Elastic Cloud Serverless, with vendor-reported coverage of 92% of the top 100 Grafana dashboard queries, and a technical preview of querying Amazon S3 data in place.
3. **Splunk's new Observability Cloud packaging now has public list prices.** Essentials is $95/host/month and Premier is $150/host/month, with a 30-host minimum for paid editions. The free edition covers up to 15 hosts.
4. **VictoriaMetrics 1.157.0 and Cilium maintenance releases landed.** VictoriaMetrics adds safer alert query timeouts, resumable migrations and partial restores. Cilium fixes an Hubble URL-query redaction edge case across supported branches.
5. **Vector has an imminent packaging action.** Its APT/YUM repository signing key changes on Nov 30. Update package-manager trust before that date.
6. **AI-agent observability continues to diversify.** DataCat is a new Apache-2.0 self-hosted project; three.dev is a commercial live-traffic evaluation/observability service; Kwatch has relaunched with a root-cause-focused v1.2.0; and a Grafana community plugin now correlates Claude Code metrics, logs and traces.
7. **Prometheus has no new stable release, but upstream main has grown.** The v3.16.0 documentation has 27 unique feature flags; current main has 31. Four are main-only, including a new metadata-default-time-range flag. Prometheus v3.17's first pre-release is scheduled for Dec 2.

## 1. Releases, security and engineering changes

### 1.1 OpenTelemetry Collector security advisories — Nov 18–19

**Project:** OpenTelemetry Collector core and contrib  
**Status:** Published security advisories; fixes available in released versions.

| Advisory | Severity | Affected range | Fixed in | Operational condition |
|---|---|---|---|---|
| [GHSA-vf52-ppm4-c35w](https://github.com/open-telemetry/opentelemetry-collector/security/advisories/GHSA-vf52-ppm4-c35w) | High, CVSS 7.5 | Collector config modules below 1.71.0 | Collector v0.165.0 | OTLP/HTTP or OTLP/gRPC receiver path using confighttp/configgrpc and zstd |
| [GHSA-c35f-chp7-9chr](https://github.com/open-telemetry/opentelemetry-collector-contrib/security/advisories/GHSA-c35f-chp7-9chr) | Critical, CVSS 9.2 | contrib v0.119.0 to before v0.165.0 | v0.165.0 | OpAMP Supervisor only; accepts_opamp_connection_settings must be true |
| [GHSA-6qvg-78vr-vgm7](https://github.com/open-telemetry/opentelemetry-collector-contrib/security/advisories/GHSA-6qvg-78vr-vgm7) | Moderate, CVSS 5.3 | contrib v0.142.0 to before v0.163.0 | v0.163.0 | yang_grpc receiver, configured allowlist/rate limits, and endpoint reachable by untrusted clients |
| [GHSA-cx3c-rmcx-ff35](https://github.com/open-telemetry/opentelemetry-collector/security/advisories/GHSA-cx3c-rmcx-ff35) | Moderate, CVSS 5.9 | Collector v0.147.0 to before v0.164.0 | v0.164.0 | Exporter queue batching with two or more metadata partition keys, receiver include_metadata=true, and client-controlled multi-valued metadata |

**Zstd memory-exhaustion issue.** A tiny compressed request can declare a very large decoder history window and cause an allocation of roughly 512 MiB before normal request-size limits or pipeline processors run. The advisory says gRPC can be exploited without credentials, even when receiver authentication is configured; HTTP exposure depends on the authentication path. The memory_limiter processor is not a mitigation because decompression occurs before the pipeline. Upgrade to v0.165.0 or later. If an immediate HTTP upgrade is impossible, remove zstd from accepted compression algorithms; for gRPC, restrict the receiver behind a trusted proxy/network boundary that rejects zstd. Keep request limits sensible after upgrading.

**OpAMP Supervisor TLS issue.** The Supervisor could disable server certificate verification after receiving connection settings without a certificate field. An attacker able to intercept or redirect its next connection could impersonate the OpAMP server and obtain Supervisor credentials; if remote configuration is also enabled, the attacker could control the managed Collector configuration. The vulnerable range includes v0.145.0, but the advisory requires the OpAMP Supervisor, HTTPS/WSS, and accepts_opamp_connection_settings=true (false by default). The Collector's opamp extension is not affected. Upgrade the Supervisor to v0.165.0 or later; until then, leave accepts_opamp_connection_settings=false and accepts_remote_config=false.

**YANG gRPC receiver issue.** The streaming RPC bypassed the configured allowed-clients and rate-limit checks because only a unary interceptor was registered. v0.145.0 is in the affected range, but the default endpoint is loopback-only. If using this receiver, keep it on loopback/trusted management networks, use mTLS/network controls and upgrade to v0.163.0 or later.

**Partition-key collision issue.** This is not a v0.145.0 exposure: the affected partitioning implementation was introduced in v0.147.0. It matters for later versions that use exporter queue batching with metadata partitioning. The issue can mix telemetry across tenants by assigning distinct metadata sets to the same batch partition. Upgrade to v0.164.0 or later.

Latest verified release baselines remain Collector core v0.165.0 (Nov 6) and contrib v0.165.1 (Nov 9); no newer stable Collector release was found in this reporting window. Sources: [core v0.165.0](https://github.com/open-telemetry/opentelemetry-collector/releases/tag/v0.165.0) · [contrib v0.165.1](https://github.com/open-telemetry/opentelemetry-collector-contrib/releases/tag/v0.165.1).

### 1.2 Grafana Mimir 3.2.6 — Nov 18

**Status:** Released maintenance/security patch.  
**Primary source:** [Mimir 3.2.6 release](https://github.com/grafana/mimir/releases/tag/mimir-3.2.6)

The release updates:
- Go to 1.26.11 for CVE-2026-97054.
- klauspost/compress to 1.20.2 for CVE-2026-116591.
- OpenTelemetry libraries to 1.47.0 for CVE-2026-81871, CVE-2026-81872 and CVE-2026-128085.

This is a dependency/security patch rather than a new Mimir feature. Update maintained 3.2.x deployments and check the equivalent patch for other supported branches.

### 1.3 Grafana Loki 3.6.22 — Nov 17

**Status:** Released patch.  
**Primary source:** [Loki 3.6.22](https://github.com/grafana/loki/releases/tag/v3.6.22)

Two changes:
- Prevent a goroutine leak in the downstreamer when context cancellation occurs.
- Update go.opentelemetry.io/otel/sdk/log to address a medium-severity security issue.

Patch maintained 3.6.x deployments. No new Loki 4 GA release was verified; the 4.0 line remains a pre-release track.

### 1.4 Cilium/Hubble patch releases — Nov 17

**Versions:** v1.20.5, v1.19.11 and v1.18.17  
**Primary sources:** [v1.20.5](https://github.com/cilium/cilium/releases/tag/v1.20.5) · [v1.19.11](https://github.com/cilium/cilium/releases/tag/v1.19.11) · [v1.18.17](https://github.com/cilium/cilium/releases/tag/v1.18.17)

The observability-relevant fix addresses Hubble HTTP URL-query redaction when an Envoy access-log URL cannot be parsed. In that edge case, query data could be folded into the path and escape the configured redaction. The fix preserves the query separately so redaction can remove it.

Important operational detail: this only helps when Hubble redaction is configured; Cilium documentation warns that sensitive Layer 7 information is not redacted by default. Review --hubble-redact-enabled and --hubble-redact-http-urlquery, especially where Hubble flows leave the cluster.

v1.20.5 also adds load-balancer ID-allocator capacity/utilization metrics. The release includes security fixes beyond observability; review the full branch-specific notes before patching.

### 1.5 VictoriaMetrics 1.157.0 — release dated Nov 20; GitHub publication Nov 23

**Status:** Released.  
**Primary source:** [VictoriaMetrics v1.157.0](https://github.com/VictoriaMetrics/VictoriaMetrics/releases/tag/v1.157.0)

Notable changes:
- vmalert gains a datasource query-timeout control, limiting the effect of a stalled datasource query on alert evaluation.
- vmctl can resume interrupted migrations.
- vmrestore supports partial restores by time range/partition selection; validate restore scope carefully before using it on production data.
- Stream-aggregation reloads can preserve state for unchanged configurations while restarting only changed configurations.
- vmselect accepts lookback_delta as a Prometheus-compatible query parameter alias.
- Review vmctl invocation changes and service-discovery configuration renames in the release notes before upgrading.

No new Enterprise price was announced in this release. The prior v1.156.0 EULA-acceptance flag change remains a packaging item to carry forward.

### 1.6 Vector package repository key — action due Nov 30

**Project:** Vector  
**Status:** Upcoming package-signing change.  
**Primary source:** [Vector 0.62.0 release/upgrade notes](https://vector.dev/releases/0.62.0/)

Vector's APT/YUM package repositories are changing signing keys on Nov 30. Update repository trust configuration before the rotation or package installation/upgrade may fail. Vector 0.62.0 itself was already covered in the Nov 16 brief; this is a new operational deadline, not a new Vector release.

### 1.7 Other tracked release status

No new stable release was verified in this window for Prometheus, Grafana core, Tempo, Alloy, Thanos, Jaeger, Fluent Bit or OpenTelemetry Semantic Conventions. Carry-forward baselines:
- Prometheus 3.16.0.
- Grafana 13.3.1.
- Tempo 3.1.1.
- Alloy 1.22.0 (released Nov 12; embeds Collector contrib 0.164.1).
- Thanos 0.42.5.
- Jaeger 2.23.0.
- Fluent Bit 5.2.0.
- Vector 0.62.0.
- Semantic Conventions 1.45.0.

No material product/pricing change was verified this week for Datadog, New Relic, Chronosphere or Honeycomb. HoneyHive is a separate company/product from Honeycomb.

## 2. Vendor strategy, product and pricing changes

### 2.1 Elastic agrees to acquire HoneyHive — Nov 19

**Status:** Acquisition agreement announced; not represented as closed.  
**Primary source:** [Elastic and HoneyHive join forces](https://www.elastic.co/blog/elastic-and-honeyhive)

Elastic announced an agreement to acquire HoneyHive, an AI observability and evaluation platform. HoneyHive provides tracing for complex agent workflows plus offline evaluation, experimentation and production monitoring/evaluation. Elastic says it intends to support existing HoneyHive customers while integrating the technology with Elastic Observability.

No purchase price, closing date or final consolidated product roadmap was disclosed. The strategic direction is clear, but integration timing and packaging remain unknown.

### 2.2 Elasticsearch 9.6 — Nov 23

**Status:** Capabilities available in Elastic Cloud Serverless; ECH and self-managed 9.6 expected in early December.  
**Primary source:** [Elasticsearch 9.6: S3 queries and 92% PromQL coverage](https://www.elastic.co/search-labs/blog/elasticsearch-9-6-whats-new)

Observability-relevant changes:

- **PromQL is GA** in the 9.6 serverless release. Elastic reports coverage of about 92% of queries used by the top 100 Grafana dashboards, up from 43.4% in 9.4. This is a vendor benchmark against a defined dashboard set, not a claim of full PromQL parity. Validate the PromQL features and query semantics used by your own dashboards.
- **ES|QL Data Federation for Amazon S3 is technical preview.** It can query Parquet, CSV, TSV and NDJSON files in place, with partition/folder pruning and Kibana time-picker integration. It is Enterprise-subscription-only and initially limited to stateful Elastic Cloud Hosted and self-managed deployments; Serverless support is listed as coming.
- **Logical Views, LOOKUP JOIN and subqueries** are GA, improving query reuse and cross-project analysis.

Operational implication: test PromQL dashboard parity with real queries before treating Elasticsearch as a drop-in Prometheus query backend. Treat S3 federation as a preview, not a production replacement for an established archive/query path.

### 2.3 Splunk Observability Cloud packaging and public prices

**Status:** Public list pricing is now visible.  
**Primary source:** [Splunk Observability Cloud pricing](https://www.splunk.com/en_us/products/pricing.html)

| Edition | Public list price | Important entitlements |
|---|---:|---|
| Free | $0; up to 15 hosts | Limited free edition |
| Essentials | $95/host/month | APM, infrastructure monitoring, AI SRE, Observability Logs (0.5 GB/day/host, 15-day retention), Agent Observability (5,000 spans/month) |
| Premier | $150/host/month | Essentials plus RUM, synthetics, Digital Experience Analytics, DB Monitoring/App Security, more Agent Observability (20,000 spans/month), Observability Logs (1 GB/day/host, 15-day retention) |

Paid editions have a 30-host minimum. Enterprise rates, volume discounts and premium support are separate commercial considerations; do not multiply the per-host list price without checking the actual host count, contract term, included data and overages.

Recent release-note additions include database-monitoring AI Assistant availability and an IBM Db2 scraper update on Nov 20. Earlier November updates added span analysis/operation-rule capabilities and expanded AI Assistant access for selected customers. Availability can vary by controlled/limited-availability status. Source: [Splunk Observability Cloud November release notes](https://help.splunk.com/en/splunk-observability-cloud/release-notes/november-2026).

### 2.4 Grafana plugin: Claude Code Stats 2.0.2 — Nov 20

**Status:** Community app plugin update; Apache-2.0.  
**Primary sources:** [Plugin documentation](https://grafana.com/grafana/plugins/timurdigital-claudestats-app/docs/) · [Repository](https://github.com/tolzhabayev/claudestats-app-grafana)

The plugin now covers Claude Code metrics, OpenTelemetry log events and traces across Overview, Costs, Tokens, Tools, Productivity, Prompts, Workflow, Reliability, Security and Traces views.

Requirements:
- Grafana 13.2.0 or later.
- Prometheus-compatible datasource (Prometheus or Mimir) for metrics.
- Loki for event-based views.
- Tempo for traces.
- Claude Code telemetry enabled and exported over OTLP.

The plugin can use a Collector-to-Prometheus path or direct OTLP to Grafana Cloud/Mimir. Prompt text, tool input and output remain redacted unless explicit environment settings enable them. Claude Code tracing itself is documented as beta, so do not assume stable span names/attributes.

This is a useful emerging example of AI coding-agent usage observability built on the existing Prometheus/Loki/Tempo stack. It is not a Grafana core feature.

## 3. OpenTelemetry governance, proposals and roadmap

### 3.1 OpenTelemetry blog policy update — Nov 17

**Status:** Project communication policy change.  
**Primary source:** [Updates to our blog policy](https://opentelemetry.io/blog/2026/blog-policy-update/)

The project now requires blog authors to be members in good standing of the OpenTelemetry organization and will strongly prefer project/organizational announcements, releases, milestones and SIG updates. The stated rationale is a shift in how users consume documentation, plus the review burden of lower-signal posts.

Monitoring implication: do not treat a quieter project blog as evidence of less engineering activity. Increase coverage of specification PRs, SIG notes, release notes, docs changes and GitHub discussions.

### 3.2 Active Semantic Conventions proposals

These are proposals/PRs, not released conventions:

- [PR #4336 — otel.span.duration](https://github.com/open-telemetry/semantic-conventions/pull/4336): proposes a standard span-derived duration metric. If accepted, it could make span-to-metric derivation more interoperable across SDKs and backends.
- [PR #4356 — Kubernetes pod volume metrics](https://github.com/open-telemetry/semantic-conventions/pull/4356): proposes advancing pod-volume metrics to Release Candidate status.
- [PR #4337 — browser conventions/client-side registry](https://github.com/open-telemetry/semantic-conventions/pull/4337): proposes moving browser-specific conventions toward a client-side registry model. Watch for implications to browser instrumentation and convention ownership.

The latest verified released semantic-conventions package remains 1.45.0; no 1.46.0 release was verified in this window.

### 3.3 Collector stability-by-default proposal

**Status:** Open proposal, not merged.  
**Primary source:** [Collector PR #16414](https://github.com/open-telemetry/opentelemetry-collector/pull/16414)

The proposal discusses making stable components the default surface and requiring explicit opt-in for less-stable components/features. This could improve default stability for broad distributions but would make custom distributions and component enablement more important. Treat this as a design proposal, not current runtime behavior.

### 3.4 Batch processor deprecation — carry-forward

The Nov 11 announcement remains operationally important ([migration guide](https://opentelemetry.io/blog/2026/collector-batching-migration/)):
- Exporter-level queue/batching becomes the default for most exporters in Collector 0.171.0 (planned February 2027).
- The old Batch processor is planned for removal in 0.177.0 (planned May 2027).

Do not remove the processor immediately without testing exporter queue/batch behavior, memory use, throughput, retry semantics and signal-specific pipeline behavior. The replacement path is not a one-line config rename.

## 4. Capability gaps, feature flags and components

### 4.1 Prometheus feature flags

**Latest stable release:** v3.16.0.  
**Deployment version:** unknown.  
**Sources:** [v3.16.0 feature flags](https://github.com/prometheus/prometheus/blob/v3.16.0/docs/feature_flags.md) · [current main feature flags](https://github.com/prometheus/prometheus/blob/main/docs/feature_flags.md) · [release schedule](https://github.com/prometheus/prometheus/blob/main/RELEASE.md)

- v3.16.0 documentation: 27 unique flags.
- Current main documentation: 31 unique flags.
- Four current-main-only flags are not in the v3.16.0 release documentation:
  - auto-recording-metadata
  - metadata-default-time-range
  - metadata-relabeling
  - promql-native-histograms-as-classic

The newly surfaced metadata-default-time-range flag changes the default time range for metadata API endpoints when callers omit one (documented as one hour). It is not in v3.16.0; do not assume it exists in a released binary yet.

Other main-only flags remain upgrade candidates, not released capabilities. The v3.16.0 flags query-cost and promql-unquoted-utf8-names are opt-in. Query-cost is worth piloting for multi-team query governance; compare estimated and actual query costs before setting limits.

**Older opt-in capability:** memory-snapshot-on-shutdown is documented in v2.30.0, absent in v2.29.0, and still present in v3.16.0. It is disabled by default. Operators on older supported versions that include it can evaluate it without upgrading to 3.16, but should test shutdown/startup behavior and snapshot persistence.

Carry-forward lifecycle notes:
- extra-scrape-metrics is deprecated.
- promql-extended-range-selectors is a no-op after selector behavior stabilized.
- Prometheus v3.17 first pre-release is scheduled for Dec 2, 2026; that is a planned pre-release date, not a claim that v3.17 is already available.

### 4.2 OpenTelemetry Collector component and gate inventory

**Reference baseline:** v0.145.0, as requested. This is an audit baseline, not a claim about the version deployed in your environment.

The last full metadata-class inventory (Nov 16) recorded 252 baseline entries and 298 current-main entries:
- Current main: 119 receivers, 46 processors, 54 exporters, 17 connectors and 62 extensions.
- The count is metadata-class inventory, not a count of components shipped in every distro or enabled at runtime.
- A fresh tree diff through Nov 23 found no new or removed runnable component metadata paths since Nov 16. One new abstract/internal transform-processor metadata path appeared; it is not a new runnable processor.
- Existing metadata files changed in core configuration/OTLP receiver and contrib components including Prometheus receiver, filelog, Kafka, Kubernetes attributes, transform, probabilistic sampling, signing, SQL Server, SNMP and several exporters/extensions. A complete field-by-field parse of every changed metadata blob was not completed this run; treat those as review targets, not asserted behavior changes.

**Feature-gate inventory caveat:** the last complete current-main census remains 139 records from Nov 8; it was not fully recounted on Nov 23. The v0.145.0 baseline has 18 gate records: 8 alpha, 5 beta, 4 stable and 1 deprecated. The current-main count is therefore a dated snapshot, not a new Nov 23 total.

Verified gate examples:
- pkg.exporterhelper.queueBatchEnabled: alpha from v0.158.0, disabled/opt-in.
- pkg.confighttp.PrioritizeNewKeepalive: stable from v0.162.0 through v0.166.0.
- pkg.configmiddleware.CustomTCPRouting: alpha from v0.164.0, disabled/opt-in.

Component maturity examples:
- queue_batch processor: beta for traces, metrics and logs; alpha for profiles. Verify the exact distribution/builder you ship rather than assuming every vendor distro includes it.
- redis_fleet_tracker extension: development stage; no distribution inclusion declared in its metadata.
- Components present in source are not automatically present in a custom/vendor binary or enabled in runtime configuration.

### 4.3 Grafana compatibility

Actual deployed Grafana version is unknown. Latest verified stable tag remains 13.3.1. Grafana's current configuration documentation marks the Plugin Frontend Sandbox deprecated and says it will be removed in 13.4. Review plugins that depend on the sandbox before upgrading to 13.4. The Claude Code Stats plugin requires Grafana >=13.2.0 and separate Loki/Tempo datasources for event/trace views.

## 5. New tools and products discovered

First-seen date below means first observed in this research run (Nov 23); it is not necessarily the original launch date.

| Candidate | First seen / original launch | Model / license | Maturity and evidence |
|---|---|---|---|
| DataCat | First seen Nov 23; public announcement Nov 17 | Open source; Apache-2.0 | New self-hosted observability project; no tagged release found |
| three.dev | First seen Nov 23; GA announcement Nov 10 | Commercial SaaS; no OSS license identified | Live AI-agent traffic scoring, failure-mode grouping, MCP and replay/experiments |
| kwatch | First seen Nov 23; Product Hunt relaunch Nov 18; original launch Jan 25, 2022 | Source-available ELv2; Community free, Pro free during early access | v1.2.0 rebuild around dependency-aware root-cause alerts |
| Radar | First seen Nov 23; original product launch predates this window | License not re-verified in this run | Existing Kubernetes UI/tool; v1.21.0–v1.21.2 shipped during the window |
| Claude Code Stats | First seen Nov 23; plugin update Nov 20 | Apache-2.0 community Grafana app | Plugin v2.0.2; Grafana >=13.2.0; metrics/logs/traces across Prometheus/Mimir, Loki and Tempo |

### DataCat — new launch, Nov 17

**Primary sources:** [Replit announcement](https://replit.com/blog/introducing-replit-missions) · [repository](https://github.com/replit/datacat)

DataCat is a self-hosted observability application with a public Apache-2.0 repository. The announcement describes Datadog Agent-compatible intake and OTLP/HTTP, with PostgreSQL or ClickHouse storage options. It has no tagged release at the time of this audit, so classify it as an early project, not a production-ready replacement.

Replit reports 38-second detection of a deliberately introduced database fault against a 60-second target, 26 million activity records plus 4.4 million log entries over three hours with zero reported loss, and 51/51 correctness/reliability checks. It also reports 49,000 traces/s and 405,100 metric points/s with PostgreSQL. These are vendor-reported controlled tests; Replit explicitly says they do not establish performance against the original hosted platform or on its production systems. Treat them as a project demonstration, not an independent benchmark.

### three.dev — newly discovered existing product

**Primary sources:** [product site](https://three.dev/) · [launch/GA announcement](https://three.dev/blog) · [pricing](https://three.dev/pricing)

Original GA announcement: Nov 10, outside the Nov 16–23 reporting window; first discovered in this run. It proxies live AI application traffic, scores requests, groups failures by root cause, and exposes failure context to coding agents over MCP. It also supports replay and experiments.

~~~mermaid
flowchart LR
  A[AI application] --> P[three.dev proxy]
  P --> M[Model provider]
  P --> E[Evaluation and scoring]
  E --> F[Failure modes and replay]
  F --> X[MCP handoff]
  X --> C[Coding agent]
  C --> A
~~~

This is the vendor-described flow; validate the data fields and network path before routing production traffic.

Public list pricing at the time of this run:
- Free: $0/month, 1 GB data, 5,000 scored requests and 30 days of history.
- Starter: $79/month, 5 GB data, 10,000 scored requests and 90 days of history.
- Pro: $249/month, 20 GB data, 25,000 scored requests and 180 days of history.
- Enterprise: custom.

Overages are charged by data volume and scored requests. A six-month Starter launch offer applied to signups Nov 9–22 with a first request within a week; that offer window had ended by the Nov 23 cutoff. Review the privacy/security terms before routing production conversations through a proxy; the vendor states it does not train on customer traffic.

### kwatch — relaunch, not a new codebase

**Primary sources:** [Product Hunt listing](https://www.producthunt.com/products/kwatch) · [official pricing/Pro page](https://kwatch.dev/pro) · [repository](https://github.com/abahmed/kwatch)

Product Hunt lists a new launch this week, but the product itself launched in 2022. The v1.2.0 rebuild focuses on grouping symptoms into one likely cause and showing what changed, who changed it, affected services and next actions.

The current Community edition is free forever. Pro is free during early access for three months per license, with up to two licenses per account/company and no payment details. Post-early-access pricing is not published. Current source is ELv2; an older v1.0.0-rc.10 tag was MIT, so organizations should review the license history before adopting or redistributing older/newer versions.

### Radar — existing tool with a new release train

**Primary source:** [Radar releases](https://github.com/skyhook-io/radar/releases)

Versions 1.21.0, 1.21.1 and 1.21.2 landed Nov 19–23. The changes include Kubernetes graph/relationship architecture work, additional troubleshooting views and fixes for metrics polling when switching clusters. This is an existing project, not a new launch.

### Early GitHub discovery leads — not promoted to the permanent watchlist

These repositories were surfaced by date-filtered GitHub searches. No release tags or independent launch evidence were found; first-seen date is Nov 23 and original launch date is unknown.

| Repository | Relationship | License | Status |
|---|---|---|---|
| [CeyNox Watch](https://github.com/CeyNova-Labs/ceynox-watch) | eBPF/system-call and process observation | Apache-2.0 | New repository; no release tag found |
| [blame](https://github.com/Erio-Harrison/blame) | eBPF request-level latency profiler | GPL-2.0 | Early repository; no release tag found |
| [agent-eye](https://github.com/developjik/agent-eye) | AI browser-agent profiling | MIT | Early repository; no release tag found |
| [mint_otlp](https://github.com/dashbitco/mint_otlp) | Elixir OTLP client/instrumentation library | Apache-2.0 | Early library; no release tag found |
| [flask-lens](https://github.com/duhanguler/flask-lens) | Flask development profiling | MIT | Early repository; no release tag found |
| [reqray](https://github.com/reqray/reqray) | Node.js request inspection | MIT | Early repository; no release tag found |
| [ai-observability-bundle](https://github.com/quentinRogeret34/ai-observability-bundle) | Symfony AI instrumentation | No license verified | Early repository; do not assume reusable licensing |

Superlog also appeared in Product Hunt's recent-launch surface, but it was already discovered in the prior archive and its original launch predates this week. It is deduplicated, not counted as a new product.

## 6. Impact and severity assessment

| Priority | Item | Why it matters | Suggested response |
|---|---|---|---|
| Critical | OpAMP Supervisor TLS verification GHSA | Potential credential disclosure and remote Collector config takeover | Inventory Supervisor usage/config; upgrade to v0.165.0+ |
| High | Collector zstd decoder allocation | Remote memory-exhaustion DoS on reachable OTLP receiver paths | Upgrade to v0.165.0+ or apply the documented mitigations |
| High | Mimir 3.2.6 and Loki 3.6.22 | Security dependency updates | Patch maintained branches |
| Medium | YANG gRPC receiver authorization/rate-limit bypass | Intended streaming-RPC controls were not enforced | Upgrade to v0.163.0+ or isolate/disable receiver |
| Medium | Partition-key collision | Cross-tenant telemetry misattribution in later Collector versions | Verify partitioned queue configuration; upgrade to v0.164.0+ |
| Medium | Cilium Hubble redaction edge case | Sensitive URL query data could escape redaction in a parsing edge case | Patch Cilium and enable the relevant redaction settings |
| Medium | Splunk packaging/pricing | Host minimum and edition entitlements materially affect cost | Model actual host count, log volume and agent spans |
| Medium | Vector repository key rotation | Package updates may fail after Nov 30 if trust is not updated | Rotate APT/YUM key before deadline |
| Medium | Elastic PromQL/S3 preview | Potential backend/query architecture option, but bounded compatibility and preview status | Pilot against real dashboards; keep preview data paths non-critical |
| Low–Medium | New AI observability tools | New options for agent behavior, evaluation and usage telemetry | Evaluate with privacy, data residency and maturity gates |

## 7. Upcoming watchlist

| Date / horizon | Watch item |
|---|---|
| Nov 30, 2026 | Vector APT/YUM repository signing-key rotation |
| Dec 2, 2026 | Prometheus v3.17 first pre-release target |
| Early Dec 2026 | Elastic 9.6 expected for Elastic Cloud Hosted and self-managed |
| Grafana 13.4 | Planned removal of the Plugin Frontend Sandbox |
| Collector 0.171.0, planned Feb 2027 | Exporter-level queue/batching becomes default for most exporters |
| Collector 0.177.0, planned May 2027 | Batch processor removal target |
| Next Semantic Conventions releases | PR #4336 span-duration metric, #4356 Kubernetes volume metrics, #4337 browser-convention ownership |
| Collector governance | Stable-by-default proposal #16414 |
| Cilium 1.21 | Watch for a stable release and Hubble changes |

## 8. What an observability engineering leader should do

1. **Run a Collector security inventory now.** Identify exact versions and whether any deployment uses OTLP/gRPC or OTLP/HTTP with zstd, OpAMP Supervisor connection-settings capability, or the YANG gRPC receiver. v0.145.0 is not a safe assumption for those configurations.
2. **Check Alloy separately.** Alloy 1.22.0 embeds Collector contrib 0.164.1; verify whether the zstd fix from core 0.165.0 was backported before exposing its OTLP receiver to untrusted networks.
3. **Prepare Vector package repositories before Nov 30.** Update signing-key trust in base images and package automation, not only on one host.
4. **Model Splunk costs against actual host/data usage.** Include the 30-host minimum, log allowances, retention, Agent Observability spans and overages.
5. **Pilot Elastic PromQL against your own dashboards.** The 92% claim is a defined vendor test, not full PromQL compatibility. Keep S3 federation in preview-only workflows until maturity and support are clear.
6. **Test VictoriaMetrics 1.157.0 restore and migration paths.** Exercise vmctl resume, partial restore boundaries and stream-aggregation reloads in staging.
7. **Patch Cilium and confirm Hubble redaction settings.** The fix does not turn redaction on automatically.
8. **Treat AI-agent telemetry as a distinct data-governance problem.** Decide which prompt/tool fields may be collected, who can see them, retention and whether payloads leave your environment before piloting three.dev, DataCat or Claude Code Stats.
9. **Plan for Grafana 13.4 plugin compatibility.** Inventory plugins that depend on the frontend sandbox.

## 9. Source health and monitoring blind spots

- **GitHub releases/advisories:** official release and advisory pages were accessible; GitHub API was used to verify several tags where the rendered release page was incomplete.
- **OpenTelemetry blog:** the Nov 17 policy change means fewer individual/community posts may appear. Monitor documentation, SIG updates, specification PRs and release metadata rather than relying on blog volume.
- **OpenTelemetry Registry:** remains frozen for new submissions/updates; use the Ecosystem Explorer, repository searches and vendor catalogs as complementary sources.
- **Product Hunt:** the observability category surfaced kwatch, superlog and three.dev. Kwatch is a relaunch of a 2022 project; superlog was already in the archive; three.dev's GA date is Nov 10, not this week's. Do not count repeated listings as new launches.
- **Hacker News:** search-engine-indexed queries did not produce a high-confidence new observability launch. Direct Algolia feed coverage was not confirmed in this run.
- **CNCF Landscape:** no new observability-specific entry was verified in the available search; a complete YAML-level landscape diff was not completed, so this is not proof of no additions.
- **Grafana plugin catalog:** the Claude Code Stats documentation shows v2.0.2 and a Nov 20 update, while older catalog/install pages still expose stale v1.1.0 metadata. Prefer the current documentation/repository and verify plugin signature/version during installation.
- **Deployment versions:** Prometheus and Grafana deployed versions remain unknown. Collector v0.145.0 is only the requested audit reference.

## Archive record

This report and its capability/discovery snapshots are indexed in the Signal Desk repository:
- [2026-11-23 weekly brief](2026/2026-11-23-weekly-brief.md)
- [Prometheus feature flags](2026-11-23-prometheus-feature-flags.json)
- [Collector capability delta](2026-11-23-collector-capability-delta.json)
- [New tool discovery snapshot](2026-11-23-discovery-candidates.json)

Stable tags: #weekly-brief #release-notes #security #licensing #pricing #capability-audit #feature-gates #tool-discovery #semantic-conventions #ai-observability
