package io.agenttel.extension;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Configuration POJO for AgentTel javaagent extension.
 * Mirrors the Spring Boot properties structure but is framework-independent.
 * Parsed from YAML config file by Jackson.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class AgentTelConfig {

    private boolean enabled = true;
    private TopologyConfig topology = new TopologyConfig();
    private List<DependencyConfig> dependencies = new ArrayList<>();
    private List<ConsumerConfig> consumers = new ArrayList<>();
    private Map<String, ProfileConfig> profiles = new LinkedHashMap<>();
    private Map<String, OperationConfig> operations = new LinkedHashMap<>();
    private BaselineConfig baselines = new BaselineConfig();
    @JsonProperty("anomaly-detection")
    private AnomalyDetectionConfig anomalyDetection = new AnomalyDetectionConfig();
    private AttributesConfig attributes = new AttributesConfig();

    public boolean isEnabled() { return enabled; }
    public void setEnabled(boolean enabled) { this.enabled = enabled; }
    public TopologyConfig getTopology() { return topology; }
    public void setTopology(TopologyConfig topology) { this.topology = topology; }
    public List<DependencyConfig> getDependencies() { return dependencies; }
    public void setDependencies(List<DependencyConfig> dependencies) { this.dependencies = dependencies; }
    public List<ConsumerConfig> getConsumers() { return consumers; }
    public void setConsumers(List<ConsumerConfig> consumers) { this.consumers = consumers; }
    public Map<String, ProfileConfig> getProfiles() { return profiles; }
    public void setProfiles(Map<String, ProfileConfig> profiles) { this.profiles = profiles; }
    public Map<String, OperationConfig> getOperations() { return operations; }
    public void setOperations(Map<String, OperationConfig> operations) { this.operations = operations; }
    public BaselineConfig getBaselines() { return baselines; }
    public void setBaselines(BaselineConfig baselines) { this.baselines = baselines; }
    public AnomalyDetectionConfig getAnomalyDetection() { return anomalyDetection; }
    public void setAnomalyDetection(AnomalyDetectionConfig anomalyDetection) { this.anomalyDetection = anomalyDetection; }
    public AttributesConfig getAttributes() { return attributes; }
    public void setAttributes(AttributesConfig attributes) { this.attributes = attributes; }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class TopologyConfig {
        private String team = "";
        private String tier = "standard";
        private String domain = "";
        @JsonProperty("on-call-channel")
        private String onCallChannel = "";
        @JsonProperty("repo-url")
        private String repoUrl = "";

        public String getTeam() { return team; }
        public void setTeam(String team) { this.team = team; }
        public String getTier() { return tier; }
        public void setTier(String tier) { this.tier = tier; }
        public String getDomain() { return domain; }
        public void setDomain(String domain) { this.domain = domain; }
        public String getOnCallChannel() { return onCallChannel; }
        public void setOnCallChannel(String onCallChannel) { this.onCallChannel = onCallChannel; }
        public String getRepoUrl() { return repoUrl; }
        public void setRepoUrl(String repoUrl) { this.repoUrl = repoUrl; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class DependencyConfig {
        private String name;
        private String type;
        private String criticality = "required";
        private String protocol = "";
        @JsonProperty("timeout-ms")
        private int timeoutMs = 0;
        @JsonProperty("circuit-breaker")
        private boolean circuitBreaker = false;
        private String fallback = "";
        @JsonProperty("health-endpoint")
        private String healthEndpoint = "";

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getType() { return type; }
        public void setType(String type) { this.type = type; }
        public String getCriticality() { return criticality; }
        public void setCriticality(String criticality) { this.criticality = criticality; }
        public String getProtocol() { return protocol; }
        public void setProtocol(String protocol) { this.protocol = protocol; }
        public int getTimeoutMs() { return timeoutMs; }
        public void setTimeoutMs(int timeoutMs) { this.timeoutMs = timeoutMs; }
        public boolean isCircuitBreaker() { return circuitBreaker; }
        public void setCircuitBreaker(boolean circuitBreaker) { this.circuitBreaker = circuitBreaker; }
        public String getFallback() { return fallback; }
        public void setFallback(String fallback) { this.fallback = fallback; }
        public String getHealthEndpoint() { return healthEndpoint; }
        public void setHealthEndpoint(String healthEndpoint) { this.healthEndpoint = healthEndpoint; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ConsumerConfig {
        private String name;
        private String pattern = "sync";
        @JsonProperty("sla-latency-ms")
        private int slaLatencyMs = 0;

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getPattern() { return pattern; }
        public void setPattern(String pattern) { this.pattern = pattern; }
        public int getSlaLatencyMs() { return slaLatencyMs; }
        public void setSlaLatencyMs(int slaLatencyMs) { this.slaLatencyMs = slaLatencyMs; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class BaselineConfig {
        @JsonProperty("rolling-window-size")
        private int rollingWindowSize = 1000;
        @JsonProperty("rolling-min-samples")
        private int rollingMinSamples = 10;

        public int getRollingWindowSize() { return rollingWindowSize; }
        public void setRollingWindowSize(int rollingWindowSize) { this.rollingWindowSize = rollingWindowSize; }
        public int getRollingMinSamples() { return rollingMinSamples; }
        public void setRollingMinSamples(int rollingMinSamples) { this.rollingMinSamples = rollingMinSamples; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class AnomalyDetectionConfig {
        private boolean enabled = true;
        @JsonProperty("z-score-threshold")
        private double zScoreThreshold = 3.0;

        public boolean isEnabled() { return enabled; }
        public void setEnabled(boolean enabled) { this.enabled = enabled; }
        public double getZScoreThreshold() { return zScoreThreshold; }
        public void setZScoreThreshold(double zScoreThreshold) { this.zScoreThreshold = zScoreThreshold; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class AttributesConfig {
        /** Attribute names to emit: legacy (agenttel.*), standard, or both. */
        private String namespace = "legacy";

        public String getNamespace() { return namespace; }
        public void setNamespace(String namespace) { this.namespace = namespace; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ProfileConfig {
        private boolean retryable = false;
        private boolean idempotent = false;
        @JsonProperty("runbook-url")
        private String runbookUrl = "";
        @JsonProperty("fallback-description")
        private String fallbackDescription = "";
        @JsonProperty("escalation-level")
        private String escalationLevel = "auto_resolve";
        @JsonProperty("safe-to-restart")
        private boolean safeToRestart = true;

        public boolean isRetryable() { return retryable; }
        public void setRetryable(boolean retryable) { this.retryable = retryable; }
        public boolean isIdempotent() { return idempotent; }
        public void setIdempotent(boolean idempotent) { this.idempotent = idempotent; }
        public String getRunbookUrl() { return runbookUrl; }
        public void setRunbookUrl(String runbookUrl) { this.runbookUrl = runbookUrl; }
        public String getFallbackDescription() { return fallbackDescription; }
        public void setFallbackDescription(String fallbackDescription) { this.fallbackDescription = fallbackDescription; }
        public String getEscalationLevel() { return escalationLevel; }
        public void setEscalationLevel(String escalationLevel) { this.escalationLevel = escalationLevel; }
        public boolean isSafeToRestart() { return safeToRestart; }
        public void setSafeToRestart(boolean safeToRestart) { this.safeToRestart = safeToRestart; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class OperationConfig {
        private String profile = "";
        @JsonProperty("expected-latency-p50")
        private String expectedLatencyP50 = "";
        @JsonProperty("expected-latency-p99")
        private String expectedLatencyP99 = "";
        @JsonProperty("expected-error-rate")
        private double expectedErrorRate = -1;
        private boolean retryable = false;
        private boolean idempotent = false;
        @JsonProperty("runbook-url")
        private String runbookUrl = "";
        @JsonProperty("fallback-description")
        private String fallbackDescription = "";
        @JsonProperty("escalation-level")
        private String escalationLevel = "auto_resolve";
        @JsonProperty("safe-to-restart")
        private boolean safeToRestart = true;

        public String getProfile() { return profile; }
        public void setProfile(String profile) { this.profile = profile; }
        public String getExpectedLatencyP50() { return expectedLatencyP50; }
        public void setExpectedLatencyP50(String expectedLatencyP50) { this.expectedLatencyP50 = expectedLatencyP50; }
        public String getExpectedLatencyP99() { return expectedLatencyP99; }
        public void setExpectedLatencyP99(String expectedLatencyP99) { this.expectedLatencyP99 = expectedLatencyP99; }
        public double getExpectedErrorRate() { return expectedErrorRate; }
        public void setExpectedErrorRate(double expectedErrorRate) { this.expectedErrorRate = expectedErrorRate; }
        public boolean isRetryable() { return retryable; }
        public void setRetryable(boolean retryable) { this.retryable = retryable; }
        public boolean isIdempotent() { return idempotent; }
        public void setIdempotent(boolean idempotent) { this.idempotent = idempotent; }
        public String getRunbookUrl() { return runbookUrl; }
        public void setRunbookUrl(String runbookUrl) { this.runbookUrl = runbookUrl; }
        public String getFallbackDescription() { return fallbackDescription; }
        public void setFallbackDescription(String fallbackDescription) { this.fallbackDescription = fallbackDescription; }
        public String getEscalationLevel() { return escalationLevel; }
        public void setEscalationLevel(String escalationLevel) { this.escalationLevel = escalationLevel; }
        public boolean isSafeToRestart() { return safeToRestart; }
        public void setSafeToRestart(boolean safeToRestart) { this.safeToRestart = safeToRestart; }
    }
}
