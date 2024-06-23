import com.android.build.gradle.internal.dsl.BaseAppModuleExtension
import org.jetbrains.kotlin.gradle.plugin.KotlinSourceSet

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.android.library).apply(false)
    alias(libs.plugins.kotlin.multiplatform)
    // kotlin("jvm")
}

apply(plugin = "com.android.application")

android {
    compileSdk = 31
    buildToolsVersion = "31.0.0"
    defaultConfig {
        applicationId = "com.kmpclient"
        minSdk = 21
        targetSdk = 33
        versionCode = 1
        versionName = "1.0"
    }

    compileOptions {
    }
    namespace = "com.kotlin.client"
}

kotlin {
    androidTarget()
    jvm()
    /*
    iosX64()
    iosArm64()
    iosSimulatorArm64()*/

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.6.4")
                implementation("io.ktor:ktor-client-core:2.0.0")
                implementation("io.ktor:ktor-client-cio:2.0.0")
                implementation("io.ktor:ktor-network:2.0.0")
            }
        }
        val androidMain by getting {
            dependencies {
                implementation("org.jetbrains.kotlin:kotlin-stdlib:1.8.0")
                implementation("io.ktor:ktor-client-okhttp:2.0.0")
            }
        }
        val jvmMain by getting {
            dependencies {
                // implementation("org.jetbrains.kotlin:kotlin-stdlib:1.8.0")
            }
        }
        /*val iosX64Main by getting
        val iosArm64Main by getting
        val iosSimulatorArm64Main by getting
        val iosMain by creating {
            dependsOn(commonMain)
            iosX64Main.dependsOn(this)
            iosArm64Main.dependsOn(this)
            iosSimulatorArm64Main.dependsOn(this)
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.6.4")
            }
        }*/
    }
    jvmToolchain(8)
}
dependencies {
    implementation(kotlin("stdlib-jdk8"))
}
repositories {
    mavenCentral()
}