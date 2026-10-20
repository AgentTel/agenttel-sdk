"""Auto-configuration for FastAPI integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agenttel.config import AgentTelConfig
from agenttel.engine import AgentTelEngine


def auto_configure(
    app: Any,
    config_path: str | Path = "agenttel.yml",
    service_name: str | None = None,
) -> AgentTelEngine:
    """Auto-configure AgentTel for a FastAPI application.

    Equivalent to :func:`agenttel.fastapi.instrument_fastapi`; ``service_name``
    is used as ``service.name`` if AgentTel has to create the TracerProvider.

    Args:
        app: FastAPI application instance.
        config_path: Path to agenttel.yml.
        service_name: Optional service name override.

    Returns:
        Configured AgentTelEngine.
    """
    from agenttel.fastapi.middleware import instrument_fastapi

    config = AgentTelConfig.from_yaml(config_path)
    if service_name:
        config.topology.service_name = service_name
    return instrument_fastapi(app, engine=AgentTelEngine(config))
