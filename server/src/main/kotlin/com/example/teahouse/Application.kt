package com.example.teahouse

import com.example.teahouse.plugins.*
import com.example.teahouse.routes.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.routing.*
import io.ktor.server.response.*
import io.ktor.server.request.*
import io.ktor.server.auth.*
import io.ktor.http.HttpStatusCode
import org.jetbrains.exposed.sql.selectAll
import org.jetbrains.exposed.sql.transactions.transaction
import com.example.teahouse.models.Members
import kotlinx.serialization.Serializable

@Serializable
data class LoginRequest(val phone: String)

fun main() {
    embeddedServer(Netty, port = 8080, host = "0.0.0.0") {
        module()
    }.start(wait = true)
}

fun Application.module() {
    configureSecurity()
    configureSerialization()
    configureDatabases()

    routing {
        get("/") {
            call.respondText("Tea House API is Live!")
        }

        post("/login") {
            val request = try { call.receive<LoginRequest>() } catch (e: Exception) { null }
            
            // Mock login for Andi (ID: 001)
            val token = generateToken("001") 
            
            call.respond(mapOf(
                "token" to token,
                "memberId" to "001"
            ))
        }

        get("/member/{id}") {
            val idParam = call.parameters["id"] ?: return@get call.respond(HttpStatusCode.BadRequest, "Missing ID")

            val member = transaction {
                Members
                    .selectAll()
                    .where { Members.id eq idParam }
                    .map { row ->
                        com.example.teahouse.models.Member(
                            id = row[Members.id],
                            name = row[Members.name],
                            email = row[Members.email],
                            phone = row[Members.phone],
                            points = row[Members.points],
                            tier = row[Members.tier],
                            profilePictureUrl = row[Members.profilePictureUrl]
                        )
                    }.singleOrNull()
            }

            if (member != null) {
                call.respond(member)
            } else {
                call.respond(HttpStatusCode.NotFound)
            }
        }

        authenticate("auth-jwt") {
            transactionRouting()
        }
    }
}
