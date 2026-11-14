import { describe, it, expect, vi, afterEach } from 'vitest';
import type { Span } from '@opentelemetry/api';
import {
  BasicTracerProvider,
  InMemorySpanExporter,
  SimpleSpanProcessor,
  type ReadableSpan,
} from '@opentelemetry/sdk-trace-base';
import { Resource } from '@opentelemetry/resources';
import {
  AttributeNamespaceMapper,
  AttributeNamespaceMode,
  parseAttributeNamespaceMode,
} from '../src/export/namespace-mapper.js';
import { NamespaceMappingSpanExporter } from '../src/export/namespace-exporter.js';
import { STANDARD_ATTRIBUTE_KEYS } from '../src/namespaces.js';
import { loadConfigFromEnv, parseConfig } from '../src/config.js';
import { AgentTelEngine } from '../src/engine.js';
import { AgentTelEventEmitter } from '../src/events/emitter.js';
import * as attrs from '../src/attributes.js';

const STD_RETRYABLE = 'reliability.decision.retryable';
const STD_TEAM = 'reliability.topology.team';

async function exportSpan(mode: AttributeNamespaceMode, body: (span: Span) => void): Promise<ReadableSpan> {
  const memory = new InMemorySpanExporter();
  const provider = new BasicTracerProvider({
    resource: new Resource({ [attrs.TOPOLOGY_TEAM]: 'payments' }),
  });
  provider.addSpanProcessor(
    new SimpleSpanProcessor(NamespaceMappingSpanExporter.wrap(memory, new AttributeNamespaceMapper(mode)) as never),
  );
  const span = provider.getTracer('test').startSpan('POST /api/payments');
  body(span);
  span.end();
  await provider.forceFlush();
  const spans = memory.getFinishedSpans();
  await provider.shutdown();
  expect(spans).toHaveLength(1);
  return spans[0];
}

describe('attribute namespace', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    delete process.env.AGENTTEL_ATTRIBUTES_NAMESPACE;
  });

  it('legacy leaves spans unchanged', async () => {
    const span = await exportSpan(AttributeNamespaceMode.LEGACY, (s) => s.setAttribute(attrs.DECISION_RETRYABLE, true));
    expect(span.attributes[attrs.DECISION_RETRYABLE]).toBe(true);
    expect(span.attributes[STD_RETRYABLE]).toBeUndefined();
    expect(span.resource.attributes[STD_TEAM]).toBeUndefined();
  });

  it('legacy wrap returns the delegate itself', () => {
    const memory = new InMemorySpanExporter();
    expect(NamespaceMappingSpanExporter.wrap(memory as never, AttributeNamespaceMapper.LEGACY)).toBe(memory);
  });

  it('standard renames mapped keys and keeps the rest', async () => {
    const span = await exportSpan(AttributeNamespaceMode.STANDARD, (s) => {
      s.setAttribute(attrs.DECISION_RETRYABLE, true);
      s.setAttribute(attrs.BASELINE_SAMPLE_COUNT, 42);
      s.setAttribute(attrs.SEVERITY_ANOMALY_SCORE, 0.9); // internal: not mapped
      s.setAttribute('http.route', '/api/payments');
    });
    expect(span.attributes[STD_RETRYABLE]).toBe(true);
    expect(span.attributes[attrs.DECISION_RETRYABLE]).toBeUndefined();
    expect(span.attributes['reliability.baseline.sample_count']).toBe(42);
    expect(span.attributes[attrs.SEVERITY_ANOMALY_SCORE]).toBe(0.9);
    expect(span.attributes['http.route']).toBe('/api/payments');
    expect(span.resource.attributes[STD_TEAM]).toBe('payments');
    expect(span.resource.attributes[attrs.TOPOLOGY_TEAM]).toBeUndefined();
    // Other span properties pass through the mapped view
    expect(span.name).toBe('POST /api/payments');
    expect(span.spanContext().traceId).toMatch(/^[0-9a-f]{32}$/);
  });

  it('both keeps legacy and adds standard', async () => {
    const span = await exportSpan(AttributeNamespaceMode.BOTH, (s) => s.setAttribute(attrs.DECISION_RETRYABLE, false));
    expect(span.attributes[attrs.DECISION_RETRYABLE]).toBe(false);
    expect(span.attributes[STD_RETRYABLE]).toBe(false);
    expect(span.resource.attributes[attrs.TOPOLOGY_TEAM]).toBe('payments');
    expect(span.resource.attributes[STD_TEAM]).toBe('payments');
  });

  it('an existing OTel attribute wins', async () => {
    const span = await exportSpan(AttributeNamespaceMode.STANDARD, (s) => {
      s.setAttribute('exception.type', 'ECONNRESET');
      s.setAttribute(attrs.ERROR_ROOT_EXCEPTION, 'TimeoutError');
    });
    expect(span.attributes['exception.type']).toBe('ECONNRESET');
    expect(span.attributes[attrs.ERROR_ROOT_EXCEPTION]).toBeUndefined();

    const both = new AttributeNamespaceMapper(AttributeNamespaceMode.BOTH).map({
      [attrs.ERROR_ROOT_EXCEPTION]: 'TimeoutError',
      'exception.type': 'ECONNRESET',
    });
    expect(both['exception.type']).toBe('ECONNRESET');
    expect(both[attrs.ERROR_ROOT_EXCEPTION]).toBe('TimeoutError');
  });

  it('maps span event names and attributes', async () => {
    const span = await exportSpan(AttributeNamespaceMode.STANDARD, (s) =>
      s.addEvent(attrs.EVENT_ANOMALY_DETECTED, { [attrs.ANOMALY_SCORE]: 0.95 }),
    );
    expect(span.events).toHaveLength(1);
    expect(span.events[0].name).toBe('reliability.anomaly.detected');
    expect(span.events[0].attributes?.['reliability.anomaly.score']).toBe(0.95);
    expect(span.events[0].time).toBeDefined();
  });

  it('both keeps the legacy event name but maps event attributes', async () => {
    const span = await exportSpan(AttributeNamespaceMode.BOTH, (s) =>
      s.addEvent(attrs.EVENT_ANOMALY_DETECTED, { [attrs.ANOMALY_SCORE]: 0.95 }),
    );
    expect(span.events[0].name).toBe(attrs.EVENT_ANOMALY_DETECTED);
    expect(span.events[0].attributes?.[attrs.ANOMALY_SCORE]).toBe(0.95);
    expect(span.events[0].attributes?.['reliability.anomaly.score']).toBe(0.95);
  });

  it('does not modify the original span', () => {
    const original = {
      name: 'op',
      attributes: { [attrs.DECISION_RETRYABLE]: true },
      events: [],
      resource: { attributes: {} },
      spanContext: () => ({ traceId: 't' }),
    } as unknown as ReadableSpan;
    const exporter = new NamespaceMappingSpanExporter(
      new InMemorySpanExporter() as never,
      new AttributeNamespaceMapper(AttributeNamespaceMode.STANDARD),
    );
    const mapped = exporter.mapSpan(original as never);
    expect(mapped.attributes[STD_RETRYABLE]).toBe(true);
    expect(original.attributes[attrs.DECISION_RETRYABLE]).toBe(true);
    expect(original.attributes[STD_RETRYABLE]).toBeUndefined();
  });

  it('mapping is idempotent and returns the input when nothing maps', () => {
    const both = new AttributeNamespaceMapper(AttributeNamespaceMode.BOTH);
    const once = both.map({ [attrs.DECISION_RETRYABLE]: true });
    expect(both.map(once)).toEqual(once);

    const standard = new AttributeNamespaceMapper(AttributeNamespaceMode.STANDARD);
    const s1 = standard.map({ [attrs.DECISION_RETRYABLE]: true, 'http.route': '/x' });
    expect(standard.map(s1)).toBe(s1);

    const unmapped = { 'http.route': '/x', [attrs.SEVERITY_ANOMALY_SCORE]: 0.5 };
    expect(standard.map(unmapped)).toBe(unmapped);
  });

  it('preserves value types', () => {
    const mapped = new AttributeNamespaceMapper(AttributeNamespaceMode.STANDARD).map({
      [attrs.BASELINE_LATENCY_P99_MS]: 120.5,
      [attrs.DECISION_RETRY_AFTER_MS]: 500,
      [attrs.DECISION_RETRYABLE]: false,
      [attrs.DECISION_ESCALATION_LEVEL]: 'page_oncall',
      'agenttel.anomaly.pattern': ['latency_spike', 'error_burst'],
    });
    expect(mapped['reliability.baseline.latency_p99_ms']).toBe(120.5);
    expect(mapped['reliability.decision.retry_after_ms']).toBe(500);
    expect(mapped['reliability.decision.retryable']).toBe(false);
    expect(mapped['reliability.decision.escalation_level']).toBe('page_oncall');
    expect(mapped['reliability.anomaly.pattern']).toEqual(['latency_spike', 'error_burst']);
  });

  it('maps event names only in standard mode', () => {
    expect(new AttributeNamespaceMapper(AttributeNamespaceMode.STANDARD).mapEventName(attrs.EVENT_SLO_BUDGET_ALERT)).toBe(
      'reliability.slo.budget_alert',
    );
    expect(new AttributeNamespaceMapper(AttributeNamespaceMode.BOTH).mapEventName(attrs.EVENT_SLO_BUDGET_ALERT)).toBe(
      attrs.EVENT_SLO_BUDGET_ALERT,
    );
    expect(AttributeNamespaceMapper.LEGACY.mapEventName(attrs.EVENT_SLO_BUDGET_ALERT)).toBe(attrs.EVENT_SLO_BUDGET_ALERT);
    expect(new AttributeNamespaceMapper(AttributeNamespaceMode.STANDARD).mapEventName('custom.event')).toBe('custom.event');
  });

  it('generated map covers candidates', () => {
    expect(STANDARD_ATTRIBUTE_KEYS['agenttel.topology.repo_url']).toBe('vcs.repository.url.full');
    expect(STANDARD_ATTRIBUTE_KEYS['agenttel.decision.runbook_url']).toBe('reliability.decision.runbook_url');
    expect(STANDARD_ATTRIBUTE_KEYS['agenttel.agentic.agent.name']).toBeUndefined();
  });

  it('parses modes case-insensitively, falling back to legacy', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(parseAttributeNamespaceMode(undefined)).toBe(AttributeNamespaceMode.LEGACY);
    expect(parseAttributeNamespaceMode('  ')).toBe(AttributeNamespaceMode.LEGACY);
    expect(parseAttributeNamespaceMode(' Standard ')).toBe(AttributeNamespaceMode.STANDARD);
    expect(parseAttributeNamespaceMode('BOTH')).toBe(AttributeNamespaceMode.BOTH);
    expect(warn).not.toHaveBeenCalled();
    expect(parseAttributeNamespaceMode('otel')).toBe(AttributeNamespaceMode.LEGACY);
    expect(warn).toHaveBeenCalledWith(expect.stringContaining("'otel'"));
  });

  it('loads attributes.namespace from config', () => {
    const config = parseConfig({ agenttel: { attributes: { namespace: 'Both' } } });
    expect(config.attributes?.namespace).toBe(AttributeNamespaceMode.BOTH);
    expect(parseConfig({ agenttel: {} }).attributes).toBeUndefined();
  });

  it('loads AGENTTEL_ATTRIBUTES_NAMESPACE from env', () => {
    process.env.AGENTTEL_ATTRIBUTES_NAMESPACE = 'standard';
    expect(loadConfigFromEnv().attributes?.namespace).toBe(AttributeNamespaceMode.STANDARD);
  });

  it('engine maps resource attributes, events and exporter', () => {
    const engine = AgentTelEngine.builder().withTeam('payments').withAttributeNamespace('standard').build();
    expect(engine.namespaceMapper.mode).toBe(AttributeNamespaceMode.STANDARD);
    expect(engine.resourceAttributes()).toEqual({ [STD_TEAM]: 'payments' });

    const memory = new InMemorySpanExporter();
    expect(engine.wrapExporter(memory as never)).toBeInstanceOf(NamespaceMappingSpanExporter);

    const legacy = AgentTelEngine.builder().withTeam('payments').build();
    expect(legacy.resourceAttributes()).toEqual({ [attrs.TOPOLOGY_TEAM]: 'payments' });
    expect(legacy.wrapExporter(memory as never)).toBe(memory);
  });

  it('event emitter maps event names and attributes', () => {
    const seen: Array<[string, Record<string, unknown>]> = [];
    const emitter = new AgentTelEventEmitter(new AttributeNamespaceMapper(AttributeNamespaceMode.STANDARD));
    emitter.onEvent((name, a) => seen.push([name, a]));
    emitter.emit(attrs.EVENT_ANOMALY_DETECTED, { [attrs.ANOMALY_SCORE]: 0.9, operation: 'GET /x' });
    expect(seen[0][0]).toBe('reliability.anomaly.detected');
    expect(seen[0][1]).toEqual({ 'reliability.anomaly.score': 0.9, operation: 'GET /x' });

    const legacySeen: string[] = [];
    const legacy = new AgentTelEventEmitter();
    legacy.onEvent((name) => legacySeen.push(name));
    legacy.emit(attrs.EVENT_ANOMALY_DETECTED);
    expect(legacySeen).toEqual([attrs.EVENT_ANOMALY_DETECTED]);
  });
});
