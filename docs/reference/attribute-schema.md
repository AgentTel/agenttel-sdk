# Attribute Schema

`attributes.json` at the repository root is the single source of truth for every attribute key and event name AgentTel emits. `scripts/validate-attributes.sh` runs in CI and checks the JVM, Go, Node.js and Python SDKs against it: the same keys in every SDK, and on the JVM the same types.

## Attribute fields

```json
"retryable": {
  "key": "agenttel.decision.retryable",
  "type": "boolean",
  "description": "Whether the operation is safe to retry",
  "stability": "development",
  "kind": "declared",
  "level": "span",
  "upstream": { "status": "candidate", "key": "reliability.decision.retryable" }
}
```

| Field | Values | Meaning |
|---|---|---|
| `key` | string | The attribute key SDKs emit today |
| `type` | `string`, `int`, `double`, `boolean`, `string[]` | Value type as emitted |
| `enum` | list (optional) | Allowed values, when the attribute is an enum |
| `stability` | `development`, `stable`, `deprecated` | Whether the key may still change. Everything is `development` until the schema freeze |
| `kind` | see below | Where the value comes from |
| `level` | `resource`, `span`, `event` | Where the value is recorded |
| `upstream` | object | How the attribute maps to OpenTelemetry semantic conventions |

### `kind`

| Value | Meaning | Example |
|---|---|---|
| `declared` | Set by the service owner in config or annotations | `agenttel.decision.runbook_url` |
| `derived` | Computed by the AgentTel engine at runtime | `agenttel.anomaly.score` |
| `hybrid` | Declared in config or computed, depending on `agenttel.baseline.source` | `agenttel.baseline.latency_p99_ms` |
| `observed` | Recorded from what instrumentation saw | `agenttel.circuit_breaker.new_state` |

### `upstream.status`

| Value | Meaning | `upstream.key` |
|---|---|---|
| `candidate` | In the first, narrow OpenTelemetry proposal | Proposed `reliability.*` key |
| `later` | In the full proposal, after the first lands | Proposed `reliability.*` key |
| `otel_existing` | OpenTelemetry already defines this | Existing OTel key to emit instead |
| `out_of_scope` | Belongs to other OTel work (`gen_ai.*`, agentic systems) | none |
| `internal` | AgentTel-only; will not be proposed | none |

`upstream.note` explains a mapping that is not obvious or a known open question.

## Events

Event names live in the top-level `events` map, not among the attributes. Each event lists its attribute namespace, `stability` and `upstream` with the same meanings as above.

## Querying the schema

```bash
# The first-proposal candidates
jq -r '.namespaces[].attributes[] | select(.upstream.status=="candidate") | "\(.key) -> \(.upstream.key)"' attributes.json

# AgentTel keys that duplicate an existing OTel attribute
jq -r '.namespaces[].attributes[] | select(.upstream.status=="otel_existing" and (.key|startswith("agenttel."))) | "\(.key) -> \(.upstream.key)"' attributes.json
```
