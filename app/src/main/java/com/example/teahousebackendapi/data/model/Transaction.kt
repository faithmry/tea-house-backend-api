package com.example.teahousebackendapi.data.model

import kotlinx.serialization.Serializable

@Serializable
data class Transaction(
    val id: String,
    val memberId: String,
    val amount: Double,
    val pointsEarned: Int,
    val date: String,
    val type: String = "PURCHASE"
)

@Serializable
data class TransactionRequest(
    val memberId: String,
    val amount: Double
)
