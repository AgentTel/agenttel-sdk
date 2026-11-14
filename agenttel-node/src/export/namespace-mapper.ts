import { STANDARD_ATTRIBUTE_KEYS, STANDARD_EVENT_NAMES } from '../namespaces.js';

/** Which attribute names AgentTel emits, set with `agenttel.attributes.namespace`. */
export enum AttributeNamespaceMode {
  /** Only the `agenttel.*` names (default). */
  LEGACY = 'legacy',
  /** Standard names in place of the `agenttel.*` names that have one. */
  STANDARD = 'standard',
  /** Both: the `agenttel.*` name and, where one exists, the standard name. */
  BOTH = 'both',
}

/**
 * Parses a configured value, case-insensitively and trimmed. Missing or blank means
 * `legacy`; an unknown value logs a warning and falls back to `legacy`.
 */
export function parseAttributeNamespaceMode(value: unknown): AttributeNamespaceMode {
  if (value === undefined || value === null) return AttributeNamespaceMode.LEGACY;
  const v = String(value).trim().toLowerCase();
  if (v === '') return AttributeNamespaceMode.LEGACY;
  for (const mode of Object.values(AttributeNamespaceMode)) {
    if (mode === v) return mode;
  }
  // eslint-disable-next-line no-console
  console.warn(
    `[agenttel] unknown agenttel.attributes.namespace '${String(value)}' (expected legacy, standard or both); using legacy`,
  );
  return AttributeNamespaceMode.LEGACY;
}

const PREFIX = 'agenttel.';

/**
 * Renames AgentTel attribute keys and event names to their standard OpenTelemetry names,
 * according to the {@link AttributeNamespaceMode}. The mapping comes from `namespaces.ts`,
 * generated from `attributes.json`.
 *
 * An existing value under the standard key always wins: a span that already has
 * `service.version` or `exception.type` keeps it. Mapping is idempotent.
 */
export class AttributeNamespaceMapper {
  static readonly LEGACY = new AttributeNamespaceMapper(AttributeNamespaceMode.LEGACY);

  readonly mode: AttributeNamespaceMode;
  private readonly attributeKeys: Readonly<Record<string, string>>;
  private readonly eventNames: Readonly<Record<string, string>>;

  constructor(
    mode: AttributeNamespaceMode | string = AttributeNamespaceMode.LEGACY,
    attributeKeys: Readonly<Record<string, string>> = STANDARD_ATTRIBUTE_KEYS,
    eventNames: Readonly<Record<string, string>> = STANDARD_EVENT_NAMES,
  ) {
    this.mode = parseAttributeNamespaceMode(mode);
    this.attributeKeys = attributeKeys;
    this.eventNames = eventNames;
  }

  isLegacy(): boolean {
    return this.mode === AttributeNamespaceMode.LEGACY;
  }

  /**
   * Returns the attributes with mapped keys renamed (`standard`) or duplicated (`both`).
   * Value types are preserved. Returns the same object when nothing maps.
   */
  map<V>(attributes: Record<string, V>): Record<string, V>;
  map<V>(attributes: Record<string, V> | undefined): Record<string, V> | undefined;
  map<V>(attributes: Record<string, V> | undefined): Record<string, V> | undefined {
    if (this.isLegacy() || !attributes || !this.hasMappedKey(attributes)) return attributes;
    const both = this.mode === AttributeNamespaceMode.BOTH;
    const out: Record<string, V> = {};
    for (const [key, value] of Object.entries(attributes)) {
      const standard = this.standardKey(key);
      if (standard === undefined || both) out[key] = value;
      if (standard !== undefined && !hasOwn(attributes, standard) && !hasOwn(out, standard)) {
        out[standard] = value;
      }
    }
    return out;
  }

  /**
   * Returns the standard event name in `standard` mode, otherwise the name unchanged.
   * Events carry a single name, so `both` keeps the `agenttel.*` name.
   */
  mapEventName(name: string): string {
    if (this.mode !== AttributeNamespaceMode.STANDARD) return name;
    return hasOwn(this.eventNames, name) ? this.eventNames[name] : name;
  }

  private standardKey(key: string): string | undefined {
    return key.startsWith(PREFIX) && hasOwn(this.attributeKeys, key) ? this.attributeKeys[key] : undefined;
  }

  private hasMappedKey(attributes: Record<string, unknown>): boolean {
    for (const key of Object.keys(attributes)) {
      if (this.standardKey(key) !== undefined) return true;
    }
    return false;
  }
}

function hasOwn(obj: object, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(obj, key);
}
