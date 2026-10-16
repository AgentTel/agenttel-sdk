// Real HTTP server + OTel auto-instrumentation + @agenttel/node, run as plain CommonJS.
// Usage: node server.cjs express|fastify [config.yml]
// Prints the agenttel.* attributes of the HTTP server spans as JSON on stdout.
'use strict';

const path = require('node:path');
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { SimpleSpanProcessor, InMemorySpanExporter } = require('@opentelemetry/sdk-trace-base');
const { Resource } = require('@opentelemetry/resources');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');
const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');
const { ExpressInstrumentation } = require('@opentelemetry/instrumentation-express');
const { SpanKind } = require('@opentelemetry/api');
const { AgentTelEngine, expressMiddleware, fastifyPlugin } = require('@agenttel/node');

const framework = process.argv[2] || 'express';
const configPath = process.argv[3] || path.join(__dirname, 'agenttel.yml');

const engine = AgentTelEngine.fromConfigFile(configPath);
const exporter = new InMemorySpanExporter();
const provider = new NodeTracerProvider({
  resource: new Resource(engine.resourceAttributes()),
  spanProcessors: [engine.spanProcessor, new SimpleSpanProcessor(exporter)],
});
provider.register();
registerInstrumentations({ instrumentations: [new HttpInstrumentation(), new ExpressInstrumentation()] });

async function startExpress() {
  const express = require('express');
  const app = express();
  app.use(expressMiddleware({ engine }));
  app.post('/api/payments', (_req, res) => res.json({ ok: true }));
  app.get('/api/payments/:id', (req, res) => res.json({ id: req.params.id }));
  const server = await new Promise((resolve) => {
    const s = app.listen(0, '127.0.0.1', () => resolve(s));
  });
  return { port: server.address().port, close: () => new Promise((r) => server.close(r)) };
}

async function startFastify() {
  const app = require('fastify')();
  await app.register(fastifyPlugin, { engine });
  app.post('/api/payments', async () => ({ ok: true }));
  app.get('/api/payments/:id', async (req) => ({ id: req.params.id }));
  await app.listen({ port: 0, host: '127.0.0.1' });
  return { port: app.server.address().port, close: () => app.close() };
}

(async () => {
  const server = framework === 'fastify' ? await startFastify() : await startExpress();
  const base = `http://127.0.0.1:${server.port}`;
  await fetch(`${base}/api/payments`, { method: 'POST' });
  await fetch(`${base}/api/payments/pay_123`);
  await server.close();
  await provider.forceFlush();

  const spans = exporter
    .getFinishedSpans()
    .filter((s) => s.kind === SpanKind.SERVER)
    .map((s) => ({
      name: s.name,
      route: s.attributes['http.route'],
      attributes: Object.fromEntries(Object.entries(s.attributes).filter(([k]) => k.startsWith('agenttel.'))),
      resource: Object.fromEntries(
        Object.entries(s.resource.attributes).filter(([k]) => k.startsWith('agenttel.')),
      ),
    }));
  process.stdout.write(JSON.stringify(spans));
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
