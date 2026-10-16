# Changelog

All notable changes to AgentTel are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0-alpha] - Unreleased

Every SDK now reads the same `agenttel.yml` and puts the same attributes on HTTP server spans. Package versions: Maven `0.4.0-alpha`, npm `0.4.0-alpha.0`, PyPI `0.4.0a1`, Go `agenttel-go/v0.4.0-alpha`.

### Shared configuration format (Python, Node.js, Go)

All SDKs now accept the Spring Boot dialect:

- `agenttel:` root, kebab-case keys (`on-call-channel`, `expected-latency-p50`, `runbook-url`)
- `operations` is a map keyed by `"METHOD /route"`. Spring-style `"[POST /api/payments]"` and bare keys are equivalent, and `:id` and `{id}` path parameters match each other
- latencies are duration strings (`45ms`, `1.5s`, `2m`) or plain numbers of milliseconds
- `profiles` hold shared decision defaults, and an operation's explicit values override its profile
- Each SDK's previous dialect (no root, snake_case or camelCase keys, Node's `operations` list) still loads and logs a deprecation warning

### Python (`agenttel`)

- **Fixed:** FastAPI server spans now get baselines and decisions. The middleware resolves the route template and enriches the active server span, so it no longer depends on the span name at `on_start`. `opentelemetry-instrumentation-fastapi` names that span `POST` at `on_start` and renames it after routing.
- **Fixed:** `instrument_fastapi()` reuses an already registered SDK `TracerProvider` instead of creating a second one. Topology is merged into its resource. It also calls `FastAPIInstrumentor.instrument_app()` when the app isn't instrumented yet.
- **Fixed:** decision attributes now use the `attributes.json` names (`agenttel.decision.*`, previously `agenttel.operation.*`), and on-call is now `agenttel.topology.on_call_channel` (previously `oncall_channel`). The old Python constant names remain as aliases.
- **Fixed:** `ConsumptionPattern.ASYNC` value is `async` (was `async_`); added `EscalationLevel.AUTO_RESOLVE` (new default, as on the JVM).
- **Fixed:** `examples/fastapi-example` imported the non-existent `BatchSpanExportProcessor` and used enum values the loader rejects.
- `AgentTelMiddleware` is now a pure ASGI middleware; `auto_configure()` delegates to `instrument_fastapi()`.

### Node.js (`@agenttel/node`)

- **Fixed:** the package loads under plain Node.js 18/20/22 as ESM (`import`) and CommonJS (`require`). Relative imports use `.js` extensions (enforced by building with `NodeNext`), and `dist/cjs/package.json` marks the CommonJS build.
- **Added:** Express and Fastify middleware set decision attributes (`retryable`, `idempotent`, `runbook_url`, `escalation_level`, `safe_to_restart`, `fallback_*`). Pass `{ engine }` to set topology, baselines and decisions in one go. Express re-checks the matched route template before the response ends, and Fastify records `http.route`.
- **Added:** `AgentTelEngine.fromConfigFile()`, `builder().withConfigFile()`, `engine.operations` (decision registry), `engine.resourceAttributes()`, `engine.topologyRegistry` alias, `parseConfig`, `normalizeOperationName`, `parseDurationMs`, `enrichOperation`.
- **Fixed:** the express/fastify examples now register `engine.spanProcessor` and HTTP instrumentation.
- Tests: real Express and Fastify servers with OTel instrumentation against the built package (`npm test`), and `npm run test:pack`, which installs the packed tarball into a fresh project.

### Go (`go.agenttel.dev/agenttel-go`)

- **Fixed:** YAML `operations` become static baselines and decision context in `Builder.Build()` (previously only `WithStaticBaselines` registered baselines).
- **Added:** `operations` package (`Registry`, `Decision`, `Normalize`, `ParseDurationMs`), `enrich` package, `Engine.Operations`, `Engine.Resource()` / `Engine.ResourceAttributes()`, `ParseConfig`, `LoadConfigFile` (alias of `LoadConfig`), and `WithEngine` / `WithDecisions` options for the net/http, Gin and gRPC middleware.
- **Added:** net/http middleware sets decision attributes and, for Go 1.22+ `ServeMux` patterns, records `http.route` and matches `GET /items/{id}` after routing.
- **Fixed:** `examples/go-service-example` and `examples/gin-example` compile and run against the real API (`agenttel.New().WithConfigFile(...).Build()`, `engine.SpanProcessor()`, `otelhttp` / `otelgin`).
- **Docs:** minimum versions are Go 1.24 and `go.opentelemetry.io/otel/sdk` v1.39.0 (previously documented as 1.22 / 1.33.0).
- **Breaking (config struct only):** YAML tags on `AgentTelConfig` are now kebab-case. camelCase files still load, with a warning.

### JVM

- No functional changes; version bump only.

## [0.3.0-alpha] - 2026-03-20

### Added

**Go SDK (agenttel-go) — Full Feature Parity**

Core (`go.agenttel.dev/agenttel-go`):
- Semantic attributes (~60 constants) matching Java/Python SDKs
- All enums (`ServiceTier`, `ErrorCategory`, `DependencyType`, etc.)
- YAML configuration loader from `agenttel.yml`
- `AgentTelSpanProcessor` with baseline/anomaly/SLO enrichment
- Rolling baseline provider, composite baseline, z-score anomaly detection
- SLO tracker with error budget calculation
- Error classifier, topology registry, structured event emitter
- HTTP, Gin, and gRPC middleware

GenAI Instrumentation (sub-modules):
- `go.agenttel.dev/agenttel-go/genai/openai` — OpenAI SDK wrapper (sync + streaming)
- `go.agenttel.dev/agenttel-go/genai/anthropic` — Anthropic SDK wrapper (sync + streaming)
- `GenAiSpanBuilder` for consistent span creation with cost calculation

Agentic Observability:
- `AgenticTracer` — builder pattern API for agent tracing
- Invocation, step, tool call scopes with auto-closing
- Orchestration patterns: sequential, parallel, eval-loop

Agent Interface:
- MCP server (JSON-RPC 2.0 over HTTP) with tool registry
- Bearer token auth with API key registry and RBAC
- Health aggregation, incident context, remediation registry

**Node.js SDK (@agenttel/node) — Full Feature Parity**

Core (`@agenttel/node`):
- Semantic attributes (~60 constants) matching Java/Python/Go SDKs
- All enums with TypeScript type safety
- YAML configuration loader from `agenttel.yml`
- `AgentTelSpanProcessor` with baseline/anomaly/SLO enrichment
- Rolling baseline provider, composite baseline, z-score anomaly detection
- SLO tracker with error budget calculation
- Error classifier, topology registry, structured event emitter
- Express and Fastify middleware

GenAI Instrumentation:
- OpenAI SDK wrapper (sync + streaming)
- Anthropic SDK wrapper (sync + streaming)
- `GenAiSpanBuilder` for consistent span creation with cost calculation

Agentic Observability:
- `AgenticTracer` — builder pattern API for agent tracing
- Invocation, step, tool call scopes
- Orchestration patterns: sequential, parallel, eval-loop

Agent Interface:
- MCP server (JSON-RPC 2.0 over HTTP) with tool registry
- Bearer token auth with API key registry and RBAC

**Shared Types (@agenttel/types)**
- Canonical TypeScript attribute constants, enums, and interfaces
- Dual ESM/CJS build for use by @agenttel/node and browser SDK

**Cross-SDK Improvements**
- `attributes.json` — canonical attribute schema (single source of truth)
- `scripts/validate-attributes.sh` — CI parity enforcement across all 4 SDKs
- Unified CI pipeline: Java (JDK 17/21), Go (1.24), Node (20), Python (3.11/3.12/3.13)
- MCP server auth (Bearer token + RBAC) added to Java SDK
- Example apps: Go net/http, Gin, Express, Fastify, FastAPI, Spring Boot

**Python SDK (agenttel-python) — Full Feature Parity**

Core (`agenttel`):
- Semantic attributes (~60 constants) matching `AgentTelAttributes.java`
- All enums (`ServiceTier`, `ErrorCategory`, `DependencyType`, etc.)
- Pydantic data models (`OperationBaseline`, `DependencyDescriptor`, `SloStatus`, etc.)
- YAML configuration loader from `agenttel.yml`
- `AgentTelSpanProcessor` — OTel SpanProcessor with baseline/anomaly/SLO enrichment
- `AgentTelEngine` — high-level orchestrator wiring all components
- Rolling baseline provider with thread-safe ring buffer
- Composite baseline provider (rolling + static with priority ordering)
- Z-score anomaly detection with pattern matching (latency degradation, error spike, cascade failure)
- SLO tracker with error budget calculation and alert levels
- Error classifier (exception type + message pattern matching)
- Causality tracker with dependency state changes and causal chain analysis
- Topology registry for service metadata
- Structured event emitter

FastAPI Integration (`agenttel[fastapi]`):
- `instrument_fastapi()` — one-line FastAPI integration
- `AgentTelMiddleware` — route resolution, topology, operation context
- `@agent_operation` decorator for per-endpoint configuration
- Auto-configuration from `agenttel.yml`

GenAI Instrumentation (`agenttel[openai,anthropic,langchain,bedrock]`):
- OpenAI SDK wrapper (sync + streaming)
- Anthropic SDK wrapper (sync + streaming)
- LangChain callback handler (ChatModel, Retriever)
- AWS Bedrock wrapper (`invoke_model` + `converse`)
- `ModelCostCalculator` with built-in pricing for 20+ models
- `GenAiSpanBuilder` for consistent span creation

Agent Interface (`agenttel[agent]`):
- MCP server (JSON-RPC 2.0 over HTTP) with 15 built-in tools
- `ServiceHealthAggregator` — per-operation stats and dependency health
- `AgentIdentity` and `ToolPermissionRegistry` — role-based access control
- `IncidentContextBuilder` — aggregated incident context for LLM consumption
- `RemediationRegistry` and `RemediationExecutor` — with audit logging
- `SloReportGenerator` and `TrendAnalyzer`

Agentic Observability (`agenttel`):
- 70+ agentic semantic attributes
- `AgentTracer` — builder pattern API for agent tracing
- 10 scope context managers: invocation, step, tool call, task, handoff, human checkpoint, code execution, evaluation, retriever, reranker
- Orchestration patterns: sequential, parallel, eval-loop
- `AgentCostAggregator` — token usage and cost tracking
- `LoopDetector` and `QualityTracker` — quality metrics
- `GuardrailRecorder` — guardrail trigger recording

## [0.2.0-alpha] - 2026-03-10

### Added

**Agentic Observability (agenttel-agentic)**
- `AgentTracer` for tracing agent invocations with full lifecycle support (steps, tool calls, tasks, handoffs)
- `AgentInvocation` with auto-closing scope, step counting, loop detection, and cost aggregation
- `AgentType` enum (SINGLE, REACT, PLAN_AND_EXECUTE, MULTI_AGENT, CUSTOM)
- `StepType` enum (THOUGHT, OBSERVATION, ACTION, PLANNING, EVALUATION, REFLECTION)
- `AgentCostAggregator` SpanProcessor for rolling up GenAI token costs to parent agent spans
- `LoopDetector` with configurable threshold for detecting repetitive tool call patterns
- `AgentConfig` and `AgentConfigRegistry` for config-driven agent identity and guardrails
- `@AgentMethod` annotation for zero-code agent invocation wrapping via AOP
- `AgentMethodAspect` for automatic `AgentInvocation` scope management on annotated methods
- `AgenticAttributes` attribute keys for agent spans (agent.name, agent.type, agent.framework, etc.)
- `AgenticAssertions` fluent test assertions for agent span verification

**Config-Driven Agent Observability**
- YAML configuration for agent identity (`agenttel.agentic.agents.*`): type, framework, version, maxSteps, loopThreshold, costBudgetUsd
- Global agentic defaults (`agenttel.agentic.loop-threshold`, `agenttel.agentic.default-max-steps`)
- Config priority: YAML > `@AgentMethod` annotation > programmatic `AgentTracer.Builder` defaults
- `AgentTelAgenticAutoConfiguration` wiring config registry, tracer, and AOP aspect

**Spring Boot Starter Enhancements**
- `McpServer` exposed as a proper Spring bean for testability and injection
- `McpServer.getPort()` returns actual bound port (supports port 0 for random assignment)

### Fixed
- `PaymentServiceIntegrationTest` BindException when MCP port 8081 is already in use

## [0.1.0-alpha] - 2025-02-27

### Added

**Core Instrumentation (agenttel-api, agenttel-core)**
- `@AgentOperation` annotation for declaring operational semantics (baselines, retryability, runbooks)
- `@AgentObservable`, `@DeclareDependency`, `@DeclareConsumer` annotations for service topology
- `AgentTelSpanProcessor` enriching spans with topology, baseline, decision, anomaly, and SLO attributes
- `TopologyRegistry` for dependency graph management with JSON serialization
- `StaticBaselineProvider` from annotation metadata
- `RollingBaselineProvider` with lock-free ring buffer sliding windows (configurable window size and min samples)
- `CompositeBaselineProvider` chaining static, rolling, and default baselines
- `AnomalyDetector` with z-score based deviation detection
- `PatternMatcher` detecting CASCADE_FAILURE, LATENCY_DEGRADATION, ERROR_RATE_SPIKE, and MEMORY_LEAK patterns
- `SloTracker` with error budget consumption tracking and threshold alerting (50%, 25%, 10%)
- `AgentTelEventEmitter` for structured events via the OTel Logs API
- `DeploymentEventEmitter` for deployment tracking

**GenAI Instrumentation (agenttel-genai)**
- LangChain4j instrumentation: `TracingChatLanguageModel`, `TracingStreamingChatLanguageModel`, `TracingEmbeddingModel`, `TracingContentRetriever`
- Spring AI span enrichment via `SpringAiSpanEnricher`
- `CostEnrichingSpanExporter` for adding cost_usd at export time
- Anthropic Java SDK instrumentation: `TracingAnthropicClient`
- OpenAI Java SDK instrumentation: `TracingOpenAIClient`
- AWS Bedrock SDK instrumentation: `TracingBedrockRuntimeClient`
- `ModelCostCalculator` with pricing for Claude, GPT-4, GPT-4o, and Bedrock models
- Spring Boot auto-configuration with `@ConditionalOnClass` activation

**Agent Interface Layer (agenttel-agent)**
- `McpServer` implementing Model Context Protocol over JSON-RPC 2.0
- `AgentTelMcpServerBuilder` with 5 pre-registered tools (get_service_health, get_incident_context, list_remediation_actions, execute_remediation, get_recent_agent_actions)
- `ServiceHealthAggregator` for real-time health from span data
- `IncidentContext` / `IncidentContextBuilder` for structured incident packages (what's happening, what changed, what's affected, what to do)
- `RemediationAction` / `RemediationRegistry` / `RemediationExecutor` with approval workflows
- `AgentActionTracker` recording agent decisions and actions as OTel spans
- `ContextFormatter` with prompt-optimized output formats (compact, full, JSON)
- `AgentContextProvider` as single entry point for agent queries

**Spring Boot Integration (agenttel-spring-boot-starter)**
- Auto-configuration for all core components
- `@ConfigurationProperties` binding for agenttel.* properties
- `AgentTelAnnotationBeanPostProcessor` for annotation scanning
- `AgentTelHealthIndicator` for Actuator integration

**Infrastructure**
- CI/CD with GitHub Actions (JDK 17 + 21 matrix)
- Maven Central publishing pipeline
- Grafana dashboard templates (overview + GenAI)
- Spring Boot and LangChain4j example applications

[0.2.0-alpha]: https://github.com/agenttel/agenttel-sdk/releases/tag/v0.2.0-alpha
[0.1.0-alpha]: https://github.com/agenttel/agenttel-sdk/releases/tag/v0.1.0-alpha
