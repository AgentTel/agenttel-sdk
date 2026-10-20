"""Tests for agentic observability."""

from agenttel.agentic.cost import AgentCostAggregator
from agenttel.agentic.quality import LoopDetector, QualityTracker
from agenttel.agentic.guardrail import GuardrailRecorder
from agenttel.enums import GuardrailAction


class TestAgentCostAggregator:
    def test_record_and_summary(self):
        agg = AgentCostAggregator()
        agg.record(input_tokens=1000, output_tokens=500, cost_usd=0.01)
        agg.record(input_tokens=2000, output_tokens=1000, cost_usd=0.02)

        summary = agg.summary()
        assert summary["total_input_tokens"] == 3000
        assert summary["total_output_tokens"] == 1500
        assert summary["llm_calls"] == 2
        assert summary["total_cost_usd"] == 0.03

    def test_reset(self):
        agg = AgentCostAggregator()
        agg.record(input_tokens=1000, output_tokens=500)
        agg.reset()
        assert agg.summary()["llm_calls"] == 0


class TestLoopDetector:
    def test_no_loop(self):
        detector = LoopDetector(max_repetitions=3)
        for action in ["search", "analyze", "report"]:
            result = detector.record_action(action)
            assert not result.detected

    def test_detect_repeated_action(self):
        detector = LoopDetector(max_repetitions=3)
        detector.record_action("search")
        detector.record_action("search")
        result = detector.record_action("search")
        assert result.detected
        assert result.pattern == "search"

    def test_reset(self):
        detector = LoopDetector(max_repetitions=3)
        detector.record_action("search")
        detector.record_action("search")
        detector.reset()
        result = detector.record_action("search")
        assert not result.detected


class TestQualityTracker:
    def test_goal_tracking(self):
        tracker = QualityTracker()
        tracker.record_goal(True)
        tracker.record_goal(True)
        tracker.record_goal(False)

        summary = tracker.summary()
        assert summary["goals_attempted"] == 3
        assert summary["goals_achieved"] == 2
        assert abs(summary["success_rate"] - 2 / 3) < 0.01


class TestGuardrailRecorder:
    def test_record_event(self):
        recorder = GuardrailRecorder()
        event = recorder.record(
            name="content-filter",
            action=GuardrailAction.BLOCK,
            reason="PII detected",
        )
        assert event.name == "content-filter"
        assert event.action == GuardrailAction.BLOCK
        assert recorder.get_block_count() == 1

    def test_multiple_events(self):
        recorder = GuardrailRecorder()
        recorder.record("filter-1", GuardrailAction.BLOCK, "reason 1")
        recorder.record("filter-2", GuardrailAction.WARN, "reason 2")
        recorder.record("filter-3", GuardrailAction.LOG, "reason 3")

        assert len(recorder.get_events()) == 3
        assert recorder.get_block_count() == 1


class TestAgentTracerEmission:
    def test_invocation_emits_canonical_agentic_keys(self, span_exporter):
        from agenttel import agentic_attributes as aa
        from agenttel.agentic.tracer import AgentTracer
        from agenttel.enums import StepType

        tracer = AgentTracer.create().agent_name("responder").framework("custom").build()
        with tracer.invoke("diagnose latency") as invocation:
            with invocation.step(StepType.THOUGHT, "analyzing"):
                pass
            with invocation.tool_call("get_health") as tool:
                tool.set_result("ok")
            invocation.complete(goal_achieved=True)

        spans = {s.name: s for s in span_exporter.get_finished_spans()}
        root = spans["agent.invoke responder"].attributes
        assert root[aa.AGENTIC_AGENT_NAME] == "responder"
        assert root[aa.AGENTIC_AGENT_FRAMEWORK] == "custom"
        assert root[aa.AGENTIC_INVOCATION_GOAL] == "diagnose latency"
        assert root[aa.AGENTIC_INVOCATION_STATUS] == "completed"
        assert root[aa.AGENTIC_INVOCATION_STEPS] == 2
        assert root[aa.AGENTIC_QUALITY_GOAL_ACHIEVED] is True

        tool_attrs = spans["agent.tool_call get_health"].attributes
        assert tool_attrs[aa.AGENTIC_STEP_TOOL_NAME] == "get_health"
        assert tool_attrs[aa.AGENTIC_STEP_TOOL_STATUS] == "success"

        for span in spans.values():
            for key in span.attributes:
                assert key.startswith("agenttel.agentic."), key

    def test_fail_marks_invocation_failed(self, span_exporter):
        from opentelemetry.trace import StatusCode

        from agenttel import agentic_attributes as aa
        from agenttel.agentic.tracer import AgentTracer

        tracer = AgentTracer.create().agent_name("responder").build()
        with tracer.invoke("goal") as invocation:
            invocation.fail(error_source="tool", error_message="timeout")

        (span,) = span_exporter.get_finished_spans()
        assert span.attributes[aa.AGENTIC_INVOCATION_STATUS] == "failed"
        assert span.attributes[aa.AGENTIC_ERROR_SOURCE] == "tool"
        assert span.status.status_code == StatusCode.ERROR
        assert span.status.description == "timeout"
