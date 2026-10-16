# Project Overview

## Vision

AgentTel is an open-source telemetry library and semantic convention extension for [OpenTelemetry](https://opentelemetry.io) that makes application telemetry **natively consumable by AI agents**. It works across the full stack — JVM backends (Java, Kotlin, Scala), Python backends (FastAPI, Django, Flask), and browser frontends (TypeScript/JavaScript) — bridging the gap between human-oriented observability and the structured, contextual data that autonomous systems require.

## Motivation

### The Observability Gap

Today's observability stack — traces, metrics, logs — is designed for human operators working through dashboards and alert rules. When AI agents are tasked with autonomous incident response, they face fundamental limitations:

**Missing Context.** A span showing `POST /api/payments` with 312ms latency tells an agent nothing without knowing the baseline is 45ms, the operation is retryable, the service is Tier 1, and the team to page is `#payments-oncall`.

**No Behavioral Baselines.** Agents cannot distinguish "this is normal for a Tuesday morning" from "this is a 5x latency spike" without baseline data attached to the telemetry itself. External baseline systems add latency and require separate integrations.

**No Topology Awareness.** Understanding that `payment-service` depends on `postgres` (required, 5s timeout, circuit breaker enabled) and `stripe-api` (required, fallback to cached pricing) requires knowledge that isn't embedded in today's telemetry.

**No Decision Metadata.** When an agent detects an anomaly, it needs to know: Can I retry this? Is there a fallback? Should I page someone or auto-remediate? Today, this information lives in runbooks, tribal knowledge, and configuration files — not in the telemetry stream.

**No Actionable Interface.** Even with enriched telemetry, agents need a structured API to query live system state, understand incidents in context, and execute remediation — not just read historical traces.

### The Solution

AgentTel enriches telemetry at the instrumentation layer — the earliest and most reliable point in the data pipeline — with seven categories of agent-ready context:

1. **Topology** — Service identity, ownership, dependency graph, consumer relationships
2. **Baselines** — Static and rolling latency/error baselines per operation, with confidence scoring
3. **Decision Metadata** — Retryability, idempotency, fallbacks, runbooks, escalation levels
4. **Anomaly Detection** — Z-score deviation detection with pattern recognition
5. **SLO Tracking** — Error budget consumption with burn rate alerting
6. **Error Classification** — Categorizing errors into actionable types (dependency timeout, code bug, rate limited) so agents know whether to retry, rollback, or escalate
7. **Autonomous Capabilities** — Structured playbooks, parameterized action specs, action feedback loops, causal analysis, and change correlation for full observe → diagnose → act → verify loops
8. **Multi-Agent Support** — Agent identity tracking, role-based tool permissions, and shared incident sessions enabling coordinator, parallel, swarm, and hierarchical agent patterns

It also provides an **agent interface layer** that packages this telemetry into structured formats AI agents can consume via the Model Context Protocol (MCP), complete with incident context building, remediation execution, multi-agent collaboration, and full action auditability.

### Why Now

- **OTel GenAI semantic conventions are still in development** — there is an opportunity to influence them before stabilization
- **JVM GenAI instrumentation is fragmented** — Spring AI has basic Micrometer support, community projects are in SNAPSHOT, and there is no coverage for Anthropic, Bedrock, or OpenAI Java SDKs
- **Enterprise Java has a massive installed base** but is underserved by the Python-centric AI observability ecosystem
- **Industry validation** from Logz.io, Mezmo, Sawmills, Splunk, and Datadog confirms that agent-consumable telemetry is the frontier of observability

## Design Principles

### Annotations-First API

Developers declare operational semantics alongside their code:

```java
@AgentOperation(
    expectedLatencyP50 = "45ms",
    retryable = true,
    runbookUrl = "https://wiki/runbooks/process-payment"
)
```

This keeps context co-located with the code it describes, reviewed in pull requests, and versioned with the application.

### Strict OpenTelemetry Extension

AgentTel is a semantic convention extension to OpenTelemetry, not a replacement. It uses the standard `SpanProcessor` and `SpanExporter` interfaces, adds attributes under the `agenttel.*` namespace, and coexists with all existing OTel conventions. Any OTel-compatible backend can ingest AgentTel-enriched spans.

### Zero-Overhead When Disabled

All enrichment is conditional. When no annotations are present or AgentTel is not configured, the library adds zero overhead. Baseline computation uses lock-free ring buffers. Anomaly detection is O(1) per span.

### Framework-Agnostic Core

The core library depends only on the OpenTelemetry SDK. Spring Boot integration is provided through a separate starter module. Frontend telemetry is provided through a standalone TypeScript SDK. The architecture supports future adapters for Quarkus, Micronaut, and other frameworks.

### Optional Dependencies

GenAI instrumentation libraries (Spring AI, LangChain4j, Anthropic SDK, OpenAI SDK, AWS Bedrock SDK) are all `compileOnly` dependencies. They activate only when the corresponding library is present on the classpath. Users are never forced to pull in libraries they don't use.

## Project Structure

```
agenttel/
├── agenttel-api/                 # Annotations, attributes, enums (zero dependencies)
├── agenttel-core/                # Runtime engine (OTel SDK dependency only)
├── agenttel-genai/               # GenAI instrumentation (optional framework deps)
├── agenttel-agent/               # Agent interface layer (MCP, health, incidents, reporting)
├── agenttel-agentic/             # Agentic observability (agent tracing, orchestration)
├── agenttel-spring-boot-starter/ # Spring Boot auto-configuration
├── agenttel-javaagent/           # Zero-code OTel javaagent extension
├── agenttel-python/              # Python SDK (full feature parity with JVM SDK)
├── agenttel-web/                 # Browser SDK (TypeScript) — frontend telemetry
├── agenttel-instrument/          # IDE MCP server (Python) — instrumentation automation
├── agenttel-testing/             # Test utilities
├── examples/
│   ├── spring-boot-example/      # Spring Boot + AgentTel demo
│   └── langchain4j-example/      # LangChain4j + AgentTel demo
├── dashboards/                   # Grafana dashboard templates
└── docs/                         # This documentation
```

## Module Summary

| Module | Artifact | Dependencies | Description |
|--------|----------|-------------|-------------|
| `agenttel-api` | `dev.agenttel:agenttel-api` | None | Annotations, attribute constants, enums, data models |
| `agenttel-core` | `dev.agenttel:agenttel-core` | OTel SDK, Jackson | Span enrichment, baselines, anomaly detection, SLO tracking, events |
| `agenttel-genai` | `dev.agenttel:agenttel-genai` | OTel SDK + optional GenAI libs | LangChain4j, Spring AI, Anthropic/OpenAI/Bedrock instrumentation |
| `agenttel-agent` | `dev.agenttel:agenttel-agent` | OTel SDK, Jackson | MCP server, health aggregation, incident context, remediation, trend analysis, SLO reports, executive summaries, cross-stack context |
| `agenttel-spring-boot-starter` | `dev.agenttel:agenttel-spring-boot-starter` | Spring Boot | Auto-configuration for Spring Boot applications |
| `agenttel-javaagent` | `dev.agenttel:agenttel-javaagent` | OTel Javaagent | Zero-code enrichment for any JVM app — no Spring dependency |
| `agenttel-web` | `@agenttel/web` (npm) | TypeScript, ES2020+ | Browser telemetry SDK — page loads, navigation, API calls, journeys, anomaly detection, cross-stack correlation |
| `agenttel-python` | `agenttel` (pip) | OTel SDK, Pydantic, PyYAML | Python SDK — core enrichment, FastAPI, GenAI, agent/MCP, agentic observability |
| `agenttel-instrument` | `agenttel-instrument` (pip) | Python 3.11+ | IDE MCP server — codebase analysis, config generation, validation, auto-improvements |
| `agenttel-testing` | `dev.agenttel:agenttel-testing` | OTel SDK Testing | Test utilities for verifying span enrichment |

## Target Audience

- **Platform engineers** building internal developer platforms with AI-assisted incident response
- **SRE teams** adopting AIOps tooling that needs structured telemetry
- **Backend developers** who want their JVM services to be "agent-ready" with minimal code changes
- **Frontend developers** who want browser telemetry with journey tracking, anomaly detection, and cross-stack correlation
- **AI/ML engineers** building autonomous agents that interact with production systems

## Current Status

AgentTel is in **alpha** (v0.4.0-alpha). The core instrumentation, GenAI support, and agent interface layer are implemented and tested. The API surface may evolve before 1.0.

## Further Reading

- [Semantic Conventions](../concepts/semantic-conventions.md) — Complete attribute and event schema
- [Architecture](../concepts/architecture.md) — Technical design and data flow
- [MCP Server & Agent Tools](../guides/mcp-server.md) — MCP server, agent interface
- [Incident Response](../guides/incident-response.md) — Health, incidents, remediation
- [GenAI Instrumentation](../guides/genai-instrumentation.md) — LLM framework instrumentation
- [Attribute Dictionary](../reference/attribute-dictionary.md) — Every attribute documented
- [Configuration Reference](../reference/configuration.md) — All configuration properties
- [Roadmap](../project/roadmap.md) — Release plan and future work
