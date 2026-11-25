package co.buscerca.app.presentacion.pasajero

import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.ViewGroup.LayoutParams.MATCH_PARENT
import android.widget.LinearLayout
import co.buscerca.app.datos.Bus
import co.buscerca.app.datos.Trazado
import co.buscerca.app.presentacion.*
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker
import org.osmdroid.views.overlay.Polyline

/** CU-13 Visualizar bus en el mapa (HU-0302): trazado, paraderos y buses que se refrescan cada 10 s (RN-305). */
class UIMapaRuta : PantallaBase() {
    private lateinit var mapa: MapView
    private lateinit var estado: android.widget.TextView
    private val marcadores = mutableListOf<Marker>()
    private var idRuta = 0
    private var idParadero = 0
    private var refresco: Job? = null
    private var segundos = 10

    override fun onCreate(estado0: Bundle?) {
        super.onCreate(estado0)
        Configuration.getInstance().userAgentValue = packageName   // requerido por los servidores de OpenStreetMap
        idRuta = intent.getIntExtra("ruta", 0); idParadero = intent.getIntExtra("paradero", 0)
        val p = Pantalla(this, "Ruta", "Cargando…", desplazable = false)
        p.contenido.setPadding(0, 0, 0, 0)
        mapa = MapView(this).apply { setTileSource(TileSourceFactory.MAPNIK); setMultiTouchControls(true); controller.setZoom(13.5) }
        p.contenido.addView(mapa, LinearLayout.LayoutParams(MATCH_PARENT, 0, 1f))
        val panel = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setBackgroundColor(Color.WHITE); setPadding(dp(16), dp(10), dp(16), dp(12)) }
        estado = texto("", 15f, Colores.TEXTO, true)
        panel.addView(estado)
        if (idParadero > 0) panel.agregar(boton("Ver llegadas a mi paradero") { irA(UIParadero::class.java) { putExtra("ruta", idRuta); putExtra("paradero", idParadero) } }, 8)
        p.contenido.addView(panel)
        pestanasPasajero(p, "")
        tarea {
            val t = api.trazado(idRuta)
            p.tituloView.text = "${t.codigo} ${t.nombre}"; p.subtitulo(if (t.estado == "Activa") "Se actualiza cada ${t.refresco_segundos} s" else "Ruta no disponible")
            segundos = t.refresco_segundos
            dibujarRuta(t)
        }
    }

    override fun onResume() {
        super.onResume(); mapa.onResume()
        refresco = launch { while (true) { cargarBuses(); delay(segundos * 1000L) } }
    }

    override fun onPause() { refresco?.cancel(); mapa.onPause(); super.onPause() }

    private fun punto(color: Int, tam: Int) = GradientDrawable().apply {
        shape = GradientDrawable.OVAL; setColor(color); setStroke(dp(3), Color.WHITE); setSize(dp(tam), dp(tam))
    }

    private fun dibujarRuta(t: Trazado) {
        val linea = Polyline(mapa).apply {
            setPoints(t.trazado.map { GeoPoint(it[0], it[1]) }); outlinePaint.color = Colores.VERDE; outlinePaint.strokeWidth = dp(5).toFloat()
        }
        mapa.overlays.add(0, linea)
        t.paraderos.forEach { pa ->
            mapa.overlays.add(Marker(mapa).apply {
                position = GeoPoint(pa.latitud, pa.longitud); title = pa.nombre
                icon = punto(if (pa.id_paradero == idParadero) Colores.NARANJA else Colores.VERDE_OSCURO, 14)
                setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)
                setOnMarkerClickListener { _, _ -> irA(UIParadero::class.java) { putExtra("ruta", idRuta); putExtra("paradero", pa.id_paradero) }; true }
            })
        }
        val centro = t.paraderos.firstOrNull { it.id_paradero == idParadero } ?: t.paraderos.getOrNull(t.paraderos.size / 2)
        centro?.let { mapa.controller.setCenter(GeoPoint(it.latitud, it.longitud)) }
        mapa.invalidate()
    }

    private suspend fun cargarBuses() {
        try {
            val r = api.buses(idRuta, idParadero.takeIf { it > 0 })
            mapa.overlays.removeAll(marcadores); marcadores.clear()
            r.buses.forEach { b -> marcadores += marcadorBus(b) }
            mapa.overlays.addAll(marcadores); mapa.invalidate()
            estado.text = when {
                r.buses.isEmpty() -> "No hay buses en camino" + (r.proxima_salida?.let { " · Próxima salida $it" } ?: "")   // CP-0302-04
                else -> r.buses.joinToString("\n") { b -> "Bus ${b.numero_interno}: " + (b.etiqueta ?: b.eta?.texto ?: "en ruta") }
            }
        } catch (e: Exception) { estado.text = co.buscerca.app.datos.ClienteApi.mensaje(e) }
    }

    /** RN-306: verde con señal; gris con "Sin señal desde hh:mm". Al tocarlo abre la ficha (CU-14). */
    private fun marcadorBus(b: Bus) = Marker(mapa).apply {
        position = GeoPoint(b.latitud, b.longitud)
        title = "Bus ${b.numero_interno}"; snippet = b.etiqueta ?: b.eta?.texto
        icon = punto(if (b.senal == "ACTIVA") Colores.VERDE else Colores.GRIS_CLARO, 24)
        setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)
        setOnMarkerClickListener { _, _ -> UIDetalleVehiculo.mostrar(this@UIMapaRuta, b.id_recorrido) { launch { cargarBuses() } }; true }
    }
}
