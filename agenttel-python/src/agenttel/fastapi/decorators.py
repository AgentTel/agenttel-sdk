"""Decorators for AgentTel operation instrumentation."""

from __future__ import annotations

import functools
from typing import Any, Callable

from opentelemetry import trace

from agenttel import attributes as attr


def agent_operation(
    expected_latency_p50: str | None = None,
    expected_latency_p99: str | None = None,
    expected_error_rate: float | None = None,
    retryable: bool = False,
    idempotent: bool = False,
    runbook_url: str | None = None,
    escalation_level: str | None = None,
    safe_to_restart: bool = True,
    profile: str | None = None,
) -> Callable:
    """Decorator that sets operation context and static baselines on the current span.

    Usage:
        @agent_operation(
            expected_latency_p50="100ms",
            expected_latency_p99="500ms",
            retryable=True,
            runbook_url="https://..."
        )
        async def create_transfer(request: TransferRequest):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            span = trace.get_current_span()
            if span and span.is_recording():
                _set_attributes(span)
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            span = trace.get_current_span()
            if span and span.is_recording():
                _set_attributes(span)
            return func(*args, **kwargs)

        def _set_attributes(span: Any) -> None:
            span.set_attribute(attr.DECISION_RETRYABLE, retryable)
            span.set_attribute(attr.DECISION_IDEMPOTENT, idempotent)
            span.set_attribute(attr.DECISION_SAFE_TO_RESTART, safe_to_restart)
            if runbook_url:
                span.set_attribute(attr.DECISION_RUNBOOK_URL, runbook_url)
            if escalation_level:
                span.set_attribute(attr.DECISION_ESCALATION_LEVEL, escalation_level)
            if profile:
                span.set_attribute(attr.OPERATION_PROFILE, profile)

            # Set baseline from decorator parameters
            p50 = _parse_latency(expected_latency_p50)
            p99 = _parse_latency(expected_latency_p99)
            if p50 is not None:
                span.set_attribute(attr.BASELINE_LATENCY_P50_MS, p50)
            if p99 is not None:
                span.set_attribute(attr.BASELINE_LATENCY_P99_MS, p99)
            if expected_error_rate is not None:
                span.set_attribute(attr.BASELINE_ERROR_RATE, expected_error_rate)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _parse_latency(value: str | None) -> float | None:
    """Parse latency string like '100ms' to float milliseconds."""
    if value is None:
        return None
    v = value.strip().lower()
    if v.endswith("ms"):
        return float(v[:-2])
    if v.endswith("s"):
        return float(v[:-1]) * 1000
    return float(v)
