"""AgentTel span processor for OpenTelemetry."""

from __future__ import annotations

from opentelemetry import context
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor

from agenttel import attributes as attr
from agenttel.anomaly.detector import AnomalyDetector
from agenttel.baseline.composite import CompositeBaselineProvider
from agenttel.baseline.rolling import RollingBaselineProvider
from agenttel.causality.tracker import CausalityTracker
from agenttel.config import AgentTelConfig, normalize_operation_name
from agenttel.enums import AlertLevel, EscalationLevel
from agenttel.error.classifier import ErrorClassifier
from agenttel.events import AgentTelEventEmitter
from agenttel.models import OperationBaseline, OperationContext
from agenttel.slo.tracker import SloTracker
from agenttel.topology.registry import TopologyRegistry


class AgentTelSpanProcessor(SpanProcessor):
    """Enriches spans with AgentTel attributes.

    On start: attaches baseline + decision attributes.
    On end: feeds rolling baselines, runs anomaly detection, checks SLO.
    """

    def __init__(
        self,
        config: AgentTelConfig,
        topology: TopologyRegistry,
        baseline_provider: CompositeBaselineProvider,
        rolling_provider: RollingBaselineProvider,
        anomaly_detector: AnomalyDetector,
        slo_tracker: SloTracker,
        error_classifier: ErrorClassifier,
        causality_tracker: CausalityTracker,
        event_emitter: AgentTelEventEmitter,
    ) -> None:
        self._config = config
        self._topology = topology
        self._baseline_provider = baseline_provider
        self._rolling_provider = rolling_provider
        self._anomaly_detector = anomaly_detector
        self._slo_tracker = slo_tracker
        self._error_classifier = error_classifier
        self._causality_tracker = causality_tracker
        self._event_emitter = event_emitter

    def on_start(self, span: Span, parent_context: context.Context | None = None) -> None:
        """Enrich span on start with topology, decision and baseline attributes."""
        if not self._config.enabled or not span.is_recording():
            return

        # Attach topology attributes
        for key, value in self._topology.get_topology_attributes().items():
            span.set_attribute(key, value)

        operation_name = self._resolve_operation_name(span)
        if operation_name:
            self.enrich_operation(span, operation_name)

    def enrich_operation(self, span: Span, operation_name: str) -> bool:
        """Set decision and baseline attributes for ``operation_name`` on ``span``.

        Framework integrations call this once the route template is known (HTTP
        server spans are usually named before routing, e.g. just "POST").
        Returns True if the operation is configured or has a baseline.
        """
        operation_name = normalize_operation_name(operation_name)
        found = False
        op_context = self.resolve_operation_context(operation_name)
        if op_context:
            self._set_operation_context(span, op_context)
            found = True
        baseline = self._baseline_provider.get_baseline(operation_name)
        if baseline:
            self._set_baseline_attributes(span, baseline)
            found = True
        return found

    def on_end(self, span: ReadableSpan) -> None:
        """Process span on end: update rolling baselines, detect anomalies, check SLO."""
        if not self._config.enabled:
            return

        operation_name = self._resolve_operation_name_from_readable(span)
        if not operation_name:
            return

        # Calculate latency
        latency_ms = self._calculate_latency_ms(span)
        is_error = span.status.is_ok is False if span.status else False

        # Feed rolling baseline
        self._rolling_provider.record(operation_name, latency_ms, is_error)

        # Anomaly detection
        if self._config.anomaly_detection.enabled:
            baseline = self._baseline_provider.get_baseline(operation_name)
            if baseline and baseline.latency_p50_ms > 0:
                snap = self._rolling_provider.get_window(operation_name)
                if snap and snap.size >= self._config.baselines.rolling_min_samples:
                    snapshot = snap.snapshot()
                    result = self._anomaly_detector.detect(
                        latency_ms, snapshot.mean, snapshot.stddev
                    )
                    if result.is_anomaly:
                        self._event_emitter.emit_anomaly_detected(
                            operation=operation_name,
                            score=result.score,
                            z_score=result.z_score,
                            pattern=result.pattern.value if result.pattern else None,
                        )

        # SLO tracking
        for slo_status in self._slo_tracker.get_all_statuses():
            self._slo_tracker.record_request(slo_status.name, is_error)
            status = self._slo_tracker.get_status(slo_status.name)
            if status and status.alert_level != AlertLevel.OK:
                self._event_emitter.emit_slo_budget_alert(
                    slo_name=status.name,
                    budget_remaining=status.budget_remaining,
                    alert_level=status.alert_level.value,
                )

    def shutdown(self) -> None:
        """Shutdown the processor."""
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any buffered data."""
        return True

    def _resolve_operation_name(self, span: Span) -> str | None:
        """Resolve operation name from span."""
        name = getattr(span, "name", None)
        return normalize_operation_name(name) if name else None

    def _resolve_operation_name_from_readable(self, span: ReadableSpan) -> str | None:
        """Resolve operation name from a readable span."""
        # Check for http.route first
        route = span.attributes.get("http.route") if span.attributes else None
        method = span.attributes.get("http.request.method") or span.attributes.get("http.method") if span.attributes else None
        if route and method:
            return normalize_operation_name(f"{method} {route}")
        return normalize_operation_name(span.name) if span.name else None

    def resolve_operation_context(self, operation_name: str) -> OperationContext | None:
        """Resolve decision context: explicit operation values > profile > defaults."""
        op_config = self._config.get_operation(operation_name)
        if op_config is None:
            return None

        profile = None
        if op_config.profile and op_config.profile in self._config.profiles:
            profile = self._config.profiles[op_config.profile]

        def pick(field: str, default: object) -> object:
            value = getattr(op_config, field)
            if value is not None:
                return value
            if profile is not None and getattr(profile, field) is not None:
                return getattr(profile, field)
            return default

        return OperationContext(
            retryable=pick("retryable", False),
            idempotent=pick("idempotent", False),
            runbook_url=pick("runbook_url", None),
            escalation_level=pick("escalation_level", EscalationLevel.AUTO_RESOLVE),
            safe_to_restart=pick("safe_to_restart", True),
            fallback_description=pick("fallback_description", None),
        )

    def _set_operation_context(self, span: Span, ctx: OperationContext) -> None:
        """Set operation context attributes on span."""
        span.set_attribute(attr.DECISION_RETRYABLE, ctx.retryable)
        span.set_attribute(attr.DECISION_IDEMPOTENT, ctx.idempotent)
        span.set_attribute(attr.DECISION_SAFE_TO_RESTART, ctx.safe_to_restart)
        span.set_attribute(attr.DECISION_FALLBACK_AVAILABLE, bool(ctx.fallback_description))
        if ctx.runbook_url:
            span.set_attribute(attr.DECISION_RUNBOOK_URL, ctx.runbook_url)
        if ctx.escalation_level:
            span.set_attribute(attr.DECISION_ESCALATION_LEVEL, ctx.escalation_level.value)
        if ctx.fallback_description:
            span.set_attribute(attr.DECISION_FALLBACK_DESCRIPTION, ctx.fallback_description)

    def _set_baseline_attributes(self, span: Span, baseline: OperationBaseline) -> None:
        """Set baseline attributes on span."""
        span.set_attribute(attr.BASELINE_LATENCY_P50_MS, baseline.latency_p50_ms)
        span.set_attribute(attr.BASELINE_LATENCY_P99_MS, baseline.latency_p99_ms)
        span.set_attribute(attr.BASELINE_ERROR_RATE, baseline.error_rate)
        span.set_attribute(attr.BASELINE_SOURCE, baseline.source.value)
        span.set_attribute(attr.BASELINE_CONFIDENCE, baseline.confidence.value)
        span.set_attribute(attr.BASELINE_SAMPLE_COUNT, baseline.sample_count)
        if baseline.latency_p95_ms > 0:
            span.set_attribute(attr.BASELINE_LATENCY_P95_MS, baseline.latency_p95_ms)

    def _calculate_latency_ms(self, span: ReadableSpan) -> float:
        """Calculate span latency in milliseconds."""
        if span.start_time and span.end_time:
            return (span.end_time - span.start_time) / 1_000_000
        return 0.0
