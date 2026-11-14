// Package events provides structured event emission via OTel-compatible logging.
package events

import (
	"encoding/json"
	"log"
	"sync"
)

// Handler is a callback for receiving emitted events.
type Handler func(eventName string, body map[string]any)

// Emitter emits structured AgentTel events.
type Emitter struct {
	mu       sync.RWMutex
	handlers []Handler
	mapName  func(string) string
}

// NewEmitter creates an event emitter.
func NewEmitter() *Emitter {
	return &Emitter{}
}

// OnEvent registers a handler for all emitted events.
func (e *Emitter) OnEvent(h Handler) {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.handlers = append(e.handlers, h)
}

// SetEventNameMapper sets a function applied to every event name before it
// reaches the handlers (used for the agenttel.attributes.namespace setting).
// A nil function leaves names unchanged.
func (e *Emitter) SetEventNameMapper(fn func(string) string) {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.mapName = fn
}

// Emit sends a structured event to all registered handlers.
func (e *Emitter) Emit(eventName string, body map[string]any) {
	e.mu.RLock()
	defer e.mu.RUnlock()

	if e.mapName != nil {
		eventName = e.mapName(eventName)
	}

	for _, h := range e.handlers {
		func() {
			defer func() {
				if r := recover(); r != nil {
					log.Printf("agenttel: event handler panic for %s: %v", eventName, r)
				}
			}()
			h(eventName, body)
		}()
	}
}

// EmitJSON emits an event, serializing the body to JSON for logging.
func (e *Emitter) EmitJSON(eventName string, body map[string]any) string {
	e.Emit(eventName, body)
	data, err := json.Marshal(body)
	if err != nil {
		return "{}"
	}
	return string(data)
}
