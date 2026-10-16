// Package grpc provides gRPC server interceptors for AgentTel span enrichment.
package grpc

import (
	"context"

	"go.opentelemetry.io/otel/trace"
	"google.golang.org/grpc"

	agenttel "go.agenttel.dev/agenttel-go"
	"go.agenttel.dev/agenttel-go/baseline"
	"go.agenttel.dev/agenttel-go/enrich"
	"go.agenttel.dev/agenttel-go/operations"
	"go.agenttel.dev/agenttel-go/topology"
)

// Config holds interceptor configuration. Operations are keyed by the gRPC
// full method name, e.g. "/payments.v1.Payments/Charge".
type Config struct {
	BaselineProvider baseline.Provider
	Topology         *topology.Registry
	Decisions        operations.Provider
}

// Option configures the interceptor.
type Option func(*Config)

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

// WithEngine takes topology, baselines and decisions from an AgentTel engine.
func WithEngine(e *agenttel.Engine) Option {
	return func(c *Config) {
		c.BaselineProvider = e.BaselineProvider
		c.Topology = e.TopologyRegistry
		c.Decisions = e.Operations
	}
}

// UnaryServerInterceptor returns a gRPC unary server interceptor that
// enriches the current span with AgentTel attributes.
func UnaryServerInterceptor(opts ...Option) grpc.UnaryServerInterceptor {
	cfg := buildConfig(opts)

	return func(
		ctx context.Context,
		req interface{},
		info *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler,
	) (interface{}, error) {
		span := trace.SpanFromContext(ctx)
		enrichSpan(span, info.FullMethod, cfg)
		return handler(ctx, req)
	}
}

// StreamServerInterceptor returns a gRPC stream server interceptor that
// enriches the current span with AgentTel attributes.
func StreamServerInterceptor(opts ...Option) grpc.StreamServerInterceptor {
	cfg := buildConfig(opts)

	return func(
		srv interface{},
		ss grpc.ServerStream,
		info *grpc.StreamServerInfo,
		handler grpc.StreamHandler,
	) error {
		span := trace.SpanFromContext(ss.Context())
		enrichSpan(span, info.FullMethod, cfg)
		return handler(srv, ss)
	}
}

func buildConfig(opts []Option) *Config {
	cfg := &Config{}
	for _, opt := range opts {
		opt(cfg)
	}
	return cfg
}

func enrichSpan(span trace.Span, fullMethod string, cfg *Config) {
	if !span.IsRecording() {
		return
	}
	enrich.Topology(span, cfg.Topology)
	enrich.Operation(span, fullMethod, cfg.BaselineProvider, cfg.Decisions)
}
