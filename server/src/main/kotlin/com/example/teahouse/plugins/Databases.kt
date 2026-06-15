package com.example.teahouse.plugins

import com.example.teahouse.models.*
import io.ktor.server.application.*
import org.jetbrains.exposed.sql.*
import org.jetbrains.exposed.sql.transactions.transaction

fun Application.configureDatabases() {
    val databaseUrl = System.getenv("DATABASE_URL") ?: "jdbc:h2:mem:test;DB_CLOSE_DELAY=-1"
    val driverClassName = if (databaseUrl.startsWith("jdbc:postgresql")) "org.postgresql.Driver" else "org.h2.Driver"
    
    Database.connect(
        url = databaseUrl,
        driver = driverClassName,
        user = System.getenv("DATABASE_USER") ?: "root",
        password = System.getenv("DATABASE_PASSWORD") ?: ""
    )

    transaction {
        SchemaUtils.create(Members, Transactions)
        
        // Optional: Add a test member if table is empty
        if (Members.selectAll().empty()) {
            Members.insert {
                it[id] = "1"
                it[name] = "Andi"
                it[email] = "andi@example.com"
                it[phone] = "08123456789"
                it[points] = 1000
                it[tier] = "Gold"
            }
        }
    }
}
