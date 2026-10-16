// OpenTelemetry + AgentTel setup. Imported first by index.ts so the HTTP
// instrumentation patches Node's http module before the web framework loads.
import { NodeSDK } from '@opentelemetry/sdk-node';
import { BatchSpanProcessor, ConsoleSpanExporter, type SpanExporter } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http';
import { ExpressInstrumentation } from '@opentelemetry/instrumentation-express';
import { Resource } from '@opentelemetry/resources';
import { ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { AgentTelEngine } from '@agenttel/node';

// Topology, baselines and decisions come from agenttel.yml (shared AgentTel format).
export const engine = AgentTelEngine.fromConfigFile(process.env.AGENTTEL_CONFIG ?? 'agenttel.yml');

const endpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? 'http://localhost:4318';
const exporter: SpanExporter =
  process.env.OTEL_TRACES_EXPORTER === 'console'
    ? new ConsoleSpanExporter()
    : new OTLPTraceExporter({ url: `${endpoint}/v1/traces` });

export const sdk = new NodeSDK({
  // service.name and agenttel.topology.* on the resource
  resource: new Resource({ ...engine.resourceAttributes(), [ATTR_SERVICE_VERSION]: '1.0.0' }),
  spanProcessors: [engine.spanProcessor, new BatchSpanProcessor(exporter)],
  instrumentations: [new HttpInstrumentation(), new ExpressInstrumentation()],
});
sdk.start();
