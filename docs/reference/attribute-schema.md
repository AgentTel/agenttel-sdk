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
| `enum_briefs` | object (optional) | One sentence per `enum` value. Required for candidate enums |
| `examples` | list (optional) | Example values of `type`. Required for candidates other than booleans |
| `note` | string (optional) | Usage guidance carried into the registry |
| `stability` | `development`, `stable`, `deprecated` | Whether the key may still change. `deprecated` marks a renamed candidate |
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

`upstream.renamed_to` names the replacement of a candidate that was renamed. It is only allowed with `stability: deprecated` (see [Schema freeze](#schema-freeze)).

The SDKs emit `upstream.key` in place of, or next to, `key` when `agenttel.attributes.namespace` is `standard` or `both` (see [Configuration](configuration.md#attribute-names)). `scripts/generate-namespace-maps.py` turns these fields into each SDK's key map; the validator fails when a generated map is out of date.

## Events

Event names live in the top-level `events` map, not among the attributes. Each event lists its attribute namespace, `stability` and `upstream` with the same meanings as above.

## Weaver registry

`model/` holds the candidates as an [OpenTelemetry Weaver](https://github.com/open-telemetry/weaver) registry, the format of the semantic-conventions repository: `model/reliability/registry.yaml` for attributes and `model/reliability/events.yaml` for events. `model/reliability/` can be copied into that repository's `model/` directory as is; `model/manifest.yaml` lets Weaver check it on its own.

`scripts/generate-semconv-registry.py` writes these files from `attributes.json`. Do not edit them by hand: the validator fails when they are out of date.

`scripts/check-semconv-registry.sh` (needs Docker) runs in CI and checks that:

1. Weaver resolves the registry.
2. It passes the semantic-conventions repository's own policy check (naming, stability, backward compatibility) when added to that repository's model. The Weaver version and policies match that repository's CI.
3. Nothing changed incompatibly since the base branch (see below).

```bash
python3 scripts/generate-semconv-registry.py   # after editing attributes.json
bash scripts/check-semconv-registry.sh         # compares against origin/main
```

## Schema freeze

Candidate keys are frozen: CI fails when a change to `attributes.json` removes a candidate, changes its type or removes an enum value, compared with the base branch. Adding candidates, enum values, examples or notes is allowed.

To rename a candidate, add the new attribute as a candidate and keep the old one with `stability: deprecated` and `upstream.renamed_to` set to the new key. The registry then marks the old key `deprecated: { reason: renamed }`, the form OpenTelemetry itself uses.

## Querying the schema

```bash
# The first-proposal candidates
jq -r '.namespaces[].attributes[] | select(.upstream.status=="candidate") | "\(.key) -> \(.upstream.key)"' attributes.json

# AgentTel keys that duplicate an existing OTel attribute
jq -r '.namespaces[].attributes[] | select(.upstream.status=="otel_existing" and (.key|startswith("agenttel."))) | "\(.key) -> \(.upstream.key)"' attributes.json
```
