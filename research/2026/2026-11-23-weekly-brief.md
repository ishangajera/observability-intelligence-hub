# Weekly Observability Intelligence Brief — 2026-11-23

**Reporting window:** 2026-11-16 through 2026-11-23  
**Research cutoff:** 2026-11-23 10:33 PT  
**Tags:** #weekly-brief #release-notes #security #licensing #pricing #prometheus #opentelemetry #collector #semantic-conventions #grafana #loki #mimir #alloy #victoriametrics #vector #cilium #splunk #elastic #tool-discovery #ai-observability

## Executive summary

1. **Collector security remains the highest-priority open-source issue.** Four relevant advisories span Nov 12–19: zstd decoder memory exhaustion and metadata-partition collisions (Nov 12), YANG gRPC authorization/rate-limit bypass (Nov 18), and critical OpAMP Supervisor TLS verification (Nov 19). The v0.145.0 example baseline is affected by the first three only when the relevant components/configurations are present; the partition collision was introduced after v0.145.0.
2. **New Relic has a concentrated set of agent and integration updates.** Its .NET agent now enables basic LLM telemetry by default (without message content), while five security bulletins require attention across eMudhra CA trust stores, Java4Shell and Ruby2Shell.
3. **Datadog Agent 7.85.5 is a security and telemetry-quality release.** TCP gRPC IPC between system-probe and security-agent now requires TLS plus an auth token; per-pod telemetry series are evicted when pods disappear.
4. **Grafana's data stack received maintenance/security patches.** Mimir 3.1.11/3.2.6, Loki 3.6.22 and Pyroscope 2.3.6/2.4.4 update dependencies; Loki 4.0.0-rc.4 remains a breaking-change pre-release.
5. **Elastic is moving further into AI observability.** It announced an agreement to acquire HoneyHive on Nov 19. Elasticsearch 9.6 brings GA PromQL to Elastic Cloud Serverless and a technical preview of Amazon S3 query federation.
6. **Splunk's current Observability Cloud packages have public list prices.** Essentials is $95/host/month and Premier $150/host/month, with a 30-host minimum for paid editions; database-monitoring AI Assistant and IBM Db2 monitoring were released Nov 20.
7. **VictoriaMetrics 1.157.0 and Cilium maintenance releases landed.** VictoriaMetrics adds safer alert query timeouts, resumable migrations and partial restores; Cilium fixes an Hubble URL-query redaction edge case across supported branches.
8. **Vector has an imminent packaging action.** Its APT/YUM repository signing key changes on Nov 30. Update package-manager trust before that date.
9. **AI-agent observability continues to diversify.** DataCat is a new Apache-2.0 self-hosted project; three.dev is a commercial live-traffic evaluation service; Kwatch has reappeared on Product Hunt; a Neo4j Grafana datasource is awaiting its first catalog review.
10. **Prometheus has no new stable release, but upstream main has grown.** The v3.16.0 documentation has 27 unique feature flags; current main has 31. Four are main-only, including metadata-default-time-range. Prometheus v3.17's first pre-release is scheduled for Dec 2.

## 1. Releases, security and engineering changes

### 1.1 OpenTelemetry Collector security advisories — Nov 12–19

**Project:** OpenTelemetry Collector core and contrib  
**Status:** Published security advisories; fixes available in released versions.

| Advisory | Published | Severity | Affected range | Fixed in | Operational condition |
|---|---|---|---|---|
| [GHSA-vf52-ppm4-c35w](https://github.com/open-telemetry/opentelemetry-collector/security/advisories/GHSA-vf52-ppm4-c35w) | Nov 12 | High, CVSS 7.5 | Collector config modules below 1.71.0 | Collector v0.165.0 | OTLP/HTTP or OTLP/gRPC receiver path using confighttp/configgrpc and zstd |
| [GHSA-c35f-chp7-9chr](https://github.com/open-telemetry/opentelemetry-collector-contrib/security/advisories/GHSA-c35f-chp7-9chr) | Nov 19 | Critical, CVSS 9.2 | contrib v0.119.0 to before v0.165.0 | v0.165.0 | OpAMP Supervisor only; accepts_opamp_connection_settings must be true |
| [GHSA-6qvg-78vr-vgm7](https://github.com/open-telemetry/opentelemetry-collector-contrib/security/advisories/GHSA-6qvg-78vr-vgm7) | Nov 18 | Moderate, CVSS 5.3 | contrib v0.142.0 to before v0.163.0 | v0.163.0 | yang_grpc receiver, configured allowlist/rate limits, and endpoint reachable by untrusted clients |
| [GHSA-cx3c-rmcx-ff35](https://github.com/open-telemetry/opentelemetry-collector/security/advisories/GHSA-cx3c-rmcx-ff35) | Nov 12 | Moderate, CVSS 5.9 | Collector v0.147.0 to before v0.164.0 | v0.164.0 | Exporter queue batching with two or more metadata partition keys, receiver include_metadata=true, and client-controlled multi-valued metadata |

Only the OpAMP and YANG advisories were first published during Nov 18–19. The zstd and partition-key advisories were published Nov 12; they remain in this audit because the requested v0.145.0 baseline and later deployments can still be affected under the stated conditions.

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

### 1.3 Grafana Loki 3.6.22 — changelog Nov 17; GitHub publication Nov 18

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

Datadog and New Relic had material agent/security updates (see verified addenda below); Honeycomb issued a company-growth announcement but no new feature release was verified. Chronosphere had no dated product/pricing change this week. HoneyHive is a separate company/product from Honeycomb.

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

**Configuration providers (separate from component metadata counts):** the core source tree has the same five confmap providers in v0.145.0 and current main — env, file, http, https and yaml. Contrib has the same four in both snapshots — aes, googlesecretmanager, s3 and secretsmanager. No provider directories were added or removed between the two refs. These are source-tree provider implementations; builder/distro inclusion and runtime use still depend on the actual binary/configuration.

Verified gate examples:
- pkg.exporterhelper.queueBatchEnabled: alpha from v0.158.0, disabled/opt-in.
- pkg.confighttp.PrioritizeNewKeepalive: stable from v0.162.0 through v0.166.0.
- pkg.configmiddleware.CustomTCPRouting: alpha from v0.164.0, disabled/opt-in.

Component maturity examples:
- queue_batch processor: beta for traces, metrics and logs; alpha for profiles. Verify the exact distribution/builder you ship rather than assuming every vendor distro includes it.
- redis_fleet_tracker extension: development stage; no distribution inclusion declared in its metadata.
- Components present in source are not automatically present in a custom/vendor binary or enabled in runtime configuration.

### 4.3 Grafana compatibility

Actual deployed Grafana version is unknown. Latest verified stable tag remains 13.3.1. Grafana's current configuration documentation marks the Plugin Frontend Sandbox deprecated and says it will be removed in 13.4. Review plugins that depend on the sandbox before upgrading to 13.4. The Claude Code Stats plugin requires Grafana >=13.2.0 and separate Loki/Tempo datasources for event/trace views. A Neo4j datasource v1.0.4 submission is pending first catalog review; it is not yet a Marketplace-approved plugin.

## 5. New tools and products discovered

First-seen date below means first observed in this research run (Nov 23); it is not necessarily the original launch date.

| Candidate | First seen / original launch | Model / license | Maturity and evidence |
|---|---|---|---|
| DataCat | First seen Nov 23; repo created and public announcement Nov 17 | Open source; Apache-2.0 | New self-hosted observability project; no tagged release found |
| three.dev | First seen Nov 23; GA announcement Nov 10 | Commercial SaaS; no OSS license identified | Live AI-agent traffic scoring, failure-mode grouping, MCP and replay/experiments |
| kwatch | First seen Nov 23; Product Hunt relaunch Nov 18; original launch Jan 25, 2022 | Source-available ELv2; Community free, Pro free during early access | v1.2.0 rebuild around dependency-aware root-cause alerts |
| Radar | First seen Nov 23; original product launch predates this window | License not re-verified in this run | Existing Kubernetes UI/tool; v1.21.0–v1.21.2 shipped during the window |
| Claude Code Stats | First seen Nov 23; plugin docs/catalog update Nov 20 | Apache-2.0 community Grafana app | Catalog/docs show v2.0.2; Grafana >=13.2.0; metrics/logs/traces across Prometheus/Mimir, Loki and Tempo |
| Neo4j datasource | First seen Nov 23; repository created Nov 18; v1.0.4 draft Nov 19; review request Nov 20 | Community plugin; Apache-2.0 | Pending first Grafana catalog review; not yet an approved listing |
| Fluent Bit browser SDK | First seen Nov 23; first experimental artifacts Nov 7, with seven tags Nov 16–21 | Fluent Bit project; Apache-2.0 project context | Experimental pre-release SDK; HTTPS and COOP/COEP required; no production support promise |

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

These repositories were surfaced by date-filtered GitHub searches. GitHub repository creation dates are shown below; repository creation is not necessarily the original public launch date. No release tags or independent launch evidence were found; first-seen date in this audit is Nov 23.

| Repository | Relationship | License | Status |
|---|---|---|---|
| [CeyNox Watch](https://github.com/CeyNova-Labs/ceynox-watch) | eBPF/system-call and process observation | Apache-2.0 | Repository created Nov 18; no release tag found |
| [blame](https://github.com/Erio-Harrison/blame) | eBPF request-level latency profiler | GPL-2.0 | Repository created Nov 20; no release tag found |
| [agent-eye](https://github.com/developjik/agent-eye) | AI browser-agent profiling | MIT | Repository created Nov 22; no release tag found |
| [mint_otlp](https://github.com/dashbitco/mint_otlp) | Elixir OTLP client/instrumentation library | Apache-2.0 | Repository created Nov 17; no release tag found |
| [flask-lens](https://github.com/duhanguler/flask-lens) | Flask development profiling | MIT | Repository created Nov 21; no release tag found |
| [reqray](https://github.com/reqray/reqray) | Node.js request inspection | MIT | Repository created Nov 18; no release tag found |
| [ai-observability-bundle](https://github.com/quentinRogeret34/ai-observability-bundle) | Symfony AI instrumentation | No license verified | Repository created Nov 21; do not assume reusable licensing |

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
| High | New Relic eMudhra CA trust updates | Pinned Fluent Bit/logging, Kubernetes and infrastructure integration images may continue trusting compromised intermediate CA roots | Upgrade pinned charts/images/packages to the bulletin's fixed versions |
| Critical, scoped | New Relic Java4Shell / Ruby2Shell | Private Synthetics Java runtimes and specific Fluentd images need updates; New Relic Java/Ruby APM agents themselves are not the vulnerable runtimes | Patch affected private-location images/JDKs and Fluentd image; do not unnecessarily update unaffected agents |
| High | Datadog Agent 7.85.5 IPC hardening | TCP gRPC IPC now requires TLS and an auth token | Upgrade and review custom TCP socket configuration |
| High | Mimir/Loki/Pyroscope patch releases | Security-related dependency updates on maintained branches | Patch the branch actually deployed; keep Loki 4.0 RC separate |
| Medium | Splunk packaging/pricing | Host minimum and edition entitlements materially affect cost | Model actual host count, log volume and agent spans |
| Medium | Vector repository key rotation | Package updates may fail after Nov 30 if trust is not updated | Rotate APT/YUM key before deadline |
| Medium | Elastic PromQL/S3 preview | Potential backend/query architecture option, but bounded compatibility and preview status | Pilot against real dashboards; keep preview data paths non-critical |
| Low–Medium | New AI observability tools | New options for agent behavior, evaluation and usage telemetry | Evaluate with privacy, data residency and maturity gates |

## 7. Upcoming watchlist

| Date / horizon | Watch item |
|---|---|
| Nov 30, 2026 | Vector APT/YUM repository signing-key rotation |
| Dec 2, 2026 | Prometheus v3.17 first pre-release target |
| Dec 7, 2026 | OpenTelemetry Collector v0.167.0 scheduled date in the current release table; v0.166.0 row has a stale 2025 date and no matching tag by cutoff |
| No confirmed date | Clarification/correction to the Collector v0.166.0 schedule row |
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
10. **Review New Relic security bulletins against pinned integrations.** Check eMudhra CA fixes across logging, Kubernetes, eBPF/Pixie and on-host integrations; assess Java4Shell on customer JDKs/private Synthetics and retire the vulnerable Fluentd image for Ruby2Shell.
11. **Patch Datadog Agent 7.85.5 and the Grafana stack.** Review TCP IPC settings, Agent Data Plane telemetry, and maintained Mimir/Loki/Pyroscope branches.

## 9. Source health and monitoring blind spots

- **GitHub releases/advisories:** official release and advisory pages were accessible; GitHub API was used to verify several tags where the rendered release page was incomplete.
- **OpenTelemetry blog:** the Nov 17 policy change means fewer individual/community posts may appear. Monitor documentation, SIG updates, specification PRs and release metadata rather than relying on blog volume.
- **OpenTelemetry Registry:** remains frozen for new submissions/updates; use the Ecosystem Explorer, repository searches and vendor catalogs as complementary sources.
- **Product Hunt:** the observability category surfaced kwatch, superlog and three.dev. Kwatch is a relaunch of a 2022 project; superlog was already in the archive; three.dev's GA date is Nov 10, not this week's. Do not count repeated listings as new launches.
- **Hacker News:** search-engine-indexed queries did not produce a high-confidence new observability launch. Direct Algolia feed coverage was not confirmed in this run.
- **CNCF Landscape:** no new observability-specific entry was verified in the available search; a complete YAML-level landscape diff was not completed, so this is not proof of no additions.
- **Grafana plugin catalog:** the Claude Code Stats documentation shows v2.0.2 and a Nov 20 update, while older catalog/install pages still expose stale v1.1.0 metadata. The Neo4j datasource is a v1.0.4 draft awaiting manual review, not an approved listing. Prefer current documentation/repository and verify plugin signature/version during installation.
- **New Relic release notes/security bulletins:** added as first-class sources after discovering Nov 16–20 agent releases and NR26-13 through NR26-17. The eMudhra, Java4Shell and Ruby2Shell notices have distinct component scopes; do not treat them as a single APM-agent vulnerability.
- **Datadog:** Agent release tags were added to the weekly release sweep; v7.85.5 was published Nov 19.
- **Fluent Bit:** the stable release feed and experimental browser SDK tags were both checked; the SDK is not a stable/production release.
- **Collector release schedule:** the v0.166.0 row still contains a 2025-11-23 date in an otherwise 2026 schedule; no matching release tag existed by cutoff. Track this as a source inconsistency.
- **GitHub topic searches:** date-filtered searches were noisy and limited to the first result page for each topic; the early-project list is a candidate sample, not an exhaustive census.
- **Deployment versions:** Prometheus and Grafana deployed versions remain unknown. Collector v0.145.0 is only the requested audit reference.

## 10. Additional verified updates and corrections

### Additional release and security updates

**Grafana stack maintenance**
- [Mimir 3.1.11](https://github.com/grafana/mimir/releases/tag/mimir-3.1.11) and [3.2.6](https://github.com/grafana/mimir/releases/tag/mimir-3.2.6) both shipped Nov 18. Both update Go 1.26.11, klauspost/compress 1.20.2 and OpenTelemetry libraries 1.47.0 for the CVEs listed in their release notes. Patch the branch actually deployed.
- [Loki 4.0.0-rc.4](https://github.com/grafana/loki/releases/tag/v4.0.0-rc.4) shipped Nov 20. It removes the unused max_chunks_per_query limit (breaking change) and updates x/net, brotli and x/crypto dependencies. It remains a release candidate, not a GA upgrade target.
- [Pyroscope 2.3.6](https://github.com/grafana/pyroscope/releases/tag/v2.3.6) and [2.4.4](https://github.com/grafana/pyroscope/releases/tag/v2.4.4) shipped Nov 20. Both update OpenTelemetry libraries to 1.47.0, klauspost/compress 1.20.2, x/crypto 0.59.0 and the Go toolchain directive to 1.26.11. Release notes call these security updates but do not assign individual CVEs/severity.

**Datadog Agent 7.85.5 — Nov 19**
- [Release](https://github.com/DataDog/datadog-agent/releases/tag/7.85.5). Python 3.13.18, Go 1.26.11 and Agent Data Plane 1.7.3.
- For TCP-configured runtime-security IPC (default on Windows), gRPC between system-probe and security-agent now requires TLS and the Agent IPC auth token; Unix/vsock behavior is unchanged.
- Agent Data Plane adds aggregator/forwarder telemetry and transaction status; APM fixes cover sampler precedence, zero/missing 128-bit trace IDs and attribute truncation.
- Per-pod language-detection telemetry series are evicted when pods are deleted, preventing stale series/cardinality growth. The Cluster Agent also fixes ddTraceConfigs valueFrom parsing.
- Datadog's Nov 17 Gartner Observability Pipelines recognition is a vendor positioning announcement, not a technical release: [source](https://www.datadoghq.com/newsroom/press-releases/datadog-named-a-leader-in-the-2026-gartner-magic-quadrant-for-observability-pipelines/).

**New Relic releases — Nov 16–18**
- [Collector Observability 1.0.0](https://docs.newrelic.com/pt/docs/release-notes/nrdot-release-notes/collector-o11y-1-0-0/) verifies NRDOT Collector 2.8.1 and upstream contrib 0.163.2, removes the newrelic.service.type resource attribute and sets delta temporality. Review queries/resource filters relying on the removed attribute.
- [Pipeline Control Gateway 3.2.1](https://docs.newrelic.com/docs/release-notes/pipeline-control-gateway-release-notes/pipeline-control-gateway-3-2-1/) fixes Python APM harvest JSON errors/duplicate logs and span timestamps, and updates x/net 0.62.0.
- [Node.js agent 14.13.0](https://docs.newrelic.com/docs/release-notes/agent-release-notes/nodejs-release-notes/node-agent-14-13-0/) adds event.name to OTel-derived logs and fixes outbound HTTP protocol/port and response-header capture.
- [PHP agent 12.13.0.43](https://docs.newrelic.com/docs/release-notes/agent-release-notes/php-release-notes/php-agent-12-13-0-43/) instruments mysqli_execute_query, verifies Ubuntu 26.04/Alpine 3.24 and updates Go/x/net dependencies. It also discontinues support for CakePHP 4, Amazon Linux 2 and RHEL 8 from Nov 15; PHP 7.2/7.3 support ends Dec 15.
- [Infrastructure agent 2.1.1](https://docs.newrelic.com/jp/docs/release-notes/infrastructure-release-notes/infrastructure-agent-release-notes/new-relic-infrastructure-agent-211/) updates Go and embedded integrations, adds SUSE 16 support and exposes nrjmx wrapper scripts.
- [.NET agent 10.58.0](https://docs.newrelic.com/docs/release-notes/agent-release-notes/net-release-notes/net-agent-10-58-0/) enables basic LLM telemetry by default, emitting Llm* events/spans/metrics without message content. Opt out with NEW_RELIC_AI_MONITORING_BASIC_TELEMETRY_ENABLED=false. Prompt/response content remains separately configurable. The release adds build-provenance attestations, SHA-256 hashes and Authenticode signatures for packages.

**New Relic security and runtime actions**
- [NR26-13](https://docs.newrelic.com/fr/docs/security/new-relic-security/security-bulletins/security-bulletin-nr26-13/) (Nov 16), [NR26-14](https://docs.newrelic.com/pt/docs/security/new-relic-security/security-bulletins/security-bulletin-nr26-14/) and [NR26-15](https://docs.newrelic.com/docs/security/new-relic-security/security-bulletins/security-bulletin-nr26-15/) (Nov 18) address CVE-2026-111943, the eMudhra intermediate-CA private-key compromise. This is a CA-trust issue, not a vulnerability in the New Relic agents themselves. Fixed versions include Fluent Bit output plugin 3.12.0/Fluent Bit 5.1.5, newrelic-logging chart 1.44.0, nri-bundle 8.0.39 (logs) / 8.0.40 (Kubernetes), Infrastructure agent 2.0.1, infrastructure-bundle 3.6.1, eBPF agent 1.7.2 and Pixie integration 2.2.3. Pinned image tags do not update automatically. FireLens users should also watch for AWS to rebuild its aws-for-fluent-bit base image; New Relic notes that the AWS base image may still carry affected roots.
- Infrastructure agent 2.0 is a major-version upgrade: safe_dir_check_enabled defaults to true and may recreate unsafe/symlinked/wrong-owner working directories; Windows packages remove legacy Fluent Bit 1.9 in favor of 5.1.5. Review this before rolling out the CA fix.
- [NR26-16](https://docs.newrelic.com/docs/security/new-relic-security/security-bulletins/security-bulletin-nr26-16/) (Nov 20) covers critical Java4Shell, CVE-2026-114938. The New Relic Java agent does not bundle a JVM; customer apps are affected only under the JDK/CPU/input conditions in the bulletin. Private Synthetics locations should use SJM release-659+ and ping runtime 1.89.0+.
- [NR26-17](https://docs.newrelic.com/docs/security/new-relic-security/security-bulletins/security-bulletin-nr26-17/) (Nov 20) covers critical Ruby2Shell, CVE-2026-132825. New Relic Ruby APM agents are not affected; the separate Fluentd Docker image needs 1.20.1+, while the deprecated newrelic/fluentd image has no fix and should be retired.
- New Relic's Node.js 16 Synthetic API runtime EOL became effective Nov 18: enabled public-location monitors that could not be auto-upgraded need script review; private locations are not force-upgraded, but image tags and runtime migration still require attention. [EOL notice](https://docs.newrelic.com/eol/2026/05/eol-05-18-26-node-16-chrome-134-runtimes/).

### Additional product, community and discovery notes

- **Honeycomb — Nov 18:** [company update](https://www.honeycomb.io/blog/honeycomb-surpasses-growth-milestones-ai-agent-observability). Honeycomb reports >70% of its customers use Canvas or MCP weekly, MCP calls up 30x since February, ARR growth >70% YoY, AI-native customer growth of 130%, NRR 125% and GRR 89%. These are company-reported figures, not independent market-share data; no new feature or price change was announced.
- **Fluent Bit browser SDK:** seven experimental browser SDK tags appeared Nov 16–21 in the [Fluent Bit release feed](https://github.com/fluent/fluent-bit/releases). They require HTTPS and COOP/COEP headers and explicitly remain unsupported for production. Treat as a newly relevant experimental module, not a stable Fluent Bit release.
- **Grafana Neo4j datasource:** [review request](https://community.grafana.com/t/plugin-review-tiagoasousa-neo4j-datasource-new-neo4j-datasource/165140) dated Nov 20; [repository](https://github.com/tiagoasousa/grafana-neo4j-datasource). Apache-2.0, v1.0.4 is a draft release and manual catalog review is pending. It is not yet an approved Marketplace listing.
- **Radar:** v1.21.0 (Nov 19), v1.21.1 (Nov 20) and [v1.21.2 (Nov 23, 09:41 PT)](https://github.com/skyhook-io/radar/releases/tag/v1.21.2) are existing-product releases, not a new launch. v1.21.2 clarifies empty resource history coverage, prevents a stuck metrics poll from blocking cluster switching, and adds vulnerability CSV/live-traffic graph export.
- **OpenTelemetry Community Awards — Nov 16:** [winner announcement](https://opentelemetry.io/blog/2026/otel-community-awards/). Ecosystem Explorer was recognized; this reinforces it as a discovery source alongside GitHub and vendor catalogs.
- **Semantic Convention PRs remain proposals:** [#4336](https://github.com/open-telemetry/semantic-conventions/pull/4336) proposes a span-duration histogram with opt-in span-name dimension to limit cardinality; [#4356](https://github.com/open-telemetry/semantic-conventions/pull/4356) promotes Kubernetes pod-volume metrics toward Release Candidate; [#4337](https://github.com/open-telemetry/semantic-conventions/pull/4337) moves browser conventions toward a separate client-side registry. All were open at cutoff.
- **Collector stable-by-default RFC #16414** remained open. Nov 18–23 review discussed dynamic components, wrapper behavior, major-version alignment between components and distributions, behavior-based tests and feature-gate transitions; no decision/merge was verified.
- **Collector release schedule discrepancy:** the main release table still shows a 2025-11-23 row for v0.166.0 even though surrounding entries are 2026. No v0.166.0 GitHub tag existed by the Nov 23 10:33 PT cutoff. The next correctly dated row is v0.167.0 on Dec 7. Treat this as a schedule typo/maintainer clarification needed, not a confirmed release date.
- **VictoriaMetrics 1.157.0 migration details:** vmctl now requires the vm-native filter end-time flag for resumable migrations; Vultr SD config uses vultr_sd_configs; partial vmrestore removes local partitions not included in the restore. Test these behaviors in staging before production recovery/upgrade.
- **Splunk pricing caveat:** $95/$150 host-month list prices and 30-host paid minimum were visible on the public pricing page Nov 23. This is a current pricing observation, not a verified price change announced during Nov 16–23.
- **Grafana plugin caveat:** Claude Code Stats docs/catalog show 2.0.2 updated Nov 20, while older catalog/install metadata remains stale. Grafana 13.4 is still the planned removal point for the Plugin Frontend Sandbox.

### Capability/provider and source-health addenda

- **Collector config providers:** core v0.145.0 and current main both contain env, file, http, https and yaml providers. Contrib v0.145.0 and current main both contain aes, googlesecretmanager, s3 and secretsmanager providers. These directories are outside metadata.yaml component counts. Source presence does not guarantee a custom/vendor distro includes them.
- **Source-health update:** New Relic release notes/security bulletins are now added as first-class monitored sources; Datadog Agent release tags, Grafana plugin-review discussions and Fluent Bit experimental tags are also added to the discovery pass. No source was intentionally removed.
- **Coverage gaps:** direct Hacker News Algolia coverage was not confirmed; GitHub topic searches were noisy and limited to first-page samples; CNCF Landscape was not fully diffed at YAML level; OpenTelemetry Registry remains frozen for new submissions. Absence of hits is not proof that no launch occurred.
- **Action priorities:** check New Relic's pinned eMudhra-related images/charts/integrations; review private Synthetic locations/JDKs and Fluentd images for Java4Shell/Ruby2Shell; patch Datadog Agent 7.85.5 and Grafana stack maintenance branches; update Vector repository keys before Nov 30; test VictoriaMetrics partial-restore behavior; keep Loki 4.0 RC and Fluent Bit browser SDK out of production; plan Grafana 13.4 plugin compatibility.

## Archive record

This report and its capability/discovery snapshots are indexed in the Signal Desk repository:
- [2026-11-23 weekly brief](2026/2026-11-23-weekly-brief.md)
- [Prometheus feature flags](2026-11-23-prometheus-feature-flags.json)
- [Collector capability delta](2026-11-23-collector-capability-delta.json)
- [New tool discovery snapshot](2026-11-23-discovery-candidates.json)

Stable tags: #weekly-brief #release-notes #security #licensing #pricing #capability-audit #feature-gates #tool-discovery #semantic-conventions #ai-observability
