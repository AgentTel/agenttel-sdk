import { engine, sdk } from './telemetry.js'; // must be the first import
import Fastify from 'fastify';
import { trace } from '@opentelemetry/api';
import { fastifyPlugin } from '@agenttel/node';

const app = Fastify({ logger: true });

// Enrich HTTP server spans with topology, baselines and decisions (retryable, runbook, ...)
app.register(fastifyPlugin, { engine });

// Routes
app.post('/api/payments', async (_request, reply) => {
  const span = trace.getActiveSpan();

  // Simulate processing latency (30-70ms)
  await sleep(30 + Math.random() * 40);

  // Simulate occasional errors (~2% rate)
  if (Math.random() < 0.02) {
    span?.recordException(new Error('Payment processing failed: insufficient funds'));
    return reply.status(402).send({ error: 'insufficient_funds' });
  }

  return {
    id: `pay_${Math.floor(Math.random() * 100000)}`,
    status: 'completed',
    amount: 99.99,
  };
});

app.get('/api/payments/:id', async (request, _reply) => {
  const { id } = request.params as { id: string };

  // Simulate read latency (10-25ms)
  await sleep(10 + Math.random() * 15);

  return {
    id,
    status: 'completed',
    amount: 99.99,
  };
});

app.get('/health', async (_request, _reply) => {
  return { status: 'ok' };
});

// Start server
const port = Number(process.env.PORT ?? 3000);
app.listen({ port, host: '0.0.0.0' }, (err) => {
  if (err) {
    app.log.error(err);
    process.exit(1);
  }
  console.log(`Fastify Payment Service starting on :${port}`);
  console.log('  POST /api/payments      - Create payment');
  console.log('  GET  /api/payments/:id  - Get payment');
  console.log('  GET  /health            - Health check');
});

// Graceful shutdown
process.on('SIGINT', async () => {
  await app.close();
  await sdk.shutdown();
  process.exit(0);
});

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
