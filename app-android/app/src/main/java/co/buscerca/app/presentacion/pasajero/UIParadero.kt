package co.buscerca.app.presentacion.pasajero

import android.os.Bundle
import android.widget.LinearLayout
import co.buscerca.app.datos.Bus
import co.buscerca.app.presentacion.*
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** CU-15 Consultar tiempo de llegada al paradero (HU-0304). */
class UIParadero : PantallaBase() {
    private lateinit var lista: LinearLayout
    private lateinit var p: Pantalla
    private var idRuta = 0
    private var idParadero = 0
    private var refresco: Job? = null

    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        idRuta = intent.getIntExtra("ruta", 0); idParadero = intent.getIntExtra("paradero", 0)
        p = Pantalla(this, "Paradero", "Llegadas estimadas")
        lista = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        p.contenido.agregar(lista, 6)
        p.contenido.agregar(botonBorde("★ Guardar paradero en favoritos") { guardarFavorito(idRuta, idParadero, p.tituloView.text.toString()) }, 14)
        p.contenido.agregar(botonBorde("Ver la ruta en el mapa") { irA(UIMapaRuta::class.java) { putExtra("ruta", idRuta); putExtra("paradero", idParadero) } }, 8)
        pestanasPasajero(p, "")
    }

    override fun onResume() { super.onResume(); refresco = launch { while (true) { cargar(); delay(10_000) } } }
    override fun onPause() { refresco?.cancel(); super.onPause() }

    private suspend fun cargar() {
        try {
            val r = api.llegadas(idParadero, idRuta)
            p.tituloView.text = r.paradero.nombre
            p.subtitulo("Se actualiza cada 10 s · ${r.paradero.municipio}")
            lista.removeAllViews()
            r.llegadas.forEach { lista.agregar(fila(it), 10) }
            if (r.mensaje != null) lista.agregar(cajaAviso(r.mensaje + (r.proxima_salida?.let { "\nPróxima salida: $it" } ?: "")), 10)   // CP-0304-05
        } catch (e: Exception) { lista.removeAllViews(); lista.agregar(cajaAviso(co.buscerca.app.datos.ClienteApi.mensaje(e)), 10) }
    }

    /** "8 min", "Llegando", "Ya pasó" o "10 min aprox." (RN-308 y RN-309). */
    private fun fila(b: Bus) = tarjeta().apply {
        orientation = LinearLayout.HORIZONTAL
        addView(texto("Bus ${b.numero_interno}\n${b.placa}", 15f, negrita = true), LinearLayout.LayoutParams(0, -2, 1f))
        val e = b.eta
        val color = when (e?.estado) { "LLEGANDO" -> Colores.NARANJA; "YA_PASO" -> Colores.GRIS_CLARO; else -> Colores.VERDE }
        addView(texto(e?.texto ?: "—", 22f, color, true))
        setOnClickListener { UIDetalleVehiculo.mostrar(this@UIParadero, b.id_recorrido) { launch { cargar() } } }
    }
}
