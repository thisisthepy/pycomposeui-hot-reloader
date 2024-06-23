import io.ktor.network.selector.*
import io.ktor.network.sockets.*
import io.ktor.utils.io.*
import kotlinx.coroutines.*
import java.io.File
import java.io.IOException
import java.io.ByteArrayInputStream
import java.nio.file.Paths
import java.util.zip.ZipInputStream

class SocketClient {

    private var socket: Socket? = null
    private var readChannel: ByteReadChannel? = null
    private var writeChannel: ByteWriteChannel? = null

    suspend fun connect(host: String, port: Int, pathInfo: String = "") {
        val selectorManager = ActorSelectorManager(Dispatchers.IO)
        println("now trying to connect to the server")
        socket = aSocket(selectorManager).tcp().connect(host, port)
        readChannel = socket?.openReadChannel()
        writeChannel = socket?.openWriteChannel(autoFlush = true)
        // Send the initial pathInfo message to the server
        send("GET $pathInfo HTTP/1.1\r\nHost: $host\r\nConnection: close\r\n\r\n", raw = true)
    }

    suspend fun send(message: String, raw: Boolean = false) {
        if (raw) {
            writeChannel?.writeStringUtf8(message)
        } else {
            writeChannel?.writeStringUtf8("$message\n")
        }
    }


    suspend fun receive(): ByteArray {
        val headers = StringBuilder()
        var line: String?
        do {
            line = readChannel?.readUTF8Line()
            headers.append(line).append("\n")
        } while (line != null && line.isNotBlank())

        // Read the body
        val contentLength = headers.lines().find { it.startsWith("content-length:", ignoreCase = true) }
            ?.split(":")
            ?.get(1)
            ?.trim()
            ?.toInt()

        return if (contentLength != null) {
            val body = ByteArray(contentLength)
            readChannel?.readFully(body)
            body
        } else {
            throw IOException("Content-Length not found")
        }
    }


    fun close() {
        socket?.close()
    }
}

fun main() = runBlocking {
    println("now in the main function")
    val job = reloadApplication(host = "10.0.3.1", port = 8000, pathInfo = "/client/", clientType = "android", appExtension = "zip")
    while (true) {
        /* the place to run the main function of the application */
        println("Running main application function...")
        delay(5000)
    }
    job.cancel() // Cancel the job when the main loop ends
}

fun CoroutineScope.reloadApplication(host: String, port: Int, pathInfo: String, clientType: String, appExtension: String): Job = launch {
    val pathName = "$pathInfo$clientType"
    println("now in reloadApplication")
    while (true) {
        try {
            println("Attempting to get newest file...")
            val response = getNewestFile(host = host, port = port, pathInfo = pathName)
            println("Response received: $response")
            saveTempFile(response = response, clientType = clientType, appExtension = appExtension)
            // updateFile(response = response, clientType = clientType, appExtension = appExtension)
        } catch (e: Exception) {
            e.printStackTrace()
        }
        delay(10000) // Adding a delay to prevent constant looping
    }
}

suspend fun getNewestFile(host: String, port: Int, pathInfo: String): ByteArray {
    val client = SocketClient()
    return try {
        println("Connecting to $host:$port with path $pathInfo")
        client.connect(host, port, pathInfo)
        client.send("Hello, server!")
        val response = client.receive()
        println("Received response: $response")
        response
    } catch (e: Exception) {
        e.printStackTrace()
        throw e
    } finally {
        client.close()
    }
}


fun saveTempFile(response: ByteArray, clientType: String, appExtension: String) {
    val tempDir = Paths.get(System.getProperty("user.home"), "Desktop", "temp").toFile()
    if (!tempDir.exists()) {
        tempDir.mkdirs()
        println("The tempDir was made at $tempDir")
    }
    val tempFile = File(tempDir, "$clientType.$appExtension")

    try {
        val zipInputStream = ZipInputStream(ByteArrayInputStream(response))
        zipInputStream.use { zip ->
            var entry = zip.nextEntry
            println("The current entry is $entry")
            while (entry != null) {
                // TODO: make to save the whole zipped files not only the contents whose name contains 'android'.
                if (entry.name.contains(clientType)) {
                    zip.copyTo(tempFile.outputStream())
                    println("Successfully saved temporary file: ${tempFile.absolutePath}")
                    // You can then apply the file update or any other action here
                    applyUpdate(tempFile)
                    break
                }
                entry = zip.nextEntry
            }
        }
    } catch (e: IOException) {
        e.printStackTrace()
    }
}

fun applyUpdate(tempFile: File) {
    // Implementation of how you apply the update from the temp file
    val finalFile = File(tempFile.parent, tempFile.nameWithoutExtension)
    tempFile.copyTo(finalFile, overwrite = true)
    finalFile.setExecutable(true)
    println("Successfully Updated ${finalFile.absolutePath}.")
}

/*
fun updateFile(response: String, clientType: String, appExtension: String) {
    val fileName = "$clientType.$appExtension"
    val tempDir = Paths.get(System.getProperty("user.home"), "Desktop", "temp").toFile()
    if (!tempDir.exists()) {
        tempDir.mkdirs()
    }

    val tempFile = File(tempDir, "$clientType.$appExtension")

    try {
        val zipInputStream = ZipInputStream(response.byteInputStream())
        zipInputStream.use { zip ->
            var entry = zip.nextEntry
            while (entry != null) {
                if (entry.name.contains(fileName)) {
                    zip.copyTo(File(fileName).outputStream())
                    zip.copyTo(tempFile.outputStream())
                    println("Successfully saved temporary file: ${tempFile.absolutePath}")
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
}*/