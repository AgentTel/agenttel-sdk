"""AgentTel engine — high-level orchestrator combining all components."""

from __future__ import annotations

from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from agenttel.anomaly.detector import AnomalyDetector
from agenttel.baseline.composite import CompositeBaselineProvider
from agenttel.baseline.provider import StaticBaselineProvider
from agenttel.baseline.rolling import RollingBaselineProvider
from agenttel.causality.tracker import CausalityTracker
from agenttel.config import AgentTelConfig
from agenttel.enums import BaselineSource
from agenttel.error.classifier import ErrorClassifier
from agenttel.events import AgentTelEventEmitter
from agenttel.models import OperationBaseline, SloDefinition
from agenttel.processor import AgentTelSpanProcessor
from agenttel.slo.tracker import SloTracker
from agenttel.topology.registry import TopologyRegistry


class AgentTelEngine:
    """High-level API that wires all AgentTel components together."""

    def __init__(self, config: AgentTelConfig) -> None:
        self._config = config

        # Initialize components
        self._topology = TopologyRegistry(config)
        self._static_baselines = StaticBaselineProvider()
        self._rolling_baselines = RollingBaselineProvider(
            window_size=config.baselines.rolling_window_size,
            min_samples=config.baselines.rolling_min_samples,
        )
        self._baseline_provider = CompositeBaselineProvider(
            [self._rolling_baselines, self._static_baselines]
        )
        self._anomaly_detector = AnomalyDetector(
            z_score_threshold=config.anomaly_detection.z_score_threshold
        )
        self._slo_tracker = SloTracker()
        self._error_classifier = ErrorClassifier()
        self._causality_tracker = CausalityTracker()
        self._event_emitter = AgentTelEventEmitter()

        # Register dependencies in causality tracker
        for dep in config.dependencies:
            self._causality_tracker.register_dependency(dep.name, dep.criticality)

        # Register static baselines from config
        self._register_static_baselines()

        # Register SLOs from config
        self._register_slos()

        # Create span processor
        self._processor = AgentTelSpanProcessor(
            config=config,
            topology=self._topology,
            baseline_provider=self._baseline_provider,
            rolling_provider=self._rolling_baselines,
            anomaly_detector=self._anomaly_detector,
            slo_tracker=self._slo_tracker,
            error_classifier=self._error_classifier,
            causality_tracker=self._causality_tracker,
            event_emitter=self._event_emitter,
        )

    @classmethod
    def from_config(cls, config_path: str | Path = "agenttel.yml") -> AgentTelEngine:
        """Create engine from a YAML config file."""
        config = AgentTelConfig.from_yaml(config_path)
        return cls(config)

    @property
    def config(self) -> AgentTelConfig:
        return self._config

    @property
    def processor(self) -> AgentTelSpanProcessor:
        return self._processor

    @property
    def topology(self) -> TopologyRegistry:
        return self._topology

    @property
    def baseline_provider(self) -> CompositeBaselineProvider:
        return self._baseline_provider

    @property
    def rolling_baselines(self) -> RollingBaselineProvider:
        return self._rolling_baselines

    @property
    def anomaly_detector(self) -> AnomalyDetector:
        return self._anomaly_detector

    @property
    def slo_tracker(self) -> SloTracker:
        return self._slo_tracker

    @property
    def error_classifier(self) -> ErrorClassifier:
        return self._error_classifier

    @property
    def causality_tracker(self) -> CausalityTracker:
        return self._causality_tracker

    @property
    def event_emitter(self) -> AgentTelEventEmitter:
        return self._event_emitter

    def install(self, tracer_provider: TracerProvider | None = None) -> TracerProvider:
        """Install the AgentTel span processor into the OTel SDK.

        Uses ``tracer_provider`` if given, otherwise the globally registered SDK
        ``TracerProvider`` if the application already set one. Only when no SDK
        provider exists is a new one created (with topology on its resource) and
        registered globally. Installing twice is a no-op.
        """
        if tracer_provider is None:
            current = trace.get_tracer_provider()
            if isinstance(current, TracerProvider):
                tracer_provider = current
            else:
                attrs: dict[str, str] = dict(self._topology.get_topology_attributes())
                if self._config.topology.service_name:
                    attrs.setdefault("service.name", self._config.topology.service_name)
                tracer_provider = TracerProvider(resource=Resource.create(attrs))
                trace.set_tracer_provider(tracer_provider)

        if getattr(tracer_provider, "_agenttel_installed", None) is self:
            return tracer_provider
        self._merge_topology_into_resource(tracer_provider)
        tracer_provider.add_span_processor(self._processor)
        tracer_provider._agenttel_installed = self  # type: ignore[attr-defined]

        # Emit deployment event if configured
        if self._config.deployment.emit_on_startup:
            self._event_emitter.emit_deployment(
                version=self._config.deployment.version,
                environment=self._config.deployment.environment,
                deployment_id=self._config.deployment.deployment_id,
            )
        return tracer_provider

    def _merge_topology_into_resource(self, provider: TracerProvider) -> None:
        """Best effort: add topology to an existing provider's resource.

        Tracers created after this call carry the merged resource. Span-level
        topology attributes are always set by the processor regardless.
        """
        resource = getattr(provider, "_resource", None)
        if not isinstance(resource, Resource):
            return
        missing = {
            k: v
            for k, v in self._topology.get_topology_attributes().items()
            if k not in resource.attributes
        }
        if not missing:
            return
        update = getattr(provider, "_update_resource", None)
        if callable(update):  # opentelemetry-sdk >= 1.39 also updates existing tracers
            update(Resource(missing))
        else:
            provider._resource = resource.merge(Resource(missing))  # type: ignore[attr-defined]

    def _register_static_baselines(self) -> None:
        """Register static baselines from operation configs."""
        for op_name, op_config in self._config.operations.items():
            p50 = op_config.latency_p50_ms
            p99 = op_config.latency_p99_ms
            if p50 is not None or p99 is not None or op_config.expected_error_rate is not None:
                baseline = OperationBaseline(
                    operation_name=op_name,
                    latency_p50_ms=p50 or 0.0,
                    latency_p99_ms=p99 or 0.0,
                    error_rate=op_config.expected_error_rate or 0.0,
                    source=BaselineSource.STATIC,
                )
                self._static_baselines.register(baseline)

    def _register_slos(self) -> None:
        """Register SLO definitions from config."""
        for slo_name, slo_config in self._config.slo.items():
            self._slo_tracker.register(
                SloDefinition(
                    name=slo_config.name or slo_name,
                    target=slo_config.target,
                    type=slo_config.type,
                )
            )
