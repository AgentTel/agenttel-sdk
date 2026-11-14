package io.agenttel.core.export;

import io.agenttel.api.attributes.AgentTelAttributes;
import io.agenttel.api.attributes.AttributeNamespaces;
import io.agenttel.api.events.AgentTelEvents;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.testing.exporter.InMemorySpanExporter;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.data.SpanData;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class NamespaceMappingSpanExporterTest {

    private static final AttributeKey<Boolean> STD_RETRYABLE = AttributeKey.booleanKey("reliability.decision.retryable");
    private static final AttributeKey<String> STD_TEAM = AttributeKey.stringKey("reliability.topology.team");
    private static final AttributeKey<String> SERVICE_VERSION = AttributeKey.stringKey("service.version");
    private static final AttributeKey<String> EXCEPTION_TYPE = AttributeKey.stringKey("exception.type");

    private SpanData export(AttributeNamespaceMode mode, java.util.function.Consumer<Span> body) {
        InMemorySpanExporter memory = InMemorySpanExporter.create();
        SdkTracerProvider provider = SdkTracerProvider.builder()
                .setResource(Resource.create(Attributes.of(AgentTelAttributes.TOPOLOGY_TEAM, "payments")))
                .addSpanProcessor(SimpleSpanProcessor.create(
                        NamespaceMappingSpanExporter.wrap(memory, new AttributeNamespaceMapper(mode))))
                .build();
        Span span = provider.get("test").spanBuilder("POST /api/payments").startSpan();
        body.accept(span);
        span.end();
        // Read before close: shutting down the in-memory exporter clears it
        List<SpanData> spans = memory.getFinishedSpanItems();
        provider.close();
        assertThat(spans).hasSize(1);
        return spans.get(0);
    }

    @Test
    void legacyLeavesSpansUnchanged() {
        SpanData span = export(AttributeNamespaceMode.LEGACY,
                s -> s.setAttribute(AgentTelAttributes.DECISION_RETRYABLE, true));

        assertThat(span.getAttributes().get(AgentTelAttributes.DECISION_RETRYABLE)).isTrue();
        assertThat(span.getAttributes().get(STD_RETRYABLE)).isNull();
        assertThat(span.getResource().getAttribute(STD_TEAM)).isNull();
    }

    @Test
    void standardRenamesMappedKeysAndKeepsTheRest() {
        SpanData span = export(AttributeNamespaceMode.STANDARD, s -> {
            s.setAttribute(AgentTelAttributes.DECISION_RETRYABLE, true);
            s.setAttribute(AgentTelAttributes.BASELINE_SAMPLE_COUNT, 42L);
            s.setAttribute(AgentTelAttributes.SEVERITY_ANOMALY_SCORE, 0.9); // internal: not mapped
        });

        Attributes attrs = span.getAttributes();
        assertThat(attrs.get(STD_RETRYABLE)).isTrue();
        assertThat(attrs.get(AgentTelAttributes.DECISION_RETRYABLE)).isNull();
        assertThat(attrs.get(AttributeKey.longKey("reliability.baseline.sample_count"))).isEqualTo(42L);
        assertThat(attrs.get(AgentTelAttributes.SEVERITY_ANOMALY_SCORE)).isEqualTo(0.9);
        assertThat(span.getResource().getAttribute(STD_TEAM)).isEqualTo("payments");
        assertThat(span.getResource().getAttribute(AgentTelAttributes.TOPOLOGY_TEAM)).isNull();
    }

    @Test
    void bothKeepsLegacyAndAddsStandard() {
        SpanData span = export(AttributeNamespaceMode.BOTH,
                s -> s.setAttribute(AgentTelAttributes.DECISION_RETRYABLE, false));

        assertThat(span.getAttributes().get(AgentTelAttributes.DECISION_RETRYABLE)).isFalse();
        assertThat(span.getAttributes().get(STD_RETRYABLE)).isFalse();
        assertThat(span.getResource().getAttribute(AgentTelAttributes.TOPOLOGY_TEAM)).isEqualTo("payments");
        assertThat(span.getResource().getAttribute(STD_TEAM)).isEqualTo("payments");
    }

    @Test
    void existingOtelAttributeWins() {
        SpanData span = export(AttributeNamespaceMode.STANDARD, s -> {
            s.setAttribute(EXCEPTION_TYPE, "java.net.SocketTimeoutException");
            s.setAttribute(AgentTelAttributes.ERROR_ROOT_EXCEPTION, "TimeoutException");
        });

        assertThat(span.getAttributes().get(EXCEPTION_TYPE)).isEqualTo("java.net.SocketTimeoutException");
        assertThat(span.getAttributes().get(AgentTelAttributes.ERROR_ROOT_EXCEPTION)).isNull();
    }

    @Test
    void spanEventsAreMapped() {
        SpanData span = export(AttributeNamespaceMode.STANDARD, s -> s.addEvent(AgentTelEvents.ANOMALY_DETECTED,
                Attributes.of(AgentTelAttributes.ANOMALY_SCORE, 0.95)));

        assertThat(span.getEvents()).hasSize(1);
        assertThat(span.getEvents().get(0).getName()).isEqualTo("reliability.anomaly.detected");
        assertThat(span.getEvents().get(0).getAttributes()
                .get(AttributeKey.doubleKey("reliability.anomaly.score"))).isEqualTo(0.95);
    }

    @Test
    void mappingIsIdempotent() {
        AttributeNamespaceMapper mapper = new AttributeNamespaceMapper(AttributeNamespaceMode.BOTH);
        Attributes once = mapper.map(Attributes.of(AgentTelAttributes.DECISION_RETRYABLE, true));
        assertThat(mapper.map(once)).isEqualTo(once);
    }

    @Test
    void typesArePreserved() {
        AttributeNamespaceMapper mapper = new AttributeNamespaceMapper(AttributeNamespaceMode.STANDARD);
        Attributes mapped = mapper.map(Attributes.of(
                AgentTelAttributes.BASELINE_LATENCY_P99_MS, 120.5,
                AgentTelAttributes.DECISION_RETRY_AFTER_MS, 500L));
        assertThat(mapped.get(AttributeKey.doubleKey("reliability.baseline.latency_p99_ms"))).isEqualTo(120.5);
        assertThat(mapped.get(AttributeKey.longKey("reliability.decision.retry_after_ms"))).isEqualTo(500L);
    }

    @Test
    void eventNamesMapOnlyInStandardMode() {
        assertThat(new AttributeNamespaceMapper(AttributeNamespaceMode.STANDARD)
                .mapEventName(AgentTelEvents.SLO_BUDGET_ALERT)).isEqualTo("reliability.slo.budget_alert");
        assertThat(new AttributeNamespaceMapper(AttributeNamespaceMode.BOTH)
                .mapEventName(AgentTelEvents.SLO_BUDGET_ALERT)).isEqualTo(AgentTelEvents.SLO_BUDGET_ALERT);
    }

    @Test
    void generatedMapCoversCandidates() {
        assertThat(AttributeNamespaces.ATTRIBUTES)
                .containsEntry("agenttel.topology.repo_url", "vcs.repository.url.full")
                .containsEntry("agenttel.decision.runbook_url", "reliability.decision.runbook_url")
                .doesNotContainKey("agenttel.agentic.agent.name");
    }

    @Test
    void modeParsing() {
        assertThat(AttributeNamespaceMode.fromValue(null)).isEqualTo(AttributeNamespaceMode.LEGACY);
        assertThat(AttributeNamespaceMode.fromValue(" Standard ")).isEqualTo(AttributeNamespaceMode.STANDARD);
        assertThatThrownBy(() -> AttributeNamespaceMode.fromValue("otel"))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
