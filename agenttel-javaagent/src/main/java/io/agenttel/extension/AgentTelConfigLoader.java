package io.agenttel.extension;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import java.io.File;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Loads AgentTel configuration from external sources for the javaagent extension.
 *
 * <p>Configuration is resolved from (in priority order):
 * <ol>
 *   <li>Config file: {@code -Dagenttel.config.file=agenttel.yml} or
 *       {@code AGENTTEL_CONFIG_FILE} environment variable</li>
 *   <li>System properties: {@code -Dagenttel.topology.team=payments}</li>
 *   <li>Environment variables: {@code AGENTTEL_TOPOLOGY_TEAM=payments}</li>
 * </ol>
 *
 * <p>The config file uses the same YAML format as the Spring Boot starter:
 * <pre>
 * agenttel:
 *   topology:
 *     team: payments-platform
 *     tier: critical
 *   operations:
 *     "POST /api/payments":
 *       expected-latency-p50: "45ms"
 *       retryable: true
 * </pre>
 */
public final class AgentTelConfigLoader {

    private static final Logger logger = Logger.getLogger(AgentTelConfigLoader.class.getName());
    private static final ObjectMapper YAML_MAPPER = new ObjectMapper(new YAMLFactory());

    private AgentTelConfigLoader() {}

    /**
     * Loads configuration from config file, system properties, and environment variables.
     */
    public static AgentTelConfig load() {
        AgentTelConfig config = loadFromFile();
        applySystemPropertyOverrides(config);
        applyEnvironmentOverrides(config);
        return config;
    }

    /**
     * Loads configuration from a specific YAML file (for testing).
     */
    static AgentTelConfig loadFromFile(File file) {
        try {
            JsonNode root = YAML_MAPPER.readTree(file);
            // Support both bare config and config nested under "agenttel:" key
            JsonNode agenttelNode = root.has("agenttel") ? root.get("agenttel") : root;
            return YAML_MAPPER.treeToValue(agenttelNode, AgentTelConfig.class);
        } catch (IOException e) {
            throw new UncheckedIOException("Failed to parse AgentTel config file: " + file, e);
        }
    }

    private static AgentTelConfig loadFromFile() {
        String configPath = System.getProperty("agenttel.config.file");
        if (configPath == null || configPath.isEmpty()) {
            configPath = System.getenv("AGENTTEL_CONFIG_FILE");
        }
        if (configPath == null || configPath.isEmpty()) {
            // Try default locations
            File defaultFile = new File("agenttel.yml");
            if (defaultFile.exists()) {
                configPath = defaultFile.getAbsolutePath();
            }
        }

        if (configPath != null && !configPath.isEmpty()) {
            File file = new File(configPath);
            if (file.exists()) {
                logger.info("Loading AgentTel config from: " + file.getAbsolutePath());
                return loadFromFile(file);
            } else {
                logger.warning("AgentTel config file not found: " + configPath);
            }
        }

        logger.info("No AgentTel config file found, using defaults with system property/env overrides");
        return new AgentTelConfig();
    }

    private static void applySystemPropertyOverrides(AgentTelConfig config) {
        applyIfSet("agenttel.topology.team", config.getTopology()::setTeam);
        applyIfSet("agenttel.topology.tier", config.getTopology()::setTier);
        applyIfSet("agenttel.topology.domain", config.getTopology()::setDomain);
        applyIfSet("agenttel.topology.on-call-channel", config.getTopology()::setOnCallChannel);
        applyIfSet("agenttel.topology.repo-url", config.getTopology()::setRepoUrl);
        applyIfSet("agenttel.attributes.namespace", config.getAttributes()::setNamespace);

        String enabled = System.getProperty("agenttel.enabled");
        if (enabled != null) {
            config.setEnabled(Boolean.parseBoolean(enabled));
        }
    }

    private static void applyEnvironmentOverrides(AgentTelConfig config) {
        applyEnvIfSet("AGENTTEL_TOPOLOGY_TEAM", config.getTopology()::setTeam);
        applyEnvIfSet("AGENTTEL_TOPOLOGY_TIER", config.getTopology()::setTier);
        applyEnvIfSet("AGENTTEL_TOPOLOGY_DOMAIN", config.getTopology()::setDomain);
        applyEnvIfSet("AGENTTEL_TOPOLOGY_ON_CALL_CHANNEL", config.getTopology()::setOnCallChannel);
        applyEnvIfSet("AGENTTEL_TOPOLOGY_REPO_URL", config.getTopology()::setRepoUrl);
        applyEnvIfSet("AGENTTEL_ATTRIBUTES_NAMESPACE", config.getAttributes()::setNamespace);

        String enabled = System.getenv("AGENTTEL_ENABLED");
        if (enabled != null) {
            config.setEnabled(Boolean.parseBoolean(enabled));
        }
    }

    private static void applyIfSet(String key, java.util.function.Consumer<String> setter) {
        String value = System.getProperty(key);
        if (value != null && !value.isEmpty()) {
            setter.accept(value);
        }
    }

    private static void applyEnvIfSet(String key, java.util.function.Consumer<String> setter) {
        String value = System.getenv(key);
        if (value != null && !value.isEmpty()) {
            setter.accept(value);
        }
    }
}
