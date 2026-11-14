# AgentTel Python SDK

AI-native telemetry SDK for Python services. Full feature parity with the JVM SDK — semantic attributes, baselines, anomaly detection, SLO tracking, GenAI instrumentation, agentic observability, and MCP agent interface.

## Installation

```bash
pip install agenttel

# With extras
pip install agenttel[fastapi]       # FastAPI middleware + auto-config
pip install agenttel[openai]        # OpenAI instrumentation
pip install agenttel[anthropic]     # Anthropic instrumentation
pip install agenttel[langchain]     # LangChain instrumentation
pip install agenttel[bedrock]       # AWS Bedrock instrumentation
pip install agenttel[agent]         # MCP server (aiohttp)
pip install agenttel[all]           # Everything
```

## Quick Start (FastAPI)

### 1. Create `agenttel.yml`

```yaml
agenttel:
  enabled: true
  topology:
    team: payments
    tier: critical
    domain: fintech
    on-call-channel: "#payments-oncall"
  dependencies:
    - name: postgres
      type: database
      criticality: required
      timeout-ms: 3000
    - name: stripe-api
      type: external_api
      criticality: degraded
      timeout-ms: 5000
      circuit-breaker: true
  operations:
    "[POST /api/transfers]":
      profile: critical-write
      expected-latency-p50: "80ms"
      expected-latency-p99: "300ms"
      expected-error-rate: 0.002
      runbook-url: "https://wiki.example.com/runbooks/transfers"
  profiles:
    critical-write:
      retryable: false
      idempotent: false
      escalation-level: page_oncall
      safe-to-restart: false
  baselines:
    rolling-window-size: 1000
    rolling-min-samples: 10
  anomaly-detection:
    enabled: true
    z-score-threshold: 3.0
  attributes:
    namespace: legacy   # legacy (agenttel.*) | standard (reliability.*/OTel names) | both;
                        # spans are mapped only via BatchSpanProcessor(engine.wrap_exporter(exporter))
```

### 2. Instrument Your App

```python
from fastapi import FastAPI
from agenttel.fastapi import instrument_fastapi

app = FastAPI()
engine = instrument_fastapi(app)

@app.post("/api/transfers")
async def create_transfer(request: dict):
    # Your spans automatically get AgentTel enrichment:
    # - topology attributes (team, tier, domain)
    # - operation context (retryable, runbook, escalation)
    # - baseline attributes (P50, P99, error rate)
    # - anomaly detection on span end
    # - SLO budget tracking
    return {"status": "completed"}
```

### 3. Use the Decorator

```python
from agenttel.fastapi import agent_operation

@app.get("/api/accounts/{account_id}")
@agent_operation(
    expected_latency_p50="10ms",
    expected_latency_p99="50ms",
    retryable=True,
    runbook_url="https://wiki.example.com/runbooks/get-account",
)
async def get_account(account_id: str):
    return {"id": account_id}
```

## GenAI Instrumentation

```python
from openai import OpenAI
from agenttel.genai import instrument_openai

client = instrument_openai(OpenAI())

# All completions are now traced with:
# - gen_ai.system, gen_ai.request.model
# - gen_ai.usage.input_tokens, gen_ai.usage.output_tokens
# - agenttel.genai.cost_usd
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
```

Anthropic, LangChain, and AWS Bedrock are also supported:

```python
from anthropic import Anthropic
from agenttel.genai import instrument_anthropic, instrument_langchain

client = instrument_anthropic(Anthropic())
instrument_langchain()  # Global LangChain instrumentation
```

## Agentic Observability

```python
from agenttel.agentic import AgentTracer
from agenttel.enums import AgentType, StepType

tracer = (AgentTracer.create()
    .agent_name("incident-responder")
    .agent_type(AgentType.SINGLE)
    .framework("langchain")
    .build())

with tracer.invoke("diagnose high latency") as invocation:
    with invocation.step(StepType.THOUGHT, "analyzing metrics"):
        pass  # reasoning

    with invocation.tool_call("get_service_health") as tool:
        result = {"status": "degraded"}
        tool.set_result(result)

    with invocation.task("check dependencies") as task:
        with task.step(StepType.ACTION, "querying deps"):
            pass

    invocation.complete(goal_achieved=True)
```

## Architecture

```
agenttel-python/
├── src/agenttel/
│   ├── attributes.py          # Semantic attribute constants
│   ├── enums.py               # All enums (ServiceTier, ErrorCategory, etc.)
│   ├── models.py              # Pydantic data models
│   ├── config.py              # YAML config loader
│   ├── processor.py           # OTel SpanProcessor
│   ├── engine.py              # High-level orchestrator
│   ├── baseline/              # Static, rolling, composite baselines
│   ├── anomaly/               # Z-score anomaly detection + pattern matching
│   ├── slo/                   # SLO tracking with error budgets
│   ├── error/                 # Error classification
│   ├── causality/             # Dependency state tracking
│   ├── topology/              # Service topology registry
│   ├── fastapi/               # FastAPI middleware + decorators
│   ├── genai/                 # OpenAI, Anthropic, LangChain, Bedrock wrappers
│   ├── agent/                 # MCP server, health aggregation, identity
│   └── agentic/               # AgentTracer, scopes, orchestration patterns
└── tests/
```

## Requirements

- Python 3.11+
- OpenTelemetry SDK 1.20+
- Pydantic 2.0+
