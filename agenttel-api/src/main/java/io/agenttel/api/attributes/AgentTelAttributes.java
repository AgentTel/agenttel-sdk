package io.agenttel.api.attributes;

import io.opentelemetry.api.common.AttributeKey;

/**
 * Attribute key constants for all AgentTel semantic conventions.
 * Follows the same pattern as OTel's SemanticAttributes.
 */
public final class AgentTelAttributes {
    private AgentTelAttributes() {}

    // --- Topology ---
    public static final AttributeKey<String> TOPOLOGY_TEAM =
            AttributeKey.stringKey("agenttel.topology.team");
    public static final AttributeKey<String> TOPOLOGY_TIER =
            AttributeKey.stringKey("agenttel.topology.tier");
    public static final AttributeKey<String> TOPOLOGY_DOMAIN =
            AttributeKey.stringKey("agenttel.topology.domain");
    public static final AttributeKey<String> TOPOLOGY_ON_CALL_CHANNEL =
            AttributeKey.stringKey("agenttel.topology.on_call_channel");
    public static final AttributeKey<String> TOPOLOGY_REPO_URL =
            AttributeKey.stringKey("agenttel.topology.repo_url");
    public static final AttributeKey<String> TOPOLOGY_DEPENDENCIES =
            AttributeKey.stringKey("agenttel.topology.dependencies");
    public static final AttributeKey<String> TOPOLOGY_CONSUMERS =
            AttributeKey.stringKey("agenttel.topology.consumers");

    // --- Baselines ---
    public static final AttributeKey<Double> BASELINE_LATENCY_P50_MS =
            AttributeKey.doubleKey("agenttel.baseline.latency_p50_ms");
    public static final AttributeKey<Double> BASELINE_LATENCY_P99_MS =
            AttributeKey.doubleKey("agenttel.baseline.latency_p99_ms");
    public static final AttributeKey<Double> BASELINE_ERROR_RATE =
            AttributeKey.doubleKey("agenttel.baseline.error_rate");
    public static final AttributeKey<Double> BASELINE_THROUGHPUT_RPS =
            AttributeKey.doubleKey("agenttel.baseline.throughput_rps");
    public static final AttributeKey<String> BASELINE_SOURCE =
            AttributeKey.stringKey("agenttel.baseline.source");
    public static final AttributeKey<String> BASELINE_UPDATED_AT =
            AttributeKey.stringKey("agenttel.baseline.updated_at");
    public static final AttributeKey<String> BASELINE_SLO =
            AttributeKey.stringKey("agenttel.baseline.slo");
    public static final AttributeKey<Long> BASELINE_SAMPLE_COUNT =
            AttributeKey.longKey("agenttel.baseline.sample_count");
    public static final AttributeKey<String> BASELINE_CONFIDENCE =
            AttributeKey.stringKey("agenttel.baseline.confidence");

    // --- Causality ---
    public static final AttributeKey<String> CAUSE_HINT =
            AttributeKey.stringKey("agenttel.cause.hint");
    public static final AttributeKey<String> CAUSE_CATEGORY =
            AttributeKey.stringKey("agenttel.cause.category");
    public static final AttributeKey<String> CAUSE_DEPENDENCY =
            AttributeKey.stringKey("agenttel.cause.dependency");
    public static final AttributeKey<String> CAUSE_CORRELATED_SPAN_ID =
            AttributeKey.stringKey("agenttel.cause.correlated_span_id");
    public static final AttributeKey<String> CAUSE_CORRELATED_EVENT_ID =
            AttributeKey.stringKey("agenttel.cause.correlated_event_id");
    public static final AttributeKey<String> CAUSE_STARTED_AT =
            AttributeKey.stringKey("agenttel.cause.started_at");

    // --- Decision ---
    public static final AttributeKey<Boolean> DECISION_RETRYABLE =
            AttributeKey.booleanKey("agenttel.decision.retryable");
    public static final AttributeKey<Long> DECISION_RETRY_AFTER_MS =
            AttributeKey.longKey("agenttel.decision.retry_after_ms");
    public static final AttributeKey<Boolean> DECISION_IDEMPOTENT =
            AttributeKey.booleanKey("agenttel.decision.idempotent");
    public static final AttributeKey<Boolean> DECISION_FALLBACK_AVAILABLE =
            AttributeKey.booleanKey("agenttel.decision.fallback_available");
    public static final AttributeKey<String> DECISION_FALLBACK_DESCRIPTION =
            AttributeKey.stringKey("agenttel.decision.fallback_description");
    public static final AttributeKey<String> DECISION_RUNBOOK_URL =
            AttributeKey.stringKey("agenttel.decision.runbook_url");
    public static final AttributeKey<String> DECISION_ESCALATION_LEVEL =
            AttributeKey.stringKey("agenttel.decision.escalation_level");
    public static final AttributeKey<String> DECISION_KNOWN_ISSUE_ID =
            AttributeKey.stringKey("agenttel.decision.known_issue_id");
    public static final AttributeKey<Boolean> DECISION_SAFE_TO_RESTART =
            AttributeKey.booleanKey("agenttel.decision.safe_to_restart");

    // --- Severity ---
    public static final AttributeKey<Double> SEVERITY_ANOMALY_SCORE =
            AttributeKey.doubleKey("agenttel.severity.anomaly_score");
    public static final AttributeKey<String> SEVERITY_PATTERN =
            AttributeKey.stringKey("agenttel.severity.pattern");
    public static final AttributeKey<String> SEVERITY_IMPACT_SCOPE =
            AttributeKey.stringKey("agenttel.severity.impact_scope");
    public static final AttributeKey<String> SEVERITY_BUSINESS_IMPACT =
            AttributeKey.stringKey("agenttel.severity.business_impact");
    public static final AttributeKey<Boolean> SEVERITY_USER_FACING =
            AttributeKey.booleanKey("agenttel.severity.user_facing");

    // --- Deployment ---
    public static final AttributeKey<String> DEPLOYMENT_ID =
            AttributeKey.stringKey("agenttel.deployment.id");
    public static final AttributeKey<String> DEPLOYMENT_VERSION =
            AttributeKey.stringKey("agenttel.deployment.version");
    public static final AttributeKey<String> DEPLOYMENT_COMMIT_SHA =
            AttributeKey.stringKey("agenttel.deployment.commit_sha");
    public static final AttributeKey<String> DEPLOYMENT_PREVIOUS_VERSION =
            AttributeKey.stringKey("agenttel.deployment.previous_version");
    public static final AttributeKey<String> DEPLOYMENT_STRATEGY =
            AttributeKey.stringKey("agenttel.deployment.strategy");
    public static final AttributeKey<String> DEPLOYMENT_TIMESTAMP =
            AttributeKey.stringKey("agenttel.deployment.timestamp");

    // --- GenAI ---
    public static final AttributeKey<String> GENAI_FRAMEWORK =
            AttributeKey.stringKey("agenttel.genai.framework");
    public static final AttributeKey<Double> GENAI_COST_USD =
            AttributeKey.doubleKey("agenttel.genai.cost_usd");
    public static final AttributeKey<Long> GENAI_RAG_SOURCE_COUNT =
            AttributeKey.longKey("agenttel.genai.rag_source_count");
    public static final AttributeKey<Double> GENAI_RAG_RELEVANCE_SCORE_AVG =
            AttributeKey.doubleKey("agenttel.genai.rag_relevance_score_avg");
    public static final AttributeKey<Boolean> GENAI_GUARDRAIL_TRIGGERED =
            AttributeKey.booleanKey("agenttel.genai.guardrail_triggered");
    public static final AttributeKey<String> GENAI_GUARDRAIL_NAME =
            AttributeKey.stringKey("agenttel.genai.guardrail_name");
    public static final AttributeKey<Boolean> GENAI_CACHE_HIT =
            AttributeKey.booleanKey("agenttel.genai.cache_hit");

    // --- Anomaly ---
    public static final AttributeKey<Boolean> ANOMALY_DETECTED =
            AttributeKey.booleanKey("agenttel.anomaly.detected");
    public static final AttributeKey<String> ANOMALY_PATTERN =
            AttributeKey.stringKey("agenttel.anomaly.pattern");
    public static final AttributeKey<Double> ANOMALY_SCORE =
            AttributeKey.doubleKey("agenttel.anomaly.score");
    public static final AttributeKey<Double> ANOMALY_LATENCY_Z_SCORE =
            AttributeKey.doubleKey("agenttel.anomaly.latency_z_score");

    // --- SLO ---
    public static final AttributeKey<String> SLO_NAME =
            AttributeKey.stringKey("agenttel.slo.name");
    public static final AttributeKey<Double> SLO_TARGET =
            AttributeKey.doubleKey("agenttel.slo.target");
    public static final AttributeKey<Double> SLO_BUDGET_REMAINING =
            AttributeKey.doubleKey("agenttel.slo.budget_remaining");
    public static final AttributeKey<Double> SLO_BURN_RATE =
            AttributeKey.doubleKey("agenttel.slo.burn_rate");

    // --- Error Classification ---
    public static final AttributeKey<String> ERROR_CATEGORY =
            AttributeKey.stringKey("agenttel.error.category");
    public static final AttributeKey<String> ERROR_ROOT_EXCEPTION =
            AttributeKey.stringKey("agenttel.error.root_exception");
    public static final AttributeKey<String> ERROR_DEPENDENCY =
            AttributeKey.stringKey("agenttel.error.dependency");

    // --- Change Correlation ---
    public static final AttributeKey<String> CORRELATION_LIKELY_CAUSE =
            AttributeKey.stringKey("agenttel.correlation.likely_cause");
    public static final AttributeKey<String> CORRELATION_CHANGE_ID =
            AttributeKey.stringKey("agenttel.correlation.change_id");
    public static final AttributeKey<Long> CORRELATION_TIME_DELTA_MS =
            AttributeKey.longKey("agenttel.correlation.time_delta_ms");
    public static final AttributeKey<Double> CORRELATION_CONFIDENCE =
            AttributeKey.doubleKey("agenttel.correlation.confidence");

    // --- Agent Identity ---
    public static final AttributeKey<String> AGENT_ID =
            AttributeKey.stringKey("agenttel.agent.id");
    public static final AttributeKey<String> AGENT_ROLE =
            AttributeKey.stringKey("agenttel.agent.role");
    public static final AttributeKey<String> AGENT_SESSION_ID =
            AttributeKey.stringKey("agenttel.agent.session_id");

    // --- Session ---
    public static final AttributeKey<String> SESSION_ID =
            AttributeKey.stringKey("agenttel.session.id");
    public static final AttributeKey<String> SESSION_INCIDENT_ID =
            AttributeKey.stringKey("agenttel.session.incident_id");

    // --- Circuit Breaker ---
    public static final AttributeKey<String> CIRCUIT_BREAKER_NAME =
            AttributeKey.stringKey("agenttel.circuit_breaker.name");
    public static final AttributeKey<String> CIRCUIT_BREAKER_PREVIOUS_STATE =
            AttributeKey.stringKey("agenttel.circuit_breaker.previous_state");
    public static final AttributeKey<String> CIRCUIT_BREAKER_NEW_STATE =
            AttributeKey.stringKey("agenttel.circuit_breaker.new_state");
    public static final AttributeKey<Long> CIRCUIT_BREAKER_FAILURE_COUNT =
            AttributeKey.longKey("agenttel.circuit_breaker.failure_count");
    public static final AttributeKey<String> CIRCUIT_BREAKER_DEPENDENCY =
            AttributeKey.stringKey("agenttel.circuit_breaker.dependency");

    // --- Dependency health event ---
    public static final AttributeKey<String> DEPENDENCY_NAME =
            AttributeKey.stringKey("agenttel.dependency.name");
    public static final AttributeKey<String> DEPENDENCY_PREVIOUS_STATE =
            AttributeKey.stringKey("agenttel.dependency.previous_state");
    public static final AttributeKey<String> DEPENDENCY_NEW_STATE =
            AttributeKey.stringKey("agenttel.dependency.new_state");
}
