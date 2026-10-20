"""End-to-end: real uvicorn server + FastAPI + OTel instrumentation + AgentTel.

Mirrors the Spring Boot EnrichmentTest: one request, then assert the HTTP server
span carries topology, static baselines and decision attributes.
"""

import socket
import threading
import time

import httpx
import pytest
from opentelemetry import trace
from opentelemetry.trace import SpanKind

fastapi = pytest.importorskip("fastapi")
uvicorn = pytest.importorskip("uvicorn")
pytest.importorskip("opentelemetry.instrumentation.fastapi")

from agenttel.fastapi import instrument_fastapi  # noqa: E402

CONFIG = """
agenttel:
  topology:
    team: payments-platform
    tier: critical
    domain: commerce
    on-call-channel: "#payments-oncall"
  operations:
    "[POST /api/payments]":
      expected-latency-p50: 45ms
      expected-latency-p99: 200ms
      expected-error-rate: 0.001
      retryable: true
      idempotent: true
      runbook-url: https://wiki.example.com/runbooks/payments
      escalation-level: page_oncall
    "GET /api/payments/{payment_id}":
      expected-latency-p50: 15
      expected-latency-p99: 80
"""


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture()
def server_spans(tmp_path, span_exporter):
    config_path = tmp_path / "agenttel.yml"
    config_path.write_text(CONFIG)

    app = fastapi.FastAPI()

    @app.post("/api/payments")
    async def create_payment():
        return {"ok": True}

    @app.get("/api/payments/{payment_id}")
    async def get_payment(payment_id: str):
        return {"id": payment_id}

    provider_before = trace.get_tracer_provider()
    instrument_fastapi(app, config_path=str(config_path))
    # The app's (here: the test suite's) SDK provider is reused, not replaced.
    assert trace.get_tracer_provider() is provider_before

    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="off")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.02)
    assert server.started, "uvicorn did not start"

    def request(method: str, path: str) -> list:
        httpx.request(method, f"http://127.0.0.1:{port}{path}", timeout=5).raise_for_status()
        return [s for s in span_exporter.get_finished_spans() if s.kind == SpanKind.SERVER]

    yield request

    server.should_exit = True
    thread.join(timeout=10)


def test_server_span_has_topology_baseline_and_decisions(server_spans):
    span = server_spans("POST", "/api/payments")[-1]
    attrs = span.attributes

    assert span.name == "POST /api/payments"
    assert attrs["agenttel.topology.team"] == "payments-platform"
    assert attrs["agenttel.topology.on_call_channel"] == "#payments-oncall"
    assert span.resource.attributes["agenttel.topology.team"] == "payments-platform"
    assert attrs["agenttel.baseline.latency_p50_ms"] == 45.0
    assert attrs["agenttel.baseline.latency_p99_ms"] == 200.0
    assert attrs["agenttel.baseline.error_rate"] == 0.001
    assert attrs["agenttel.decision.retryable"] is True
    assert attrs["agenttel.decision.idempotent"] is True
    assert attrs["agenttel.decision.runbook_url"] == "https://wiki.example.com/runbooks/payments"
    assert attrs["agenttel.decision.escalation_level"] == "page_oncall"


def test_parameterized_route_uses_route_template(server_spans):
    span = server_spans("GET", "/api/payments/pay_123")[-1]
    assert span.attributes["http.route"] == "/api/payments/{payment_id}"
    assert span.attributes["agenttel.baseline.latency_p50_ms"] == 15.0
    assert span.attributes["agenttel.decision.retryable"] is False
