package operations

import "testing"

func TestNormalize(t *testing.T) {
	cases := map[string]string{
		"[POST /api/payments]": "POST /api/payments",
		"post /api/payments":   "POST /api/payments",
		"GET /orders/:id":      "GET /orders/{id}",
		"GET /orders/{id}":     "GET /orders/{id}",
		"process-payment":      "process-payment",
		"/pkg.Svc/Method":      "/pkg.Svc/Method",
	}
	for in, want := range cases {
		if got := Normalize(in); got != want {
			t.Errorf("Normalize(%q) = %q, want %q", in, got, want)
		}
	}
}

func TestParseDurationMs(t *testing.T) {
	cases := map[string]float64{"45ms": 45, "1.5s": 1500, "2m": 120000, "45": 45, " 10 ms ": 10}
	for in, want := range cases {
		got, ok, err := ParseDurationMs(in)
		if err != nil || !ok || got != want {
			t.Errorf("ParseDurationMs(%q) = %v, %v, %v; want %v", in, got, ok, err, want)
		}
	}
	if _, ok, err := ParseDurationMs(""); ok || err != nil {
		t.Errorf("empty duration should be (0, false, nil)")
	}
	if _, _, err := ParseDurationMs("fast"); err == nil {
		t.Errorf("expected error for invalid duration")
	}
}
