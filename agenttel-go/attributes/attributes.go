// Package attributes defines all agenttel.* semantic attribute key constants
// for enriching OpenTelemetry spans with agent-ready observability metadata.
// These constants match the Java SDK's AgentTelAttributes class exactly.
package attributes

// Topology attributes describe service ownership, tier, and dependency graph.
const (
	TopologyTeam          = "agenttel.topology.team"
	TopologyTier          = "agenttel.topology.tier"
	TopologyDomain        = "agenttel.topology.domain"
	TopologyOnCallChannel = "agenttel.topology.on_call_channel"
	TopologyRepoURL       = "agenttel.topology.repo_url"
	TopologyDependencies  = "agenttel.topology.dependencies"
	TopologyConsumers     = "agenttel.topology.consumers"
)

// Baseline attributes capture expected operational norms for anomaly detection.
const (
	BaselineLatencyP50Ms  = "agenttel.baseline.latency_p50_ms"
	BaselineLatencyP99Ms  = "agenttel.baseline.latency_p99_ms"
	BaselineErrorRate     = "agenttel.baseline.error_rate"
	BaselineThroughputRPS = "agenttel.baseline.throughput_rps"
	BaselineSource        = "agenttel.baseline.source"
	BaselineUpdatedAt     = "agenttel.baseline.updated_at"
	BaselineSLO           = "agenttel.baseline.slo"
	BaselineSampleCount   = "agenttel.baseline.sample_count"
	BaselineConfidence    = "agenttel.baseline.confidence"
)

// Causality attributes link spans to probable root causes.
const (
	CauseHint              = "agenttel.cause.hint"
	CauseCategory          = "agenttel.cause.category"
	CauseDependency        = "agenttel.cause.dependency"
	CauseCorrelatedSpanID  = "agenttel.cause.correlated_span_id"
	CauseCorrelatedEventID = "agenttel.cause.correlated_event_id"
	CauseStartedAt         = "agenttel.cause.started_at"
)

// Decision attributes provide actionable context for automated response.
const (
	DecisionRetryable           = "agenttel.decision.retryable"
	DecisionRetryAfterMs        = "agenttel.decision.retry_after_ms"
	DecisionIdempotent          = "agenttel.decision.idempotent"
	DecisionFallbackAvailable   = "agenttel.decision.fallback_available"
	DecisionFallbackDescription = "agenttel.decision.fallback_description"
	DecisionRunbookURL          = "agenttel.decision.runbook_url"
	DecisionEscalationLevel     = "agenttel.decision.escalation_level"
	DecisionKnownIssueID        = "agenttel.decision.known_issue_id"
	DecisionSafeToRestart       = "agenttel.decision.safe_to_restart"
)

// Severity attributes quantify impact and urgency of anomalous conditions.
const (
	SeverityAnomalyScore   = "agenttel.severity.anomaly_score"
	SeverityPattern        = "agenttel.severity.pattern"
	SeverityImpactScope    = "agenttel.severity.impact_scope"
	SeverityBusinessImpact = "agenttel.severity.business_impact"
	SeverityUserFacing     = "agenttel.severity.user_facing"
)

// Deployment attributes track release metadata for change correlation.
const (
	DeploymentID              = "agenttel.deployment.id"
	DeploymentVersion         = "agenttel.deployment.version"
	DeploymentCommitSHA       = "agenttel.deployment.commit_sha"
	DeploymentPreviousVersion = "agenttel.deployment.previous_version"
	DeploymentStrategy        = "agenttel.deployment.strategy"
	DeploymentTimestamp       = "agenttel.deployment.timestamp"
)

// GenAI attributes capture LLM and generative AI operational metadata.
const (
	GenAIFramework             = "agenttel.genai.framework"
	GenAICostUSD               = "agenttel.genai.cost_usd"
	GenAIRAGSourceCount        = "agenttel.genai.rag_source_count"
	GenAIRAGRelevanceScoreAvg  = "agenttel.genai.rag_relevance_score_avg"
	GenAIGuardrailTriggered    = "agenttel.genai.guardrail_triggered"
	GenAIGuardrailName         = "agenttel.genai.guardrail_name"
	GenAICacheHit              = "agenttel.genai.cache_hit"
	GenAIPromptTemplateID      = "agenttel.genai.prompt_template_id"
	GenAIPromptTemplateVersion = "agenttel.genai.prompt_template_version"
	GenAIReasoningTokens       = "agenttel.genai.reasoning_tokens"
	GenAICachedReadTokens      = "agenttel.genai.cached_read_tokens"
	GenAICachedWriteTokens     = "agenttel.genai.cached_write_tokens"
	GenAITimeToFirstTokenMs    = "agenttel.genai.time_to_first_token_ms"
)

// Anomaly attributes indicate detected anomalous behavior.
const (
	AnomalyDetected      = "agenttel.anomaly.detected"
	AnomalyPattern       = "agenttel.anomaly.pattern"
	AnomalyScore         = "agenttel.anomaly.score"
	AnomalyLatencyZScore = "agenttel.anomaly.latency_z_score"
)

// SLO attributes track service level objective status and budget.
const (
	SLOName            = "agenttel.slo.name"
	SLOTarget          = "agenttel.slo.target"
	SLOBudgetRemaining = "agenttel.slo.budget_remaining"
	SLOBurnRate        = "agenttel.slo.burn_rate"
)

// Error classification attributes categorize errors for automated triage.
const (
	ErrorCategory      = "agenttel.error.category"
	ErrorRootException = "agenttel.error.root_exception"
	ErrorDependency    = "agenttel.error.dependency"
)

// Change correlation attributes link anomalies to recent changes.
const (
	CorrelationLikelyCause = "agenttel.correlation.likely_cause"
	CorrelationChangeID    = "agenttel.correlation.change_id"
	CorrelationTimeDeltaMs = "agenttel.correlation.time_delta_ms"
	CorrelationConfidence  = "agenttel.correlation.confidence"
)

// Agent identity attributes identify autonomous agents.
const (
	AgentID        = "agenttel.agent.id"
	AgentRole      = "agenttel.agent.role"
	AgentSessionID = "agenttel.agent.session_id"
)

// Session attributes group related spans under a logical session.
const (
	SessionID         = "agenttel.session.id"
	SessionIncidentID = "agenttel.session.incident_id"
)

// Circuit breaker attributes track state transitions.
const (
	CircuitBreakerName          = "agenttel.circuit_breaker.name"
	CircuitBreakerPreviousState = "agenttel.circuit_breaker.previous_state"
	CircuitBreakerNewState      = "agenttel.circuit_breaker.new_state"
	CircuitBreakerFailureCount  = "agenttel.circuit_breaker.failure_count"
	CircuitBreakerDependency    = "agenttel.circuit_breaker.dependency"
)

// Dependency attributes describe a dependency health change event.
const (
	DependencyName          = "agenttel.dependency.name"
	DependencyPreviousState = "agenttel.dependency.previous_state"
	DependencyNewState      = "agenttel.dependency.new_state"
)

// Event name constants for structured event emission.
const (
	EventDeploymentInfo            = "agenttel.deployment.info"
	EventAnomalyDetected           = "agenttel.anomaly.detected"
	EventDependencyStateChange     = "agenttel.dependency.state_change"
	EventSLOBudgetAlert            = "agenttel.slo.budget_alert"
	EventCircuitBreakerStateChange = "agenttel.circuit_breaker.state_change"
)

// Standard OpenTelemetry GenAI semantic convention attributes (gen_ai.* namespace).
const (
	GenAIOperationName         = "gen_ai.operation.name"
	GenAISystem                = "gen_ai.system"
	GenAIRequestModel          = "gen_ai.request.model"
	GenAIRequestTemperature    = "gen_ai.request.temperature"
	GenAIRequestMaxTokens      = "gen_ai.request.max_tokens"
	GenAIRequestTopP           = "gen_ai.request.top_p"
	GenAIResponseModel         = "gen_ai.response.model"
	GenAIResponseID            = "gen_ai.response.id"
	GenAIResponseFinishReasons = "gen_ai.response.finish_reasons"
	GenAIUsageInputTokens      = "gen_ai.usage.input_tokens"
	GenAIUsageOutputTokens     = "gen_ai.usage.output_tokens"
)
