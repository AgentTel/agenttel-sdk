// Package baseline provides baseline providers for tracking expected operational norms.
package baseline

import (
	"go.agenttel.dev/agenttel-go/models"
	"go.agenttel.dev/agenttel-go/operations"
)

// Provider returns baseline data for a named operation.
type Provider interface {
	GetBaseline(operationName string) (models.OperationBaseline, bool)
}

// StaticProvider returns baselines from a pre-configured map.
type StaticProvider struct {
	baselines map[string]models.OperationBaseline
}

// NewStaticProvider creates a StaticProvider from a map of operation baselines.
func NewStaticProvider(baselines map[string]models.OperationBaseline) *StaticProvider {
	m := make(map[string]models.OperationBaseline, len(baselines))
	for k, v := range baselines {
		m[operations.Normalize(k)] = v
	}
	return &StaticProvider{baselines: m}
}

// GetBaseline returns the baseline for the given operation, if configured.
func (s *StaticProvider) GetBaseline(operationName string) (models.OperationBaseline, bool) {
	b, ok := s.baselines[operations.Normalize(operationName)]
	return b, ok
}
