plugins {
    kotlin("multiplatform") version "1.8.0"
    id("com.android.library") version "7.2.1"
    kotlin("plugin.serialization") version "1.8.0"
}

group = "thisisthepy"
version = "1.0-SNAPSHOT"

kotlin {
    android()
    ios()
    jvm("windows")
    mingwX64("mingw")

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-core:2.0.0")
                implementation("io.ktor:ktor-client-websockets:2.0.0")
                implementation("io.ktor:ktor-client-serialization:2.0.0")
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.6.0")
                implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.3.2")
            }
        }
        val androidMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-okhttp:2.0.0") // Replace with appropriate client
            }
        }
        val iosMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-ios:2.0.0")
            }
        }
        val windowsMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-cio:2.0.0")
            }
        }
        val mingwMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-cio:2.0.0")
            }
        }
    }
}
