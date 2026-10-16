// Core
export { AgentTelEngine, AgentTelEngineBuilder } from './engine.js';
export { AgentTelSpanProcessor } from './processor.js';
export type { ProcessorOptions } from './processor.js';

// Config
export { loadConfig, loadConfigFromEnv, defaultConfig } from './config.js';
export { loadConfig as loadConfigFile, parseConfig } from './config.js';
export type { AgentTelConfig, TopologyConfig, DependencyConfig, ConsumerConfig, OperationConfig, ProfileConfig, SLOConfig } from './config.js';
export { OperationRegistry, normalizeOperationName, parseDurationMs } from './operations.js';
export type { DecisionContext, DecisionProvider } from './operations.js';
export { enrichOperation, enrichTopology } from './enrich.js';

// Attributes
export * from './attributes.js';
export * from './agentic-attributes.js';

// Enums
export * from './enums-impl.js';

// Models / interfaces
export * from './interfaces.js';

// Baseline
export { StaticBaselineProvider } from './baseline/provider.js';
export type { BaselineProvider } from './baseline/provider.js';
export { RollingBaselineProvider, RollingWindow } from './baseline/rolling.js';
export { CompositeBaselineProvider } from './baseline/composite.js';

// Anomaly detection
export { AnomalyDetector } from './anomaly/detector.js';
export { PatternMatcher } from './anomaly/patterns.js';

// SLO tracking
export { SLOTracker } from './slo/tracker.js';

// Error classification
export { ErrorClassifier } from './error/classifier.js';

// Topology
export { TopologyRegistry } from './topology/registry.js';

// Events
export { AgentTelEventEmitter } from './events/emitter.js';
export type { EventHandler } from './events/emitter.js';

// Middleware
export { expressMiddleware } from './middleware/express.js';
export type { ExpressMiddlewareOptions } from './middleware/express.js';
export { fastifyPlugin } from './middleware/fastify.js';
export type { FastifyPluginOptions } from './middleware/fastify.js';

// GenAI
export { GenAiSpanBuilder } from './genai/span-builder.js';
export { calculateCost, registerModelPricing } from './genai/cost.js';
export { instrumentOpenAI } from './genai/openai.js';
export { instrumentAnthropic } from './genai/anthropic.js';

// Agent
export { HealthAggregator } from './agent/health.js';
export type { ServiceHealth, ComponentHealth } from './agent/health.js';
export { IncidentContextBuilder } from './agent/incident.js';
export type { IncidentContext } from './agent/incident.js';
export { RemediationRegistry } from './agent/remediation.js';
export type { RemediationAction, RemediationResult } from './agent/remediation.js';
export { MCPServer } from './agent/mcp/server.js';
export type { MCPTool, MCPToolHandler } from './agent/mcp/server.js';

// Agentic observability
export { AgentTracer, AgentInvocation, StepScope, TaskScope } from './agentic/tracer.js';
export type { AgentTracerOptions } from './agentic/tracer.js';
export { SequentialOrchestrator, ParallelOrchestrator, EvalLoopOrchestrator } from './agentic/orchestration.js';
