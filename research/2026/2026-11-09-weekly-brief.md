# Weekly Observability Intelligence Brief — 2026-11-09

**Coverage:** 2026-11-02 to 2026-11-09  
**Tags:** #weekly-brief #observability #prometheus #opentelemetry #collector #semantic-conventions #grafana #loki #tempo #mimir #alloy #jaeger #fluent-bit #victoriametrics #cilium #ebpf #security #feature-gates #tool-discovery

## Executive summary

1. Security and compatibility dominate this week. Fluent Bit 5.2.0 adds broad parser/network hardening; Loki 3.6.20 and Pyroscope 2.4.3 patch vulnerable dependencies; Collector 0.165.0 bounds zstd decoder allocations and deeply nested payload parsing; Grafana's Jaeger and Infinity plugins also ship security fixes.
2. Prometheus 3.16.0 adds query-cost estimation and execution limits behind a new opt-in flag. The long-running memory-snapshot-on-shutdown flag is not new: it is documented in v2.30.0, remains available in v3.16.0, and is disabled by default. This is a capability-inventory finding, not a new-release alert.
3. OpenTelemetry has both a release and a schema migration story. Collector core/contrib 0.165.0 changes receiver and processor behavior, removes the SignalFx receiver, and promotes semantic-convention migrations. Semantic Conventions 1.45.0 makes RPC conventions stable and renames several attributes.
4. Grafana Cloud shipped control-plane improvements: Adaptive Metrics reached GA; Fleet Management can automatically deliver self-monitoring pipelines to connected Alloy/Collector agents; Grafana Assistant gained a movable/floating layout. The self-managed Assistant still relies on Grafana Cloud services and token-based usage billing.
5. New-tool discovery found two verifiable early releases and several pre-release candidates. Watchlog is an eBPF-oriented Kubernetes/Docker monitor; Magnife is a local OpenTelemetry debugging app. Other candidates target OTLP tail sampling, coding-agent usage telemetry and mobile test observability.
6. Discovery coverage has a structural gap: the OpenTelemetry Registry is frozen for new submissions. The newer OpenTelemetry Ecosystem Explorer is a better active source for instrumentation discovery. Hacker News Algolia's API was inaccessible during this run; site search was used as a weaker fallback.

## 1. Executive change log

| Date | Project | Change | Status | Impact |
|---|---|---|---|---|
| Nov 2 | OpenTelemetry Semantic Conventions | v1.45.0; RPC spans/metrics stable; RPC, messaging, FaaS and DB attribute changes | Released | High |
| Nov 2 | Cilium/Hubble | v1.21.0-pre.4 adds remote-node workload context to Hubble flows and cilium_agent_memory_bytes | Pre-release | Medium |
| Nov 3–6 | Grafana Cloud / Assistant | Adaptive Metrics GA; Assistant floating layout; Fleet self-monitoring pipeline improvements | Cloud features released | Medium |
| Nov 3 | Grafana Pyroscope | v2.4.3 dependency security update | Released | High |
| Nov 4 | Prometheus | v3.16.0; query-cost estimation/limits and UTF-8 PromQL names | Released | High |
| Nov 4–6 | Grafana plugins | Infinity 4.1.6, Traces Drilldown 3.2.0, Azure Monitor 13.0.8, Jaeger 13.0.8, Pyroscope datasource 13.0.10 | Released | Medium–High |
| Nov 5 | Jaeger | v2.23.0 adds SQL query surface, MCP SQL search and api_v3 search | Released | Medium |
| Nov 5 | Grafana Alloy | v1.22.0-rc.0 | Pre-release only | Medium |
| Nov 6 | OpenTelemetry Collector core | v0.165.0; queue_batch maturity, memory-limiter option, zstd and recursion hardening | Released | High |
| Nov 6 | Loki | v3.6.20 dependency security patch | Released | High |
| Nov 7 | OpenTelemetry Collector contrib | v0.165.0; SignalFx receiver removal, Kafka deprecations, new components | Released | High |
| Nov 7 | Loki | v4.0.0-rc.3; S3 storage-class restriction | Pre-release | Medium–High |
| Nov 9 | Fluent Bit | v5.2.0; FTS processor, experimental WASM runtime and extensive security hardening | Released | High |
| Nov 9 | VictoriaMetrics | v1.156.0; Enterprise EULA acceptance change and new CPU-throttling telemetry | Released | Medium–High |

## 2. Detailed release and product changes

### 2.1 Prometheus 3.16.0 — query-cost controls and PromQL changes

**Date:** release notes dated 2026-11-04; GitHub release published 2026-11-05  
**Status:** released, stable  
**Sources:** [Prometheus v3.16.0 release](https://github.com/prometheus/prometheus/releases/tag/v3.16.0), [v3.16.0 feature-flag documentation](https://github.com/prometheus/prometheus/blob/v3.16.0/docs/feature_flags.md)

**What changed**
- Adds experimental query-cost estimation, actual-cost reporting and configurable execution limits behind the query-cost feature flag.
- Adds unquoted Unicode letters and dots in PromQL identifiers behind promql-unquoted-utf8-names.
- Adds experimental integral() for range vectors behind the existing promql-experimental-functions flag.
- Anchored and smoothed vector selectors are now stable and always on. promql-extended-range-selectors is therefore a no-op in this release.
- Adds the X-Prometheus-Use-Start-Timestamps HTTP header to override start-timestamp handling per query; the behavior remains behind use-start-timestamps.
- Adds experimental remote-write option convert_nhcb_to_classic to translate native histograms with custom buckets to classic histograms for systems that do not support NHCB.
- Search API batch_size is now clamped to 1,000.

**Why it matters**
Query-cost is the most operationally significant addition. It creates a path to estimate and constrain expensive PromQL before a shared query tier is overwhelmed. Treat estimates as a policy signal, not a perfect predictor of wall-clock cost. Native-histogram conversion is a compatibility bridge, not a free transformation: classic histograms can expand into more series and change downstream cardinality and query behavior.

**Migration / operational impact**
- Test query-cost in non-production, collect estimated-versus-actual costs for representative dashboards and recording rules, then configure enforcement limits.
- Review remote-write consumers that cannot ingest NHCB before enabling convert_nhcb_to_classic.
- Remove promql-extended-range-selectors from deployment configuration. Keep use-start-timestamps opt-in until counter-reset behavior has been validated.
- Check clients that send oversized search batches; requests are now clamped.

### 2.2 Prometheus capability inventory — flags that release-note monitoring misses

**Version comparison:** v3.14.0, v3.15.0, v3.16.0 and current upstream main  
**Sources:** [feature flags at v3.16.0](https://github.com/prometheus/prometheus/blob/v3.16.0/docs/feature_flags.md), [current upstream feature flags](https://github.com/prometheus/prometheus/blob/main/docs/feature_flags.md)

- The v3.16.0 tag documents 27 feature flags. Current upstream main documents 28.
- All flags documented in the v3.16.0 feature-flag page are disabled by default.
- The two flags newly present in v3.16.0 compared with v3.15.0 are query-cost and promql-unquoted-utf8-names.
- openmetrics2 and zstd-scrape are present in v3.15.0 and absent in v3.14.0.
- promql-native-histograms-as-classic appears in current upstream main but not in the v3.16.0 tag. It is a main-only capability at this audit point; do not assume it ships in v3.16.0.
- extra-scrape-metrics is marked deprecated in the v3.16 documentation. Prefer the extra_scrape_metrics configuration path.
- promql-extended-range-selectors is a no-op after anchored/smoothed selectors became stable and always on.

The 27 flags in the v3.16.0 tag are:

concurrent-rule-eval, created-timestamp-zero-ingestion, delayed-compaction, exemplar-storage, extra-scrape-metrics, histograms-st-encoding, memory-snapshot-on-shutdown, metadata-wal-records, old-ui, openmetrics2, otlp-deltatocumulative, otlp-native-delta-ingestion, promql-binop-fill-modifiers, promql-delayed-name-removal, promql-experimental-functions, promql-extended-range-selectors, promql-per-step-stats, promql-unquoted-utf8-names, query-cost, search-api, st-storage, st-synthesis, type-and-unit-labels, use-start-timestamps, use-uncached-io, xor2-encoding, zstd-scrape.

**Specific startup flag that should not be missed:** memory-snapshot-on-shutdown is present in v2.30.0 documentation, absent in v2.29.0 documentation, and still present in v3.16.0. The first verified release is therefore v2.30.0. It is disabled by default and is an opt-in shutdown snapshot intended to reduce work during a subsequent startup. It is not a new v3.16 feature and did not appear as a new release-note item this week. This is why monitoring needs a versioned capability inventory in addition to release-note tracking.

**Historical-version limitation:** this run reconstructed first-verified versions for the flags called out above, but did not establish the exact introduction release for every older flag. Those are deliberately left unknown rather than inferred from current documentation.

### 2.3 OpenTelemetry Collector core 0.165.0

**Date:** 2026-11-06  
**Status:** released  
**Source:** [Collector core v0.165.0 release](https://github.com/open-telemetry/opentelemetry-collector/releases/tag/v0.165.0)

**What changed**
- processor/queue_batch is promoted to beta for traces, metrics and logs, and alpha for profiles. It now reports queue and batch metrics as processor metrics.
- processor/memory_limiter gains a garbage_collector.enabled setting to allow forced garbage collection to be disabled.
- The gRPC and HTTP zstd decoders now bound their decoder windows by configured maximum receive/body sizes. Previously, a small crafted zstd frame could declare a very large window and trigger a large allocation before decoded output was produced.
- Protobuf unmarshalling now limits recursive nesting depth to 100 to protect against stack exhaustion from maliciously nested payloads.
- Deprecated confighttp fields IdleConnTimeout, MaxIdleConns, MaxIdleConnsPerHost and DisableKeepAlives are removed.

**Why it matters**
The zstd and recursion changes are security hardening for collectors accepting untrusted or externally supplied telemetry. The release notes do not attach a CVE identifier, but the resource-exhaustion path is concrete. queue_batch may offer a useful queue/batch primitive, but source presence is not proof that a given distribution includes it. Removing deprecated HTTP fields can break custom components or builders that still compile against the old configuration struct.

**Migration / operational impact**
- Prioritize this update for public OTLP/gRPC or HTTP ingestion endpoints that accept compressed payloads.
- Audit custom Collector components and configuration generators for the removed confighttp fields.
- Test queue_batch under representative queue saturation, retry and backpressure scenarios before adopting it.
- Change forced-GC behavior only after measuring heap, RSS, pause and OOM behavior; the new setting is a tuning lever, not an automatic recommendation.

### 2.4 OpenTelemetry Collector contrib 0.165.0

**Date:** 2026-11-07  
**Status:** released  
**Source:** [Collector contrib v0.165.0 release](https://github.com/open-telemetry/opentelemetry-collector-contrib/releases/tag/v0.165.0)

**Breaking changes and migration**
- The deprecated SignalFx receiver is removed. Use the OTLP receiver instead.
- The SignalFx exporter stops producing disk_ops.total and disk_ops.pending under its default translation rules. Replace disk_ops.total with system.disk.operations; replace disk_ops.pending with system.disk.pending_operations and explicitly add the latter to include_metrics.
- goldendataset database convention gates move from alpha to beta. They are now enabled by default, so db.system.name is emitted instead of deprecated db.system.
- Network and RPC convention gates move to stable. The old net.host.ip, net.peer.ip, http.host, http.server_name, rpc.service and peer.service attributes are no longer emitted by those paths.
- The Jaeger translator's HTTP convention gates move to beta; it emits http.response.status_code instead of http.status_code by default.
- Zipkin cloud-resource and network convention gates move to beta/stable; cloud.resource_id, network.local.address, network.peer.address and service.peer.name replace older attributes.
- Prometheus receiver samples now retain __scheme__ and __metrics_path__ as datapoint attributes instead of dropping them.
- processor/transform deprecates flatten_data; replace flatten_data: true with flatten: { log: true }.
- Kafka receiver deprecates partition_processing.max_buffered_batches in favor of partition_processing.max_prefetch.batches; the old field is scheduled for removal in v0.166.0.
- The built-in Kafka jaeger_proto, jaeger_json and json encodings are deprecated in favor of encoding extensions.
- exporter/logicmonitor and receiver/riak are now marked unmaintained and will eventually be removed from community distributions.

**New components**
- extension/redis_fleet_tracker reports a Collector fleet's live member count so adaptive_tail_sampling can treat goal_throughput as a fleet-wide budget.
- processor/verify is introduced as a skeleton for verifying RFC 8785/JCS integrity attributes on log records. The release notes explicitly say concrete verification logic follows in a subsequent PR; do not treat the initial component skeleton as production-ready.
- receiver/gnmi is introduced.
- receiver/nats is a receiver skeleton and is explicitly marked in development.

**Why it matters**
The SignalFx receiver removal is an immediate configuration/build break for anyone using it. Semantic-convention gates changing their default or becoming stable can silently change emitted attribute names and therefore dashboards, alert queries, sampling policies and downstream indexing. Preserving __scheme__ and __metrics_path__ changes the label/attribute surface and may affect cardinality and relabeling assumptions. The Kafka field has a concrete next-release removal version, so this is a near-term migration rather than a vague deprecation.

**Conceptual data/control flow for adaptive tail sampling with fleet tracking**

~~~mermaid
flowchart LR
  S[OTLP spans] --> C1[Collector replica A<br/>adaptive_tail_sampling]
  S --> C2[Collector replica B<br/>adaptive_tail_sampling]
  C1 -. membership / live count .-> R[(Redis fleet tracker)]
  C2 -. membership / live count .-> R
  R -. fleet size / budget context .-> C1
  R -. fleet size / budget context .-> C2
  C1 -->|kept traces| T[Trace backend]
  C2 -->|kept traces| T
~~~

The span data path remains Collector-to-backend; Redis supplies fleet membership/budget context. The release notes announce the component pair, but the metadata snapshot does not prove every distro includes the Redis extension.

### 2.5 Collector component inventory — v0.145.0 baseline versus current upstream

**Method:** compare metadata.yaml component inventories in the requested v0.145.0 source tags against the current main source snapshot captured 2026-11-08. The full component and feature-gate records are archived in [the Collector capability audit JSON](2026-11-09-collector-capability-audit.json).

| Component type | v0.145.0 baseline | Current main |
|---|---:|---:|
| Receivers | 117 | 119 |
| Processors | 35 | 46 |
| Exporters | 54 | 54 |
| Connectors | 16 | 17 |
| Extensions | 30 | 38 |
| **Total** | **252** | **274** |

Repository split:
- Core: 19 components at v0.145.0; 28 in current main.
- Contrib: 233 at v0.145.0; 246 in current main.
- Net inventory change: 31 additions and 9 removals. Exporter count is unchanged.

**New components with explicit distribution metadata in current main** (all marked alpha in the inventory snapshot):
- Receiver: activedirectoryinvreceiver — logs.
- Processors: adaptivetailsamplingprocessor — traces; cardinalityguardianprocessor — metrics; drainprocessor — logs; genainormalizerprocessor — traces; partitioningprocessor — logs/metrics/traces, with profiles still development; rollingspanlatencyprocessor — traces; spanpruningprocessor — traces.
- Extension: sdnotifyextension.

The inventory also includes new source-tree records without distribution metadata. A component in core/contrib source is not necessarily built into the upstream default distribution, a vendor distro or a custom Collector image.

**Other source-tree additions / maturity notes**
- adaptive_tail_sampling and rolling_span_latency were promoted to alpha and included in the contrib distribution in v0.164.0; partitioning was added as an initial skeleton in that release.
- v0.165.0 adds redis_fleet_tracker, verify, gnmi and nats. The release notes identify verify and nats as skeleton/in-development work. The metadata snapshot does not provide a distribution declaration for every one of these new components.
- Core queue_batch is beta for traces/metrics/logs and alpha for profiles, but the source inventory does not show it as included in a default distribution manifest.
- No new exporter count appears in the v0.145-to-main metadata diff.

**Components present in v0.145.0 but absent from current main metadata:** bigipreceiver, datadogsemanticsprocessor, dnslookupprocessor, jmxreceiver, k8slogreceiver, mezmoexporter, sapmexporter, signalfxreceiver, wavefrontreceiver.

The exact removal release is not established for every item in this source diff. The SignalFx receiver removal is explicitly confirmed in v0.165.0 release notes; the other absences should be checked against component-specific release history before assuming the exact removal version.

### 2.6 Collector feature-gate audit — all 18 gates in the v0.145.0 baseline

Collector feature-gate defaults are determined by lifecycle stage: alpha is disabled by default; beta is enabled by default but can be disabled; stable is permanently enabled and should no longer be explicitly configured; deprecated is permanently disabled. The metadata records from_version and to_version; to_version is the version when a stable/deprecated gate reached its current stage, stable gates are removed in their to_version, and deprecated gates are removed after at least two Collector releases. See the [Collector feature-gate lifecycle documentation](https://github.com/open-telemetry/opentelemetry-collector/blob/main/featuregate/README.md).

| Gate ID | Stage | From | To | Default / behavior |
|---|---|---:|---:|---|
| filelog.allowFileDeletion | alpha | 0.70.0 | — | Off; permits delete_after_read. |
| filelog.allowHeaderMetadataParsing | beta | 0.73.0 | — | On; permits the header setting. |
| filelog.decompressFingerprint | stable | 0.128.0 | 0.142.0 | Permanently on; computes fingerprints for compressed files by decompressing data. |
| filelog.mtimeSortType | alpha | 0.89.0 | — | Off; permits ordering_criteria.mode: mtime. |
| filelog.windows.caseInsensitive | alpha | 0.142.0 | — | Off; makes include/exclude matching case-insensitive on Windows. |
| logs.assignKeys | beta | 0.93.0 | — | On; permits the assign_keys transformer. |
| logs.jsonParserArray | beta | 0.93.0 | — | On; permits json_array_parser. |
| parser.uri.ecscompliant | alpha | 0.103.0 | — | Off; emits a semantic-convention-compliant URI map. |
| stanza.synchronousLogEmitter | alpha | 0.122.0 | — | Off; synchronous log emission intended to prevent possible Stanza receiver data loss. |
| k8sattr.labelsAnnotationsSingular.allow | alpha | 0.125.0 | — | Off; uses singular default Kubernetes label/annotation resource keys. |
| processor.resourcedetection.propagateerrors | beta | 0.121.0 | — | On; detector errors can propagate from Start() and stop the Collector. |
| processor.resourcedetection.removeGCPFaasID | stable | 0.87.0 | 0.145.0 | Permanently on; removes faas.id in favor of faas.instance. |
| receiver.prometheusreceiver.EnableCreatedTimestampZeroIngestion | alpha | 0.113.0 | — | Off; injects zero-valued created-timestamp samples; metadata warns of worse CPU at high metric volumes. |
| receiver.prometheusreceiver.EnableNativeHistograms | stable | 0.142.0 | 0.145.0 | Permanently on; converts scraped native histograms to OTel exponential histograms. You must still set scrape_native_histograms: true in scrape configuration. |
| receiver.prometheusreceiver.EnableReportExtraScrapeMetrics | alpha | 0.143.0 | — | Off; enables extra Prometheus scrape metrics. |
| receiver.prometheusreceiver.RemoveReportExtraScrapeMetricsConfig | beta | 0.143.0 | — | On; ignores report_extra_scrape_metrics and leaves control to the feature gate. |
| receiver.prometheusreceiver.RemoveStartTimeAdjustment | stable | 0.121.0 | 0.142.0 | Permanently on; leaves start time unset; use metricstarttime processor if needed. |
| receiver.prometheusreceiver.UseCreatedMetric | deprecated | 0.89.0 | 0.141.0 | Permanently disabled; legacy _created-metric behavior. |

**Current upstream gate inventory:** 139 gates in the 2026-11-08 main snapshot: 83 alpha, 51 beta and 5 stable. Nine of the 18 baseline IDs remain in current main; nine are absent. The missing set includes stable/deprecated gates whose lifecycle has advanced, plus alpha/beta gates that were removed or replaced. Do not carry old gate flags forward blindly; compare component metadata and current configuration documentation.

### 2.7 OpenTelemetry Semantic Conventions 1.45.0

**Date:** 2026-11-02  
**Status:** released  
**Source:** [Semantic Conventions v1.45.0 release](https://github.com/open-telemetry/semantic-conventions/releases/tag/v1.45.0)

**What changed**
- RPC spans and call-duration metrics are now stable, including gRPC and Apache Dubbo.
- RPC metadata is split into headers and trailers: rpc.request.metadata.* becomes rpc.request.header.*; rpc.response.metadata.* becomes rpc.response.header.* or rpc.response.trailer.*; rpc.response.status_code becomes rpc.status_code.
- Messaging attributes are renamed and re-namespaced: messaging.system becomes messaging.system.name; Kafka, RabbitMQ, RocketMQ, GCP Pub/Sub and Azure messaging attributes move into their system namespaces.
- FaaS invocation attributes move to faas.invocation.*: faas.time becomes faas.invocation.start_time; faas.invocation_id becomes faas.invocation.id.
- db.client.connection.max becomes db.client.connection.limit.
- system.device becomes system.device.name; system.memory.state now defines only used and available, with free, buffers and cached deprecated.
- Entity schemas are updated or removed for Android, AWS ECS/logs, GCP GCE/Cloud Run and z/OS; enduser.id and enduser.pseudo.id are deprecated in favor of client-side conventions.
- Kubernetes resource monitoring, container metrics, JVM file-descriptor metrics and hostmetrics attributes receive release-candidate promotions.

**Why it matters**
This is a schema migration, not just a documentation refresh. Dashboards, OTTL transformations, tail-sampling policies, service maps, alert rules and exporters that read old attribute names can lose dimensions or stop matching.

**Migration**
- Update instrumentation and Collector transformations in stages. Use schema URLs and official migration rules where available.
- Search for old rpc.*metadata, rpc.response.status_code, messaging.*, faas.time, faas.invocation_id, db.client.connection.max and system.device references.
- Validate exporters and translators, not only SDK instrumentation; Collector contrib 0.165.0 also changes its default golden-dataset/translator conventions.

### 2.8 Fluent Bit 5.2.0

**Date:** 2026-11-09  
**Status:** released  
**Sources:** [Fluent Bit v5.2.0 release](https://github.com/fluent/fluent-bit/releases/tag/v5.2.0), [official announcement](https://fluentbit.io/announcements/v5.2.0/)

**What changed**
- Introduces the Fluent Typed Scripting (FTS) processor for typed, declarative log transformations and reusable policy packs.
- Adds an experimental WebAssembly browser runtime and SDK.
- Improves the OpenTelemetry input/output path, including dropped-count metadata handling; adds multiple contexts to Prometheus textfile input and scrape_on_start to node-exporter metrics input.
- Adds HTTP worker processing for eligible OpenTelemetry input logs.
- The release contains broad security hardening across credential URI handling, TLS/HTTP behavior, decompression, request limits, OTLP decoding allocations, regex stack growth, header parsing, tags, OAuth2/JWKS and Unix sockets.

**Why it matters**
The security fixes are relevant to deployments accepting externally supplied logs or telemetry. The release notes do not enumerate CVE IDs or severity scores, so this is reported as release-note security hardening, not as a set of independently severity-rated CVEs.

**Operational impact**
- Prioritize an upgrade where Fluent Bit HTTP/OTLP inputs are reachable by untrusted clients.
- Test FTS policy packs separately from existing Lua/modify/grep pipelines; the WASM browser runtime is explicitly experimental.
- Re-run parser and input regression tests for custom tags, decompression, TLS and credential configuration.

### 2.9 VictoriaMetrics 1.156.0 — Enterprise EULA and new cgroup telemetry

**Date:** 2026-11-09  
**Status:** released  
**Source:** [VictoriaMetrics changelog](https://docs.victoriametrics.com/changelog/)

**What changed**
- All VictoriaMetrics Enterprise components now accept the Enterprise Source Agreement using -eula. License keys are no longer verified. -license, -licenseFile, -licenseFile.reloadInterval and -license.forceOffline are deprecated and treated as -eula for compatibility.
- All components expose process_cgroup_cpu_throttled_seconds_total.
- vmagent and single-node VictoriaMetrics support Azure WorkloadIdentity authentication in azure_sd_configs.
- vmagent adds per-remote-write -remoteWrite.queuePath.
- vmagent adds Kafka consumer rebalance/partition metrics.
- vmalert adds -notifier.sanitizeLabelNames for preserving UTF-8 label names with compatible Alertmanager versions.
- vmselect exposes cache mode through vm_cache_mode.
- Fixes include cgroup v1/systemd-slice limit detection and stream-aggregation flush/spike behavior under delayed or out-of-order samples.

**Why it matters**
The -eula change is a licensing/activation change for Enterprise components, not evidence of a price change. It affects LTS lines too: the v1.148.9 LTS notes carry the same EULA acceptance behavior. The new cgroup throttling metric is useful for diagnosing container CPU pressure without relying only on host-level CPU utilization.

**Migration**
- Review Enterprise terms and startup arguments before rolling out the new binaries. Existing license flags are compatibility aliases, but should be removed from future configuration templates.
- Add process_cgroup_cpu_throttled_seconds_total to resource-pressure dashboards and alerts.
- Consider per-remote-write queue paths where destinations have different latency, retry and disk-retention requirements.
- Test Azure Workload Identity discovery from the actual Kubernetes federation setup.

### 2.10 Jaeger 2.23.0 — SQL query surface and MCP search

**Date:** 2026-11-05  
**Status:** released  
**Source:** [Jaeger v2.23.0 release](https://github.com/jaegertracing/jaeger/releases/tag/v2.23.0)

**What changed**
- Adds a SQL query surface that compiles into RFC 0005 filters.
- Exposes storage search capabilities through api_v3 HTTP and gRPC.
- The MCP search_traces tool accepts a SQL statement.
- ClickHouse routes structured filters into SQL WHERE clauses.
- ClickHouse schema creation now requires an explicit table engine.
- AI endpoints can be gated with the ai.auth authenticator.

**Why it matters**
This is a more expressive trace-search path and a useful bridge for MCP-based investigation workflows. It is not a claim that Jaeger has become a general-purpose SQL database; the SQL surface compiles into the project's filter/query model.

**Migration**
- Set an explicit ClickHouse table engine in schema-creation configuration.
- Review auth configuration before enabling AI/MCP endpoints.
- Test existing query clients against api_v3 and the new SQL-to-filter translation.

### 2.11 Loki 3.6.20 and 4.0.0-rc.3

**Dates:** 2026-11-06 and 2026-11-07  
**Status:** 3.6.20 stable patch; 4.0.0-rc.3 pre-release  
**Sources:** [Loki 3.6.20](https://github.com/grafana/loki/releases/tag/v3.6.20), [Loki 4.0.0-rc.3](https://github.com/grafana/loki/releases/tag/v4.0.0-rc.3)

- **3.6.20:** security dependency updates include go-jose v4.1.6 and go-openapi/swag/jsonutils v0.29.2 marked HIGH in the release notes, plus golang.org/x/net v0.62.0 and klauspost/compress v1.20.2 marked UNKNOWN. This is a patch-level security update; apply it to affected 3.6.x deployments.
- **4.0.0-rc.3:** breaking change limits supported S3 storage classes to STANDARD and STANDARD_IA. The RC also fixes compactor deletion behavior.

Do not treat the 4.0 RC as production-ready. Check bucket storage-class usage and retention/lifecycle policies before planning a major-version migration.

### 2.12 Grafana Pyroscope 2.4.3

**Date:** 2026-11-03  
**Status:** released  
**Source:** [Pyroscope v2.4.3 release](https://github.com/grafana/pyroscope/releases/tag/v2.4.3)

This patch updates go-jose to v4.1.6 and golang.org/x/net to v0.62.0 as security fixes. The release notes do not supply CVE identifiers or severity for every dependency. The 2.3.x line also received v2.3.5. Upgrade the maintained branch you actually run rather than jumping branches solely for a patch.

### 2.13 Grafana Alloy 1.22.0-rc.0

**Date:** 2026-11-05  
**Status:** release candidate; explicitly not for production  
**Sources:** [Alloy v1.22.0-rc.0](https://github.com/grafana/alloy/releases/tag/v1.22.0-rc.0), [release PR #7436](https://github.com/grafana/alloy/pull/7436)

The RC adds/updates Collector components and integrations including k8seventreceiver, SQL Server database observability, otelcol.connector.exceptions, Prometheus Operator scrape classes and multiple SNMP exporter configuration files. loki.enrich and prometheus.enrich move to public preview. The release PR also carries Kafka receiver configuration changes, including the migration path from partition_processing.max_buffered_batches to max_prefetch.batches.

The RC is built against Collector 0.164.1, not 0.165.0. Test configuration changes and wait for a stable Alloy release before production rollout. Validate the changed loki.enrich matching arguments and Kafka prefetch/in-flight settings.

### 2.14 Cilium/Hubble 1.21.0-pre.4

**Date:** 2026-11-02  
**Status:** pre-release  
**Source:** [Cilium v1.21.0-pre.4](https://github.com/cilium/cilium/releases/tag/v1.21.0-pre.4)

Observability-relevant changes:
- Hubble flows now include Kubernetes workload information for endpoints on remote nodes.
- Adds cilium_agent_memory_bytes, an estimate of agent memory by component that accounts for BPF memlock as well as Go heap.
- Other Hubble/metrics work includes dynamic metric cleanup behavior.

The release is a pre-release, not a production upgrade recommendation. The remote-workload context and memory metric are worth validating in a staging cluster because they improve network-flow attribution and agent memory accounting.

### 2.15 Grafana Cloud, Assistant and plugin ecosystem

**Dates:** Cloud updates 2026-11-03 through 2026-11-06  
**Sources:** [Grafana What's New](https://grafana.com/whats-new/), [Grafana Assistant self-managed documentation](https://grafana.com/docs/grafana/latest/administration/ai-assistant/), [Assistant usage/pricing documentation](https://grafana.com/docs/grafana-cloud/visualizations/simplified-exploration/assistant/)

**Grafana Cloud**
- Adaptive Metrics reached GA on Nov 6, with updated recommendations and rule-management workflows.
- Fleet Management can automatically deliver self-monitoring pipelines to connected Alloy and OpenTelemetry Collector agents, including environments managed through infrastructure-as-code.
- Audit Log is in public preview.
- Grafana Assistant's floating layout can be moved, resized, collapsed or popped out into a separate window.

**Assistant packaging and compatibility**
- The self-managed Assistant is a Grafana plugin, but the backend remains Grafana Cloud; prompts and query context are sent to the Cloud service while data sources can remain in the self-managed Grafana environment.
- Usage is token-based. Exact rates depend on the applicable Grafana Cloud plan and are not repeated here as a universal price.
- Grafana documentation warns that upgrading the Assistant plugin on Grafana versions below 13.3.0 can remove manually added Assistant permissions; Grafana 13.3.0+ addresses this behavior.
- The Grafana What's New page labels a self-managed feature release as Grafana 13.4.0, while the GitHub stable-release endpoint checked for this brief still lists v13.3.0 as the latest stable tag. Verify the package/channel you deploy before assuming 13.4.0 is generally available.

**Plugin catalog**
The Signal Desk catalog snapshot captured 388 plugins, 56 catalog records refreshed since Nov 2, and 3 new listings. A catalog metadata refresh is not automatically a new plugin release.

Notable releases:
- Grafana Assistant plugin 2.1.5 — catalog/org listing updated Nov 5.
- Traces Drilldown 3.2.0 — Nov 3; lazy loading in breakdown panels and filter-selection fixes.
- Infinity 4.1.6 — Nov 4; fixes CVE-2026-85063 and a gRPC connection-freeze issue under heavy query load.
- Azure Monitor 13.0.8 — Nov 6; fixes trace-correlation requests on configured hosts and a dimension-filter 403 case.
- Jaeger datasource 13.0.8 — Nov 2; fixes listed security advisories (GHSA-cg2g-xh64-v4q7, GHSA-mrv2-3pqr-j5jr, CVE-2026-93749 and CVE-2023-54404) and a gRPC connection-freeze issue.
- Pyroscope datasource 13.0.10 and Elasticsearch datasource 12.9.5 — Nov 2; both include the gRPC connection-freeze fix.
- Grafana Advisor 1.1.2 — Nov 5; maintenance/fix release.

New catalog listings:
- n8n datasource: catalog entry first seen Nov 5; repository created Oct 13; Apache-2.0. The v1.0.6 GitHub release is still a draft, so treat the listing as early.
- Rack elevation panel: catalog entry first seen Nov 4; repository created Oct 31; Apache-2.0. The v1.0.1 GitHub release is still a draft.
- Wi-Fi coverage panel: catalog entry first seen Nov 4; repository created Oct 29; Apache-2.0; signed community release v0.1.1 and Grafana 13.2+ requirement.

The individual Assistant plugin page lags the current org/catalog listing (it still shows an older 2.0.x version in one page view); use the current catalog/org listing and verify the installed artifact version before upgrades.

## 3. Other monitored projects and vendors

| Project/vendor | Latest relevant state checked | This week's result |
|---|---|---|
| Grafana core | v13.3.0 is the latest stable tag found; What's New references 13.4.0 | Cloud feature updates and plugin releases; self-managed version discrepancy noted |
| Loki | v3.6.20 stable; v4.0.0-rc.3 | Security patch plus major-version RC |
| Tempo | v3.1.1 (Oct 21) | No material release in the window |
| Mimir | v3.2.4 (Oct 30) | No material release in the window |
| Alloy | v1.21.3 stable; v1.22.0-rc.0 | RC only |
| Thanos | v0.42.5 (Oct 27) | No material release in the window |
| Vector | v0.61.0 (Oct 29) | No material release in the window |
| Datadog | Official product/release sources checked | No material launch or pricing/packaging change verified |
| New Relic | Official product/release sources checked | No material launch or pricing/packaging change verified |
| Honeycomb | Official product/release sources checked | No material launch or pricing/packaging change verified |
| Elastic | Official product/release sources checked | No material launch or pricing/packaging change verified |
| Splunk | Official product/release sources checked | No material launch or pricing/packaging change verified |
| Chronosphere | Official product/release sources checked | No material launch or pricing/packaging change verified |

No public price change was verified for Datadog, New Relic, Honeycomb, Elastic, Splunk or Chronosphere during this window. Enterprise pricing is often plan-specific or quote-based; no prices have been inferred.

### Prom++

No Prom++ release was published during Nov 2–9. The latest checked release is [v0.8.18, 2026-10-30](https://github.com/deckhouse/prompp/releases/tag/v0.8.18). It fixes external-label overwrites, a federation head-read regression and a C++ stream-cleanup exception; it updates Go to 1.26.10 for CVE-2026-111943 and updates golang.org/x/net to v0.62.0. This is a carry-forward item, not a new release in this week's window.

## 4. New tools and products discovered

**First-seen date below is this research run (2026-11-09) unless noted. Repository creation/release dates are kept separate from first-seen dates.** None of the early community candidates is promoted to a production recommendation based only on a new repository or a small number of releases.

### Verified new releases / projects

| Candidate | Original evidence/date | Model / license | What it does | Maturity and confidence |
|---|---|---|---|---|
| Watchlog | Repository created Nov 5; first public v0.1.x release Nov 6; v0.2.0 published Nov 8 | AGPL-3.0 core; README describes commercial Enterprise modules | eBPF-oriented Kubernetes/Docker monitoring with service maps, metrics/logs/alerts; v0.2.0 adds MCP server and REST API | Verified new project/release; pre-1.0 and very early. No production-readiness claim. [Repository](https://github.com/watchlog-light/watchlog), [v0.2.0](https://github.com/watchlog-light/watchlog/releases/tag/v0.2.0) |
| Magnife | Repository created Nov 4; v0.3.0 published Nov 6 | MIT | Local macOS OpenTelemetry traces/logs debugger; adds trace comparison and an MCP compare_traces tool | Verified new project/release; pre-1.0 desktop developer tool, not a production telemetry backend. [Repository](https://github.com/NsRF/Magnife), [v0.3.0](https://github.com/NsRF/Magnife/releases/tag/v0.3.0) |

### Newly discovered early community candidates — not confirmed product launches

| Candidate | Repository created | License | Observability relationship | Status |
|---|---|---|---|---|
| obs-tail | Nov 5 | MIT | Small OTLP tail-sampling proxy with latency/error-oriented sampling | No release tags found; early source-only candidate. [Repository](https://github.com/zmaqholok0/obs-tail) |
| ai-monitoring | Nov 3 | Apache-2.0 | OpenCode plugin → OpenTelemetry Collector → VictoriaMetrics → Grafana for coding-agent usage, tokens and cost telemetry | No release tags found; integration/template, not a hosted product. [Repository](https://github.com/accso/ai-monitoring) |
| Fleet | Nov 5 | AGPL-3.0 | Self-hosted live observability for mobile UI test runs; README currently describes Android support | No release tags found; early project. [Repository](https://github.com/moyaver/fleet) |

### Newly discovered existing product — not a new launch this week

**Superlog** was first surfaced by this discovery pass, but its original Product Hunt launch evidence is older: June 3, 2026, with a separate Responder listing on Aug 6, 2026. Its GitHub repository was created June 2 and is Apache-2.0. The project has an open-source core and a commercial hosted offering; exact current pricing was not verified. It is therefore classified as a newly discovered existing tool, not a November launch. [GitHub](https://github.com/superloglabs/superlog) · [Product Hunt listing](https://www.producthunt.com/products/superlog)

### Launch verification

- Product Hunt search did not surface a verified observability-tool launch dated Nov 2–9.
- Hacker News site search did not surface a high-confidence new observability product launch. The direct HN Algolia API endpoint was inaccessible during this run, so HN coverage is incomplete.
- Reddit/community mentions were treated only as discovery leads, not primary evidence.

## 5. Pricing, packaging and licensing

- **VictoriaMetrics Enterprise:** -eula is now the Enterprise agreement-acceptance mechanism; legacy license flags remain compatibility aliases but are deprecated. This is a license-flow change, not a verified price change.
- **Grafana Assistant:** self-managed UI, Grafana Cloud backend, token-based usage billing. Exact rates are plan-dependent; check the current plan before enabling broadly.
- **Watchlog:** AGPL-3.0 core; commercial Enterprise modules are described in the repository. No verified public price.
- **Magnife / obs-tail / ai-monitoring:** MIT / MIT / Apache-2.0 respectively; no commercial pricing surfaced.
- **Fleet:** AGPL-3.0; no hosted tier or price verified in the repository evidence.
- **Superlog:** Apache-2.0 open-source core plus commercial hosted offering; no current price verified.
- No new public pricing or packaging change was verified for Datadog, New Relic, Honeycomb, Elastic, Splunk or Chronosphere this week.

## 6. Impact and severity assessment

| Severity | Finding | Recommended response |
|---|---|---|
| **High** | Fluent Bit 5.2.0 security hardening across HTTP, decompression, OTLP parsing, credentials and regex handling | Upgrade first where inputs are internet-facing or accept untrusted telemetry; regression-test parsers and auth |
| **High** | Loki 3.6.20 dependency security fixes; Pyroscope 2.4.3 security dependency fixes | Patch maintained release branches; do not wait for Loki 4.0 |
| **High** | Collector 0.165.0 zstd decoder memory bounds and recursion-depth cap | Prioritize exposed OTLP/HTTP/gRPC collectors; test payload limits |
| **High** | Grafana Jaeger datasource 13.0.8 and Infinity 4.1.6 security fixes | Update affected plugins and verify plugin compatibility |
| **High** | Collector contrib removes SignalFx receiver | Identify any remaining SignalFx receiver configuration/build references and migrate to OTLP |
| **Medium–High** | Semantic Conventions 1.45.0 and Collector 0.165.0 default convention changes | Run attribute-compatibility checks on dashboards, alerts, OTTL and exporters |
| **Medium–High** | VictoriaMetrics Enterprise -eula migration | Review license acceptance and startup configuration before Enterprise upgrades |
| **Medium** | Prometheus 3.16 query-cost feature | Pilot query-cost estimates and limits in staging before enabling enforcement |
| **Medium** | Loki 4.0.0-rc.3 S3 storage-class restriction | Check bucket storage classes; do not deploy the RC to production |
| **Medium** | Jaeger 2.23 SQL/API v3 and ClickHouse engine requirement | Test query clients, ClickHouse schema creation and AI endpoint auth |
| **Low–Medium** | Watchlog, Magnife, obs-tail, ai-monitoring and Fleet | Track releases and inspect security/build provenance before any evaluation deployment |

No zero-day claim is made from the release notes reviewed. Where vendors did not publish CVE identifiers or severity, this brief says so rather than assigning a severity.

## 7. What an observability engineering leader should do

1. **Close the version inventory gap.** Record the actual deployed Prometheus and Grafana versions, Collector distribution/image digest, build manifest and enabled feature gates. The v0.145.0 Collector comparison here is the requested baseline, not proof that v0.145.0 is deployed.
2. **Prioritize security patches.** Review Fluent Bit 5.2.0, Loki 3.6.20, Pyroscope 2.4.3, Grafana Jaeger datasource 13.0.8 and Infinity 4.1.6 against running versions and exposure.
3. **Stage Collector 0.165.0.** Check for SignalFx receiver use, old disk metric names, flatten_data, Kafka max_buffered_batches, and assumptions that Prometheus scrape meta labels are dropped. Validate zstd limits on real compressed payloads.
4. **Run a semantic-convention compatibility scan.** Search OTTL, dashboards, recording rules, alerts, sampling policies and exporter mappings for the v1.45 RPC/messaging/FaaS/DB renames.
5. **Pilot Prometheus 3.16 query-cost.** Baseline expensive dashboards, ad-hoc queries and recording rules. Test estimated-versus-actual cost before setting hard limits.
6. **Review VictoriaMetrics Enterprise startup flags.** Move templates toward -eula after legal/operations approval; add cgroup throttling telemetry to resource-pressure views.
7. **Check Grafana plugin hygiene.** Update security-relevant plugins; confirm Assistant permissions if Grafana is below 13.3.0; validate Cloud data-flow and token-billing expectations for self-managed Assistant.
8. **Keep pre-releases out of production.** Alloy 1.22.0-rc.0, Loki 4.0.0-rc.3 and Cilium 1.21.0-pre.4 are test candidates only.
9. **Do not add every new GitHub repo to the production watchlist.** Keep Watchlog, Magnife, obs-tail, ai-monitoring and Fleet in a discovery-candidate tier until they demonstrate sustained releases, documentation and a clear maintenance model.

## 8. Upcoming watchlist

| Watch item | Why to watch | Trigger / timing |
|---|---|---|
| OpenTelemetry Collector 0.166.0 | Kafka partition_processing.max_buffered_batches is scheduled for removal; check feature-gate removals and component metadata | Next release; no date asserted |
| Alloy 1.22.0 GA | Validate RC changes, Collector version, Kafka migration and loki.enrich matching arguments | Watch stable tag |
| Loki 4.0 GA | S3 storage-class restriction and compactor changes | Watch next RC / GA |
| VictoriaMetrics 1.156.0 rollout | EULA behavior, new cgroup throttling metric, Azure Workload Identity and per-remote-write queue path | Current release; validate Enterprise and LTS paths |
| Grafana 13.4.0 | What's New references 13.4.0 while stable GitHub tag check still showed 13.3.0 | Confirm release channel/tag |
| Cilium 1.21 GA | Hubble remote-node workload context and agent memory metric | Watch stable release |
| Prometheus next release | Query-cost feedback, native histogram compatibility and main-only flag evolution | No date asserted |
| KubeCon + CloudNativeCon North America 2026 | Likely source of project announcements, roadmap discussions and new ecosystem tools | Nov 9–12, 2026 |
| OpenTelemetry Ecosystem Explorer | Watch expansion beyond Java instrumentation and new version-diff capabilities | Ongoing |

## 9. Source health and discovery coverage

- **CNCF Landscape:** diffed the latest 10 repository commits through Nov 9; no observability-specific landscape additions were found in those commits.
- **OpenTelemetry Registry:** the registry states that it is frozen for new entries/updates. It should not be treated as a live component-launch feed.
- **OpenTelemetry Ecosystem Explorer:** launched Apr 30, 2026; it provides a more active ecosystem/instrumentation discovery surface, currently with detailed Java-agent instrumentation/version coverage. Add it to the discovery-source set.
- **Grafana plugin catalog:** 388 records in the Nov 8 snapshot; 56 records refreshed since Nov 2 and 3 new listings. A metadata refresh is not proof of a new release. Some individual plugin pages lag the current organization/catalog version.
- **Curated directories:** Awesome Observability search results were fragmented and included an LLM-specific list with a March 2026 update; Observability Wiki pages are not a weekly release feed. Neither should be treated as comprehensive.
- **Product Hunt:** no verified Nov 2–9 observability launch found; Superlog is an older June/August listing.
- **Hacker News:** site search found no high-confidence new launch, but the direct Algolia API endpoint failed in this run. This is an explicit blind spot, not proof of no HN activity.
- **GitHub discovery:** fresh repository creation dates and release tags were checked for candidates before classifying them. Repositories without tags/releases remain low-confidence candidates.
- **Vendor coverage:** official Datadog, New Relic, Honeycomb, Elastic, Splunk and Chronosphere sources were checked; no material product/pricing change was verified in this window.
- **Snapshot freshness:** Signal Desk capability/plugin source snapshots were generated Nov 8; release-tag and primary-page checks were refreshed Nov 9. The Collector main inventory therefore represents the Nov 8 source snapshot, not a guaranteed post-Nov-9 commit.
- **Deployment gap:** actual Prometheus and Grafana deployed versions are unknown. The Collector v0.145.0 baseline is an audit reference, not an assertion about the running environment.
- **Pricing gap:** no universal vendor price is inferred. Grafana Assistant is usage/token-based; enterprise vendor pricing is often plan-specific or quote-based.

## 10. Sources and reproducibility

Primary-source repositories/pages checked:
- [Prometheus releases and feature flags](https://github.com/prometheus/prometheus/releases) · [v3.16.0 flags](https://github.com/prometheus/prometheus/blob/v3.16.0/docs/feature_flags.md)
- [OpenTelemetry Collector core releases](https://github.com/open-telemetry/opentelemetry-collector/releases) · [contrib releases](https://github.com/open-telemetry/opentelemetry-collector-contrib/releases) · [feature-gate lifecycle](https://github.com/open-telemetry/opentelemetry-collector/blob/main/featuregate/README.md)
- [OpenTelemetry Semantic Conventions releases](https://github.com/open-telemetry/semantic-conventions/releases)
- [Grafana releases](https://github.com/grafana/grafana/releases) · [Grafana What's New](https://grafana.com/whats-new/) · [plugin catalog](https://grafana.com/grafana/plugins/)
- [Loki releases](https://github.com/grafana/loki/releases) · [Tempo](https://github.com/grafana/tempo/releases) · [Mimir](https://github.com/grafana/mimir/releases) · [Alloy](https://github.com/grafana/alloy/releases) · [Pyroscope](https://github.com/grafana/pyroscope/releases)
- [Jaeger releases](https://github.com/jaegertracing/jaeger/releases) · [Fluent Bit releases](https://github.com/fluent/fluent-bit/releases) · [VictoriaMetrics changelog](https://docs.victoriametrics.com/changelog/)
- [Cilium releases](https://github.com/cilium/cilium/releases) · [Thanos](https://github.com/thanos-io/thanos/releases) · [Vector](https://github.com/vectordotdev/vector/releases)
- [CNCF Landscape](https://github.com/cncf/landscape) · [OpenTelemetry Registry](https://opentelemetry.io/ecosystem/registry/) · [OpenTelemetry Ecosystem Explorer](https://explorer.opentelemetry.io/)
- [Product Hunt Observability](https://www.producthunt.com/topics/observability) · [Observability Wiki](https://observability.wiki/)

**Archive tags:** #weekly-brief #release-notes #capability-audit #feature-gates #tool-discovery #security #licensing #semantic-conventions
