"""AgentTel event emitter for structured OTel log events."""

from __future__ import annotations

import logging
import time
from typing import Any

from opentelemetry import trace

from agenttel.export.namespace import AttributeNamespaceMapper

logger = logging.getLogger("agenttel.events")


class AgentTelEventEmitter:
    """Emits structured events as OTel log records."""

    def __init__(
        self,
        service_name: str = "",
        namespace_mapper: AttributeNamespaceMapper | None = None,
    ) -> None:
        self._service_name = service_name
        self._mapper = namespace_mapper or AttributeNamespaceMapper()
        self._logger = logging.getLogger(f"agenttel.events.{service_name}")

    def emit(
        self,
        event_name: str,
        attributes: dict[str, Any] | None = None,
        severity: str = "INFO",
    ) -> None:
        """Emit a structured event.

        The event name and attributes follow ``agenttel.attributes.namespace``.
        """
        event_name = self._mapper.map_event_name(event_name)
        attrs: dict[str, Any] = {
            "event.name": event_name,
            "event.domain": "agenttel",
            "service.name": self._service_name,
            "event.timestamp": time.time(),
        }
        if attributes:
            attrs.update(attributes)
        attrs = dict(self._mapper.map_attributes(attrs) or {})

        # Attach to current span if available
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event(event_name, attributes=attrs)

        # Also log
        log_level = getattr(logging, severity.upper(), logging.INFO)
        self._logger.log(log_level, "[%s] %s", event_name, attrs)

    def emit_anomaly_detected(
        self,
        operation: str,
        score: float,
        z_score: float,
        pattern: str | None = None,
    ) -> None:
        """Emit an anomaly detection event."""
        self.emit(
            "agenttel.anomaly.detected",
            {
                "operation": operation,
                "anomaly.score": score,
                "anomaly.z_score": z_score,
                "anomaly.pattern": pattern or "unknown",
            },
            severity="WARNING",
        )

    def emit_slo_budget_alert(
        self,
        slo_name: str,
        budget_remaining: float,
        alert_level: str,
    ) -> None:
        """Emit an SLO budget alert event."""
        self.emit(
            "agenttel.slo.budget_alert",
            {
                "slo.name": slo_name,
                "slo.budget_remaining": budget_remaining,
                "slo.alert_level": alert_level,
            },
            severity="WARNING" if alert_level == "warning" else "CRITICAL"
            if alert_level == "critical"
            else "INFO",
        )

    def emit_dependency_state_change(
        self,
        dependency: str,
        previous_state: str,
        new_state: str,
    ) -> None:
        """Emit a dependency state change event."""
        self.emit(
            "agenttel.dependency.state_change",
            {
                "dependency.name": dependency,
                "dependency.previous_state": previous_state,
                "dependency.new_state": new_state,
            },
            severity="WARNING" if new_state == "failing" else "INFO",
        )

    def emit_deployment(
        self,
        version: str | None = None,
        environment: str = "development",
        deployment_id: str | None = None,
    ) -> None:
        """Emit a deployment event."""
        attrs: dict[str, Any] = {"deployment.environment": environment}
        if version:
            attrs["deployment.version"] = version
        if deployment_id:
            attrs["deployment.id"] = deployment_id
        self.emit("agenttel.deployment.started", attrs)
