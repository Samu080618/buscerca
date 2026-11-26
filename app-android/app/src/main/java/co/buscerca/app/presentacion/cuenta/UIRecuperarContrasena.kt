package co.buscerca.app.presentacion.cuenta

import android.os.Bundle
import android.text.InputType
import android.view.View
import co.buscerca.app.datos.CorreoReq
import co.buscerca.app.datos.Restablecer
import co.buscerca.app.dominio.ValidadorCuenta
import co.buscerca.app.presentacion.*

/** HU-0103 Recuperación de contraseña con un código de 6 dígitos válido por 15 minutos. */
class UIRecuperarContrasena : PantallaBase() {
    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        val p = Pantalla(this, "Recuperar contraseña", "Te enviamos un código para crear una nueva")
        val c = p.contenido
        val correo = campo("Correo de tu cuenta", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS)
        val error = texto("", 14f, Colores.ROJO)
        val info = cajaAviso("", Colores.VERDE_CLARO).apply { visibility = View.GONE }
        val codigo = campo("Código de 6 dígitos", InputType.TYPE_CLASS_NUMBER)
        val nueva = campo("Nueva contraseña", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD)
        val nueva2 = campo("Repite la nueva contraseña", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD)
        val paso2 = listOf(codigo, nueva, nueva2)
        c.agregar(correo, 16)
        val enviar = boton("Enviar código") {}
        c.agregar(enviar, 10); c.agregar(info, 12)
        paso2.forEach { it.visibility = View.GONE; c.agregar(it, 10) }
        val cambiar = boton("Cambiar contraseña") {}.apply { visibility = View.GONE }
        c.agregar(error, 8); c.agregar(cambiar, 6)
        enviar.setOnClickListener {
            ValidadorCuenta.correo(correo.text.toString())?.let { error.text = it; return@setOnClickListener }
            error.text = ""
            tarea({ _, m -> error.text = m }) {
                val r = api.recuperar(CorreoReq(correo.text.toString().trim()))
                info.text = r.mensaje + (r.codigo_demo?.let { "\n\nModo demostración (sin servidor de correo): tu código es $it" } ?: "")
                info.visibility = View.VISIBLE
                paso2.forEach { it.visibility = View.VISIBLE }; cambiar.visibility = View.VISIBLE
                enviar.text = "Reenviar código"
            }
        }
        cambiar.setOnClickListener {
            val msg = (if (codigo.text.length != 6) "Escribe el código de 6 dígitos" else null)
                ?: ValidadorCuenta.contrasena(nueva.text.toString()) ?: ValidadorCuenta.coinciden(nueva.text.toString(), nueva2.text.toString())
            if (msg != null) { error.text = msg; return@setOnClickListener }
            error.text = ""
            tarea({ _, m -> error.text = m }) {
                val r = api.restablecer(Restablecer(correo.text.toString().trim(), codigo.text.toString(), nueva.text.toString()))
                aviso(r.mensaje); finish()
            }
        }
    }
}
