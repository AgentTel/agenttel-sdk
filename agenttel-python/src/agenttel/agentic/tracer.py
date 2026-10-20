"""AgentTracer — builder pattern API for agentic observability."""

from __future__ import annotations

import uuid
from opentelemetry import trace

from agenttel import agentic_attributes as aa
from agenttel.agentic.cost import AgentCostAggregator
from agenttel.agentic.scopes import AgentInvocation, Orchestration
from agenttel.enums import AgentType, OrchestrationPattern


class AgentTracer:
    """Builder pattern API for creating agentic observability spans.

    Usage:
        tracer = (AgentTracer.create()
            .agent_name("incident-responder")
            .agent_type(AgentType.SINGLE)
            .framework("langchain")
            .build())

        with tracer.invoke("diagnose high latency") as invocation:
            with invocation.step(StepType.THOUGHT, "analyzing"):
                ...
    """

    def __init__(
        self,
        otel_tracer: trace.Tracer,
        name: str = "",
        type: AgentType = AgentType.SINGLE,
        framework: str = "",
        version: str = "",
    ) -> None:
        self._tracer = otel_tracer
        self._name = name
        self._type = type
        self._framework = framework
        self._version = version
        self._cost_aggregator = AgentCostAggregator()

    @classmethod
    def create(cls, tracer: trace.Tracer | None = None) -> AgentTracerBuilder:
        """Create a new AgentTracer builder."""
        return AgentTracerBuilder(tracer)

    def invoke(self, goal: str) -> AgentInvocation:
        """Start a new agent invocation.

        Args:
            goal: The goal/objective of this invocation.

        Returns:
            AgentInvocation context manager.
        """
        invocation_id = str(uuid.uuid4())
        span = self._tracer.start_span(
            f"agent.invoke {self._name}",
            kind=trace.SpanKind.INTERNAL,
        )

        # Set agent identity attributes
        span.set_attribute(aa.AGENTIC_AGENT_NAME, self._name)
        span.set_attribute(aa.AGENTIC_AGENT_TYPE, self._type.value)
        if self._framework:
            span.set_attribute(aa.AGENTIC_AGENT_FRAMEWORK, self._framework)
        if self._version:
            span.set_attribute(aa.AGENTIC_AGENT_VERSION, self._version)

        # Set invocation attributes
        span.set_attribute(aa.AGENTIC_INVOCATION_ID, invocation_id)
        span.set_attribute(aa.AGENTIC_INVOCATION_GOAL, goal)

        return AgentInvocation(
            span=span,
            tracer=self._tracer,
            invocation_id=invocation_id,
            goal=goal,
            agent_name=self._name,
            cost_aggregator=self._cost_aggregator,
        )

    def orchestrate(self, pattern: OrchestrationPattern) -> Orchestration:
        """Start an orchestration span.

        Args:
            pattern: The orchestration pattern (sequential, parallel, etc.)

        Returns:
            Orchestration context manager.
        """
        span = self._tracer.start_span(
            f"agent.orchestrate {pattern.value}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_ORCHESTRATION_PATTERN, pattern.value)
        span.set_attribute(aa.AGENTIC_AGENT_NAME, self._name)

        return Orchestration(
            span=span,
            tracer=self._tracer,
            pattern=pattern,
        )

    def memory(
        self,
        operation: str,
        store_type: str,
        items: int = 0,
    ) -> trace.Span:
        """Create a memory access span."""
        span = self._tracer.start_span(
            f"agent.memory.{operation}",
            kind=trace.SpanKind.INTERNAL,
        )
        span.set_attribute(aa.AGENTIC_MEMORY_OPERATION, operation)
        span.set_attribute(aa.AGENTIC_MEMORY_STORE_TYPE, store_type)
        span.set_attribute(aa.AGENTIC_MEMORY_ITEMS, items)
        return span

    @property
    def cost_aggregator(self) -> AgentCostAggregator:
        return self._cost_aggregator


class AgentTracerBuilder:
    """Builder for AgentTracer."""

    def __init__(self, tracer: trace.Tracer | None = None) -> None:
        self._tracer = tracer or trace.get_tracer("agenttel.agentic")
        self._name = ""
        self._type = AgentType.SINGLE
        self._framework = ""
        self._version = ""

    def agent_name(self, name: str) -> AgentTracerBuilder:
        self._name = name
        return self

    def agent_type(self, type: AgentType) -> AgentTracerBuilder:
        self._type = type
        return self

    def framework(self, framework: str) -> AgentTracerBuilder:
        self._framework = framework
        return self

    def version(self, version: str) -> AgentTracerBuilder:
        self._version = version
        return self

    def build(self) -> AgentTracer:
        return AgentTracer(
            otel_tracer=self._tracer,
            name=self._name,
            type=self._type,
            framework=self._framework,
            version=self._version,
        )
