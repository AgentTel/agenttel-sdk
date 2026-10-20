package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"time"

	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/trace"

	agenttel "go.agenttel.dev/agenttel-go"
	agmw "go.agenttel.dev/agenttel-go/middleware/http"
)

func main() {
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
	defer cancel()

	// Build the AgentTel engine from agenttel.yml: topology, baselines and
	// decision context (retryable, runbook, escalation) per "METHOD /route".
	engine, err := agenttel.New().WithConfigFile("agenttel.yml").Build()
	if err != nil {
		log.Fatalf("Failed to build AgentTel engine: %v", err)
	}

	// Exporter: OTLP/HTTP by default, stdout with OTEL_TRACES_EXPORTER=console.
	var exporter sdktrace.SpanExporter
	if os.Getenv("OTEL_TRACES_EXPORTER") == "console" {
		exporter, err = stdouttrace.New(stdouttrace.WithPrettyPrint())
	} else {
		exporter, err = otlptracehttp.New(ctx,
			otlptracehttp.WithEndpoint(envOrDefault("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4318")),
			otlptracehttp.WithInsecure(),
		)
	}
	if err != nil {
		log.Fatalf("Failed to create exporter: %v", err)
	}

	// TracerProvider with topology on the resource and the AgentTel processor.
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithResource(engine.Resource()),
		sdktrace.WithSpanProcessor(engine.SpanProcessor()),
		sdktrace.WithBatcher(exporter),
	)
	defer tp.Shutdown(context.Background())
	otel.SetTracerProvider(tp)

	// Set up HTTP routes with AgentTel middleware
	mux := http.NewServeMux()

	mux.HandleFunc("POST /api/payments", func(w http.ResponseWriter, r *http.Request) {
		span := trace.SpanFromContext(r.Context()) // the otelhttp server span

		// Simulate processing
		time.Sleep(time.Duration(30+rand.Intn(40)) * time.Millisecond)

		// Simulate occasional errors
		if rand.Float64() < 0.02 {
			span.RecordError(fmt.Errorf("payment processing failed: insufficient funds"))
			http.Error(w, `{"error":"insufficient_funds"}`, http.StatusPaymentRequired)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"id":     fmt.Sprintf("pay_%d", rand.Intn(100000)),
			"status": "completed",
			"amount": 99.99,
		})
	})

	mux.HandleFunc("GET /api/payments/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		time.Sleep(time.Duration(10+rand.Intn(15)) * time.Millisecond)

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"id":     id,
			"status": "completed",
			"amount": 99.99,
		})
	})

	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
	})

	// otelhttp creates the server span; AgentTel enriches it with topology,
	// baselines and decisions for the matched "METHOD /route".
	handler := otelhttp.NewHandler(agmw.Middleware(agmw.WithEngine(engine))(mux), "server",
		otelhttp.WithSpanNameFormatter(func(_ string, r *http.Request) string { return r.Method }),
	)

	port := envOrDefault("PORT", "8080")
	srv := &http.Server{Addr: ":" + port, Handler: handler}

	go func() {
		<-ctx.Done()
		shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer shutdownCancel()
		srv.Shutdown(shutdownCtx)
	}()

	log.Printf("Go Payment Service starting on :%s", port)
	log.Printf("  POST /api/payments      - Create payment")
	log.Printf("  GET  /api/payments/{id} - Get payment")
	log.Printf("  GET  /health            - Health check")

	if err := srv.ListenAndServe(); err != http.ErrServerClosed {
		log.Fatalf("Server error: %v", err)
	}
}

func envOrDefault(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
