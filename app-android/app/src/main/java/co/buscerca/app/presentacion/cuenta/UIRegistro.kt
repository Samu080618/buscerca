package co.buscerca.app.presentacion.cuenta

import android.os.Bundle
import android.text.InputType
import android.widget.RadioButton
import android.widget.RadioGroup
import co.buscerca.app.datos.Registro
import co.buscerca.app.dominio.ValidadorCuenta
import co.buscerca.app.presentacion.*

/** HU-0101 Registro de usuario por rol (pasajero o conductor; los administradores los crea otro administrador). */
class UIRegistro : PantallaBase() {
    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        val p = Pantalla(this, "Crear cuenta", "Regístrate como pasajero o conductor")
        val c = p.contenido
        val nombre = campo("Nombre completo", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_WORDS)
        val correo = campo("Correo", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS)
        val telefono = campo("Celular (opcional)", InputType.TYPE_CLASS_PHONE)
        val clave = campo("Contraseña (mín. 8, letras y números)", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD)
        val clave2 = campo("Repite la contraseña", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD)
        val roles = RadioGroup(this).apply { orientation = RadioGroup.HORIZONTAL }
        val pasajero = RadioButton(this).apply { text = "Pasajero"; textSize = 16f; id = android.view.View.generateViewId(); isChecked = true }
        val conductor = RadioButton(this).apply { text = "Conductor"; textSize = 16f; id = android.view.View.generateViewId() }
        roles.addView(pasajero); roles.addView(conductor)
        c.agregar(texto("Soy", 14f, Colores.GRIS, true), 14); c.agregar(roles, 2)
        listOf(nombre, correo, telefono, clave, clave2).forEach { c.agregar(it, 10) }
        val error = texto("", 14f, Colores.ROJO); c.agregar(error, 8)
        val crear = boton("Crear cuenta") {}
        crear.setOnClickListener {
            val msg = ValidadorCuenta.registro(nombre.text.toString(), correo.text.toString(), clave.text.toString(), clave2.text.toString(), telefono.text.toString())
            if (msg != null) { error.text = msg; return@setOnClickListener }
            error.text = ""; crear.isEnabled = false
            tarea({ _, m -> error.text = m; crear.isEnabled = true }) {
                val r = api.registrar(Registro(nombre.text.toString().trim(), correo.text.toString().trim(), clave.text.toString(),
                    if (conductor.isChecked) "CONDUCTOR" else "PASAJERO", telefono.text.toString().ifBlank { null }))
                aviso(r.mensaje); finish()
            }
        }
        c.agregar(crear, 6)
        c.agregar(botonBorde("Ya tengo cuenta") { finish() }, 8)
    }
}
