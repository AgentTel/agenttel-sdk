import { readFileSync } from 'node:fs';
import yaml from 'js-yaml';
import { normalizeOperationName } from './operations.js';

/*
 * The canonical format is shared by every AgentTel SDK (JVM, Go, Node.js, Python):
 *
 *   agenttel:
 *     topology:
 *       team: payments-platform
 *       on-call-channel: "#payments-oncall"
 *     operations:
 *       "[POST /api/payments]":        # brackets optional
 *         expected-latency-p50: 45ms   # duration string, or a number in ms
 *         retryable: true
 *
 * The pre-0.4.0 Node.js dialect (no `agenttel:` root, snake_case keys, `operations`
 * as a list of `{ name, baseline_latency_p50_ms }`) still loads, with a warning.
 */

export interface TopologyConfig {
  serviceName?: string;
  team?: string;
  tier?: string;
  domain?: string;
  onCallChannel?: string;
  repoUrl?: string;
}

export interface DependencyConfig {
  name: string;
  type?: string;
  criticality?: string;
  protocol?: string;
  timeoutMs?: number;
  circuitBreaker?: boolean;
  fallback?: string;
  healthEndpoint?: string;
}

export interface ConsumerConfig {
  name: string;
  pattern?: string;
  slaLatencyMs?: number;
}

/** Shared decision defaults that operations can reference by name. */
export interface ProfileConfig {
  retryable?: boolean;
  idempotent?: boolean;
  runbookUrl?: string;
  fallbackDescription?: string;
  escalationLevel?: string;
  safeToRestart?: boolean;
}

/** Per-operation configuration. Explicit values override the referenced profile. */
export interface OperationConfig extends ProfileConfig {
  profile?: string;
  /** Duration string ("45ms", "1s") or number of milliseconds. */
  expectedLatencyP50?: string | number;
  expectedLatencyP99?: string | number;
  expectedErrorRate?: number;
  /** @deprecated pre-0.4.0 list form; use the `operations` map key instead. */
  name?: string;
  /** @deprecated use expectedLatencyP50 */
  baselineLatencyP50Ms?: number;
  /** @deprecated use expectedLatencyP99 */
  baselineLatencyP99Ms?: number;
  /** @deprecated use expectedErrorRate */
  baselineErrorRate?: number;
}

export interface SLOConfig {
  name: string;
  operationName?: string;
  type?: string;
  target: number;
  windowSeconds?: number;
}

export interface AgentTelConfig {
  enabled?: boolean;
  topology?: TopologyConfig;
  dependencies?: DependencyConfig[];
  consumers?: ConsumerConfig[];
  profiles?: Record<string, ProfileConfig>;
  /** Map keyed by "METHOD /route". The array form is deprecated but still accepted. */
  operations?: Record<string, OperationConfig> | OperationConfig[];
  slos?: SLOConfig[];
  rollingWindowSize?: number;
  rollingMinSamples?: number;
  anomalyDetectionEnabled?: boolean;
  anomalyZScoreThreshold?: number;
}

/** Load config from a YAML file (canonical `agenttel:` format or a legacy dialect). */
export function loadConfig(path: string): AgentTelConfig {
  const content = readFileSync(path, 'utf-8');
  const raw = (yaml.load(content) ?? {}) as Record<string, unknown>;
  return parseConfig(raw);
}

/** Load config from environment variables (AGENTTEL_TOPOLOGY_TEAM, etc.). */
export function loadConfigFromEnv(): AgentTelConfig {
  const config = defaultConfig();

  if (!config.topology) config.topology = {};
  if (process.env.AGENTTEL_TOPOLOGY_TEAM) config.topology.team = process.env.AGENTTEL_TOPOLOGY_TEAM;
  if (process.env.AGENTTEL_TOPOLOGY_TIER) config.topology.tier = process.env.AGENTTEL_TOPOLOGY_TIER;
  if (process.env.AGENTTEL_TOPOLOGY_DOMAIN) config.topology.domain = process.env.AGENTTEL_TOPOLOGY_DOMAIN;
  if (process.env.AGENTTEL_TOPOLOGY_ON_CALL_CHANNEL) config.topology.onCallChannel = process.env.AGENTTEL_TOPOLOGY_ON_CALL_CHANNEL;
  if (process.env.AGENTTEL_TOPOLOGY_REPO_URL) config.topology.repoUrl = process.env.AGENTTEL_TOPOLOGY_REPO_URL;

  const thresh = process.env.AGENTTEL_ANOMALY_ZSCORE_THRESHOLD;
  if (thresh) config.anomalyZScoreThreshold = parseFloat(thresh);

  const winSize = process.env.AGENTTEL_ROLLING_WINDOW_SIZE;
  if (winSize) config.rollingWindowSize = parseInt(winSize, 10);

  const minSamp = process.env.AGENTTEL_ROLLING_MIN_SAMPLES;
  if (minSamp) config.rollingMinSamples = parseInt(minSamp, 10);

  return config;
}

/** Returns a config with sensible defaults. */
export function defaultConfig(): AgentTelConfig {
  return {
    rollingWindowSize: 1000,
    rollingMinSamples: 10,
    anomalyZScoreThreshold: 3.0,
  };
}

type Raw = Record<string, unknown>;

// Sections whose keys are user-chosen names, not schema keys.
const NAMED_MAPS = new Set(['operations', 'profiles', 'slo', 'agent-roles']);
const ENTRY = Symbol('entry');

function toKebab(key: string): string {
  return key.replace(/([a-z0-9])([A-Z])/g, '$1-$2').replace(/_/g, '-').toLowerCase();
}

function kebabKeys(value: unknown, section: string | symbol | undefined, legacy: Set<string>): unknown {
  if (Array.isArray(value)) return value.map((v) => kebabKeys(v, undefined, legacy));
  if (!value || typeof value !== 'object') return value;
  const out: Raw = {};
  for (const [key, v] of Object.entries(value as Raw)) {
    if (typeof section === 'string' && NAMED_MAPS.has(section)) {
      out[section === 'operations' ? normalizeOperationName(key) : key] = kebabKeys(v, ENTRY, legacy);
      continue;
    }
    const k = toKebab(key);
    if (k !== key) legacy.add(key);
    out[k] = kebabKeys(v, k, legacy);
  }
  return out;
}

const str = (v: unknown): string | undefined => (v === undefined || v === null ? undefined : String(v));
const num = (v: unknown): number | undefined => (typeof v === 'number' ? v : typeof v === 'string' && v.trim() !== '' && !isNaN(Number(v)) ? Number(v) : undefined);
const bool = (v: unknown): boolean | undefined => (typeof v === 'boolean' ? v : v === 'true' ? true : v === 'false' ? false : undefined);
const obj = (v: unknown): Raw => (v && typeof v === 'object' && !Array.isArray(v) ? (v as Raw) : {});

function warn(message: string): void {
  // eslint-disable-next-line no-console
  console.warn(`[agenttel] ${message}`);
}

function parseProfile(p: Raw): ProfileConfig {
  return {
    retryable: bool(p['retryable']),
    idempotent: bool(p['idempotent']),
    runbookUrl: str(p['runbook-url']),
    fallbackDescription: str(p['fallback-description']),
    escalationLevel: str(p['escalation-level']),
    safeToRestart: bool(p['safe-to-restart']),
  };
}

function parseOperation(o: Raw): OperationConfig {
  const latency = (v: unknown) => (typeof v === 'number' ? v : str(v));
  return {
    ...parseProfile(o),
    profile: str(o['profile']),
    expectedLatencyP50: latency(o['expected-latency-p50'] ?? o['baseline-latency-p50-ms']),
    expectedLatencyP99: latency(o['expected-latency-p99'] ?? o['baseline-latency-p99-ms']),
    expectedErrorRate: num(o['expected-error-rate'] ?? o['baseline-error-rate']),
  };
}

/** Parse an already-loaded YAML/JSON document into an AgentTelConfig. */
export function parseConfig(input: Record<string, unknown>): AgentTelConfig {
  let root: Raw = input ?? {};
  if (root['agenttel'] && typeof root['agenttel'] === 'object') {
    root = root['agenttel'] as Raw;
  } else if (Object.keys(root).length > 0) {
    warn("config without a top-level 'agenttel:' key is deprecated; nest the configuration under 'agenttel:'");
  }

  const legacy = new Set<string>();
  const raw = kebabKeys(root, undefined, legacy) as Raw;
  const config: AgentTelConfig = defaultConfig();

  if (raw['enabled'] !== undefined) config.enabled = bool(raw['enabled']);

  const t = obj(raw['topology']);
  if (raw['topology']) {
    config.topology = {
      serviceName: str(t['service-name']),
      team: str(t['team']),
      tier: str(t['tier']),
      domain: str(t['domain']),
      onCallChannel: str(t['on-call-channel']),
      repoUrl: str(t['repo-url']),
    };
  }

  if (Array.isArray(raw['dependencies'])) {
    config.dependencies = (raw['dependencies'] as Raw[]).map((d) => ({
      name: String(d['name']),
      type: str(d['type']),
      criticality: str(d['criticality']),
      protocol: str(d['protocol']),
      timeoutMs: num(d['timeout-ms']),
      circuitBreaker: bool(d['circuit-breaker']),
      fallback: str(d['fallback']),
      healthEndpoint: str(d['health-endpoint']),
    }));
  }

  if (Array.isArray(raw['consumers'])) {
    config.consumers = (raw['consumers'] as Raw[]).map((c) => ({
      name: String(c['name']),
      pattern: str(c['pattern']),
      slaLatencyMs: num(c['sla-latency-ms']),
    }));
  }

  if (raw['profiles']) {
    config.profiles = {};
    for (const [name, p] of Object.entries(obj(raw['profiles']))) config.profiles[name] = parseProfile(obj(p));
  }

  let ops = raw['operations'];
  if (Array.isArray(ops)) {
    warn("'operations' as a list is deprecated; use a map keyed by \"METHOD /route\"");
    const converted: Raw = {};
    for (const item of ops as Raw[]) {
      const { name, ...rest } = obj(item);
      if (name) converted[normalizeOperationName(String(name))] = rest;
    }
    ops = converted;
  }
  if (ops) {
    const operations: Record<string, OperationConfig> = {};
    for (const [name, o] of Object.entries(obj(ops))) {
      const op = obj(o);
      for (const k of ['baseline-latency-p50-ms', 'baseline-latency-p99-ms', 'baseline-error-rate']) {
        if (k in op) legacy.add(k);
      }
      operations[name] = parseOperation(op);
    }
    config.operations = operations;
  }

  const slos: SLOConfig[] = [];
  for (const [name, s] of Object.entries(obj(raw['slo']))) {
    const so = obj(s);
    slos.push({
      name: str(so['name']) ?? name,
      operationName: str(so['operation'] ?? so['operation-name']),
      type: str(so['type']),
      target: num(so['target']) ?? 0.999,
      windowSeconds: num(so['window-seconds']),
    });
  }
  if (Array.isArray(raw['slos'])) {
    for (const so of raw['slos'] as Raw[]) {
      slos.push({
        name: String(so['name']),
        operationName: str(so['operation-name']),
        type: str(so['type']),
        target: num(so['target']) ?? 0.999,
        windowSeconds: num(so['window-seconds']),
      });
    }
  }
  if (slos.length > 0) config.slos = slos;

  const baselines = obj(raw['baselines']);
  const windowSize = num(baselines['rolling-window-size'] ?? raw['rolling-window-size']);
  if (windowSize !== undefined) config.rollingWindowSize = windowSize;
  const minSamples = num(baselines['rolling-min-samples'] ?? raw['rolling-min-samples']);
  if (minSamples !== undefined) config.rollingMinSamples = minSamples;

  const anomaly = obj(raw['anomaly-detection']);
  if (anomaly['enabled'] !== undefined) config.anomalyDetectionEnabled = bool(anomaly['enabled']);
  const threshold = num(anomaly['z-score-threshold'] ?? raw['anomaly-zscore-threshold']);
  if (threshold !== undefined) config.anomalyZScoreThreshold = threshold;

  for (const k of ['rolling-window-size', 'rolling-min-samples', 'anomaly-zscore-threshold', 'slos']) {
    if (k in raw) legacy.add(k);
  }
  if (legacy.size > 0) {
    warn(
      `config uses deprecated key spellings [${[...legacy].sort().join(', ')}]; use the shared kebab-case ` +
        "format (e.g. 'on-call-channel', 'expected-latency-p50', 'baselines.rolling-window-size')",
    );
  }
  return config;
}
