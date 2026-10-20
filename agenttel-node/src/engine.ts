import type { AgentTelConfig, OperationConfig } from './config.js';
import { defaultConfig, loadConfig } from './config.js';
import { OperationRegistry, normalizeOperationName, parseDurationMs } from './operations.js';
import * as attrs from './attributes.js';
import { AnomalyDetector } from './anomaly/detector.js';
import { StaticBaselineProvider, type BaselineProvider } from './baseline/provider.js';
import { RollingBaselineProvider } from './baseline/rolling.js';
import { CompositeBaselineProvider } from './baseline/composite.js';
import { ErrorClassifier } from './error/classifier.js';
import { SLOTracker } from './slo/tracker.js';
import { TopologyRegistry } from './topology/registry.js';
import { AgentTelEventEmitter } from './events/emitter.js';
import { AgentTelSpanProcessor } from './processor.js';
import type { OperationBaseline, SLODefinition } from './interfaces.js';

/** Top-level orchestrator for AgentTel SDK. */
export class AgentTelEngine {
  readonly topology: TopologyRegistry;
  readonly rollingProvider: RollingBaselineProvider;
  readonly baselineProvider: BaselineProvider;
  readonly anomalyDetector: AnomalyDetector;
  readonly sloTracker: SLOTracker;
  readonly errorClassifier: ErrorClassifier;
  readonly eventEmitter: AgentTelEventEmitter;
  readonly spanProcessor: AgentTelSpanProcessor;
  /** Per-operation decision context (retryable, runbook, escalation, ...). */
  readonly operations: OperationRegistry;
  readonly config: AgentTelConfig;

  private constructor(config: AgentTelConfig) {
    this.config = config;
    // Topology
    this.topology = new TopologyRegistry();
    if (config.topology) {
      if (config.topology.team) this.topology.team = config.topology.team;
      if (config.topology.tier) this.topology.tier = config.topology.tier;
      if (config.topology.domain) this.topology.domain = config.topology.domain;
      if (config.topology.onCallChannel) this.topology.onCallChannel = config.topology.onCallChannel;
      if (config.topology.repoUrl) this.topology.repoUrl = config.topology.repoUrl;
    }
    if (config.dependencies) {
      for (const dep of config.dependencies) {
        this.topology.registerDependency({
          name: dep.name,
          type: dep.type ?? '',
          criticality: dep.criticality ?? '',
          protocol: dep.protocol,
          timeoutMs: dep.timeoutMs,
          circuitBreaker: dep.circuitBreaker,
          fallback: dep.fallback,
          healthEndpoint: dep.healthEndpoint,
        });
      }
    }
    if (config.consumers) {
      for (const c of config.consumers) {
        this.topology.registerConsumer({ name: c.name, pattern: c.pattern ?? 'sync', slaLatencyMs: c.slaLatencyMs ?? 0 });
      }
    }

    // Baselines
    this.rollingProvider = new RollingBaselineProvider(
      config.rollingWindowSize ?? 1000,
      config.rollingMinSamples ?? 10,
    );

    const operations = normalizeOperations(config.operations);
    this.operations = new OperationRegistry(operations, config.profiles ?? {});
    const staticBaselines: Record<string, OperationBaseline> = {};
    for (const [name, op] of Object.entries(operations)) {
      const p50 = parseDurationMs(op.expectedLatencyP50 ?? op.baselineLatencyP50Ms);
      const p99 = parseDurationMs(op.expectedLatencyP99 ?? op.baselineLatencyP99Ms);
      const errorRate = op.expectedErrorRate ?? op.baselineErrorRate;
      if (p50 === undefined && p99 === undefined && errorRate === undefined) continue;
      staticBaselines[name] = {
        operationName: name,
        latencyP50Ms: p50 ?? 0,
        latencyP99Ms: p99 ?? 0,
        errorRate: errorRate ?? 0,
        source: 'static',
        updatedAt: new Date(),
      };
    }
    const staticProvider = new StaticBaselineProvider(staticBaselines);
    this.baselineProvider = new CompositeBaselineProvider(staticProvider, this.rollingProvider);

    // Anomaly detection
    this.anomalyDetector = new AnomalyDetector(config.anomalyZScoreThreshold ?? 3.0);

    // SLO tracking
    this.sloTracker = new SLOTracker();
    if (config.slos) {
      for (const slo of config.slos) {
        this.sloTracker.register({
          name: slo.name,
          operationName: slo.operationName,
          type: slo.type ?? 'availability',
          target: slo.target,
          windowSeconds: slo.windowSeconds,
        });
      }
    }

    // Error classifier
    this.errorClassifier = new ErrorClassifier();

    // Events
    this.eventEmitter = new AgentTelEventEmitter();

    // Span processor
    this.spanProcessor = new AgentTelSpanProcessor({
      topology: this.topology,
      baselineProvider: this.baselineProvider,
      rollingProvider: this.rollingProvider,
      anomalyDetector: this.anomalyDetector,
      sloTracker: this.sloTracker,
      errorClassifier: this.errorClassifier,
      eventEmitter: this.eventEmitter,
      operations: this.operations,
    });
  }

  /** Alias of `topology`. */
  get topologyRegistry(): TopologyRegistry {
    return this.topology;
  }

  /**
   * Topology as OTel resource attributes, for `new Resource(engine.resourceAttributes())`
   * (or `resourceFromAttributes` in OTel JS 2.x).
   */
  resourceAttributes(): Record<string, string> {
    const out: Record<string, string> = {};
    const t = this.topology;
    if (this.config.topology?.serviceName) out['service.name'] = this.config.topology.serviceName;
    if (t.team) out[attrs.TOPOLOGY_TEAM] = t.team;
    if (t.tier) out[attrs.TOPOLOGY_TIER] = t.tier;
    if (t.domain) out[attrs.TOPOLOGY_DOMAIN] = t.domain;
    if (t.onCallChannel) out[attrs.TOPOLOGY_ON_CALL_CHANNEL] = t.onCallChannel;
    if (t.repoUrl) out[attrs.TOPOLOGY_REPO_URL] = t.repoUrl;
    return out;
  }

  /** Create an engine from a YAML file in the shared AgentTel config format. */
  static fromConfigFile(path: string): AgentTelEngine {
    return new AgentTelEngine(loadConfig(path));
  }

  /** Create a new builder. */
  static builder(): AgentTelEngineBuilder {
    return new AgentTelEngineBuilder();
  }

  /** Create an engine with a config directly. */
  static fromConfig(config: AgentTelConfig): AgentTelEngine {
    return new AgentTelEngine(config);
  }
}

/** Builder for configuring and creating an AgentTelEngine. */
export class AgentTelEngineBuilder {
  private config: AgentTelConfig = defaultConfig();

  withConfig(config: AgentTelConfig): this {
    this.config = { ...this.config, ...config };
    return this;
  }

  /** Load a YAML file in the shared AgentTel config format. */
  withConfigFile(path: string): this {
    return this.withConfig(loadConfig(path));
  }

  /** Add or replace one operation ("METHOD /route"). */
  withOperation(name: string, op: OperationConfig): this {
    const ops = normalizeOperations(this.config.operations);
    ops[normalizeOperationName(name)] = op;
    this.config.operations = ops;
    return this;
  }

  withTeam(team: string): this {
    if (!this.config.topology) this.config.topology = {};
    this.config.topology.team = team;
    return this;
  }

  withTier(tier: string): this {
    if (!this.config.topology) this.config.topology = {};
    this.config.topology.tier = tier;
    return this;
  }

  withDomain(domain: string): this {
    if (!this.config.topology) this.config.topology = {};
    this.config.topology.domain = domain;
    return this;
  }

  withSLO(slo: SLODefinition): this {
    if (!this.config.slos) this.config.slos = [];
    this.config.slos.push(slo);
    return this;
  }

  withAnomalyThreshold(threshold: number): this {
    this.config.anomalyZScoreThreshold = threshold;
    return this;
  }

  build(): AgentTelEngine {
    return AgentTelEngine.fromConfig(this.config);
  }
}

function normalizeOperations(
  operations: AgentTelConfig['operations'],
): Record<string, OperationConfig> {
  const out: Record<string, OperationConfig> = {};
  if (Array.isArray(operations)) {
    for (const op of operations) if (op.name) out[normalizeOperationName(op.name)] = op;
  } else if (operations) {
    for (const [name, op] of Object.entries(operations)) out[normalizeOperationName(name)] = op;
  }
  return out;
}
