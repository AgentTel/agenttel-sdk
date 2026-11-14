package agenttel

import (
	"os"
	"path/filepath"
	"testing"

	"go.agenttel.dev/agenttel-go/attributes"
	"go.agenttel.dev/agenttel-go/namespace"
)

func TestConfigAttributesNamespace(t *testing.T) {
	cfg, err := ParseConfig([]byte(`
agenttel:
  attributes:
    namespace: standard
`))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Attributes.Namespace != "standard" {
		t.Errorf("expected attributes.namespace=standard, got %q", cfg.Attributes.Namespace)
	}

	cfg, err = ParseConfig([]byte("agenttel:\n  topology:\n    team: payments\n"))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Attributes.Namespace != "" {
		t.Errorf("expected attributes.namespace unset by default, got %q", cfg.Attributes.Namespace)
	}
}

func TestAttributesNamespaceEnvOverride(t *testing.T) {
	path := filepath.Join(t.TempDir(), "agenttel.yml")
	if err := os.WriteFile(path, []byte("agenttel:\n  attributes:\n    namespace: legacy\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	t.Setenv("AGENTTEL_ATTRIBUTES_NAMESPACE", "both")

	cfg, err := LoadConfig(path)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Attributes.Namespace != "both" {
		t.Errorf("expected env override both, got %q", cfg.Attributes.Namespace)
	}
}

func TestEngineStandardNamespace(t *testing.T) {
	cfg := DefaultConfig()
	cfg.Topology.Team = "payments"
	cfg.Topology.RepoURL = "https://github.com/example/payments"
	cfg.Attributes.Namespace = "Standard"

	engine, err := New().WithConfig(cfg).Build()
	if err != nil {
		t.Fatal(err)
	}
	if engine.NamespaceMapper.Mode() != namespace.Standard {
		t.Fatalf("expected standard mode, got %s", engine.NamespaceMapper.Mode())
	}

	got := map[string]string{}
	for _, kv := range engine.ResourceAttributes() {
		got[string(kv.Key)] = kv.Value.AsString()
	}
	if got["reliability.topology.team"] != "payments" {
		t.Errorf("expected reliability.topology.team=payments, got %v", got)
	}
	if got["vcs.repository.url.full"] != "https://github.com/example/payments" {
		t.Errorf("expected vcs.repository.url.full, got %v", got)
	}
	if _, ok := got[attributes.TopologyTeam]; ok {
		t.Errorf("standard mode must not emit %s", attributes.TopologyTeam)
	}

	var name string
	engine.EventEmitter.OnEvent(func(eventName string, _ map[string]any) { name = eventName })
	engine.EventEmitter.Emit(attributes.EventAnomalyDetected, map[string]any{})
	if name != "reliability.anomaly.detected" {
		t.Errorf("expected emitted event name reliability.anomaly.detected, got %s", name)
	}
}

func TestEngineAttributeNamespaceOption(t *testing.T) {
	cfg := DefaultConfig()
	cfg.Topology.Team = "payments"

	engine, err := New().WithConfig(cfg).WithAttributeNamespace(namespace.Both).Build()
	if err != nil {
		t.Fatal(err)
	}
	got := map[string]bool{}
	for _, kv := range engine.ResourceAttributes() {
		got[string(kv.Key)] = true
	}
	if !got[attributes.TopologyTeam] || !got["reliability.topology.team"] {
		t.Errorf("both mode should emit legacy and standard keys, got %v", got)
	}
}

func TestEngineUnknownNamespaceFallsBackToLegacy(t *testing.T) {
	var warned bool
	orig := warnf
	warnf = func(string, ...any) { warned = true }
	defer func() { warnf = orig }()

	cfg := DefaultConfig()
	cfg.Topology.Team = "payments"
	cfg.Attributes.Namespace = "otel"

	engine, err := New().WithConfig(cfg).Build()
	if err != nil {
		t.Fatal(err)
	}
	if !warned {
		t.Error("expected a warning for an unknown attributes.namespace")
	}
	if !engine.NamespaceMapper.IsLegacy() {
		t.Errorf("expected legacy fallback, got %s", engine.NamespaceMapper.Mode())
	}
	for _, kv := range engine.ResourceAttributes() {
		if kv.Key == "reliability.topology.team" {
			t.Error("legacy mode must not emit reliability.topology.team")
		}
	}
}
