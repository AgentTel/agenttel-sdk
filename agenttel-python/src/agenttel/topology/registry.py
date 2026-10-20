"""Central topology registry for service metadata."""

from __future__ import annotations

from agenttel.config import AgentTelConfig
from agenttel.models import ConsumerDescriptor, DependencyDescriptor


class TopologyRegistry:
    """Central registry for service topology metadata."""

    def __init__(self, config: AgentTelConfig) -> None:
        self._config = config
        self._dependencies: dict[str, DependencyDescriptor] = {}
        self._consumers: dict[str, ConsumerDescriptor] = {}
        self._load_from_config()

    def _load_from_config(self) -> None:
        """Load topology from configuration."""
        for dep_config in self._config.dependencies:
            descriptor = DependencyDescriptor(
                name=dep_config.name,
                type=dep_config.type,
                criticality=dep_config.criticality,
                protocol=dep_config.protocol,
                timeout_ms=dep_config.timeout_ms,
                circuit_breaker=dep_config.circuit_breaker,
                fallback=dep_config.fallback,
                health_endpoint=dep_config.health_endpoint,
            )
            self._dependencies[dep_config.name] = descriptor

        for con_config in self._config.consumers:
            descriptor = ConsumerDescriptor(
                name=con_config.name,
                pattern=con_config.pattern,
                sla_latency_ms=con_config.sla_latency_ms,
            )
            self._consumers[con_config.name] = descriptor

    @property
    def team(self) -> str:
        return self._config.topology.team

    @property
    def tier(self) -> str:
        return self._config.topology.tier.value

    @property
    def domain(self) -> str:
        return self._config.topology.domain

    @property
    def on_call_channel(self) -> str:
        return self._config.topology.on_call_channel

    def get_dependency(self, name: str) -> DependencyDescriptor | None:
        """Get a dependency descriptor by name."""
        return self._dependencies.get(name)

    def get_all_dependencies(self) -> list[DependencyDescriptor]:
        """Get all registered dependencies."""
        return list(self._dependencies.values())

    def get_consumer(self, name: str) -> ConsumerDescriptor | None:
        """Get a consumer descriptor by name."""
        return self._consumers.get(name)

    def get_all_consumers(self) -> list[ConsumerDescriptor]:
        """Get all registered consumers."""
        return list(self._consumers.values())

    def get_topology_attributes(self) -> dict[str, str]:
        """Get topology as OTel resource attributes."""
        from agenttel import attributes as attr

        attrs: dict[str, str] = {}
        if self._config.topology.team:
            attrs[attr.TOPOLOGY_TEAM] = self._config.topology.team
        if self._config.topology.tier:
            attrs[attr.TOPOLOGY_TIER] = self._config.topology.tier.value
        if self._config.topology.domain:
            attrs[attr.TOPOLOGY_DOMAIN] = self._config.topology.domain
        if self._config.topology.on_call_channel:
            attrs[attr.TOPOLOGY_ON_CALL_CHANNEL] = self._config.topology.on_call_channel
        if self._config.topology.repo_url:
            attrs[attr.TOPOLOGY_REPO_URL] = self._config.topology.repo_url
        return attrs
