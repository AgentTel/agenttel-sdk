// Package processor implements the OTel SpanProcessor that enriches spans with AgentTel metadata.
package processor

import (
	"context"
	"time"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"

	"go.agenttel.dev/agenttel-go/anomaly"
	"go.agenttel.dev/agenttel-go/attributes"
	"go.agenttel.dev/agenttel-go/baseline"
	"go.agenttel.dev/agenttel-go/enrich"
	"go.agenttel.dev/agenttel-go/errorclass"
	"go.agenttel.dev/agenttel-go/events"
	"go.agenttel.dev/agenttel-go/operations"
	"go.agenttel.dev/agenttel-go/slo"
	"go.agenttel.dev/agenttel-go/topology"
)

// SpanCompletionListener is called after a span is processed.
type SpanCompletionListener func(span sdktrace.ReadOnlySpan)

// AgentTelSpanProcessor enriches OTel spans with AgentTel observability attributes.
type AgentTelSpanProcessor struct {
	baselineProvider baseline.Provider
	rollingProvider  *baseline.RollingProvider
	anomalyDetector  *anomaly.Detector
	patternMatcher   *anomaly.PatternMatcher
	sloTracker       *slo.Tracker
	errorClassifier  *errorclass.Classifier
	topologyRegistry *topology.Registry
	eventEmitter     *events.Emitter
	decisions        operations.Provider
	listener         SpanCompletionListener
}

// Option configures the span processor.
type Option func(*AgentTelSpanProcessor)

// WithBaseline sets the baseline provider for span enrichment.
func WithBaseline(p baseline.Provider) Option {
	return func(sp *AgentTelSpanProcessor) { sp.baselineProvider = p }
}

// WithRolling sets the rolling baseline provider.
func WithRolling(p *baseline.RollingProvider) Option {
	return func(sp *AgentTelSpanProcessor) { sp.rollingProvider = p }
}

// WithAnomalyDetector sets the anomaly detector.
func WithAnomalyDetector(d *anomaly.Detector) Option {
	return func(sp *AgentTelSpanProcessor) { sp.anomalyDetector = d }
}

// WithPatternMatcher sets the pattern matcher.
func WithPatternMatcher(m *anomaly.PatternMatcher) Option {
	return func(sp *AgentTelSpanProcessor) { sp.patternMatcher = m }
}

// WithSLOTracker sets the SLO tracker.
func WithSLOTracker(t *slo.Tracker) Option {
	return func(sp *AgentTelSpanProcessor) { sp.sloTracker = t }
}

// WithErrorClassifier sets the error classifier.
func WithErrorClassifier(c *errorclass.Classifier) Option {
	return func(sp *AgentTelSpanProcessor) { sp.errorClassifier = c }
}

// WithTopology sets the topology registry.
func WithTopology(r *topology.Registry) Option {
	return func(sp *AgentTelSpanProcessor) { sp.topologyRegistry = r }
}

// WithEventEmitter sets the event emitter.
func WithEventEmitter(e *events.Emitter) Option {
	return func(sp *AgentTelSpanProcessor) { sp.eventEmitter = e }
}

// WithDecisions sets the per-operation decision context provider.
func WithDecisions(d operations.Provider) Option {
	return func(sp *AgentTelSpanProcessor) { sp.decisions = d }
}

// WithCompletionListener sets a listener called after each span is processed.
func WithCompletionListener(l SpanCompletionListener) Option {
	return func(sp *AgentTelSpanProcessor) { sp.listener = l }
}

// New creates an AgentTelSpanProcessor with the given options.
func New(opts ...Option) *AgentTelSpanProcessor {
	p := &AgentTelSpanProcessor{}
	for _, opt := range opts {
		opt(p)
	}
	return p
}

// OnStart enriches spans with topology, and with baseline and decision
// attributes when the span name is a configured operation. HTTP server spans
// are usually named before routing; the framework middleware covers those.
func (p *AgentTelSpanProcessor) OnStart(_ context.Context, span sdktrace.ReadWriteSpan) {
	enrich.Topology(span, p.topologyRegistry)
	if enrich.Operation(span, span.Name(), p.baselineProvider, p.decisions) {
		if p.baselineProvider != nil {
			if b, ok := p.baselineProvider.GetBaseline(operations.Normalize(span.Name())); ok {
				span.SetAttributes(attribute.String(attributes.BaselineUpdatedAt, b.UpdatedAt.Format(time.RFC3339)))
			}
		}
	}
}

// OnEnd records rolling baselines, performs anomaly detection, and tracks SLOs.
func (p *AgentTelSpanProcessor) OnEnd(span sdktrace.ReadOnlySpan) {
	name := operationName(span)
	durationMs := float64(span.EndTime().Sub(span.StartTime()).Milliseconds())
	isError := span.Status().Code == codes.Error

	// Record rolling baseline
	if p.rollingProvider != nil {
		if isError {
			p.rollingProvider.RecordError(name)
		} else {
			p.rollingProvider.RecordLatency(name, durationMs)
		}
	}

	// SLO tracking
	if p.sloTracker != nil {
		if isError {
			p.sloTracker.RecordFailure(name)
		} else {
			p.sloTracker.RecordSuccess(name)
		}
	}

	// Anomaly detection
	if p.anomalyDetector != nil && p.rollingProvider != nil {
		if snap, ok := p.rollingProvider.GetSnapshot(name); ok && !snap.IsEmpty() {
			result := p.anomalyDetector.Evaluate("latency", durationMs, snap.Mean, snap.Stddev)
			if result.IsAnomaly && p.eventEmitter != nil {
				p.eventEmitter.Emit(attributes.EventAnomalyDetected, map[string]any{
					"operation":    name,
					"anomalyScore": result.AnomalyScore,
					"zScore":       result.ZScore,
					"latencyMs":    durationMs,
				})
			}
		}
	}

	// Notify listener
	if p.listener != nil {
		p.listener(span)
	}
}

// Shutdown gracefully shuts down the processor.
func (p *AgentTelSpanProcessor) Shutdown(_ context.Context) error {
	return nil
}

// ForceFlush flushes pending data.
func (p *AgentTelSpanProcessor) ForceFlush(_ context.Context) error {
	return nil
}

// operationName is "METHOD /route" for HTTP server spans with a route,
// otherwise the span name.
func operationName(span sdktrace.ReadOnlySpan) string {
	var route, method string
	for _, kv := range span.Attributes() {
		switch kv.Key {
		case "http.route":
			route = kv.Value.AsString()
		case "http.request.method", "http.method":
			method = kv.Value.AsString()
		}
	}
	if route != "" && method != "" {
		return operations.Normalize(method + " " + route)
	}
	return operations.Normalize(span.Name())
}
