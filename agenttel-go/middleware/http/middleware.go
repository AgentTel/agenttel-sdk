// Package http provides net/http middleware for AgentTel span enrichment.
//
// The middleware enriches the span that is already active on the request
// context, so wrap it in an OTel HTTP instrumentation such as otelhttp:
//
//	handler := otelhttp.NewHandler(agmw.Middleware(agmw.WithEngine(engine))(mux), "server")
package http

import (
	"net/http"
	"strings"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"

	agenttel "go.agenttel.dev/agenttel-go"
	"go.agenttel.dev/agenttel-go/baseline"
	"go.agenttel.dev/agenttel-go/enrich"
	"go.agenttel.dev/agenttel-go/operations"
	"go.agenttel.dev/agenttel-go/topology"
)

// Config holds middleware configuration.
type Config struct {
	BaselineProvider baseline.Provider
	Topology         *topology.Registry
	Decisions        operations.Provider
	RouteResolver    func(r *http.Request) string
}

// Option configures the middleware.
type Option func(*Config)

// WithEngine takes topology, baselines and decisions from an AgentTel engine.
func WithEngine(e *agenttel.Engine) Option {
	return func(c *Config) {
		c.BaselineProvider = e.BaselineProvider
		c.Topology = e.TopologyRegistry
		c.Decisions = e.Operations
	}
}

// WithBaselineProvider sets the baseline provider for enrichment.
func WithBaselineProvider(p baseline.Provider) Option {
	return func(c *Config) { c.BaselineProvider = p }
}

// WithTopology sets the topology registry for enrichment.
func WithTopology(t *topology.Registry) Option {
	return func(c *Config) { c.Topology = t }
}

// WithDecisions sets the per-operation decision context (retryable, runbook, ...).
func WithDecisions(p operations.Provider) Option {
	return func(c *Config) { c.Decisions = p }
}

// WithRouteResolver sets a custom resolver returning the operation name
// ("METHOD /route") for a request.
func WithRouteResolver(fn func(r *http.Request) string) Option {
	return func(c *Config) { c.RouteResolver = fn }
}

// Middleware returns an http.Handler wrapper that enriches the active OTel span
// with AgentTel topology, baseline and decision attributes for "METHOD /route".
//
// Without a RouteResolver the operation is resolved from the request path and,
// when the wrapped handler is a Go 1.22+ http.ServeMux, again from the matched
// pattern (e.g. "GET /api/payments/{id}") after routing.
func Middleware(opts ...Option) func(http.Handler) http.Handler {
	cfg := &Config{}
	for _, opt := range opts {
		opt(cfg)
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			span := trace.SpanFromContext(r.Context())
			if !span.IsRecording() {
				next.ServeHTTP(w, r)
				return
			}

			enrich.Topology(span, cfg.Topology)
			first := resolveOperationName(r, cfg)
			found := enrich.Operation(span, first, cfg.BaselineProvider, cfg.Decisions)

			next.ServeHTTP(w, r)

			if cfg.RouteResolver == nil && r.Pattern != "" {
				route, op := patternOperation(r)
				span.SetAttributes(attribute.String("http.route", route))
				if !found && op != first {
					enrich.Operation(span, op, cfg.BaselineProvider, cfg.Decisions)
				}
			}
		})
	}
}

func resolveOperationName(r *http.Request, cfg *Config) string {
	if cfg.RouteResolver != nil {
		return cfg.RouteResolver(r)
	}
	if r.Pattern != "" {
		_, op := patternOperation(r)
		return op
	}
	return r.Method + " " + r.URL.Path
}

// patternOperation converts a ServeMux pattern ("[METHOD ][HOST]/path") to
// the route and "METHOD /path" operation name.
func patternOperation(r *http.Request) (route, op string) {
	method, path := r.Method, r.Pattern
	if m, rest, ok := strings.Cut(r.Pattern, " "); ok {
		method, path = m, strings.TrimSpace(rest)
	}
	if i := strings.Index(path, "/"); i > 0 {
		path = path[i:] // drop host
	}
	return path, method + " " + path
}
