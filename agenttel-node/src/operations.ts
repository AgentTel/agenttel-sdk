import type { OperationConfig, ProfileConfig } from './config.js';

/** Decision context an agent needs to act safely on an operation. */
export interface DecisionContext {
  retryable: boolean;
  idempotent: boolean;
  runbookUrl?: string;
  fallbackDescription?: string;
  escalationLevel: string;
  safeToRestart: boolean;
}

/** Looks up decision context for a named operation. */
export interface DecisionProvider {
  getDecision(operationName: string): DecisionContext | undefined;
}

const DURATION_RE = /^\s*([0-9]*\.?[0-9]+)\s*(ms|s|m)?\s*$/i;
const PATH_PARAM_RE = /(^|\/):([A-Za-z_][A-Za-z0-9_]*)/g;

/** Parse a duration ("45ms", "1.5s", "2m") or a plain number (milliseconds). */
export function parseDurationMs(value: string | number | undefined | null): number | undefined {
  if (value === undefined || value === null || value === '') return undefined;
  if (typeof value === 'number') return value;
  const m = DURATION_RE.exec(String(value));
  if (!m) throw new Error(`agenttel: invalid duration ${JSON.stringify(value)} (expected e.g. "45ms" or 45)`);
  const unit = (m[2] ?? 'ms').toLowerCase();
  return parseFloat(m[1]) * (unit === 's' ? 1000 : unit === 'm' ? 60000 : 1);
}

/**
 * Normalize an operation key to the canonical "METHOD /route" form: strips
 * Spring-style [brackets], upper-cases the method, and rewrites `:param` path
 * segments to `{param}` so Express, Fastify, FastAPI and Go route templates share one key.
 */
export function normalizeOperationName(name: string): string {
  let n = name.trim();
  if (n.startsWith('[') && n.endsWith(']')) n = n.slice(1, -1).trim();
  const m = /^(\S+)\s+(\/.*)$/.exec(n);
  if (m) n = `${m[1].toUpperCase()} ${m[2].replace(PATH_PARAM_RE, '$1{$2}')}`;
  return n;
}

/** Resolves decision context from config: explicit operation values > profile > defaults. */
export class OperationRegistry implements DecisionProvider {
  private readonly ops = new Map<string, OperationConfig>();

  constructor(
    operations: Record<string, OperationConfig> = {},
    private readonly profiles: Record<string, ProfileConfig> = {},
  ) {
    for (const [name, op] of Object.entries(operations)) this.ops.set(normalizeOperationName(name), op);
  }

  /** Register or replace an operation's configuration. */
  register(name: string, op: OperationConfig): void {
    this.ops.set(normalizeOperationName(name), op);
  }

  getOperation(name: string): OperationConfig | undefined {
    return this.ops.get(normalizeOperationName(name));
  }

  operationNames(): string[] {
    return [...this.ops.keys()];
  }

  getDecision(name: string): DecisionContext | undefined {
    const op = this.getOperation(name);
    if (!op) return undefined;
    const profile = op.profile ? this.profiles[op.profile] : undefined;
    const pick = <K extends keyof ProfileConfig>(key: K, fallback: NonNullable<ProfileConfig[K]>) =>
      (op[key] ?? profile?.[key] ?? fallback) as NonNullable<ProfileConfig[K]>;
    return {
      retryable: pick('retryable', false),
      idempotent: pick('idempotent', false),
      runbookUrl: op.runbookUrl ?? profile?.runbookUrl,
      fallbackDescription: op.fallbackDescription ?? profile?.fallbackDescription,
      escalationLevel: pick('escalationLevel', 'auto_resolve'),
      safeToRestart: pick('safeToRestart', true),
    };
  }
}
