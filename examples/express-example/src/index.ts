import { engine, sdk } from './telemetry.js'; // must be the first import
import express from 'express';
import { trace } from '@opentelemetry/api';
import { expressMiddleware } from '@agenttel/node';

const app = express();
app.use(express.json());

// Enrich HTTP server spans with topology, baselines and decisions (retryable, runbook, ...)
app.use(expressMiddleware({ engine }));

// Routes
app.post('/api/payments', (_req, res) => {
  const span = trace.getActiveSpan();

  // Simulate processing
  const delay = 30 + Math.random() * 40;
  setTimeout(() => {
    // Simulate occasional errors
    if (Math.random() < 0.02) {
      span?.recordException(new Error('Payment processing failed: insufficient funds'));
      res.status(402).json({ error: 'insufficient_funds' });
      return;
    }

    res.json({
      id: `pay_${Math.floor(Math.random() * 100000)}`,
      status: 'completed',
      amount: 99.99,
    });
  }, delay);
});

app.get('/api/payments/:id', (req, res) => {
  const delay = 10 + Math.random() * 15;
  setTimeout(() => {
    res.json({
      id: req.params.id,
      status: 'completed',
      amount: 99.99,
    });
  }, delay);
});

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

const port = process.env.PORT ?? 3000;
app.listen(port, () => {
  console.log(`Express Payment Service starting on :${port}`);
  console.log('  POST /api/payments      - Create payment');
  console.log('  GET  /api/payments/:id  - Get payment');
  console.log('  GET  /health            - Health check');
});

// Graceful shutdown
process.on('SIGINT', async () => {
  await sdk.shutdown();
  process.exit(0);
});
