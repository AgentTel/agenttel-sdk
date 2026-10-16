package agenttel

import (
	"fmt"
	"log"
	"os"
	"regexp"
	"sort"
	"strings"

	"gopkg.in/yaml.v3"

	"go.agenttel.dev/agenttel-go/operations"
)

// AgentTelConfig is the top-level configuration matching agenttel.yml.
//
// The file format is shared by every AgentTel SDK (JVM, Go, Node.js, Python):
//
//	agenttel:
//	  topology:
//	    team: payments-platform
//	    tier: critical
//	    on-call-channel: "#payments-oncall"
//	  operations:
//	    "[POST /api/payments]":          # brackets optional
//	      expected-latency-p50: 45ms     # duration string, or a number in ms
//	      expected-latency-p99: 200ms
//	      expected-error-rate: 0.001
//	      retryable: true
//	      runbook-url: https://wiki.example.com/runbooks/payments
//
// The pre-0.4.0 Go dialect (no "agenttel:" root, camelCase keys) still loads,
// with a deprecation warning.
type AgentTelConfig struct {
	Enabled          bool                       `yaml:"enabled"`
	Topology         TopologyConfig             `yaml:"topology"`
	Dependencies     []DependencyConfig         `yaml:"dependencies"`
	Consumers        []ConsumerConfig           `yaml:"consumers"`
	Profiles         map[string]ProfileConfig   `yaml:"profiles"`
	Operations       map[string]OperationConfig `yaml:"operations"`
	Baselines        BaselineConfig             `yaml:"baselines"`
	AnomalyDetection AnomalyDetectionConfig     `yaml:"anomaly-detection"`
	SLO              map[string]SLOConfig       `yaml:"slo"`
}

// TopologyConfig describes service ownership metadata.
type TopologyConfig struct {
	ServiceName   string `yaml:"service-name"`
	Team          string `yaml:"team"`
	Tier          string `yaml:"tier"`
	Domain        string `yaml:"domain"`
	OnCallChannel string `yaml:"on-call-channel"`
	RepoURL       string `yaml:"repo-url"`
}

// DependencyConfig declares a service dependency.
type DependencyConfig struct {
	Name           string `yaml:"name"`
	Type           string `yaml:"type"`
	Criticality    string `yaml:"criticality"`
	Protocol       string `yaml:"protocol"`
	TimeoutMs      int    `yaml:"timeout-ms"`
	CircuitBreaker bool   `yaml:"circuit-breaker"`
	Fallback       string `yaml:"fallback"`
	HealthEndpoint string `yaml:"health-endpoint"`
}

// ConsumerConfig declares a downstream consumer.
type ConsumerConfig struct {
	Name         string `yaml:"name"`
	Pattern      string `yaml:"pattern"`
	SLALatencyMs int    `yaml:"sla-latency-ms"`
}

// ProfileConfig holds decision defaults that operations reference by name.
type ProfileConfig struct {
	Retryable           *bool  `yaml:"retryable"`
	Idempotent          *bool  `yaml:"idempotent"`
	RunbookURL          string `yaml:"runbook-url"`
	FallbackDescription string `yaml:"fallback-description"`
	EscalationLevel     string `yaml:"escalation-level"`
	SafeToRestart       *bool  `yaml:"safe-to-restart"`
}

// OperationConfig provides per-operation configuration. Explicit values
// override the referenced profile. Latencies are durations ("45ms", "1s") or
// plain numbers of milliseconds.
type OperationConfig struct {
	Profile             string  `yaml:"profile"`
	ExpectedLatencyP50  string  `yaml:"expected-latency-p50"`
	ExpectedLatencyP99  string  `yaml:"expected-latency-p99"`
	ExpectedErrorRate   float64 `yaml:"expected-error-rate"`
	Retryable           *bool   `yaml:"retryable"`
	Idempotent          *bool   `yaml:"idempotent"`
	RunbookURL          string  `yaml:"runbook-url"`
	FallbackDescription string  `yaml:"fallback-description"`
	EscalationLevel     string  `yaml:"escalation-level"`
	SafeToRestart       *bool   `yaml:"safe-to-restart"`
}

// BaselineConfig configures the rolling baseline provider.
type BaselineConfig struct {
	RollingWindowSize int `yaml:"rolling-window-size"`
	RollingMinSamples int `yaml:"rolling-min-samples"`
}

// AnomalyDetectionConfig configures anomaly detection.
type AnomalyDetectionConfig struct {
	Enabled         bool    `yaml:"enabled"`
	ZScoreThreshold float64 `yaml:"z-score-threshold"`
}

// SLOConfig declares a service level objective, keyed by name under "slo".
type SLOConfig struct {
	Target    float64 `yaml:"target"`
	Type      string  `yaml:"type"`
	Operation string  `yaml:"operation"`
}

// DefaultConfig returns a configuration with sensible defaults.
func DefaultConfig() AgentTelConfig {
	return AgentTelConfig{
		Enabled: true,
		Baselines: BaselineConfig{
			RollingWindowSize: 1000,
			RollingMinSamples: 10,
		},
		AnomalyDetection: AnomalyDetectionConfig{
			Enabled:         true,
			ZScoreThreshold: 3.0,
		},
	}
}

// LoadConfig reads an AgentTelConfig from a YAML file, then applies env overrides.
func LoadConfig(path string) (AgentTelConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return DefaultConfig(), err
	}
	cfg, err := ParseConfig(data)
	if err != nil {
		return cfg, fmt.Errorf("agenttel: %s: %w", path, err)
	}
	applyEnvOverrides(&cfg)
	return cfg, nil
}

// LoadConfigFile is an alias of LoadConfig.
func LoadConfigFile(path string) (AgentTelConfig, error) { return LoadConfig(path) }

// ParseConfig parses YAML in the shared AgentTel format (or a legacy dialect).
// Environment overrides are not applied.
func ParseConfig(data []byte) (AgentTelConfig, error) {
	cfg := DefaultConfig()
	var raw map[string]any
	if err := yaml.Unmarshal(data, &raw); err != nil {
		return cfg, err
	}
	normalized, err := yaml.Marshal(normalizeRaw(raw))
	if err != nil {
		return cfg, err
	}
	if err := yaml.Unmarshal(normalized, &cfg); err != nil {
		return cfg, err
	}
	for name, op := range cfg.Operations {
		for _, v := range []string{op.ExpectedLatencyP50, op.ExpectedLatencyP99} {
			if _, _, err := operations.ParseDurationMs(v); err != nil {
				return cfg, fmt.Errorf("operation %q: %w", name, err)
			}
		}
	}
	return cfg, nil
}

// LoadConfigFromEnv attempts to load config from the AGENTTEL_CONFIG_FILE env var
// or falls back to "agenttel.yml" in the current directory.
func LoadConfigFromEnv() (AgentTelConfig, error) {
	path := os.Getenv("AGENTTEL_CONFIG_FILE")
	if path == "" {
		path = "agenttel.yml"
	}

	cfg, err := LoadConfig(path)
	if err != nil && !os.IsNotExist(err) {
		return cfg, err
	}
	if os.IsNotExist(err) {
		cfg = DefaultConfig()
	}

	applyEnvOverrides(&cfg)
	return cfg, nil
}

func applyEnvOverrides(cfg *AgentTelConfig) {
	envMap := map[string]*string{
		"AGENTTEL_TOPOLOGY_TEAM":            &cfg.Topology.Team,
		"AGENTTEL_TOPOLOGY_TIER":            &cfg.Topology.Tier,
		"AGENTTEL_TOPOLOGY_DOMAIN":          &cfg.Topology.Domain,
		"AGENTTEL_TOPOLOGY_ON_CALL_CHANNEL": &cfg.Topology.OnCallChannel,
		"AGENTTEL_TOPOLOGY_REPO_URL":        &cfg.Topology.RepoURL,
	}

	for envKey, field := range envMap {
		if val := os.Getenv(envKey); val != "" {
			*field = val
		}
	}

	if val := os.Getenv("AGENTTEL_ENABLED"); val != "" {
		cfg.Enabled = strings.EqualFold(val, "true")
	}
}

// --- raw document normalization (shared dialect + backward compatibility) ---

// warnf reports deprecated config usage. Replaceable for tests.
var warnf = log.Printf

// Sections whose keys are user-chosen names, not schema keys.
var namedMaps = map[string]bool{"operations": true, "profiles": true, "slo": true, "agent-roles": true}

var camelBoundary = regexp.MustCompile(`([a-z0-9])([A-Z])`)

func toKebab(key string) string {
	return strings.ToLower(strings.ReplaceAll(camelBoundary.ReplaceAllString(key, "$1-$2"), "_", "-"))
}

func normalizeRaw(raw map[string]any) map[string]any {
	if root, ok := asMap(raw["agenttel"]); ok {
		raw = root
	} else if len(raw) > 0 {
		warnf("agenttel: config without a top-level 'agenttel:' key is deprecated; nest the configuration under 'agenttel:'")
	}

	legacy := map[string]bool{}
	out, _ := kebabKeys(raw, "", legacy).(map[string]any)
	if out == nil {
		out = map[string]any{}
	}

	if list, ok := out["operations"].([]any); ok {
		warnf("agenttel: 'operations' as a list is deprecated; use a map keyed by \"METHOD /route\"")
		converted := map[string]any{}
		for _, item := range list {
			m, ok := asMap(item)
			if !ok || m["name"] == nil {
				continue
			}
			name := fmt.Sprint(m["name"])
			delete(m, "name")
			converted[operations.Normalize(name)] = m
		}
		out["operations"] = converted
	}
	if ops, ok := asMap(out["operations"]); ok {
		for _, v := range ops {
			op, ok := asMap(v)
			if !ok {
				continue
			}
			for old, canonical := range map[string]string{
				"baseline-latency-p50-ms": "expected-latency-p50",
				"baseline-latency-p99-ms": "expected-latency-p99",
				"baseline-error-rate":     "expected-error-rate",
			} {
				if val, ok := op[old]; ok {
					legacy[old] = true
					if _, exists := op[canonical]; !exists {
						op[canonical] = val
					}
					delete(op, old)
				}
			}
			// Latencies may be numbers (milliseconds); the struct field is a string.
			for _, k := range []string{"expected-latency-p50", "expected-latency-p99"} {
				if val, ok := op[k]; ok && val != nil {
					op[k] = fmt.Sprint(val)
				}
			}
		}
	}

	if len(legacy) > 0 {
		keys := make([]string, 0, len(legacy))
		for k := range legacy {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		warnf("agenttel: config uses deprecated key spellings %v; use kebab-case (e.g. 'on-call-channel', 'expected-latency-p50')", keys)
	}
	return out
}

func kebabKeys(value any, section string, legacy map[string]bool) any {
	switch v := value.(type) {
	case []any:
		out := make([]any, len(v))
		for i, item := range v {
			out[i] = kebabKeys(item, "", legacy)
		}
		return out
	case map[string]any, map[any]any:
		m, _ := asMap(v)
		out := make(map[string]any, len(m))
		for key, child := range m {
			if namedMaps[section] {
				if section == "operations" {
					key = operations.Normalize(key)
				}
				out[key] = kebabKeys(child, "\x00entry", legacy)
				continue
			}
			k := toKebab(key)
			if k != key {
				legacy[key] = true
			}
			out[k] = kebabKeys(child, k, legacy)
		}
		return out
	default:
		return value
	}
}

func asMap(v any) (map[string]any, bool) {
	switch m := v.(type) {
	case map[string]any:
		return m, true
	case map[any]any:
		out := make(map[string]any, len(m))
		for k, val := range m {
			out[fmt.Sprint(k)] = val
		}
		return out, true
	}
	return nil, false
}
