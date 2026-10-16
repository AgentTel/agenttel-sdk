package http_test

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel/attribute"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
	"go.opentelemetry.io/otel/trace"

	agenttel "go.agenttel.dev/agenttel-go"
	agmw "go.agenttel.dev/agenttel-go/middleware/http"
)

const config = `
agenttel:
  topology:
    service-name: payment-service
    team: payments-platform
    tier: critical
    domain: commerce
    on-call-channel: "#payments-oncall"
  profiles:
    critical-write:
      escalation-level: page_oncall
  operations:
    "[POST /api/payments]":
      profile: critical-write
      expected-latency-p50: 45ms
      expected-latency-p99: 200ms
      expected-error-rate: 0.001
      retryable: true
      idempotent: true
      runbook-url: https://wiki.example.com/runbooks/payments
    "GET /api/payments/:id":
      expected-latency-p50: 15
      expected-latency-p99: 80
`

// End-to-end, mirroring the Spring Boot EnrichmentTest: a real HTTP server with
// otelhttp + AgentTel middleware, one request, then assert the server span.
func TestServerSpanIsEnriched(t *testing.T) {
	path := filepath.Join(t.TempDir(), "agenttel.yml")
	if err := os.WriteFile(path, []byte(config), 0o644); err != nil {
		t.Fatal(err)
	}
	engine, err := agenttel.New().WithConfigFile(path).Build()
	if err != nil {
		t.Fatal(err)
	}

	exporter := tracetest.NewInMemoryExporter()
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithResource(engine.Resource()),
		sdktrace.WithSpanProcessor(engine.SpanProcessor()),
		sdktrace.WithSyncer(exporter),
	)
	defer tp.Shutdown(context.Background())

	mux := http.NewServeMux()
	mux.HandleFunc("POST /api/payments", func(w http.ResponseWriter, _ *http.Request) { w.Write([]byte(`{"ok":true}`)) })
	mux.HandleFunc("GET /api/payments/{id}", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte(r.PathValue("id"))) })
	handler := otelhttp.NewHandler(agmw.Middleware(agmw.WithEngine(engine))(mux), "server", otelhttp.WithTracerProvider(tp))

	srv := httptest.NewServer(handler)
	for _, req := range []struct{ method, path string }{{"POST", "/api/payments"}, {"GET", "/api/payments/pay_123"}} {
		r, _ := http.NewRequest(req.method, srv.URL+req.path, strings.NewReader("{}"))
		resp, err := http.DefaultClient.Do(r)
		if err != nil {
			t.Fatal(err)
		}
		resp.Body.Close()
	}
	srv.Close()

	byRoute := map[string]map[attribute.Key]attribute.Value{}
	var resourceAttrs []attribute.KeyValue
	for _, s := range exporter.GetSpans() {
		if s.SpanKind != trace.SpanKindServer {
			continue
		}
		attrs := map[attribute.Key]attribute.Value{}
		for _, kv := range s.Attributes {
			attrs[kv.Key] = kv.Value
		}
		byRoute[attrs["http.route"].AsString()] = attrs
		resourceAttrs = s.Resource.Attributes()
	}

	post, ok := byRoute["/api/payments"]
	if !ok {
		t.Fatalf("no server span for /api/payments: %v", byRoute)
	}
	expect := map[string]any{
		"agenttel.topology.team":             "payments-platform",
		"agenttel.topology.on_call_channel":  "#payments-oncall",
		"agenttel.baseline.latency_p50_ms":   45.0,
		"agenttel.baseline.latency_p99_ms":   200.0,
		"agenttel.baseline.error_rate":       0.001,
		"agenttel.decision.retryable":        true,
		"agenttel.decision.idempotent":       true,
		"agenttel.decision.runbook_url":      "https://wiki.example.com/runbooks/payments",
		"agenttel.decision.escalation_level": "page_oncall",
	}
	for k, want := range expect {
		if got := post[attribute.Key(k)].AsInterface(); got != want {
			t.Errorf("%s = %v, want %v", k, got, want)
		}
	}

	get, ok := byRoute["/api/payments/{id}"]
	if !ok {
		t.Fatalf("no server span for /api/payments/{id}: %v", byRoute)
	}
	if got := get["agenttel.baseline.latency_p50_ms"].AsFloat64(); got != 15 {
		t.Errorf("GET p50 = %v, want 15", got)
	}
	if got := get["agenttel.decision.retryable"].AsBool(); got {
		t.Errorf("GET retryable = true, want false")
	}

	foundTeam := false
	for _, kv := range resourceAttrs {
		if kv.Key == "agenttel.topology.team" && kv.Value.AsString() == "payments-platform" {
			foundTeam = true
		}
	}
	if !foundTeam {
		t.Errorf("resource lacks agenttel.topology.team: %v", resourceAttrs)
	}
}
