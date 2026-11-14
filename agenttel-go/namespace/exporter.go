package namespace

import (
	"context"
	"sync"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

// SpanExporter applies the agenttel.attributes.namespace setting to span
// attributes, span events and the span's resource before handing spans to the
// delegate exporter.
type SpanExporter struct {
	delegate sdktrace.SpanExporter
	mapper   *Mapper

	// Spans of one TracerProvider share a resource; cache its mapping.
	mu        sync.Mutex
	lastIn    *resource.Resource
	lastOut   *resource.Resource
	hasCached bool
}

var _ sdktrace.SpanExporter = (*SpanExporter)(nil)

// WrapSpanExporter wraps delegate so that it receives mapped spans. In Legacy
// mode (or with a nil mapper) it returns delegate unchanged.
func WrapSpanExporter(delegate sdktrace.SpanExporter, mapper *Mapper) sdktrace.SpanExporter {
	if mapper.IsLegacy() {
		return delegate
	}
	return &SpanExporter{delegate: delegate, mapper: mapper}
}

// ExportSpans maps each span and exports the result with the delegate.
func (e *SpanExporter) ExportSpans(ctx context.Context, spans []sdktrace.ReadOnlySpan) error {
	mapped := make([]sdktrace.ReadOnlySpan, len(spans))
	for i, span := range spans {
		mapped[i] = e.mapSpan(span)
	}
	return e.delegate.ExportSpans(ctx, mapped)
}

// Shutdown shuts down the delegate exporter.
func (e *SpanExporter) Shutdown(ctx context.Context) error {
	return e.delegate.Shutdown(ctx)
}

func (e *SpanExporter) mapSpan(span sdktrace.ReadOnlySpan) sdktrace.ReadOnlySpan {
	attrs, attrsChanged := e.mapper.mapAttributes(span.Attributes())
	res := span.Resource()
	mappedRes := e.mapResource(res)
	events, eventsChanged := e.mapEvents(span.Events())
	if !attrsChanged && mappedRes == res && !eventsChanged {
		return span
	}
	return &mappedSpan{
		ReadOnlySpan: span,
		attributes:   attrs,
		events:       events,
		resource:     mappedRes,
	}
}

func (e *SpanExporter) mapResource(res *resource.Resource) *resource.Resource {
	e.mu.Lock()
	defer e.mu.Unlock()
	if e.hasCached && e.lastIn == res {
		return e.lastOut
	}
	out := e.mapper.MapResource(res)
	e.lastIn, e.lastOut, e.hasCached = res, out, true
	return out
}

func (e *SpanExporter) mapEvents(events []sdktrace.Event) ([]sdktrace.Event, bool) {
	var out []sdktrace.Event
	for i, event := range events {
		name := e.mapper.MapEventName(event.Name)
		attrs, changed := e.mapper.mapAttributes(event.Attributes)
		if name == event.Name && !changed {
			if out != nil {
				out = append(out, event)
			}
			continue
		}
		if out == nil {
			out = make([]sdktrace.Event, i, len(events))
			copy(out, events[:i])
		}
		event.Name = name
		event.Attributes = attrs
		out = append(out, event)
	}
	if out == nil {
		return events, false
	}
	return out, true
}

// mappedSpan is a ReadOnlySpan with mapped attributes, events and resource.
// Embedding the interface keeps its unexported method satisfied.
type mappedSpan struct {
	sdktrace.ReadOnlySpan
	attributes []attribute.KeyValue
	events     []sdktrace.Event
	resource   *resource.Resource
}

func (s *mappedSpan) Attributes() []attribute.KeyValue { return s.attributes }

func (s *mappedSpan) Events() []sdktrace.Event { return s.events }

func (s *mappedSpan) Resource() *resource.Resource { return s.resource }
