package io.agenttel.core.export;

import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.trace.SpanContext;
import io.opentelemetry.api.trace.SpanKind;
import io.opentelemetry.sdk.common.CompletableResultCode;
import io.opentelemetry.sdk.common.InstrumentationScopeInfo;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.data.EventData;
import io.opentelemetry.sdk.trace.data.LinkData;
import io.opentelemetry.sdk.trace.data.SpanData;
import io.opentelemetry.sdk.trace.data.StatusData;
import io.opentelemetry.sdk.trace.export.SpanExporter;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

/**
 * SpanExporter that applies the {@code agenttel.attributes.namespace} setting to span
 * attributes, span events and the span's resource before handing spans to the delegate.
 *
 * <p>Register it inside {@link AgentTelEnrichingSpanExporter} so that attributes added at
 * export time are mapped too.
 */
public class NamespaceMappingSpanExporter implements SpanExporter {

    private final SpanExporter delegate;
    private final AttributeNamespaceMapper mapper;

    public NamespaceMappingSpanExporter(SpanExporter delegate, AttributeNamespaceMapper mapper) {
        this.delegate = delegate;
        this.mapper = mapper;
    }

    /** Wraps the exporter, or returns it unchanged in {@code legacy} mode. */
    public static SpanExporter wrap(SpanExporter delegate, AttributeNamespaceMapper mapper) {
        return mapper.isLegacy() ? delegate : new NamespaceMappingSpanExporter(delegate, mapper);
    }

    @Override
    public CompletableResultCode export(Collection<SpanData> spans) {
        List<SpanData> mapped = new ArrayList<>(spans.size());
        for (SpanData span : spans) {
            mapped.add(map(span));
        }
        return delegate.export(mapped);
    }

    @Override
    public CompletableResultCode flush() {
        return delegate.flush();
    }

    @Override
    public CompletableResultCode shutdown() {
        return delegate.shutdown();
    }

    private SpanData map(SpanData span) {
        Attributes attributes = mapper.map(span.getAttributes());
        Resource resource = mapper.map(span.getResource());
        List<EventData> events = mapEvents(span.getEvents());
        if (attributes == span.getAttributes() && resource == span.getResource()
                && events == span.getEvents()) {
            return span;
        }
        return new MappedSpanData(span, attributes, resource, events);
    }

    private List<EventData> mapEvents(List<EventData> events) {
        List<EventData> mapped = null;
        for (int i = 0; i < events.size(); i++) {
            EventData event = events.get(i);
            String name = mapper.mapEventName(event.getName());
            Attributes attributes = mapper.map(event.getAttributes());
            if (name.equals(event.getName()) && attributes == event.getAttributes()) {
                if (mapped != null) mapped.add(event);
                continue;
            }
            if (mapped == null) {
                mapped = new ArrayList<>(events.subList(0, i));
            }
            mapped.add(EventData.create(event.getEpochNanos(), name, attributes,
                    event.getTotalAttributeCount() - event.getAttributes().size() + attributes.size()));
        }
        return mapped == null ? events : mapped;
    }

    /** Delegating SpanData with mapped attributes, resource and events. */
    private static final class MappedSpanData implements SpanData {
        private final SpanData delegate;
        private final Attributes attributes;
        private final Resource resource;
        private final List<EventData> events;

        MappedSpanData(SpanData delegate, Attributes attributes, Resource resource, List<EventData> events) {
            this.delegate = delegate;
            this.attributes = attributes;
            this.resource = resource;
            this.events = events;
        }

        @Override public SpanContext getSpanContext() { return delegate.getSpanContext(); }
        @Override public SpanContext getParentSpanContext() { return delegate.getParentSpanContext(); }
        @Override public Resource getResource() { return resource; }
        @Override public InstrumentationScopeInfo getInstrumentationScopeInfo() { return delegate.getInstrumentationScopeInfo(); }
        @SuppressWarnings("deprecation")
        @Override public io.opentelemetry.sdk.common.InstrumentationLibraryInfo getInstrumentationLibraryInfo() { return delegate.getInstrumentationLibraryInfo(); }
        @Override public String getName() { return delegate.getName(); }
        @Override public SpanKind getKind() { return delegate.getKind(); }
        @Override public long getStartEpochNanos() { return delegate.getStartEpochNanos(); }
        @Override public Attributes getAttributes() { return attributes; }
        @Override public List<EventData> getEvents() { return events; }
        @Override public List<LinkData> getLinks() { return delegate.getLinks(); }
        @Override public StatusData getStatus() { return delegate.getStatus(); }
        @Override public long getEndEpochNanos() { return delegate.getEndEpochNanos(); }
        @Override public boolean hasEnded() { return delegate.hasEnded(); }
        @Override public int getTotalRecordedEvents() { return delegate.getTotalRecordedEvents(); }
        @Override public int getTotalRecordedLinks() { return delegate.getTotalRecordedLinks(); }
        @Override public int getTotalAttributeCount() {
            return delegate.getTotalAttributeCount() - delegate.getAttributes().size() + attributes.size();
        }
    }
}
