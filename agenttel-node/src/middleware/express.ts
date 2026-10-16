import { trace, type Span } from '@opentelemetry/api';
import type { BaselineProvider } from '../baseline/provider.js';
import type { TopologyRegistry } from '../topology/registry.js';
import type { DecisionProvider } from '../operations.js';
import { enrichOperation, enrichTopology } from '../enrich.js';

export interface ExpressMiddlewareOptions {
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
  routeResolver?: (req: ExpressRequest) => string;
}

interface ExpressRequest {
  method: string;
  route?: { path: string };
  baseUrl?: string;
  originalUrl: string;
  path: string;
}

interface ExpressResponse {
  statusCode: number;
  end?: (...args: unknown[]) => unknown;
}

type NextFunction = (err?: unknown) => void;

/**
 * Express middleware that enriches the active HTTP server span with AgentTel
 * topology, baseline and decision attributes for "METHOD /route".
 *
 * Mounted with `app.use()` it runs before routing, so it enriches by request path
 * first and again with the matched route template (e.g. `/orders/:id`) just
 * before the response ends.
 *
 * Usage:
 * ```ts
 * import { AgentTelEngine, expressMiddleware } from '@agenttel/node';
 * const engine = AgentTelEngine.fromConfigFile('agenttel.yml');
 * app.use(expressMiddleware({ engine }));
 * ```
 */
export function expressMiddleware(options: ExpressMiddlewareOptions = {}) {
  const topology = options.topology ?? options.engine?.topology;
  const sources = {
    baselineProvider: options.baselineProvider ?? options.engine?.baselineProvider,
    decisions: options.operations ?? options.engine?.operations,
  };

  const resolve = (req: ExpressRequest): string =>
    options.routeResolver
      ? options.routeResolver(req)
      : req.route?.path !== undefined
        ? `${req.baseUrl ?? ''}${req.route.path}`
        : req.path;

  return (req: ExpressRequest, res: ExpressResponse, next: NextFunction): void => {
    const span = trace.getActiveSpan();
    if (!span) {
      next();
      return;
    }

    if (topology) enrichTopology(span, topology);

    const firstRoute = resolve(req);
    const found = enrichOperation(span, `${req.method} ${firstRoute}`, sources);

    // Route templates are only known after routing; re-check before the span ends.
    if (!found && !options.routeResolver && typeof res.end === 'function') {
      const end = res.end;
      res.end = function patchedEnd(this: unknown, ...args: unknown[]) {
        res.end = end;
        reEnrich(span, req, firstRoute, resolve, sources);
        return end.apply(this, args);
      };
    }

    next();
  };
}

function reEnrich(
  span: Span,
  req: ExpressRequest,
  firstRoute: string,
  resolve: (req: ExpressRequest) => string,
  sources: Parameters<typeof enrichOperation>[2],
): void {
  try {
    const route = resolve(req);
    if (route !== firstRoute) enrichOperation(span, `${req.method} ${route}`, sources);
  } catch {
    // never break the response because of telemetry
  }
}
