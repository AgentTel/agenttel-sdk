package namespace

import (
	"context"
	"testing"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
	"go.opentelemetry.io/otel/trace"

	attrs "go.agenttel.dev/agenttel-go/attributes"
)

const (
	stdRetryable = "reliability.decision.retryable"
	stdTeam      = "reliability.topology.team"
)

// exportOne records one span through a TracerProvider whose exporter is
// wrapped for mode, and returns the exported span.
func exportOne(t *testing.T, mode Mode, setAttrs []attribute.KeyValue, eventAttrs []attribute.KeyValue) tracetest.SpanStub {
	t.Helper()
	exporter := tracetest.NewInMemoryExporter()
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithResource(resource.NewSchemaless(attribute.String(attrs.TopologyTeam, "payments"))),
		sdktrace.WithSyncer(WrapSpanExporter(exporter, NewMapper(mode))),
	)
	defer func() { _ = tp.Shutdown(context.Background()) }()

	_, span := tp.Tracer("test").Start(context.Background(), "POST /api/payments")
	span.SetAttributes(setAttrs...)
	if eventAttrs != nil {
		span.AddEvent(attrs.EventAnomalyDetected, trace.WithAttributes(eventAttrs...))
	}
	span.End()

	spans := exporter.GetSpans()
	if len(spans) != 1 {
		t.Fatalf("expected 1 span, got %d", len(spans))
	}
	return spans[0]
}

func find(kvs []attribute.KeyValue, key string) (attribute.Value, bool) {
	for _, kv := range kvs {
		if string(kv.Key) == key {
			return kv.Value, true
		}
	}
	return attribute.Value{}, false
}

func TestLegacyLeavesSpansUnchanged(t *testing.T) {
	span := exportOne(t, Legacy, []attribute.KeyValue{attribute.Bool(attrs.DecisionRetryable, true)}, nil)

	if v, ok := find(span.Attributes, attrs.DecisionRetryable); !ok || !v.AsBool() {
		t.Errorf("expected %s=true, got %v (present=%v)", attrs.DecisionRetryable, v.Emit(), ok)
	}
	if _, ok := find(span.Attributes, stdRetryable); ok {
		t.Errorf("legacy mode must not add %s", stdRetryable)
	}
	if _, ok := find(span.Resource.Attributes(), stdTeam); ok {
		t.Errorf("legacy mode must not add %s to the resource", stdTeam)
	}
}

func TestStandardRenamesMappedKeysAndKeepsTheRest(t *testing.T) {
	span := exportOne(t, Standard, []attribute.KeyValue{
		attribute.Bool(attrs.DecisionRetryable, true),
		attribute.Int64(attrs.BaselineSampleCount, 42),
		attribute.Float64(attrs.SeverityAnomalyScore, 0.9),
	}, nil)

	if v, ok := find(span.Attributes, stdRetryable); !ok || !v.AsBool() {
		t.Errorf("expected %s=true", stdRetryable)
	}
	if _, ok := find(span.Attributes, attrs.DecisionRetryable); ok {
		t.Errorf("standard mode must drop %s", attrs.DecisionRetryable)
	}
	if v, ok := find(span.Attributes, "reliability.baseline.sample_count"); !ok || v.AsInt64() != 42 {
		t.Errorf("expected reliability.baseline.sample_count=42")
	}
	if v, ok := find(span.Attributes, attrs.SeverityAnomalyScore); !ok || v.AsFloat64() != 0.9 {
		t.Errorf("expected unmapped %s to pass through", attrs.SeverityAnomalyScore)
	}
	res := span.Resource.Attributes()
	if v, ok := find(res, stdTeam); !ok || v.AsString() != "payments" {
		t.Errorf("expected resource %s=payments", stdTeam)
	}
	if _, ok := find(res, attrs.TopologyTeam); ok {
		t.Errorf("standard mode must drop resource %s", attrs.TopologyTeam)
	}
}

func TestBothKeepsLegacyAndAddsStandard(t *testing.T) {
	span := exportOne(t, Both, []attribute.KeyValue{attribute.Bool(attrs.DecisionRetryable, false)}, nil)

	if v, ok := find(span.Attributes, attrs.DecisionRetryable); !ok || v.AsBool() {
		t.Errorf("expected %s=false", attrs.DecisionRetryable)
	}
	if v, ok := find(span.Attributes, stdRetryable); !ok || v.AsBool() {
		t.Errorf("expected %s=false", stdRetryable)
	}
	res := span.Resource.Attributes()
	if v, ok := find(res, attrs.TopologyTeam); !ok || v.AsString() != "payments" {
		t.Errorf("expected resource %s=payments", attrs.TopologyTeam)
	}
	if v, ok := find(res, stdTeam); !ok || v.AsString() != "payments" {
		t.Errorf("expected resource %s=payments", stdTeam)
	}
}

func TestExistingOtelAttributeWins(t *testing.T) {
	span := exportOne(t, Standard, []attribute.KeyValue{
		attribute.String("exception.type", "net.OpError"),
		attribute.String(attrs.ErrorRootException, "something.Else"),
	}, nil)

	if v, ok := find(span.Attributes, "exception.type"); !ok || v.AsString() != "net.OpError" {
		t.Errorf("expected existing exception.type to win, got %q", v.AsString())
	}
	if _, ok := find(span.Attributes, attrs.ErrorRootException); ok {
		t.Errorf("standard mode must drop %s", attrs.ErrorRootException)
	}
	count := 0
	for _, kv := range span.Attributes {
		if kv.Key == "exception.type" {
			count++
		}
	}
	if count != 1 {
		t.Errorf("expected exactly one exception.type, got %d", count)
	}
}

func TestSpanEventsAreMapped(t *testing.T) {
	span := exportOne(t, Standard, nil, []attribute.KeyValue{attribute.Float64("agenttel.anomaly.score", 0.95)})

	if len(span.Events) != 1 {
		t.Fatalf("expected 1 event, got %d", len(span.Events))
	}
	event := span.Events[0]
	if event.Name != "reliability.anomaly.detected" {
		t.Errorf("expected event name reliability.anomaly.detected, got %s", event.Name)
	}
	if v, ok := find(event.Attributes, "reliability.anomaly.score"); !ok || v.AsFloat64() != 0.95 {
		t.Errorf("expected event attribute reliability.anomaly.score=0.95")
	}
	if _, ok := find(event.Attributes, "agenttel.anomaly.score"); ok {
		t.Errorf("standard mode must drop event attribute agenttel.anomaly.score")
	}
}

func TestBothKeepsEventNameButMapsEventAttributes(t *testing.T) {
	span := exportOne(t, Both, nil, []attribute.KeyValue{attribute.Float64("agenttel.anomaly.score", 0.95)})

	if len(span.Events) != 1 {
		t.Fatalf("expected 1 event, got %d", len(span.Events))
	}
	event := span.Events[0]
	if event.Name != attrs.EventAnomalyDetected {
		t.Errorf("expected event name %s, got %s", attrs.EventAnomalyDetected, event.Name)
	}
	if _, ok := find(event.Attributes, "reliability.anomaly.score"); !ok {
		t.Errorf("expected event attribute reliability.anomaly.score")
	}
	if _, ok := find(event.Attributes, "agenttel.anomaly.score"); !ok {
		t.Errorf("expected event attribute agenttel.anomaly.score")
	}
}

func TestMappingIsIdempotent(t *testing.T) {
	in := []attribute.KeyValue{
		attribute.Bool(attrs.DecisionRetryable, true),
		attribute.String(attrs.TopologyTeam, "payments"),
		attribute.String("http.route", "/api/payments"),
	}
	for _, mode := range []Mode{Standard, Both} {
		m := NewMapper(mode)
		once := m.MapAttributes(in)
		twice := m.MapAttributes(once)
		onceSet, twiceSet := attribute.NewSet(once...), attribute.NewSet(twice...)
		if !onceSet.Equals(&twiceSet) {
			t.Errorf("%s: mapping twice changed the attributes: %v vs %v", mode, once, twice)
		}
		if _, changed := m.mapAttributes(once); changed {
			t.Errorf("%s: second mapping reported a change", mode)
		}
	}
}

func TestUnmappedInputIsReturnedUnchanged(t *testing.T) {
	in := []attribute.KeyValue{attribute.String("http.route", "/x"), attribute.Float64(attrs.SeverityAnomalyScore, 1)}
	out := NewMapper(Standard).MapAttributes(in)
	if len(out) != len(in) || &out[0] != &in[0] {
		t.Errorf("expected the input slice back when nothing maps")
	}
	res := resource.NewSchemaless(attribute.String("service.name", "svc"))
	if NewMapper(Both).MapResource(res) != res {
		t.Errorf("expected the same resource back when nothing maps")
	}
}

func TestTypesArePreserved(t *testing.T) {
	mapped := NewMapper(Standard).MapAttributes([]attribute.KeyValue{
		attribute.Float64(attrs.BaselineLatencyP99Ms, 120.5),
		attribute.Int64(attrs.DecisionRetryAfterMs, 500),
		attribute.Bool(attrs.DecisionRetryable, true),
		attribute.String(attrs.TopologyTeam, "payments"),
	})

	checks := []struct {
		key  string
		kind attribute.Type
	}{
		{"reliability.baseline.latency_p99_ms", attribute.FLOAT64},
		{"reliability.decision.retry_after_ms", attribute.INT64},
		{stdRetryable, attribute.BOOL},
		{stdTeam, attribute.STRING},
	}
	for _, c := range checks {
		v, ok := find(mapped, c.key)
		if !ok {
			t.Errorf("missing %s", c.key)
			continue
		}
		if v.Type() != c.kind {
			t.Errorf("%s: expected type %s, got %s", c.key, c.kind, v.Type())
		}
	}
	if v, _ := find(mapped, "reliability.baseline.latency_p99_ms"); v.AsFloat64() != 120.5 {
		t.Errorf("expected 120.5, got %v", v.AsFloat64())
	}
	if v, _ := find(mapped, "reliability.decision.retry_after_ms"); v.AsInt64() != 500 {
		t.Errorf("expected 500, got %v", v.AsInt64())
	}
}

func TestEventNamesMapOnlyInStandardMode(t *testing.T) {
	if got := NewMapper(Standard).MapEventName(attrs.EventAnomalyDetected); got != "reliability.anomaly.detected" {
		t.Errorf("standard: got %s", got)
	}
	if got := NewMapper(Both).MapEventName(attrs.EventAnomalyDetected); got != attrs.EventAnomalyDetected {
		t.Errorf("both: got %s", got)
	}
	if got := NewMapper(Legacy).MapEventName(attrs.EventAnomalyDetected); got != attrs.EventAnomalyDetected {
		t.Errorf("legacy: got %s", got)
	}
	if got := NewMapper(Standard).MapEventName("custom.event"); got != "custom.event" {
		t.Errorf("unmapped: got %s", got)
	}
}

func TestModeParsing(t *testing.T) {
	cases := map[string]Mode{
		"":           Legacy,
		"  ":         Legacy,
		"legacy":     Legacy,
		" Standard ": Standard,
		"BOTH":       Both,
	}
	for in, want := range cases {
		got, err := ParseMode(in)
		if err != nil || got != want {
			t.Errorf("ParseMode(%q) = %s, %v; want %s", in, got, err, want)
		}
	}
	got, err := ParseMode("otel")
	if err == nil {
		t.Error("expected an error for an unknown mode")
	}
	if got != Legacy {
		t.Errorf("expected fallback to legacy, got %s", got)
	}
}

func TestLegacyWrapReturnsDelegate(t *testing.T) {
	exporter := tracetest.NewInMemoryExporter()
	if WrapSpanExporter(exporter, NewMapper(Legacy)) != sdktrace.SpanExporter(exporter) {
		t.Error("expected legacy mode to return the delegate unchanged")
	}
	if WrapSpanExporter(exporter, nil) != sdktrace.SpanExporter(exporter) {
		t.Error("expected a nil mapper to return the delegate unchanged")
	}
}
