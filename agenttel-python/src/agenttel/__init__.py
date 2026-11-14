"""AgentTel Python SDK — AI-native telemetry for Python services."""

from agenttel.config import AgentTelConfig
from agenttel.engine import AgentTelEngine
from agenttel.export import (
    AttributeNamespaceMapper,
    AttributeNamespaceMode,
    NamespaceMappingSpanExporter,
)
from agenttel.processor import AgentTelSpanProcessor

__all__ = [
    "AgentTelConfig",
    "AgentTelEngine",
    "AgentTelSpanProcessor",
    "AttributeNamespaceMapper",
    "AttributeNamespaceMode",
    "NamespaceMappingSpanExporter",
]

__version__ = "0.4.0a1"
