package co.buscerca.app.presentacion

import android.app.AlertDialog
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import co.buscerca.app.datos.Credenciales
import co.buscerca.app.presentacion.cuenta.UIRecuperarContrasena
import co.buscerca.app.presentacion.cuenta.UIRegistro
import co.buscerca.app.presentacion.conductor.UIIniciarRecorrido
import co.buscerca.app.presentacion.pasajero.UIBuscarRutas

/** Inicio de sesión (Módulo 01). Lleva a cada usuario a su panel según el rol. */
class UIIniciarSesion : PantallaBase() {

    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        if (sesion.token != null) { abrirPanel(sesion.rol); return }
        val p = Pantalla(this, "BusCerca", "Transporte rural en tiempo real")
        val c = p.contenido
        c.agregar(texto("Inicia sesión", 20f, negrita = true), 20)
        val correo = campo("Correo", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS)
        val clave = campo("Contraseña", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD)
        val error = texto("", 14f, Colores.ROJO)
        c.agregar(correo, 16); c.agregar(clave); c.agregar(error, 6)
        val ingresar = boton("Ingresar") {}
        ingresar.setOnClickListener {
            error.text = ""
            if (correo.text.isBlank() || clave.text.isBlank()) { error.text = "Escribe tu correo y tu contraseña"; return@setOnClickListener }
            ingresar.isEnabled = false
            tarea({ _, m -> error.text = m; ingresar.isEnabled = true }) {
                val r = api.login(Credenciales(correo.text.toString().trim(), clave.text.toString()))
                sesion.guardar(r)
                abrirPanel(r.usuario.rol)
            }
        }
        c.agregar(ingresar, 12)
        c.agregar(texto("¿Olvidaste tu contraseña?", 15f, Colores.VERDE, true).apply {
            gravity = Gravity.CENTER; setPadding(0, dp(8), 0, dp(8)); setOnClickListener { irA(UIRecuperarContrasena::class.java) }
        }, 10)
        c.agregar(botonBorde("Crear cuenta") { irA(UIRegistro::class.java) }, 6)
        val servidor = texto("Servidor: ${sesion.servidor}", 13f, Colores.GRIS).apply { gravity = Gravity.CENTER }
        servidor.setOnClickListener {
            val e = campo("http://192.168.0.10:8000/").apply { setText(sesion.servidor) }
            AlertDialog.Builder(this).setTitle("Dirección del servidor").setView(e).setNegativeButton("Cancelar", null)
                .setPositiveButton("Guardar") { _, _ -> sesion.servidor = e.text.toString().trim(); servidor.text = "Servidor: ${sesion.servidor}" }.show()
        }
        c.agregar(servidor, 28)
    }

    private fun abrirPanel(rol: String?) {
        when (rol) {
            "CONDUCTOR" -> irA(UIIniciarRecorrido::class.java, limpiar = true)
            "PASAJERO" -> irA(UIBuscarRutas::class.java, limpiar = true)
            else -> { aviso("El panel de administración se construye en el Módulo 05"); sesion.cerrar(); return }
        }
        finish()
    }
}
