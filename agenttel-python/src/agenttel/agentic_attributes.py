"""Agentic observability semantic attributes (``agenttel.agentic.*``).

Values match the canonical ``attributes.json`` at the repository root.
SDK-specific keys that are not in the canonical schema live in
:mod:`agenttel.extension_attributes`.
"""

# Agent Identity
AGENTIC_AGENT_NAME = "agenttel.agentic.agent.name"
AGENTIC_AGENT_TYPE = "agenttel.agentic.agent.type"
AGENTIC_AGENT_FRAMEWORK = "agenttel.agentic.agent.framework"
AGENTIC_AGENT_VERSION = "agenttel.agentic.agent.version"

# Invocation
AGENTIC_INVOCATION_ID = "agenttel.agentic.invocation.id"
AGENTIC_INVOCATION_GOAL = "agenttel.agentic.invocation.goal"
AGENTIC_INVOCATION_STATUS = "agenttel.agentic.invocation.status"
AGENTIC_INVOCATION_STEPS = "agenttel.agentic.invocation.steps"
AGENTIC_INVOCATION_MAX_STEPS = "agenttel.agentic.invocation.max_steps"

# Task
AGENTIC_TASK_ID = "agenttel.agentic.task.id"
AGENTIC_TASK_NAME = "agenttel.agentic.task.name"
AGENTIC_TASK_STATUS = "agenttel.agentic.task.status"
AGENTIC_TASK_PARENT_ID = "agenttel.agentic.task.parent_id"
AGENTIC_TASK_DEPTH = "agenttel.agentic.task.depth"

# Step
AGENTIC_STEP_NUMBER = "agenttel.agentic.step.number"
AGENTIC_STEP_TYPE = "agenttel.agentic.step.type"
AGENTIC_STEP_ITERATION = "agenttel.agentic.step.iteration"
AGENTIC_STEP_TOOL_NAME = "agenttel.agentic.step.tool_name"
AGENTIC_STEP_TOOL_STATUS = "agenttel.agentic.step.tool_status"

# Orchestration
AGENTIC_ORCHESTRATION_PATTERN = "agenttel.agentic.orchestration.pattern"
AGENTIC_ORCHESTRATION_COORDINATOR_ID = "agenttel.agentic.orchestration.coordinator_id"
AGENTIC_ORCHESTRATION_STAGE = "agenttel.agentic.orchestration.stage"
AGENTIC_ORCHESTRATION_TOTAL_STAGES = "agenttel.agentic.orchestration.total_stages"
AGENTIC_ORCHESTRATION_PARALLEL_BRANCHES = "agenttel.agentic.orchestration.parallel_branches"
AGENTIC_ORCHESTRATION_AGGREGATION = "agenttel.agentic.orchestration.aggregation"

# Handoff
AGENTIC_HANDOFF_FROM_AGENT = "agenttel.agentic.handoff.from_agent"
AGENTIC_HANDOFF_TO_AGENT = "agenttel.agentic.handoff.to_agent"
AGENTIC_HANDOFF_REASON = "agenttel.agentic.handoff.reason"
AGENTIC_HANDOFF_CHAIN_DEPTH = "agenttel.agentic.handoff.chain_depth"

# Cost
AGENTIC_COST_TOTAL_USD = "agenttel.agentic.cost.total_usd"
AGENTIC_COST_INPUT_TOKENS = "agenttel.agentic.cost.input_tokens"
AGENTIC_COST_OUTPUT_TOKENS = "agenttel.agentic.cost.output_tokens"
AGENTIC_COST_LLM_CALLS = "agenttel.agentic.cost.llm_calls"
AGENTIC_COST_REASONING_TOKENS = "agenttel.agentic.cost.reasoning_tokens"
AGENTIC_COST_CACHED_READ_TOKENS = "agenttel.agentic.cost.cached_read_tokens"
AGENTIC_COST_CACHED_WRITE_TOKENS = "agenttel.agentic.cost.cached_write_tokens"

# Quality
AGENTIC_QUALITY_GOAL_ACHIEVED = "agenttel.agentic.quality.goal_achieved"
AGENTIC_QUALITY_HUMAN_INTERVENTIONS = "agenttel.agentic.quality.human_interventions"
AGENTIC_QUALITY_LOOP_DETECTED = "agenttel.agentic.quality.loop_detected"
AGENTIC_QUALITY_LOOP_ITERATIONS = "agenttel.agentic.quality.loop_iterations"
AGENTIC_QUALITY_EVAL_SCORE = "agenttel.agentic.quality.eval_score"

# Guardrail
AGENTIC_GUARDRAIL_TRIGGERED = "agenttel.agentic.guardrail.triggered"
AGENTIC_GUARDRAIL_NAME = "agenttel.agentic.guardrail.name"
AGENTIC_GUARDRAIL_ACTION = "agenttel.agentic.guardrail.action"
AGENTIC_GUARDRAIL_REASON = "agenttel.agentic.guardrail.reason"

# Memory
AGENTIC_MEMORY_OPERATION = "agenttel.agentic.memory.operation"
AGENTIC_MEMORY_STORE_TYPE = "agenttel.agentic.memory.store_type"
AGENTIC_MEMORY_ITEMS = "agenttel.agentic.memory.items"

# Human-in-the-Loop
AGENTIC_HUMAN_CHECKPOINT_TYPE = "agenttel.agentic.human.checkpoint_type"
AGENTIC_HUMAN_WAIT_MS = "agenttel.agentic.human.wait_ms"
AGENTIC_HUMAN_DECISION = "agenttel.agentic.human.decision"

# Code Execution
AGENTIC_CODE_LANGUAGE = "agenttel.agentic.code.language"
AGENTIC_CODE_STATUS = "agenttel.agentic.code.status"
AGENTIC_CODE_EXIT_CODE = "agenttel.agentic.code.exit_code"
AGENTIC_CODE_SANDBOXED = "agenttel.agentic.code.sandboxed"

# Evaluation
AGENTIC_EVAL_SCORER_NAME = "agenttel.agentic.eval.scorer_name"
AGENTIC_EVAL_CRITERIA = "agenttel.agentic.eval.criteria"
AGENTIC_EVAL_SCORE = "agenttel.agentic.eval.score"
AGENTIC_EVAL_FEEDBACK = "agenttel.agentic.eval.feedback"
AGENTIC_EVAL_TYPE = "agenttel.agentic.eval.type"

# Conversation
AGENTIC_CONVERSATION_ID = "agenttel.agentic.conversation.id"
AGENTIC_CONVERSATION_TURN = "agenttel.agentic.conversation.turn"
AGENTIC_CONVERSATION_MESSAGE_COUNT = "agenttel.agentic.conversation.message_count"
AGENTIC_CONVERSATION_SPEAKER_ROLE = "agenttel.agentic.conversation.speaker_role"

# Retrieval
AGENTIC_RETRIEVAL_QUERY = "agenttel.agentic.retrieval.query"
AGENTIC_RETRIEVAL_STORE_TYPE = "agenttel.agentic.retrieval.store_type"
AGENTIC_RETRIEVAL_DOCUMENT_COUNT = "agenttel.agentic.retrieval.document_count"
AGENTIC_RETRIEVAL_TOP_K = "agenttel.agentic.retrieval.top_k"
AGENTIC_RETRIEVAL_RELEVANCE_SCORE_AVG = "agenttel.agentic.retrieval.relevance_score_avg"
AGENTIC_RETRIEVAL_RELEVANCE_SCORE_MIN = "agenttel.agentic.retrieval.relevance_score_min"

# Reranker
AGENTIC_RERANKER_MODEL = "agenttel.agentic.reranker.model"
AGENTIC_RERANKER_INPUT_DOCUMENTS = "agenttel.agentic.reranker.input_documents"
AGENTIC_RERANKER_OUTPUT_DOCUMENTS = "agenttel.agentic.reranker.output_documents"
AGENTIC_RERANKER_TOP_SCORE = "agenttel.agentic.reranker.top_score"

# Error
AGENTIC_ERROR_SOURCE = "agenttel.agentic.error.source"
AGENTIC_ERROR_CATEGORY = "agenttel.agentic.error.category"
AGENTIC_ERROR_RETRYABLE = "agenttel.agentic.error.retryable"

# Capability
AGENTIC_CAPABILITY_TOOL_COUNT = "agenttel.agentic.capability.tool_count"
AGENTIC_CAPABILITY_SYSTEM_PROMPT_HASH = "agenttel.agentic.capability.system_prompt_hash"

# Deprecated aliases (pre-0.4.0 names). Values now point at the canonical
# agenttel.agentic.* keys; the old top-level keys (agenttel.agent.name,
# agenttel.step.*, ...) are no longer emitted.
AGENT_NAME = AGENTIC_AGENT_NAME
AGENT_TYPE = AGENTIC_AGENT_TYPE
AGENT_FRAMEWORK = AGENTIC_AGENT_FRAMEWORK
AGENT_VERSION = AGENTIC_AGENT_VERSION
INVOCATION_ID = AGENTIC_INVOCATION_ID
INVOCATION_GOAL = AGENTIC_INVOCATION_GOAL
INVOCATION_STATUS = AGENTIC_INVOCATION_STATUS
INVOCATION_STEPS = AGENTIC_INVOCATION_STEPS
INVOCATION_ERROR_SOURCE = AGENTIC_ERROR_SOURCE
TASK_ID = AGENTIC_TASK_ID
TASK_NAME = AGENTIC_TASK_NAME
TASK_STATUS = AGENTIC_TASK_STATUS
TASK_PARENT_ID = AGENTIC_TASK_PARENT_ID
TASK_DEPTH = AGENTIC_TASK_DEPTH
STEP_NUMBER = AGENTIC_STEP_NUMBER
STEP_TYPE = AGENTIC_STEP_TYPE
STEP_ITERATION = AGENTIC_STEP_ITERATION
STEP_TOOL_NAME = AGENTIC_STEP_TOOL_NAME
STEP_TOOL_STATUS = AGENTIC_STEP_TOOL_STATUS
ORCHESTRATION_PATTERN = AGENTIC_ORCHESTRATION_PATTERN
ORCHESTRATION_COORDINATOR_ID = AGENTIC_ORCHESTRATION_COORDINATOR_ID
ORCHESTRATION_STAGE = AGENTIC_ORCHESTRATION_STAGE
ORCHESTRATION_STAGE_COUNT = AGENTIC_ORCHESTRATION_TOTAL_STAGES
ORCHESTRATION_PARALLEL_BRANCHES = AGENTIC_ORCHESTRATION_PARALLEL_BRANCHES
HANDOFF_FROM_AGENT = AGENTIC_HANDOFF_FROM_AGENT
HANDOFF_TO_AGENT = AGENTIC_HANDOFF_TO_AGENT
HANDOFF_REASON = AGENTIC_HANDOFF_REASON
HANDOFF_CHAIN_DEPTH = AGENTIC_HANDOFF_CHAIN_DEPTH
COST_TOTAL_USD = AGENTIC_COST_TOTAL_USD
COST_INPUT_TOKENS = AGENTIC_COST_INPUT_TOKENS
COST_OUTPUT_TOKENS = AGENTIC_COST_OUTPUT_TOKENS
COST_REASONING_TOKENS = AGENTIC_COST_REASONING_TOKENS
COST_LLM_CALLS = AGENTIC_COST_LLM_CALLS
QUALITY_GOAL_ACHIEVED = AGENTIC_QUALITY_GOAL_ACHIEVED
QUALITY_HUMAN_INTERVENTIONS = AGENTIC_QUALITY_HUMAN_INTERVENTIONS
QUALITY_LOOP_DETECTED = AGENTIC_QUALITY_LOOP_DETECTED
GUARDRAIL_TRIGGERED = AGENTIC_GUARDRAIL_TRIGGERED
GUARDRAIL_NAME = AGENTIC_GUARDRAIL_NAME
GUARDRAIL_ACTION = AGENTIC_GUARDRAIL_ACTION
GUARDRAIL_REASON = AGENTIC_GUARDRAIL_REASON
MEMORY_OPERATION = AGENTIC_MEMORY_OPERATION
MEMORY_STORE_TYPE = AGENTIC_MEMORY_STORE_TYPE
MEMORY_ITEMS = AGENTIC_MEMORY_ITEMS
HUMAN_CHECKPOINT_TYPE = AGENTIC_HUMAN_CHECKPOINT_TYPE
HUMAN_WAIT_MS = AGENTIC_HUMAN_WAIT_MS
HUMAN_DECISION = AGENTIC_HUMAN_DECISION
CODE_LANGUAGE = AGENTIC_CODE_LANGUAGE
CODE_STATUS = AGENTIC_CODE_STATUS
CODE_EXIT_CODE = AGENTIC_CODE_EXIT_CODE
CODE_SANDBOXED = AGENTIC_CODE_SANDBOXED
EVAL_SCORER_NAME = AGENTIC_EVAL_SCORER_NAME
EVAL_CRITERIA = AGENTIC_EVAL_CRITERIA
EVAL_SCORE = AGENTIC_EVAL_SCORE
EVAL_FEEDBACK = AGENTIC_EVAL_FEEDBACK
EVAL_TYPE = AGENTIC_EVAL_TYPE
RETRIEVAL_QUERY = AGENTIC_RETRIEVAL_QUERY
RETRIEVAL_STORE_TYPE = AGENTIC_RETRIEVAL_STORE_TYPE
RETRIEVAL_DOCUMENT_COUNT = AGENTIC_RETRIEVAL_DOCUMENT_COUNT
RETRIEVAL_RELEVANCE_SCORE = AGENTIC_RETRIEVAL_RELEVANCE_SCORE_AVG
CONVERSATION_ID = AGENTIC_CONVERSATION_ID
CONVERSATION_TURN = AGENTIC_CONVERSATION_TURN
CONVERSATION_MESSAGE_COUNT = AGENTIC_CONVERSATION_MESSAGE_COUNT
CONVERSATION_ROLE = AGENTIC_CONVERSATION_SPEAKER_ROLE
