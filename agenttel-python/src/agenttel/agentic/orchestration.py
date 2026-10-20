"""Orchestration pattern implementations."""

from __future__ import annotations

from typing import Any, Callable

from opentelemetry import trace

from agenttel import agentic_attributes as aa
from agenttel.enums import OrchestrationPattern


class SequentialOrchestration:
    """Orchestration where stages run in order."""

    def __init__(self, tracer: trace.Tracer, name: str = "") -> None:
        self._tracer = tracer
        self._name = name

    def run(self, stages: list[tuple[str, Callable[[], Any]]]) -> list[Any]:
        """Run stages sequentially."""
        span = self._tracer.start_span(
            f"orchestration.sequential {self._name}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_ORCHESTRATION_PATTERN, OrchestrationPattern.SEQUENTIAL.value)
        span.set_attribute(aa.AGENTIC_ORCHESTRATION_TOTAL_STAGES, len(stages))

        results = []
        try:
            with trace.use_span(span, end_on_exit=False):
                for i, (stage_name, handler) in enumerate(stages):
                    stage_span = self._tracer.start_span(
                        f"stage {stage_name}",
                        kind=trace.SpanKind.INTERNAL,
                    )
                    stage_span.set_attribute(aa.AGENTIC_ORCHESTRATION_STAGE, stage_name)
                    try:
                        with trace.use_span(stage_span, end_on_exit=False):
                            result = handler()
                            results.append(result)
                    except Exception as exc:
                        stage_span.set_status(
                            trace.Status(trace.StatusCode.ERROR, str(exc))
                        )
                        stage_span.record_exception(exc)
                        raise
                    finally:
                        stage_span.end()
        except Exception as exc:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise
        finally:
            span.end()

        return results


class ParallelOrchestration:
    """Orchestration where branches run concurrently."""

    def __init__(self, tracer: trace.Tracer, name: str = "") -> None:
        self._tracer = tracer
        self._name = name

    def run(self, branches: list[tuple[str, Callable[[], Any]]]) -> list[Any]:
        """Run branches in parallel using threads."""
        import concurrent.futures

        span = self._tracer.start_span(
            f"orchestration.parallel {self._name}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_ORCHESTRATION_PATTERN, OrchestrationPattern.PARALLEL.value)
        span.set_attribute(aa.AGENTIC_ORCHESTRATION_PARALLEL_BRANCHES, len(branches))

        results: list[Any] = [None] * len(branches)
        try:
            with trace.use_span(span, end_on_exit=False):
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = {}
                    for i, (branch_name, handler) in enumerate(branches):
                        future = executor.submit(handler)
                        futures[future] = (i, branch_name)

                    for future in concurrent.futures.as_completed(futures):
                        idx, name = futures[future]
                        results[idx] = future.result()
        except Exception as exc:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise
        finally:
            span.end()

        return results


class EvalLoopOrchestration:
    """Evaluator-optimizer loop with max iterations."""

    def __init__(
        self,
        tracer: trace.Tracer,
        max_iterations: int = 5,
        name: str = "",
    ) -> None:
        self._tracer = tracer
        self._max_iterations = max_iterations
        self._name = name

    def run(
        self,
        generator: Callable[[], Any],
        evaluator: Callable[[Any], tuple[float, str]],
        threshold: float = 0.8,
    ) -> tuple[Any, float, int]:
        """Run the eval loop until threshold is met or max iterations reached.

        Args:
            generator: Callable that produces output.
            evaluator: Callable that scores output -> (score, feedback).
            threshold: Score threshold to accept.

        Returns:
            (best_output, best_score, iterations)
        """
        span = self._tracer.start_span(
            f"orchestration.eval_loop {self._name}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_ORCHESTRATION_PATTERN, OrchestrationPattern.EVALUATOR_OPTIMIZER.value)

        best_output = None
        best_score = 0.0

        try:
            with trace.use_span(span, end_on_exit=False):
                for i in range(self._max_iterations):
                    output = generator()
                    score, feedback = evaluator(output)

                    if score > best_score:
                        best_score = score
                        best_output = output

                    if score >= threshold:
                        span.set_attribute(aa.AGENTIC_STEP_ITERATION, i + 1)
                        return best_output, best_score, i + 1

                span.set_attribute(aa.AGENTIC_STEP_ITERATION, self._max_iterations)
        except Exception as exc:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise
        finally:
            span.end()

        return best_output, best_score, self._max_iterations
