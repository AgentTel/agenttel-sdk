package io.agenttel.extension.it;

import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * End-to-end, mirroring the Spring Boot EnrichmentTest: a plain Spring Boot app is
 * started with {@code -javaagent:agenttel-javaagent.jar} (the built artifact), one
 * request is sent, and the exported Tomcat SERVER span must carry baselines and
 * decisions, with topology on the resource.
 */
class JavaagentIntegrationTest {

    private static final String CONFIG = """
            agenttel:
              topology:
                team: payments-platform
                tier: critical
                domain: commerce
                on-call-channel: "#payments-oncall"
              operations:
                "[POST /api/payments]":
                  expected-latency-p50: "45ms"
                  expected-latency-p99: "200ms"
                  expected-error-rate: 0.001
                  retryable: true
                  runbook-url: "https://wiki.example.com/runbooks/payments"
                "GET /api/payments/{id}":
                  expected-latency-p50: "15ms"
                  expected-latency-p99: "80ms"
            """;

    @TempDir
    static Path tmp;

    private static Process app;
    private static Path log;
    private static int port;

    @BeforeAll
    static void startAppWithAgent() throws Exception {
        String agentJar = System.getProperty("agenttel.it.agentJar");
        String classpath = System.getProperty("agenttel.it.appClasspath");
        assertThat(agentJar).as("run via Gradle: agenttel.it.agentJar").isNotNull();

        Path config = Files.writeString(tmp.resolve("agenttel.yml"), CONFIG);
        log = tmp.resolve("app.log");
        try (ServerSocket s = new ServerSocket(0)) {
            port = s.getLocalPort();
        }
        String java = ProcessHandle.current().info().command().orElse("java");
        app = new ProcessBuilder(java,
                "-javaagent:" + agentJar,
                "-Dagenttel.config.file=" + config,
                "-Dotel.service.name=payment-service",
                "-Dotel.traces.exporter=logging-otlp",
                "-Dotel.metrics.exporter=none",
                "-Dotel.logs.exporter=none",
                "-Dotel.bsp.schedule.delay=100",
                "-Dserver.port=" + port,
                "-cp", classpath,
                PaymentsTestApp.class.getName())
                .redirectErrorStream(true)
                .redirectOutput(log.toFile())
                .start();
    }

    @AfterAll
    static void stopApp() throws Exception {
        if (app != null) {
            app.destroy();
            app.waitFor(10, TimeUnit.SECONDS);
        }
    }

    @Test
    void serverSpansAreEnriched() throws Exception {
        HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();
        send(http, "POST", "/api/payments", Duration.ofSeconds(120));
        send(http, "GET", "/api/payments/pay_123", Duration.ofSeconds(10));

        Map<String, Map<String, Object>> serverSpans = new HashMap<>();
        Map<String, Object> resource = new HashMap<>();
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(20);
        while (serverSpans.size() < 2 && System.nanoTime() < deadline) {
            Thread.sleep(250);
            serverSpans.clear();
            collectServerSpans(Files.readAllLines(log), serverSpans, resource);
        }
        String output = Files.readString(log);
        assertThat(serverSpans).as(output).containsKeys("POST /api/payments", "GET /api/payments/{id}");

        Map<String, Object> post = serverSpans.get("POST /api/payments");
        assertThat(post).as("POST span attributes")
                .containsEntry("agenttel.baseline.latency_p50_ms", 45.0)
                .containsEntry("agenttel.baseline.latency_p99_ms", 200.0)
                .containsEntry("agenttel.baseline.error_rate", 0.001)
                .containsEntry("agenttel.baseline.source", "static")
                .containsEntry("agenttel.decision.retryable", true)
                .containsEntry("agenttel.decision.runbook_url", "https://wiki.example.com/runbooks/payments");

        Map<String, Object> get = serverSpans.get("GET /api/payments/{id}");
        assertThat(get).containsEntry("agenttel.baseline.latency_p50_ms", 15.0)
                .containsEntry("agenttel.decision.retryable", false);

        assertThat(resource)
                .containsEntry("agenttel.topology.team", "payments-platform")
                .containsEntry("agenttel.topology.tier", "critical")
                .containsEntry("agenttel.topology.on_call_channel", "#payments-oncall");
    }

    private static void send(HttpClient http, String method, String path, Duration timeout) throws Exception {
        long deadline = System.nanoTime() + timeout.toNanos();
        while (true) {
            assertThat(app.isAlive()).as(() -> read(log)).isTrue();
            try {
                HttpResponse<String> response = http.send(HttpRequest.newBuilder(URI.create("http://localhost:" + port + path))
                        .method(method, HttpRequest.BodyPublishers.noBody()).timeout(Duration.ofSeconds(5)).build(),
                        HttpResponse.BodyHandlers.ofString());
                assertThat(response.statusCode()).as(method + " " + path + ": " + response.body()).isEqualTo(200);
                return;
            } catch (IOException notUpYet) {
                if (System.nanoTime() > deadline) throw notUpYet;
                Thread.sleep(500);
            }
        }
    }

    /** Parses OtlpJsonLoggingSpanExporter lines (one ResourceSpans JSON object per line). */
    private static void collectServerSpans(List<String> lines, Map<String, Map<String, Object>> spans,
                                           Map<String, Object> resource) throws IOException {
        ObjectMapper json = new ObjectMapper();
        for (String line : lines) {
            int start = line.indexOf("{\"resource\"");
            if (start < 0) continue;
            JsonNode resourceSpans = json.readTree(line.substring(start));
            resource.putAll(attributes(resourceSpans.path("resource").path("attributes")));
            for (JsonNode scope : resourceSpans.path("scopeSpans")) {
                for (JsonNode span : scope.path("spans")) {
                    if (span.path("kind").asInt() == 2) { // SPAN_KIND_SERVER
                        spans.put(span.path("name").asText(), attributes(span.path("attributes")));
                    }
                }
            }
        }
    }

    private static Map<String, Object> attributes(JsonNode list) {
        Map<String, Object> out = new HashMap<>();
        for (JsonNode kv : list) {
            JsonNode v = kv.path("value");
            Object value = v.has("stringValue") ? v.get("stringValue").asText()
                    : v.has("boolValue") ? v.get("boolValue").asBoolean()
                    : v.has("doubleValue") ? v.get("doubleValue").asDouble()
                    : v.has("intValue") ? (Object) v.get("intValue").asLong()
                    : v.toString();
            out.put(kv.path("key").asText(), value);
        }
        return out;
    }

    private static String read(Path p) {
        try {
            return Files.readString(p);
        } catch (IOException e) {
            return "";
        }
    }
}
