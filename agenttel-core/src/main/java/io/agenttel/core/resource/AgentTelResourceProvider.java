package io.agenttel.core.resource;

import io.agenttel.api.attributes.AgentTelAttributes;
import io.agenttel.core.topology.TopologyRegistry;
import io.opentelemetry.sdk.autoconfigure.spi.ConfigProperties;
import io.opentelemetry.sdk.autoconfigure.spi.ResourceProvider;
import io.opentelemetry.sdk.resources.Resource;

/**
 * OTel ResourceProvider SPI implementation that adds AgentTel topology
 * attributes to the service's Resource.
 */
public class AgentTelResourceProvider implements ResourceProvider {

    @Override
    public Resource createResource(ConfigProperties config) {
        TopologyRegistry topology = AgentTelGlobalState.getTopologyRegistry();
        if (topology == null) {
            return Resource.empty();
        }

        var builder = Resource.builder();

        if (!topology.getTeam().isEmpty()) {
            builder.put(AgentTelAttributes.TOPOLOGY_TEAM, topology.getTeam());
        }
        builder.put(AgentTelAttributes.TOPOLOGY_TIER, topology.getTier().getValue());
        if (!topology.getDomain().isEmpty()) {
            builder.put(AgentTelAttributes.TOPOLOGY_DOMAIN, topology.getDomain());
        }
        if (!topology.getOnCallChannel().isEmpty()) {
            builder.put(AgentTelAttributes.TOPOLOGY_ON_CALL_CHANNEL, topology.getOnCallChannel());
        }
        if (!topology.getRepoUrl().isEmpty()) {
            builder.put(AgentTelAttributes.TOPOLOGY_REPO_URL, topology.getRepoUrl());
        }

        String dependenciesJson = topology.serializeDependenciesToJson();
        if (!"[]".equals(dependenciesJson)) {
            builder.put(AgentTelAttributes.TOPOLOGY_DEPENDENCIES, dependenciesJson);
        }

        String consumersJson = topology.serializeConsumersToJson();
        if (!"[]".equals(consumersJson)) {
            builder.put(AgentTelAttributes.TOPOLOGY_CONSUMERS, consumersJson);
        }

        return AgentTelGlobalState.getNamespaceMapper().map(builder.build());
    }
}
