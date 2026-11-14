"""The ``agenttel.attributes.namespace`` setting: emit ``agenttel.*`` names, standard
OpenTelemetry names, or both.

The mapping comes from :mod:`agenttel.namespaces`, generated from ``attributes.json``.
An existing value under the standard key always wins (a span that already has
``service.version`` or ``exception.type`` keeps it), and mapping is idempotent.
"""

from __future__ import annotations

import copy
import logging
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import Event, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.util import BoundedList
from opentelemetry.attributes import BoundedAttributes

from agenttel.namespaces import STANDARD_ATTRIBUTE_KEYS, STANDARD_EVENT_NAMES

logger = logging.getLogger("agenttel.export")

_PREFIX = "agenttel."


class AttributeNamespaceMode(str, Enum):
    """Which attribute names AgentTel emits, set with ``agenttel.attributes.namespace``."""

    LEGACY = "legacy"
    """Only the ``agenttel.*`` names (default)."""
    STANDARD = "standard"
    """Standard names in place of the ``agenttel.*`` names that have one."""
    BOTH = "both"
    """Both: the ``agenttel.*`` name and, where one exists, the standard name."""

    @classmethod
    def from_value(cls, value: str | AttributeNamespaceMode | None) -> AttributeNamespaceMode:
        """Parse a configured value case-insensitively; ``None`` or blank means legacy.

        Raises:
            ValueError: for any other value.
        """
        if isinstance(value, AttributeNamespaceMode):
            return value
        if value is None or not str(value).strip():
            return cls.LEGACY
        normalized = str(value).strip().lower()
        for mode in cls:
            if mode.value == normalized:
                return mode
        raise ValueError(
            f"Unknown agenttel.attributes.namespace {value!r} "
            "(expected legacy, standard or both)"
        )

    @classmethod
    def parse(cls, value: str | AttributeNamespaceMode | None) -> AttributeNamespaceMode:
        """Like :meth:`from_value`, but logs a warning and returns legacy for unknown values."""
        try:
            return cls.from_value(value)
        except ValueError as e:
            logger.warning("%s; falling back to 'legacy'", e)
            return cls.LEGACY


class AttributeNamespaceMapper:
    """Renames AgentTel attribute keys and event names according to the mode."""

    def __init__(
        self,
        mode: AttributeNamespaceMode | str | None = AttributeNamespaceMode.LEGACY,
        attribute_keys: Mapping[str, str] = STANDARD_ATTRIBUTE_KEYS,
        event_names: Mapping[str, str] = STANDARD_EVENT_NAMES,
    ) -> None:
        self._mode = AttributeNamespaceMode.parse(mode)
        self._attribute_keys = attribute_keys
        self._event_names = event_names

    @property
    def mode(self) -> AttributeNamespaceMode:
        return self._mode

    @property
    def is_legacy(self) -> bool:
        return self._mode is AttributeNamespaceMode.LEGACY

    def map_attributes(self, attributes: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
        """Return the attributes with mapped keys renamed (``standard``) or duplicated
        (``both``). Returns the same object when nothing changes."""
        if self.is_legacy or not attributes or not self._has_mapped_key(attributes):
            return attributes
        both = self._mode is AttributeNamespaceMode.BOTH
        out: dict[str, Any] = {}
        for key, value in attributes.items():
            standard = self._attribute_keys.get(key)
            if standard is None or both:
                out[key] = value
            if standard is not None and standard not in attributes:
                out[standard] = value
        return out

    def map_resource(self, resource: Resource) -> Resource:
        """Return the resource with its attributes mapped (same object if unchanged)."""
        mapped = self.map_attributes(resource.attributes)
        if mapped is resource.attributes:
            return resource
        return Resource(dict(mapped or {}), resource.schema_url)

    def map_event_name(self, name: str) -> str:
        """Return the standard event name in ``standard`` mode, otherwise ``name``.

        Events carry a single name, so ``both`` keeps the ``agenttel.*`` name.
        """
        if self._mode is not AttributeNamespaceMode.STANDARD or name is None:
            return name
        return self._event_names.get(name, name)

    def _has_mapped_key(self, attributes: Mapping[str, Any]) -> bool:
        return any(k.startswith(_PREFIX) and k in self._attribute_keys for k in attributes)


class NamespaceMappingSpanExporter(SpanExporter):
    """SpanExporter that applies the namespace setting to span attributes, span events
    and the span's resource before handing spans to the delegate.

    ``ReadableSpan`` is immutable once ended, so changed spans are passed on as
    mapped shallow copies; unchanged spans are passed through as-is.
    """

    def __init__(self, delegate: SpanExporter, mapper: AttributeNamespaceMapper) -> None:
        self._delegate = delegate
        self._mapper = mapper

    @property
    def delegate(self) -> SpanExporter:
        return self._delegate

    @property
    def mapper(self) -> AttributeNamespaceMapper:
        return self._mapper

    @staticmethod
    def wrap(delegate: SpanExporter, mapper: AttributeNamespaceMapper) -> SpanExporter:
        """Wrap ``delegate``, or return it unchanged in ``legacy`` mode or if already wrapped."""
        if mapper.is_legacy or isinstance(delegate, NamespaceMappingSpanExporter):
            return delegate
        return NamespaceMappingSpanExporter(delegate, mapper)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        return self._delegate.export([self.map_span(s) for s in spans])

    def shutdown(self) -> None:
        self._delegate.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._delegate.force_flush(timeout_millis)

    def map_span(self, span: ReadableSpan) -> ReadableSpan:
        """Return ``span`` with mapped attributes, events and resource."""
        # ReadableSpan properties return fresh views, so read each one once.
        orig_attributes, orig_resource, orig_events = span.attributes, span.resource, span.events
        attributes = self._mapper.map_attributes(orig_attributes)
        resource = self._mapper.map_resource(orig_resource) if orig_resource else orig_resource
        events = self._map_events(orig_events)
        if (
            attributes is orig_attributes
            and resource is orig_resource
            and events is orig_events
        ):
            return span
        # ReadableSpan's constructor takes no dropped-attribute/event counts and its
        # signature varies across opentelemetry-sdk versions, so copy the span and
        # replace only the three private fields. tests/test_namespace.py asserts these
        # fields exist, so an SDK upgrade that renames them fails loudly.
        mapped = copy.copy(span)
        if attributes is not orig_attributes:
            mapped._attributes = _bounded(  # type: ignore[attr-defined]
                attributes, getattr(span, "_attributes", None)
            )
        if resource is not orig_resource:
            mapped._resource = resource  # type: ignore[attr-defined]
        if events is not orig_events:
            mapped._events = _bounded_events(  # type: ignore[attr-defined]
                events, getattr(span, "_events", None)
            )
        return mapped

    def _map_events(self, events: Sequence[Event]) -> Sequence[Event]:
        out: list[Event] | None = None
        for i, event in enumerate(events):
            name = self._mapper.map_event_name(event.name)
            attributes = self._mapper.map_attributes(event.attributes)
            if name == event.name and attributes is event.attributes:
                if out is not None:
                    out.append(event)
                continue
            if out is None:
                out = list(events[:i]) if isinstance(events, (list, tuple)) else list(events)[:i]
            out.append(Event(name, attributes=attributes, timestamp=event.timestamp, limit=None))
        return events if out is None else tuple(out)


def _bounded(attributes: Mapping[str, Any] | None, original: Any) -> BoundedAttributes:
    """Immutable attributes without a length limit (``both`` may add keys), keeping
    the original dropped count."""
    bounded = BoundedAttributes(maxlen=None, attributes=attributes, immutable=True)
    bounded.dropped = getattr(original, "dropped", 0)
    return bounded


def _bounded_events(events: Sequence[Event], original: Any) -> Sequence[Event]:
    """Events as a BoundedList when the original was one, keeping its dropped count."""
    if not isinstance(original, BoundedList):
        return tuple(events)
    bounded = BoundedList(None)
    bounded.extend(events)
    bounded.dropped = original.dropped
    return bounded
