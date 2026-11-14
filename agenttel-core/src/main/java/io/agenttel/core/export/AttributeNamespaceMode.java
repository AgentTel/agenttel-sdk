package io.agenttel.core.export;

/**
 * Which attribute names AgentTel emits, set with {@code agenttel.attributes.namespace}.
 */
public enum AttributeNamespaceMode {
    /** Only the {@code agenttel.*} names (default). */
    LEGACY("legacy"),
    /** Standard names in place of the {@code agenttel.*} names that have one. */
    STANDARD("standard"),
    /** Both: the {@code agenttel.*} name and, where one exists, the standard name. */
    BOTH("both");

    private final String value;

    AttributeNamespaceMode(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }

    /**
     * Parses a configured value, case-insensitively. {@code null} or blank means {@link #LEGACY}.
     *
     * @throws IllegalArgumentException for any other value
     */
    public static AttributeNamespaceMode fromValue(String value) {
        if (value == null || value.isBlank()) {
            return LEGACY;
        }
        for (AttributeNamespaceMode mode : values()) {
            if (mode.value.equalsIgnoreCase(value.trim())) {
                return mode;
            }
        }
        throw new IllegalArgumentException(
                "Unknown agenttel.attributes.namespace '" + value + "' (expected legacy, standard or both)");
    }
}
