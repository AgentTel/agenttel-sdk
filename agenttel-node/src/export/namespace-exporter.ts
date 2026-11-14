import type { ReadableSpan, SpanExporter, TimedEvent } from '@opentelemetry/sdk-trace-node';
import { AttributeNamespaceMapper } from './namespace-mapper.js';

type ExportCallback = Parameters<SpanExporter['export']>[1];
type SpanResource = ReadableSpan['resource'];

/**
 * SpanExporter that applies the `agenttel.attributes.namespace` setting to span
 * attributes, span events and the span's resource before handing spans to the delegate.
 *
 * Spans are immutable once ended, so the delegate receives a mapped view of each span
 * (a proxy that overrides `attributes`, `events` and `resource`); the original span is
 * never modified. Wrap the exporter you register with the span processor, e.g.
 * `new BatchSpanProcessor(NamespaceMappingSpanExporter.wrap(otlpExporter, mapper))`,
 * so attributes added at any point before export are mapped too.
 */
export class NamespaceMappingSpanExporter implements SpanExporter {
  private readonly resources = new WeakMap<object, SpanResource>();

  constructor(
    private readonly delegate: SpanExporter,
    private readonly mapper: AttributeNamespaceMapper,
  ) {}

  /** Wraps the exporter, or returns it unchanged in `legacy` mode. */
  static wrap(delegate: SpanExporter, mapper: AttributeNamespaceMapper): SpanExporter {
    return mapper.isLegacy() ? delegate : new NamespaceMappingSpanExporter(delegate, mapper);
  }

  export(spans: ReadableSpan[], resultCallback: ExportCallback): void {
    this.delegate.export(spans.map((span) => this.mapSpan(span)), resultCallback);
  }

  shutdown(): Promise<void> {
    return this.delegate.shutdown();
  }

  forceFlush(): Promise<void> {
    return this.delegate.forceFlush ? this.delegate.forceFlush() : Promise.resolve();
  }

  /** Returns a mapped view of the span, or the span itself when nothing maps. */
  mapSpan(span: ReadableSpan): ReadableSpan {
    const attributes = this.mapper.map(span.attributes);
    const events = this.mapEvents(span.events);
    const resource = this.mapResource(span.resource);
    if (attributes === span.attributes && events === span.events && resource === span.resource) {
      return span;
    }
    return overlay(span, { attributes, events, resource });
  }

  private mapEvents(events: TimedEvent[]): TimedEvent[] {
    if (!events || events.length === 0) return events;
    let mapped: TimedEvent[] | undefined;
    events.forEach((event, i) => {
      const name = this.mapper.mapEventName(event.name);
      const attributes = this.mapper.map(event.attributes);
      if (name === event.name && attributes === event.attributes) {
        mapped?.push(event);
        return;
      }
      if (!mapped) mapped = events.slice(0, i);
      mapped.push({ ...event, name, attributes });
    });
    return mapped ?? events;
  }

  private mapResource(resource: SpanResource): SpanResource {
    if (!resource) return resource;
    // Async resource attributes may still change; only cache settled resources.
    const settled = !resource.asyncAttributesPending;
    const cached = settled ? this.resources.get(resource) : undefined;
    if (cached) return cached;
    const attributes = this.mapper.map(resource.attributes);
    let result = resource;
    if (attributes !== resource.attributes) {
      const overrides: Record<string, unknown> = { attributes };
      // OTel JS 2.x resources also expose their attributes as raw entries.
      if (typeof (resource as { getRawAttributes?: unknown }).getRawAttributes === 'function') {
        overrides['getRawAttributes'] = () => Object.entries(attributes);
      }
      result = overlay(resource, overrides);
    }
    if (settled) this.resources.set(resource, result);
    return result;
  }
}

/** A read-only view of `target` with some properties replaced. */
function overlay<T extends object>(target: T, overrides: Record<string, unknown>): T {
  return new Proxy(target, {
    get(t, prop, _receiver) {
      if (typeof prop === 'string' && Object.prototype.hasOwnProperty.call(overrides, prop)) {
        return overrides[prop];
      }
      const value = Reflect.get(t, prop, t);
      return typeof value === 'function' ? value.bind(t) : value;
    },
  });
}
