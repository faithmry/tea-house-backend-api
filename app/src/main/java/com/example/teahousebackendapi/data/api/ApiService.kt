package com.example.teahousebackendapi.data.api

import com.example.teahousebackendapi.data.model.Member
import com.example.teahousebackendapi.data.model.TransactionRequest
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path

interface ApiService {
    @POST("login")
    suspend fun login(): Map<String, String>

    @GET("member/{id}")
    suspend fun getProfile(
        @Path("id") id: String
    ): Member

    @POST("transactions")
    suspend fun postTransaction(
        @Header("Authorization") token: String,
        @Body request: TransactionRequest
    ): Member
}
