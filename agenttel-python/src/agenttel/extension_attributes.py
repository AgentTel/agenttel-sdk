"""Python-SDK-specific attribute keys that are not in the canonical schema.

Everything in :mod:`agenttel.attributes`, :mod:`agenttel.agentic_attributes`
and :mod:`agenttel.genai.attributes` matches ``attributes.json`` exactly
(enforced by ``scripts/validate-attributes.sh``). The keys below are still
emitted by the Python SDK but have no canonical equivalent yet; they are
candidates for adding to ``attributes.json`` or for removal.
"""

# Core
BASELINE_LATENCY_P95_MS = "agenttel.baseline.latency_p95_ms"
OPERATION_PROFILE = "agenttel.operation.profile"

# GenAI
GENAI_USAGE_TOTAL_TOKENS = "gen_ai.usage.total_tokens"
GENAI_RETRIEVAL_SOURCE = "gen_ai.retrieval.source"
GENAI_RAG_ENABLED = "agenttel.genai.rag_enabled"

# Agentic
AGENTIC_STEP_DESCRIPTION = "agenttel.agentic.step.description"
AGENTIC_STEP_TOOL_INPUT = "agenttel.agentic.step.tool_input"
AGENTIC_STEP_TOOL_OUTPUT = "agenttel.agentic.step.tool_output"
AGENTIC_HANDOFF_CONTEXT_KEYS = "agenttel.agentic.handoff.context_keys"
AGENTIC_HUMAN_FEEDBACK = "agenttel.agentic.human.feedback"
AGENTIC_CODE_OUTPUT_SIZE = "agenttel.agentic.code.output_size"
AGENTIC_EVAL_MAX_SCORE = "agenttel.agentic.eval.max_score"
AGENTIC_QUALITY_CONFIDENCE = "agenttel.agentic.quality.confidence"
AGENTIC_GUARDRAIL_INPUT_VIOLATION = "agenttel.agentic.guardrail.input_violation"
AGENTIC_GUARDRAIL_OUTPUT_VIOLATION = "agenttel.agentic.guardrail.output_violation"
