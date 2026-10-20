package io.agenttel.extension.it;

import java.util.Map;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

/** Plain Spring Boot app (no AgentTel dependency) started by {@link JavaagentIntegrationTest}. */
@SpringBootApplication
@RestController
public class PaymentsTestApp {

    public static void main(String[] args) {
        SpringApplication.run(PaymentsTestApp.class, args);
    }

    @PostMapping("/api/payments")
    public Map<String, String> pay() {
        return Map.of("status", "completed");
    }

    @GetMapping("/api/payments/{id}")
    public Map<String, String> get(@PathVariable("id") String id) {
        return Map.of("id", id);
    }
}
