// Package enrich sets AgentTel attributes on OTel spans. It is shared by the
// span processor and the framework middleware.
package enrich

import (
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"

	attrs "go.agenttel.dev/agenttel-go/attributes"
	"go.agenttel.dev/agenttel-go/baseline"
	"go.agenttel.dev/agenttel-go/operations"
	"go.agenttel.dev/agenttel-go/topology"
)

// Topology sets team, tier, domain and on-call channel on the span.
func Topology(span trace.Span, t *topology.Registry) {
	if t == nil {
		return
	}
	for k, v := range map[string]string{
		attrs.TopologyTeam:          t.Team(),
		attrs.TopologyTier:          t.Tier(),
		attrs.TopologyDomain:        t.Domain(),
		attrs.TopologyOnCallChannel: t.OnCallChannel(),
	} {
		if v != "" {
			span.SetAttributes(attribute.String(k, v))
		}
	}
}

// Operation sets baseline and decision attributes for operationName
// ("METHOD /route") and reports whether anything was found.
func Operation(span trace.Span, operationName string, baselines baseline.Provider, decisions operations.Provider) bool {
	name := operations.Normalize(operationName)
	found := false
	if baselines != nil {
		if b, ok := baselines.GetBaseline(name); ok {
			span.SetAttributes(
				attribute.Float64(attrs.BaselineLatencyP50Ms, b.LatencyP50Ms),
				attribute.Float64(attrs.BaselineLatencyP99Ms, b.LatencyP99Ms),
				attribute.Float64(attrs.BaselineErrorRate, b.ErrorRate),
				attribute.String(attrs.BaselineSource, b.Source),
			)
			found = true
		}
	}
	if decisions != nil {
		if d, ok := decisions.GetDecision(name); ok {
			span.SetAttributes(
				attribute.Bool(attrs.DecisionRetryable, d.Retryable),
				attribute.Bool(attrs.DecisionIdempotent, d.Idempotent),
				attribute.Bool(attrs.DecisionSafeToRestart, d.SafeToRestart),
				attribute.String(attrs.DecisionEscalationLevel, d.EscalationLevel),
				attribute.Bool(attrs.DecisionFallbackAvailable, d.FallbackDescription != ""),
			)
			if d.RunbookURL != "" {
				span.SetAttributes(attribute.String(attrs.DecisionRunbookURL, d.RunbookURL))
			}
			if d.FallbackDescription != "" {
				span.SetAttributes(attribute.String(attrs.DecisionFallbackDescription, d.FallbackDescription))
			}
			found = true
		}
	}
	return found
}
