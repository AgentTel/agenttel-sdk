// Topology attributes
export const TOPOLOGY_TEAM = 'agenttel.topology.team';
export const TOPOLOGY_TIER = 'agenttel.topology.tier';
export const TOPOLOGY_DOMAIN = 'agenttel.topology.domain';
export const TOPOLOGY_ON_CALL_CHANNEL = 'agenttel.topology.on_call_channel';
export const TOPOLOGY_REPO_URL = 'agenttel.topology.repo_url';
export const TOPOLOGY_DEPENDENCIES = 'agenttel.topology.dependencies';
export const TOPOLOGY_CONSUMERS = 'agenttel.topology.consumers';

// Baseline attributes
export const BASELINE_LATENCY_P50_MS = 'agenttel.baseline.latency_p50_ms';
export const BASELINE_LATENCY_P99_MS = 'agenttel.baseline.latency_p99_ms';
export const BASELINE_ERROR_RATE = 'agenttel.baseline.error_rate';
export const BASELINE_THROUGHPUT_RPS = 'agenttel.baseline.throughput_rps';
export const BASELINE_SOURCE = 'agenttel.baseline.source';
export const BASELINE_UPDATED_AT = 'agenttel.baseline.updated_at';
export const BASELINE_SLO = 'agenttel.baseline.slo';
export const BASELINE_SAMPLE_COUNT = 'agenttel.baseline.sample_count';
export const BASELINE_CONFIDENCE = 'agenttel.baseline.confidence';

// Causality attributes
export const CAUSE_HINT = 'agenttel.cause.hint';
export const CAUSE_CATEGORY = 'agenttel.cause.category';
export const CAUSE_DEPENDENCY = 'agenttel.cause.dependency';
export const CAUSE_CORRELATED_SPAN_ID = 'agenttel.cause.correlated_span_id';
export const CAUSE_CORRELATED_EVENT_ID = 'agenttel.cause.correlated_event_id';
export const CAUSE_STARTED_AT = 'agenttel.cause.started_at';

// Decision attributes
export const DECISION_RETRYABLE = 'agenttel.decision.retryable';
export const DECISION_RETRY_AFTER_MS = 'agenttel.decision.retry_after_ms';
export const DECISION_IDEMPOTENT = 'agenttel.decision.idempotent';
export const DECISION_FALLBACK_AVAILABLE = 'agenttel.decision.fallback_available';
export const DECISION_FALLBACK_DESCRIPTION = 'agenttel.decision.fallback_description';
export const DECISION_RUNBOOK_URL = 'agenttel.decision.runbook_url';
export const DECISION_ESCALATION_LEVEL = 'agenttel.decision.escalation_level';
export const DECISION_KNOWN_ISSUE_ID = 'agenttel.decision.known_issue_id';
export const DECISION_SAFE_TO_RESTART = 'agenttel.decision.safe_to_restart';

// Severity attributes
export const SEVERITY_ANOMALY_SCORE = 'agenttel.severity.anomaly_score';
export const SEVERITY_PATTERN = 'agenttel.severity.pattern';
export const SEVERITY_IMPACT_SCOPE = 'agenttel.severity.impact_scope';
export const SEVERITY_BUSINESS_IMPACT = 'agenttel.severity.business_impact';
export const SEVERITY_USER_FACING = 'agenttel.severity.user_facing';

// Deployment attributes
export const DEPLOYMENT_ID = 'agenttel.deployment.id';
export const DEPLOYMENT_VERSION = 'agenttel.deployment.version';
export const DEPLOYMENT_COMMIT_SHA = 'agenttel.deployment.commit_sha';
export const DEPLOYMENT_PREVIOUS_VERSION = 'agenttel.deployment.previous_version';
export const DEPLOYMENT_STRATEGY = 'agenttel.deployment.strategy';
export const DEPLOYMENT_TIMESTAMP = 'agenttel.deployment.timestamp';

// GenAI attributes (agenttel extensions)
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

// Anomaly attributes
export const ANOMALY_DETECTED = 'agenttel.anomaly.detected';
export const ANOMALY_PATTERN = 'agenttel.anomaly.pattern';
export const ANOMALY_SCORE = 'agenttel.anomaly.score';
export const ANOMALY_LATENCY_Z_SCORE = 'agenttel.anomaly.latency_z_score';

// SLO attributes
export const SLO_NAME = 'agenttel.slo.name';
export const SLO_TARGET = 'agenttel.slo.target';
export const SLO_BUDGET_REMAINING = 'agenttel.slo.budget_remaining';
export const SLO_BURN_RATE = 'agenttel.slo.burn_rate';

// Error classification attributes
export const ERROR_CATEGORY = 'agenttel.error.category';
export const ERROR_ROOT_EXCEPTION = 'agenttel.error.root_exception';
export const ERROR_DEPENDENCY = 'agenttel.error.dependency';

// Change correlation attributes
export const CORRELATION_LIKELY_CAUSE = 'agenttel.correlation.likely_cause';
export const CORRELATION_CHANGE_ID = 'agenttel.correlation.change_id';
export const CORRELATION_TIME_DELTA_MS = 'agenttel.correlation.time_delta_ms';
export const CORRELATION_CONFIDENCE = 'agenttel.correlation.confidence';

// Agent identity attributes
export const AGENT_ID = 'agenttel.agent.id';
export const AGENT_ROLE = 'agenttel.agent.role';
export const AGENT_SESSION_ID = 'agenttel.agent.session_id';

// Session attributes
export const SESSION_ID = 'agenttel.session.id';
export const SESSION_INCIDENT_ID = 'agenttel.session.incident_id';

// Circuit breaker attributes
export const CIRCUIT_BREAKER_NAME = 'agenttel.circuit_breaker.name';
export const CIRCUIT_BREAKER_PREVIOUS_STATE = 'agenttel.circuit_breaker.previous_state';
export const CIRCUIT_BREAKER_NEW_STATE = 'agenttel.circuit_breaker.new_state';
export const CIRCUIT_BREAKER_FAILURE_COUNT = 'agenttel.circuit_breaker.failure_count';
export const CIRCUIT_BREAKER_DEPENDENCY = 'agenttel.circuit_breaker.dependency';

// Dependency health event attributes
export const DEPENDENCY_NAME = 'agenttel.dependency.name';
export const DEPENDENCY_PREVIOUS_STATE = 'agenttel.dependency.previous_state';
export const DEPENDENCY_NEW_STATE = 'agenttel.dependency.new_state';

// Event name constants
export const EVENT_DEPLOYMENT_INFO = 'agenttel.deployment.info';
export const EVENT_ANOMALY_DETECTED = 'agenttel.anomaly.detected';
export const EVENT_DEPENDENCY_STATE_CHANGE = 'agenttel.dependency.state_change';
export const EVENT_SLO_BUDGET_ALERT = 'agenttel.slo.budget_alert';
export const EVENT_CIRCUIT_BREAKER_STATE_CHANGE = 'agenttel.circuit_breaker.state_change';

// Standard OTel GenAI semantic convention attributes (gen_ai.* namespace)
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

// Agentic agent identity attributes
export const AGENTIC_AGENT_NAME = 'agenttel.agentic.agent.name';
export const AGENTIC_AGENT_TYPE = 'agenttel.agentic.agent.type';
export const AGENTIC_AGENT_FRAMEWORK = 'agenttel.agentic.agent.framework';
export const AGENTIC_AGENT_VERSION = 'agenttel.agentic.agent.version';

// Agentic invocation attributes
export const AGENTIC_INVOCATION_ID = 'agenttel.agentic.invocation.id';
export const AGENTIC_INVOCATION_GOAL = 'agenttel.agentic.invocation.goal';
export const AGENTIC_INVOCATION_STATUS = 'agenttel.agentic.invocation.status';
export const AGENTIC_INVOCATION_STEPS = 'agenttel.agentic.invocation.steps';
export const AGENTIC_INVOCATION_MAX_STEPS = 'agenttel.agentic.invocation.max_steps';

// Agentic task tracking attributes
export const AGENTIC_TASK_ID = 'agenttel.agentic.task.id';
export const AGENTIC_TASK_NAME = 'agenttel.agentic.task.name';
export const AGENTIC_TASK_STATUS = 'agenttel.agentic.task.status';
export const AGENTIC_TASK_PARENT_ID = 'agenttel.agentic.task.parent_id';
export const AGENTIC_TASK_DEPTH = 'agenttel.agentic.task.depth';

// Agentic step and reasoning attributes
export const AGENTIC_STEP_NUMBER = 'agenttel.agentic.step.number';
export const AGENTIC_STEP_TYPE = 'agenttel.agentic.step.type';
export const AGENTIC_STEP_ITERATION = 'agenttel.agentic.step.iteration';
export const AGENTIC_STEP_TOOL_NAME = 'agenttel.agentic.step.tool_name';
export const AGENTIC_STEP_TOOL_STATUS = 'agenttel.agentic.step.tool_status';

// Agentic orchestration attributes
export const AGENTIC_ORCHESTRATION_PATTERN = 'agenttel.agentic.orchestration.pattern';
export const AGENTIC_ORCHESTRATION_COORDINATOR_ID = 'agenttel.agentic.orchestration.coordinator_id';
export const AGENTIC_ORCHESTRATION_STAGE = 'agenttel.agentic.orchestration.stage';
export const AGENTIC_ORCHESTRATION_TOTAL_STAGES = 'agenttel.agentic.orchestration.total_stages';
export const AGENTIC_ORCHESTRATION_PARALLEL_BRANCHES = 'agenttel.agentic.orchestration.parallel_branches';
export const AGENTIC_ORCHESTRATION_AGGREGATION = 'agenttel.agentic.orchestration.aggregation';

// Agentic handoff attributes
export const AGENTIC_HANDOFF_FROM_AGENT = 'agenttel.agentic.handoff.from_agent';
export const AGENTIC_HANDOFF_TO_AGENT = 'agenttel.agentic.handoff.to_agent';
export const AGENTIC_HANDOFF_REASON = 'agenttel.agentic.handoff.reason';
export const AGENTIC_HANDOFF_CHAIN_DEPTH = 'agenttel.agentic.handoff.chain_depth';

// Agentic cost attributes
export const AGENTIC_COST_TOTAL_USD = 'agenttel.agentic.cost.total_usd';
export const AGENTIC_COST_INPUT_TOKENS = 'agenttel.agentic.cost.input_tokens';
export const AGENTIC_COST_OUTPUT_TOKENS = 'agenttel.agentic.cost.output_tokens';
export const AGENTIC_COST_LLM_CALLS = 'agenttel.agentic.cost.llm_calls';
export const AGENTIC_COST_REASONING_TOKENS = 'agenttel.agentic.cost.reasoning_tokens';
export const AGENTIC_COST_CACHED_READ_TOKENS = 'agenttel.agentic.cost.cached_read_tokens';
export const AGENTIC_COST_CACHED_WRITE_TOKENS = 'agenttel.agentic.cost.cached_write_tokens';

// Agentic quality attributes
export const AGENTIC_QUALITY_GOAL_ACHIEVED = 'agenttel.agentic.quality.goal_achieved';
export const AGENTIC_QUALITY_HUMAN_INTERVENTIONS = 'agenttel.agentic.quality.human_interventions';
export const AGENTIC_QUALITY_LOOP_DETECTED = 'agenttel.agentic.quality.loop_detected';
export const AGENTIC_QUALITY_LOOP_ITERATIONS = 'agenttel.agentic.quality.loop_iterations';
export const AGENTIC_QUALITY_EVAL_SCORE = 'agenttel.agentic.quality.eval_score';

// Agentic guardrail attributes
export const AGENTIC_GUARDRAIL_TRIGGERED = 'agenttel.agentic.guardrail.triggered';
export const AGENTIC_GUARDRAIL_NAME = 'agenttel.agentic.guardrail.name';
export const AGENTIC_GUARDRAIL_ACTION = 'agenttel.agentic.guardrail.action';
export const AGENTIC_GUARDRAIL_REASON = 'agenttel.agentic.guardrail.reason';

// Agentic memory attributes
export const AGENTIC_MEMORY_OPERATION = 'agenttel.agentic.memory.operation';
export const AGENTIC_MEMORY_STORE_TYPE = 'agenttel.agentic.memory.store_type';
export const AGENTIC_MEMORY_ITEMS = 'agenttel.agentic.memory.items';

// Agentic human-in-the-loop attributes
export const AGENTIC_HUMAN_CHECKPOINT_TYPE = 'agenttel.agentic.human.checkpoint_type';
export const AGENTIC_HUMAN_WAIT_MS = 'agenttel.agentic.human.wait_ms';
export const AGENTIC_HUMAN_DECISION = 'agenttel.agentic.human.decision';

// Agentic code execution attributes
export const AGENTIC_CODE_LANGUAGE = 'agenttel.agentic.code.language';
export const AGENTIC_CODE_STATUS = 'agenttel.agentic.code.status';
export const AGENTIC_CODE_EXIT_CODE = 'agenttel.agentic.code.exit_code';
export const AGENTIC_CODE_SANDBOXED = 'agenttel.agentic.code.sandboxed';

// Agentic evaluation attributes
export const AGENTIC_EVAL_SCORER_NAME = 'agenttel.agentic.eval.scorer_name';
export const AGENTIC_EVAL_CRITERIA = 'agenttel.agentic.eval.criteria';
export const AGENTIC_EVAL_SCORE = 'agenttel.agentic.eval.score';
export const AGENTIC_EVAL_FEEDBACK = 'agenttel.agentic.eval.feedback';
export const AGENTIC_EVAL_TYPE = 'agenttel.agentic.eval.type';

// Agentic conversation attributes
export const AGENTIC_CONVERSATION_ID = 'agenttel.agentic.conversation.id';
export const AGENTIC_CONVERSATION_TURN = 'agenttel.agentic.conversation.turn';
export const AGENTIC_CONVERSATION_MESSAGE_COUNT = 'agenttel.agentic.conversation.message_count';
export const AGENTIC_CONVERSATION_SPEAKER_ROLE = 'agenttel.agentic.conversation.speaker_role';

// Agentic retrieval attributes
export const AGENTIC_RETRIEVAL_QUERY = 'agenttel.agentic.retrieval.query';
export const AGENTIC_RETRIEVAL_STORE_TYPE = 'agenttel.agentic.retrieval.store_type';
export const AGENTIC_RETRIEVAL_DOCUMENT_COUNT = 'agenttel.agentic.retrieval.document_count';
export const AGENTIC_RETRIEVAL_TOP_K = 'agenttel.agentic.retrieval.top_k';
export const AGENTIC_RETRIEVAL_RELEVANCE_SCORE_AVG = 'agenttel.agentic.retrieval.relevance_score_avg';
export const AGENTIC_RETRIEVAL_RELEVANCE_SCORE_MIN = 'agenttel.agentic.retrieval.relevance_score_min';

// Agentic reranker attributes
export const AGENTIC_RERANKER_MODEL = 'agenttel.agentic.reranker.model';
export const AGENTIC_RERANKER_INPUT_DOCUMENTS = 'agenttel.agentic.reranker.input_documents';
export const AGENTIC_RERANKER_OUTPUT_DOCUMENTS = 'agenttel.agentic.reranker.output_documents';
export const AGENTIC_RERANKER_TOP_SCORE = 'agenttel.agentic.reranker.top_score';

// Agentic error attributes
export const AGENTIC_ERROR_SOURCE = 'agenttel.agentic.error.source';
export const AGENTIC_ERROR_CATEGORY = 'agenttel.agentic.error.category';
export const AGENTIC_ERROR_RETRYABLE = 'agenttel.agentic.error.retryable';

// Agentic capability attributes
export const AGENTIC_CAPABILITY_TOOL_COUNT = 'agenttel.agentic.capability.tool_count';
export const AGENTIC_CAPABILITY_SYSTEM_PROMPT_HASH = 'agenttel.agentic.capability.system_prompt_hash';
