// Package operations holds per-operation decision context and the helpers that
// give every AgentTel SDK the same operation keys ("METHOD /route") and
// duration format ("45ms", or a number of milliseconds).
package operations

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"sync"
)

// Decision is the context an agent needs to act safely on an operation.
type Decision struct {
	Retryable           bool
	Idempotent          bool
	RunbookURL          string
	FallbackDescription string
	EscalationLevel     string
	SafeToRestart       bool
}

// Provider looks up decision context by operation name.
type Provider interface {
	GetDecision(operationName string) (Decision, bool)
}

// Registry is a concurrency-safe Provider keyed by normalized operation name.
type Registry struct {
	mu        sync.RWMutex
	decisions map[string]Decision
}

// NewRegistry creates an empty decision registry.
func NewRegistry() *Registry {
	return &Registry{decisions: make(map[string]Decision)}
}

// Register adds or replaces the decision context for an operation.
func (r *Registry) Register(operationName string, d Decision) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.decisions[Normalize(operationName)] = d
}

// GetDecision returns the decision context for an operation, if configured.
func (r *Registry) GetDecision(operationName string) (Decision, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	d, ok := r.decisions[Normalize(operationName)]
	return d, ok
}

var pathParam = regexp.MustCompile(`(^|/):([A-Za-z_][A-Za-z0-9_]*)`)

// Normalize returns the canonical "METHOD /route" form of an operation key:
// Spring-style [brackets] are stripped, the HTTP method is upper-cased and
// ":param" path segments become "{param}", so net/http, Gin, Express and
// FastAPI route templates all share one key. Other names are only trimmed.
func Normalize(name string) string {
	n := strings.TrimSpace(name)
	if strings.HasPrefix(n, "[") && strings.HasSuffix(n, "]") {
		n = strings.TrimSpace(n[1 : len(n)-1])
	}
	method, route, ok := strings.Cut(n, " ")
	route = strings.TrimSpace(route)
	if ok && strings.HasPrefix(route, "/") {
		n = strings.ToUpper(method) + " " + pathParam.ReplaceAllString(route, "$1{$2}")
	}
	return n
}

// ParseDurationMs parses "45ms", "1.5s", "2m" or a plain number of
// milliseconds ("45"). An empty string returns (0, false, nil).
func ParseDurationMs(value string) (ms float64, ok bool, err error) {
	v := strings.ToLower(strings.TrimSpace(value))
	if v == "" {
		return 0, false, nil
	}
	mult := 1.0
	switch {
	case strings.HasSuffix(v, "ms"):
		v = strings.TrimSuffix(v, "ms")
	case strings.HasSuffix(v, "s"):
		v, mult = strings.TrimSuffix(v, "s"), 1000
	case strings.HasSuffix(v, "m"):
		v, mult = strings.TrimSuffix(v, "m"), 60000
	}
	f, perr := strconv.ParseFloat(strings.TrimSpace(v), 64)
	if perr != nil || f < 0 {
		return 0, false, fmt.Errorf("agenttel: invalid duration %q (expected e.g. \"45ms\" or 45)", value)
	}
	return f * mult, true, nil
}
