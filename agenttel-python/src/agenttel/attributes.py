"""AgentTel semantic attributes for OpenTelemetry spans."""

# Topology attributes
TOPOLOGY_TEAM = "agenttel.topology.team"
TOPOLOGY_TIER = "agenttel.topology.tier"
TOPOLOGY_DOMAIN = "agenttel.topology.domain"
TOPOLOGY_ON_CALL_CHANNEL = "agenttel.topology.on_call_channel"
TOPOLOGY_ONCALL_CHANNEL = TOPOLOGY_ON_CALL_CHANNEL  # deprecated alias
TOPOLOGY_REPO_URL = "agenttel.topology.repo_url"
TOPOLOGY_SERVICE_VERSION = "agenttel.topology.service_version"

# Dependency attributes
DEPENDENCY_NAME = "agenttel.dependency.name"
DEPENDENCY_TYPE = "agenttel.dependency.type"
DEPENDENCY_CRITICALITY = "agenttel.dependency.criticality"
DEPENDENCY_PROTOCOL = "agenttel.dependency.protocol"
DEPENDENCY_TIMEOUT_MS = "agenttel.dependency.timeout_ms"
DEPENDENCY_CIRCUIT_BREAKER = "agenttel.dependency.circuit_breaker"
DEPENDENCY_FALLBACK = "agenttel.dependency.fallback"
DEPENDENCY_HEALTH_ENDPOINT = "agenttel.dependency.health_endpoint"
DEPENDENCY_STATE = "agenttel.dependency.state"

# Consumer attributes
CONSUMER_NAME = "agenttel.consumer.name"
CONSUMER_PATTERN = "agenttel.consumer.pattern"
CONSUMER_SLA_LATENCY_MS = "agenttel.consumer.sla_latency_ms"

# Decision attributes (operation context an agent needs to act safely)
DECISION_RETRYABLE = "agenttel.decision.retryable"
DECISION_IDEMPOTENT = "agenttel.decision.idempotent"
DECISION_RUNBOOK_URL = "agenttel.decision.runbook_url"
DECISION_FALLBACK_AVAILABLE = "agenttel.decision.fallback_available"
DECISION_FALLBACK_DESCRIPTION = "agenttel.decision.fallback_description"
DECISION_ESCALATION_LEVEL = "agenttel.decision.escalation_level"
DECISION_SAFE_TO_RESTART = "agenttel.decision.safe_to_restart"

# Deprecated aliases (pre-0.4.0 names); values now match attributes.json
OPERATION_RETRYABLE = DECISION_RETRYABLE
OPERATION_IDEMPOTENT = DECISION_IDEMPOTENT
OPERATION_RUNBOOK_URL = DECISION_RUNBOOK_URL
OPERATION_FALLBACK_DESCRIPTION = DECISION_FALLBACK_DESCRIPTION
OPERATION_ESCALATION_LEVEL = DECISION_ESCALATION_LEVEL
OPERATION_SAFE_TO_RESTART = DECISION_SAFE_TO_RESTART
OPERATION_PROFILE = "agenttel.operation.profile"

# Baseline attributes
BASELINE_LATENCY_P50_MS = "agenttel.baseline.latency_p50_ms"
BASELINE_LATENCY_P95_MS = "agenttel.baseline.latency_p95_ms"
BASELINE_LATENCY_P99_MS = "agenttel.baseline.latency_p99_ms"
BASELINE_ERROR_RATE = "agenttel.baseline.error_rate"
BASELINE_SOURCE = "agenttel.baseline.source"
BASELINE_CONFIDENCE = "agenttel.baseline.confidence"
BASELINE_SAMPLE_COUNT = "agenttel.baseline.sample_count"

# Anomaly attributes
ANOMALY_DETECTED = "agenttel.anomaly.detected"
ANOMALY_SCORE = "agenttel.anomaly.score"
ANOMALY_Z_SCORE = "agenttel.anomaly.z_score"
ANOMALY_PATTERN = "agenttel.anomaly.pattern"
ANOMALY_BASELINE_MEAN = "agenttel.anomaly.baseline_mean"
ANOMALY_BASELINE_STDDEV = "agenttel.anomaly.baseline_stddev"

# SLO attributes
SLO_NAME = "agenttel.slo.name"
SLO_TARGET = "agenttel.slo.target"
SLO_TYPE = "agenttel.slo.type"
SLO_BUDGET_REMAINING = "agenttel.slo.budget_remaining"
SLO_BURN_RATE = "agenttel.slo.burn_rate"
SLO_ALERT_LEVEL = "agenttel.slo.alert_level"

# Error classification attributes
ERROR_CATEGORY = "agenttel.error.category"
ERROR_IS_TRANSIENT = "agenttel.error.is_transient"
ERROR_ROOT_CAUSE = "agenttel.error.root_cause"

# Causality attributes
CAUSALITY_CAUSE_CATEGORY = "agenttel.causality.cause_category"
CAUSALITY_BUSINESS_IMPACT = "agenttel.causality.business_impact"
CAUSALITY_IMPACT_SCOPE = "agenttel.causality.impact_scope"
CAUSALITY_DEPENDENCY_CHAIN = "agenttel.causality.dependency_chain"

# Deployment attributes
DEPLOYMENT_ID = "agenttel.deployment.id"
DEPLOYMENT_VERSION = "agenttel.deployment.version"
DEPLOYMENT_ENVIRONMENT = "agenttel.deployment.environment"
DEPLOYMENT_TIMESTAMP = "agenttel.deployment.timestamp"
DEPLOYMENT_COMMIT_SHA = "agenttel.deployment.commit_sha"

# GenAI extension attributes
GENAI_FRAMEWORK = "agenttel.genai.framework"
GENAI_COST_USD = "agenttel.genai.cost_usd"
GENAI_CACHE_HIT = "agenttel.genai.cache_hit"
GENAI_RAG_ENABLED = "agenttel.genai.rag_enabled"
GENAI_RAG_SOURCE_COUNT = "agenttel.genai.rag_source_count"
GENAI_GUARDRAIL_TRIGGERED = "agenttel.genai.guardrail_triggered"
