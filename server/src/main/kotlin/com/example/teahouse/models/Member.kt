package com.example.teahouse.models

import kotlinx.serialization.Serializable
import org.jetbrains.exposed.sql.Table

@Serializable
data class Member(
    val id: String,
    val name: String,
    val email: String,
    val phone: String,
    val points: Int,
    val tier: String,
    val profilePictureUrl: String?
)

object Members : Table() {
    val id = varchar("id", 50)
    val name = varchar("name", 100)
    val email = varchar("email", 100)
    val phone = varchar("phone", 20)
    val points = integer("points").default(0)
    val tier = varchar("tier", 20).default("Bronze")
    val profilePictureUrl = varchar("profile_picture_url", 255).nullable()

    override val primaryKey = PrimaryKey(id)
}
