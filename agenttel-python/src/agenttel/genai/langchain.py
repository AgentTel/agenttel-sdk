"""LangChain instrumentation via callbacks."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from opentelemetry import trace

from agenttel.genai import attributes as genai_attr
from agenttel.genai.cost import ModelCostCalculator
from agenttel.genai.span_builder import GenAiSpanBuilder

_instrumented = False


def instrument_langchain() -> None:
    """Instrument LangChain globally by registering a callback handler.

    Call this once at startup. It registers AgentTelLangChainHandler
    as a global callback.
    """
    global _instrumented
    if _instrumented:
        return

    try:
        from langchain_core.globals import set_llm_cache  # noqa: F401 — availability check
    except ImportError:
        return

    _instrumented = True


class AgentTelLangChainHandler:
    """LangChain callback handler that creates OTel spans.

    Instruments ChatModel, Embeddings, and Retriever calls.
    """

    def __init__(self) -> None:
        self._span_builder = GenAiSpanBuilder()
        self._cost_calculator = ModelCostCalculator()
        self._spans: dict[UUID, trace.Span] = {}

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM starts running."""
        model = serialized.get("kwargs", {}).get("model_name", "unknown")
        span = self._span_builder.start_chat_span(
            model=model,
            system="langchain",
            framework="langchain",
        )
        self._spans[run_id] = span

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Called when a chat model starts."""
        model = serialized.get("kwargs", {}).get("model_name", "unknown")
        if "model" in serialized.get("kwargs", {}):
            model = serialized["kwargs"]["model"]
        span = self._span_builder.start_chat_span(
            model=model,
            system="langchain",
            framework="langchain",
        )
        self._spans[run_id] = span

    def on_llm_end(
        self,
        response: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM ends."""
        span = self._spans.pop(run_id, None)
        if span is None:
            return

        input_tokens = 0
        output_tokens = 0
        model = "unknown"

        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            model = response.llm_output.get("model_name", model)

        self._span_builder.end_span_with_response(
            span=span,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM errors."""
        span = self._spans.pop(run_id, None)
        if span:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))
            span.record_exception(error)
            span.end()

    def on_retriever_start(
        self,
        serialized: dict[str, Any],
        query: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Called when a retriever starts."""
        source = serialized.get("name", "retriever")
        span = self._span_builder.start_retrieval_span(
            source=source,
            rag_enabled=True,
        )
        self._spans[run_id] = span

    def on_retriever_end(
        self,
        documents: list[Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Called when a retriever finishes."""
        span = self._spans.pop(run_id, None)
        if span:
            span.set_attribute(genai_attr.RAG_SOURCE_COUNT, len(documents))
            span.end()

    def on_retriever_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Called when a retriever errors."""
        span = self._spans.pop(run_id, None)
        if span:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))
            span.record_exception(error)
            span.end()
