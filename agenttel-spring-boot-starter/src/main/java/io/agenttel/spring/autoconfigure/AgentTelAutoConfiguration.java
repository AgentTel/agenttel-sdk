package io.agenttel.spring.autoconfigure;

import io.agenttel.api.BaselineSource;
import io.agenttel.api.ConsumptionPattern;
import io.agenttel.api.DependencyCriticality;
import io.agenttel.api.DependencyType;
import io.agenttel.api.EscalationLevel;
import io.agenttel.api.ServiceTier;
import io.agenttel.api.baseline.OperationBaseline;
import io.agenttel.api.topology.ConsumerDescriptor;
import io.agenttel.api.topology.DependencyDescriptor;
import io.agenttel.core.anomaly.AnomalyDetector;
import io.agenttel.core.anomaly.PatternMatcher;
import io.agenttel.core.baseline.DurationParser;
import io.agenttel.core.baseline.RollingBaselineProvider;
import io.agenttel.core.baseline.StaticBaselineProvider;
import io.agenttel.core.causality.CausalityTracker;
import io.agenttel.core.causality.OperationDependencyTracker;
import io.agenttel.core.engine.AgentTelEngine;
import io.agenttel.core.error.ErrorClassifier;
import io.agenttel.core.enrichment.AgentTelSpanProcessor;
import io.agenttel.core.enrichment.OperationContext;
import io.agenttel.core.enrichment.OperationContextRegistry;
import io.agenttel.core.resource.AgentTelGlobalState;
import io.agenttel.core.slo.SloTracker;
import io.agenttel.core.topology.TopologyRegistry;
import io.agenttel.core.export.AgentTelEnrichingSpanExporter;
import io.agenttel.core.export.AttributeNamespaceMapper;
import io.agenttel.core.export.AttributeNamespaceMode;
import io.agenttel.core.export.NamespaceMappingSpanExporter;
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.sdk.autoconfigure.spi.AutoConfigurationCustomizerProvider;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Auto-configuration for AgentTel in Spring Boot applications.
 */
@AutoConfiguration
@ConditionalOnProperty(prefix = "agenttel", name = "enabled", havingValue = "true", matchIfMissing = true)
@EnableConfigurationProperties(AgentTelProperties.class)
public class AgentTelAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public TopologyRegistry agentTelTopologyRegistry(AgentTelProperties props) {
        TopologyRegistry registry = new TopologyRegistry();

        // Populate from properties
        var topo = props.getTopology();
        if (!topo.getTeam().isEmpty()) {
            registry.setTeam(topo.getTeam());
        }
        try {
            registry.setTier(ServiceTier.fromValue(topo.getTier()));
        } catch (IllegalArgumentException e) {
            registry.setTier(ServiceTier.STANDARD);
        }
        if (!topo.getDomain().isEmpty()) {
            registry.setDomain(topo.getDomain());
        }
        if (!topo.getOnCallChannel().isEmpty()) {
            registry.setOnCallChannel(topo.getOnCallChannel());
        }
        if (!topo.getRepoUrl().isEmpty()) {
            registry.setRepoUrl(topo.getRepoUrl());
        }

        // Register dependencies from config
        for (var dep : props.getDependencies()) {
            registry.registerDependency(new DependencyDescriptor(
                    dep.getName(),
                    DependencyType.fromValue(dep.getType()),
                    DependencyCriticality.fromValue(dep.getCriticality()),
                    dep.getProtocol(),
                    dep.getTimeoutMs(),
                    dep.isCircuitBreaker(),
                    dep.getFallback(),
                    dep.getHealthEndpoint()
            ));
        }

        // Register consumers from config
        for (var consumer : props.getConsumers()) {
            registry.registerConsumer(new ConsumerDescriptor(
                    consumer.getName(),
                    ConsumptionPattern.fromValue(consumer.getPattern()),
                    consumer.getSlaLatencyMs()
            ));
        }

        // Set global state for SPI-based ResourceProvider
        AgentTelGlobalState.initialize(registry);
        AgentTelGlobalState.setNamespaceMapper(new AttributeNamespaceMapper(
                AttributeNamespaceMode.fromValue(props.getAttributes().getNamespace())));

        return registry;
    }

    @Bean
    @ConditionalOnMissingBean
    public StaticBaselineProvider agentTelBaselineProvider() {
        return new StaticBaselineProvider();
    }

    @Bean
    @ConditionalOnMissingBean
    public RollingBaselineProvider agentTelRollingBaselineProvider(AgentTelProperties props) {
        var baselineProps = props.getBaselines();
        return new RollingBaselineProvider(
                baselineProps.getRollingWindowSize(),
                baselineProps.getRollingMinSamples());
    }

    @Bean
    @ConditionalOnMissingBean
    public OperationContextRegistry agentTelOperationContextRegistry(AgentTelProperties props,
                                                                       StaticBaselineProvider baselines) {
        OperationContextRegistry registry = new OperationContextRegistry();

        // Register operations from YAML config (runs before annotation scanning)
        for (var entry : props.getOperations().entrySet()) {
            String operationName = entry.getKey();
            var op = entry.getValue();

            // Resolve profile defaults if referenced
            AgentTelProperties.ProfileProperties profile = null;
            if (!op.getProfile().isEmpty()) {
                profile = props.getProfiles().get(op.getProfile());
            }

            // Register baseline (baselines are always per-operation, not from profiles)
            double p50 = DurationParser.parseToMs(op.getExpectedLatencyP50());
            double p99 = DurationParser.parseToMs(op.getExpectedLatencyP99());
            double errorRate = op.getExpectedErrorRate();
            if (p50 > 0 || p99 > 0 || errorRate >= 0) {
                baselines.register(operationName, OperationBaseline.builder(operationName)
                        .latencyP50Ms(Math.max(p50, 0))
                        .latencyP99Ms(Math.max(p99, 0))
                        .errorRate(Math.max(errorRate, 0))
                        .source(BaselineSource.STATIC)
                        .build());
            }

            // Resolve decision context: profile defaults < per-operation explicit overrides.
            // Fields that differ from OperationProperties defaults are considered "explicitly set".
            boolean retryable, idempotent, safeToRestart;
            String runbookUrl, fallbackDesc, escalationStr;
            if (profile != null) {
                retryable = op.isRetryable() || profile.isRetryable();
                idempotent = op.isIdempotent() || profile.isIdempotent();
                safeToRestart = !op.isSafeToRestart() ? false : profile.isSafeToRestart();
                runbookUrl = !op.getRunbookUrl().isEmpty() ? op.getRunbookUrl() : profile.getRunbookUrl();
                fallbackDesc = !op.getFallbackDescription().isEmpty() ? op.getFallbackDescription() : profile.getFallbackDescription();
                escalationStr = !"auto_resolve".equals(op.getEscalationLevel()) ? op.getEscalationLevel() : profile.getEscalationLevel();
            } else {
                retryable = op.isRetryable();
                idempotent = op.isIdempotent();
                safeToRestart = op.isSafeToRestart();
                runbookUrl = op.getRunbookUrl();
                fallbackDesc = op.getFallbackDescription();
                escalationStr = op.getEscalationLevel();
            }

            EscalationLevel escalation;
            try {
                escalation = EscalationLevel.fromValue(escalationStr);
            } catch (IllegalArgumentException e) {
                escalation = EscalationLevel.AUTO_RESOLVE;
            }
            registry.register(operationName, new OperationContext(
                    retryable, idempotent, runbookUrl,
                    fallbackDesc, escalation, safeToRestart));
        }

        return registry;
    }

    @Bean
    @ConditionalOnMissingBean
    public AnomalyDetector agentTelAnomalyDetector(AgentTelProperties props) {
        return new AnomalyDetector(props.getAnomalyDetection().getZScoreThreshold());
    }

    @Bean
    @ConditionalOnMissingBean
    public PatternMatcher agentTelPatternMatcher() {
        return new PatternMatcher();
    }

    @Bean
    @ConditionalOnMissingBean
    public SloTracker agentTelSloTracker() {
        return new SloTracker();
    }

    @Bean
    @ConditionalOnMissingBean
    public ErrorClassifier agentTelErrorClassifier() {
        return new ErrorClassifier();
    }

    @Bean
    @ConditionalOnMissingBean
    public OperationDependencyTracker agentTelOperationDependencyTracker() {
        return new OperationDependencyTracker();
    }

    @Bean
    @ConditionalOnMissingBean
    public CausalityTracker agentTelCausalityTracker(OperationDependencyTracker dependencyTracker) {
        return new CausalityTracker(dependencyTracker);
    }

    @Bean
    @ConditionalOnMissingBean
    public AgentTelAnnotationBeanPostProcessor agentTelAnnotationBeanPostProcessor(
            TopologyRegistry topology,
            StaticBaselineProvider baselines,
            OperationContextRegistry operationContexts,
            AgentTelProperties props) {
        return new AgentTelAnnotationBeanPostProcessor(topology, baselines, operationContexts, props.getProfiles());
    }

    @Bean
    @ConditionalOnMissingBean
    public AgentOperationAspect agentOperationAspect(AgentTelEngine engine) {
        return new AgentOperationAspect(engine);
    }

    @Bean
    @ConditionalOnMissingBean
    public AgentTelEngine agentTelEngine(TopologyRegistry topology,
                                          StaticBaselineProvider baselines,
                                          RollingBaselineProvider rollingBaselines,
                                          OperationContextRegistry operationContexts,
                                          AnomalyDetector anomalyDetector,
                                          PatternMatcher patternMatcher,
                                          SloTracker sloTracker,
                                          CausalityTracker causalityTracker,
                                          OpenTelemetry otel) {
        return AgentTelEngine.builder()
                .topologyRegistry(topology)
                .baselineProvider(baselines)
                .rollingBaselines(rollingBaselines)
                .operationContexts(operationContexts)
                .anomalyDetector(anomalyDetector)
                .patternMatcher(patternMatcher)
                .sloTracker(sloTracker)
                .causalityTracker(causalityTracker)
                .openTelemetry(otel)
                .build();
    }

    @Bean
    public AgentTelSpanProcessor agentTelSpanProcessor(StaticBaselineProvider baselines,
                                                        OperationContextRegistry operationContexts,
                                                        AnomalyDetector anomalyDetector,
                                                        PatternMatcher patternMatcher,
                                                        RollingBaselineProvider rollingBaselines,
                                                        SloTracker sloTracker,
                                                        OperationDependencyTracker dependencyTracker,
                                                        CausalityTracker causalityTracker) {
        return new AgentTelSpanProcessor(
                baselines, operationContexts,
                anomalyDetector, patternMatcher, rollingBaselines, sloTracker, null,
                dependencyTracker, causalityTracker);
    }

    @Bean
    public AutoConfigurationCustomizerProvider agentTelOtelCustomizer(
            AgentTelSpanProcessor spanProcessor,
            RollingBaselineProvider rollingBaselines,
            SloTracker sloTracker,
            CausalityTracker causalityTracker,
            AnomalyDetector anomalyDetector,
            ErrorClassifier errorClassifier,
            TopologyRegistry topology) {
        // Register AgentTelSpanProcessor and enriching exporter with the OTel SDK.
        return customizer -> {
            customizer.addTracerProviderCustomizer(
                    (builder, config) -> builder.addSpanProcessor(spanProcessor));
            customizer.addSpanExporterCustomizer(
                    (exporter, config) -> new AgentTelEnrichingSpanExporter(
                            NamespaceMappingSpanExporter.wrap(
                                    exporter, AgentTelGlobalState.getNamespaceMapper()),
                            rollingBaselines, sloTracker, causalityTracker,
                            anomalyDetector, errorClassifier, topology));
        };
    }

    @Bean
    @ConditionalOnClass(name = "org.springframework.web.servlet.HandlerInterceptor")
    public WebMvcConfigurer agentTelWebMvcConfigurer(
            StaticBaselineProvider baselines,
            OperationContextRegistry operationContexts) {
        return new WebMvcConfigurer() {
            @Override
            public void addInterceptors(InterceptorRegistry registry) {
                // Enriches spans with baseline and decision attributes after route resolution.
                // At SpanProcessor.onStart(), the span name is just "POST" (HTTP method).
                // By the time this interceptor runs, the route is resolved and we can look up
                // the operation name (e.g., "POST /api/payments") for baseline/decision metadata.
                registry.addInterceptor(new AgentTelEnrichmentInterceptor(baselines, operationContexts));
            }
        };
    }
}
