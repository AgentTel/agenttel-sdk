package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"time"

	"github.com/gin-gonic/gin"
	"go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/trace"

	agenttel "go.agenttel.dev/agenttel-go"
	aggin "go.agenttel.dev/agenttel-go/middleware/gin"
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

	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())

	// otelgin creates the server span ...
	r.Use(otelgin.Middleware(engine.Config.Topology.ServiceName))

	// ... and AgentTel enriches it. c.FullPath() is the route template
	// ("/api/payments/:id"), which matches the config key "GET /api/payments/:id".
	enrichCfg := aggin.NewConfig(aggin.WithEngine(engine))
	r.Use(func(c *gin.Context) {
		aggin.EnrichSpan(trace.SpanFromContext(c.Request.Context()), c.Request.Method, c.FullPath(), enrichCfg)
		c.Next()
	})

	// Routes
	r.POST("/api/payments", createPayment)
	r.GET("/api/payments/:id", getPayment)
	r.GET("/health", healthCheck)

	port := envOrDefault("PORT", "8080")
	srv := &http.Server{Addr: ":" + port, Handler: r}

	go func() {
		<-ctx.Done()
		shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer shutdownCancel()
		srv.Shutdown(shutdownCtx)
	}()

	log.Printf("Gin Payment Service starting on :%s", port)
	log.Printf("  POST /api/payments      - Create payment")
	log.Printf("  GET  /api/payments/:id  - Get payment")
	log.Printf("  GET  /health            - Health check")

	if err := srv.ListenAndServe(); err != http.ErrServerClosed {
		log.Fatalf("Server error: %v", err)
	}
}

func createPayment(c *gin.Context) {
	// Simulate processing latency (30-70ms)
	time.Sleep(time.Duration(30+rand.Intn(40)) * time.Millisecond)

	// Simulate occasional errors (~2% rate)
	if rand.Float64() < 0.02 {
		span := trace.SpanFromContext(c.Request.Context())
		span.RecordError(fmt.Errorf("payment processing failed: insufficient funds"))
		c.JSON(http.StatusPaymentRequired, gin.H{"error": "insufficient_funds"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"id":     fmt.Sprintf("pay_%d", rand.Intn(100000)),
		"status": "completed",
		"amount": 99.99,
	})
}

func getPayment(c *gin.Context) {
	id := c.Param("id")

	// Simulate read latency (10-25ms)
	time.Sleep(time.Duration(10+rand.Intn(15)) * time.Millisecond)

	c.JSON(http.StatusOK, gin.H{
		"id":     id,
		"status": "completed",
		"amount": 99.99,
	})
}

func healthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

func envOrDefault(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
