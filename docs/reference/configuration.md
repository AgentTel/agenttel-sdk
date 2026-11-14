# Configuration Reference

Complete reference for every configuration property in AgentTel -- backend (Spring Boot and JavaAgent), frontend (browser SDK), and tooling.

> **Tip:** This page is searchable. Use `Ctrl+F` / `Cmd+F` to find a specific property.

---

## Quick Reference

| Section | Properties | Description |
|---------|-----------|-------------|
| [Core](#core) | 1 | Enable/disable |
| [Topology](#topology) | 5 | Service identity and ownership |
| [Dependencies](#dependencies) | 8 per entry | Dependency declarations |
| [Consumers](#consumers) | 3 per entry | Consumer declarations |
| [Profiles](#profiles) | 6 per profile | Reusable operation defaults |
| [Operations](#operations) | 10 per operation | Per-operation baselines and decisions |
| [Baselines](#baselines) | 3 | Rolling baseline configuration |
| [Anomaly Detection](#anomaly-detection) | 2 | Detection tuning |
| [Attribute Names](#attribute-names) | 1 | `agenttel.*` or standard OpenTelemetry names |
| [Deployment](#deployment) | 3 | Deployment metadata |
| [Agent Roles](#agent-roles) | 1 per role | Role-based permissions |
| [Agentic](#agentic) | 3 global + 6 per agent | Agent identity and safety guardrails |
| [Frontend SDK](#frontend-sdk) | ~25 | Browser telemetry configuration |

---

## Configuration Sources

| Runtime | Source | Format |
|---------|--------|--------|
| Spring Boot Starter | `application.yml` / `application.properties` | Standard Spring Boot property binding |
| JavaAgent Extension | `agenttel.yml` config file | YAML (same schema as Spring Boot) |
| JavaAgent Extension | System properties | `-Dagenttel.topology.team=payments` |
| JavaAgent Extension | Environment variables | `AGENTTEL_TOPOLOGY_TEAM=payments` |
| Frontend SDK | JavaScript object passed to `initAgentTel()` | TypeScript / JavaScript |

**JavaAgent resolution order** (highest priority first): system properties > environment variables > config file.

---

## Core {#core}

Master switch for all AgentTel enrichment. When disabled, the `SpanProcessor` becomes a no-op and no AgentTel attributes are added to spans.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.enabled` | boolean | `true` | Enable/disable all AgentTel enrichment |

!!! example "Example"
    ```yaml
    agenttel:
      enabled: true
    ```

!!! tip "Tuning"
    Set to `false` in local development if you want vanilla OTel traces without AgentTel attributes. Topology resource attributes are still registered (they come from the `ResourceProvider` SPI) but span-level enrichment is skipped.

---

## Topology {#topology}

Service identity and ownership metadata. Set once per service, attached to all telemetry as OTel Resource attributes.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.topology.team` | string | `""` | Owning team identifier |
| `agenttel.topology.tier` | string | `standard` | Service criticality: `critical`, `standard`, `internal`, `experimental` |
| `agenttel.topology.domain` | string | `""` | Business domain |
| `agenttel.topology.on-call-channel` | string | `""` | Escalation channel (e.g., Slack channel) |
| `agenttel.topology.repo-url` | string | `""` | Source repository URL |

!!! example "Example"
    ```yaml
    agenttel:
      topology:
        team: payments-platform
        tier: critical
        domain: commerce
        on-call-channel: "#payments-oncall"
        repo-url: "https://github.com/acme/payment-service"
    ```

!!! tip "Tuning"
    - Set `tier: critical` for user-facing, revenue-impacting services to ensure agents prioritize them during incidents
    - The `on-call-channel` value is included in incident context when agents escalate

---

## Dependencies {#dependencies}

Declares downstream dependencies. Each entry describes a service, database, or external API that this service calls. Used by agents to understand blast radius and cascade failures.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.dependencies[].name` | string | **required** | Dependency name |
| `agenttel.dependencies[].type` | string | **required** | Type: `database`, `rest_api`, `grpc`, `message_broker`, `cache`, `object_store`, `identity_provider`, `internal_service`, `external_api` |
| `agenttel.dependencies[].criticality` | string | `required` | Impact if unavailable: `required`, `degraded`, `optional` |
| `agenttel.dependencies[].protocol` | string | `""` | Communication protocol (e.g., `https`, `grpc`, `jdbc`) |
| `agenttel.dependencies[].timeout-ms` | int | `0` | Configured timeout in milliseconds |
| `agenttel.dependencies[].circuit-breaker` | boolean | `false` | Whether a circuit breaker protects this dependency |
| `agenttel.dependencies[].fallback` | string | `""` | Fallback behavior when dependency is unavailable |
| `agenttel.dependencies[].health-endpoint` | string | `""` | Health check endpoint URL |

!!! example "Example"
    ```yaml
    agenttel:
      dependencies:
        - name: payment-gateway
          type: external_api
          criticality: required
          timeout-ms: 5000
          circuit-breaker: true
          fallback: "Return cached pricing from last successful gateway call"
        - name: postgres-orders
          type: database
          criticality: required
          timeout-ms: 3000
    ```

!!! tip "Tuning"
    - Use `criticality: degraded` for dependencies where the service can still function with reduced quality
    - Setting `circuit-breaker: true` tells agents this dependency has automatic protection, reducing urgency for transient failures

---

## Consumers {#consumers}

Declares upstream consumers of this service. Used by agents to understand who is impacted when this service degrades.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.consumers[].name` | string | **required** | Consumer service name |
| `agenttel.consumers[].pattern` | string | `sync` | Communication pattern: `synchronous`, `asynchronous`, `batch`, `streaming` (short forms: `sync`, `async`) |
| `agenttel.consumers[].sla-latency-ms` | int | `0` | Consumer's latency SLA in milliseconds |

!!! example "Example"
    ```yaml
    agenttel:
      consumers:
        - name: checkout-service
          pattern: synchronous
          sla-latency-ms: 500
        - name: notification-service
          pattern: async
    ```

---

## Profiles {#profiles}

Reusable sets of operational defaults. Profiles define decision context (retry policy, escalation, etc.) that multiple operations can reference to reduce repetition.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.profiles.<name>.retryable` | boolean | `false` | Default retry policy |
| `agenttel.profiles.<name>.idempotent` | boolean | `false` | Default idempotency |
| `agenttel.profiles.<name>.runbook-url` | string | `""` | Default runbook URL |
| `agenttel.profiles.<name>.fallback-description` | string | `""` | Default fallback description |
| `agenttel.profiles.<name>.escalation-level` | string | `auto_resolve` | Default escalation: `auto_resolve`, `notify_team`, `page_oncall`, `incident_commander` |
| `agenttel.profiles.<name>.safe-to-restart` | boolean | `true` | Default restart safety |

!!! example "Example"
    ```yaml
    agenttel:
      profiles:
        critical-write:
          retryable: false
          idempotent: false
          escalation-level: page_oncall
          safe-to-restart: false
        read-only:
          retryable: true
          idempotent: true
          escalation-level: notify_team
          safe-to-restart: true
    ```

!!! tip "Tuning"
    Create profiles for common patterns (reads vs. writes, internal vs. external) to keep config DRY. Operations referencing a profile can still override individual fields.

---

## Operations {#operations}

Per-operation metadata: baselines (expected latency, error rate) and decision context (what to do when things go wrong). This tells agents exactly what "normal" looks like and how to respond to anomalies.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.operations."[OP_NAME]".profile` | string | `""` | Reference to a named profile for defaults |
| `agenttel.operations."[OP_NAME]".expected-latency-p50` | string | `""` | Expected P50 latency (e.g., `"45ms"`, `"1.5s"`) |
| `agenttel.operations."[OP_NAME]".expected-latency-p99` | string | `""` | Expected P99 latency |
| `agenttel.operations."[OP_NAME]".expected-error-rate` | double | `-1` (unset) | Expected error rate as a fraction (0.0-1.0) |
| `agenttel.operations."[OP_NAME]".retryable` | boolean | `false` | Whether the operation is safe to retry |
| `agenttel.operations."[OP_NAME]".idempotent` | boolean | `false` | Whether the operation is idempotent |
| `agenttel.operations."[OP_NAME]".runbook-url` | string | `""` | Operational runbook URL |
| `agenttel.operations."[OP_NAME]".fallback-description` | string | `""` | Fallback behavior description |
| `agenttel.operations."[OP_NAME]".escalation-level` | string | `auto_resolve` | Escalation: `auto_resolve`, `notify_team`, `page_oncall`, `incident_commander` |
| `agenttel.operations."[OP_NAME]".safe-to-restart` | boolean | `true` | Whether safe to restart while this operation is in-flight |

!!! example "Example"
    ```yaml
    agenttel:
      operations:
        "[POST /api/payments]":
          profile: critical-write
          expected-latency-p50: "45ms"
          expected-latency-p99: "200ms"
          expected-error-rate: 0.001
          retryable: true
          runbook-url: "https://wiki/runbooks/process-payment"
        "[GET /api/payments/{id}]":
          profile: read-only
          expected-latency-p50: "15ms"
          expected-latency-p99: "80ms"
    ```

!!! warning "Bracket Notation Required"
    Operation names containing special characters (spaces, slashes) **must** use bracket notation `"[OP_NAME]"` in YAML. Without brackets, Spring Boot normalizes map keys by stripping non-alphanumeric characters, causing a silent key mismatch. See [Gotchas](#gotchas).

!!! tip "Tuning"
    - Profile defaults are applied first, then per-operation overrides take precedence
    - An `expected-error-rate` of `-1` means "unset" -- anomaly detection is not applied for error rate on that operation
    - Latency strings support suffixes: `ms` (milliseconds), `s` (seconds), `m` (minutes)

---

## Baselines {#baselines}

Configures how AgentTel computes baseline statistics for anomaly detection.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.baselines.source` | string | `static` | Baseline source: `static` (from config) or `rolling` (from live traffic) |
| `agenttel.baselines.rolling-window-size` | int | `1000` | Observations per sliding window |
| `agenttel.baselines.rolling-min-samples` | int | `10` | Minimum samples before a rolling baseline is valid |

!!! example "Example"
    ```yaml
    agenttel:
      baselines:
        source: static
        rolling-window-size: 1000
        rolling-min-samples: 10
    ```

!!! tip "Tuning"
    Use `static` baselines with well-known SLOs for deterministic detection. Use `rolling` for services with variable load patterns. Increase `rolling-min-samples` for noisy services to avoid false positives during cold start.

---

## Anomaly Detection {#anomaly-detection}

Controls built-in anomaly detection that flags spans deviating from expected baselines.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.anomaly-detection.enabled` | boolean | `true` | Enable/disable anomaly detection |
| `agenttel.anomaly-detection.z-score-threshold` | double | `3.0` | Z-score threshold for anomaly flagging |

!!! example "Example"
    ```yaml
    agenttel:
      anomaly-detection:
        enabled: true
        z-score-threshold: 3.0
    ```

!!! tip "Tuning"
    A z-score of `3.0` means ~0.3% of normal observations are flagged. Lower to `2.0` for stricter detection on critical operations; raise to `4.0` to reduce alert fatigue on noisy operations.

---

## Attribute Names {#attribute-names}

Chooses which attribute names AgentTel emits. Every SDK (JVM, Go, Node.js, Python) supports it.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.attributes.namespace` | string | `legacy` | `legacy`, `standard` or `both` |

| Value | Effect |
|-------|--------|
| `legacy` | Only `agenttel.*` names, as in earlier releases |
| `standard` | Each `agenttel.*` attribute or event that has a standard name is emitted under that name instead. The rest keep their `agenttel.*` name |
| `both` | Each such attribute is emitted under both names. Events keep their `agenttel.*` name |

Standard names are the existing OpenTelemetry attribute where one exists (for example `agenttel.topology.repo_url` becomes `vcs.repository.url.full` and `agenttel.error.root_exception` becomes `exception.type`), and otherwise a provisional `reliability.*` name proposed for OpenTelemetry semantic conventions. The mapping comes from the `upstream` field in `attributes.json`; see [Attribute Schema](attribute-schema.md). An attribute already on the span under the standard name (such as an `exception.type` set by instrumentation) is never overwritten.

The mapping applies at export time to span attributes, span events and the resource, and to the topology resource and events AgentTel emits. AgentTel's own processing (baselines, anomaly detection, the MCP server) is unaffected.

On the JVM (javaagent and Spring Boot starter) AgentTel wraps the span exporter for you. In Go, Node.js and Python you register the exporter yourself, so pass it through the engine for span attributes to be mapped:

| SDK | Exporter wrapping |
|-----|-------------------|
| Go | `sdktrace.WithBatcher(engine.WrapSpanExporter(exporter))` |
| Node.js | `new BatchSpanProcessor(engine.wrapExporter(exporter))` |
| Python | `BatchSpanProcessor(engine.wrap_exporter(exporter))` |

Without it, `standard` and `both` still apply to the topology resource and to events, but span attributes keep their `agenttel.*` names. The Go and Node.js SDKs also read `AGENTTEL_ATTRIBUTES_NAMESPACE`.

!!! example "Example"
    ```yaml
    agenttel:
      attributes:
        namespace: both   # migrate dashboards before switching to standard
    ```

!!! warning "Provisional names"
    `reliability.*` names are a proposal and may change before OpenTelemetry adopts them. Use `both` while migrating queries and dashboards.

---

## Deployment {#deployment}

Deployment metadata emitted as a span event on application startup.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.deployment.emit-on-startup` | boolean | `true` | Emit deployment info event on startup |
| `agenttel.deployment.version` | string | `""` | Application version string |
| `agenttel.deployment.commit-sha` | string | `""` | Git commit SHA |

!!! example "Example"
    ```yaml
    agenttel:
      deployment:
        emit-on-startup: true
        version: "2.4.1"
        commit-sha: "a1b2c3d"
    ```

---

## Agent Roles {#agent-roles}

Role-based access control for AI agents interacting via the MCP server.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.agent-roles.<role>` | list of string | built-in defaults | Permissions: `READ`, `DIAGNOSE`, `REMEDIATE`, `ADMIN` |

Built-in defaults: `observer` (READ), `diagnostician` (READ + DIAGNOSE), `operator` (READ + DIAGNOSE + REMEDIATE), `admin` (all).

!!! example "Example"
    ```yaml
    agenttel:
      agent-roles:
        observer:
          - READ
        sre-agent:
          - READ
          - DIAGNOSE
          - REMEDIATE
    ```

!!! tip "Tuning"
    Start with `READ` + `DIAGNOSE` only and grant `REMEDIATE` after validating agent behavior in staging.

---

## Agentic {#agentic}

Configuration for the agent observability layer (`agenttel-agentic`). Defines agent identity, safety guardrails, and per-agent overrides. These settings are applied automatically when `AgentTracer.invoke()` is called or when a method annotated with `@AgentMethod` executes.

### Global Defaults

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.agentic.loop-threshold` | int | `3` | Global default for loop detection threshold |
| `agenttel.agentic.default-max-steps` | long | `0` (unlimited) | Global default max steps per invocation |

### Per-Agent Configuration

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `agenttel.agentic.agents.<name>.type` | string | `""` | Agent type: `single`, `orchestrator`, `worker`, `evaluator`, `critic`, `router` |
| `agenttel.agentic.agents.<name>.framework` | string | `""` | Framework name (e.g., `langchain4j`, `spring-ai`, `custom`) |
| `agenttel.agentic.agents.<name>.version` | string | `""` | Agent version string |
| `agenttel.agentic.agents.<name>.max-steps` | long | `0` | Max steps guardrail (0 = use global default) |
| `agenttel.agentic.agents.<name>.loop-threshold` | int | `0` | Loop detection threshold (0 = use global default) |
| `agenttel.agentic.agents.<name>.cost-budget-usd` | double | `0` | Cost budget in USD (0 = unlimited) |

!!! example "Example"
    ```yaml
    agenttel:
      agentic:
        loop-threshold: 3
        default-max-steps: 50
        agents:
          incident-responder:
            type: react
            framework: langchain4j
            version: "2.0"
            max-steps: 100
            loop-threshold: 5
            cost-budget-usd: 2.0
          code-reviewer:
            type: worker
            max-steps: 20
    ```

!!! tip "Tuning"
    - Per-agent `max-steps` and `loop-threshold` override global defaults
    - Use `cost-budget-usd` to set spending limits for agents that make many LLM calls
    - Agent names in YAML must match the name passed to `AgentTracer.invoke()` or `@AgentMethod(name = ...)`

!!! info "Config Priority"
    ```
    YAML config  >  @AgentMethod annotation  >  AgentTracer.Builder defaults
    ```
    When both YAML config and `@AgentMethod` define the same agent, YAML values take precedence. This follows the same priority model as `@AgentOperation` for operations.

---

## Frontend SDK {#frontend-sdk}

Configuration for the `@agenttel/web` browser SDK, passed as a JavaScript object to `initAgentTel()`.

### Core Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `appName` | string | **required** | Application name |
| `appVersion` | string | -- | Application version |
| `environment` | string | -- | Environment: `production`, `staging`, `development` |
| `collectorEndpoint` | string | **required** | OTLP HTTP endpoint URL |
| `team` | string | -- | Owning team |
| `domain` | string | -- | Business domain |

### Route Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `routes.<pattern>.businessCriticality` | string | -- | `revenue`, `engagement`, `internal` |
| `routes.<pattern>.baseline.pageLoadP50Ms` | number | -- | Expected page load P50 (ms) |
| `routes.<pattern>.baseline.pageLoadP99Ms` | number | -- | Expected page load P99 (ms) |
| `routes.<pattern>.baseline.apiCallP50Ms` | number | -- | Expected API response P50 (ms) |
| `routes.<pattern>.baseline.interactionErrorRate` | number | -- | Expected error rate (0.0-1.0) |
| `routes.<pattern>.decision.escalationLevel` | string | -- | Escalation level |
| `routes.<pattern>.decision.runbookUrl` | string | -- | Runbook URL |
| `routes.<pattern>.decision.fallbackPage` | string | -- | Fallback route on failure |
| `routes.<pattern>.decision.retryOnFailure` | boolean | -- | Retry on page load failure |

### Journey Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `journeys.<name>.steps` | string[] | **required** | Ordered route list forming a user journey |
| `journeys.<name>.baseline.completionRate` | number | -- | Expected completion rate (0.0-1.0) |
| `journeys.<name>.baseline.avgDurationS` | number | -- | Expected average duration (seconds) |

### Anomaly Detection

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `anomalyDetection.rageClickThreshold` | number | `3` | Clicks to trigger rage click detection |
| `anomalyDetection.rageClickWindowMs` | number | `2000` | Rage click time window (ms) |
| `anomalyDetection.apiFailureCascadeThreshold` | number | `3` | API failures to trigger cascade detection |
| `anomalyDetection.apiFailureCascadeWindowMs` | number | `10000` | Cascade time window (ms) |
| `anomalyDetection.slowPageLoadMultiplier` | number | `2.0` | Multiplier over P50 for slow page loads |
| `anomalyDetection.errorLoopThreshold` | number | `5` | Errors to trigger error loop detection |
| `anomalyDetection.errorLoopWindowMs` | number | `30000` | Error loop time window (ms) |

!!! example "Example"
    ```javascript
    import { initAgentTel } from '@agenttel/web';
    initAgentTel({
      appName: 'checkout-spa',
      collectorEndpoint: 'https://otel-collector.acme.com:4318',
      environment: 'production',
      team: 'frontend-platform',
      routes: {
        '/checkout': {
          businessCriticality: 'revenue',
          baseline: { pageLoadP50Ms: 800, apiCallP50Ms: 200 },
          decision: { escalationLevel: 'page_oncall' }
        }
      },
      journeys: {
        checkout: {
          steps: ['/products/:id', '/cart', '/checkout', '/confirmation'],
          baseline: { completionRate: 0.85 }
        }
      }
    });
    ```

---

## JavaAgent Extension {#javaagent-extension}

The AgentTel javaagent reads the same config schema but from different sources, enabling zero-code instrumentation for non-Spring applications.

Specify the config file via `-Dagenttel.config.file=agenttel.yml` or `AGENTTEL_CONFIG_FILE` env var. If neither is set, AgentTel looks for `agenttel.yml` in the working directory.

```bash
java -javaagent:agenttel-javaagent.jar \
     -Dagenttel.config.file=/etc/agenttel/agenttel.yml \
     -jar myapp.jar
```

> **Note:** In the javaagent config file, bracket notation for operation names is **not** required because Jackson YAML parses keys directly (no Spring Boot normalization).

### System Property and Environment Variable Mapping

| YAML Property | System Property | Environment Variable |
|--------------|----------------|---------------------|
| `agenttel.enabled` | `-Dagenttel.enabled` | `AGENTTEL_ENABLED` |
| `agenttel.topology.team` | `-Dagenttel.topology.team` | `AGENTTEL_TOPOLOGY_TEAM` |
| `agenttel.topology.tier` | `-Dagenttel.topology.tier` | `AGENTTEL_TOPOLOGY_TIER` |
| `agenttel.topology.domain` | `-Dagenttel.topology.domain` | `AGENTTEL_TOPOLOGY_DOMAIN` |
| `agenttel.topology.on-call-channel` | `-Dagenttel.topology.on-call-channel` | `AGENTTEL_TOPOLOGY_ON_CALL_CHANNEL` |
| `agenttel.topology.repo-url` | `-Dagenttel.topology.repo-url` | `AGENTTEL_TOPOLOGY_REPO_URL` |
| `agenttel.attributes.namespace` | `-Dagenttel.attributes.namespace` | `AGENTTEL_ATTRIBUTES_NAMESPACE` |

---

## Gotchas {#gotchas}

### 1. Spring Boot Map Key Normalization

Spring Boot's `@ConfigurationProperties` normalizes map keys by stripping non-alphanumeric, non-hyphen characters. Operation names like `POST /api/payments` **must** use bracket notation:

```yaml
# CORRECT -- bracket notation preserves the exact key
operations:
  "[POST /api/payments]":
    expected-latency-p50: "45ms"

# WRONG -- Spring Boot strips spaces and slashes, causing silent key mismatch
operations:
  POST /api/payments:
    expected-latency-p50: "45ms"
```

This applies only to the Spring Boot starter. The javaagent config file (parsed by Jackson) does not have this restriction.

### 2. Config Priority: YAML Over Annotations

When both YAML and annotations (`@AgentObservable`, `@AgentOperation`) are present, YAML takes precedence. Annotations are applied only if the property is not already registered via YAML.

```
YAML config  >  @AgentOperation annotation  >  profile defaults  >  hardcoded defaults
```

### 3. Profile Resolution Order

When an operation references a profile:

1. **Hardcoded defaults** (e.g., `retryable=false`, `escalationLevel=auto_resolve`)
2. **Profile defaults** override hardcoded defaults
3. **Per-operation explicit values** override profile defaults

```yaml
profiles:
  critical-write:
    retryable: false          # profile default
    escalation-level: page_oncall

operations:
  "[POST /api/payments]":
    profile: critical-write
    retryable: true           # overrides profile's retryable=false
    # escalation-level inherited from profile: page_oncall
```

---

## Complete Example {#complete-example}

A full `application.yml` with all AgentTel sections:

```yaml
agenttel:
  enabled: true
  topology:
    team: payments-platform
    tier: critical
    domain: commerce
    on-call-channel: "#payments-oncall"
    repo-url: "https://github.com/acme/payment-service"
  dependencies:
    - name: payment-gateway
      type: external_api
      criticality: required
      timeout-ms: 5000
      circuit-breaker: true
      fallback: "Return cached pricing from last successful gateway call"
    - name: postgres-orders
      type: database
      criticality: required
      timeout-ms: 3000
  consumers:
    - name: checkout-service
      pattern: synchronous
      sla-latency-ms: 500
    - name: notification-service
      pattern: async
  profiles:
    critical-write:
      retryable: false
      escalation-level: page_oncall
      safe-to-restart: false
    read-only:
      retryable: true
      idempotent: true
      escalation-level: notify_team
  operations:
    "[POST /api/payments]":
      profile: critical-write
      expected-latency-p50: "45ms"
      expected-latency-p99: "200ms"
      expected-error-rate: 0.001
      retryable: true
      idempotent: true
      runbook-url: "https://wiki/runbooks/process-payment"
    "[GET /api/payments/{id}]":
      profile: read-only
      expected-latency-p50: "15ms"
      expected-latency-p99: "80ms"
  baselines:
    source: static
    rolling-window-size: 1000
    rolling-min-samples: 10
  anomaly-detection:
    enabled: true
    z-score-threshold: 3.0
  deployment:
    emit-on-startup: true
    version: "2.4.1"
    commit-sha: "a1b2c3d"
  agent-roles:
    observer: [READ]
    diagnostician: [READ, DIAGNOSE]
    operator: [READ, DIAGNOSE, REMEDIATE]
    admin: [READ, DIAGNOSE, REMEDIATE, ADMIN]
  agentic:
    loop-threshold: 3
    default-max-steps: 50
    agents:
      incident-responder:
        type: react
        framework: langchain4j
        version: "2.0"
        max-steps: 100
        loop-threshold: 5
        cost-budget-usd: 2.0
      code-reviewer:
        type: worker
        max-steps: 20
```
