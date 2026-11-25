package co.buscerca.app.datos

import android.content.Context
import okhttp3.OkHttpClient
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.IOException
import java.util.concurrent.TimeUnit

/** Crea el cliente Retrofit con el token de la sesión en cada petición. */
object ClienteApi {
    private var api: ApiBusCerca? = null
    private var urlActual: String? = null

    fun de(context: Context): ApiBusCerca {
        val sesion = Sesion(context)
        if (api == null || urlActual != sesion.servidor) {
            val http = OkHttpClient.Builder()
                .connectTimeout(8, TimeUnit.SECONDS).readTimeout(10, TimeUnit.SECONDS)
                .addInterceptor { cadena ->
                    val token = Sesion(context).token
                    val pet = cadena.request().newBuilder()
                    if (token != null) pet.header("Authorization", "Bearer $token")
                    cadena.proceed(pet.build())
                }.build()
            urlActual = sesion.servidor
            api = Retrofit.Builder().baseUrl(sesion.servidor).client(http)
                .addConverterFactory(GsonConverterFactory.create()).build().create(ApiBusCerca::class.java)
        }
        return api!!
    }

    /** Convierte un error de la API o de red en el mensaje que ve el usuario. */
    fun mensaje(e: Throwable): String = when (e) {
        is HttpException -> detalle(e.response()?.errorBody()?.string()) ?: "Error ${e.code()}"
        is IOException -> "No fue posible conectar con el servidor"
        else -> e.message ?: "Error inesperado"
    }

    fun detalle(cuerpo: String?): String? {
        if (cuerpo.isNullOrBlank()) return null
        return try {
            val json = com.google.gson.JsonParser.parseString(cuerpo).asJsonObject.get("detail")
            when {
                json == null -> null
                json.isJsonPrimitive -> json.asString
                json.isJsonObject && json.asJsonObject.has("mensaje") -> json.asJsonObject.get("mensaje").asString
                else -> json.toString()
            }
        } catch (_: Exception) { null }
    }
}
