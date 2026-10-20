"""AgentTel configuration loader.

The canonical format is shared by every AgentTel SDK (JVM, Go, Node.js, Python)::

    agenttel:
      topology:
        team: payments-platform
        tier: critical
        on-call-channel: "#payments-oncall"
      operations:
        "[POST /api/payments]":          # brackets optional
          expected-latency-p50: 45ms     # duration string, or a number in ms
          expected-latency-p99: 200ms
          expected-error-rate: 0.001
          retryable: true
          runbook-url: https://wiki.example.com/runbooks/payments

Older dialects (no ``agenttel:`` root, snake_case or camelCase keys, and the
``operations`` list used by the Node.js SDK before 0.4.0) are still accepted and
logged as deprecated.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from agenttel.enums import (
    ConsumptionPattern,
    DependencyCriticality,
    DependencyType,
    EscalationLevel,
    ServiceTier,
    SloType,
)

logger = logging.getLogger("agenttel.config")


def _kebab(name: str) -> str:
    return name.replace("_", "-")


class _ConfigModel(BaseModel):
    """Base model: kebab-case keys in YAML, snake_case attributes in Python."""

    model_config = ConfigDict(alias_generator=_kebab, populate_by_name=True)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_DURATION_RE = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*(ms|s|m)?\s*$", re.IGNORECASE)
_PATH_PARAM_RE = re.compile(r"(^|/):([A-Za-z_][A-Za-z0-9_]*)")


def parse_duration_ms(value: str | int | float | None) -> float | None:
    """Parse a duration ("45ms", "1.5s", "2m") or a plain number (milliseconds)."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"invalid duration: {value!r}")
    if isinstance(value, (int, float)):
        return float(value)
    m = _DURATION_RE.match(str(value))
    if not m:
        raise ValueError(f"invalid duration: {value!r} (expected e.g. '45ms' or 45)")
    number, unit = float(m.group(1)), (m.group(2) or "ms").lower()
    return number * {"ms": 1.0, "s": 1000.0, "m": 60000.0}[unit]


def normalize_operation_name(name: str) -> str:
    """Normalize an operation key to the canonical "METHOD /route" form.

    Strips Spring-style ``[brackets]``, collapses whitespace, upper-cases the HTTP
    method, and rewrites ``:param`` path segments to ``{param}`` so that Express,
    Gin, FastAPI and net/http route templates all share one key.
    """
    n = name.strip()
    if n.startswith("[") and n.endswith("]"):
        n = n[1:-1].strip()
    parts = n.split(None, 1)
    if len(parts) == 2 and parts[1].startswith("/"):
        route = _PATH_PARAM_RE.sub(r"\1{\2}", parts[1])
        n = f"{parts[0].upper()} {route}"
    return n


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TopologyConfig(_ConfigModel):
    """Service topology configuration."""

    service_name: str = ""
    team: str = ""
    tier: ServiceTier = ServiceTier.STANDARD
    domain: str = ""
    on_call_channel: str = ""
    repo_url: str = ""
    service_version: str = ""


class DependencyConfig(_ConfigModel):
    """Dependency configuration."""

    name: str
    type: DependencyType = DependencyType.INTERNAL_SERVICE
    criticality: DependencyCriticality = DependencyCriticality.REQUIRED
    protocol: str | None = None
    timeout_ms: int = 5000
    circuit_breaker: bool = False
    fallback: str | None = None
    health_endpoint: str | None = None


class ConsumerConfig(_ConfigModel):
    """Consumer configuration."""

    name: str
    pattern: ConsumptionPattern = ConsumptionPattern.SYNC
    sla_latency_ms: int | None = None


class ProfileConfig(_ConfigModel):
    """Operation profile configuration (shared decision defaults)."""

    retryable: bool = False
    idempotent: bool = False
    runbook_url: str | None = None
    escalation_level: EscalationLevel = EscalationLevel.AUTO_RESOLVE
    safe_to_restart: bool = True
    fallback_description: str | None = None


class OperationConfig(_ConfigModel):
    """Per-operation configuration. Explicit values override the profile."""

    profile: str | None = None
    expected_latency_p50: str | float | None = None
    expected_latency_p99: str | float | None = None
    expected_error_rate: float | None = None
    retryable: bool | None = None
    idempotent: bool | None = None
    runbook_url: str | None = None
    escalation_level: EscalationLevel | None = None
    safe_to_restart: bool | None = None
    fallback_description: str | None = None

    def parse_latency_ms(self, value: str | float | None) -> float | None:
        """Parse latency like '80ms', '1s' or 80 to float milliseconds."""
        return parse_duration_ms(value)

    @property
    def latency_p50_ms(self) -> float | None:
        return parse_duration_ms(self.expected_latency_p50)

    @property
    def latency_p99_ms(self) -> float | None:
        return parse_duration_ms(self.expected_latency_p99)


class BaselineConfig(_ConfigModel):
    """Baseline configuration."""

    rolling_window_size: int = 1000
    rolling_min_samples: int = 10


class AnomalyDetectionConfig(_ConfigModel):
    """Anomaly detection configuration."""

    enabled: bool = True
    z_score_threshold: float = 3.0


class SloConfig(_ConfigModel):
    """SLO configuration."""

    name: str = ""
    target: float = 0.999
    type: SloType = SloType.AVAILABILITY


class DeploymentConfig(_ConfigModel):
    """Deployment configuration."""

    emit_on_startup: bool = True
    deployment_id: str | None = None
    version: str | None = None
    environment: str = "development"


class McpConfig(_ConfigModel):
    """MCP server configuration."""

    enabled: bool = False
    port: int = 8091
    host: str = "0.0.0.0"


class AgentRoleConfig(_ConfigModel):
    """Agent role permissions configuration."""

    tools: list[str] = []


class AgentTelConfig(_ConfigModel):
    """Root AgentTel configuration."""

    enabled: bool = True
    topology: TopologyConfig = TopologyConfig()
    dependencies: list[DependencyConfig] = []
    consumers: list[ConsumerConfig] = []
    profiles: dict[str, ProfileConfig] = {}
    operations: dict[str, OperationConfig] = {}
    baselines: BaselineConfig = BaselineConfig()
    anomaly_detection: AnomalyDetectionConfig = AnomalyDetectionConfig()
    slo: dict[str, SloConfig] = {}
    deployment: DeploymentConfig = DeploymentConfig()
    mcp: McpConfig = McpConfig()
    agent_roles: dict[str, AgentRoleConfig] = {}

    def get_operation(self, name: str) -> OperationConfig | None:
        """Look up an operation by name in any accepted key form."""
        key = normalize_operation_name(name)
        op = self.operations.get(key)
        if op is None:  # operations assigned after construction may be unnormalized
            op = next(
                (v for k, v in self.operations.items() if normalize_operation_name(k) == key),
                None,
            )
        return op

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AgentTelConfig:
        """Build configuration from a parsed YAML/JSON document."""
        return cls.model_validate(normalize_raw_config(data or {}))

    @classmethod
    def from_yaml(cls, path: str | Path) -> AgentTelConfig:
        """Load configuration from a YAML file. A missing file yields defaults."""
        path = Path(path)
        if not path.exists():
            return cls()
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls.from_dict(data)

    @classmethod
    def from_env(cls) -> AgentTelConfig:
        """Load configuration from $AGENTTEL_CONFIG or ./agenttel.yml."""
        config_path = os.environ.get("AGENTTEL_CONFIG", "agenttel.yml")
        return cls.from_yaml(config_path)

    def model_post_init(self, __context: Any) -> None:
        # Operations set programmatically get the same key normalization as YAML.
        if any(normalize_operation_name(k) != k for k in self.operations):
            self.operations = {normalize_operation_name(k): v for k, v in self.operations.items()}


# ---------------------------------------------------------------------------
# Raw document normalization (shared dialect + backward compatibility)
# ---------------------------------------------------------------------------

# Sections whose keys are user-chosen names, not schema keys.
_NAMED_MAPS = {"operations", "profiles", "slo", "agent-roles"}

# Legacy key spellings that are not a plain case conversion.
_LEGACY_OPERATION_KEYS = {
    "baseline-latency-p50-ms": "expected-latency-p50",
    "baseline-latency-p99-ms": "expected-latency-p99",
    "baseline-error-rate": "expected-error-rate",
}


def _to_kebab(key: str) -> str:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", key)
    return s.replace("_", "-").lower()


_ENTRY = object()  # marks the value of a user-named map entry


def _kebab_keys(value: Any, section: Any, legacy: set[str]) -> Any:
    """Recursively convert schema keys to kebab-case; keep user-chosen names."""
    if isinstance(value, list):
        return [_kebab_keys(v, None, legacy) for v in value]
    if not isinstance(value, dict):
        return value
    out: dict[str, Any] = {}
    for k, v in value.items():
        key = str(k)
        if section in _NAMED_MAPS:
            new_key = normalize_operation_name(key) if section == "operations" else key
            out[new_key] = _kebab_keys(v, _ENTRY, legacy)
            continue
        new_key = _to_kebab(key)
        if new_key != key:
            legacy.add(key)
        out[new_key] = _kebab_keys(v, new_key, legacy)
    return out


def normalize_raw_config(data: dict[str, Any]) -> dict[str, Any]:
    """Convert any supported dialect into the canonical kebab-case structure."""
    if "agenttel" in data and isinstance(data["agenttel"], dict):
        data = data["agenttel"]
    elif data:
        logger.warning(
            "agenttel config without a top-level 'agenttel:' key is deprecated; "
            "nest the configuration under 'agenttel:'"
        )

    legacy: set[str] = set()
    data = _kebab_keys(data, None, legacy)

    # Node.js < 0.4.0 flat keys.
    for old, new in (("rolling-window-size", "baselines"), ("rolling-min-samples", "baselines")):
        if old in data:
            data.setdefault(new, {})[old] = data.pop(old)
            legacy.add(old)
    if "anomaly-zscore-threshold" in data:
        data.setdefault("anomaly-detection", {})["z-score-threshold"] = data.pop(
            "anomaly-zscore-threshold"
        )
        legacy.add("anomaly_zscore_threshold")

    ops = data.get("operations")
    if isinstance(ops, list):
        logger.warning(
            "agenttel 'operations' as a list is deprecated; use a map keyed by "
            "\"METHOD /route\" (see the AgentTel configuration docs)"
        )
        converted: dict[str, Any] = {}
        for item in ops:
            item = dict(item or {})
            name = item.pop("name", None)
            if not name:
                continue
            converted[normalize_operation_name(str(name))] = item
        data["operations"] = ops = converted
    if isinstance(ops, dict):
        for op in ops.values():
            if isinstance(op, dict):
                for old, new in _LEGACY_OPERATION_KEYS.items():
                    if old in op:
                        op.setdefault(new, op.pop(old))
                        legacy.add(old)

    if legacy:
        logger.warning(
            "agenttel config uses deprecated key spellings %s; use kebab-case "
            "(e.g. 'on-call-channel', 'expected-latency-p50')",
            sorted(legacy),
        )
    return data
