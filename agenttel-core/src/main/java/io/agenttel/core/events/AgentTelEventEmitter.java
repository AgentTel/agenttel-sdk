package io.agenttel.core.events;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.agenttel.core.resource.AgentTelGlobalState;
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.logs.Logger;
import io.opentelemetry.api.logs.Severity;
import org.slf4j.LoggerFactory;

import java.util.Map;

/**
 * Emits structured AgentTel events via the OTel Logs API.
 */
public class AgentTelEventEmitter {

    private static final org.slf4j.Logger LOG = LoggerFactory.getLogger(AgentTelEventEmitter.class);
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private final Logger otelLogger;

    public AgentTelEventEmitter(OpenTelemetry openTelemetry) {
        this.otelLogger = openTelemetry.getLogsBridge()
                .loggerBuilder("io.agenttel")
                .build();
    }

    /**
     * Emits a structured event with the given name and body.
     */
    public void emitEvent(String eventName, Map<String, Object> body) {
        emitEvent(eventName, body, Severity.INFO);
    }

    /**
     * Emits a structured event with the given name, body, and severity.
     */
    public void emitEvent(String eventName, Map<String, Object> body, Severity severity) {
        try {
            String bodyJson = OBJECT_MAPPER.writeValueAsString(body);
            otelLogger.logRecordBuilder()
                    .setSeverity(severity)
                    .setAttribute(io.opentelemetry.api.common.AttributeKey.stringKey("event.name"),
                            AgentTelGlobalState.getNamespaceMapper().mapEventName(eventName))
                    .setBody(bodyJson)
                    .emit();
        } catch (JsonProcessingException e) {
            LOG.warn("Failed to serialize event body for {}: {}", eventName, e.getMessage());
        }
    }
}
