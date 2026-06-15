plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ktor)
    id("application")
}

group = "com.example"
version = "1.0.0"

application {
    mainClass.set("com.example.teahouse.ApplicationKt")
}

dependencies {
    implementation(libs.ktor.server.core)
    implementation(libs.ktor.server.netty)
    implementation(libs.ktor.server.content.negotiation)
    implementation(libs.ktor.serialization.kotlinx.json)
    implementation(libs.ktor.server.auth)
    implementation(libs.ktor.server.auth.jwt)
    implementation(libs.ktor.server.cors)
    
    implementation(libs.exposed.core)
    implementation(libs.exposed.jdbc)
    implementation(libs.exposed.kotlin.datetime)
    
    implementation(libs.postgresql)
    implementation(libs.h2)
    implementation(libs.logback)
}

kotlin {
    jvmToolchain(21)
}

tasks.withType<JavaExec> {
    // Inject the host parameter straight into the system properties when the server boots
    systemProperty("ktor.deployment.host", "0.0.0.0")
    systemProperty("ktor.deployment.port", "8080")
}