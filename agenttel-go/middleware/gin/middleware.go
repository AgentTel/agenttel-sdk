// Package gin provides Gin framework helpers for AgentTel span enrichment.
//
// To avoid a hard dependency on Gin, this package exposes EnrichSpan; register
// it from a one-line Gin middleware after otelgin:
//
//	cfg := aggin.NewConfig(aggin.WithEngine(engine))
//	r.Use(otelgin.Middleware("payment-service"))
//	r.Use(func(c *gin.Context) {
//	    aggin.EnrichSpan(trace.SpanFromContext(c.Request.Context()), c.Request.Method, c.FullPath(), cfg)
//	    c.Next()
//	})
package gin

import (
	"go.opentelemetry.io/otel/trace"

	agenttel "go.agenttel.dev/agenttel-go"
	"go.agenttel.dev/agenttel-go/baseline"
	"go.agenttel.dev/agenttel-go/enrich"
	"go.agenttel.dev/agenttel-go/operations"
	"go.agenttel.dev/agenttel-go/topology"
)

// GinContext is a minimal interface for the gin.Context methods we need,
// to avoid a hard dependency on the gin package.
//
// Deprecated: unused; call EnrichSpan from a gin.HandlerFunc instead.
type GinContext interface {
	Request() interface{ Method() string }
	FullPath() string
	Next()
}

// Config holds middleware configuration.
type Config struct {
	BaselineProvider baseline.Provider
	Topology         *topology.Registry
	Decisions        operations.Provider
}

// Option configures the middleware.
type Option func(*Config)

// NewConfig builds a Config from options.
func NewConfig(opts ...Option) *Config {
	cfg := &Config{}
	for _, opt := range opts {
		opt(cfg)
	}
	return cfg
}

// WithEngine takes topology, baselines and decisions from an AgentTel engine.
func WithEngine(e *agenttel.Engine) Option {
	return func(c *Config) {
		c.BaselineProvider = e.BaselineProvider
		c.Topology = e.TopologyRegistry
		c.Decisions = e.Operations
	}
}

// WithBaselineProvider sets the baseline provider.
func WithBaselineProvider(p baseline.Provider) Option {
	return func(c *Config) { c.BaselineProvider = p }
}

// WithTopology sets the topology registry.
func WithTopology(t *topology.Registry) Option {
	return func(c *Config) { c.Topology = t }
}

// WithDecisions sets the per-operation decision context (retryable, runbook, ...).
func WithDecisions(p operations.Provider) Option {
	return func(c *Config) { c.Decisions = p }
}

// EnrichSpan enriches an OTel span with AgentTel topology, baseline and
// decision attributes for "METHOD routePattern" (Gin's c.FullPath(), e.g.
// "/api/payments/:id", which matches a config key "GET /api/payments/{id}").
func EnrichSpan(span trace.Span, method, routePattern string, cfg *Config) {
	if cfg == nil || !span.IsRecording() {
		return
	}
	enrich.Topology(span, cfg.Topology)
	if routePattern != "" {
		enrich.Operation(span, method+" "+routePattern, cfg.BaselineProvider, cfg.Decisions)
	}
}
