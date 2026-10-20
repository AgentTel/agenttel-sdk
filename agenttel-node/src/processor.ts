import type { ReadableSpan, SpanProcessor } from '@opentelemetry/sdk-trace-node';
import type { Context } from '@opentelemetry/api';
import type { Span } from '@opentelemetry/api';
import * as attrs from './attributes.js';
import { AnomalyDetector } from './anomaly/detector.js';
import type { BaselineProvider } from './baseline/provider.js';
import { RollingBaselineProvider } from './baseline/rolling.js';
import { ErrorClassifier } from './error/classifier.js';
import { SLOTracker } from './slo/tracker.js';
import { TopologyRegistry } from './topology/registry.js';
import { AgentTelEventEmitter } from './events/emitter.js';
import { enrichOperation, enrichTopology } from './enrich.js';
import { normalizeOperationName, type DecisionProvider } from './operations.js';

export interface ProcessorOptions {
  topology?: TopologyRegistry;
  baselineProvider?: BaselineProvider;
  rollingProvider?: RollingBaselineProvider;
  anomalyDetector?: AnomalyDetector;
  sloTracker?: SLOTracker;
  errorClassifier?: ErrorClassifier;
  eventEmitter?: AgentTelEventEmitter;
  /** Decision context per operation (retryable, runbook, escalation, ...). */
  operations?: DecisionProvider;
}

/** OTel SpanProcessor that enriches spans with AgentTel metadata. */
export class AgentTelSpanProcessor implements SpanProcessor {
  private readonly topology?: TopologyRegistry;
  private readonly baselineProvider?: BaselineProvider;
  private readonly rollingProvider?: RollingBaselineProvider;
  private readonly anomalyDetector?: AnomalyDetector;
  private readonly sloTracker?: SLOTracker;
  private readonly errorClassifier?: ErrorClassifier;
  private readonly eventEmitter?: AgentTelEventEmitter;
  private readonly operations?: DecisionProvider;

  constructor(options: ProcessorOptions = {}) {
    this.topology = options.topology;
    this.baselineProvider = options.baselineProvider;
    this.rollingProvider = options.rollingProvider;
    this.anomalyDetector = options.anomalyDetector;
    this.sloTracker = options.sloTracker;
    this.errorClassifier = options.errorClassifier;
    this.eventEmitter = options.eventEmitter;
    this.operations = options.operations;
  }

  onStart(span: Span, _parentContext: Context): void {
    // Enrich with topology metadata
    if (this.topology) {
      enrichTopology(span, this.topology);

      const deps = this.topology.dependencies();
      if (deps.length > 0) {
        span.setAttribute(attrs.TOPOLOGY_DEPENDENCIES, this.topology.serializeDependenciesJSON());
      }
      const consumers = this.topology.consumers();
      if (consumers.length > 0) {
        span.setAttribute(attrs.TOPOLOGY_CONSUMERS, this.topology.serializeConsumersJSON());
      }
    }

    // Enrich spans already named after a configured operation. HTTP server spans are
    // named before routing (e.g. "POST"); the framework middleware handles those.
    const opName = (span as unknown as { name?: string }).name;
    if (opName) {
      enrichOperation(span, opName, { baselineProvider: this.baselineProvider, decisions: this.operations });
    }
  }

  onEnd(span: ReadableSpan): void {
    const opName = operationNameOf(span);
    const durationMs = (span.endTime[0] - span.startTime[0]) * 1000 +
      (span.endTime[1] - span.startTime[1]) / 1e6;
    const isError = span.status?.code === 2; // StatusCode.ERROR

    // Record in rolling baseline
    if (this.rollingProvider && opName) {
      if (isError) {
        this.rollingProvider.recordError(opName);
      } else {
        this.rollingProvider.recordLatency(opName, durationMs);
      }
    }

    // Anomaly detection
    if (this.anomalyDetector && this.rollingProvider && opName) {
      const snap = this.rollingProvider.getSnapshot(opName);
      if (snap && snap.sampleCount > 0) {
        const result = this.anomalyDetector.evaluate('latency', durationMs, snap.mean, snap.stddev);
        if (result.isAnomaly && this.eventEmitter) {
          this.eventEmitter.emit(attrs.EVENT_ANOMALY_DETECTED, {
            operation: opName,
            score: result.anomalyScore,
            zScore: result.zScore,
          });
        }
      }
    }

    // SLO tracking
    if (this.sloTracker && opName) {
      if (isError) {
        this.sloTracker.recordFailure(opName);
      } else {
        this.sloTracker.recordSuccess(opName);
      }
    }

    // Error classification
    if (this.errorClassifier && isError) {
      const events = span.events || [];
      for (const event of events) {
        if (event.name === 'exception') {
          const exType = String(event.attributes?.['exception.type'] ?? '');
          const exMsg = String(event.attributes?.['exception.message'] ?? '');
          if (exType) {
            this.errorClassifier.classifyException(exType, exMsg);
          }
        }
      }
    }
  }

  async shutdown(): Promise<void> {
    // no-op
  }

  async forceFlush(): Promise<void> {
    // no-op
  }
}

/** "METHOD /route" for HTTP server spans with a route, otherwise the span name. */
function operationNameOf(span: ReadableSpan): string {
  const route = span.attributes?.['http.route'];
  const method = span.attributes?.['http.request.method'] ?? span.attributes?.['http.method'];
  if (typeof route === 'string' && typeof method === 'string') {
    return normalizeOperationName(`${method} ${route}`);
  }
  return normalizeOperationName(span.name);
}
