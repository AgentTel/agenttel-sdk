"""Tests for AgentTel semantic attributes."""

from agenttel import attributes as attr
from agenttel import agentic_attributes as aa


class TestAgentTelAttributes:
    def test_topology_attributes_have_correct_prefix(self):
        assert attr.TOPOLOGY_TEAM == "agenttel.topology.team"
        assert attr.TOPOLOGY_TIER == "agenttel.topology.tier"
        assert attr.TOPOLOGY_DOMAIN == "agenttel.topology.domain"

    def test_topology_relationship_attributes(self):
        assert attr.TOPOLOGY_DEPENDENCIES == "agenttel.topology.dependencies"
        assert attr.TOPOLOGY_CONSUMERS == "agenttel.topology.consumers"

    def test_baseline_attributes(self):
        assert attr.BASELINE_LATENCY_P50_MS == "agenttel.baseline.latency_p50_ms"
        assert attr.BASELINE_LATENCY_P99_MS == "agenttel.baseline.latency_p99_ms"
        assert attr.BASELINE_SOURCE == "agenttel.baseline.source"

    def test_anomaly_attributes(self):
        assert attr.ANOMALY_DETECTED == "agenttel.anomaly.detected"
        assert attr.ANOMALY_SCORE == "agenttel.anomaly.score"
        assert attr.ANOMALY_LATENCY_Z_SCORE == "agenttel.anomaly.latency_z_score"
        assert attr.ANOMALY_Z_SCORE == attr.ANOMALY_LATENCY_Z_SCORE  # deprecated alias

    def test_slo_attributes(self):
        assert attr.SLO_NAME == "agenttel.slo.name"
        assert attr.SLO_TARGET == "agenttel.slo.target"
        assert attr.SLO_BUDGET_REMAINING == "agenttel.slo.budget_remaining"

    def test_genai_attributes(self):
        assert attr.GENAI_COST_USD == "agenttel.genai.cost_usd"
        assert attr.GENAI_FRAMEWORK == "agenttel.genai.framework"

    def test_all_attributes_have_agenttel_prefix(self):
        for name in dir(attr):
            if name.isupper() and not name.startswith("_"):
                value = getattr(attr, name)
                assert value.startswith("agenttel."), f"{name}={value} missing prefix"


class TestAgenticAttributes:
    def test_agent_identity_attributes(self):
        assert aa.AGENTIC_AGENT_NAME == "agenttel.agentic.agent.name"
        assert aa.AGENTIC_AGENT_TYPE == "agenttel.agentic.agent.type"
        assert aa.AGENTIC_AGENT_FRAMEWORK == "agenttel.agentic.agent.framework"

    def test_invocation_attributes(self):
        assert aa.AGENTIC_INVOCATION_ID == "agenttel.agentic.invocation.id"
        assert aa.AGENTIC_INVOCATION_GOAL == "agenttel.agentic.invocation.goal"
        assert aa.AGENTIC_INVOCATION_STATUS == "agenttel.agentic.invocation.status"

    def test_cost_attributes(self):
        assert aa.AGENTIC_COST_TOTAL_USD == "agenttel.agentic.cost.total_usd"
        assert aa.AGENTIC_COST_INPUT_TOKENS == "agenttel.agentic.cost.input_tokens"

    def test_deprecated_aliases_point_at_canonical_keys(self):
        assert aa.AGENT_NAME == aa.AGENTIC_AGENT_NAME
        assert aa.STEP_TOOL_NAME == aa.AGENTIC_STEP_TOOL_NAME
        assert aa.ORCHESTRATION_STAGE_COUNT == aa.AGENTIC_ORCHESTRATION_TOTAL_STAGES

    def test_all_agentic_attributes_use_agentic_namespace(self):
        for name in dir(aa):
            if name.isupper() and not name.startswith("_"):
                value = getattr(aa, name)
                assert value.startswith("agenttel.agentic."), f"{name}={value}"

    def test_all_agentic_attributes_have_prefix(self):
        for name in dir(aa):
            if name.isupper() and not name.startswith("_"):
                value = getattr(aa, name)
                assert value.startswith("agenttel."), f"{name}={value} missing prefix"
