import { describe, it, expect, beforeAll } from 'vitest';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

// End-to-end, mirroring the Spring Boot EnrichmentTest: a real HTTP server with OTel
// auto-instrumentation and the *built* package (plain `node`, no bundler/tsx), one
// request, then assert the HTTP server span is enriched.

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const script = path.join(root, 'tests', 'integration', 'server.cjs');

interface ServerSpan {
  name: string;
  route?: string;
  attributes: Record<string, unknown>;
  resource: Record<string, unknown>;
}

function run(framework: string): ServerSpan[] {
  const out = execFileSync(process.execPath, [script, framework], { cwd: root, encoding: 'utf-8' });
  return JSON.parse(out) as ServerSpan[];
}

// `npm test` builds first (pretest); the server script loads dist/ via package self-reference.
describe.each(['express', 'fastify'])('%s server span', (framework) => {
  let spans: ServerSpan[];
  beforeAll(() => {
    spans = run(framework);
  }, 60_000);

  it('has topology, static baseline and decision attributes', () => {
    const span = spans.find((s) => s.route === '/api/payments');
    expect(span, JSON.stringify(spans)).toBeDefined();
    const a = span!.attributes;
    expect(a['agenttel.topology.team']).toBe('payments-platform');
    expect(a['agenttel.topology.on_call_channel']).toBe('#payments-oncall');
    expect(a['agenttel.baseline.latency_p50_ms']).toBe(45);
    expect(a['agenttel.baseline.latency_p99_ms']).toBe(200);
    expect(a['agenttel.baseline.error_rate']).toBe(0.001);
    expect(a['agenttel.decision.retryable']).toBe(true);
    expect(a['agenttel.decision.idempotent']).toBe(true);
    expect(a['agenttel.decision.runbook_url']).toBe('https://wiki.example.com/runbooks/payments');
    expect(a['agenttel.decision.escalation_level']).toBe('page_oncall'); // from profile
    expect(span!.resource['agenttel.topology.team']).toBe('payments-platform');
  });

  it('matches parameterized routes by template', () => {
    const span = spans.find((s) => s.route === '/api/payments/:id');
    expect(span, JSON.stringify(spans)).toBeDefined();
    expect(span!.attributes['agenttel.baseline.latency_p50_ms']).toBe(15);
    expect(span!.attributes['agenttel.decision.retryable']).toBe(false);
  });
});
