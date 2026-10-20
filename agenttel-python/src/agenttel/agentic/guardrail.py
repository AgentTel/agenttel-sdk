"""Guardrail recording for agentic workflows."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Any

from opentelemetry import trace

from agenttel import agentic_attributes as aa
from agenttel import extension_attributes as ext
from agenttel.enums import GuardrailAction


@dataclass
class GuardrailEvent:
    """Record of a guardrail trigger."""

    name: str
    action: GuardrailAction
    reason: str = ""
    input_violation: bool = False
    output_violation: bool = False
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class GuardrailRecorder:
    """Records and tracks guardrail triggers during agent execution."""

    def __init__(self) -> None:
        self._events: list[GuardrailEvent] = []
        self._lock = threading.Lock()

    def record(
        self,
        name: str,
        action: GuardrailAction,
        reason: str = "",
        input_violation: bool = False,
        output_violation: bool = False,
        span: trace.Span | None = None,
    ) -> GuardrailEvent:
        """Record a guardrail trigger.

        If a span is provided, sets guardrail attributes on it.
        """
        event = GuardrailEvent(
            name=name,
            action=action,
            reason=reason,
            input_violation=input_violation,
            output_violation=output_violation,
        )

        with self._lock:
            self._events.append(event)

        # Set span attributes if available
        if span and span.is_recording():
            span.set_attribute(aa.AGENTIC_GUARDRAIL_TRIGGERED, True)
            span.set_attribute(aa.AGENTIC_GUARDRAIL_NAME, name)
            span.set_attribute(aa.AGENTIC_GUARDRAIL_ACTION, action.value)
            if reason:
                span.set_attribute(aa.AGENTIC_GUARDRAIL_REASON, reason)
            span.set_attribute(ext.AGENTIC_GUARDRAIL_INPUT_VIOLATION, input_violation)
            span.set_attribute(ext.AGENTIC_GUARDRAIL_OUTPUT_VIOLATION, output_violation)

        return event

    def get_events(self) -> list[GuardrailEvent]:
        """Get all recorded guardrail events."""
        with self._lock:
            return list(self._events)

    def get_block_count(self) -> int:
        """Get count of block actions."""
        with self._lock:
            return sum(1 for e in self._events if e.action == GuardrailAction.BLOCK)

    def reset(self) -> None:
        """Clear all recorded events."""
        with self._lock:
            self._events.clear()
