<p align="center">
  <strong>AgentTel</strong><br/>
  <em>Agent-Ready Telemetry</em>
</p>

<p align="center">
  <a href="https://github.com/agenttel/agenttel-sdk/actions/workflows/ci.yml"><img src="https://github.com/agenttel/agenttel-sdk/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://www.apache.org/licenses/LICENSE-2.0"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://opentelemetry.io"><img src="https://img.shields.io/badge/OpenTelemetry-1.39%2B-blueviolet.svg" alt="OpenTelemetry"></a>
  <a href="https://agenttel.dev"><img src="https://img.shields.io/badge/docs-agenttel.dev-blue.svg" alt="Documentation"></a>
</p>

<p align="center">
  <a href="https://central.sonatype.com/search?q=dev.agenttel"><img src="https://img.shields.io/maven-central/v/dev.agenttel/agenttel-core?label=Maven%20Central&logo=apachemaven" alt="Maven Central"></a>
  <a href="https://www.npmjs.com/package/@agenttel/node"><img src="https://img.shields.io/npm/v/@agenttel/node?label=npm&logo=npm" alt="npm"></a>
  <a href="https://pypi.org/project/agenttel/"><img src="https://img.shields.io/pypi/v/agenttel?label=PyPI&logo=python&logoColor=white" alt="PyPI"></a>
  <a href="https://pkg.go.dev/go.agenttel.dev/agenttel-go"><img src="https://img.shields.io/badge/Go-pkg.go.dev-00ADD8?logo=go&logoColor=white" alt="Go Reference"></a>
</p>

<p align="center">
  <a href="https://www.oracle.com/java/technologies/javase/jdk17-archive-downloads.html"><img src="https://img.shields.io/badge/JDK-17%2B-orange.svg?logo=openjdk&logoColor=white" alt="JDK 17+"></a>
  <a href="https://go.dev"><img src="https://img.shields.io/badge/Go-1.24%2B-00ADD8.svg?logo=go&logoColor=white" alt="Go 1.24+"></a>
  <a href="https://nodejs.org"><img src="https://img.shields.io/badge/Node.js-18%2B-339933.svg?logo=nodedotjs&logoColor=white" alt="Node.js 18+"></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="https://www.typescriptlang.org"><img src="https://img.shields.io/badge/TypeScript-4.7%2B-3178C6.svg?logo=typescript&logoColor=white" alt="TypeScript"></a>
</p>

---

AgentTel enriches [OpenTelemetry](https://opentelemetry.io) telemetry with the structured context AI agents need to **autonomously diagnose, reason about, and resolve production incidents** — without human interpretation of dashboards. Works across the full stack: JVM backends (Java, Kotlin, Scala), Go backends, Node.js/TypeScript backends, Python backends (FastAPI, Django, Flask), and browser frontends (TypeScript/JavaScript).

Standard observability answers *"What happened?"* AgentTel adds *"What does an AI agent need to know to act on this?"*

## The Problem

Modern observability tools generate massive volumes of telemetry — traces, metrics, logs — optimized for human consumption through dashboards and alert rules. AI agents tasked with autonomous incident response face critical gaps:

- **No behavioral context** — Spans lack baselines, so agents can't distinguish normal from anomalous
- **No topology awareness** — Agents don't know which services are critical, who owns them, or what depends on what
- **No decision metadata** — Is this operation retryable? Is there a fallback? What's the runbook?
- **No actionable interface** — Agents can read telemetry but can't query live system state or execute remediation

AgentTel closes these gaps at the instrumentation layer.

## Design Philosophy

**Core principle: telemetry should carry enough context for AI agents to reason and act autonomously.**

AgentTel enriches telemetry at three levels — all configurable via YAML, no code changes required:

| Level | Where | What | Example |
|-------|-------|------|---------|
| **Topology** | OTel Resource (once per service) | Service identity, ownership, dependencies | team, tier, on-call channel |
| **Baselines** | Span attributes (per operation) | What "normal" looks like | P50/P99 latency, error rate |
| **Decisions** | Span attributes (per operation) | What an agent is allowed to do | retryable, runbook URL, escalation level |

Topology is set once on the OTel Resource and automatically associated with all telemetry by the SDK. Baselines and decision metadata are attached per-operation on spans. This avoids redundant data on every span while ensuring agents always have the full context.

<p align="center">
  <img src="docs/assets/images/agenttel-overview.png" alt="AgentTel — How it works" width="800"/>
</p>

## Quick Demo

Try AgentTel in one command — starts a demo payment service with OTel Collector and Jaeger:

```bash
cd examples/spring-boot-example
docker compose -f docker/docker-compose.yml up --build
```

Then open [Jaeger](http://localhost:16686) to see enriched traces, [Swagger UI](http://localhost:8080/swagger-ui.html) for the API, and [MCP Tool Docs](http://localhost:8081/mcp/docs) for the agent interface.

## What AgentTel Provides

### Enriched Telemetry (agenttel-core)

Every span is automatically enriched with agent-actionable attributes:

| Category | Attributes | Purpose |
|----------|-----------|---------|
| **Topology** | `agenttel.topology.team`, `tier`, `domain`, `dependencies` | Service identity and dependency graph |
| **Baselines** | `agenttel.baseline.latency_p50_ms`, `error_rate`, `source` | What "normal" looks like for each operation |
| **Decisions** | `agenttel.decision.retryable`, `idempotent`, `runbook_url`, `escalation_level` | What an agent is allowed to do |
| **Anomalies** | `agenttel.anomaly.detected`, `pattern`, `score` | Real-time deviation detection |
| **SLOs** | `agenttel.slo.budget_remaining`, `burn_rate` | Error budget consumption tracking |

### Agent Interface Layer (agenttel-agent)

A complete toolkit for AI agent interaction with production systems:

| Component | Description |
|-----------|-------------|
| **MCP Server** | JSON-RPC server implementing the [Model Context Protocol](https://modelcontextprotocol.io) — exposes telemetry as tools AI agents can call |
| **Health Aggregation** | Real-time service health from span data with operation-level and dependency-level metrics |
| **Incident Context** | Structured incident packages: what's happening, what changed, what's affected, what to do |
| **Remediation Framework** | Registry of executable remediation actions with approval workflows |
| **Action Tracking** | Every agent decision and action recorded as OTel spans for full auditability |
| **Context Formatters** | Prompt-optimized output formats (compact, full, JSON) tuned for LLM context windows |

### Frontend Telemetry (agenttel-web)

Browser SDK for agent-ready frontend observability:

| Feature | Description |
|---------|-------------|
| **Auto-Instrumentation** | Page loads (Navigation Timing API), SPA navigation, `fetch`/`XMLHttpRequest` interception, click/submit interactions, JavaScript errors |
| **Journey Tracking** | Multi-step user funnel tracking with completion rates, abandonment detection, and duration baselines |
| **Anomaly Detection** | Client-side pattern detection — rage clicks, API failure cascades, slow page loads, error loops, funnel drop-offs |
| **Cross-Stack Correlation** | W3C Trace Context injection on all outgoing requests; backend trace ID extraction from responses |
| **Route Baselines** | Per-route configuration of expected page load times, API response times, error rates, and business criticality |
| **Decision Metadata** | Escalation levels, runbook URLs, retry policies, and fallback pages per route |

### Instrumentation Agent (agenttel-instrument)

IDE-integrated MCP server for automated instrumentation setup:

| Tool | Description |
|------|-------------|
| `analyze_codebase` | Scans Java/Spring Boot source code — detects endpoints, dependencies, and framework |
| `instrument_backend` | Generates backend config — Gradle/Maven dependencies, annotations, agenttel.yml |
| `instrument_frontend` | Generates frontend config — React route detection, criticality inference, SDK initialization |
| `validate_instrumentation` | Validates agenttel.yml completeness against source code |
| `suggest_improvements` | Analyzes config and suggests fixes — missing baselines, uncovered endpoints, stale thresholds |
| `apply_improvements` | Auto-applies low-risk improvements using live health data; flags high-risk items for review |

### GenAI Instrumentation (agenttel-genai)

Full observability for AI/ML workloads on the JVM:

| Framework | Approach | Coverage |
|-----------|----------|----------|
| **Spring AI** | SpanProcessor enrichment of existing Micrometer spans | Framework tag, cost calculation |
| **LangChain4j** | Decorator-based full instrumentation | Chat, embeddings, RAG retrieval |
| **Anthropic SDK** | Client wrapper | Messages API with token/cost tracking |
| **OpenAI SDK** | Client wrapper | Chat completions with token/cost tracking |
| **AWS Bedrock** | Client wrapper | Converse API with token/cost tracking |

### Agent Observability (agenttel-agentic)

Full lifecycle tracing for AI agents with 70+ semantic attributes:

| Feature | Description |
|---------|-------------|
| **Invocation Lifecycle** | Goal, status, step count, max steps for each agent execution |
| **Reasoning Steps** | Thought, action, observation, evaluation, revision tracking |
| **Tool Calls** | Tool name, success/error/timeout status per call |
| **Task Decomposition** | Nested task breakdown with depth and parent tracking |
| **Orchestration Patterns** | Sequential, parallel, evaluator-optimizer, handoff, ReAct, orchestrator-workers |
| **Cost Aggregation** | Automatic LLM cost rollup from GenAI spans to agent sessions |
| **Guardrails** | Block, warn, log, escalate actions with named guardrails |
| **Human Checkpoints** | Approval, feedback, correction gates with wait time tracking |
| **Loop Detection** | Detects stuck reasoning loops (identical tool calls) |
| **Quality Signals** | Goal achievement, human interventions, eval scores |
| **RAG Pipeline** | Retriever and reranker spans with relevance scoring |
| **Error Classification** | Source (LLM/tool/agent/guardrail/timeout/network), retryability |

Three integration styles — programmatic, annotation, or YAML config:

**Programmatic:**
```java
AgentTracer tracer = AgentTracer.create(openTelemetry)
    .agentName("incident-responder")
    .agentType(AgentType.SINGLE)
    .build();

try (AgentInvocation inv = tracer.invoke("Diagnose high latency")) {
    inv.step(StepType.THOUGHT, "Need to check service metrics");
    try (ToolCallScope tool = inv.toolCall("get_service_health")) {
        tool.success();
    }
    inv.complete(true);
}
```

**@AgentMethod annotation (Spring Boot):**
```java
@AgentMethod(name = "incident-responder", type = "single", maxSteps = 100)
public IncidentReport diagnose(String incidentId) {
    // Automatically wrapped in AgentInvocation — no manual tracer calls
    return analyzeAndRespond(incidentId);
}
```

**YAML config (Spring Boot):**
```yaml
agenttel:
  agentic:
    agents:
      incident-responder:
        type: single
        max-steps: 100
        loop-threshold: 5
```

## Quick Start

AgentTel supports multiple integration paths — pick what fits your stack:

| Path | Best For | Effort |
|------|----------|--------|
| Spring Boot Starter | Spring Boot applications | Add dependency + YAML config |
| **Go SDK** | **Go services (net/http, Gin, gRPC)** | **`go get` + YAML config** |
| **Node.js SDK** | **Express / Fastify services** | **`npm install` + YAML config** |
| **Python SDK** | **FastAPI / Python services** | **`pip install` + YAML config** |
| JavaAgent Extension | Any JVM app (no code changes) | JVM flag + YAML config |
| Web SDK | Browser/SPA applications | `npm install` + init call |
| Instrument Agent | IDE-assisted setup | Run MCP server in IDE |

### Backend: Spring Boot

#### 1. Add Dependencies

**Maven:**

```xml
<dependencies>
    <!-- Core: span enrichment, baselines, anomaly detection, SLO tracking -->
    <dependency>
        <groupId>dev.agenttel</groupId>
        <artifactId>agenttel-spring-boot-starter</artifactId>
        <version>0.4.0-alpha</version>
    </dependency>

    <!-- Optional: GenAI instrumentation -->
    <dependency>
        <groupId>dev.agenttel</groupId>
        <artifactId>agenttel-genai</artifactId>
        <version>0.4.0-alpha</version>
    </dependency>

    <!-- Optional: Agent interface layer (MCP server, incident context, remediation) -->
    <dependency>
        <groupId>dev.agenttel</groupId>
        <artifactId>agenttel-agent</artifactId>
        <version>0.4.0-alpha</version>
    </dependency>
</dependencies>
```

**Gradle:**

```kotlin
// build.gradle.kts
dependencies {
    // Core: span enrichment, baselines, anomaly detection, SLO tracking
    implementation("dev.agenttel:agenttel-spring-boot-starter:0.4.0-alpha")

    // Optional: GenAI instrumentation
    implementation("dev.agenttel:agenttel-genai:0.4.0-alpha")

    // Optional: Agent interface layer (MCP server, incident context, remediation)
    implementation("dev.agenttel:agenttel-agent:0.4.0-alpha")
}
```

#### 2. Configure Your Service

All enrichment is driven by YAML configuration -- no code changes needed:

```yaml
# application.yml
agenttel:
  # Topology: set once on the OTel Resource, associated with all telemetry
  topology:
    team: payments-platform
    tier: critical
    domain: commerce
    on-call-channel: "#payments-oncall"
  dependencies:
    - name: postgres
      type: database
      criticality: required
      timeout-ms: 5000
      circuit-breaker: true
    - name: stripe-api
      type: rest_api
      criticality: required
      fallback: "Return cached pricing"

  # Reusable operational profiles — reduce repetition across operations
  profiles:
    critical-write:
      retryable: false
      escalation-level: page_oncall
      safe-to-restart: false
    read-only:
      retryable: true
      idempotent: true
      escalation-level: notify_team

  # Per-operation baselines and decision metadata
  # Use bracket notation [key] for operation names with special characters
  operations:
    "[POST /api/payments]":
      profile: critical-write
      expected-latency-p50: "45ms"
      expected-latency-p99: "200ms"
      expected-error-rate: 0.001
      retryable: true               # overrides profile default
      idempotent: true
      runbook-url: "https://wiki/runbooks/process-payment"
    "[GET /api/payments/{id}]":
      profile: read-only
      expected-latency-p50: "15ms"
      expected-latency-p99: "80ms"

  baselines:
    rolling-window-size: 1000
    rolling-min-samples: 10
  anomaly-detection:
    z-score-threshold: 3.0
```

#### 3. Optional: Annotate for IDE Support

Annotations are optional -- YAML config above is sufficient. Use `@AgentOperation` when you want IDE autocomplete and compile-time validation. Reference profiles to avoid repeating values:

```java
@AgentOperation(profile = "critical-write")
@PostMapping("/api/payments")
public ResponseEntity<PaymentResult> processPayment(@RequestBody PaymentRequest req) {
    // Your business logic — spans are enriched automatically
}
```

> When both YAML config and annotations define the same operation, YAML config takes priority. Per-operation values override profile defaults.

#### 4. Start the MCP Server (Optional)

```java
// Expose telemetry to AI agents via MCP
McpServer mcp = new AgentTelMcpServerBuilder()
    .port(8081)
    .contextProvider(agentContextProvider)
    .remediationExecutor(remediationExecutor)
    .build();
mcp.start();
```

AI agents can now call tools like `get_service_health`, `get_incident_context`, `list_remediation_actions`, and `execute_remediation` over JSON-RPC.

#### 5. What You Get

**Resource attributes** (set once per service, associated with all telemetry):

```
agenttel.topology.team         = "payments-platform"
agenttel.topology.tier         = "critical"
agenttel.topology.domain       = "commerce"
agenttel.topology.on_call_channel = "#payments-oncall"
agenttel.topology.dependencies = [{"name":"postgres","type":"database",...}]
```

**Span attributes** (per operation, only on operations with registered metadata):

```
agenttel.baseline.latency_p50_ms = 45.0
agenttel.baseline.latency_p99_ms = 200.0
agenttel.baseline.error_rate     = 0.001
agenttel.baseline.source         = "static"
agenttel.decision.retryable      = true
agenttel.decision.runbook_url    = "https://wiki/runbooks/process-payment"
agenttel.decision.escalation_level = "page_oncall"
agenttel.anomaly.detected        = false
agenttel.slo.budget_remaining    = 0.85
```

When an incident occurs, agents get structured context via MCP:

```
=== INCIDENT inc-a3f2b1c4 ===
SEVERITY: HIGH
SUMMARY: POST /api/payments experiencing elevated error rate (5.2%)

## WHAT IS HAPPENING
Error Rate: 5.2% (baseline: 0.1%)
Latency P50: 312ms (baseline: 45ms)
Patterns: ERROR_RATE_SPIKE

## WHAT CHANGED
Last Deploy: v2.1.0 at 2025-01-15T14:30:00Z

## WHAT IS AFFECTED
Scope: operation_specific
User-Facing: YES
Affected Deps: stripe-api

## SUGGESTED ACTIONS
  - [HIGH] rollback_deployment: Rollback to previous version (NEEDS APPROVAL)
  - [MEDIUM] enable_circuit_breakers: Circuit break stripe-api
```

### Backend: Python (FastAPI)

#### 1. Install

```bash
pip install agenttel[fastapi]

# Optional extras
pip install agenttel[openai]       # OpenAI instrumentation
pip install agenttel[anthropic]    # Anthropic instrumentation
pip install agenttel[langchain]    # LangChain instrumentation
pip install agenttel[all]          # Everything
```

#### 2. Configure

```yaml
# agenttel.yml
agenttel:
  topology:
    service-name: payment-service
    team: payments-platform
    tier: critical
    domain: commerce
    on-call-channel: "#payments-oncall"
  operations:
    "POST /api/payments":
      expected-latency-p50: 45ms
      expected-latency-p99: 200ms
      retryable: true
      runbook-url: "https://wiki/runbooks/process-payment"
  slo:
    availability:
      target: 0.999
      type: availability
```

#### 3. Instrument

```python
from fastapi import FastAPI
from agenttel.fastapi import instrument_fastapi

app = FastAPI()
instrument_fastapi(app)  # One-line integration
```

`instrument_fastapi()` attaches the AgentTel span processor to your existing OpenTelemetry `TracerProvider` (or creates one if none is set), instruments the app with `opentelemetry-instrumentation-fastapi`, and enriches each HTTP server span with topology, baselines and decision attributes for its `METHOD /route` — identical attributes to the JVM SDK.

### Backend: Go

#### 1. Install

```bash
go get go.agenttel.dev/agenttel-go@latest
```

#### 2. Configure

```yaml
# agenttel.yml — same format as JVM/Python SDKs
agenttel:
  topology:
    service-name: payment-service
    team: payments-platform
    tier: critical
  operations:
    "POST /api/payments":
      expected-latency-p50: 45ms
      expected-latency-p99: 200ms
      retryable: true
```

#### 3. Instrument

```go
import (
    "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"

    agenttel "go.agenttel.dev/agenttel-go"
    agmw "go.agenttel.dev/agenttel-go/middleware/http"
)

engine, err := agenttel.New().WithConfigFile("agenttel.yml").Build()
if err != nil {
    log.Fatal(err)
}

tp := sdktrace.NewTracerProvider(
    sdktrace.WithResource(engine.Resource()),          // topology on the resource
    sdktrace.WithSpanProcessor(engine.SpanProcessor()),
    sdktrace.WithBatcher(exporter),
)
otel.SetTracerProvider(tp)

// otelhttp creates the server span; AgentTel enriches it for the matched "METHOD /route"
handler := otelhttp.NewHandler(agmw.Middleware(agmw.WithEngine(engine))(mux), "server")
```

Requires `go.opentelemetry.io/otel/sdk` v1.39.0+.

Also supports **Gin** (`middleware/gin`) and **gRPC** (`middleware/grpc`) out of the box. See [Go Quickstart](docs/getting-started/go-quickstart.md) for details.

### Backend: Node.js (Express / Fastify)

#### 1. Install

```bash
npm install @agenttel/node @opentelemetry/api @opentelemetry/sdk-trace-node @opentelemetry/instrumentation-http
```

#### 2. Configure

```yaml
# agenttel.yml — same format as all other SDKs
agenttel:
  topology:
    service-name: payment-service
    team: payments-platform
    tier: critical
  operations:
    "POST /api/payments":
      expected-latency-p50: 45ms
      expected-latency-p99: 200ms
      retryable: true
```

#### 3. Instrument

```typescript
import { AgentTelEngine, expressMiddleware } from '@agenttel/node';

const engine = AgentTelEngine.fromConfigFile('agenttel.yml');

// Register the processor with your tracer provider (alongside your exporter)
const provider = new NodeTracerProvider({
  resource: new Resource(engine.resourceAttributes()),
  spanProcessors: [engine.spanProcessor, new BatchSpanProcessor(exporter)],
});
provider.register();
registerInstrumentations({ instrumentations: [new HttpInstrumentation(), new ExpressInstrumentation()] });

app.use(expressMiddleware({ engine }));  // topology, baselines and decisions on the server span
```

Works under plain `node` as ESM (`import`) or CommonJS (`require`), Node.js 18+.

Also supports **Fastify** (`fastifyPlugin`). See [Node.js Quickstart](docs/getting-started/nodejs-quickstart.md) for details.

### Frontend: Browser SDK

```bash
npm install @agenttel/web
```

```typescript
import { AgentTelWeb } from '@agenttel/web';

AgentTelWeb.init({
  appName: 'checkout-web',
  appVersion: '1.0.0',
  environment: 'production',
  collectorEndpoint: '/otlp',

  routes: {
    '/checkout/:step': {
      businessCriticality: 'revenue',
      baseline: { pageLoadP50Ms: 800, apiCallP50Ms: 300 },
      decision: { escalationLevel: 'page_oncall', runbookUrl: 'https://wiki/runbooks/checkout' },
    },
  },

  journeys: {
    checkout: {
      steps: ['/products', '/cart', '/checkout/shipping', '/checkout/payment', '/confirmation'],
      baseline: { completionRate: 0.65, avgDurationS: 300 },
    },
  },

  anomalyDetection: {
    rageClickThreshold: 3,
    apiFailureCascadeThreshold: 3,
    errorLoopThreshold: 5,
  },
});
```

The SDK automatically instruments page loads, SPA navigation, API calls, clicks, and errors — with cross-stack correlation via W3C Trace Context headers.

### IDE: Instrument Agent

Run the instrument agent as an MCP server in your IDE (Cursor, VS Code, etc.):

```bash
pip install agenttel-instrument
agenttel-instrument --config instrument.yml
```

Then ask your IDE agent: *"Analyze my codebase and generate AgentTel configuration"* — it will scan your endpoints, detect dependencies, and generate a complete `agenttel.yml`.

## Module Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Your Application                            │
│    Backend: application.yml + @AgentOperation                       │
│    Frontend: AgentTelWeb.init(config)                               │
├──────────────────────────┬──────────────────┬───────────────────────┤
│  agenttel-spring-boot-   │  agenttel-       │  agenttel-web         │
│  starter                 │  javaagent-      │  (@agenttel/web)      │
│  Auto-config · BPP · AOP │  extension       │  Browser SDK          │
│  (Spring Boot apps)      │  (any JVM app)   │  (TypeScript/JS)      │
├──────────────┬───────────┴──┬───────────────┴───────────────────────┤
│agenttel-core │agenttel-genai│     agenttel-agent                    │
│              │              │                                       │
│ SpanProcessor│ LangChain4j  │ MCP Server (JSON-RPC)                 │
│ Baselines    │ Spring AI    │ Health Aggregation                    │
│ Anomaly      │ Anthropic SDK│ Incident Context + Reporting          │
│  Detection   │ OpenAI SDK   │ Remediation Framework                 │
│ SLO Tracking │ Bedrock SDK  │ Trend Analysis · SLO Reports          │
│ Pattern      │ Cost Calc    │ Executive Summaries                   │
│  Matching    │              │ Cross-Stack Context                   │
├──────────────┴──────────────┴───────────────────────────────────────┤
│                          agenttel-api                                │
│       @AgentOperation · AgentTelAttributes · Data Models            │
├─────────────────────────────────────────────────────────────────────┤
│                      OpenTelemetry SDK                               │
└─────────────────────────────────────────────────────────────────────┘

  agenttel-go (Go SDK — full feature parity)
  Core · net/http · Gin · gRPC · GenAI · Agent/MCP · Agentic Observability

  agenttel-node (Node.js SDK — full feature parity)
  Core · Express · Fastify · GenAI · Agent/MCP · Agentic Observability

  agenttel-python (Python SDK — full feature parity)
  Core · FastAPI · GenAI · Agent/MCP · Agentic Observability

  agenttel-instrument (IDE MCP Server — Python)
  Codebase analysis · Config generation · Validation · Auto-improvements
```

| Module | Artifact | Description |
|--------|----------|-------------|
| `agenttel-api` | `dev.agenttel:agenttel-api` | Annotations, attribute constants, enums, data models. Zero runtime dependencies. |
| `agenttel-core` | `dev.agenttel:agenttel-core` | Runtime engine — span enrichment, static + rolling baselines, z-score anomaly detection, pattern matching, SLO tracking, structured events. |
| `agenttel-genai` | `dev.agenttel:agenttel-genai` | GenAI instrumentation — LangChain4j wrappers, Spring AI enrichment, Anthropic/OpenAI/Bedrock SDK instrumentation, cost calculation. |
| `agenttel-agent` | `dev.agenttel:agenttel-agent` | Agent interface layer — MCP server, health aggregation, incident context, remediation, trend analysis, SLO reports, executive summaries, cross-stack context. |
| `agenttel-agentic` | `dev.agenttel:agenttel-agentic` | Agent observability — lifecycle, reasoning, orchestration patterns (ReAct, sequential, parallel, handoff, evaluator-optimizer), cost aggregation, quality signals, guardrails, loop detection. |
| `agenttel-javaagent` | `dev.agenttel:agenttel-javaagent` | Zero-code OTel javaagent extension. Drop-in enrichment for any JVM app — no Spring dependency. |
| `agenttel-spring-boot-starter` | `dev.agenttel:agenttel-spring-boot-starter` | Spring Boot auto-configuration. Single dependency for Spring Boot apps. |
| `agenttel-web` | `@agenttel/web` (npm) | Browser telemetry SDK — auto-instrumentation of page loads, navigation, API calls, errors, Web Vitals, journey tracking, anomaly detection, W3C trace propagation. |
| `agenttel-go` | `go.agenttel.dev/agenttel-go` (Go module) | Go SDK — full feature parity. Core enrichment, net/http + Gin + gRPC middleware, GenAI instrumentation, MCP agent interface, agentic observability. |
| `agenttel-node` | `@agenttel/node` (npm) | Node.js SDK — full feature parity. Core enrichment, Express + Fastify middleware, GenAI instrumentation, MCP agent interface, agentic observability. |
| `agenttel-types` | `@agenttel/types` (npm) | Shared TypeScript types, enums, and attribute constants for `@agenttel/web` and `@agenttel/node`. |
| `agenttel-python` | `agenttel` (pip) | Python SDK — full feature parity with JVM SDK. Core enrichment, FastAPI integration, GenAI instrumentation, MCP agent interface, agentic observability. |
| `agenttel-instrument` | `agenttel-instrument` (pip) | IDE MCP server — codebase analysis, config generation, validation, improvement suggestions, and auto-apply for both backend and frontend instrumentation. |
| `agenttel-testing` | `dev.agenttel:agenttel-testing` | Test utilities for verifying span enrichment. |

## Documentation

**Full documentation site: [agenttel.dev](https://agenttel.dev)**

| Document | Description |
|----------|-------------|
| [Project Overview](docs/01-PROJECT-OVERVIEW.md) | Vision, motivation, and design philosophy |
| [Semantic Conventions](docs/02-SEMANTIC-CONVENTIONS.md) | Complete attribute and event schema reference |
| [Architecture](docs/03-ARCHITECTURE.md) | Technical architecture, data flow, and extension points |
| [Agent Layer](docs/04-AGENT-LAYER.md) | MCP server, incident context, remediation, and agent interaction |
| [GenAI Instrumentation](docs/05-GENAI-INSTRUMENTATION.md) | LLM framework instrumentation and cost tracking |
| [API Reference](docs/06-API-REFERENCE.md) | Annotations, programmatic API, and configuration reference |
| [Roadmap](docs/07-ROADMAP.md) | Implementation phases and release plan |
| [Design Considerations](docs/08-DESIGN-CONSIDERATIONS.md) | Trade-offs, evolution path, and future direction |
| [API Documentation](docs/09-API-DOCUMENTATION.md) | Swagger UI, MCP tool docs, and aggregated Javadoc |

## Examples

Working examples to get you started quickly:

| Example | Description | Run Command |
|---------|-------------|-------------|
| [Spring Boot Example](examples/spring-boot-example) | Payment service with span enrichment, topology, baselines, anomaly detection, and MCP server | `./gradlew :examples:spring-boot-example:bootRun` |
| [LangChain4j Example](examples/langchain4j-example) | GenAI tracing with LangChain4j — chat spans, token tracking, and cost calculation | `./gradlew :examples:langchain4j-example:run` |
| [Go Service Example](examples/go-service-example) | Go payment service with net/http middleware, topology, baselines, anomaly detection | `cd examples/go-service-example && go run .` |
| [Express Example](examples/express-example) | Node.js payment service with Express middleware, topology, baselines, anomaly detection | `cd examples/express-example && npm run dev` |
| [React Checkout Example](agenttel-web/examples/react-checkout) | React SPA with frontend telemetry — journey tracking, anomaly detection, cross-stack correlation | `cd agenttel-web/examples/react-checkout && npm start` |

Each example includes a README with step-by-step instructions and curl commands to exercise the instrumentation.

## Compatibility

### Backend (JVM)

| Component | Supported Versions |
|-----------|--------------------|
| Java | 17, 21 |
| OpenTelemetry SDK | 1.59.0+ |
| Spring Boot | 3.4.x |
| Spring AI | 1.0.0+ (optional) |
| LangChain4j | 1.0.0+ (optional) |
| Anthropic Java SDK | 2.0.0+ (optional) |
| OpenAI Java SDK | 4.0.0+ (optional) |
| AWS Bedrock SDK | 2.30.0+ (optional) |

### Backend (Go)

| Component | Supported Versions |
|-----------|--------------------|
| Go | 1.24+ |
| OpenTelemetry SDK (`go.opentelemetry.io/otel/sdk`) | 1.39.0+ |
| net/http | Standard library (+ `otelhttp` for server spans) |
| Gin | 1.11+ with `otelgin` (optional) |
| gRPC | 1.79+ (optional) |

### Backend (Node.js)

| Component | Supported Versions |
|-----------|--------------------|
| Node.js | 18+ (ESM and CommonJS) |
| TypeScript | 5.0+ |
| OpenTelemetry JS SDK | 1.25.0+ (1.x) |
| Express | 4.x / 5.x (optional) |
| Fastify | 4.x+ (optional) |

### Frontend (Browser)

| Component | Supported Versions |
|-----------|--------------------|
| TypeScript | 4.7+ |
| Modern browsers | Chrome, Firefox, Safari, Edge (ES2020+) |
| React (example) | 18+ |

### Backend (Python)

| Component | Supported Versions |
|-----------|--------------------|
| Python | 3.11+ |
| OpenTelemetry SDK | 1.20.0+ |
| FastAPI | 0.100.0+ (optional) |
| OpenAI SDK | 1.0+ (optional) |
| Anthropic SDK | 0.20+ (optional) |
| LangChain | 0.1+ (optional) |
| AWS Bedrock (boto3) | 1.28+ (optional) |

### Tooling

| Component | Supported Versions |
|-----------|--------------------|
| Python (instrument agent) | 3.11+ |

## Build Tool Support

AgentTel publishes standard Maven artifacts to Maven Central. Your application can use **any build tool** — Maven, Gradle, sbt, Bazel, or anything that resolves Maven dependencies.

### Maven

```xml
<dependency>
    <groupId>dev.agenttel</groupId>
    <artifactId>agenttel-spring-boot-starter</artifactId>
    <version>0.4.0-alpha</version>
</dependency>
```

### Gradle (Kotlin DSL)

```kotlin
implementation("dev.agenttel:agenttel-spring-boot-starter:0.4.0-alpha")
```

### Gradle (Groovy DSL)

```groovy
implementation 'dev.agenttel:agenttel-spring-boot-starter:0.4.0-alpha'
```

### All Available Artifacts

**Maven/Gradle (JVM):**

| Group ID | Artifact ID | Description |
|----------|------------|-------------|
| `dev.agenttel` | `agenttel-api` | Annotations and constants (zero dependencies) |
| `dev.agenttel` | `agenttel-core` | Runtime engine |
| `dev.agenttel` | `agenttel-genai` | GenAI instrumentation |
| `dev.agenttel` | `agenttel-agent` | Agent interface layer (MCP, health, incidents, reporting) |
| `dev.agenttel` | `agenttel-agentic` | Agent observability (lifecycle, orchestration, cost, quality) |
| `dev.agenttel` | `agenttel-javaagent` | Zero-code OTel javaagent extension |
| `dev.agenttel` | `agenttel-spring-boot-starter` | Spring Boot auto-configuration |
| `dev.agenttel` | `agenttel-testing` | Test utilities |

**Go module:**

| Module | Description |
|--------|-------------|
| `go.agenttel.dev/agenttel-go` | Go SDK — core enrichment, middleware (net/http, Gin, gRPC), GenAI, Agent/MCP, agentic observability |

**npm (Browser + Node.js):**

| Package | Description |
|---------|-------------|
| `@agenttel/node` | Node.js SDK — core enrichment, middleware (Express, Fastify), GenAI, Agent/MCP, agentic observability |
| `@agenttel/types` | Shared TypeScript types, enums, and attribute constants |
| `@agenttel/web` | Browser telemetry SDK with auto-instrumentation |

**pip (Python SDK + Tooling):**

| Package | Description |
|---------|-------------|
| `agenttel` | Python SDK — core, FastAPI, GenAI, agent/MCP, agentic observability |
| `agenttel-instrument` | IDE MCP server for instrumentation automation |

## Zero-Code Mode (JavaAgent Extension)

For applications where you cannot add a library dependency, use the javaagent extension. No code changes, no Spring dependency:

```bash
java -javaagent:agenttel-javaagent.jar \
     -Dagenttel.config.file=agenttel.yml \
     -jar myapp.jar
```

The javaagent bundles the OTel agent with AgentTel enrichment in a single JAR. It reads configuration from `agenttel.yml`, system properties (`-Dagenttel.topology.team=payments`), or environment variables (`AGENTTEL_TOPOLOGY_TEAM=payments`).

## FAQ

See [FAQ.md](FAQ.md) for frequently asked questions about code changes, performance, telemetry size, compatibility, and more.

## Building from Source

```bash
# Java (requires JDK 17+)
./gradlew clean build
./gradlew test
./gradlew :agenttel-agent:build

# Go (requires Go 1.24+)
cd agenttel-go && go test -race ./...

# Node.js (requires Node.js 18+)
cd agenttel-node && npm ci && npm test

# Shared TypeScript types
cd agenttel-types && npm ci && npx tsc --noEmit
```

## Contributing

Contributions are welcome. Please read the [Contributing Guide](CONTRIBUTING.md) for build instructions, PR guidelines, and code style conventions. See the [Architecture](docs/03-ARCHITECTURE.md) document for design guidance.

For security issues, please see our [Security Policy](SECURITY.md).

## License

AgentTel is released under the [Apache License 2.0](LICENSE).
