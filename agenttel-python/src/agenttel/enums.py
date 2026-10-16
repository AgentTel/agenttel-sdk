"""AgentTel enumeration types."""

from enum import StrEnum


class ServiceTier(StrEnum):
    CRITICAL = "critical"
    STANDARD = "standard"
    INTERNAL = "internal"
    EXPERIMENTAL = "experimental"


class ErrorCategory(StrEnum):
    DEPENDENCY_TIMEOUT = "dependency_timeout"
    CONNECTION_ERROR = "connection_error"
    CODE_BUG = "code_bug"
    RATE_LIMITED = "rate_limited"
    AUTH_FAILURE = "auth_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DATA_VALIDATION = "data_validation"
    UNKNOWN = "unknown"


class DependencyType(StrEnum):
    INTERNAL_SERVICE = "internal_service"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    MESSAGE_BROKER = "message_broker"
    CACHE = "cache"
    OBJECT_STORE = "object_store"
    IDENTITY_PROVIDER = "identity_provider"


class DependencyCriticality(StrEnum):
    REQUIRED = "required"
    DEGRADED = "degraded"
    OPTIONAL = "optional"


class DependencyState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    UNKNOWN = "unknown"


class BaselineSource(StrEnum):
    STATIC = "static"
    ROLLING_7D = "rolling_7d"
    ML_MODEL = "ml_model"
    SLO = "slo"


class BaselineConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CauseCategory(StrEnum):
    INFRASTRUCTURE = "infrastructure"
    DEPENDENCY = "dependency"
    CODE_CHANGE = "code_change"
    CONFIGURATION = "configuration"
    CAPACITY = "capacity"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class BusinessImpact(StrEnum):
    REVENUE = "revenue"
    USER_EXPERIENCE = "user_experience"
    DATA_INTEGRITY = "data_integrity"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"


class ImpactScope(StrEnum):
    SINGLE_OPERATION = "single_operation"
    SINGLE_SERVICE = "single_service"
    MULTI_SERVICE = "multi_service"
    PLATFORM_WIDE = "platform_wide"


class EscalationLevel(StrEnum):
    AUTO_RESOLVE = "auto_resolve"
    NOTIFY_TEAM = "notify_team"
    PAGE_ONCALL = "page_oncall"
    PAGE_MANAGER = "page_manager"
    INCIDENT_COMMANDER = "incident_commander"


class AgentRole(StrEnum):
    OBSERVER = "observer"
    DIAGNOSTICIAN = "diagnostician"
    REMEDIATOR = "remediator"
    ADMIN = "admin"


class ConsumptionPattern(StrEnum):
    SYNC = "sync"
    ASYNC = "async"
    BATCH = "batch"
    STREAMING = "streaming"


class SloType(StrEnum):
    AVAILABILITY = "availability"
    LATENCY_P99 = "latency_p99"
    LATENCY_P50 = "latency_p50"
    ERROR_RATE = "error_rate"


class AlertLevel(StrEnum):
    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AnomalyPattern(StrEnum):
    LATENCY_DEGRADATION = "latency_degradation"
    ERROR_RATE_SPIKE = "error_rate_spike"
    CASCADE_FAILURE = "cascade_failure"
    SUSTAINED_DEGRADATION = "sustained_degradation"


# Phase 5: Agentic enums
class AgentType(StrEnum):
    SINGLE = "single"
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    EVALUATOR = "evaluator"
    CRITIC = "critic"
    ROUTER = "router"


class OrchestrationPattern(StrEnum):
    REACT = "react"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HANDOFF = "handoff"
    ORCHESTRATOR_WORKERS = "orchestrator_workers"
    EVALUATOR_OPTIMIZER = "evaluator_optimizer"
    GROUP_CHAT = "group_chat"
    SWARM = "swarm"
    HIERARCHICAL = "hierarchical"


class StepType(StrEnum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    EVALUATION = "evaluation"
    REVISION = "revision"


class InvocationStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ErrorSource(StrEnum):
    TOOL = "tool"
    LLM = "llm"
    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"


class EvalType(StrEnum):
    LLM_JUDGE = "llm_judge"
    PROGRAMMATIC = "programmatic"
    HUMAN = "human"
    COMPOSITE = "composite"


class GuardrailAction(StrEnum):
    BLOCK = "block"
    WARN = "warn"
    LOG = "log"
    MODIFY = "modify"


class HumanCheckpointType(StrEnum):
    APPROVAL = "approval"
    REVIEW = "review"
    ESCALATION = "escalation"
    FEEDBACK = "feedback"


class MemoryOperation(StrEnum):
    READ = "read"
    WRITE = "write"
    SEARCH = "search"
    DELETE = "delete"
