package io.agenttel.core.export;

import io.agenttel.api.ErrorCategory;
import io.agenttel.api.ServiceTier;
import io.agenttel.api.attributes.AgentTelAttributes;
import io.agenttel.core.anomaly.AnomalyDetector;
import io.agenttel.core.anomaly.AnomalyResult;
import io.agenttel.core.anomaly.IncidentPattern;
import io.agenttel.core.anomaly.PatternMatcher;
import io.agenttel.core.baseline.BaselineProvider;
import io.agenttel.core.baseline.RollingBaselineProvider;
import io.agenttel.core.baseline.RollingWindow;
import io.agenttel.core.causality.CausalityTracker;
import io.agenttel.core.enrichment.OperationContextRegistry;
import io.agenttel.core.error.ErrorClassifier;
import io.agenttel.core.slo.SloTracker;
import io.agenttel.core.topology.TopologyRegistry;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.trace.StatusCode;
import io.opentelemetry.sdk.common.CompletableResultCode;
import io.opentelemetry.sdk.trace.data.SpanData;
import io.opentelemetry.sdk.trace.export.SpanExporter;

import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 * Enriching SpanExporter that adds computed attributes to spans at export time.
 *
 * <p>Since {@code ReadableSpan} is immutable in {@code onEnd()}, enrichment attributes
 * computed from rolling baselines, anomaly detection, SLO tracking, error classification,
 * and causality analysis must be added at export time via delegating SpanData.
 *
 * <p>Attributes added:
 * <ul>
 *   <li>{@code agenttel.anomaly.*} — detection results</li>
 *   <li>{@code agenttel.slo.*} — budget remaining, burn rate</li>
 *   <li>{@code agenttel.error.*} — error classification</li>
 *   <li>{@code agenttel.cause.*} — causal analysis</li>
 *   <li>{@code agenttel.severity.*} — severity assessment</li>
 *   <li>{@code agenttel.baseline.sample_count/confidence} — baseline reliability</li>
 *   <li>{@code agenttel.baseline.*} and {@code agenttel.decision.*} for configured operations,
 *       when {@link #withOperationMetadata} is set and the span did not get them at start.
 *       HTTP server spans start with a provisional name (e.g. {@code POST}) and only get
 *       their route ({@code POST /api/payments}, {@code http.route}) after routing.</li>
 * </ul>
 */
public class AgentTelEnrichingSpanExporter implements SpanExporter {

    private final SpanExporter delegate;
    private final RollingBaselineProvider rollingBaselines;
    private final SloTracker sloTracker;
    private final CausalityTracker causalityTracker;
    private final AnomalyDetector anomalyDetector;
    private final ErrorClassifier errorClassifier;
    private final TopologyRegistry topology;
    private BaselineProvider staticBaselines;
    private OperationContextRegistry operationContexts;

    public AgentTelEnrichingSpanExporter(SpanExporter delegate,
                                          RollingBaselineProvider rollingBaselines,
                                          SloTracker sloTracker,
                                          CausalityTracker causalityTracker,
                                          AnomalyDetector anomalyDetector,
                                          ErrorClassifier errorClassifier,
                                          TopologyRegistry topology) {
        this.delegate = delegate;
        this.rollingBaselines = rollingBaselines;
        this.sloTracker = sloTracker;
        this.causalityTracker = causalityTracker;
        this.anomalyDetector = anomalyDetector;
        this.errorClassifier = errorClassifier;
        this.topology = topology;
    }

    /**
     * Also add static baseline and decision attributes at export time, resolved from the
     * final span name or {@code METHOD http.route}, for spans that missed them at start.
     */
    public AgentTelEnrichingSpanExporter withOperationMetadata(BaselineProvider staticBaselines,
                                                               OperationContextRegistry operationContexts) {
        this.staticBaselines = staticBaselines;
        this.operationContexts = operationContexts;
        return this;
    }

    @Override
    public CompletableResultCode export(Collection<SpanData> spans) {
        List<SpanData> enriched = new ArrayList<>(spans.size());
        for (SpanData span : spans) {
            enriched.add(enrich(span));
        }
        return delegate.export(enriched);
    }

    @Override
    public CompletableResultCode flush() {
        return delegate.flush();
    }

    @Override
    public CompletableResultCode shutdown() {
        return delegate.shutdown();
    }

    private SpanData enrich(SpanData span) {
        Map<AttributeKey<?>, Object> extra = new LinkedHashMap<>();
        String operationName = span.getName();
        double latencyMs = (double) (span.getEndEpochNanos() - span.getStartEpochNanos())
                / TimeUnit.MILLISECONDS.toNanos(1);
        boolean isError = span.getStatus().getStatusCode() == StatusCode.ERROR;

        // --- Static baselines + decisions missed at span start ---
        enrichOperationMetadata(extra, span);

        // --- Anomaly detection ---
        enrichAnomaly(extra, operationName, latencyMs, isError);

        // --- SLO context ---
        enrichSlo(extra, operationName);

        // --- Baseline confidence ---
        enrichBaselineConfidence(extra, operationName);

        // --- Error classification ---
        ErrorCategory errorCategory = null;
        if (isError) {
            errorCategory = enrichErrorClassification(extra, span);
        }

        // --- Causality analysis ---
        if (isError || !extra.isEmpty()) {
            enrichCausality(extra, operationName, errorCategory);
        }

        // --- Severity assessment ---
        enrichSeverity(extra, isError);

        if (extra.isEmpty()) {
            return span;
        }

        return new EnrichedSpanData(span, extra);
    }

    private void enrichOperationMetadata(Map<AttributeKey<?>, Object> extra, SpanData span) {
        if (staticBaselines == null && operationContexts == null) return;
        var attrs = span.getAttributes();
        boolean needBaseline = staticBaselines != null
                && attrs.get(AgentTelAttributes.BASELINE_SOURCE) == null;
        boolean needDecision = operationContexts != null
                && attrs.get(AgentTelAttributes.DECISION_RETRYABLE) == null;
        if (!needBaseline && !needDecision) return;

        List<String> candidates = new ArrayList<>(2);
        candidates.add(span.getName());
        String route = attrs.get(AttributeKey.stringKey("http.route"));
        String method = attrs.get(AttributeKey.stringKey("http.request.method"));
        if (method == null) method = attrs.get(AttributeKey.stringKey("http.method"));
        if (route != null && method != null) candidates.add(method + " " + route);

        for (String name : candidates) {
            if (needBaseline) {
                var baseline = staticBaselines.getBaseline(name);
                if (baseline.isPresent()) {
                    var b = baseline.get();
                    if (b.latencyP50Ms() > 0) extra.put(AgentTelAttributes.BASELINE_LATENCY_P50_MS, b.latencyP50Ms());
                    if (b.latencyP99Ms() > 0) extra.put(AgentTelAttributes.BASELINE_LATENCY_P99_MS, b.latencyP99Ms());
                    if (b.errorRate() >= 0) extra.put(AgentTelAttributes.BASELINE_ERROR_RATE, b.errorRate());
                    extra.put(AgentTelAttributes.BASELINE_SOURCE, b.source().getValue());
                    needBaseline = false;
                }
            }
            if (needDecision) {
                var context = operationContexts.getContext(name);
                if (context.isPresent()) {
                    var ctx = context.get();
                    extra.put(AgentTelAttributes.DECISION_RETRYABLE, ctx.isRetryable());
                    extra.put(AgentTelAttributes.DECISION_IDEMPOTENT, ctx.isIdempotent());
                    if (!ctx.getRunbookUrl().isEmpty()) {
                        extra.put(AgentTelAttributes.DECISION_RUNBOOK_URL, ctx.getRunbookUrl());
                    }
                    if (!ctx.getFallbackDescription().isEmpty()) {
                        extra.put(AgentTelAttributes.DECISION_FALLBACK_AVAILABLE, true);
                        extra.put(AgentTelAttributes.DECISION_FALLBACK_DESCRIPTION, ctx.getFallbackDescription());
                    }
                    extra.put(AgentTelAttributes.DECISION_ESCALATION_LEVEL, ctx.getEscalationLevel().getValue());
                    extra.put(AgentTelAttributes.DECISION_SAFE_TO_RESTART, ctx.isSafeToRestart());
                    needDecision = false;
                }
            }
        }
    }

    private void enrichAnomaly(Map<AttributeKey<?>, Object> extra,
                                String operationName, double latencyMs, boolean isError) {
        if (anomalyDetector == null || rollingBaselines == null) return;

        rollingBaselines.getSnapshot(operationName).ifPresent(snapshot -> {
            if (snapshot.stddev() > 0) {
                AnomalyResult result = anomalyDetector.evaluate(
                        "latency", latencyMs, snapshot.mean(), snapshot.stddev());
                extra.put(AgentTelAttributes.ANOMALY_DETECTED, result.isAnomaly());
                extra.put(AgentTelAttributes.ANOMALY_SCORE, result.anomalyScore());
                extra.put(AgentTelAttributes.ANOMALY_LATENCY_Z_SCORE, result.zScore());
            }
        });
    }

    private void enrichSlo(Map<AttributeKey<?>, Object> extra, String operationName) {
        if (sloTracker == null) return;

        for (SloTracker.SloStatus status : sloTracker.getStatuses()) {
            // Match SLOs that cover this operation (by name prefix or exact match)
            if (status.sloName().contains(operationName)
                    || operationName.contains(status.sloName().replace("-availability", "")
                    .replace("-latency-p99", ""))) {
                extra.put(AgentTelAttributes.SLO_BUDGET_REMAINING, status.budgetRemaining());
                extra.put(AgentTelAttributes.SLO_BURN_RATE, status.burnRate());
                break;
            }
        }
    }

    private void enrichBaselineConfidence(Map<AttributeKey<?>, Object> extra, String operationName) {
        if (rollingBaselines == null) return;

        rollingBaselines.getSnapshot(operationName).ifPresent(snapshot -> {
            if (!snapshot.isEmpty()) {
                extra.put(AgentTelAttributes.BASELINE_SAMPLE_COUNT, (long) snapshot.sampleCount());
                extra.put(AgentTelAttributes.BASELINE_CONFIDENCE, snapshot.confidence());
            }
        });
    }

    private ErrorCategory enrichErrorClassification(Map<AttributeKey<?>, Object> extra, SpanData span) {
        if (errorClassifier == null) return null;

        ErrorClassifier.ErrorClassification classification = errorClassifier.classify(span);
        if (classification == null) return null;

        extra.put(AgentTelAttributes.ERROR_CATEGORY, classification.category().getValue());
        if (!classification.rootException().isEmpty()) {
            extra.put(AgentTelAttributes.ERROR_ROOT_EXCEPTION, classification.rootException());
        }
        if (classification.dependency() != null) {
            extra.put(AgentTelAttributes.ERROR_DEPENDENCY, classification.dependency());
        }
        return classification.category();
    }

    private void enrichCausality(Map<AttributeKey<?>, Object> extra,
                                  String operationName, ErrorCategory errorCategory) {
        if (causalityTracker == null) return;

        CausalityTracker.CausalAnalysis analysis =
                causalityTracker.analyzeCause(operationName, errorCategory);

        if (analysis.confidence() > 0.2) {
            extra.put(AgentTelAttributes.CAUSE_HINT, analysis.causeHint());
            extra.put(AgentTelAttributes.CAUSE_CATEGORY, analysis.causeCategory());
            if (analysis.causeDependency() != null) {
                extra.put(AgentTelAttributes.CAUSE_DEPENDENCY, analysis.causeDependency());
            }
        }
    }

    private void enrichSeverity(Map<AttributeKey<?>, Object> extra, boolean isError) {
        Double anomalyScore = (Double) extra.get(AgentTelAttributes.ANOMALY_SCORE);
        if (anomalyScore != null) {
            extra.put(AgentTelAttributes.SEVERITY_ANOMALY_SCORE, anomalyScore);
        }

        Boolean anomalyDetected = (Boolean) extra.get(AgentTelAttributes.ANOMALY_DETECTED);
        String errorCategory = (String) extra.get(AgentTelAttributes.ERROR_CATEGORY);

        // Business impact assessment
        if (isError || (anomalyDetected != null && anomalyDetected)) {
            boolean isCriticalTier = topology != null
                    && topology.getTier() == ServiceTier.CRITICAL;
            extra.put(AgentTelAttributes.SEVERITY_USER_FACING, isCriticalTier);

            String impact;
            if (anomalyScore != null && anomalyScore > 0.8) {
                impact = "critical";
            } else if (isError && errorCategory != null
                    && !ErrorCategory.DATA_VALIDATION.getValue().equals(errorCategory)) {
                impact = isCriticalTier ? "high" : "medium";
            } else if (anomalyScore != null && anomalyScore > 0.5) {
                impact = "medium";
            } else {
                impact = "low";
            }
            extra.put(AgentTelAttributes.SEVERITY_BUSINESS_IMPACT, impact);
        }
    }
}
