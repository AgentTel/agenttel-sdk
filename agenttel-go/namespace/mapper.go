// Package namespace implements the agenttel.attributes.namespace setting: it
// renames agenttel.* attribute keys and event names to their standard
// OpenTelemetry names. The mapping comes from attributes.StandardAttributeKeys
// and attributes.StandardEventNames, generated from attributes.json.
package namespace

import (
	"fmt"
	"strings"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/sdk/resource"

	"go.agenttel.dev/agenttel-go/attributes"
)

// Mode selects which attribute names AgentTel emits.
type Mode string

const (
	// Legacy emits only the agenttel.* names (default).
	Legacy Mode = "legacy"
	// Standard emits standard names in place of the agenttel.* names that have one.
	Standard Mode = "standard"
	// Both emits the agenttel.* name and, where one exists, the standard name.
	Both Mode = "both"
)

const prefix = "agenttel."

// ParseMode parses a configured value, case-insensitively and ignoring
// surrounding whitespace. An empty value means Legacy. Any other unknown value
// returns Legacy and an error.
func ParseMode(value string) (Mode, error) {
	v := strings.ToLower(strings.TrimSpace(value))
	switch Mode(v) {
	case "":
		return Legacy, nil
	case Legacy, Standard, Both:
		return Mode(v), nil
	}
	return Legacy, fmt.Errorf("unknown agenttel.attributes.namespace %q (expected legacy, standard or both)", value)
}

// Mapper applies a Mode to attributes, resources and event names. A nil
// *Mapper behaves like Legacy. Mapping is idempotent, and an existing value
// under the standard key always wins (a real exception.type or service.version
// is never overwritten).
type Mapper struct {
	mode          Mode
	attributeKeys map[string]string
	eventNames    map[string]string
}

// NewMapper returns a Mapper for mode using the generated standard names.
func NewMapper(mode Mode) *Mapper {
	return newMapper(mode, attributes.StandardAttributeKeys, attributes.StandardEventNames)
}

func newMapper(mode Mode, attributeKeys, eventNames map[string]string) *Mapper {
	return &Mapper{mode: mode, attributeKeys: attributeKeys, eventNames: eventNames}
}

// Mode returns the mapper's mode.
func (m *Mapper) Mode() Mode {
	if m == nil {
		return Legacy
	}
	return m.mode
}

// IsLegacy reports whether the mapper leaves everything unchanged.
func (m *Mapper) IsLegacy() bool {
	return m.Mode() != Standard && m.Mode() != Both
}

// MapAttributes returns kvs with mapped keys renamed (Standard) or duplicated
// (Both). It returns kvs itself when nothing changes.
func (m *Mapper) MapAttributes(kvs []attribute.KeyValue) []attribute.KeyValue {
	mapped, _ := m.mapAttributes(kvs)
	return mapped
}

// mapAttributes is MapAttributes, also reporting whether anything changed.
func (m *Mapper) mapAttributes(kvs []attribute.KeyValue) ([]attribute.KeyValue, bool) {
	if m.IsLegacy() || len(kvs) == 0 || !m.hasMappedKey(kvs) {
		return kvs, false
	}
	present := make(map[attribute.Key]bool, len(kvs))
	for _, kv := range kvs {
		present[kv.Key] = true
	}
	changed := false
	out := make([]attribute.KeyValue, 0, len(kvs)*2)
	for _, kv := range kvs {
		std, ok := m.attributeKeys[string(kv.Key)]
		if !ok || m.mode == Both {
			out = append(out, kv)
		} else {
			changed = true
		}
		if ok && !present[attribute.Key(std)] {
			out = append(out, attribute.KeyValue{Key: attribute.Key(std), Value: kv.Value})
			present[attribute.Key(std)] = true
			changed = true
		}
	}
	if !changed {
		return kvs, false
	}
	return out, true
}

// MapResource returns res with its attributes mapped, or res itself when
// nothing changes.
func (m *Mapper) MapResource(res *resource.Resource) *resource.Resource {
	if m.IsLegacy() || res == nil {
		return res
	}
	mapped, changed := m.mapAttributes(res.Attributes())
	if !changed {
		return res
	}
	return resource.NewWithAttributes(res.SchemaURL(), mapped...)
}

// MapEventName returns the standard event name in Standard mode, otherwise the
// name unchanged. Events carry a single name, so Both keeps the agenttel.* name.
func (m *Mapper) MapEventName(name string) string {
	if m.Mode() != Standard {
		return name
	}
	if std, ok := m.eventNames[name]; ok {
		return std
	}
	return name
}

func (m *Mapper) hasMappedKey(kvs []attribute.KeyValue) bool {
	for _, kv := range kvs {
		k := string(kv.Key)
		if strings.HasPrefix(k, prefix) {
			if _, ok := m.attributeKeys[k]; ok {
				return true
			}
		}
	}
	return false
}
