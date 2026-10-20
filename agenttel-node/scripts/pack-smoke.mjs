// Installs the packed tarball into a fresh project and checks it under plain Node:
//   1. ESM:  import('@agenttel/node')
//   2. CJS:  require('@agenttel/node')
//   3. A real Express and Fastify server with OTel instrumentation gets enriched server spans.
//
// Usage: node scripts/pack-smoke.mjs [path/to/agenttel-node-x.y.z.tgz]
// Without an argument the package is packed first (run `npm run build` before).
import { execFileSync } from 'node:child_process';
import { copyFileSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const pkgRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const work = mkdtempSync(path.join(tmpdir(), 'agenttel-node-smoke-'));
const sh = (cmd, args, opts = {}) =>
  execFileSync(cmd, args, { cwd: work, encoding: 'utf-8', stdio: ['ignore', 'pipe', 'inherit'], ...opts });

let tarball = process.argv[2] && path.resolve(process.argv[2]);
if (!tarball) {
  const name = sh('npm', ['pack', '--silent', '--pack-destination', work], { cwd: pkgRoot }).trim().split('\n').pop();
  tarball = path.join(work, name);
}
console.log(`smoke: ${path.basename(tarball)} on node ${process.version} in ${work}`);

const devDeps = JSON.parse(readFileSync(path.join(pkgRoot, 'package.json'), 'utf-8')).devDependencies;
const pin = (name) => `${name}@${devDeps[name]}`;
writeFileSync(path.join(work, 'package.json'), JSON.stringify({ name: 'smoke', private: true }));
sh('npm', [
  'install', '--no-audit', '--no-fund', '--loglevel=error', tarball,
  pin('@opentelemetry/api'), pin('@opentelemetry/sdk-trace-node'), pin('@opentelemetry/sdk-trace-base'),
  pin('@opentelemetry/resources'), pin('@opentelemetry/instrumentation'),
  pin('@opentelemetry/instrumentation-http'), pin('@opentelemetry/instrumentation-express'),
  pin('express'), pin('fastify'),
]);

const check = "if (typeof m.AgentTelEngine !== 'function' || typeof m.expressMiddleware !== 'function') throw new Error('missing exports')";
sh(process.execPath, ['--input-type=module', '-e', `const m = await import('@agenttel/node'); ${check}; console.log('ESM import ok')`], { stdio: 'inherit' });
sh(process.execPath, ['-e', `const m = require('@agenttel/node'); ${check}; console.log('CJS require ok')`], { stdio: 'inherit' });

copyFileSync(path.join(pkgRoot, 'tests/integration/server.cjs'), path.join(work, 'server.cjs'));
copyFileSync(path.join(pkgRoot, 'tests/integration/agenttel.yml'), path.join(work, 'agenttel.yml'));
for (const framework of ['express', 'fastify']) {
  const spans = JSON.parse(sh(process.execPath, ['server.cjs', framework, 'agenttel.yml']));
  const span = spans.find((s) => s.route === '/api/payments');
  const a = span?.attributes ?? {};
  if (a['agenttel.baseline.latency_p50_ms'] !== 45 || a['agenttel.decision.retryable'] !== true || a['agenttel.topology.team'] !== 'payments-platform') {
    throw new Error(`${framework}: server span not enriched: ${JSON.stringify(spans)}`);
  }
  console.log(`${framework}: server span enriched (p50=45, retryable=true, team=payments-platform)`);
}
console.log('smoke: OK');
