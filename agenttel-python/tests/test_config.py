"""Tests for the shared AgentTel config format and legacy dialects."""

import logging

import pytest

from agenttel.config import AgentTelConfig, normalize_operation_name, parse_duration_ms
from agenttel.engine import AgentTelEngine


class TestCanonicalFormat:
    def test_spring_style_document(self):
        config = AgentTelConfig.from_dict(
            {
                "agenttel": {
                    "topology": {"team": "payments", "tier": "critical", "on-call-channel": "#oncall"},
                    "operations": {
                        "[POST /api/payments]": {
                            "expected-latency-p50": "45ms",
                            "expected-latency-p99": "1.5s",
                            "expected-error-rate": 0.001,
                            "retryable": True,
                            "runbook-url": "https://runbooks/payments",
                        }
                    },
                    "anomaly-detection": {"z-score-threshold": 2.5},
                }
            }
        )
        assert config.topology.on_call_channel == "#oncall"
        op = config.get_operation("POST /api/payments")
        assert op is not None
        assert op.latency_p50_ms == 45.0
        assert op.latency_p99_ms == 1500.0
        assert op.retryable is True
        assert config.anomaly_detection.z_score_threshold == 2.5

    def test_bare_and_bracketed_keys_are_equivalent(self):
        bare = AgentTelConfig.from_dict({"agenttel": {"operations": {"GET /x": {}}}})
        bracketed = AgentTelConfig.from_dict({"agenttel": {"operations": {"[GET /x]": {}}}})
        assert list(bare.operations) == list(bracketed.operations) == ["GET /x"]

    def test_numeric_latency_is_milliseconds(self):
        config = AgentTelConfig.from_dict(
            {"agenttel": {"operations": {"GET /x": {"expected-latency-p50": 45}}}}
        )
        assert config.get_operation("GET /x").latency_p50_ms == 45.0

    def test_no_deprecation_warning_for_canonical_form(self, caplog):
        with caplog.at_level(logging.WARNING, logger="agenttel.config"):
            AgentTelConfig.from_dict({"agenttel": {"topology": {"on-call-channel": "#x"}}})
        assert caplog.records == []


class TestLegacyDialects:
    def test_flat_camel_case_go_dialect(self, caplog):
        with caplog.at_level(logging.WARNING, logger="agenttel.config"):
            config = AgentTelConfig.from_dict(
                {
                    "topology": {"team": "t", "onCallChannel": "#c"},
                    "operations": {"POST /p": {"expectedLatencyP50": "45ms", "runbookUrl": "u"}},
                    "anomalyDetection": {"zScoreThreshold": 4},
                }
            )
        assert config.topology.on_call_channel == "#c"
        assert config.get_operation("POST /p").latency_p50_ms == 45.0
        assert config.get_operation("POST /p").runbook_url == "u"
        assert config.anomaly_detection.z_score_threshold == 4
        assert any("deprecated" in r.message for r in caplog.records)

    def test_node_operations_list_dialect(self):
        config = AgentTelConfig.from_dict(
            {
                "topology": {"on_call_channel": "#c"},
                "operations": [
                    {"name": "POST /p", "baseline_latency_p50_ms": 45, "baseline_error_rate": 0.01}
                ],
                "rolling_window_size": 50,
                "anomaly_zscore_threshold": 2.0,
            }
        )
        op = config.get_operation("POST /p")
        assert op.latency_p50_ms == 45.0
        assert op.expected_error_rate == 0.01
        assert config.baselines.rolling_window_size == 50
        assert config.anomaly_detection.z_score_threshold == 2.0


class TestOperationNames:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("[POST /api/payments]", "POST /api/payments"),
            ("post  /api/payments", "POST /api/payments"),
            ("GET /orders/:id", "GET /orders/{id}"),
            ("GET /orders/{id}", "GET /orders/{id}"),
            ("process-payment", "process-payment"),
        ],
    )
    def test_normalize(self, raw, expected):
        assert normalize_operation_name(raw) == expected

    @pytest.mark.parametrize(
        "raw,expected", [("45ms", 45.0), ("2s", 2000.0), ("1m", 60000.0), (45, 45.0), ("12", 12.0)]
    )
    def test_parse_duration(self, raw, expected):
        assert parse_duration_ms(raw) == expected

    def test_invalid_duration(self):
        with pytest.raises(ValueError):
            parse_duration_ms("fast")


class TestDecisionResolution:
    def test_profile_defaults_and_overrides(self):
        engine = AgentTelEngine(
            AgentTelConfig.from_dict(
                {
                    "agenttel": {
                        "profiles": {
                            "critical-write": {
                                "retryable": False,
                                "runbook-url": "https://profile",
                                "escalation-level": "page_oncall",
                            }
                        },
                        "operations": {
                            "[POST /p]": {"profile": "critical-write", "retryable": True},
                        },
                    }
                }
            )
        )
        ctx = engine.processor.resolve_operation_context("POST /p")
        assert ctx.retryable is True
        assert ctx.runbook_url == "https://profile"
        assert ctx.escalation_level.value == "page_oncall"
        assert engine.processor.resolve_operation_context("GET /unknown") is None
