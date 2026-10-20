import com.vanniktech.maven.publish.MavenPublishBaseExtension

plugins {
    java
    `java-library`
    id("com.vanniktech.maven.publish") version "0.34.0" apply false
}

// Centralized version properties
extra["otelVersion"] = "1.59.0"
extra["otelSemconvVersion"] = "1.40.0"
extra["otelInstrumentationVersion"] = "2.25.0"
extra["springBootVersion"] = "3.4.3"
extra["jacksonVersion"] = "2.17.2"
extra["junitVersion"] = "5.11.4"
extra["assertjVersion"] = "3.27.3"
extra["mockitoVersion"] = "5.14.2"
extra["slf4jVersion"] = "2.0.16"

// GenAI dependencies (Phase 2)
extra["otelSemconvIncubatingVersion"] = "1.40.0-alpha"
extra["springAiVersion"] = "1.0.0-M6"
extra["langchain4jVersion"] = "1.0.0-beta1"
extra["anthropicSdkVersion"] = "2.0.0"
extra["openaiSdkVersion"] = "4.0.0"
extra["bedrockSdkVersion"] = "2.30.0"

allprojects {
    group = "dev.agenttel"
    version = rootProject.property("VERSION_NAME") as String

    repositories {
        mavenCentral()
    }
}

// Published library modules (not examples)
val publishedModules = setOf("agenttel-api", "agenttel-core", "agenttel-genai",
    "agenttel-agent", "agenttel-agentic", "agenttel-javaagent", "agenttel-spring-boot-starter", "agenttel-testing")

// Aggregated Javadoc across all published library modules
tasks.register<Javadoc>("aggregatedJavadoc") {
    group = "documentation"
    description = "Generates aggregated Javadoc for all library modules"
    destinationDir = file("${layout.buildDirectory.get()}/docs/javadoc")

    val published = publishedModules
    val javadocProjects = subprojects.filter { it.name in published }

    dependsOn(javadocProjects.map { it.tasks.named("classes") })

    javadocProjects.forEach { proj ->
        source(proj.sourceSets["main"].allJava)
    }
    classpath = files(javadocProjects.map { it.sourceSets["main"].compileClasspath })

    options {
        this as StandardJavadocDocletOptions
        addStringOption("Xdoclint:none", "-quiet")
        encoding = "UTF-8"
        charSet = "UTF-8"
        windowTitle = "AgentTel ${project.version} API"
        docTitle = "AgentTel ${project.version} API"
        overview = "src/javadoc/overview.html"
    }
    isFailOnError = false
}

subprojects {
    apply(plugin = "java-library")

    java {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
        toolchain {
            languageVersion.set(JavaLanguageVersion.of(17))
        }
    }

    dependencies {
        testImplementation(platform("org.junit:junit-bom:${rootProject.extra["junitVersion"]}"))
        testImplementation("org.junit.jupiter:junit-jupiter")
        testImplementation("org.assertj:assertj-core:${rootProject.extra["assertjVersion"]}")
        testImplementation("org.mockito:mockito-core:${rootProject.extra["mockitoVersion"]}")
        testImplementation("org.mockito:mockito-junit-jupiter:${rootProject.extra["mockitoVersion"]}")
    }

    tasks.withType<Test> {
        useJUnitPlatform()
    }

    tasks.withType<JavaCompile> {
        options.encoding = "UTF-8"
    }

    // Javadoc configuration for all subprojects
    tasks.withType<Javadoc> {
        options {
            this as StandardJavadocDocletOptions
            addStringOption("Xdoclint:none", "-quiet")
            encoding = "UTF-8"
            charSet = "UTF-8"
        }
        isFailOnError = false
    }

    // Publishing configuration for library modules only
    if (name in publishedModules) {
        apply(plugin = "com.vanniktech.maven.publish")

        configure<MavenPublishBaseExtension> {
            publishToMavenCentral()
            if (project.findProperty("signingInMemoryKey") != null ||
                System.getenv("ORG_GRADLE_PROJECT_signingInMemoryKey") != null) {
                signAllPublications()
            }

            pom {
                name.set(project.name)
                description.set(project.description ?: "AgentTel - Agent-ready telemetry for Java")
                url.set("https://github.com/agenttel/agenttel-sdk")

                licenses {
                    license {
                        name.set("Apache License 2.0")
                        url.set("https://www.apache.org/licenses/LICENSE-2.0")
                    }
                }

                developers {
                    developer {
                        id.set("rrohitramsen")
                        name.set("Rohit")
                    }
                }

                scm {
                    connection.set("scm:git:git://github.com/agenttel/agenttel-sdk.git")
                    developerConnection.set("scm:git:ssh://github.com/agenttel/agenttel-sdk.git")
                    url.set("https://github.com/agenttel/agenttel-sdk")
                }
            }
        }
    }
}
