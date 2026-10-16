"""AgentTel middleware for FastAPI/Starlette."""

from __future__ import annotations

import logging
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from starlette.routing import Match

from agenttel.engine import AgentTelEngine

logger = logging.getLogger("agenttel.fastapi")


def instrument_fastapi(
    app: Any,
    config_path: str = "agenttel.yml",
    engine: AgentTelEngine | None = None,
    tracer_provider: TracerProvider | None = None,
    instrument_http: bool = True,
) -> AgentTelEngine:
    """One-line integration for FastAPI apps.

    Loads ``agenttel.yml`` (unless ``engine`` is given), attaches the AgentTel span
    processor to ``tracer_provider`` -- or to the application's already registered
    SDK ``TracerProvider``, creating one only if none exists -- adds the AgentTel
    middleware, and (if ``opentelemetry-instrumentation-fastapi`` is installed and
    the app is not instrumented yet) instruments the app so server spans exist.

    Args:
        app: FastAPI application instance.
        config_path: Path to agenttel.yml configuration file.
        engine: Optional pre-configured engine. If None, one is created from config.
        tracer_provider: Optional SDK TracerProvider to attach to.
        instrument_http: Call ``FastAPIInstrumentor.instrument_app`` when available.

    Returns:
        The AgentTelEngine instance.
    """
    if engine is None:
        engine = AgentTelEngine.from_config(config_path)

    provider = engine.install(tracer_provider)
    # Added before the OTel middleware so that, on older instrumentation versions
    # that use add_middleware, the server span is already active when we run.
    app.add_middleware(AgentTelMiddleware, engine=engine)

    if instrument_http and not getattr(app, "_is_instrumented_by_opentelemetry", False):
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        except ImportError:
            logger.info(
                "opentelemetry-instrumentation-fastapi not installed; AgentTel will "
                "enrich server spans created by your own instrumentation"
            )
        else:
            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    return engine


class AgentTelMiddleware:
    """ASGI middleware that enriches the active server span with AgentTel attributes.

    HTTP instrumentations name the server span before routing (e.g. just "POST"),
    so the span processor cannot match it to a configured operation at start. This
    middleware resolves the route template and sets baseline and decision
    attributes for "METHOD /route" on the server span.
    """

    def __init__(self, app: Any, engine: AgentTelEngine) -> None:
        self.app = app
        self._engine = engine

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope.get("type") == "http":
            try:
                self._enrich(scope)
            except Exception:  # never break the request because of telemetry
                logger.debug("AgentTel span enrichment failed", exc_info=True)
        await self.app(scope, receive, send)

    def _enrich(self, scope: dict) -> None:
        span = trace.get_current_span()
        if not span.is_recording():
            return

        route_template = self._resolve_route(scope)
        if route_template:
            span.set_attribute("http.route", route_template)

        for key, value in self._engine.topology.get_topology_attributes().items():
            span.set_attribute(key, value)

        method = scope.get("method", "")
        path = route_template or scope.get("path", "")
        if method and path:
            self._engine.processor.enrich_operation(span, f"{method} {path}")

    @staticmethod
    def _resolve_route(scope: dict) -> str | None:
        """Resolve the route template from the FastAPI/Starlette router."""
        app = scope.get("app")
        for route in getattr(app, "routes", []) or []:
            try:
                match, _ = route.matches(scope)
            except Exception:
                continue
            if match == Match.FULL:
                return getattr(route, "path", None)
        return None
