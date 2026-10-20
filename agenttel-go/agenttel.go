// Package agenttel provides the top-level AgentTel engine for Go services.
//
// AgentTel enriches OpenTelemetry spans with agent-ready observability metadata
// including baselines, anomaly detection, SLO tracking, error classification,
// and topology context.
//
// Usage:
//
//	engine, err := agenttel.New().
//	    WithConfigFile("agenttel.yml").
//	    Build()
//
//	tp := sdktrace.NewTracerProvider(
//	    sdktrace.WithResource(engine.Resource()),
//	    sdktrace.WithSpanProcessor(engine.SpanProcessor()),
//	    sdktrace.WithBatcher(exporter),
//	)
//
//	handler := otelhttp.NewHandler(agmw.Middleware(agmw.WithEngine(engine))(mux), "server")
package agenttel

import (
	"fmt"
	"time"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/sdk/resource"

	"go.agenttel.dev/agenttel-go/anomaly"
	"go.agenttel.dev/agenttel-go/attributes"
	"go.agenttel.dev/agenttel-go/baseline"
	"go.agenttel.dev/agenttel-go/errorclass"
	"go.agenttel.dev/agenttel-go/events"
	"go.agenttel.dev/agenttel-go/models"
	"go.agenttel.dev/agenttel-go/operations"
	"go.agenttel.dev/agenttel-go/processor"
	"go.agenttel.dev/agenttel-go/slo"
	"go.agenttel.dev/agenttel-go/topology"
)

// Engine is the top-level orchestrator for all AgentTel components.
type Engine struct {
	Config           AgentTelConfig
	TopologyRegistry *topology.Registry
	BaselineProvider baseline.Provider
	RollingProvider  *baseline.RollingProvider
	AnomalyDetector  *anomaly.Detector
	PatternMatcher   *anomaly.PatternMatcher
	SLOTracker       *slo.Tracker
	ErrorClassifier  *errorclass.Classifier
	EventEmitter     *events.Emitter
	// Operations holds per-operation decision context (retryable, runbook, escalation, ...).
	Operations    *operations.Registry
	spanProcessor *processor.AgentTelSpanProcessor
}

// ResourceAttributes returns service.name (if configured) and the topology as
// OTel resource attributes.
func (e *Engine) ResourceAttributes() []attribute.KeyValue {
	var kv []attribute.KeyValue
	if e.Config.Topology.ServiceName != "" {
		kv = append(kv, attribute.String("service.name", e.Config.Topology.ServiceName))
	}
	t := e.TopologyRegistry
	for k, v := range map[string]string{
		attributes.TopologyTeam:          t.Team(),
		attributes.TopologyTier:          t.Tier(),
		attributes.TopologyDomain:        t.Domain(),
		attributes.TopologyOnCallChannel: t.OnCallChannel(),
		attributes.TopologyRepoURL:       t.RepoURL(),
	} {
		if v != "" {
			kv = append(kv, attribute.String(k, v))
		}
	}
	return kv
}

// Resource returns the default OTel resource (host, process, OTEL_* env)
// merged with ResourceAttributes, for sdktrace.WithResource.
func (e *Engine) Resource() *resource.Resource {
	r, err := resource.Merge(resource.Default(), resource.NewSchemaless(e.ResourceAttributes()...))
	if err != nil {
		return resource.NewSchemaless(e.ResourceAttributes()...)
	}
	return r
}

// SpanProcessor returns the OTel SpanProcessor for use with TracerProvider.
func (e *Engine) SpanProcessor() *processor.AgentTelSpanProcessor {
	return e.spanProcessor
}

// Builder constructs an Engine with the desired components.
type Builder struct {
	config           *AgentTelConfig
	configFile       string
	topologyRegistry *topology.Registry
	staticBaselines  map[string]models.OperationBaseline
	sloDefinitions   []models.SLODefinition
}

// New creates a new Engine builder.
func New() *Builder {
	return &Builder{}
}

// WithConfig sets the configuration directly.
func (b *Builder) WithConfig(cfg AgentTelConfig) *Builder {
	b.config = &cfg
	return b
}

// WithConfigFile sets the path to load configuration from.
func (b *Builder) WithConfigFile(path string) *Builder {
	b.configFile = path
	return b
}

// WithTopology sets a pre-configured topology registry.
func (b *Builder) WithTopology(r *topology.Registry) *Builder {
	b.topologyRegistry = r
	return b
}

// WithStaticBaselines adds static baseline data.
func (b *Builder) WithStaticBaselines(baselines map[string]models.OperationBaseline) *Builder {
	b.staticBaselines = baselines
	return b
}

// WithSLOs registers SLO definitions.
func (b *Builder) WithSLOs(slos ...models.SLODefinition) *Builder {
	b.sloDefinitions = append(b.sloDefinitions, slos...)
	return b
}

// Build constructs the Engine with all configured components.
func (b *Builder) Build() (*Engine, error) {
	// Load config
	var cfg AgentTelConfig
	if b.config != nil {
		cfg = *b.config
	} else if b.configFile != "" {
		var err error
		cfg, err = LoadConfig(b.configFile)
		if err != nil {
			return nil, err
		}
	} else {
		var err error
		cfg, err = LoadConfigFromEnv()
		if err != nil {
			cfg = DefaultConfig()
		}
	}

	// Topology
	topoReg := b.topologyRegistry
	if topoReg == nil {
		topoReg = topology.NewRegistry()
	}
	if cfg.Topology.Team != "" {
		topoReg.SetTeam(cfg.Topology.Team)
	}
	if cfg.Topology.Tier != "" {
		topoReg.SetTier(cfg.Topology.Tier)
	}
	if cfg.Topology.Domain != "" {
		topoReg.SetDomain(cfg.Topology.Domain)
	}
	if cfg.Topology.OnCallChannel != "" {
		topoReg.SetOnCallChannel(cfg.Topology.OnCallChannel)
	}
	if cfg.Topology.RepoURL != "" {
		topoReg.SetRepoURL(cfg.Topology.RepoURL)
	}
	for _, dep := range cfg.Dependencies {
		topoReg.RegisterDependency(models.DependencyDescriptor{
			Name:           dep.Name,
			Type:           dep.Type,
			Criticality:    dep.Criticality,
			Protocol:       dep.Protocol,
			TimeoutMs:      dep.TimeoutMs,
			CircuitBreaker: dep.CircuitBreaker,
			Fallback:       dep.Fallback,
			HealthEndpoint: dep.HealthEndpoint,
		})
	}
	for _, con := range cfg.Consumers {
		topoReg.RegisterConsumer(models.ConsumerDescriptor{
			Name:         con.Name,
			Pattern:      con.Pattern,
			SLALatencyMs: con.SLALatencyMs,
		})
	}

	// Baselines
	rollingProvider := baseline.NewRollingProvider(
		cfg.Baselines.RollingWindowSize,
		cfg.Baselines.RollingMinSamples,
	)

	// Static baselines and decisions from config operations. Baselines passed
	// to WithStaticBaselines take precedence over the config file.
	staticBaselines, decisions, err := buildOperations(cfg)
	if err != nil {
		return nil, err
	}
	for name, bl := range b.staticBaselines {
		staticBaselines[operations.Normalize(name)] = bl
	}

	var baseProvider baseline.Provider
	if len(staticBaselines) > 0 {
		baseProvider = baseline.NewCompositeProvider(
			baseline.NewStaticProvider(staticBaselines),
			rollingProvider,
		)
	} else {
		baseProvider = rollingProvider
	}

	// Anomaly
	detector := anomaly.NewDetector(cfg.AnomalyDetection.ZScoreThreshold)
	patternMatcher := anomaly.NewPatternMatcher(2.0, 0.1, 3)

	// SLO
	sloTracker := slo.NewTracker()
	for name, s := range cfg.SLO {
		sloTracker.Register(models.SLODefinition{
			Name:          name,
			OperationName: s.Operation,
			Type:          s.Type,
			Target:        s.Target,
		})
	}
	for _, def := range b.sloDefinitions {
		sloTracker.Register(def)
	}

	// Error classifier
	errorClassifier := errorclass.NewClassifier()

	// Events
	eventEmitter := events.NewEmitter()

	// Span processor
	sp := processor.New(
		processor.WithBaseline(baseProvider),
		processor.WithRolling(rollingProvider),
		processor.WithAnomalyDetector(detector),
		processor.WithPatternMatcher(patternMatcher),
		processor.WithSLOTracker(sloTracker),
		processor.WithErrorClassifier(errorClassifier),
		processor.WithTopology(topoReg),
		processor.WithEventEmitter(eventEmitter),
		processor.WithDecisions(decisions),
	)

	return &Engine{
		Config:           cfg,
		TopologyRegistry: topoReg,
		BaselineProvider: baseProvider,
		RollingProvider:  rollingProvider,
		AnomalyDetector:  detector,
		PatternMatcher:   patternMatcher,
		SLOTracker:       sloTracker,
		ErrorClassifier:  errorClassifier,
		EventEmitter:     eventEmitter,
		Operations:       decisions,
		spanProcessor:    sp,
	}, nil
}

// buildOperations turns config operations into static baselines and decision
// context: explicit operation values > referenced profile > defaults.
func buildOperations(cfg AgentTelConfig) (map[string]models.OperationBaseline, *operations.Registry, error) {
	baselines := make(map[string]models.OperationBaseline)
	decisions := operations.NewRegistry()
	for rawName, op := range cfg.Operations {
		name := operations.Normalize(rawName)

		p50, hasP50, err := operations.ParseDurationMs(op.ExpectedLatencyP50)
		if err != nil {
			return nil, nil, fmt.Errorf("operation %q: %w", rawName, err)
		}
		p99, hasP99, err := operations.ParseDurationMs(op.ExpectedLatencyP99)
		if err != nil {
			return nil, nil, fmt.Errorf("operation %q: %w", rawName, err)
		}
		if hasP50 || hasP99 || op.ExpectedErrorRate > 0 {
			baselines[name] = models.OperationBaseline{
				OperationName: name,
				LatencyP50Ms:  p50,
				LatencyP99Ms:  p99,
				ErrorRate:     op.ExpectedErrorRate,
				Source:        "static",
				UpdatedAt:     time.Now(),
			}
		}

		profile := cfg.Profiles[op.Profile]
		decisions.Register(name, operations.Decision{
			Retryable:           pickBool(op.Retryable, profile.Retryable, false),
			Idempotent:          pickBool(op.Idempotent, profile.Idempotent, false),
			RunbookURL:          pickString(op.RunbookURL, profile.RunbookURL, ""),
			FallbackDescription: pickString(op.FallbackDescription, profile.FallbackDescription, ""),
			EscalationLevel:     pickString(op.EscalationLevel, profile.EscalationLevel, "auto_resolve"),
			SafeToRestart:       pickBool(op.SafeToRestart, profile.SafeToRestart, true),
		})
	}
	return baselines, decisions, nil
}

func pickBool(op, profile *bool, def bool) bool {
	if op != nil {
		return *op
	}
	if profile != nil {
		return *profile
	}
	return def
}

func pickString(op, profile, def string) string {
	if op != "" {
		return op
	}
	if profile != "" {
		return profile
	}
	return def
}
