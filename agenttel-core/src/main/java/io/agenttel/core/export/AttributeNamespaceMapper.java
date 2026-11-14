package io.agenttel.core.export;

import io.agenttel.api.attributes.AttributeNamespaces;
import io.opentelemetry.api.common.AttributeKey;
import io.opentelemetry.api.common.Attributes;
import io.opentelemetry.api.common.AttributesBuilder;
import io.opentelemetry.sdk.resources.Resource;

import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * Renames AgentTel attribute keys and event names to their standard OpenTelemetry names,
 * according to the {@link AttributeNamespaceMode}. The mapping comes from
 * {@link AttributeNamespaces}, generated from {@code attributes.json}.
 *
 * <p>An existing value under the standard key always wins: a span that already has
 * {@code service.version} or {@code exception.type} keeps it. Mapping is idempotent.
 */
public final class AttributeNamespaceMapper {

    private static final String PREFIX = "agenttel.";

    public static final AttributeNamespaceMapper LEGACY = new AttributeNamespaceMapper(AttributeNamespaceMode.LEGACY);

    private final AttributeNamespaceMode mode;
    private final Map<String, String> attributeKeys;
    private final Map<String, String> eventNames;

    public AttributeNamespaceMapper(AttributeNamespaceMode mode) {
        this(mode, AttributeNamespaces.ATTRIBUTES, AttributeNamespaces.EVENTS);
    }

    AttributeNamespaceMapper(AttributeNamespaceMode mode,
                             Map<String, String> attributeKeys, Map<String, String> eventNames) {
        this.mode = mode;
        this.attributeKeys = attributeKeys;
        this.eventNames = eventNames;
    }

    public AttributeNamespaceMode getMode() {
        return mode;
    }

    public boolean isLegacy() {
        return mode == AttributeNamespaceMode.LEGACY;
    }

    /**
     * Returns the attributes with mapped keys renamed ({@code standard}) or duplicated
     * ({@code both}). Returns the same instance when nothing changes.
     */
    public Attributes map(Attributes attributes) {
        if (isLegacy() || attributes.isEmpty() || !hasMappedKey(attributes)) {
            return attributes;
        }
        Set<String> names = new HashSet<>();
        attributes.forEach((key, value) -> names.add(key.getKey()));
        AttributesBuilder builder = Attributes.builder();
        attributes.forEach((key, value) -> {
            String standard = attributeKeys.get(key.getKey());
            if (standard == null || mode == AttributeNamespaceMode.BOTH) {
                put(builder, key, value);
            }
            if (standard != null && !names.contains(standard)) {
                put(builder, rename(key, standard), value);
            }
        });
        return builder.build();
    }

    /** Returns the resource with its attributes mapped. */
    public Resource map(Resource resource) {
        Attributes mapped = map(resource.getAttributes());
        if (mapped == resource.getAttributes()) {
            return resource;
        }
        return Resource.create(mapped, resource.getSchemaUrl());
    }

    /**
     * Returns the standard event name in {@code standard} mode, otherwise the name unchanged.
     * Events carry a single name, so {@code both} keeps the {@code agenttel.*} name.
     */
    public String mapEventName(String name) {
        if (mode != AttributeNamespaceMode.STANDARD || name == null) {
            return name;
        }
        return eventNames.getOrDefault(name, name);
    }

    private boolean hasMappedKey(Attributes attributes) {
        for (AttributeKey<?> key : attributes.asMap().keySet()) {
            String name = key.getKey();
            if (name.startsWith(PREFIX) && attributeKeys.containsKey(name)) {
                return true;
            }
        }
        return false;
    }

    private static AttributeKey<?> rename(AttributeKey<?> key, String name) {
        return switch (key.getType()) {
            case STRING -> AttributeKey.stringKey(name);
            case BOOLEAN -> AttributeKey.booleanKey(name);
            case LONG -> AttributeKey.longKey(name);
            case DOUBLE -> AttributeKey.doubleKey(name);
            case STRING_ARRAY -> AttributeKey.stringArrayKey(name);
            case BOOLEAN_ARRAY -> AttributeKey.booleanArrayKey(name);
            case LONG_ARRAY -> AttributeKey.longArrayKey(name);
            case DOUBLE_ARRAY -> AttributeKey.doubleArrayKey(name);
            default -> AttributeKey.stringKey(name);
        };
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void put(AttributesBuilder builder, AttributeKey<?> key, Object value) {
        builder.put((AttributeKey) key, value);
    }
}
