"""AgentTel semantic attributes for OpenTelemetry spans.

Values match the canonical ``attributes.json`` at the repository root.
SDK-specific keys that are not in the canonical schema live in
:mod:`agenttel.extension_attributes`.
"""

# Topology attributes
TOPOLOGY_TEAM = "agenttel.topology.team"
TOPOLOGY_TIER = "agenttel.topology.tier"
TOPOLOGY_DOMAIN = "agenttel.topology.domain"
TOPOLOGY_ON_CALL_CHANNEL = "agenttel.topology.on_call_channel"
TOPOLOGY_ONCALL_CHANNEL = TOPOLOGY_ON_CALL_CHANNEL  # deprecated alias
TOPOLOGY_REPO_URL = "agenttel.topology.repo_url"
TOPOLOGY_DEPENDENCIES = "agenttel.topology.dependencies"
TOPOLOGY_CONSUMERS = "agenttel.topology.consumers"

# Baseline attributes
BASELINE_LATENCY_P50_MS = "agenttel.baseline.latency_p50_ms"
BASELINE_LATENCY_P99_MS = "agenttel.baseline.latency_p99_ms"
BASELINE_ERROR_RATE = "agenttel.baseline.error_rate"
BASELINE_THROUGHPUT_RPS = "agenttel.baseline.throughput_rps"
BASELINE_SOURCE = "agenttel.baseline.source"
BASELINE_UPDATED_AT = "agenttel.baseline.updated_at"
BASELINE_SLO = "agenttel.baseline.slo"
BASELINE_SAMPLE_COUNT = "agenttel.baseline.sample_count"
BASELINE_CONFIDENCE = "agenttel.baseline.confidence"

# Causality attributes
CAUSE_HINT = "agenttel.cause.hint"
CAUSE_CATEGORY = "agenttel.cause.category"
CAUSE_DEPENDENCY = "agenttel.cause.dependency"
CAUSE_CORRELATED_SPAN_ID = "agenttel.cause.correlated_span_id"
CAUSE_CORRELATED_EVENT_ID = "agenttel.cause.correlated_event_id"
CAUSE_STARTED_AT = "agenttel.cause.started_at"

# Decision attributes (operation context an agent needs to act safely)
DECISION_RETRYABLE = "agenttel.decision.retryable"
DECISION_RETRY_AFTER_MS = "agenttel.decision.retry_after_ms"
DECISION_IDEMPOTENT = "agenttel.decision.idempotent"
DECISION_FALLBACK_AVAILABLE = "agenttel.decision.fallback_available"
DECISION_FALLBACK_DESCRIPTION = "agenttel.decision.fallback_description"
DECISION_RUNBOOK_URL = "agenttel.decision.runbook_url"
DECISION_ESCALATION_LEVEL = "agenttel.decision.escalation_level"
DECISION_KNOWN_ISSUE_ID = "agenttel.decision.known_issue_id"
DECISION_SAFE_TO_RESTART = "agenttel.decision.safe_to_restart"

# Severity attributes
SEVERITY_ANOMALY_SCORE = "agenttel.severity.anomaly_score"
SEVERITY_PATTERN = "agenttel.severity.pattern"
SEVERITY_IMPACT_SCOPE = "agenttel.severity.impact_scope"
SEVERITY_BUSINESS_IMPACT = "agenttel.severity.business_impact"
SEVERITY_USER_FACING = "agenttel.severity.user_facing"

# Deployment attributes
DEPLOYMENT_ID = "agenttel.deployment.id"
DEPLOYMENT_VERSION = "agenttel.deployment.version"
DEPLOYMENT_COMMIT_SHA = "agenttel.deployment.commit_sha"
DEPLOYMENT_PREVIOUS_VERSION = "agenttel.deployment.previous_version"
DEPLOYMENT_STRATEGY = "agenttel.deployment.strategy"
DEPLOYMENT_TIMESTAMP = "agenttel.deployment.timestamp"

# GenAI extension attributes
GENAI_FRAMEWORK = "agenttel.genai.framework"
GENAI_COST_USD = "agenttel.genai.cost_usd"
GENAI_RAG_SOURCE_COUNT = "agenttel.genai.rag_source_count"
GENAI_RAG_RELEVANCE_SCORE_AVG = "agenttel.genai.rag_relevance_score_avg"
GENAI_GUARDRAIL_TRIGGERED = "agenttel.genai.guardrail_triggered"
GENAI_GUARDRAIL_NAME = "agenttel.genai.guardrail_name"
GENAI_CACHE_HIT = "agenttel.genai.cache_hit"
GENAI_PROMPT_TEMPLATE_ID = "agenttel.genai.prompt_template_id"
GENAI_PROMPT_TEMPLATE_VERSION = "agenttel.genai.prompt_template_version"
GENAI_REASONING_TOKENS = "agenttel.genai.reasoning_tokens"
GENAI_CACHED_READ_TOKENS = "agenttel.genai.cached_read_tokens"
GENAI_CACHED_WRITE_TOKENS = "agenttel.genai.cached_write_tokens"
GENAI_TIME_TO_FIRST_TOKEN_MS = "agenttel.genai.time_to_first_token_ms"

# Anomaly attributes
ANOMALY_DETECTED = "agenttel.anomaly.detected"
ANOMALY_PATTERN = "agenttel.anomaly.pattern"
ANOMALY_SCORE = "agenttel.anomaly.score"
ANOMALY_LATENCY_Z_SCORE = "agenttel.anomaly.latency_z_score"

# SLO attributes
SLO_NAME = "agenttel.slo.name"
SLO_TARGET = "agenttel.slo.target"
SLO_BUDGET_REMAINING = "agenttel.slo.budget_remaining"
SLO_BURN_RATE = "agenttel.slo.burn_rate"

# Error classification attributes
ERROR_CATEGORY = "agenttel.error.category"
ERROR_ROOT_EXCEPTION = "agenttel.error.root_exception"
ERROR_DEPENDENCY = "agenttel.error.dependency"

# Correlation attributes
CORRELATION_LIKELY_CAUSE = "agenttel.correlation.likely_cause"
CORRELATION_CHANGE_ID = "agenttel.correlation.change_id"
CORRELATION_TIME_DELTA_MS = "agenttel.correlation.time_delta_ms"
CORRELATION_CONFIDENCE = "agenttel.correlation.confidence"

# Agent identity attributes (agents acting on the service, e.g. via MCP)
AGENT_ID = "agenttel.agent.id"
AGENT_ROLE = "agenttel.agent.role"
AGENT_SESSION_ID = "agenttel.agent.session_id"

# Session attributes
SESSION_ID = "agenttel.session.id"
SESSION_INCIDENT_ID = "agenttel.session.incident_id"

# Circuit breaker attributes
CIRCUIT_BREAKER_NAME = "agenttel.circuit_breaker.name"
CIRCUIT_BREAKER_PREVIOUS_STATE = "agenttel.circuit_breaker.previous_state"
CIRCUIT_BREAKER_NEW_STATE = "agenttel.circuit_breaker.new_state"
CIRCUIT_BREAKER_FAILURE_COUNT = "agenttel.circuit_breaker.failure_count"
CIRCUIT_BREAKER_DEPENDENCY = "agenttel.circuit_breaker.dependency"

# Event names
EVENT_DEPLOYMENT_INFO = "agenttel.deployment.info"
EVENT_ANOMALY_DETECTED = "agenttel.anomaly.detected"
EVENT_DEPENDENCY_STATE_CHANGE = "agenttel.dependency.state_change"
EVENT_SLO_BUDGET_ALERT = "agenttel.slo.budget_alert"
EVENT_CIRCUIT_BREAKER_STATE_CHANGE = "agenttel.circuit_breaker.state_change"

# Deprecated aliases (pre-0.4.0 names); values now match attributes.json
OPERATION_RETRYABLE = DECISION_RETRYABLE
OPERATION_IDEMPOTENT = DECISION_IDEMPOTENT
OPERATION_RUNBOOK_URL = DECISION_RUNBOOK_URL
OPERATION_FALLBACK_DESCRIPTION = DECISION_FALLBACK_DESCRIPTION
OPERATION_ESCALATION_LEVEL = DECISION_ESCALATION_LEVEL
OPERATION_SAFE_TO_RESTART = DECISION_SAFE_TO_RESTART
ANOMALY_Z_SCORE = ANOMALY_LATENCY_Z_SCORE
ERROR_ROOT_CAUSE = ERROR_ROOT_EXCEPTION
CAUSALITY_CAUSE_CATEGORY = CAUSE_CATEGORY
CAUSALITY_BUSINESS_IMPACT = SEVERITY_BUSINESS_IMPACT
CAUSALITY_IMPACT_SCOPE = SEVERITY_IMPACT_SCOPE
