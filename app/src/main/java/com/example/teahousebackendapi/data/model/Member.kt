package com.example.teahousebackendapi.data.model

import kotlinx.serialization.Serializable

@Serializable
data class Member(
    val id: String,
    val name: String,
    val email: String,
    val phone: String,
    val points: Int = 0,
    val tier: String = "Bronze",
    val profilePictureUrl: String? = null
)
