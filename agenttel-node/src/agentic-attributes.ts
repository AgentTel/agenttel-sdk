// Agentic agent identity
export const AGENTIC_AGENT_NAME = 'agenttel.agentic.agent.name';
export const AGENTIC_AGENT_TYPE = 'agenttel.agentic.agent.type';
export const AGENTIC_AGENT_FRAMEWORK = 'agenttel.agentic.agent.framework';
export const AGENTIC_AGENT_VERSION = 'agenttel.agentic.agent.version';

// Agentic invocation
export const AGENTIC_INVOCATION_ID = 'agenttel.agentic.invocation.id';
export const AGENTIC_INVOCATION_GOAL = 'agenttel.agentic.invocation.goal';
export const AGENTIC_INVOCATION_STATUS = 'agenttel.agentic.invocation.status';
export const AGENTIC_INVOCATION_STEPS = 'agenttel.agentic.invocation.steps';
export const AGENTIC_INVOCATION_MAX_STEPS = 'agenttel.agentic.invocation.max_steps';

// Agentic task tracking
export const AGENTIC_TASK_ID = 'agenttel.agentic.task.id';
export const AGENTIC_TASK_NAME = 'agenttel.agentic.task.name';
export const AGENTIC_TASK_STATUS = 'agenttel.agentic.task.status';
export const AGENTIC_TASK_PARENT_ID = 'agenttel.agentic.task.parent_id';
export const AGENTIC_TASK_DEPTH = 'agenttel.agentic.task.depth';

// Agentic step and reasoning
export const AGENTIC_STEP_NUMBER = 'agenttel.agentic.step.number';
export const AGENTIC_STEP_TYPE = 'agenttel.agentic.step.type';
export const AGENTIC_STEP_ITERATION = 'agenttel.agentic.step.iteration';
export const AGENTIC_STEP_TOOL_NAME = 'agenttel.agentic.step.tool_name';
export const AGENTIC_STEP_TOOL_STATUS = 'agenttel.agentic.step.tool_status';

// Agentic orchestration
export const AGENTIC_ORCHESTRATION_PATTERN = 'agenttel.agentic.orchestration.pattern';
export const AGENTIC_ORCHESTRATION_COORDINATOR_ID = 'agenttel.agentic.orchestration.coordinator_id';
export const AGENTIC_ORCHESTRATION_STAGE = 'agenttel.agentic.orchestration.stage';
export const AGENTIC_ORCHESTRATION_TOTAL_STAGES = 'agenttel.agentic.orchestration.total_stages';
export const AGENTIC_ORCHESTRATION_PARALLEL_BRANCHES = 'agenttel.agentic.orchestration.parallel_branches';
export const AGENTIC_ORCHESTRATION_AGGREGATION = 'agenttel.agentic.orchestration.aggregation';

// Agentic handoff
export const AGENTIC_HANDOFF_FROM_AGENT = 'agenttel.agentic.handoff.from_agent';
export const AGENTIC_HANDOFF_TO_AGENT = 'agenttel.agentic.handoff.to_agent';
export const AGENTIC_HANDOFF_REASON = 'agenttel.agentic.handoff.reason';
export const AGENTIC_HANDOFF_CHAIN_DEPTH = 'agenttel.agentic.handoff.chain_depth';

// Agentic cost
export const AGENTIC_COST_TOTAL_USD = 'agenttel.agentic.cost.total_usd';
export const AGENTIC_COST_INPUT_TOKENS = 'agenttel.agentic.cost.input_tokens';
export const AGENTIC_COST_OUTPUT_TOKENS = 'agenttel.agentic.cost.output_tokens';
export const AGENTIC_COST_LLM_CALLS = 'agenttel.agentic.cost.llm_calls';
export const AGENTIC_COST_REASONING_TOKENS = 'agenttel.agentic.cost.reasoning_tokens';
export const AGENTIC_COST_CACHED_READ_TOKENS = 'agenttel.agentic.cost.cached_read_tokens';
export const AGENTIC_COST_CACHED_WRITE_TOKENS = 'agenttel.agentic.cost.cached_write_tokens';

// Agentic quality
export const AGENTIC_QUALITY_GOAL_ACHIEVED = 'agenttel.agentic.quality.goal_achieved';
export const AGENTIC_QUALITY_HUMAN_INTERVENTIONS = 'agenttel.agentic.quality.human_interventions';
export const AGENTIC_QUALITY_LOOP_DETECTED = 'agenttel.agentic.quality.loop_detected';
export const AGENTIC_QUALITY_LOOP_ITERATIONS = 'agenttel.agentic.quality.loop_iterations';
export const AGENTIC_QUALITY_EVAL_SCORE = 'agenttel.agentic.quality.eval_score';

// Agentic guardrail
export const AGENTIC_GUARDRAIL_TRIGGERED = 'agenttel.agentic.guardrail.triggered';
export const AGENTIC_GUARDRAIL_NAME = 'agenttel.agentic.guardrail.name';
export const AGENTIC_GUARDRAIL_ACTION = 'agenttel.agentic.guardrail.action';
export const AGENTIC_GUARDRAIL_REASON = 'agenttel.agentic.guardrail.reason';

// Agentic memory
export const AGENTIC_MEMORY_OPERATION = 'agenttel.agentic.memory.operation';
export const AGENTIC_MEMORY_STORE_TYPE = 'agenttel.agentic.memory.store_type';
export const AGENTIC_MEMORY_ITEMS = 'agenttel.agentic.memory.items';

// Agentic human-in-the-loop
export const AGENTIC_HUMAN_CHECKPOINT_TYPE = 'agenttel.agentic.human.checkpoint_type';
export const AGENTIC_HUMAN_WAIT_MS = 'agenttel.agentic.human.wait_ms';
export const AGENTIC_HUMAN_DECISION = 'agenttel.agentic.human.decision';

// Agentic code execution
export const AGENTIC_CODE_LANGUAGE = 'agenttel.agentic.code.language';
export const AGENTIC_CODE_STATUS = 'agenttel.agentic.code.status';
export const AGENTIC_CODE_EXIT_CODE = 'agenttel.agentic.code.exit_code';
export const AGENTIC_CODE_SANDBOXED = 'agenttel.agentic.code.sandboxed';

// Agentic evaluation
export const AGENTIC_EVAL_SCORER_NAME = 'agenttel.agentic.eval.scorer_name';
export const AGENTIC_EVAL_CRITERIA = 'agenttel.agentic.eval.criteria';
export const AGENTIC_EVAL_SCORE = 'agenttel.agentic.eval.score';
export const AGENTIC_EVAL_FEEDBACK = 'agenttel.agentic.eval.feedback';
export const AGENTIC_EVAL_TYPE = 'agenttel.agentic.eval.type';

// Agentic conversation
export const AGENTIC_CONVERSATION_ID = 'agenttel.agentic.conversation.id';
export const AGENTIC_CONVERSATION_TURN = 'agenttel.agentic.conversation.turn';
export const AGENTIC_CONVERSATION_MESSAGE_COUNT = 'agenttel.agentic.conversation.message_count';
export const AGENTIC_CONVERSATION_SPEAKER_ROLE = 'agenttel.agentic.conversation.speaker_role';

// Agentic retrieval
export const AGENTIC_RETRIEVAL_QUERY = 'agenttel.agentic.retrieval.query';
export const AGENTIC_RETRIEVAL_STORE_TYPE = 'agenttel.agentic.retrieval.store_type';
export const AGENTIC_RETRIEVAL_DOCUMENT_COUNT = 'agenttel.agentic.retrieval.document_count';
export const AGENTIC_RETRIEVAL_TOP_K = 'agenttel.agentic.retrieval.top_k';
export const AGENTIC_RETRIEVAL_RELEVANCE_SCORE_AVG = 'agenttel.agentic.retrieval.relevance_score_avg';
export const AGENTIC_RETRIEVAL_RELEVANCE_SCORE_MIN = 'agenttel.agentic.retrieval.relevance_score_min';

// Agentic reranker
export const AGENTIC_RERANKER_MODEL = 'agenttel.agentic.reranker.model';
export const AGENTIC_RERANKER_INPUT_DOCUMENTS = 'agenttel.agentic.reranker.input_documents';
export const AGENTIC_RERANKER_OUTPUT_DOCUMENTS = 'agenttel.agentic.reranker.output_documents';
export const AGENTIC_RERANKER_TOP_SCORE = 'agenttel.agentic.reranker.top_score';

// Agentic error
export const AGENTIC_ERROR_SOURCE = 'agenttel.agentic.error.source';
export const AGENTIC_ERROR_CATEGORY = 'agenttel.agentic.error.category';
export const AGENTIC_ERROR_RETRYABLE = 'agenttel.agentic.error.retryable';

// Agentic capability
export const AGENTIC_CAPABILITY_TOOLS = 'agenttel.agentic.capability.tools';
export const AGENTIC_CAPABILITY_TOOL_COUNT = 'agenttel.agentic.capability.tool_count';
export const AGENTIC_CAPABILITY_SYSTEM_PROMPT_HASH = 'agenttel.agentic.capability.system_prompt_hash';
