"""FastAPI Payment Service with AgentTel Python SDK."""

from __future__ import annotations

import asyncio
import os
import random

import uvicorn
from fastapi import FastAPI

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes

from agenttel import AgentTelEngine
from agenttel.fastapi import instrument_fastapi
from agenttel.agent.mcp_server import McpServer, create_default_tools

# --- OTel Setup ---

otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: "fastapi-payment-service",
    ResourceAttributes.SERVICE_VERSION: "1.0.0",
})

exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("fastapi-payment-service")

# --- FastAPI App ---

app = FastAPI(title="FastAPI Payment Service")

# --- AgentTel Setup ---

engine = AgentTelEngine.from_config("agenttel.yml")
instrument_fastapi(app, engine=engine)

# --- MCP Server Setup ---

tool_registry = create_default_tools(engine)
mcp_server = McpServer(tool_registry, port=8091)

# --- Routes ---


@app.post("/api/payments")
async def create_payment() -> dict:
    """Create a new payment."""
    with tracer.start_as_current_span("POST /api/payments") as span:
        # Simulate processing latency (30-70ms)
        await asyncio.sleep((30 + random.random() * 40) / 1000)

        # Simulate occasional errors (~2% rate)
        if random.random() < 0.02:
            span.record_exception(Exception("Payment processing failed: insufficient funds"))
            span.set_status(trace.StatusCode.ERROR, "insufficient funds")
            return {"error": "insufficient_funds"}

        return {
            "id": f"pay_{random.randint(0, 99999)}",
            "status": "completed",
            "amount": 99.99,
        }


@app.get("/api/payments/{payment_id}")
async def get_payment(payment_id: str) -> dict:
    """Retrieve a payment by ID."""
    with tracer.start_as_current_span("GET /api/payments/{payment_id}"):
        # Simulate read latency (10-25ms)
        await asyncio.sleep((10 + random.random() * 15) / 1000)

        return {
            "id": payment_id,
            "status": "completed",
            "amount": 99.99,
        }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


# --- Lifecycle ---


@app.on_event("startup")
async def on_startup() -> None:
    """Start MCP server on startup."""
    await mcp_server.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Graceful shutdown."""
    provider.shutdown()


# --- Entrypoint ---

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"FastAPI Payment Service starting on :{port}")
    print("  POST /api/payments         - Create payment")
    print("  GET  /api/payments/{{id}}    - Get payment")
    print("  GET  /health               - Health check")
    print("  MCP server on :8091        - Agent tools")

    uvicorn.run(app, host="0.0.0.0", port=port)
