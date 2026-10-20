import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { defaultConfig, loadConfigFromEnv, parseConfig, type OperationConfig } from '../src/config.js';
import { normalizeOperationName, parseDurationMs } from '../src/operations.js';
import { AgentTelEngine } from '../src/engine.js';

describe('Config', () => {
  it('default config has sensible defaults', () => {
    const config = defaultConfig();
    expect(config.rollingWindowSize).toBe(1000);
    expect(config.rollingMinSamples).toBe(10);
    expect(config.anomalyZScoreThreshold).toBe(3.0);
  });

  describe('env overrides', () => {
    const envBackup: Record<string, string | undefined> = {};

    beforeEach(() => {
      envBackup.AGENTTEL_TOPOLOGY_TEAM = process.env.AGENTTEL_TOPOLOGY_TEAM;
      envBackup.AGENTTEL_TOPOLOGY_TIER = process.env.AGENTTEL_TOPOLOGY_TIER;
      envBackup.AGENTTEL_TOPOLOGY_DOMAIN = process.env.AGENTTEL_TOPOLOGY_DOMAIN;
      envBackup.AGENTTEL_ANOMALY_ZSCORE_THRESHOLD = process.env.AGENTTEL_ANOMALY_ZSCORE_THRESHOLD;
    });

    afterEach(() => {
      for (const [key, value] of Object.entries(envBackup)) {
        if (value === undefined) delete process.env[key];
        else process.env[key] = value;
      }
    });

    it('loads topology from env vars', () => {
      process.env.AGENTTEL_TOPOLOGY_TEAM = 'payments';
      process.env.AGENTTEL_TOPOLOGY_TIER = 'critical';
      process.env.AGENTTEL_TOPOLOGY_DOMAIN = 'fintech';

      const config = loadConfigFromEnv();
      expect(config.topology?.team).toBe('payments');
      expect(config.topology?.tier).toBe('critical');
      expect(config.topology?.domain).toBe('fintech');
    });

    it('loads anomaly threshold from env', () => {
      process.env.AGENTTEL_ANOMALY_ZSCORE_THRESHOLD = '4.5';
      const config = loadConfigFromEnv();
      expect(config.anomalyZScoreThreshold).toBe(4.5);
    });
  });
});

describe('shared config format', () => {
  it('parses the canonical agenttel: document', () => {
    const config = parseConfig({
      agenttel: {
        topology: { team: 'payments', 'on-call-channel': '#oncall', 'service-name': 'svc' },
        operations: {
          '[POST /api/payments]': {
            'expected-latency-p50': '45ms',
            'expected-latency-p99': '1.5s',
            'expected-error-rate': 0.001,
            retryable: true,
            'runbook-url': 'https://runbooks/payments',
          },
          'GET /orders/:id': { 'expected-latency-p50': 15 },
        },
        baselines: { 'rolling-window-size': 500 },
        'anomaly-detection': { 'z-score-threshold': 2.5 },
        slo: { availability: { target: 0.999, type: 'availability' } },
      },
    });
    expect(config.topology?.onCallChannel).toBe('#oncall');
    expect(config.topology?.serviceName).toBe('svc');
    const ops = config.operations as Record<string, OperationConfig>;
    expect(Object.keys(ops)).toEqual(['POST /api/payments', 'GET /orders/{id}']);
    expect(ops['POST /api/payments'].expectedLatencyP50).toBe('45ms');
    expect(ops['POST /api/payments'].retryable).toBe(true);
    expect(config.rollingWindowSize).toBe(500);
    expect(config.anomalyZScoreThreshold).toBe(2.5);
    expect(config.slos?.[0]).toMatchObject({ name: 'availability', target: 0.999 });

    const engine = AgentTelEngine.fromConfig(config);
    expect(engine.baselineProvider.getBaseline('POST /api/payments')?.latencyP99Ms).toBe(1500);
    expect(engine.baselineProvider.getBaseline('GET /orders/{id}')?.latencyP50Ms).toBe(15);
    expect(engine.operations.getDecision('[POST /api/payments]')).toMatchObject({
      retryable: true,
      runbookUrl: 'https://runbooks/payments',
      escalationLevel: 'auto_resolve',
    });
  });

  it('still loads the pre-0.4.0 Node dialect, with a warning', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const config = parseConfig({
      topology: { team: 't', on_call_channel: '#c' },
      operations: [{ name: 'POST /p', baseline_latency_p50_ms: 45, baseline_latency_p99_ms: 200 }],
      rolling_window_size: 50,
      anomaly_zscore_threshold: 2,
    });
    expect(config.topology?.onCallChannel).toBe('#c');
    expect(config.rollingWindowSize).toBe(50);
    expect(config.anomalyZScoreThreshold).toBe(2);
    const engine = AgentTelEngine.fromConfig(config);
    expect(engine.baselineProvider.getBaseline('POST /p')?.latencyP50Ms).toBe(45);
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it('accepts programmatic operation arrays (pre-0.4.0 API)', () => {
    const engine = AgentTelEngine.fromConfig({
      operations: [{ name: 'GET /x', baselineLatencyP50Ms: 10, baselineLatencyP99Ms: 20 }],
    });
    expect(engine.baselineProvider.getBaseline('GET /x')?.latencyP50Ms).toBe(10);
  });

  it('parses durations and normalizes operation names', () => {
    expect(parseDurationMs('45ms')).toBe(45);
    expect(parseDurationMs('2s')).toBe(2000);
    expect(parseDurationMs(12)).toBe(12);
    expect(() => parseDurationMs('fast')).toThrow();
    expect(normalizeOperationName('[post /a/:id]')).toBe('POST /a/{id}');
    expect(normalizeOperationName('process-payment')).toBe('process-payment');
  });
});
