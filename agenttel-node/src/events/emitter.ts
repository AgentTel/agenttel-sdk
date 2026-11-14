import { AttributeNamespaceMapper } from '../export/namespace-mapper.js';

/** Structured event emitter for observability events. */
export type EventHandler = (eventName: string, attributes: Record<string, unknown>) => void;

export class AgentTelEventEmitter {
  private readonly handlers: EventHandler[] = [];

  /**
   * @param mapper applies `agenttel.attributes.namespace`: in `standard` mode handlers
   *   receive the standard event name; event attributes are mapped in `standard` and `both`.
   */
  constructor(private readonly mapper: AttributeNamespaceMapper = AttributeNamespaceMapper.LEGACY) {}

  onEvent(handler: EventHandler): void {
    this.handlers.push(handler);
  }

  emit(eventName: string, attributes: Record<string, unknown> = {}): void {
    eventName = this.mapper.mapEventName(eventName);
    attributes = this.mapper.map(attributes);
    for (const handler of this.handlers) {
      try {
        handler(eventName, attributes);
      } catch {
        // handlers should not throw
      }
    }
  }

  emitJSON(eventName: string, data: unknown): void {
    this.emit(eventName, { payload: JSON.stringify(data) });
  }
}
