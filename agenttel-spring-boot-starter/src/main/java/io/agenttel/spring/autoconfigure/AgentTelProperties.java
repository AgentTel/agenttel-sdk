package io.agenttel.spring.autoconfigure;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Configuration properties for AgentTel.
 * Bind to the {@code agenttel.*} namespace in application.yml.
 */
@ConfigurationProperties(prefix = "agenttel")
public class AgentTelProperties {

    private boolean enabled = true;
    private TopologyProperties topology = new TopologyProperties();
    private List<DependencyProperties> dependencies = new ArrayList<>();
    private List<ConsumerProperties> consumers = new ArrayList<>();
    private Map<String, ProfileProperties> profiles = new LinkedHashMap<>();
    private Map<String, OperationProperties> operations = new LinkedHashMap<>();
    private BaselineProperties baselines = new BaselineProperties();
    private AnomalyDetectionProperties anomalyDetection = new AnomalyDetectionProperties();
    private AttributesProperties attributes = new AttributesProperties();
    private DeploymentProperties deployment = new DeploymentProperties();
    private Map<String, List<String>> agentRoles = new LinkedHashMap<>();
    private AgenticProperties agentic = new AgenticProperties();

    public boolean isEnabled() { return enabled; }
    public void setEnabled(boolean enabled) { this.enabled = enabled; }
    public TopologyProperties getTopology() { return topology; }
    public void setTopology(TopologyProperties topology) { this.topology = topology; }
    public List<DependencyProperties> getDependencies() { return dependencies; }
    public void setDependencies(List<DependencyProperties> dependencies) { this.dependencies = dependencies; }
    public List<ConsumerProperties> getConsumers() { return consumers; }
    public void setConsumers(List<ConsumerProperties> consumers) { this.consumers = consumers; }
    public Map<String, ProfileProperties> getProfiles() { return profiles; }
    public void setProfiles(Map<String, ProfileProperties> profiles) { this.profiles = profiles; }
    public Map<String, OperationProperties> getOperations() { return operations; }
    public void setOperations(Map<String, OperationProperties> operations) { this.operations = operations; }
    public BaselineProperties getBaselines() { return baselines; }
    public void setBaselines(BaselineProperties baselines) { this.baselines = baselines; }
    public AnomalyDetectionProperties getAnomalyDetection() { return anomalyDetection; }
    public void setAnomalyDetection(AnomalyDetectionProperties anomalyDetection) { this.anomalyDetection = anomalyDetection; }
    public AttributesProperties getAttributes() { return attributes; }
    public void setAttributes(AttributesProperties attributes) { this.attributes = attributes; }
    public DeploymentProperties getDeployment() { return deployment; }
    public void setDeployment(DeploymentProperties deployment) { this.deployment = deployment; }
    public Map<String, List<String>> getAgentRoles() { return agentRoles; }
    public void setAgentRoles(Map<String, List<String>> agentRoles) { this.agentRoles = agentRoles; }
    public AgenticProperties getAgentic() { return agentic; }
    public void setAgentic(AgenticProperties agentic) { this.agentic = agentic; }

    public static class TopologyProperties {
        private String team = "";
        private String tier = "standard";
        private String domain = "";
        private String onCallChannel = "";
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

    public static class DependencyProperties {
        private String name;
        private String type;
        private String criticality = "required";
        private String protocol = "";
        private int timeoutMs = 0;
        private boolean circuitBreaker = false;
        private String fallback = "";
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

    public static class ConsumerProperties {
        private String name;
        private String pattern = "sync";
        private int slaLatencyMs = 0;

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getPattern() { return pattern; }
        public void setPattern(String pattern) { this.pattern = pattern; }
        public int getSlaLatencyMs() { return slaLatencyMs; }
        public void setSlaLatencyMs(int slaLatencyMs) { this.slaLatencyMs = slaLatencyMs; }
    }

    public static class BaselineProperties {
        private String source = "static";
        private int rollingWindowSize = 1000;
        private int rollingMinSamples = 10;

        public String getSource() { return source; }
        public void setSource(String source) { this.source = source; }
        public int getRollingWindowSize() { return rollingWindowSize; }
        public void setRollingWindowSize(int rollingWindowSize) { this.rollingWindowSize = rollingWindowSize; }
        public int getRollingMinSamples() { return rollingMinSamples; }
        public void setRollingMinSamples(int rollingMinSamples) { this.rollingMinSamples = rollingMinSamples; }
    }

    public static class AnomalyDetectionProperties {
        private boolean enabled = true;
        private double zScoreThreshold = 3.0;

        public boolean isEnabled() { return enabled; }
        public void setEnabled(boolean enabled) { this.enabled = enabled; }
        public double getZScoreThreshold() { return zScoreThreshold; }
        public void setZScoreThreshold(double zScoreThreshold) { this.zScoreThreshold = zScoreThreshold; }
    }

    public static class AttributesProperties {
        /** Attribute names to emit: legacy (agenttel.*), standard, or both. */
        private String namespace = "legacy";

        public String getNamespace() { return namespace; }
        public void setNamespace(String namespace) { this.namespace = namespace; }
    }

    public static class DeploymentProperties {
        private boolean emitOnStartup = true;
        private String version = "";
        private String commitSha = "";

        public boolean isEmitOnStartup() { return emitOnStartup; }
        public void setEmitOnStartup(boolean emitOnStartup) { this.emitOnStartup = emitOnStartup; }
        public String getVersion() { return version; }
        public void setVersion(String version) { this.version = version; }
        public String getCommitSha() { return commitSha; }
        public void setCommitSha(String commitSha) { this.commitSha = commitSha; }
    }

    /**
     * Reusable sets of operational defaults.
     * Profiles define decision context (retry policy, escalation, etc.) that can be
     * referenced by multiple operations to reduce config repetition.
     */
    public static class ProfileProperties {
        private boolean retryable = false;
        private boolean idempotent = false;
        private String runbookUrl = "";
        private String fallbackDescription = "";
        private String escalationLevel = "auto_resolve";
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

    /**
     * Per-operation metadata: baselines and decision context.
     * Map key is the operation name (e.g., "POST /api/payments").
     */
    public static class OperationProperties {
        private String profile = "";
        private String expectedLatencyP50 = "";
        private String expectedLatencyP99 = "";
        private double expectedErrorRate = -1;
        private boolean retryable = false;
        private boolean idempotent = false;
        private String runbookUrl = "";
        private String fallbackDescription = "";
        private String escalationLevel = "auto_resolve";
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

    /**
     * Configuration for the agentic layer: agent identity, safety guardrails.
     * Bind to {@code agenttel.agentic.*}.
     */
    public static class AgenticProperties {
        private int loopThreshold = 3;
        private long defaultMaxSteps = 0;
        private Map<String, AgentProperties> agents = new LinkedHashMap<>();

        public int getLoopThreshold() { return loopThreshold; }
        public void setLoopThreshold(int loopThreshold) { this.loopThreshold = loopThreshold; }
        public long getDefaultMaxSteps() { return defaultMaxSteps; }
        public void setDefaultMaxSteps(long defaultMaxSteps) { this.defaultMaxSteps = defaultMaxSteps; }
        public Map<String, AgentProperties> getAgents() { return agents; }
        public void setAgents(Map<String, AgentProperties> agents) { this.agents = agents; }
    }

    /**
     * Per-agent configuration: identity and guardrails.
     * Map key is the agent name (e.g., "incident-responder").
     */
    public static class AgentProperties {
        private String type = "";
        private String framework = "";
        private String version = "";
        private long maxSteps = 0;
        private int loopThreshold = 0;
        private double costBudgetUsd = 0;

        public String getType() { return type; }
        public void setType(String type) { this.type = type; }
        public String getFramework() { return framework; }
        public void setFramework(String framework) { this.framework = framework; }
        public String getVersion() { return version; }
        public void setVersion(String version) { this.version = version; }
        public long getMaxSteps() { return maxSteps; }
        public void setMaxSteps(long maxSteps) { this.maxSteps = maxSteps; }
        public int getLoopThreshold() { return loopThreshold; }
        public void setLoopThreshold(int loopThreshold) { this.loopThreshold = loopThreshold; }
        public double getCostBudgetUsd() { return costBudgetUsd; }
        public void setCostBudgetUsd(double costBudgetUsd) { this.costBudgetUsd = costBudgetUsd; }
    }
}
