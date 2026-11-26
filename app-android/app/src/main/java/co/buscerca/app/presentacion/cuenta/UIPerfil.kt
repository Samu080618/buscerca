package co.buscerca.app.presentacion.cuenta

import android.app.AlertDialog
import android.os.Bundle
import android.text.InputType
import android.widget.LinearLayout
import co.buscerca.app.datos.CambioClave
import co.buscerca.app.datos.DatosPerfil
import co.buscerca.app.dominio.ValidadorCuenta
import co.buscerca.app.presentacion.*

/** HU-0104 Edición de datos del perfil y HU-0105 Cierre de sesión seguro. */
class UIPerfil : PantallaBase() {
    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        val p = Pantalla(this, "Mi perfil", sesion.nombre)
        val c = p.contenido
        val cuenta = texto("", 14f, Colores.GRIS)
        val nombre = campo("Nombre completo", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_WORDS)
        val telefono = campo("Celular", InputType.TYPE_CLASS_PHONE)
        val direccion = campo("Dirección o vereda")
        val error = texto("", 14f, Colores.ROJO)
        c.agregar(cuenta, 14)
        c.agregar(texto("Nombre", 14f, Colores.GRIS, true), 12); c.agregar(nombre, 4)
        c.agregar(texto("Celular", 14f, Colores.GRIS, true), 10); c.agregar(telefono, 4)
        c.agregar(texto("Dirección", 14f, Colores.GRIS, true), 10); c.agregar(direccion, 4)
        c.agregar(error, 8)
        c.agregar(boton("Guardar cambios") {
            val msg = ValidadorCuenta.nombre(nombre.text.toString()) ?: ValidadorCuenta.telefono(telefono.text.toString())
            if (msg != null) { error.text = msg; return@boton }
            error.text = ""
            tarea({ _, m -> error.text = m }) {
                val r = api.editarPerfil(DatosPerfil(nombre.text.toString(), telefono.text.toString().ifBlank { null }, direccion.text.toString().ifBlank { null }))
                sesion.nombre = r.nombre; p.subtitulo(r.nombre); aviso(r.mensaje ?: "Datos actualizados")
            }
        }, 6)
        c.agregar(botonBorde("Cambiar contraseña") { cambiarClave() }, 10)
        c.agregar(botonBorde("Cerrar sesión", Colores.ROJO) { cerrarSesion() }, 10)
        tarea({ _, m -> error.text = m }) {
            val pf = api.perfil()
            cuenta.text = "${pf.correo} · ${pf.rol.lowercase().replaceFirstChar { it.uppercase() }}"
            nombre.setText(pf.nombre); telefono.setText(pf.telefono ?: ""); direccion.setText(pf.direccion ?: "")
        }
    }

    private fun cambiarClave() {
        val caja = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(20), dp(8), dp(20), 0) }
        val actual = campo("Contraseña actual", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD)
        val nueva = campo("Nueva contraseña", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD)
        caja.agregar(actual, 4); caja.agregar(nueva, 8)
        AlertDialog.Builder(this).setTitle("Cambiar contraseña").setView(caja).setNegativeButton("Cancelar", null)
            .setPositiveButton("Cambiar") { _, _ ->
                ValidadorCuenta.contrasena(nueva.text.toString())?.let { aviso(it); return@setPositiveButton }
                tarea { aviso(api.cambiarClave(CambioClave(actual.text.toString(), nueva.text.toString())).mensaje) }
            }.show()
    }
}
