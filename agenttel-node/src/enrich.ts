import type { Span } from '@opentelemetry/api';
import * as attrs from './attributes.js';
import type { BaselineProvider } from './baseline/provider.js';
import type { DecisionProvider } from './operations.js';
import { normalizeOperationName } from './operations.js';
import type { TopologyRegistry } from './topology/registry.js';

/** Set topology attributes (team, tier, domain, on-call channel) on a span. */
export function enrichTopology(span: Span, t: TopologyRegistry): void {
  if (t.team) span.setAttribute(attrs.TOPOLOGY_TEAM, t.team);
  if (t.tier) span.setAttribute(attrs.TOPOLOGY_TIER, t.tier);
  if (t.domain) span.setAttribute(attrs.TOPOLOGY_DOMAIN, t.domain);
  if (t.onCallChannel) span.setAttribute(attrs.TOPOLOGY_ON_CALL_CHANNEL, t.onCallChannel);
}

/**
 * Set baseline and decision attributes for `operationName` ("METHOD /route").
 * Returns true if anything was found for the operation.
 */
export function enrichOperation(
  span: Span,
  operationName: string,
  sources: { baselineProvider?: BaselineProvider; decisions?: DecisionProvider },
): boolean {
  const name = normalizeOperationName(operationName);
  let found = false;

  const baseline = sources.baselineProvider?.getBaseline(name);
  if (baseline) {
    span.setAttribute(attrs.BASELINE_LATENCY_P50_MS, baseline.latencyP50Ms);
    span.setAttribute(attrs.BASELINE_LATENCY_P99_MS, baseline.latencyP99Ms);
    span.setAttribute(attrs.BASELINE_ERROR_RATE, baseline.errorRate);
    span.setAttribute(attrs.BASELINE_SOURCE, baseline.source);
    found = true;
  }

  const decision = sources.decisions?.getDecision(name);
  if (decision) {
    span.setAttribute(attrs.DECISION_RETRYABLE, decision.retryable);
    span.setAttribute(attrs.DECISION_IDEMPOTENT, decision.idempotent);
    span.setAttribute(attrs.DECISION_SAFE_TO_RESTART, decision.safeToRestart);
    span.setAttribute(attrs.DECISION_ESCALATION_LEVEL, decision.escalationLevel);
    span.setAttribute(attrs.DECISION_FALLBACK_AVAILABLE, !!decision.fallbackDescription);
    if (decision.runbookUrl) span.setAttribute(attrs.DECISION_RUNBOOK_URL, decision.runbookUrl);
    if (decision.fallbackDescription) {
      span.setAttribute(attrs.DECISION_FALLBACK_DESCRIPTION, decision.fallbackDescription);
    }
    found = true;
  }
  return found;
}
