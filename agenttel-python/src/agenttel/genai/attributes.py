"""GenAI semantic attributes following OTel GenAI conventions.

Values match the canonical ``attributes.json`` at the repository root.
SDK-specific keys that are not in the canonical schema live in
:mod:`agenttel.extension_attributes`.
"""

# Standard OTel GenAI semantic conventions
OPERATION_NAME = "gen_ai.operation.name"
SYSTEM = "gen_ai.system"
REQUEST_MODEL = "gen_ai.request.model"
REQUEST_TEMPERATURE = "gen_ai.request.temperature"
REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
REQUEST_TOP_P = "gen_ai.request.top_p"

RESPONSE_MODEL = "gen_ai.response.model"
RESPONSE_FINISH_REASONS = "gen_ai.response.finish_reasons"
RESPONSE_ID = "gen_ai.response.id"

USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"

# AgentTel GenAI extensions
FRAMEWORK = "agenttel.genai.framework"
COST_USD = "agenttel.genai.cost_usd"
CACHE_HIT = "agenttel.genai.cache_hit"
RAG_SOURCE_COUNT = "agenttel.genai.rag_source_count"
RAG_RELEVANCE_SCORE_AVG = "agenttel.genai.rag_relevance_score_avg"
GUARDRAIL_TRIGGERED = "agenttel.genai.guardrail_triggered"
GUARDRAIL_NAME = "agenttel.genai.guardrail_name"
PROMPT_TEMPLATE_ID = "agenttel.genai.prompt_template_id"
PROMPT_TEMPLATE_VERSION = "agenttel.genai.prompt_template_version"
REASONING_TOKENS = "agenttel.genai.reasoning_tokens"
CACHED_READ_TOKENS = "agenttel.genai.cached_read_tokens"
CACHED_WRITE_TOKENS = "agenttel.genai.cached_write_tokens"
TIME_TO_FIRST_TOKEN_MS = "agenttel.genai.time_to_first_token_ms"

# Deprecated aliases (pre-0.4.0 names); values now match attributes.json
USAGE_REASONING_TOKENS = REASONING_TOKENS
USAGE_CACHED_TOKENS = CACHED_READ_TOKENS
RAG_RELEVANCE_SCORE = RAG_RELEVANCE_SCORE_AVG
RETRIEVAL_DOCUMENT_COUNT = RAG_SOURCE_COUNT
