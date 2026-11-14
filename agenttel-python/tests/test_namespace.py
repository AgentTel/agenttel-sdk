"""Tests for the agenttel.attributes.namespace setting (legacy | standard | both)."""

import logging

import pytest
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from agenttel import attributes as attr
from agenttel.config import AgentTelConfig
from agenttel.engine import AgentTelEngine
from agenttel.events import AgentTelEventEmitter
from agenttel.export import (
    AttributeNamespaceMapper,
    AttributeNamespaceMode,
    NamespaceMappingSpanExporter,
)
from agenttel.namespaces import STANDARD_ATTRIBUTE_KEYS, STANDARD_EVENT_NAMES

STD_RETRYABLE = "reliability.decision.retryable"
STD_TEAM = "reliability.topology.team"


def _export_one(mode, span_attrs, event=None):
    """Create one span with a 'payments' team resource and export it through the wrapper."""
    exporter = InMemorySpanExporter()
    mapper = AttributeNamespaceMapper(mode)
    provider = TracerProvider(
        resource=Resource({attr.TOPOLOGY_TEAM: "payments", "service.name": "svc"})
    )
    provider.add_span_processor(
        SimpleSpanProcessor(NamespaceMappingSpanExporter.wrap(exporter, mapper))
    )
    with provider.get_tracer("test").start_as_current_span("op") as span:
        span.set_attributes(span_attrs)
        if event:
            span.add_event(*event)
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    return spans[0]


class TestNamespaceMappingSpanExporter:
    def test_legacy_leaves_spans_unchanged(self):
        span = _export_one(AttributeNamespaceMode.LEGACY, {attr.DECISION_RETRYABLE: True})
        assert span.attributes[attr.DECISION_RETRYABLE] is True
        assert STD_RETRYABLE not in span.attributes
        assert STD_TEAM not in span.resource.attributes

    def test_standard_renames_mapped_keys_and_keeps_the_rest(self):
        span = _export_one(
            "standard",
            {
                attr.DECISION_RETRYABLE: True,
                attr.BASELINE_SAMPLE_COUNT: 42,
                attr.SEVERITY_ANOMALY_SCORE: 0.9,
                "http.route": "/pay",
            },
        )
        a = span.attributes
        assert a[STD_RETRYABLE] is True
        assert attr.DECISION_RETRYABLE not in a
        assert a["reliability.baseline.sample_count"] == 42
        assert a[attr.SEVERITY_ANOMALY_SCORE] == 0.9  # unmapped, passes through
        assert a["http.route"] == "/pay"
        assert span.resource.attributes[STD_TEAM] == "payments"
        assert attr.TOPOLOGY_TEAM not in span.resource.attributes
        assert span.resource.attributes["service.name"] == "svc"

    def test_both_keeps_legacy_and_adds_standard(self):
        span = _export_one("both", {attr.DECISION_RETRYABLE: False})
        assert span.attributes[attr.DECISION_RETRYABLE] is False
        assert span.attributes[STD_RETRYABLE] is False
        assert span.resource.attributes[attr.TOPOLOGY_TEAM] == "payments"
        assert span.resource.attributes[STD_TEAM] == "payments"

    def test_existing_otel_attribute_wins(self):
        span = _export_one(
            "standard",
            {
                "exception.type": "TimeoutError",
                attr.ERROR_ROOT_EXCEPTION: "ConnectionError",
            },
        )
        assert span.attributes["exception.type"] == "TimeoutError"
        assert attr.ERROR_ROOT_EXCEPTION not in span.attributes

    def test_span_events_are_mapped(self):
        span = _export_one(
            "standard",
            {},
            event=("agenttel.anomaly.detected", {"agenttel.anomaly.score": 0.97}),
        )
        assert len(span.events) == 1
        assert span.events[0].name == "reliability.anomaly.detected"
        assert span.events[0].attributes["reliability.anomaly.score"] == 0.97
        assert "agenttel.anomaly.score" not in span.events[0].attributes

    def test_both_keeps_event_name_but_maps_event_attributes(self):
        span = _export_one(
            "both",
            {},
            event=("agenttel.anomaly.detected", {"agenttel.anomaly.score": 0.97}),
        )
        event = span.events[0]
        assert event.name == "agenttel.anomaly.detected"
        assert event.attributes["agenttel.anomaly.score"] == 0.97
        assert event.attributes["reliability.anomaly.score"] == 0.97

    def test_unchanged_span_is_passed_through(self):
        mapper = AttributeNamespaceMapper("standard")
        exporter = NamespaceMappingSpanExporter(InMemorySpanExporter(), mapper)
        provider = TracerProvider(resource=Resource({"service.name": "svc"}))
        captured = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(captured))
        with provider.get_tracer("t").start_as_current_span("op") as s:
            s.set_attribute("http.route", "/x")
        original = captured.get_finished_spans()[0]
        assert exporter.map_span(original) is original

    def test_dropped_counts_are_kept(self):
        from opentelemetry.sdk.trace import SpanLimits

        exporter = InMemorySpanExporter()
        provider = TracerProvider(span_limits=SpanLimits(max_span_attributes=2, max_events=1))
        provider.add_span_processor(
            SimpleSpanProcessor(
                NamespaceMappingSpanExporter(exporter, AttributeNamespaceMapper("both"))
            )
        )
        with provider.get_tracer("t").start_as_current_span("op") as s:
            s.set_attribute(attr.DECISION_RETRYABLE, True)
            s.set_attribute(attr.DECISION_IDEMPOTENT, True)
            s.set_attribute("extra", 1)
            s.add_event("e1")
            s.add_event("agenttel.anomaly.detected", {"agenttel.anomaly.score": 1.0})
        span = exporter.get_finished_spans()[0]
        assert span.dropped_attributes == 1
        assert span.dropped_events == 1
        assert span.events[0].attributes["reliability.anomaly.score"] == 1.0
        # 'both' may exceed the original attribute limit: nothing new is dropped
        assert len(span.attributes) == 3

    def test_readable_span_has_private_fields_the_mapper_replaces(self):
        """map_span copies the span and replaces _attributes/_events/_resource. If an
        opentelemetry-sdk upgrade renames them, this fails instead of mapping silently
        doing nothing."""
        provider = TracerProvider()
        captured = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(captured))
        with provider.get_tracer("t").start_as_current_span("op") as s:
            s.set_attribute(attr.DECISION_RETRYABLE, True)
            s.add_event("agenttel.anomaly.detected")
        span = captured.get_finished_spans()[0]
        for field in ("_attributes", "_events", "_resource"):
            assert field in vars(span), f"ReadableSpan.{field} missing in this SDK"

        mapped = NamespaceMappingSpanExporter(
            InMemorySpanExporter(), AttributeNamespaceMapper("standard")
        ).map_span(span)
        assert mapped is not span
        assert mapped.attributes[STD_RETRYABLE] is True
        assert mapped.events[0].name == "reliability.anomaly.detected"
        assert span.attributes[attr.DECISION_RETRYABLE] is True  # original untouched

    def test_wrap_is_noop_in_legacy_mode_and_when_already_wrapped(self):
        delegate = InMemorySpanExporter()
        assert NamespaceMappingSpanExporter.wrap(delegate, AttributeNamespaceMapper()) is delegate
        wrapped = NamespaceMappingSpanExporter.wrap(delegate, AttributeNamespaceMapper("both"))
        assert isinstance(wrapped, NamespaceMappingSpanExporter)
        assert NamespaceMappingSpanExporter.wrap(wrapped, AttributeNamespaceMapper("both")) is wrapped


class TestAttributeNamespaceMapper:
    def test_mapping_is_idempotent(self):
        for mode in ("standard", "both"):
            mapper = AttributeNamespaceMapper(mode)
            once = mapper.map_attributes({attr.DECISION_RETRYABLE: True, attr.TOPOLOGY_TEAM: "p"})
            assert mapper.map_attributes(once) == once

    def test_returns_same_object_when_nothing_maps(self):
        attrs = {"http.route": "/x", attr.SEVERITY_ANOMALY_SCORE: 0.5}
        assert AttributeNamespaceMapper("standard").map_attributes(attrs) is attrs
        legacy = {attr.DECISION_RETRYABLE: True}
        assert AttributeNamespaceMapper("legacy").map_attributes(legacy) is legacy
        resource = Resource({"service.name": "svc"})
        assert AttributeNamespaceMapper("standard").map_resource(resource) is resource

    def test_types_are_preserved(self):
        mapped = AttributeNamespaceMapper("standard").map_attributes(
            {
                attr.BASELINE_LATENCY_P99_MS: 120.5,
                attr.DECISION_RETRY_AFTER_MS: 500,
                attr.DECISION_RETRYABLE: True,
                attr.TOPOLOGY_DEPENDENCIES: ("db", "cache"),
            }
        )
        assert mapped["reliability.baseline.latency_p99_ms"] == 120.5
        assert isinstance(mapped["reliability.decision.retry_after_ms"], int)
        assert mapped["reliability.decision.retryable"] is True
        assert mapped["reliability.topology.dependencies"] == ("db", "cache")

    def test_event_names_map_only_in_standard_mode(self):
        name = "agenttel.anomaly.detected"
        assert AttributeNamespaceMapper("standard").map_event_name(name) == "reliability.anomaly.detected"
        assert AttributeNamespaceMapper("both").map_event_name(name) == name
        assert AttributeNamespaceMapper("legacy").map_event_name(name) == name
        assert AttributeNamespaceMapper("standard").map_event_name("custom.event") == "custom.event"

    def test_generated_maps_cover_candidates(self):
        assert STANDARD_ATTRIBUTE_KEYS[attr.DECISION_RETRYABLE] == STD_RETRYABLE
        assert STANDARD_ATTRIBUTE_KEYS[attr.ERROR_ROOT_EXCEPTION] == "exception.type"
        assert attr.SEVERITY_ANOMALY_SCORE not in STANDARD_ATTRIBUTE_KEYS
        assert all(k.startswith("agenttel.") for k in STANDARD_ATTRIBUTE_KEYS)
        assert "agenttel.slo.budget_alert" in STANDARD_EVENT_NAMES


class TestModeParsing:
    def test_from_value(self):
        assert AttributeNamespaceMode.from_value(None) is AttributeNamespaceMode.LEGACY
        assert AttributeNamespaceMode.from_value("  ") is AttributeNamespaceMode.LEGACY
        assert AttributeNamespaceMode.from_value(" Standard ") is AttributeNamespaceMode.STANDARD
        assert AttributeNamespaceMode.from_value("BOTH") is AttributeNamespaceMode.BOTH
        with pytest.raises(ValueError, match="otel"):
            AttributeNamespaceMode.from_value("otel")

    def test_parse_warns_and_falls_back_to_legacy(self, caplog):
        with caplog.at_level(logging.WARNING, logger="agenttel.export"):
            assert AttributeNamespaceMode.parse("otel") is AttributeNamespaceMode.LEGACY
        assert "otel" in caplog.text


class TestConfig:
    def test_default_is_legacy(self):
        assert AgentTelConfig().attributes.namespace is AttributeNamespaceMode.LEGACY
        assert AgentTelConfig.from_dict({"agenttel": {}}).attributes.namespace == "legacy"

    def test_loads_attributes_namespace(self):
        config = AgentTelConfig.from_dict({"agenttel": {"attributes": {"namespace": "Standard"}}})
        assert config.attributes.namespace is AttributeNamespaceMode.STANDARD

    def test_loads_from_yaml(self, tmp_path):
        path = tmp_path / "agenttel.yml"
        path.write_text("agenttel:\n  attributes:\n    namespace: both\n")
        assert AgentTelConfig.from_yaml(path).attributes.namespace is AttributeNamespaceMode.BOTH

    def test_unknown_value_falls_back_to_legacy(self, caplog):
        with caplog.at_level(logging.WARNING, logger="agenttel.export"):
            config = AgentTelConfig.from_dict({"agenttel": {"attributes": {"namespace": "otel"}}})
        assert config.attributes.namespace is AttributeNamespaceMode.LEGACY
        assert "otel" in caplog.text


class TestEngineWiring:
    def _config(self, mode):
        return AgentTelConfig.from_dict(
            {
                "agenttel": {
                    "topology": {"team": "payments", "repo-url": "https://git.example/p"},
                    "attributes": {"namespace": mode},
                    "deployment": {"emit-on-startup": False},
                }
            }
        )

    def test_wrapped_exporter_maps_spans_and_resource(self):
        exporter = InMemorySpanExporter()
        engine = AgentTelEngine(self._config("standard"))
        provider = TracerProvider(resource=Resource({"service.name": "svc"}))
        engine.install(provider)
        provider.add_span_processor(BatchSpanProcessor(engine.wrap_exporter(exporter)))

        with provider.get_tracer("t").start_as_current_span("op"):
            pass
        provider.force_flush()

        span = exporter.get_finished_spans()[0]
        assert span.attributes[STD_TEAM] == "payments"
        assert attr.TOPOLOGY_TEAM not in span.attributes
        assert span.resource.attributes["vcs.repository.url.full"] == "https://git.example/p"
        assert attr.TOPOLOGY_REPO_URL not in span.resource.attributes
        provider.shutdown()

    def test_install_does_not_touch_registered_exporters(self):
        exporter = InMemorySpanExporter()
        processor = SimpleSpanProcessor(exporter)
        provider = TracerProvider()
        provider.add_span_processor(processor)
        add_span_processor = provider.add_span_processor
        AgentTelEngine(self._config("standard")).install(provider)
        assert processor.span_exporter is exporter
        assert "add_span_processor" not in vars(provider)
        assert provider.add_span_processor == add_span_processor

        # Unwrapped exporters keep legacy span attributes; the resource is mapped at source.
        with provider.get_tracer("t").start_as_current_span("op"):
            pass
        span = exporter.get_finished_spans()[0]
        assert span.attributes[attr.TOPOLOGY_TEAM] == "payments"
        assert STD_TEAM not in span.attributes
        provider.shutdown()

    def test_resource_attributes_mapped_at_source(self):
        engine = AgentTelEngine(self._config("both"))
        attrs = engine.topology.get_resource_attributes()
        assert attrs[attr.TOPOLOGY_TEAM] == "payments"
        assert attrs[STD_TEAM] == "payments"
        # span-level topology stays legacy; it is mapped at export time
        assert STD_TEAM not in engine.topology.get_topology_attributes()

    def test_wrap_exporter(self):
        delegate = InMemorySpanExporter()
        assert AgentTelEngine(self._config("legacy")).wrap_exporter(delegate) is delegate
        wrapped = AgentTelEngine(self._config("both")).wrap_exporter(delegate)
        assert isinstance(wrapped, NamespaceMappingSpanExporter)


class TestEventEmitter:
    def _emit(self, mode, caplog):
        emitter = AgentTelEventEmitter(namespace_mapper=AttributeNamespaceMapper(mode))
        with caplog.at_level(logging.INFO, logger="agenttel.events"):
            emitter.emit("agenttel.slo.budget_alert", {"agenttel.slo.name": "availability"})
        return caplog.text

    def test_standard_renames_event_and_attributes(self, caplog):
        text = self._emit("standard", caplog)
        assert "[reliability.slo.budget_alert]" in text
        assert "'reliability.slo.name': 'availability'" in text
        assert "'agenttel.slo.name'" not in text

    def test_both_keeps_event_name(self, caplog):
        text = self._emit("both", caplog)
        assert "[agenttel.slo.budget_alert]" in text
        assert "'event.name': 'agenttel.slo.budget_alert'" in text
        assert "'reliability.slo.name': 'availability'" in text

    def test_legacy_default(self, caplog):
        emitter = AgentTelEventEmitter()
        with caplog.at_level(logging.INFO, logger="agenttel.events"):
            emitter.emit("agenttel.slo.budget_alert", {"agenttel.slo.name": "a"})
        assert "'event.name': 'agenttel.slo.budget_alert'" in caplog.text
        assert "reliability." not in caplog.text
