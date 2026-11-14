package attributes

// Agentic agent identity attributes.
const (
	AgenticAgentName      = "agenttel.agentic.agent.name"
	AgenticAgentType      = "agenttel.agentic.agent.type"
	AgenticAgentFramework = "agenttel.agentic.agent.framework"
	AgenticAgentVersion   = "agenttel.agentic.agent.version"
)

// Agentic invocation attributes.
const (
	AgenticInvocationID       = "agenttel.agentic.invocation.id"
	AgenticInvocationGoal     = "agenttel.agentic.invocation.goal"
	AgenticInvocationStatus   = "agenttel.agentic.invocation.status"
	AgenticInvocationSteps    = "agenttel.agentic.invocation.steps"
	AgenticInvocationMaxSteps = "agenttel.agentic.invocation.max_steps"
)

// Agentic task tracking attributes.
const (
	AgenticTaskID       = "agenttel.agentic.task.id"
	AgenticTaskName     = "agenttel.agentic.task.name"
	AgenticTaskStatus   = "agenttel.agentic.task.status"
	AgenticTaskParentID = "agenttel.agentic.task.parent_id"
	AgenticTaskDepth    = "agenttel.agentic.task.depth"
)

// Agentic step and reasoning attributes.
const (
	AgenticStepNumber     = "agenttel.agentic.step.number"
	AgenticStepType       = "agenttel.agentic.step.type"
	AgenticStepIteration  = "agenttel.agentic.step.iteration"
	AgenticStepToolName   = "agenttel.agentic.step.tool_name"
	AgenticStepToolStatus = "agenttel.agentic.step.tool_status"
)

// Agentic orchestration attributes.
const (
	AgenticOrchestrationPattern          = "agenttel.agentic.orchestration.pattern"
	AgenticOrchestrationCoordinatorID    = "agenttel.agentic.orchestration.coordinator_id"
	AgenticOrchestrationStage            = "agenttel.agentic.orchestration.stage"
	AgenticOrchestrationTotalStages      = "agenttel.agentic.orchestration.total_stages"
	AgenticOrchestrationParallelBranches = "agenttel.agentic.orchestration.parallel_branches"
	AgenticOrchestrationAggregation      = "agenttel.agentic.orchestration.aggregation"
)

// Agentic handoff attributes.
const (
	AgenticHandoffFromAgent  = "agenttel.agentic.handoff.from_agent"
	AgenticHandoffToAgent    = "agenttel.agentic.handoff.to_agent"
	AgenticHandoffReason     = "agenttel.agentic.handoff.reason"
	AgenticHandoffChainDepth = "agenttel.agentic.handoff.chain_depth"
)

// Agentic cost attributes.
const (
	AgenticCostTotalUSD          = "agenttel.agentic.cost.total_usd"
	AgenticCostInputTokens       = "agenttel.agentic.cost.input_tokens"
	AgenticCostOutputTokens      = "agenttel.agentic.cost.output_tokens"
	AgenticCostLLMCalls          = "agenttel.agentic.cost.llm_calls"
	AgenticCostReasoningTokens   = "agenttel.agentic.cost.reasoning_tokens"
	AgenticCostCachedReadTokens  = "agenttel.agentic.cost.cached_read_tokens"
	AgenticCostCachedWriteTokens = "agenttel.agentic.cost.cached_write_tokens"
)

// Agentic quality attributes.
const (
	AgenticQualityGoalAchieved       = "agenttel.agentic.quality.goal_achieved"
	AgenticQualityHumanInterventions = "agenttel.agentic.quality.human_interventions"
	AgenticQualityLoopDetected       = "agenttel.agentic.quality.loop_detected"
	AgenticQualityLoopIterations     = "agenttel.agentic.quality.loop_iterations"
	AgenticQualityEvalScore          = "agenttel.agentic.quality.eval_score"
)

// Agentic guardrail attributes.
const (
	AgenticGuardrailTriggered = "agenttel.agentic.guardrail.triggered"
	AgenticGuardrailName      = "agenttel.agentic.guardrail.name"
	AgenticGuardrailAction    = "agenttel.agentic.guardrail.action"
	AgenticGuardrailReason    = "agenttel.agentic.guardrail.reason"
)

// Agentic memory attributes.
const (
	AgenticMemoryOperation = "agenttel.agentic.memory.operation"
	AgenticMemoryStoreType = "agenttel.agentic.memory.store_type"
	AgenticMemoryItems     = "agenttel.agentic.memory.items"
)

// Agentic human-in-the-loop attributes.
const (
	AgenticHumanCheckpointType = "agenttel.agentic.human.checkpoint_type"
	AgenticHumanWaitMs         = "agenttel.agentic.human.wait_ms"
	AgenticHumanDecision       = "agenttel.agentic.human.decision"
)

// Agentic code execution attributes.
const (
	AgenticCodeLanguage  = "agenttel.agentic.code.language"
	AgenticCodeStatus    = "agenttel.agentic.code.status"
	AgenticCodeExitCode  = "agenttel.agentic.code.exit_code"
	AgenticCodeSandboxed = "agenttel.agentic.code.sandboxed"
)

// Agentic evaluation attributes.
const (
	AgenticEvalScorerName = "agenttel.agentic.eval.scorer_name"
	AgenticEvalCriteria   = "agenttel.agentic.eval.criteria"
	AgenticEvalScore      = "agenttel.agentic.eval.score"
	AgenticEvalFeedback   = "agenttel.agentic.eval.feedback"
	AgenticEvalType       = "agenttel.agentic.eval.type"
)

// Agentic conversation attributes.
const (
	AgenticConversationID           = "agenttel.agentic.conversation.id"
	AgenticConversationTurn         = "agenttel.agentic.conversation.turn"
	AgenticConversationMessageCount = "agenttel.agentic.conversation.message_count"
	AgenticConversationSpeakerRole  = "agenttel.agentic.conversation.speaker_role"
)

// Agentic retrieval attributes.
const (
	AgenticRetrievalQuery             = "agenttel.agentic.retrieval.query"
	AgenticRetrievalStoreType         = "agenttel.agentic.retrieval.store_type"
	AgenticRetrievalDocumentCount     = "agenttel.agentic.retrieval.document_count"
	AgenticRetrievalTopK              = "agenttel.agentic.retrieval.top_k"
	AgenticRetrievalRelevanceScoreAvg = "agenttel.agentic.retrieval.relevance_score_avg"
	AgenticRetrievalRelevanceScoreMin = "agenttel.agentic.retrieval.relevance_score_min"
)

// Agentic reranker attributes.
const (
	AgenticRerankerModel           = "agenttel.agentic.reranker.model"
	AgenticRerankerInputDocuments  = "agenttel.agentic.reranker.input_documents"
	AgenticRerankerOutputDocuments = "agenttel.agentic.reranker.output_documents"
	AgenticRerankerTopScore        = "agenttel.agentic.reranker.top_score"
)

// Agentic error attributes.
const (
	AgenticErrorSource    = "agenttel.agentic.error.source"
	AgenticErrorCategory  = "agenttel.agentic.error.category"
	AgenticErrorRetryable = "agenttel.agentic.error.retryable"
)

// Agentic capability attributes.
const (
	AgenticCapabilityTools            = "agenttel.agentic.capability.tools"
	AgenticCapabilityToolCount        = "agenttel.agentic.capability.tool_count"
	AgenticCapabilitySystemPromptHash = "agenttel.agentic.capability.system_prompt_hash"
)
