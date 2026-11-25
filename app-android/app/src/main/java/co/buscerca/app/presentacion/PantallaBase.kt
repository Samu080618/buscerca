package co.buscerca.app.presentacion

import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.widget.Toast
import co.buscerca.app.datos.ApiBusCerca
import co.buscerca.app.datos.ClienteApi
import co.buscerca.app.datos.Sesion
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.MainScope
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import retrofit2.HttpException

/** Base de todas las pantallas: sesión, cliente de la API y tareas que se cancelan al cerrar la pantalla. */
abstract class PantallaBase : Activity(), CoroutineScope by MainScope() {
    val sesion by lazy { Sesion(this) }
    val api: ApiBusCerca get() = ClienteApi.de(this)

    override fun onDestroy() { cancel(); super.onDestroy() }

    /** Ejecuta una llamada a la API; ante un error muestra el mensaje y, si la sesión venció, vuelve al inicio de sesión. */
    fun tarea(alError: ((Throwable, String) -> Unit)? = null, bloque: suspend () -> Unit): Job = launch {
        try { bloque() } catch (e: Exception) {
            if (e is kotlinx.coroutines.CancellationException) throw e
            val msg = ClienteApi.mensaje(e)
            if (e is HttpException && e.code() == 401) { sesion.cerrar(); irA(UIIniciarSesion::class.java, limpiar = true); return@launch }
            if (alError != null) alError(e, msg) else aviso(msg)
        }
    }

    fun aviso(msg: String) = Toast.makeText(this, msg, Toast.LENGTH_LONG).show()

    fun irA(destino: Class<*>, limpiar: Boolean = false, extras: Intent.() -> Unit = {}) {
        val i = Intent(this, destino).apply(extras)
        if (limpiar) i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        startActivity(i)
    }

    fun confirmar(titulo: String, mensaje: String, si: String, accion: () -> Unit) {
        AlertDialog.Builder(this).setTitle(titulo).setMessage(mensaje)
            .setNegativeButton("Cancelar", null).setPositiveButton(si) { _, _ -> accion() }.show()
    }

    fun cerrarSesion() = confirmar("Cerrar sesión", "¿Quieres salir de BusCerca?", "Salir") {
        sesion.cerrar(); irA(UIIniciarSesion::class.java, limpiar = true)
    }
}
