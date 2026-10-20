"""Consistent GenAI span creation following OTel semantic conventions."""

from __future__ import annotations

from typing import Any

from opentelemetry import trace

from agenttel.genai import attributes as genai_attr
from agenttel import extension_attributes as ext
from agenttel.genai.cost import ModelCostCalculator


class GenAiSpanBuilder:
    """Builder for creating GenAI spans with consistent attributes."""

    def __init__(
        self,
        tracer: trace.Tracer | None = None,
        cost_calculator: ModelCostCalculator | None = None,
    ) -> None:
        self._tracer = tracer or trace.get_tracer("agenttel.genai")
        self._cost_calculator = cost_calculator or ModelCostCalculator()

    def start_chat_span(
        self,
        model: str,
        system: str,
        **kwargs: Any,
    ) -> trace.Span:
        """Start a chat completion span."""
        span = self._tracer.start_span(
            f"gen_ai chat {model}",
            kind=trace.SpanKind.CLIENT,
        )
        span.set_attribute(genai_attr.OPERATION_NAME, "chat")
        span.set_attribute(genai_attr.SYSTEM, system)
        span.set_attribute(genai_attr.REQUEST_MODEL, model)

        if "temperature" in kwargs:
            span.set_attribute(genai_attr.REQUEST_TEMPERATURE, kwargs["temperature"])
        if "max_tokens" in kwargs:
            span.set_attribute(genai_attr.REQUEST_MAX_TOKENS, kwargs["max_tokens"])
        if "top_p" in kwargs:
            span.set_attribute(genai_attr.REQUEST_TOP_P, kwargs["top_p"])

        # AgentTel extensions
        if "framework" in kwargs:
            span.set_attribute(genai_attr.FRAMEWORK, kwargs["framework"])

        return span

    def start_embedding_span(
        self,
        model: str,
        system: str,
        **kwargs: Any,
    ) -> trace.Span:
        """Start an embedding span."""
        span = self._tracer.start_span(
            f"gen_ai embeddings {model}",
            kind=trace.SpanKind.CLIENT,
        )
        span.set_attribute(genai_attr.OPERATION_NAME, "embeddings")
        span.set_attribute(genai_attr.SYSTEM, system)
        span.set_attribute(genai_attr.REQUEST_MODEL, model)
        return span

    def start_retrieval_span(
        self,
        source: str,
        **kwargs: Any,
    ) -> trace.Span:
        """Start a retrieval span."""
        span = self._tracer.start_span(
            f"gen_ai retrieval {source}",
            kind=trace.SpanKind.CLIENT,
        )
        span.set_attribute(genai_attr.OPERATION_NAME, "retrieval")
        span.set_attribute(ext.GENAI_RETRIEVAL_SOURCE, source)

        if "rag_enabled" in kwargs:
            span.set_attribute(ext.GENAI_RAG_ENABLED, kwargs["rag_enabled"])
        return span

    def end_span_with_response(
        self,
        span: trace.Span,
        model: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        reasoning_tokens: int = 0,
        cached_tokens: int = 0,
        finish_reason: str | None = None,
        response_id: str | None = None,
    ) -> None:
        """End a span with response data and cost calculation."""
        if not span.is_recording():
            return

        if model:
            span.set_attribute(genai_attr.RESPONSE_MODEL, model)
        if response_id:
            span.set_attribute(genai_attr.RESPONSE_ID, response_id)
        if finish_reason:
            span.set_attribute(genai_attr.RESPONSE_FINISH_REASONS, [finish_reason])

        span.set_attribute(genai_attr.USAGE_INPUT_TOKENS, input_tokens)
        span.set_attribute(genai_attr.USAGE_OUTPUT_TOKENS, output_tokens)
        total = input_tokens + output_tokens
        span.set_attribute(ext.GENAI_USAGE_TOTAL_TOKENS, total)

        if reasoning_tokens > 0:
            span.set_attribute(genai_attr.REASONING_TOKENS, reasoning_tokens)
        if cached_tokens > 0:
            span.set_attribute(genai_attr.CACHED_READ_TOKENS, cached_tokens)

        # Calculate and set cost
        if model and total > 0:
            cost = self._cost_calculator.calculate(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            if cost > 0:
                span.set_attribute(genai_attr.COST_USD, cost)

        span.end()
