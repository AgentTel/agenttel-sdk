package io.agenttel.core.resource;

import io.agenttel.core.export.AttributeNamespaceMapper;
import io.agenttel.core.topology.TopologyRegistry;

/**
 * Static holder that bridges the SPI world with the Spring/programmatic world.
 * Set during initialization so the ResourceProvider SPI can access topology data.
 */
public final class AgentTelGlobalState {
    private AgentTelGlobalState() {}

    private static volatile TopologyRegistry topologyRegistry;
    private static volatile AttributeNamespaceMapper namespaceMapper = AttributeNamespaceMapper.LEGACY;

    public static void initialize(TopologyRegistry registry) {
        topologyRegistry = registry;
    }

    public static TopologyRegistry getTopologyRegistry() {
        return topologyRegistry;
    }

    /** Sets the {@code agenttel.attributes.namespace} mapping used for resources and events. */
    public static void setNamespaceMapper(AttributeNamespaceMapper mapper) {
        namespaceMapper = mapper == null ? AttributeNamespaceMapper.LEGACY : mapper;
    }

    public static AttributeNamespaceMapper getNamespaceMapper() {
        return namespaceMapper;
    }

    /** Resets state (for testing). */
    public static void reset() {
        topologyRegistry = null;
        namespaceMapper = AttributeNamespaceMapper.LEGACY;
    }
}
