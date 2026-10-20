package agenttel

import (
	"os"
	"path/filepath"
	"testing"
)

func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()
	if !cfg.Enabled {
		t.Error("expected enabled=true")
	}
	if cfg.Baselines.RollingWindowSize != 1000 {
		t.Errorf("expected rollingWindowSize=1000, got %d", cfg.Baselines.RollingWindowSize)
	}
	if cfg.AnomalyDetection.ZScoreThreshold != 3.0 {
		t.Errorf("expected zScoreThreshold=3.0, got %f", cfg.AnomalyDetection.ZScoreThreshold)
	}
}

func TestLoadConfigFromFile(t *testing.T) {
	yaml := `
enabled: true
topology:
  team: payments
  tier: critical
  domain: fintech
dependencies:
  - name: postgres
    type: database
    criticality: required
operations:
  POST /transfer:
    expectedLatencyP50: 200ms
baselines:
  rollingWindowSize: 500
  rollingMinSamples: 20
anomalyDetection:
  enabled: true
  zScoreThreshold: 2.5
`
	dir := t.TempDir()
	path := filepath.Join(dir, "agenttel.yml")
	if err := os.WriteFile(path, []byte(yaml), 0644); err != nil {
		t.Fatal(err)
	}

	cfg, err := LoadConfig(path)
	if err != nil {
		t.Fatal(err)
	}

	if cfg.Topology.Team != "payments" {
		t.Errorf("expected team=payments, got %s", cfg.Topology.Team)
	}
	if cfg.Topology.Tier != "critical" {
		t.Errorf("expected tier=critical, got %s", cfg.Topology.Tier)
	}
	if len(cfg.Dependencies) != 1 {
		t.Errorf("expected 1 dependency, got %d", len(cfg.Dependencies))
	}
	if cfg.Dependencies[0].Name != "postgres" {
		t.Errorf("expected dep name=postgres, got %s", cfg.Dependencies[0].Name)
	}
	if cfg.Baselines.RollingWindowSize != 500 {
		t.Errorf("expected rollingWindowSize=500, got %d", cfg.Baselines.RollingWindowSize)
	}
	if cfg.AnomalyDetection.ZScoreThreshold != 2.5 {
		t.Errorf("expected zScoreThreshold=2.5, got %f", cfg.AnomalyDetection.ZScoreThreshold)
	}
}

func TestEnvOverrides(t *testing.T) {
	t.Setenv("AGENTTEL_TOPOLOGY_TEAM", "platform")
	t.Setenv("AGENTTEL_TOPOLOGY_TIER", "internal")

	cfg := DefaultConfig()
	applyEnvOverrides(&cfg)

	if cfg.Topology.Team != "platform" {
		t.Errorf("expected team=platform, got %s", cfg.Topology.Team)
	}
	if cfg.Topology.Tier != "internal" {
		t.Errorf("expected tier=internal, got %s", cfg.Topology.Tier)
	}
}

func TestSharedConfigFormat(t *testing.T) {
	cfg, err := ParseConfig([]byte(`
agenttel:
  topology:
    team: payments
    on-call-channel: "#oncall"
  profiles:
    critical-write:
      retryable: false
      runbook-url: https://profile
      escalation-level: page_oncall
  operations:
    "[POST /api/payments]":
      profile: critical-write
      expected-latency-p50: 45ms
      expected-latency-p99: 1.5s
      expected-error-rate: 0.001
      retryable: true
    GET /orders/:id:
      expected-latency-p50: 15
  baselines:
    rolling-window-size: 500
  anomaly-detection:
    z-score-threshold: 2.5
  slo:
    availability:
      target: 0.999
      type: availability
`))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Topology.OnCallChannel != "#oncall" || cfg.Baselines.RollingWindowSize != 500 || cfg.AnomalyDetection.ZScoreThreshold != 2.5 {
		t.Errorf("unexpected config: %+v", cfg)
	}
	if _, ok := cfg.Operations["POST /api/payments"]; !ok {
		t.Fatalf("bracketed key not normalized: %v", cfg.Operations)
	}
	if cfg.Operations["GET /orders/{id}"].ExpectedLatencyP50 != "15" {
		t.Errorf("numeric latency not accepted: %+v", cfg.Operations)
	}

	engine, err := New().WithConfig(cfg).Build()
	if err != nil {
		t.Fatal(err)
	}
	b, ok := engine.BaselineProvider.GetBaseline("POST /api/payments")
	if !ok || b.LatencyP50Ms != 45 || b.LatencyP99Ms != 1500 || b.ErrorRate != 0.001 {
		t.Errorf("static baseline from config = %+v, %v", b, ok)
	}
	if b, ok := engine.BaselineProvider.GetBaseline("GET /orders/{id}"); !ok || b.LatencyP50Ms != 15 {
		t.Errorf("GET baseline = %+v, %v", b, ok)
	}
	d, ok := engine.Operations.GetDecision("POST /api/payments")
	if !ok || !d.Retryable || d.RunbookURL != "https://profile" || d.EscalationLevel != "page_oncall" || !d.SafeToRestart {
		t.Errorf("decision = %+v, %v", d, ok)
	}
	if d, _ := engine.Operations.GetDecision("GET /orders/{id}"); d.EscalationLevel != "auto_resolve" {
		t.Errorf("default escalation = %q", d.EscalationLevel)
	}
}

func TestLegacyNodeOperationsList(t *testing.T) {
	cfg, err := ParseConfig([]byte(`
topology:
  on_call_channel: "#c"
operations:
  - name: POST /p
    baseline_latency_p50_ms: 45
    baseline_latency_p99_ms: 200
`))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Topology.OnCallChannel != "#c" {
		t.Errorf("on_call_channel = %q", cfg.Topology.OnCallChannel)
	}
	op := cfg.Operations["POST /p"]
	if op.ExpectedLatencyP50 != "45" || op.ExpectedLatencyP99 != "200" {
		t.Errorf("legacy operation = %+v", op)
	}
}

func TestInvalidLatencyIsAnError(t *testing.T) {
	if _, err := ParseConfig([]byte("agenttel:\n  operations:\n    GET /x:\n      expected-latency-p50: fast\n")); err == nil {
		t.Error("expected error for invalid latency")
	}
}
