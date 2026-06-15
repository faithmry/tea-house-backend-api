package com.example.teahouse.models

import kotlinx.serialization.Serializable
import org.jetbrains.exposed.sql.Table

@Serializable
data class Transaction(
    val id: String,
    val memberId: String,
    val amount: Double,
    val pointsEarned: Int,
    val date: String,
    val type: String
)

object Transactions : Table() {
    val id = varchar("id", 50)
    val memberId = varchar("member_id", 50) references Members.id
    val amount = double("amount")
    val pointsEarned = integer("points_earned")
    val date = varchar("date", 50)
    val type = varchar("type", 20).default("PURCHASE")

    override val primaryKey = PrimaryKey(id)
}
