package com.example.teahousebackendapi

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.lifecycleScope
import com.example.teahousebackendapi.data.api.ApiService
import com.example.teahousebackendapi.data.model.Member
import com.example.teahousebackendapi.data.model.TransactionRequest
import com.example.teahousebackendapi.ui.theme.TeaHouseBackendApiTheme
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory

class MainActivity : ComponentActivity() {
    
    private lateinit var apiService: ApiService
    private var authToken by mutableStateOf<String?>(null)
    private var memberProfile by mutableStateOf<Member?>(null)
    private var isConnecting by mutableStateOf(false)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setupRetrofit()
        
        enableEdgeToEdge()
        setContent {
            TeaHouseBackendApiTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    Column(
                        modifier = Modifier
                            .padding(innerPadding)
                            .padding(16.dp)
                            .fillMaxSize()
                    ) {
                        Text(text = "TEA HOUSE API TEST", style = MaterialTheme.typography.headlineMedium)
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        if (authToken == null) {
                            Button(
                                onClick = { login() }, 
                                modifier = Modifier.fillMaxWidth(),
                                enabled = !isConnecting
                            ) {
                                Text(if (isConnecting) "Connecting..." else "Login (Get JWT)")
                            }
                        } else {
                            Text("Logged in as ID: 001", style = MaterialTheme.typography.bodySmall)
                            Spacer(modifier = Modifier.height(8.dp))
                            
                            memberProfile?.let { profile ->
                                Card(modifier = Modifier.fillMaxWidth()) {
                                    Column(modifier = Modifier.padding(16.dp)) {
                                        Text("Name: ${profile.name}", style = MaterialTheme.typography.titleLarge)
                                        Text("Points Balance: ${profile.points} pts")
                                        Text("Current Tier: ${profile.tier}")
                                    }
                                }
                                
                                Spacer(modifier = Modifier.height(16.dp))
                                
                                Button(
                                    onClick = { buyTea(50000.0) }, // Rp 50.000 = 10 Points
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text("Buy Tea (Rp 50.000)")
                                }
                            } ?: run {
                                Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                                    CircularProgressIndicator()
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    private fun setupRetrofit() {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .build()

        val json = Json { ignoreUnknownKeys = true }
        val contentType = "application/json".toMediaType()

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8080/")
            .client(client)
            .addConverterFactory(json.asConverterFactory(contentType))
            .build()

        apiService = retrofit.create(ApiService::class.java)
    }

    private fun login() {
        isConnecting = true
        lifecycleScope.launch {
            try {
                val response = apiService.login()
                authToken = response["token"]
                Log.d("TeaHouse", "Token received: $authToken")
                fetchProfile()
            } catch (e: Exception) {
                Log.e("TeaHouse", "Login failed. Ensure server is running!", e)
                isConnecting = false
            }
        }
    }

    private fun fetchProfile() {
        lifecycleScope.launch {
            try {
                memberProfile = apiService.getProfile("001")
            } catch (e: Exception) {
                Log.e("TeaHouse", "Failed to fetch profile", e)
            } finally {
                isConnecting = false
            }
        }
    }

    private fun buyTea(amount: Double) {
        val token = authToken ?: return
        lifecycleScope.launch {
            try {
                val updatedMember = apiService.postTransaction(
                    token = "Bearer $token",
                    request = TransactionRequest(memberId = "001", amount = amount)
                )
                memberProfile = updatedMember
            } catch (e: Exception) {
                Log.e("TeaHouse", "Transaction failed", e)
            }
        }
    }
}
