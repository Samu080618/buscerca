package co.buscerca.app.datos

import android.content.Context
import co.buscerca.app.BuildConfig

/** Datos de la sesión guardados en el teléfono (token, rol, servidor y recorrido activo). */
class Sesion(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("buscerca_sesion", Context.MODE_PRIVATE)

    var token: String? get() = prefs.getString("token", null); set(v) = prefs.edit().putString("token", v).apply()
    var rol: String? get() = prefs.getString("rol", null); set(v) = prefs.edit().putString("rol", v).apply()
    var nombre: String? get() = prefs.getString("nombre", null); set(v) = prefs.edit().putString("nombre", v).apply()
    var servidor: String
        get() = prefs.getString("servidor", null) ?: BuildConfig.API_URL
        set(v) = prefs.edit().putString("servidor", if (v.endsWith("/")) v else "$v/").apply()
    var recorridoActivo: Int
        get() = prefs.getInt("recorrido", -1)
        set(v) = prefs.edit().putInt("recorrido", v).apply()

    fun guardar(r: RespuestaLogin) { token = r.token; rol = r.usuario.rol; nombre = r.usuario.nombre }
    fun cerrar() = prefs.edit().remove("token").remove("rol").remove("nombre").remove("recorrido").apply()
}
