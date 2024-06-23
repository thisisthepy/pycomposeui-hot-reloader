import io.ktor.network.selector.*
import io.ktor.network.sockets.*
import io.ktor.utils.io.*
import kotlinx.coroutines.*
import java.io.File
import java.io.IOException
import java.util.zip.ZipInputStream

class SocketClient {

    private var socket: Socket? = null
    private var readChannel: ByteReadChannel? = null
    private var writeChannel: ByteWriteChannel? = null

    suspend fun connect(host: String, port: Int, pathInfo: String = "") {
        val selectorManager = ActorSelectorManager(Dispatchers.IO)
        socket = aSocket(selectorManager).tcp().connect(host, port)
        readChannel = socket?.openReadChannel()
        writeChannel = socket?.openWriteChannel(autoFlush = true)
        // Send the initial pathInfo message to the server
        send("GET $pathInfo HTTP/1.1\r\nHost: $host\r\n\r\n")
    }

    suspend fun send(message: String) {
        writeChannel?.writeStringUtf8("$message\n")
    }

    suspend fun receive(): String {
        return readChannel?.readUTF8Line() ?: throw IOException("Connection closed")
    }

    fun close() {
        socket?.close()
    }
}

fun main() = runBlocking {
    launch {
        reloadApplication(host = "localhost", port = 8000, pathInfo = "/client/", clientType = "android", appExtension = "zip")
    }
    while (true) {
        /* the place to run the main function of the application */
    }
}

fun CoroutineScope.reloadApplication(host: String, port: Int, pathInfo: String, clientType: String, appExtension: String) = launch {
    val pathName = "$pathInfo$clientType"
    while (true) {
        try {
            val response = getNewestFile(host=host, port=port, pathInfo=pathName)
            updateFile(response=response, clientType=clientType, appExtension=appExtension)
        } catch (e: Exception) {
            e.printStackTrace()
        }
        delay(10000) // Adding a delay to prevent constant looping
    }
}

suspend fun getNewestFile(host: String, port: Int, pathInfo: String): String {
    val client = SocketClient()
    return try {
        client.connect(host, port, pathInfo)
        client.send("Hello, server!")

        client.receive()
    } catch (e: Exception) {
        e.printStackTrace()
        throw e
    } finally {
        client.close()
    }
}

fun updateFile(response: String, clientType: String, appExtension: String) {
    val fileName = "$clientType.$appExtension"
    try {
        val zipInputStream = ZipInputStream(response.byteInputStream())
        zipInputStream.use { zip ->
            var entry = zip.nextEntry
            while (entry != null) {
                if (entry.name.contains(fileName)) {
                    zip.copyTo(File(fileName).outputStream())
                    File(fileName).setExecutable(true)
                    println("Successfully Updated $fileName.")
                    break
                }
                entry = zip.nextEntry
            }
        }
    } catch (e: IOException) {
        e.printStackTrace()
    }
}
