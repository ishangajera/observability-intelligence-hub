# Weekly Observability Intelligence Brief — 2026-11-16

**Reporting window:** 2026-11-09 through 2026-11-16 (verified through 11:24 PT on Nov 16)  
**Tags:** #weekly-brief #release-notes #capability-audit #feature-gates #tool-discovery #security #licensing #semantic-conventions

## Executive summary

This was a materially active week. The highest-impact developments are:

1. **OpenTelemetry Collector batching is now on a formal deprecation path.** The Batch processor is officially deprecated; exporter-level queue/batching becomes the default for most exporters in 0.171.0 (planned February 2027), and the old processor is planned for removal in 0.177.0 (May 2027). This is a migration, not an immediate removal.
2. **Grafana shipped 13.3.1 with six security fixes, but a separate critical Brotli issue in bundled plugin binaries remains unresolved in the public tracking issue.** Do not assume the core patch closes the bundled-plugin gap.
3. **Vector 0.62.0 shipped today with six breaking changes.** The most operationally significant are removal of several internal metrics, a changed histogram-sum behavior, a MongoDB 4.4 minimum, and removal of structural configuration interpolation.
4. **Grafana Alloy 1.22.0 is stable.** It adds Kubernetes events, SQL Server collectors, an exceptions connector and Kafka partition-processing controls, but it still embeds Collector contrib 0.164.1 rather than the upstream 0.165 line.
5. **Mimir 3.2.5 hardens Alertmanager SNS handling** by requiring explicit AWS credentials and disabling a custom HTTP-client path that could bypass expected network controls.
6. **Splunk Observability Cloud added Essentials and Premier host-based editions on November 12**, with different Agent Observability entitlements, and added A2A access to its AI Assistant for selected customers.
7. **Elastic Streams entered private preview** as a managed telemetry-pipeline service, while New Relic changed the default for basic AI monitoring in its Node.js agent.
8. **New discovery candidates include agent-otel-kit and SITREP**, both aimed at observability of AI coding-agent activity, plus a new Trivy Operator/Grafana dashboard integration.

The release cadence was quiet for Prometheus, Tempo, Thanos, Jaeger, VictoriaMetrics and Cilium/Hubble. Their latest verified versions remain carry-forward baselines, not new releases this week.

---

## 1. Releases and product changes

### 1.1 Vector 0.62.0 — November 16 — released

Primary sources: [GitHub release](https://github.com/vectordotdev/vector/releases/tag/v0.62.0) · [upgrade guide](https://vector.dev/releases/0.62.0/)

The Datadog COSE team published Vector 0.62.0. The release contains 40 changes: 6 breaking changes, 3 features, 8 enhancements and 23 bug fixes.

Important breaking changes:

- Histogram sums that are absent are no longer synthesized as zero. Consumers that relied on a zero-valued sum need to handle missing values explicitly.
- The internal metric **internal_metrics_cardinality_total** is removed.
- Legacy buffer metrics are removed.
- The **process_runtime** metric family is removed.
- The MongoDB source now requires MongoDB 4.4 or later.
- Configuration is parsed before environment interpolation. Interpolation can still populate values, but it can no longer construct or alter the configuration tree/structure.

Operational impact: check dashboards and alerts for the removed internal metrics, verify histogram queries that assumed a zero sum, and test templated configuration before rolling out. The MongoDB minimum is a hard compatibility constraint. Status: stable release.

### 1.2 Grafana 13.3.1 — November 10 — security patch

Primary source: [Grafana v13.3.1](https://github.com/grafana/grafana/releases/tag/v13.3.1)

The patch resolves six published security issues:

- CVE-2026-102589 — High; cross-instance user impersonation involving image-renderer JWT handling.
- CVE-2026-111024 — High; folder-permission bypass in the Git Sync repository-files API.
- CVE-2026-107509 — Medium; memory exhaustion involving SQL Expressions.
- CVE-2026-110992 — Medium; authorization/path handling issue in Git Sync jobs.
- CVE-2026-13721 — Medium; folder authorization bypass in Git Sync provisioning files.
- CVE-2026-14242 — Medium; authorization bypass in Git Sync provisioning jobs.

Use the matching patched release for the deployed Grafana branch. The latest stable tag verified in this run is 13.3.1; no 13.4.0 stable tag was confirmed.

**Separate dependency concern — Grafana issue [#137257](https://github.com/grafana/grafana/issues/137257):** an open community issue reports that bundled Prometheus, Jaeger and Cloud Monitoring plugin binaries include github.com/andybalholm/brotli below 1.2.7 and asks for rebuilt binaries. The issue associates this with CVE-2026-111497, but the official New Relic/Node.js advisories describe that CVE as a Node.js Brotli-decoder RCE; the applicability of that CVE to the pure-Go package named in the Grafana issue is not established by the issue itself. The issue remained open without a confirmed remediation in this run. Treat it as a dependency/version question to validate with Grafana, not a confirmed Grafana CVE. The confirmed CVE-2026-111497 exposure is in vulnerable Node.js runtimes; see New Relic NR26-11 below.

### 1.3 Grafana plugin SDK Go 0.299.0 — November 12

Primary source: [grafana-plugin-sdk-go v0.299.0](https://github.com/grafana/grafana-plugin-sdk-go/releases/tag/v0.299.0)

The SDK release fixes a gRPC connection deadlock that could leave a plugin connection frozen, and updates dependencies including golang.org/x/net and klauspost/compress. This is a plugin-author/runtime reliability update, not a new Marketplace listing.

### 1.4 Grafana Alloy 1.22.0 — November 12 — stable

Primary source: [Alloy v1.22.0](https://github.com/grafana/alloy/releases/tag/v1.22.0) · [tagged go.mod](https://github.com/grafana/alloy/blob/v1.22.0/go.mod)

New capabilities:

- Kubernetes event receiver.
- SQL Server server-configuration and server-metrics collectors, extra performance counters and throttling controls for query-sample collection.
- Exceptions connector.
- Kafka receiver/exporter support for dial_timeout (default 10 seconds), max_decompress_batch_bytes (default 1 GiB), max_prefetch and max_in_flight partition-processing controls.
- Prometheus Operator scrape classes, multiple SNMP exporter configuration files and Azure encoding extension support.
- Distroless Helm chart option.

Breaking changes:

- loki.enrich and prometheus.enrich remove target_match_label, logs_match_label and metrics_match_label; target_to_log_match and target_to_metric_match are now required.
- otelcol.connector validates output signal types more strictly.
- Kafka partition_processing.max_buffered_batches is deprecated in favor of max_prefetch.batches and upstream removes it in Collector 0.166.0.

Alloy 1.22.0 embeds OpenTelemetry Collector contrib 0.164.1. Upstream Collector 0.165.0/0.165.1 is newer, so do not assume Alloy 1.22 contains the 0.165 component or behavior set.

Security: the release updates github.com/andybalholm/brotli to 1.2.7, golang.org/x/net to 0.62.0, Vite to 7.3.7 and Go to 1.27.3. Status: stable.

### 1.5 Grafana Mimir — November 13 — maintenance/security releases

Primary sources: [3.2.5](https://github.com/grafana/mimir/releases/tag/mimir-3.2.5) · [3.1.10](https://github.com/grafana/mimir/releases/tag/mimir-3.1.10) · [2.17.12](https://github.com/grafana/mimir/releases/tag/mimir-2.17.12)

Mimir 3.2.5 hardens Alertmanager SNS configuration:

- SNS receivers require explicit AWS credentials.
- The use_aws_http_client path is disabled because the AWS SDK HTTP client could bypass expected firewall/network restrictions.
- Existing tenant configurations are revalidated and may need changes.

This prevents a tenant-controlled SNS receiver URL from becoming a route for credential disclosure or SSRF-like behavior. Review SNS receiver configuration before upgrading; use explicit credentials and preserve egress controls. The 3.1.x and 2.17.x maintenance branches also received releases; check their individual notes before selecting a branch-specific patch.

Carry-forward security advisory: CVE-2026-81938 / GHSA-243G-H4F6-PRQR exposed a file-read path through tenant-supplied Alertmanager receiver settings. It was fixed in Mimir 3.1.7 and 3.2.2; current 3.1.10 and 3.2.5 are later patched releases. The issue requires permission to write a tenant's Alertmanager configuration.

### 1.6 Grafana Loki — November 13 — patch releases

Primary sources: [3.7.10](https://github.com/grafana/loki/releases/tag/v3.7.10) · [3.6.21](https://github.com/grafana/loki/releases/tag/v3.6.21)

The 3.7.10 line changes TLS CurvePreferences to prefer X25519MLKEM768, followed by X25519 and P-256. This introduces a hybrid post-quantum key-exchange preference; verify interoperability with older TLS clients and proxies.

The 3.6.21 maintenance release updates golang.org/x/crypto. The release notes do not assign a severity to that dependency change. Status: patch releases.

### 1.7 Pyroscope Go SDK 1.5.0 — November 10

Primary source: [pyroscope-go v1.5.0](https://github.com/grafana/pyroscope-go/releases/tag/v1.5.0)

The SDK changes the profile-type field from plural profile_types to singular profile_type in the relevant API/config surface and includes dependency/security updates. Check custom SDK integrations and any configuration or dashboard tooling that reads the old field. Status: released.

### 1.8 Prom++ 0.8.19 — November 13

Primary source: [Prom++ v0.8.19](https://github.com/deckhouse/prompp/releases/tag/v0.8.19)

Notable fixes and behavior changes:

- Future-dated samples that would otherwise force a far-future block/head window are skipped by default; --keep-future-samples preserves the old behavior.
- Remote-read responses preserve chunk contents and respect frame-size limits.
- Query results remain consistently ordered during index rebuilds.
- Alertmanager notification sending is isolated per Alertmanager instance, so one slow destination is less likely to stall healthy destinations.
- New queue/drop/send metrics improve Alertmanager diagnosis.
- Go 1.26.11 and dependency updates address security issues.

Review any workflows that intentionally ingest future timestamps before upgrading.

### 1.9 Datadog agents — November 11–13

Primary sources: [Agent 7.85.4](https://github.com/DataDog/datadog-agent/releases/tag/7.85.4) · [Python tracer 4.17.0](https://github.com/DataDog/dd-trace-py/releases/tag/v4.17.0) · [Python tracer 4.16.5](https://github.com/DataDog/dd-trace-py/releases/tag/v4.16.5)

- Datadog Agent 7.85.4 disables Agent Health Platform by default on Kubernetes to avoid Autodiscovery stalls. If you depend on that health telemetry, verify whether you need to re-enable it.
- dd-trace-py 4.17.0 adds Python 3.15 support, AI Guard instrumentation and support for additional AI/audio paths including ElevenLabs and Amazon Nova 2 Sonic. It removes legacy pytest plugin environment variables; check CI configurations that still use them.
- dd-trace-py 4.16.5 is a maintenance patch including a memory-leak fix.

### 1.10 OpenTelemetry JavaScript — November 9–12

Primary sources: [JS v3.1.1](https://github.com/open-telemetry/opentelemetry-js/releases/tag/v3.1.1) · [experimental v0.301.2](https://github.com/open-telemetry/opentelemetry-js/releases/tag/experimental/v0.301.2) · [Node auto-instrumentations v0.83.1](https://github.com/open-telemetry/opentelemetry-js-contrib/releases/tag/auto-instrumentations-node-v0.83.1)

- Stable v3.1.1 fixes host.id detection on Darwin/BSD.
- Experimental v0.301.2 improves redaction of credentials and sensitive query parameters from url.full in fetch/XHR instrumentation.
- Node auto-instrumentations 0.83.1 and related contrib packages received updates.

Carry-forward major-version note: OpenTelemetry JS v3.0.0 was published October 20, not November 5. November 5 was v3.1.0. The v3 major line raises runtime/API compatibility requirements and removes/changes legacy package surfaces; check the official migration notes before moving older Node.js services.

### 1.11 Fluent Bit browser SDK — November 14 — alpha

Primary source: [experimental browser SDK release](https://github.com/fluent/fluent-bit/releases/tag/wasm-browser-5b0f4538ca3db617c0f8f7fdabcfedeb138255de)

The Fluent Bit repository now publishes an experimental WebAssembly browser SDK release. It is built from the main branch and explicitly carries no production-support promise. Browser deployments require HTTPS and appropriate COOP/COEP headers. Treat this as an experiment, not a stable browser telemetry agent. Fluent Bit 5.2.0 remains the latest stable core release in this run.

---

## 2. OpenTelemetry architecture, semantics and community

### 2.1 Collector Batch processor deprecation — November 11 — confirmed project direction

Primary source: [Deprecating the Collector Batch Processor](https://opentelemetry.io/blog/2026/collector-batching-migration/)

The project has formally entered phase 2 of the batching migration:

- The Batch processor is officially deprecated.
- Exporter-level queue/batching is the preferred path for most pipelines.
- Batching is planned to become enabled by default in most exporters using the common sending_queue behavior in Collector 0.171.0 (planned February 2027).
- The Batch processor is planned to be removed from core and distributions in 0.177.0 (planned May 2027).
- queue_batch is the replacement processor for the smaller set of cases where batching must remain in the processor pipeline.

The exporter queue is now on the other side of the batching operation. A queue_size of 1,000 requests may buffer materially less data than a queue holding 1,000 already-batched requests. Re-evaluate queue capacity, sizer, num_consumers, block_on_overflow and persistent storage. The project recommends monitoring otelcol_exporter_queue_size against otelcol_exporter_queue_capacity after migration.

~~~mermaid
flowchart LR
  R[Receiver] --> P[Other processors]
  P --> Q[Exporter sending_queue]
  Q --> B[Exporter-level batch]
  B --> E[Exporter]
  P --> QB[queue_batch processor]
  QB --> E
  BP[Deprecated batch processor] -. remove by 0.177.0 .-> P
~~~

**Baseline implication:** sending_queue has been stable since approximately Collector 0.126.0, so a Collector v0.145.0 deployment already has exporter queueing. The exporter batching feature gate is newer: pkg.exporterhelper.queueBatchEnabled was introduced in 0.158.0 and is alpha/opt-in. queue_batch itself is newer than the user's v0.145.0 example baseline.

### 2.2 Collector 0.165.1 contrib patch — November 9

Primary source: [Collector contrib v0.165.1](https://github.com/open-telemetry/opentelemetry-collector-contrib/releases/tag/v0.165.1)

The patch pins the Consul API dependency to avoid an unintended API-v2 behavior change. It is a maintenance release, not a broad component refresh. The latest stable core release object checked remains 0.165.0; the contrib release notes reference the matching core tag, but no separate core 0.165.1 release object was confirmed in the release listing.

### 2.3 Semantic Conventions 1.45.0 — carry-forward; no new release this week

Primary source: [Semantic Conventions 1.45.0](https://github.com/open-telemetry/semantic-conventions/releases/tag/v1.45.0)

The current migration work still includes RPC status-code naming, messaging system-name changes, FaaS invocation namespace changes and database connection-limit naming. Audit OTTL transformations, dashboards, alerts, service maps and exporter mappings. No newer semantic-conventions release was verified in this window.

### 2.4 OTel eBPF Instrumentation 1.0.0 — carry-forward correction

Primary source: [OBI v1.0.0](https://github.com/open-telemetry/opentelemetry-ebpf-instrumentation/releases/tag/v1.0.0)

The stable 1.0.0 release was published October 30 and was not included in the previous brief. It freezes the v1 configuration surface and is a meaningful milestone for zero-code eBPF instrumentation. Do not confuse the OBI agent's 1.0.0 version with the separately versioned Collector receiver; the receiver remains on its own release line. Check the OBI release notes for current protocol/language coverage and known restart/timestamp limitations before broad deployment.

### 2.5 Kafka receiver engineering note — November 6 — upstream changes predate the blog

Elastic published an engineering explanation of Kafka receiver partition workers and independent processing. The upstream PRs were merged before the blog date; the article is a useful explanation, not a new November 6 code release. Independent partition processing and max_in_flight can improve throughput, but require careful review of ordering, offset commits, retry behavior and concurrency safety. Elastic's per-tenant queue-fairness processor is part of its managed pipeline implementation; do not assume it is a generic upstream Collector component.

Primary sources: [Elastic engineering article](https://www.elastic.co/observability-labs/blog/opentelemetry-kafka-receiver-tenant-isolation) · [upstream Kafka receiver PR #51127](https://github.com/open-telemetry/opentelemetry-collector-contrib/pull/51127).

---

## 3. Vendor products, packaging and notable engineering

### 3.1 Splunk Observability Cloud — November 12

Primary sources: [November release notes](https://help.splunk.com/en/splunk-observability-cloud/release-notes/november-2026) · [Essentials/Premier announcement](https://www.splunk.com/en_us/blog/observability/splunk-observability-cloud-essentials-and-premier-packages.html) · [pricing](https://www.splunk.com/en_us/products/pricing.html)

The November 12 release notes list two host-based editions:

- Essentials includes core infrastructure and application monitoring, Observability Logs, AI-assisted troubleshooting and Agent Observability.
- Premier includes Essentials plus Database Monitoring, Secure Application, Synthetic Monitoring, RUM, Digital Experience Analytics, Business Journeys and AI Agent Evaluation, with a higher monthly Agent Observability span allowance.

New November 12 capabilities include A2A access to the Observability AI Assistant for selected customers, Log Observer summaries, APM Span Analyzer, mobile RUM defaults/session investigation improvements, MetricSet cardinality analytics and a capability search/pin catalog.

Pricing: the new edition-specific price was not found in the public release notes. The public pricing page still lists host-based Observability Cloud starting prices of $15/host/month for Infrastructure, $60 for App & Infra and $75 for End-to-End, billed annually. Observability Logs is listed at $0.60 per GB per day for 15-day retention and $0.85 per GB per day for 30-day retention. Splunk Agent Observability is separately listed from $100/month per 1.2 million spans annually. Do not conflate these public starting prices with a confirmed Essentials/Premier quote.

The November 10 Splunk blog is internally inconsistent on Tokenomics timing: its summary says a November 2026 preview, while the detailed availability section says December 2026. Treat the preview date as unconfirmed; GA on AWS Marketplace is planned for early 2027. Eval-G1 and Evaluation Tuner were announced for November GA, but their availability was not confirmed in the November 12 release notes.

### 3.2 Elastic Streams — November 10 — private preview

Primary source: [Introducing Elastic Streams](https://www.elastic.co/observability-labs/blog/elastic-streams-telemetry-pipeline-s3)

Elastic introduced Streams as a managed telemetry-pipeline service for Elastic Cloud Serverless. The preview accepts OTLP, Prometheus Remote Write and Elasticsearch bulk data, runs processing in Elastic-managed OpenTelemetry Collectors, and routes to Elastic and/or S3. The UI includes a Streams Map and YAML export/import.

~~~mermaid
flowchart LR
  A[OTLP / Prometheus Remote Write / Bulk API] --> C[Elastic-managed OTel Collectors]
  C --> P[Pipeline processors and routing]
  P --> S[(S3 data lake)]
  P --> E[(Elasticsearch)]
  P --> BOTH[Both destinations]
~~~

Status and caveats: private preview for selected design partners; preview access is free for those partners, but no public GA price was found. Elastic describes preview delivery as best-effort, so do not make it the sole copy of critical telemetry. Public technical preview is planned for early 2027.

### 3.3 New Relic — November 9–18

Primary sources: [Node.js agent 14.12.0](https://docs.newrelic.com/docs/release-notes/agent-release-notes/nodejs-release-notes/node-agent-14-12-0/) · [NR26-11 Node.js security bulletin](https://docs.newrelic.com/docs/security/new-relic-security/security-bulletins/security-bulletin-nr26-11/) · [NR26-12 eMudhra bulletin](https://docs.newrelic.com/docs/security/new-relic-security/security-bulletins/security-bulletin-nr26-12/) · [CodeStream EOL](https://docs.newrelic.com/eol/2026/05/eol-05-11-26-codestream/) · [November 2–6 docs release notes](https://docs.newrelic.com/fr/docs/release-notes/docs-release-notes/docs-11-06-2026/)

Node.js APM agent 14.12.0 (November 9) enables basic AI monitoring telemetry by default. The vendor says this basic telemetry sends Llm* custom events, spans and metrics without message content. Opt out with ai_monitoring.basic_telemetry.enabled=false or NEW_RELIC_AI_MONITORING_BASIC_TELEMETRY_ENABLED=false. The older ai_monitoring.enabled setting/environment variable is deprecated, although setting it false still opts out. The release notes also list “Disabled core tracing” without enough context to infer its exact scope; verify this item before rollout. This APM-agent change is separate from the Synthetics Node.js runtime CVEs below.

CodeStream reached end of life on November 5. The IDE extensions, cloud components and API endpoints were removed; uninstall the extension and delete CodeStream-specific API keys if any remain.

Security bulletin NR26-11 is high priority: CVE-2026-111497 and related Node.js vulnerabilities include remote code execution when a vulnerable Node.js process receives a Brotli-compressed HTTP response from an attacker-controlled server. New Relic lists fixed Node.js versions 22.23.4, 24.22.1 and 26.12.1. Node.js 16.x is EOL and will not receive a fix. Enabled scripted API monitors pinned to Node 16.10 are not auto-upgraded; migrate them to a supported runtime before November 18, 2026. New Relic says public-location monitors still on Node 16.x will be force-upgraded from November 18.

Security bulletin NR26-12 addresses the separate eMudhra intermediate-CA compromise. Private-location customers must manually pull and restart updated images:
- Synthetics Job Manager v642 or newer
- Node API runtime 1.2.296 or newer
- Node browser runtime 3.0.259 or newer
- Ping runtime 1.87.0 or newer

**Documentation inconsistency:** NR26-12 tells Node 16.10 monitor owners to migrate to Node 22.23.0, while NR26-11 lists 22.23.4 as the fixed Node.js 22 line. Prefer the later fixed version 22.23.4 or newer and confirm with New Relic rather than relying on the older 22.23.0 instruction. NR26-12 has no CVE assigned; NR26-11 carries the Node.js CVEs.

Other integration/distribution signals in the November 2–6 docs update: Google Gemini Enterprise monitoring integration, log-configuration workflow actions, fleet-wide Kubernetes triage, NRDOT 2.8.1 adding awsiamdbauthextension to its experimental distribution, and Pipeline Control Gateway 3.2.0 embedding Collector 0.164.0.

### 3.4 Honeycomb Team Agents — November 3 carry-forward

Primary sources: [launch announcement](https://www.honeycomb.io/blog/honeycomb-team-agents-ai-sre-done-right) · [Team Agents product page](https://www.honeycomb.io/platform/team-agents)

Honeycomb announced Personal and Team AI SRE agents in early access. They work from high-cardinality traces, retain investigation context and can pursue scheduled goals such as checking releases, instrumentation, cost and agent quality. Teams set autonomy per goal/action, from observe and recommend through human-approved action and bounded autonomous operation.

Availability: early access now; GA planned for December 1, 2026. Personal agents are planned for every Honeycomb plan; Team Agents require Honeycomb Intelligence on Pro/Enterprise and are priced by hours of agent work rather than tokens. No unit rate was published. This launch was missed in the previous brief and is recorded here as a carry-forward correction.

### 3.5 Grepr AI — November 3 carry-forward

Primary sources: [Grepr AI launch](https://www.grepr.ai/blog/introducing-grepr-ai) · [pricing](https://www.grepr.ai/pricing)

Grepr introduced a commercial harness for proactive operational agents. Its signal processor fingerprints log patterns before indexing and sends new/changed patterns to agents for investigation, rather than waiting for a pre-existing alert. The agents can create issues, draft fixes or use connected MCP tools within configured guardrails.

The vendor claims 90% telemetry-cost reduction and reports 17,000 investigations with 20 human-required issues during a 30-day internal run; these are vendor-reported results, not independently validated benchmarks. The current Grepr pricing page shows Free, Pro and Enterprise tiers, but Pro/Enterprise and Grepr-hosted storage are custom-priced; no current per-GB list rate or separate Grepr AI agent-hour price was found. The November 3 launch was not included in the previous brief.

### 3.6 Other vendors/projects

- Chronosphere: no material public product, release or pricing change verified for this window.
- Tempo: latest verified release remains 3.1.1 (October 21); no new release.
- Thanos: latest verified release remains 0.42.5 (October 27); no new release.
- Jaeger: latest verified release remains 2.23.0 (November 5); no new release.
- VictoriaMetrics: 1.156.0 (November 9) remains the latest verified release; no new release this week.
- Cilium/Hubble: latest verified release remains 1.21.0-pre.4 (November 2); no new release this week.
- Prometheus: 3.16.0 (November 5) remains latest stable; no new release this week.
- Fluent Bit: 5.2.0 (November 9) remains latest stable core release; only the experimental browser SDK appeared in the current window.

---

## 4. CNCF and community signals

### 4.1 CNCF Technology Radar Q3 2026 — November 10

Primary source: [CNCF Technology Radar Q3 2026 PDF](https://www.cncf.io/wp-content/uploads/2026/11/CNCF-Tech-Radar-survey-W5-261020-3.pdf)

The report's observability survey has 239 respondents. Prometheus and OpenTelemetry are in the Adopt quadrant. Fluent Bit receives a 99% recommendation score among respondents who evaluated it; Jaeger is also highly recommended. This is a survey of current/former users, not market share or a production-readiness certification. The report is useful for qualitative ecosystem sentiment, not as an adoption census.

### 4.2 OpenFeature as a runtime control plane for OTel — KubeCon discussion

The KubeCon talk describes using OpenFeature flags to change telemetry verbosity, sampling and instrumentation behavior at runtime without redeploying services. See the [OpenTelemetry KubeCon talk roundup](https://opentelemetry.io/blog/2026/kubecon-na/). This is a design pattern and conference discussion, not an accepted OpenTelemetry specification or a shipped Collector feature. It is worth tracking for cost and incident-debugging workflows.

### 4.3 AI observability standardization

KubeCon sessions discussed standardizing agent/AI observability and cross-vendor conventions. No new standard or accepted semantic-convention proposal was verified in this window. Treat this as roadmap discussion, not a finalized schema.

---

## 5. New tools and products discovered

Discovery sources included GitHub repository searches filtered to repositories created November 9–16, CNCF Landscape changes, Product Hunt daily leaderboards, plugin/catalog searches and vendor announcements. First-seen date below is this audit's first discovery date; it is not the original launch date.

| Candidate | First seen / original date | Model / license | Maturity and evidence | Assessment |
|---|---|---|---|---|
| [agent-otel-kit](https://github.com/s3onghyun/agent-otel-kit) | First seen Nov 16; repo created Nov 15; v0.1.0 Nov 15, v0.2.0 Nov 16 | Open source, Apache-2.0 | Local OTel stack for Claude Code, Codex, Gemini CLI and Qwen Code; collector, Prometheus, Loki, Tempo and Grafana/Perses; redaction defaults | Strong new discovery. Early/pre-1.0; vendor cost estimates are partly mocked/estimated, not validated against all real providers. Candidate for watchlist. |
| [SITREP](https://github.com/IluvatarLabs/sitrep) | First seen Nov 16; repo created Nov 12; v0.4.1 Nov 12 | Open source, MIT | Multi-machine Claude Code/Codex session dashboard with state, cost, turns and context usage | Useful adjacent AI-agent operational visibility; not an OTLP backend and not a general application observability platform. |
| [trivy-grafana](https://github.com/francesco-z/trivy-grafana) | First seen Nov 16; repo created Nov 9 | Open source, Apache-2.0 | Grafana dashboard for Trivy Operator vulnerability metrics across clusters; no release object found | New security-observability dashboard/integration, not a standalone product. |
| [eve-sre-agent-template](https://github.com/aphrody-labs/eve-sre-agent-template) | First seen Nov 16; repo created Nov 12 | Open source, MIT | Vercel template for read-only incident triage with Datadog, GitHub, Vercel and Slack connectors | SRE/incident-response template, not a new observability backend. |
| [distributed-request-debugger](https://github.com/ranajahanzaib/distributed-request-debugger) | First seen Nov 16; repo created Nov 11 | Open source, MIT | Reference app using OpenTelemetry, Tempo, Prometheus and Grafana; no release object | Useful demo/reference implementation, not a product launch. |
| [Watchhouse](https://github.com/tiagocolombo/watchhouse) | First seen Nov 16; repo created Nov 14 | No license found; no release | Very early SRE agent prototype; README describes simulated/mock execution rather than live production integrations | Low-confidence lead; do not promote to permanent watchlist. |

No relevant Product Hunt launch was verified in the November 9–16 daily leaderboards. The Hacker News Algolia endpoint was inaccessible during this run; search-engine fallback did not provide a reliable date-filtered launch list. No candidate was promoted solely from Reddit or directory mentions.

---

## 6. Capability gaps, feature flags and component inventories

### 6.1 Prometheus feature flags

Sources: [v3.16.0 feature_flags.md](https://github.com/prometheus/prometheus/blob/v3.16.0/docs/feature_flags.md) · [current main feature_flags.md](https://github.com/prometheus/prometheus/blob/main/docs/feature_flags.md) · [v2.30.0 feature flags](https://github.com/prometheus/prometheus/blob/v2.30.0/docs/feature_flags.md)

Direct recount from the versioned documents:

- Prometheus v3.16.0: 27 unique documented feature flags.
- Current upstream main: 30 unique flags (the document contains repeated occurrences, so count unique IDs, not textual mentions).
- Main-only flags: auto-recording-metadata, metadata-relabeling and promql-native-histograms-as-classic. These are not in the v3.16.0 release documentation and must not be assumed to ship in 3.16 binaries.
- New in v3.16.0: query-cost and promql-unquoted-utf8-names; both are experimental opt-ins.
- memory-snapshot-on-shutdown is present in the v2.30.0 documentation and remains a useful older opt-in; it is disabled by default.
- extra-scrape-metrics is deprecated; promql-extended-range-selectors is now a no-op after the selector behavior became stable.

No Prometheus release or feature-flag lifecycle change was verified this week. Prometheus and Grafana deployed versions are not known; this is an upstream inventory, not a claim about the running environment.

### 6.2 OpenTelemetry Collector v0.145.0 baseline versus current main

Source trees: [Collector core main](https://github.com/open-telemetry/opentelemetry-collector/tree/main) · [Collector contrib main](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main)

A fresh metadata-path diff against the previous November 8 snapshot found:

| Component type | Current main metadata entries |
|---|---:|
| Receivers | 119 |
| Processors | 46 |
| Exporters | 54 |
| Connectors | 17 |
| Extensions | 62 |
| Total | 298 |

Previous current-main snapshot: 274. Baseline v0.145.0: 252. The 24 additions since the previous snapshot are all extension metadata entries; no new receiver/processor/exporter/connector metadata paths were found in this delta. Counts are source metadata entries, not counts of components shipped in every distribution.

New extension families include:
- Encoding: Avro, AWS CloudWatch Metric Streams, AWS Logs, Azure, Google Cloud log entry, Jaeger, JSON log, OTLP, SkyWalking, text and Zipkin.
- Observers: Cloud Foundry Garden, Docker, ECS, host and Kubernetes.
- Storage: database, file, Pebble tail storage and Redis storage.
- Authentication/fleet: AWS IAM database authentication and Redis fleet tracker.
- Two extension test fixtures.

Selected metadata status:
- file_storage: beta; contrib and contrib/k8s distribution metadata.
- k8sobserver: alpha; contrib and contrib/k8s.
- otlpencodingextension: beta; contrib.
- pebbletailstorageextension and redisstorageextension: alpha; contrib.
- awsiamdbauthextension: alpha; contrib. New Relic NRDOT 2.8.1 separately lists it in its nrdot-collector-experimental distribution.
- redisfleettrackerextension: development stage and distributions empty. It is source-tree-only, not evidence of a shipped default component.
- queue_batch processor: beta for traces, metrics and logs; alpha for profiles; distributions empty in core metadata. It is not included in every upstream/default distribution.

The current full feature-gate census was last completed on November 8: 18 gates in the v0.145.0 baseline and 139 in the then-current main snapshot. This run did not reparse every gate-bearing metadata file, so 139 is explicitly a last-complete-snapshot count, not a newly verified November 16 total.

Verified gate details:
- pkg.exporterhelper.queueBatchEnabled: alpha, introduced v0.158.0, opt-in/disabled by default; enables exporter-helper batching by default in NewDefaultQueueConfig.
- pkg.confighttp.PrioritizeNewKeepalive: stable, introduced v0.162.0, lifecycle target v0.166.0.
- pkg.configmiddleware.CustomTCPRouting: alpha, introduced v0.164.0, disabled by default.

Providers: no provider/*/metadata.yaml inventory was found in the core/contrib trees; provider implementations are not represented by this component-metadata count. This remains a structured-inventory gap.

### 6.3 Grafana capability/plugin inventory

- Latest stable Grafana release verified: 13.3.1 (November 10).
- Grafana plugin SDK Go: 0.299.0 (November 12), including a gRPC deadlock fix and dependency updates.
- The last complete plugin-catalog snapshot in the archive is November 8 (388 records). No new plugin listing with a primary release artifact was confirmed for November 9–16; the catalog was not fully re-enumerated this run.
- The separate bundled-plugin Brotli issue remains a security follow-up; plugin catalog versions and bundled plugin binaries are not interchangeable evidence.

---

## 7. Impact and severity assessment

| Severity | Item | Recommended response |
|---|---|---|
| Critical / urgent | CVE-2026-111497 Node.js Brotli-decoder RCE; New Relic NR26-11 lists fixed versions and Node 16.x remains unpatched | Migrate scripted API monitors off Node 16.10 before Nov 18; use Node 22.23.4 or newer |
| Investigate | Grafana issue #137257 alleges a vulnerable Go Brotli dependency in bundled plugin binaries; CVE applicability is not established | Ask Grafana to confirm affected binaries and patch status; do not label as a confirmed Grafana CVE |
| High | Grafana 13.3.1 fixes two High and four Medium CVEs | Upgrade to matching patched branch |
| High | Mimir SNS credential/HTTP-client hardening in 3.2.5 | Review SNS receiver configuration, explicit credentials and egress rules |
| High | New Relic NR26-12 eMudhra CA compromise | Pull updated Synthetics Private Location images and restart containers |
| High | Collector Batch processor deprecation roadmap | Inventory pipelines now; plan exporter-level batching or queue_batch migration |
| Medium–High | Vector 0.62.0 six breaking changes | Audit dashboards, histogram handling, MongoDB versions and config interpolation |
| Medium–High | Alloy 1.22.0 config and Kafka changes | Test enrich labels, connector validation and Kafka settings |
| Medium | New Relic Node.js AI telemetry now on by default | Review ingestion, privacy and opt-out configuration |
| Medium | Datadog Agent Health Platform disabled by default on Kubernetes | Verify whether health telemetry is required |
| Medium | Splunk editions and Agent Observability packaging | Reconcile entitlements and cost model before procurement |
| Low–Medium | New agent-otel-kit/SITREP/Trivy dashboard projects | Evaluate in a sandbox; do not infer production maturity |

---

## 8. Upcoming watchlist

1. **Collector 0.166.0:** next planned version; the release calendar currently contains an inconsistent 2025-11-23 date, so the expected date is not treated as confirmed. Watch Kafka max_buffered_batches removal and the PrioritizeNewKeepalive gate lifecycle.
2. **Collector 0.171.0:** exporter-level batching planned to become default in most exporters in February 2027.
3. **Collector 0.177.0:** Batch processor removal planned for May 2027.
4. **New Relic Synthetics:** Node.js 16.10 scripted API monitor EOL on November 18, 2026.
5. **Honeycomb Team Agents:** GA planned December 1, 2026.
6. **Splunk Tokenomics:** preview planned December 2026; GA on AWS Marketplace planned early 2027.
7. **Elastic Streams:** public technical preview planned early 2027.
8. **Grafana bundled-plugin Brotli issue:** watch for a vendor-confirmed rebuild/fix; no fix date confirmed.
9. **OpenTelemetry AI/agent conventions:** monitor proposals and registry changes; KubeCon discussion is not a finalized standard.
10. **OBI:** follow the stable 1.0.0 release for supported protocols, language coverage and restart behavior.

---

## 9. What an observability engineering leader should do

1. Inventory actual Prometheus/Grafana versions, Collector image digests, distro manifests and enabled feature gates; upstream source presence is not deployment evidence.
2. Patch Grafana to the appropriate 13.3.1-equivalent branch, then separately verify the bundled Brotli plugin binaries.
3. Upgrade Mimir to 3.2.5/3.1.10 as applicable and audit SNS credentials and egress restrictions.
4. Pull updated New Relic Synthetics private-location images and migrate Node 16.10 monitors before November 18 if applicable.
5. Pilot Collector exporter-level batching in staging. Measure queue occupancy, capacity, memory, consumer concurrency, overflow and retry behavior before removing batch processors.
6. Do not assume queue_batch ships in your Collector distro; the upstream core metadata currently lists no default distribution inclusion.
7. Test Alloy 1.22.0 Kafka and enrich configuration migrations, and remember it embeds Collector contrib 0.164.1.
8. Before Vector 0.62.0 rollout, search dashboards/alerts for removed internal metrics and test config interpolation and histogram behavior.
9. Review New Relic AI monitoring default-on behavior and Datadog Agent Health Platform defaults in Kubernetes.
10. Evaluate Splunk, Elastic, Honeycomb and Grepr AI agent products with explicit data access, permissions, retention, residency and billing checks.

---

## 10. Source health and discovery coverage

- **CNCF Landscape:** the repository had two relevant commits in the window (November 14–15); they updated OpenShell/CAIPE/Praxis links, not observability project entries.
- **OpenTelemetry Registry:** the registry remains frozen for new submissions; the Ecosystem Explorer is a better source for instrumentation/ecosystem discovery but is not a comprehensive product/plugin launch feed.
- **GitHub:** searched new repositories by creation date and observability/telemetry/OpenTelemetry/Prometheus/tracing/monitoring/SRE terms. Candidate projects were followed to README, license and release pages.
- **Product Hunt:** daily leaderboards for November 9–16 were checked; no high-confidence observability-specific launch was confirmed.
- **Hacker News:** direct Algolia search was inaccessible; web fallback did not yield a reliable date-filtered launch list.
- **Grafana plugin catalog:** last complete archived snapshot is November 8; no full re-crawl this run. Plugin catalog pages can lag GitHub release artifacts.
- **Collector feature gates:** the full 139-record current-main census is the November 8 snapshot; only selected current gates were re-verified this week.
- **Vendor pricing:** Splunk and Grepr publish some list prices; Honeycomb publishes a usage metric for Team Agents but no unit rate; Elastic Streams preview pricing and edition-specific Splunk package quotes are not public in the sources checked.
- **Deployed versions:** Prometheus and Grafana deployed versions remain unknown. Collector v0.145.0 is the requested comparison baseline, not a claim about the running image.

## 11. Corrections and carry-forward items from the previous brief

- Prometheus 3.16.0 was published November 5, not November 4.
- OpenTelemetry JS v3.0.0 was published October 20; November 5 was v3.1.0. v3.1.1 followed on November 9.
- A direct recount of Prometheus feature-flag documents gives 27 unique flags in v3.16.0 and 30 in current main, not 28 in main.
- The Redis fleet tracker extension is development-stage with an empty distribution list; source presence does not mean it ships in a default distro.
- queue_batch is beta for traces/metrics/logs and alpha for profiles, but its core metadata has no default distribution inclusion.
- OTel eBPF Instrumentation 1.0.0 was released October 30 and was omitted from the previous report.
- Honeycomb Team Agents and Grepr AI were announced November 3 and were omitted from the previous report; both are recorded above as carry-forward launches.

**Bottom line:** The two changes with the most planning value are the Collector batching migration and the expanding agent-observability product category. The most urgent operational checks are Grafana's bundled-plugin Brotli exposure and New Relic's November 18 Synthetics runtime transition.
