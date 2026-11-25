package co.buscerca.app.presentacion.pasajero

import android.app.AlertDialog
import android.os.Bundle
import android.widget.LinearLayout
import co.buscerca.app.datos.Favorito
import co.buscerca.app.datos.Renombrar
import co.buscerca.app.dominio.ValidadorFavorito
import co.buscerca.app.presentacion.*

/** CU-17 Administrar favoritos (HU-0305): abrir con un toque, renombrar y eliminar. */
class UIFavoritos : PantallaBase() {
    private lateinit var lista: LinearLayout

    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        val p = Pantalla(this, "Mis favoritos", "Máximo 10")
        lista = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        p.contenido.agregar(lista, 6)
        pestanasPasajero(p, "favoritos")
    }

    override fun onResume() { super.onResume(); cargar() }

    private fun cargar(): kotlinx.coroutines.Job = tarea {
        val fs = api.favoritos()
        lista.removeAllViews()
        if (fs.isEmpty()) lista.agregar(cajaAviso("Aún no tienes favoritos. Guarda una ruta o un paradero desde la búsqueda."), 12)
        else lista.agregar(texto("${fs.size} de 10 favoritos", 14f, Colores.GRIS, true), 10)
        fs.forEach { lista.agregar(tarjetaFavorito(it), 10) }
    }

    private fun tarjetaFavorito(f: Favorito) = tarjeta().apply {
        addView(texto(f.titulo, 17f, negrita = true))
        addView(texto(listOfNotNull(f.ruta_codigo?.let { "$it ${f.ruta_nombre}" }, f.paradero_nombre?.let { "Paradero $it" }).joinToString(" · "), 14f, Colores.GRIS))
        f.aviso?.let { addView(texto(it, 14f, Colores.ROJO, true)) }   // "Ruta no disponible"
        val fila = LinearLayout(context).apply { orientation = LinearLayout.HORIZONTAL }
        fila.addView(botonBorde("Renombrar") { renombrar(f) }, LinearLayout.LayoutParams(0, -2, 1f).apply { rightMargin = dp(6) })
        fila.addView(botonBorde("Eliminar", Colores.ROJO) { eliminar(f) }, LinearLayout.LayoutParams(0, -2, 1f))
        agregar(fila, 8)
        setOnClickListener { abrir(f) }
    }

    private fun abrir(f: Favorito) {
        if (!f.disponible) { aviso("Ruta no disponible"); return }
        when {
            f.id_ruta != null -> irA(UIMapaRuta::class.java) { putExtra("ruta", f.id_ruta); putExtra("paradero", f.id_paradero ?: 0) }
            else -> aviso("Busca una ruta que pase por ${f.paradero_nombre}")
        }
    }

    private fun renombrar(f: Favorito) {
        val e = campo("Nuevo alias (máx. 30)").apply { setText(f.alias ?: "") }
        AlertDialog.Builder(this).setTitle("Renombrar favorito").setView(e).setNegativeButton("Cancelar", null)
            .setPositiveButton("Guardar") { _, _ ->
                val a = e.text.toString()
                ValidadorFavorito.validarAlias(a)?.let { aviso(it); return@setPositiveButton }   // CP-0305-04
                tarea { api.renombrarFavorito(f.id_favorito, Renombrar(a.ifBlank { null })); cargar() }
            }.show()
    }

    private fun eliminar(f: Favorito) = confirmar("Eliminar favorito", "¿Eliminar \"${f.titulo}\"?", "Eliminar") {
        tarea { api.eliminarFavorito(f.id_favorito); cargar() }
    }
}
