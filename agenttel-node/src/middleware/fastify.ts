import { trace } from '@opentelemetry/api';
import type { BaselineProvider } from '../baseline/provider.js';
import type { TopologyRegistry } from '../topology/registry.js';
import type { DecisionProvider } from '../operations.js';
import { enrichOperation, enrichTopology } from '../enrich.js';

export interface FastifyPluginOptions {
  /** Shorthand: take topology, baselines and decisions from an AgentTelEngine. */
  engine?: {
    topology: TopologyRegistry;
    baselineProvider: BaselineProvider;
    operations: DecisionProvider;
  };
  baselineProvider?: BaselineProvider;
  topology?: TopologyRegistry;
  /** Decision context per operation, usually `engine.operations`. */
  operations?: DecisionProvider;
}

interface FastifyRequest {
  method: string;
  routeOptions?: { url: string };
  url: string;
}

interface FastifyReply {
  statusCode: number;
}

interface FastifyInstance {
  addHook(hook: string, handler: (req: FastifyRequest, reply: FastifyReply, done: () => void) => void): void;
}

/**
 * Fastify plugin that enriches the active HTTP server span with AgentTel
 * topology, baseline and decision attributes for "METHOD /route".
 *
 * Usage:
 * ```ts
 * import { AgentTelEngine, fastifyPlugin } from '@agenttel/node';
 * const engine = AgentTelEngine.fromConfigFile('agenttel.yml');
 * fastify.register(fastifyPlugin, { engine });
 * ```
 */
export function fastifyPlugin(
  fastify: FastifyInstance,
  options: FastifyPluginOptions,
  done: () => void,
): void {
  const topology = options.topology ?? options.engine?.topology;
  const sources = {
    baselineProvider: options.baselineProvider ?? options.engine?.baselineProvider,
    decisions: options.operations ?? options.engine?.operations,
  };

  fastify.addHook('onRequest', (req: FastifyRequest, _reply: FastifyReply, hookDone: () => void) => {
    const span = trace.getActiveSpan();
    if (span) {
      // Routing has already happened at onRequest, so the template is known.
      const route = req.routeOptions?.url;
      if (route) span.setAttribute('http.route', route);
      const routePattern = route ?? req.url;
      if (topology) enrichTopology(span, topology);
      enrichOperation(span, `${req.method} ${routePattern}`, sources);
    }
    hookDone();
  });

  done();
}

// Fastify requires this metadata for plugin registration
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(fastifyPlugin as any)[Symbol.for('skip-override')] = true;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(fastifyPlugin as any)[Symbol.for('fastify.display-name')] = '@agenttel/node/fastify';
