// Re-export all attribute constants — matches Go SDK and Java SDK exactly.
// Topology
export const TOPOLOGY_TEAM = 'agenttel.topology.team';
export const TOPOLOGY_TIER = 'agenttel.topology.tier';
export const TOPOLOGY_DOMAIN = 'agenttel.topology.domain';
export const TOPOLOGY_ON_CALL_CHANNEL = 'agenttel.topology.on_call_channel';
export const TOPOLOGY_REPO_URL = 'agenttel.topology.repo_url';
export const TOPOLOGY_DEPENDENCIES = 'agenttel.topology.dependencies';
export const TOPOLOGY_CONSUMERS = 'agenttel.topology.consumers';

// Baseline
export const BASELINE_LATENCY_P50_MS = 'agenttel.baseline.latency_p50_ms';
export const BASELINE_LATENCY_P99_MS = 'agenttel.baseline.latency_p99_ms';
export const BASELINE_ERROR_RATE = 'agenttel.baseline.error_rate';
export const BASELINE_THROUGHPUT_RPS = 'agenttel.baseline.throughput_rps';
export const BASELINE_SOURCE = 'agenttel.baseline.source';
export const BASELINE_UPDATED_AT = 'agenttel.baseline.updated_at';
export const BASELINE_SLO = 'agenttel.baseline.slo';
export const BASELINE_SAMPLE_COUNT = 'agenttel.baseline.sample_count';
export const BASELINE_CONFIDENCE = 'agenttel.baseline.confidence';

// Causality
export const CAUSE_HINT = 'agenttel.cause.hint';
export const CAUSE_CATEGORY = 'agenttel.cause.category';
export const CAUSE_DEPENDENCY = 'agenttel.cause.dependency';
export const CAUSE_CORRELATED_SPAN_ID = 'agenttel.cause.correlated_span_id';
export const CAUSE_CORRELATED_EVENT_ID = 'agenttel.cause.correlated_event_id';
export const CAUSE_STARTED_AT = 'agenttel.cause.started_at';

// Decision
export const DECISION_RETRYABLE = 'agenttel.decision.retryable';
export const DECISION_RETRY_AFTER_MS = 'agenttel.decision.retry_after_ms';
export const DECISION_IDEMPOTENT = 'agenttel.decision.idempotent';
export const DECISION_FALLBACK_AVAILABLE = 'agenttel.decision.fallback_available';
export const DECISION_FALLBACK_DESCRIPTION = 'agenttel.decision.fallback_description';
export const DECISION_RUNBOOK_URL = 'agenttel.decision.runbook_url';
export const DECISION_ESCALATION_LEVEL = 'agenttel.decision.escalation_level';
export const DECISION_KNOWN_ISSUE_ID = 'agenttel.decision.known_issue_id';
export const DECISION_SAFE_TO_RESTART = 'agenttel.decision.safe_to_restart';

// Severity
export const SEVERITY_ANOMALY_SCORE = 'agenttel.severity.anomaly_score';
export const SEVERITY_PATTERN = 'agenttel.severity.pattern';
export const SEVERITY_IMPACT_SCOPE = 'agenttel.severity.impact_scope';
export const SEVERITY_BUSINESS_IMPACT = 'agenttel.severity.business_impact';
export const SEVERITY_USER_FACING = 'agenttel.severity.user_facing';

// Deployment
export const DEPLOYMENT_ID = 'agenttel.deployment.id';
export const DEPLOYMENT_VERSION = 'agenttel.deployment.version';
export const DEPLOYMENT_COMMIT_SHA = 'agenttel.deployment.commit_sha';
export const DEPLOYMENT_PREVIOUS_VERSION = 'agenttel.deployment.previous_version';
export const DEPLOYMENT_STRATEGY = 'agenttel.deployment.strategy';
export const DEPLOYMENT_TIMESTAMP = 'agenttel.deployment.timestamp';

// GenAI (agenttel extensions)
export const GENAI_FRAMEWORK = 'agenttel.genai.framework';
export const GENAI_COST_USD = 'agenttel.genai.cost_usd';
export const GENAI_RAG_SOURCE_COUNT = 'agenttel.genai.rag_source_count';
export const GENAI_RAG_RELEVANCE_SCORE_AVG = 'agenttel.genai.rag_relevance_score_avg';
export const GENAI_GUARDRAIL_TRIGGERED = 'agenttel.genai.guardrail_triggered';
export const GENAI_GUARDRAIL_NAME = 'agenttel.genai.guardrail_name';
export const GENAI_CACHE_HIT = 'agenttel.genai.cache_hit';
export const GENAI_PROMPT_TEMPLATE_ID = 'agenttel.genai.prompt_template_id';
export const GENAI_PROMPT_TEMPLATE_VERSION = 'agenttel.genai.prompt_template_version';
export const GENAI_REASONING_TOKENS = 'agenttel.genai.reasoning_tokens';
export const GENAI_CACHED_READ_TOKENS = 'agenttel.genai.cached_read_tokens';
export const GENAI_CACHED_WRITE_TOKENS = 'agenttel.genai.cached_write_tokens';
export const GENAI_TIME_TO_FIRST_TOKEN_MS = 'agenttel.genai.time_to_first_token_ms';

// Anomaly
export const ANOMALY_DETECTED = 'agenttel.anomaly.detected';
export const ANOMALY_PATTERN = 'agenttel.anomaly.pattern';
export const ANOMALY_SCORE = 'agenttel.anomaly.score';
export const ANOMALY_LATENCY_Z_SCORE = 'agenttel.anomaly.latency_z_score';

// SLO
export const SLO_NAME = 'agenttel.slo.name';
export const SLO_TARGET = 'agenttel.slo.target';
export const SLO_BUDGET_REMAINING = 'agenttel.slo.budget_remaining';
export const SLO_BURN_RATE = 'agenttel.slo.burn_rate';

// Error classification
export const ERROR_CATEGORY_ATTR = 'agenttel.error.category';
export const ERROR_ROOT_EXCEPTION = 'agenttel.error.root_exception';
export const ERROR_DEPENDENCY = 'agenttel.error.dependency';

// Correlation
export const CORRELATION_LIKELY_CAUSE = 'agenttel.correlation.likely_cause';
export const CORRELATION_CHANGE_ID = 'agenttel.correlation.change_id';
export const CORRELATION_TIME_DELTA_MS = 'agenttel.correlation.time_delta_ms';
export const CORRELATION_CONFIDENCE = 'agenttel.correlation.confidence';

// Agent identity
export const AGENT_ID = 'agenttel.agent.id';
export const AGENT_ROLE = 'agenttel.agent.role';
export const AGENT_SESSION_ID = 'agenttel.agent.session_id';

// Session
export const SESSION_ID = 'agenttel.session.id';
export const SESSION_INCIDENT_ID = 'agenttel.session.incident_id';

// Circuit breaker
export const CIRCUIT_BREAKER_NAME = 'agenttel.circuit_breaker.name';
export const CIRCUIT_BREAKER_PREVIOUS_STATE = 'agenttel.circuit_breaker.previous_state';
export const CIRCUIT_BREAKER_NEW_STATE = 'agenttel.circuit_breaker.new_state';
export const CIRCUIT_BREAKER_FAILURE_COUNT = 'agenttel.circuit_breaker.failure_count';
export const CIRCUIT_BREAKER_DEPENDENCY = 'agenttel.circuit_breaker.dependency';

// Dependency health event
export const DEPENDENCY_NAME = 'agenttel.dependency.name';
export const DEPENDENCY_PREVIOUS_STATE = 'agenttel.dependency.previous_state';
export const DEPENDENCY_NEW_STATE = 'agenttel.dependency.new_state';

// Event names
export const EVENT_DEPLOYMENT_INFO = 'agenttel.deployment.info';
export const EVENT_ANOMALY_DETECTED = 'agenttel.anomaly.detected';
export const EVENT_DEPENDENCY_STATE_CHANGE = 'agenttel.dependency.state_change';
export const EVENT_SLO_BUDGET_ALERT = 'agenttel.slo.budget_alert';
export const EVENT_CIRCUIT_BREAKER_STATE_CHANGE = 'agenttel.circuit_breaker.state_change';

// Standard OTel GenAI semantic conventions (gen_ai.*)
export const GENAI_OPERATION_NAME = 'gen_ai.operation.name';
export const GENAI_SYSTEM = 'gen_ai.system';
export const GENAI_REQUEST_MODEL = 'gen_ai.request.model';
export const GENAI_REQUEST_TEMPERATURE = 'gen_ai.request.temperature';
export const GENAI_REQUEST_MAX_TOKENS = 'gen_ai.request.max_tokens';
export const GENAI_REQUEST_TOP_P = 'gen_ai.request.top_p';
export const GENAI_RESPONSE_MODEL = 'gen_ai.response.model';
export const GENAI_RESPONSE_ID = 'gen_ai.response.id';
export const GENAI_RESPONSE_FINISH_REASONS = 'gen_ai.response.finish_reasons';
export const GENAI_USAGE_INPUT_TOKENS = 'gen_ai.usage.input_tokens';
export const GENAI_USAGE_OUTPUT_TOKENS = 'gen_ai.usage.output_tokens';
