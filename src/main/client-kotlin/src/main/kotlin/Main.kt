import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request


fun main() {
    val client = OkHttpClient()

    runBlocking {
        withContext(Dispatchers.IO) {
            val request = Request.Builder()
                .url("http://127.0.0.1:8000")
                .build()

            val response = client.newCall(request).execute()
            println(response.body?.string())
        }
    }
}