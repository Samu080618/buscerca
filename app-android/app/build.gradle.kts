plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "co.buscerca.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "co.buscerca.app"
        minSdk = 26
        targetSdk = 34
        versionCode = 3
        versionName = "0.3.0-sprint3"
        // Dirección de la API. En el emulador 10.0.2.2 es el computador; en un celular use la IP del servidor.
        // También se puede cambiar desde la pantalla de inicio de sesión (enlace "Servidor").
        // GitHub Actions la toma de la variable del repositorio API_URL (ver .github/workflows/apk.yml).
        val apiUrl = ((project.findProperty("apiUrl") as String?)?.takeIf { it.isNotBlank() } ?: "http://10.0.2.2:8000/")
            .let { if (it.endsWith("/")) it else "$it/" }
        buildConfigField("String", "API_URL", "\"$apiUrl\"")
    }

    buildFeatures { buildConfig = true }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-gson:2.11.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
    implementation("org.osmdroid:osmdroid-android:6.1.20")   // mapa con teselas de OpenStreetMap

    testImplementation("junit:junit:4.13.2")
}
