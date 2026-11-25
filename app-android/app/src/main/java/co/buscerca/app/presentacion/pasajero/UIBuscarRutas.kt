package co.buscerca.app.presentacion.pasajero

import android.Manifest
import android.os.Bundle
import android.view.inputmethod.EditorInfo
import android.widget.LinearLayout
import co.buscerca.app.datos.ResultadoRuta
import co.buscerca.app.dominio.ValidadorBusqueda
import co.buscerca.app.presentacion.*

/** CU-12 Buscar rutas por destino (HU-0301). */
class UIBuscarRutas : PantallaBase() {
    private lateinit var resultados: LinearLayout
    private lateinit var mensaje: android.widget.TextView

    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        val p = Pantalla(this, "¿A dónde vas?", "Hola, ${sesion.nombre ?: "pasajero"}")
        val c = p.contenido
        val texto = campo("Escribe tu destino: vereda, paradero o municipio")
        c.agregar(texto, 14)
        mensaje = texto("", 14f, Colores.ROJO); c.agregar(mensaje, 6)
        c.agregar(boton("Buscar rutas") { buscar(texto.text.toString()) }, 6)
        texto.setOnEditorActionListener { _, accion, _ -> if (accion == EditorInfo.IME_ACTION_SEARCH || accion == EditorInfo.IME_ACTION_DONE) { buscar(texto.text.toString()); true } else false }
        resultados = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        c.agregar(resultados, 8)
        pestanasPasajero(p, "buscar")
        requestPermissions(arrayOf(Manifest.permission.ACCESS_COARSE_LOCATION, Manifest.permission.ACCESS_FINE_LOCATION), 3)
    }

    private fun buscar(t: String) {
        mensaje.text = ""
        ValidadorBusqueda.validar(t)?.let { mensaje.text = it; return }   // CP-0301-02: no se envía la petición
        val (lat, lon) = ubicacionPasajero()
        resultados.removeAllViews()
        resultados.agregar(texto("Buscando…", 14f, Colores.GRIS))
        tarea({ _, m -> resultados.removeAllViews(); mensaje.text = m }) {
            val r = api.buscarRutas(t.trim(), lat, lon)
            resultados.removeAllViews()
            if (r.resultados.isEmpty()) { resultados.agregar(cajaAviso(r.mensaje ?: "No encontramos rutas"), 12); return@tarea }   // CP-0301-05
            resultados.agregar(texto("${r.resultados.size} rutas hacia ${r.resultados[0].destino.nombre}", 14f, Colores.GRIS, true), 12)
            r.resultados.forEach { resultados.agregar(tarjetaRuta(it), 10) }
        }
    }

    private fun tarjetaRuta(r: ResultadoRuta) = tarjeta().apply {
        addView(texto("${r.codigo}  ${r.nombre}", 17f, negrita = true))
        addView(texto("Sube en ${r.abordaje.nombre} (${r.abordaje.metros} m) · ${r.sentido}", 14f, Colores.GRIS))
        addView(texto("${r.vehiculos_operando} vehículo(s) operando", 13f, Colores.GRIS))
        val estado = r.proximo_bus?.indicador ?: (r.proxima_salida?.let { "Sin buses en camino · próxima salida $it" } ?: "Sin buses en camino")
        addView(texto(estado, 15f, if (r.proximo_bus != null) Colores.VERDE else Colores.NARANJA, true).apply { setPadding(0, dp(6), 0, 0) })
        val fila = LinearLayout(context).apply { orientation = LinearLayout.HORIZONTAL }
        fila.addView(botonBorde("Ver en el mapa") { abrirMapa(r) }, LinearLayout.LayoutParams(0, -2, 1f).apply { rightMargin = dp(6) })
        fila.addView(botonBorde("★ Guardar") { guardarFavorito(r.id_ruta, r.abordaje.id_paradero, "") }, LinearLayout.LayoutParams(0, -2, 1f))
        agregar(fila, 8)
        setOnClickListener { abrirMapa(r) }
    }

    private fun abrirMapa(r: ResultadoRuta) = irA(UIMapaRuta::class.java) { putExtra("ruta", r.id_ruta); putExtra("paradero", r.abordaje.id_paradero) }
}
