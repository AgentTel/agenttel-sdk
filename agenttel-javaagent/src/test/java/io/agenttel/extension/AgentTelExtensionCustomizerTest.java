package io.agenttel.extension;

import io.agenttel.api.EscalationLevel;
import io.agenttel.api.ServiceTier;
import io.agenttel.core.baseline.StaticBaselineProvider;
import io.agenttel.core.enrichment.OperationContext;
import io.agenttel.core.enrichment.OperationContextRegistry;
import io.agenttel.core.resource.AgentTelGlobalState;
import io.agenttel.core.topology.TopologyRegistry;
import org.junit.jupiter.api.Test;

import java.io.File;
import java.util.Objects;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Tests that the config loader correctly parses YAML and populates
 * topology, baselines, and operation contexts.
 */
class AgentTelExtensionCustomizerTest {

    @Test
    void loadsConfigFromYamlFile() {
        File configFile = new File(
                Objects.requireNonNull(getClass().getClassLoader().getResource("test-agenttel.yml")).getFile());
        AgentTelConfig config = AgentTelConfigLoader.loadFromFile(configFile);

        // Verify topology
        assertThat(config.getTopology().getTeam()).isEqualTo("payments-platform");
        assertThat(config.getTopology().getTier()).isEqualTo("critical");
        assertThat(config.getTopology().getDomain()).isEqualTo("commerce");
        assertThat(config.getTopology().getOnCallChannel()).isEqualTo("#payments-oncall");
        assertThat(config.getTopology().getRepoUrl()).isEqualTo("https://github.com/example/payment-service");

        // Verify dependencies
        assertThat(config.getDependencies()).hasSize(2);
        assertThat(config.getDependencies().get(0).getName()).isEqualTo("payment-gateway");
        assertThat(config.getDependencies().get(0).getType()).isEqualTo("external_api");
        assertThat(config.getDependencies().get(0).getTimeoutMs()).isEqualTo(5000);
        assertThat(config.getDependencies().get(0).isCircuitBreaker()).isTrue();

        // Verify consumers
        assertThat(config.getConsumers()).hasSize(1);
        assertThat(config.getConsumers().get(0).getName()).isEqualTo("notification-service");

        // Verify profiles
        assertThat(config.getProfiles()).containsKey("critical-write");
        assertThat(config.getProfiles().get("critical-write").isRetryable()).isFalse();
        assertThat(config.getProfiles().get("critical-write").getEscalationLevel()).isEqualTo("page_oncall");

        // Verify operations
        assertThat(config.getOperations()).containsKey("POST /api/payments");
        assertThat(config.getOperations().get("POST /api/payments").getExpectedLatencyP50()).isEqualTo("45ms");
        assertThat(config.getOperations().get("POST /api/payments").isRetryable()).isTrue();
        assertThat(config.getOperations().get("POST /api/payments").getProfile()).isEqualTo("critical-write");

        // Verify baseline config
        assertThat(config.getBaselines().getRollingWindowSize()).isEqualTo(500);
        assertThat(config.getBaselines().getRollingMinSamples()).isEqualTo(5);

        // Verify anomaly detection config
        assertThat(config.getAnomalyDetection().getZScoreThreshold()).isEqualTo(2.5);

        // Verify attribute namespace
        assertThat(config.getAttributes().getNamespace()).isEqualTo("both");
    }

    @Test
    void attributeNamespaceDefaultsToLegacy() {
        assertThat(new AgentTelConfig().getAttributes().getNamespace()).isEqualTo("legacy");
    }

    @Test
    void buildTopologyFromConfig() {
        File configFile = new File(
                Objects.requireNonNull(getClass().getClassLoader().getResource("test-agenttel.yml")).getFile());
        AgentTelConfig config = AgentTelConfigLoader.loadFromFile(configFile);

        // Build topology via the same code path as the extension
        TopologyRegistry topology = buildTopologyForTest(config);

        assertThat(topology.getTeam()).isEqualTo("payments-platform");
        assertThat(topology.getTier()).isEqualTo(ServiceTier.CRITICAL);
        assertThat(topology.getDomain()).isEqualTo("commerce");
        assertThat(topology.getOnCallChannel()).isEqualTo("#payments-oncall");
        assertThat(topology.getDependency("payment-gateway")).isPresent();
        assertThat(topology.getDependency("postgres-orders")).isPresent();
    }

    @Test
    void registersBaselinesFromConfig() {
        File configFile = new File(
                Objects.requireNonNull(getClass().getClassLoader().getResource("test-agenttel.yml")).getFile());
        AgentTelConfig config = AgentTelConfigLoader.loadFromFile(configFile);

        StaticBaselineProvider baselines = new StaticBaselineProvider();
        OperationContextRegistry opContexts = new OperationContextRegistry();
        registerOperationsForTest(config, baselines, opContexts);

        // Verify baselines
        assertThat(baselines.getBaseline("POST /api/payments")).isPresent();
        assertThat(baselines.getBaseline("POST /api/payments").get().latencyP50Ms()).isEqualTo(45.0);
        assertThat(baselines.getBaseline("POST /api/payments").get().latencyP99Ms()).isEqualTo(200.0);
        assertThat(baselines.getBaseline("POST /api/payments").get().errorRate()).isEqualTo(0.001);

        assertThat(baselines.getBaseline("GET /api/payments/{id}")).isPresent();
        assertThat(baselines.getBaseline("GET /api/payments/{id}").get().latencyP50Ms()).isEqualTo(15.0);
    }

    @Test
    void resolvedProfileMergeForOperationContext() {
        File configFile = new File(
                Objects.requireNonNull(getClass().getClassLoader().getResource("test-agenttel.yml")).getFile());
        AgentTelConfig config = AgentTelConfigLoader.loadFromFile(configFile);

        StaticBaselineProvider baselines = new StaticBaselineProvider();
        OperationContextRegistry opContexts = new OperationContextRegistry();
        registerOperationsForTest(config, baselines, opContexts);

        // POST /api/payments: profile=critical-write, operation overrides retryable=true
        OperationContext postCtx = opContexts.getContext("POST /api/payments").orElseThrow();
        assertThat(postCtx.isRetryable()).isTrue(); // operation overrides profile
        assertThat(postCtx.isIdempotent()).isFalse(); // profile default (false), not overridden
        assertThat(postCtx.getEscalationLevel()).isEqualTo(EscalationLevel.PAGE_ONCALL); // from profile
        assertThat(postCtx.isSafeToRestart()).isFalse(); // from profile
        assertThat(postCtx.getRunbookUrl()).isEqualTo("https://wiki/runbooks/process-payment");
        assertThat(postCtx.getFallbackDescription()).isEqualTo("Returns cached pricing from last successful gateway call");

        // GET /api/payments/{id}: profile=read-only, no operation overrides
        OperationContext getCtx = opContexts.getContext("GET /api/payments/{id}").orElseThrow();
        assertThat(getCtx.isRetryable()).isTrue(); // from profile
        assertThat(getCtx.isIdempotent()).isTrue(); // from profile
        assertThat(getCtx.getEscalationLevel()).isEqualTo(EscalationLevel.NOTIFY_TEAM); // from profile
        assertThat(getCtx.isSafeToRestart()).isTrue(); // from profile
    }

    // Extracted from AgentTelExtensionCustomizer for direct testing
    private static TopologyRegistry buildTopologyForTest(AgentTelConfig config) {
        TopologyRegistry registry = new TopologyRegistry();
        var topo = config.getTopology();
        if (!topo.getTeam().isEmpty()) registry.setTeam(topo.getTeam());
        try {
            registry.setTier(ServiceTier.fromValue(topo.getTier()));
        } catch (IllegalArgumentException e) {
            registry.setTier(ServiceTier.STANDARD);
        }
        if (!topo.getDomain().isEmpty()) registry.setDomain(topo.getDomain());
        if (!topo.getOnCallChannel().isEmpty()) registry.setOnCallChannel(topo.getOnCallChannel());

        for (var dep : config.getDependencies()) {
            registry.registerDependency(new io.agenttel.api.topology.DependencyDescriptor(
                    dep.getName(),
                    io.agenttel.api.DependencyType.fromValue(dep.getType()),
                    io.agenttel.api.DependencyCriticality.fromValue(dep.getCriticality()),
                    dep.getProtocol(), dep.getTimeoutMs(), dep.isCircuitBreaker(),
                    dep.getFallback(), dep.getHealthEndpoint()));
        }
        return registry;
    }

    private static void registerOperationsForTest(AgentTelConfig config,
                                                    StaticBaselineProvider baselines,
                                                    OperationContextRegistry opContexts) {
        for (var entry : config.getOperations().entrySet()) {
            String operationName = entry.getKey();
            var op = entry.getValue();

            AgentTelConfig.ProfileConfig profile = null;
            if (!op.getProfile().isEmpty()) {
                profile = config.getProfiles().get(op.getProfile());
            }

            double p50 = io.agenttel.core.baseline.DurationParser.parseToMs(op.getExpectedLatencyP50());
            double p99 = io.agenttel.core.baseline.DurationParser.parseToMs(op.getExpectedLatencyP99());
            double errorRate = op.getExpectedErrorRate();
            if (p50 > 0 || p99 > 0 || errorRate >= 0) {
                baselines.register(operationName, io.agenttel.api.baseline.OperationBaseline.builder(operationName)
                        .latencyP50Ms(Math.max(p50, 0))
                        .latencyP99Ms(Math.max(p99, 0))
                        .errorRate(Math.max(errorRate, 0))
                        .source(io.agenttel.api.BaselineSource.STATIC)
                        .build());
            }

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

            io.agenttel.api.EscalationLevel escalation;
            try {
                escalation = io.agenttel.api.EscalationLevel.fromValue(escalationStr);
            } catch (IllegalArgumentException e) {
                escalation = io.agenttel.api.EscalationLevel.AUTO_RESOLVE;
            }

            opContexts.register(operationName, new OperationContext(
                    retryable, idempotent, runbookUrl,
                    fallbackDesc, escalation, safeToRestart));
        }
    }
}
