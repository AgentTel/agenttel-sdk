# Go Service Example

Demonstrates the AgentTel Go SDK with a payment service using `net/http` (Go 1.22+ `ServeMux` patterns).

## Features

- `agenttel.yml` in the shared AgentTel format (same file shape as Spring Boot, Node.js and Python)
- `otelhttp` creates the HTTP server span; `agmw.Middleware(agmw.WithEngine(engine))` enriches it with
  topology, static baselines (`expected-latency-p50` etc.) and decision attributes (`retryable`, `runbook-url`, ...)
  for the matched `METHOD /route`
- Topology on the OTel resource via `engine.Resource()`

Requires `go.opentelemetry.io/otel/sdk` v1.39.0 or newer.

## Run

```bash
# Print spans to stdout
OTEL_TRACES_EXPORTER=console go run .

# With an OTel Collector on localhost:4318
go run .

# Or with a custom endpoint
OTEL_EXPORTER_OTLP_ENDPOINT=collector:4318 go run .
```

## Test

```bash
curl -X POST http://localhost:8080/api/payments -H "Content-Type: application/json"
curl http://localhost:8080/api/payments/pay_12345
curl http://localhost:8080/health
```
