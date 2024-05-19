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
            }
        }
        val androidMain by getting {
            dependencies {
            }
        }
        val iosMain by getting {
            dependencies {
            }
        }
        val windowsMain by getting {
            dependencies {
            }
        }
        val mingwMain by getting {
            dependencies {
            }
        }
    }
}
