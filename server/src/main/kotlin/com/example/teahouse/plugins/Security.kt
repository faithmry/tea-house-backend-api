package com.example.teahouse.plugins

import com.auth0.jwt.JWT
import com.auth0.jwt.algorithms.Algorithm
import io.ktor.server.application.*
import io.ktor.server.auth.*
import io.ktor.server.auth.jwt.*
import io.ktor.server.response.*

fun Application.configureSecurity() {
    // These should be in environment variables in a real app
    val jwtAudience = "teahouse-api"
    val jwtDomain = "https://teahouse-api.railway.app/"
    val jwtRealm = "teahouse-api"
    val jwtSecret = "secret-key-change-this"

    install(Authentication) {
        jwt("auth-jwt") {
            realm = jwtRealm
            verifier(
                JWT
                    .require(Algorithm.HMAC256(jwtSecret))
                    .withAudience(jwtAudience)
                    .withIssuer(jwtDomain)
                    .build()
            )
            validate { credential ->
                if (credential.payload.audience.contains(jwtAudience)) {
                    JWTPrincipal(credential.payload)
                } else null
            }
            challenge { defaultScheme, realm ->
                call.respond(io.ktor.http.HttpStatusCode.Unauthorized, "Token is not valid or has expired")
            }
        }
    }
}

// Helper to generate token for login
fun generateToken(id: String): String {
    val jwtAudience = "teahouse-api"
    val jwtDomain = "https://teahouse-api.railway.app/"
    val jwtSecret = "secret-key-change-this"
    
    return JWT.create()
        .withAudience(jwtAudience)
        .withIssuer(jwtDomain)
        .withClaim("id", id)
        .withExpiresAt(java.util.Date(System.currentTimeMillis() + 3600000)) // 1 hour
        .sign(Algorithm.HMAC256(jwtSecret))
}
