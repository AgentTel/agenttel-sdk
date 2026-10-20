"""Scope context managers for agentic observability."""

from __future__ import annotations

import time
import uuid
from typing import Any

from opentelemetry import trace

from agenttel import agentic_attributes as aa
from agenttel import extension_attributes as ext
from agenttel.enums import (
    HumanCheckpointType,
    InvocationStatus,
    StepType,
)


class AgentInvocation:
    """Top-level invocation span context manager.

    Usage:
        with tracer.invoke("diagnose high latency") as invocation:
            with invocation.step(StepType.THOUGHT, "analyzing"):
                ...
            with invocation.tool_call("get_health") as tool:
                result = call_tool()
                tool.set_result(result)
            invocation.complete(goal_achieved=True)
    """

    def __init__(
        self,
        span: trace.Span,
        tracer: trace.Tracer,
        invocation_id: str,
        goal: str,
        agent_name: str = "",
        cost_aggregator: Any = None,
    ) -> None:
        self._span = span
        self._tracer = tracer
        self._invocation_id = invocation_id
        self._goal = goal
        self._agent_name = agent_name
        self._cost_aggregator = cost_aggregator
        self._step_count = 0
        self._status = InvocationStatus.RUNNING
        self._ctx_token = None

    def __enter__(self) -> AgentInvocation:
        self._ctx_token = trace.use_span(self._span, end_on_exit=False)
        self._ctx_token.__enter__()
        self._span.set_attribute(aa.AGENTIC_INVOCATION_STATUS, InvocationStatus.RUNNING.value)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._span.set_attribute(aa.AGENTIC_INVOCATION_STEPS, self._step_count)

        if exc_type is not None:
            self._span.set_attribute(aa.AGENTIC_INVOCATION_STATUS, InvocationStatus.FAILED.value)
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            self._span.record_exception(exc_val)
        elif self._status == InvocationStatus.RUNNING:
            self._span.set_attribute(aa.AGENTIC_INVOCATION_STATUS, InvocationStatus.COMPLETED.value)

        # Set cost attributes if available
        if self._cost_aggregator:
            summary = self._cost_aggregator.summary()
            self._span.set_attribute(aa.AGENTIC_COST_TOTAL_USD, summary.get("total_cost_usd", 0))
            self._span.set_attribute(aa.AGENTIC_COST_INPUT_TOKENS, summary.get("total_input_tokens", 0))
            self._span.set_attribute(aa.AGENTIC_COST_OUTPUT_TOKENS, summary.get("total_output_tokens", 0))
            self._span.set_attribute(aa.AGENTIC_COST_LLM_CALLS, summary.get("llm_calls", 0))

        self._span.end()
        if self._ctx_token:
            self._ctx_token.__exit__(None, None, None)
            self._ctx_token = None

    def step(self, step_type: StepType, description: str = "") -> StepScope:
        """Create a step within this invocation."""
        self._step_count += 1
        span = self._tracer.start_span(
            f"agent.step.{step_type.value}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_STEP_NUMBER, self._step_count)
        span.set_attribute(aa.AGENTIC_STEP_TYPE, step_type.value)
        if description:
            span.set_attribute(ext.AGENTIC_STEP_DESCRIPTION, description)
        span.set_attribute(aa.AGENTIC_INVOCATION_ID, self._invocation_id)
        return StepScope(span=span)

    def tool_call(self, tool_name: str) -> ToolCallScope:
        """Create a tool call within this invocation."""
        self._step_count += 1
        span = self._tracer.start_span(
            f"agent.tool_call {tool_name}",
            kind=trace.SpanKind.CLIENT,
        )
        span.set_attribute(aa.AGENTIC_STEP_TOOL_NAME, tool_name)
        span.set_attribute(aa.AGENTIC_STEP_TYPE, StepType.ACTION.value)
        span.set_attribute(aa.AGENTIC_STEP_NUMBER, self._step_count)
        span.set_attribute(aa.AGENTIC_INVOCATION_ID, self._invocation_id)
        return ToolCallScope(span=span, tool_name=tool_name)

    def task(self, name: str, parent_id: str | None = None, depth: int = 0) -> TaskScope:
        """Create a task within this invocation."""
        task_id = str(uuid.uuid4())
        span = self._tracer.start_span(
            f"agent.task {name}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_TASK_ID, task_id)
        span.set_attribute(aa.AGENTIC_TASK_NAME, name)
        span.set_attribute(aa.AGENTIC_INVOCATION_ID, self._invocation_id)
        if parent_id:
            span.set_attribute(aa.AGENTIC_TASK_PARENT_ID, parent_id)
        span.set_attribute(aa.AGENTIC_TASK_DEPTH, depth)
        return TaskScope(
            span=span,
            tracer=self._tracer,
            task_id=task_id,
            invocation_id=self._invocation_id,
        )

    def handoff(self, to_agent: str, reason: str = "") -> HandoffScope:
        """Create a handoff to another agent."""
        span = self._tracer.start_span(
            f"agent.handoff {self._agent_name} -> {to_agent}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_HANDOFF_FROM_AGENT, self._agent_name)
        span.set_attribute(aa.AGENTIC_HANDOFF_TO_AGENT, to_agent)
        if reason:
            span.set_attribute(aa.AGENTIC_HANDOFF_REASON, reason)
        return HandoffScope(span=span)

    def human_checkpoint(
        self, checkpoint_type: HumanCheckpointType
    ) -> HumanCheckpointScope:
        """Create a human-in-the-loop checkpoint."""
        span = self._tracer.start_span(
            f"agent.human.{checkpoint_type.value}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_HUMAN_CHECKPOINT_TYPE, checkpoint_type.value)
        return HumanCheckpointScope(span=span)

    def code_execution(
        self, language: str, sandboxed: bool = True
    ) -> CodeExecutionScope:
        """Create a code execution scope."""
        span = self._tracer.start_span(
            f"agent.code.{language}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_CODE_LANGUAGE, language)
        span.set_attribute(aa.AGENTIC_CODE_SANDBOXED, sandboxed)
        return CodeExecutionScope(span=span)

    def evaluation(self, scorer_name: str, criteria: str = "") -> EvaluationScope:
        """Create an evaluation scope."""
        span = self._tracer.start_span(
            f"agent.eval {scorer_name}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_EVAL_SCORER_NAME, scorer_name)
        if criteria:
            span.set_attribute(aa.AGENTIC_EVAL_CRITERIA, criteria)
        return EvaluationScope(span=span)

    def retriever(self, query: str, store_type: str = "") -> RetrieverScope:
        """Create a retrieval scope."""
        span = self._tracer.start_span(
            "agent.retrieval",
            kind=trace.SpanKind.CLIENT,
        )
        span.set_attribute(aa.AGENTIC_RETRIEVAL_QUERY, query)
        if store_type:
            span.set_attribute(aa.AGENTIC_RETRIEVAL_STORE_TYPE, store_type)
        return RetrieverScope(span=span)

    def complete(self, goal_achieved: bool = True, confidence: float | None = None) -> None:
        """Mark the invocation as completed."""
        self._status = InvocationStatus.COMPLETED
        self._span.set_attribute(aa.AGENTIC_INVOCATION_STATUS, InvocationStatus.COMPLETED.value)
        self._span.set_attribute(aa.AGENTIC_QUALITY_GOAL_ACHIEVED, goal_achieved)
        if confidence is not None:
            self._span.set_attribute(ext.AGENTIC_QUALITY_CONFIDENCE, confidence)

    def fail(self, error_source: str = "agent", error_message: str = "") -> None:
        """Mark the invocation as failed."""
        self._status = InvocationStatus.FAILED
        self._span.set_attribute(aa.AGENTIC_INVOCATION_STATUS, InvocationStatus.FAILED.value)
        self._span.set_attribute(aa.AGENTIC_ERROR_SOURCE, error_source)
        self._span.set_status(trace.Status(trace.StatusCode.ERROR, error_message or None))


class StepScope:
    """Reasoning step context manager."""

    def __init__(self, span: trace.Span) -> None:
        self._span = span

    def __enter__(self) -> StepScope:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            self._span.record_exception(exc_val)
        self._span.end()


class ToolCallScope:
    """Tool invocation context manager."""

    def __init__(self, span: trace.Span, tool_name: str) -> None:
        self._span = span
        self._tool_name = tool_name

    def __enter__(self) -> ToolCallScope:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self._span.set_attribute(aa.AGENTIC_STEP_TOOL_STATUS, "error")
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            self._span.record_exception(exc_val)
        else:
            self._span.set_attribute(aa.AGENTIC_STEP_TOOL_STATUS, "success")
        self._span.end()

    def set_input(self, input_data: str) -> None:
        self._span.set_attribute(ext.AGENTIC_STEP_TOOL_INPUT, input_data)

    def set_result(self, result: Any) -> None:
        self._span.set_attribute(ext.AGENTIC_STEP_TOOL_OUTPUT, str(result)[:4096])
        self._span.set_attribute(aa.AGENTIC_STEP_TOOL_STATUS, "success")


class TaskScope:
    """Task decomposition context manager."""

    def __init__(
        self,
        span: trace.Span,
        tracer: trace.Tracer,
        task_id: str,
        invocation_id: str,
    ) -> None:
        self._span = span
        self._tracer = tracer
        self._task_id = task_id
        self._invocation_id = invocation_id
        self._step_count = 0

    def __enter__(self) -> TaskScope:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self._span.set_attribute(aa.AGENTIC_TASK_STATUS, "failed")
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            self._span.record_exception(exc_val)
        else:
            self._span.set_attribute(aa.AGENTIC_TASK_STATUS, "completed")
        self._span.end()

    def step(self, step_type: StepType, description: str = "") -> StepScope:
        self._step_count += 1
        span = self._tracer.start_span(
            f"agent.step.{step_type.value}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_STEP_NUMBER, self._step_count)
        span.set_attribute(aa.AGENTIC_STEP_TYPE, step_type.value)
        if description:
            span.set_attribute(ext.AGENTIC_STEP_DESCRIPTION, description)
        span.set_attribute(aa.AGENTIC_TASK_ID, self._task_id)
        return StepScope(span=span)

    @property
    def task_id(self) -> str:
        return self._task_id


class HandoffScope:
    """Agent-to-agent handoff context manager."""

    def __init__(self, span: trace.Span) -> None:
        self._span = span

    def __enter__(self) -> HandoffScope:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            self._span.record_exception(exc_val)
        self._span.end()

    def set_chain_depth(self, depth: int) -> None:
        self._span.set_attribute(aa.AGENTIC_HANDOFF_CHAIN_DEPTH, depth)

    def set_context_keys(self, keys: list[str]) -> None:
        self._span.set_attribute(ext.AGENTIC_HANDOFF_CONTEXT_KEYS, keys)


class HumanCheckpointScope:
    """Human-in-the-loop checkpoint context manager."""

    def __init__(self, span: trace.Span) -> None:
        self._span = span
        self._start_time = time.time()

    def __enter__(self) -> HumanCheckpointScope:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        wait_ms = (time.time() - self._start_time) * 1000
        self._span.set_attribute(aa.AGENTIC_HUMAN_WAIT_MS, wait_ms)
        if exc_type:
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
        self._span.end()

    def set_decision(self, decision: str) -> None:
        self._span.set_attribute(aa.AGENTIC_HUMAN_DECISION, decision)

    def set_feedback(self, feedback: str) -> None:
        self._span.set_attribute(ext.AGENTIC_HUMAN_FEEDBACK, feedback)


class CodeExecutionScope:
    """Code interpreter execution context manager."""

    def __init__(self, span: trace.Span) -> None:
        self._span = span

    def __enter__(self) -> CodeExecutionScope:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self._span.set_attribute(aa.AGENTIC_CODE_STATUS, "error")
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
        self._span.end()

    def set_result(self, exit_code: int, output_size: int = 0) -> None:
        self._span.set_attribute(aa.AGENTIC_CODE_EXIT_CODE, exit_code)
        self._span.set_attribute(aa.AGENTIC_CODE_STATUS, "success" if exit_code == 0 else "error")
        if output_size:
            self._span.set_attribute(ext.AGENTIC_CODE_OUTPUT_SIZE, output_size)


class EvaluationScope:
    """Evaluation/scoring context manager."""

    def __init__(self, span: trace.Span) -> None:
        self._span = span

    def __enter__(self) -> EvaluationScope:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
        self._span.end()

    def set_score(self, score: float, max_score: float = 1.0) -> None:
        self._span.set_attribute(aa.AGENTIC_EVAL_SCORE, score)
        self._span.set_attribute(ext.AGENTIC_EVAL_MAX_SCORE, max_score)

    def set_feedback(self, feedback: str) -> None:
        self._span.set_attribute(aa.AGENTIC_EVAL_FEEDBACK, feedback)

    def set_type(self, eval_type: str) -> None:
        self._span.set_attribute(aa.AGENTIC_EVAL_TYPE, eval_type)


class RetrieverScope:
    """RAG retrieval context manager."""

    def __init__(self, span: trace.Span) -> None:
        self._span = span

    def __enter__(self) -> RetrieverScope:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
        self._span.end()

    def set_results(self, document_count: int, relevance_score: float = 0.0) -> None:
        self._span.set_attribute(aa.AGENTIC_RETRIEVAL_DOCUMENT_COUNT, document_count)
        if relevance_score > 0:
            self._span.set_attribute(aa.AGENTIC_RETRIEVAL_RELEVANCE_SCORE_AVG, relevance_score)


class RerankerScope:
    """Reranking context manager."""

    def __init__(self, span: trace.Span) -> None:
        self._span = span

    def __enter__(self) -> RerankerScope:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
        self._span.end()

    def set_results(self, input_count: int, output_count: int) -> None:
        self._span.set_attribute(aa.AGENTIC_RERANKER_INPUT_DOCUMENTS, input_count)
        self._span.set_attribute(aa.AGENTIC_RERANKER_OUTPUT_DOCUMENTS, output_count)


class Orchestration:
    """Orchestration context manager."""

    def __init__(
        self,
        span: trace.Span,
        tracer: trace.Tracer,
        pattern: Any,
    ) -> None:
        self._span = span
        self._tracer = tracer
        self._pattern = pattern
        self._stage_count = 0

    def __enter__(self) -> Orchestration:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._span.set_attribute(aa.AGENTIC_ORCHESTRATION_TOTAL_STAGES, self._stage_count)
        if exc_type:
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
            self._span.record_exception(exc_val)
        self._span.end()

    def stage(self, name: str) -> StepScope:
        """Create a stage within this orchestration."""
        self._stage_count += 1
        span = self._tracer.start_span(
            f"agent.stage {name}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_ORCHESTRATION_STAGE, name)
        span.set_attribute(aa.AGENTIC_ORCHESTRATION_PATTERN, self._pattern.value)
        return StepScope(span=span)

    def set_coordinator_id(self, coordinator_id: str) -> None:
        self._span.set_attribute(aa.AGENTIC_ORCHESTRATION_COORDINATOR_ID, coordinator_id)

    def set_parallel_branches(self, count: int) -> None:
        self._span.set_attribute(aa.AGENTIC_ORCHESTRATION_PARALLEL_BRANCHES, count)
