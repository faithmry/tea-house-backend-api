package com.example.teahouse.routes

import com.example.teahouse.models.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.Serializable
import org.jetbrains.exposed.sql.*
import org.jetbrains.exposed.sql.SqlExpressionBuilder.plus
import org.jetbrains.exposed.sql.transactions.transaction
import java.util.UUID

@Serializable
data class TransactionRequest(val memberId: String, val amount: Double)

fun Route.transactionRouting() {
    route("/transactions") {
        post {
            val request = call.receive<TransactionRequest>()
            
            // 1. SERVER-SIDE CALCULATION: Rp 5.000 = 1 Point
            val pointsToAdd = (request.amount / 5000).toInt()

            val updatedMember = transaction {
                // 2. Update Member Points
                Members.update({ Members.id eq request.memberId }) {
                    it[points] = points plus pointsToAdd
                }

                // 3. Log the Transaction
                val txId = UUID.randomUUID().toString()
                Transactions.insert {
                    it[id] = txId
                    it[memberId] = request.memberId
                    it[amount] = request.amount
                    it[pointsEarned] = pointsToAdd
                    it[date] = System.currentTimeMillis().toString()
                    it[type] = "PURCHASE"
                }

                // 4. Fetch and return updated profile
                Members.selectAll().where { Members.id eq request.memberId }
                    .map {
                        Member(
                            id = it[Members.id],
                            name = it[Members.name],
                            email = it[Members.email],
                            phone = it[Members.phone],
                            points = it[Members.points],
                            tier = it[Members.tier],
                            profilePictureUrl = it[Members.profilePictureUrl]
                        )
                    }.singleOrNull()
            }

            if (updatedMember != null) {
                call.respond(updatedMember)
            } else {
                call.respond(io.ktor.http.HttpStatusCode.NotFound, "Member not found")
            }
        }
    }
}
