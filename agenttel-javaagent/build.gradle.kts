plugins {
    `java-library`
    id("com.gradleup.shadow") version "9.0.0-beta12"
}

description = "AgentTel JavaAgent — zero-code agent-ready telemetry (bundles OTel javaagent)"

// Configuration for the upstream OTel javaagent
val otel: Configuration by configurations.creating {
    isCanBeResolved = true
    isCanBeConsumed = false
}

// Runtime classpath of the plain Spring Boot app started by JavaagentIntegrationTest
// (no AgentTel or OpenTelemetry on it; AgentTel is attached with -javaagent)
val integrationApp: Configuration by configurations.creating {
    isCanBeResolved = true
    isCanBeConsumed = false
}

dependencies {
    implementation(project(":agenttel-core"))

    implementation(platform("io.opentelemetry:opentelemetry-bom:${rootProject.extra["otelVersion"]}"))
    implementation("io.opentelemetry:opentelemetry-sdk-extension-autoconfigure-spi")

    implementation("com.fasterxml.jackson.core:jackson-databind:${rootProject.extra["jacksonVersion"]}")
    implementation("com.fasterxml.jackson.dataformat:jackson-dataformat-yaml:${rootProject.extra["jacksonVersion"]}")

    testImplementation("io.opentelemetry:opentelemetry-sdk-testing")

    val springBootVersion = rootProject.extra["springBootVersion"]
    testCompileOnly(platform("org.springframework.boot:spring-boot-dependencies:${springBootVersion}"))
    testCompileOnly("org.springframework.boot:spring-boot-starter-web")
    integrationApp(platform("org.springframework.boot:spring-boot-dependencies:${springBootVersion}"))
    integrationApp("org.springframework.boot:spring-boot-starter-web")

    // Upstream OTel javaagent (downloaded, not on compile classpath)
    otel("io.opentelemetry.javaagent:opentelemetry-javaagent:${rootProject.extra["otelInstrumentationVersion"]}")
}

// Step 1: Shadow creates a self-contained extension JAR with all AgentTel dependencies
tasks.shadowJar {
    archiveClassifier.set("extension")
    mergeServiceFiles()
}

// Disable the default jar — the agentJar replaces it
tasks.named<Jar>("jar") {
    enabled = false
}

// Step 2: Bundle the extension inside the upstream OTel javaagent
tasks.register<Jar>("agentJar") {
    dependsOn(tasks.shadowJar, otel)
    group = "build"
    description = "Builds the AgentTel javaagent — OTel agent + AgentTel extension in a single JAR"

    // Use empty classifier so this becomes the main artifact
    archiveClassifier.set("")

    // Extract the upstream OTel javaagent
    from(zipTree(otel.singleFile))

    // Add AgentTel extension into the extensions/ directory
    from(tasks.shadowJar.get().archiveFile) {
        into("extensions")
    }

    duplicatesStrategy = DuplicatesStrategy.EXCLUDE

    // Preserve the upstream agent's manifest (includes Premain-Class)
    doFirst {
        manifest.from(
            zipTree(otel.singleFile).matching {
                include("META-INF/MANIFEST.MF")
            }.singleFile
        )
    }
}

tasks.named("assemble") {
    dependsOn("agentJar")
}

tasks.test {
    val agentJar = tasks.named<Jar>("agentJar")
    dependsOn(agentJar)
    inputs.files(integrationApp)
    doFirst {
        systemProperty("agenttel.it.agentJar", agentJar.get().archiveFile.get().asFile.absolutePath)
        systemProperty("agenttel.it.appClasspath",
            (sourceSets["test"].output.classesDirs.files + integrationApp.files).joinToString(File.pathSeparator))
    }
}

// Wire the agentJar as the main artifact for publishing
afterEvaluate {
    val agentJarTask = tasks.named<Jar>("agentJar")
    configurations.named("runtimeElements") {
        outgoing.artifacts.clear()
        outgoing.artifact(agentJarTask)
    }
    configurations.named("apiElements") {
        outgoing.artifacts.clear()
        outgoing.artifact(agentJarTask)
    }
}
