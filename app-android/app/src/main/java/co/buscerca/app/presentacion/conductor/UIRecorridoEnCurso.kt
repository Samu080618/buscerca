package co.buscerca.app.presentacion.conductor

import android.Manifest
import android.app.AlertDialog
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.Gravity
import android.view.View
import co.buscerca.app.datos.AlmacenLocal
import co.buscerca.app.datos.RecorridoInfo
import co.buscerca.app.dominio.Envio
import co.buscerca.app.dominio.formatoVelocidad
import co.buscerca.app.presentacion.*
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** Pantalla del recorrido EN CURSO: GPS activo, velocidad promedio (HU-0203), novedad (HU-0204) y finalizar (HU-0205). */
class UIRecorridoEnCurso : PantallaBase() {
    private var id = -1
    private lateinit var p: Pantalla
    private lateinit var datos: android.widget.TextView
    private lateinit var gps: android.widget.TextView
    private lateinit var velocidad: android.widget.TextView
    private lateinit var pendientes: android.widget.TextView
    private var refresco: Job? = null

    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        id = intent.getIntExtra("id", sesion.recorridoActivo)
        p = Pantalla(this, "Recorrido en curso", "Ruta —")
        val c = p.contenido
        gps = texto("● GPS activo · enviando cada 10 s", 14f, Colores.VERDE, true).apply {
            background = fondo(Colores.VERDE_CLARO, 20, ctx = context); setPadding(dp(12), dp(6), dp(12), dp(6))
        }
        c.agregar(gps, 14)
        pendientes = cajaAviso("").apply { visibility = View.GONE }
        c.agregar(pendientes, 10)
        val t = tarjeta()
        datos = texto("", 15f)
        t.addView(datos)
        c.agregar(t, 12)
        val tv = tarjeta().apply { gravity = Gravity.CENTER_HORIZONTAL }
        tv.addView(texto("Velocidad promedio (5 min)", 14f, Colores.GRIS).apply { gravity = Gravity.CENTER })
        velocidad = texto("— km/h", 34f, Colores.VERDE_OSCURO, true).apply { gravity = Gravity.CENTER }
        tv.addView(velocidad)
        c.agregar(tv, 12)
        c.agregar(boton("⚠ Reportar novedad", Colores.NARANJA) { irA(UIReportarNovedad::class.java) { putExtra("id", id) } }, 18)
        c.agregar(boton("■ Finalizar recorrido", Colores.ROJO) { confirmarFinalizar() }, 10)
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED && !ServicioGPS.enEjecucion)
            ServicioGPS.iniciar(this, id)
    }

    override fun onResume() {
        super.onResume()
        refresco = launch { while (true) { actualizar(); delay(10_000) } }
    }

    override fun onPause() { refresco?.cancel(); super.onPause() }

    private suspend fun actualizar() {
        val n = AlmacenLocal(this).contar(id)
        val sinRed = ServicioGPS.ultimoEnvio == Envio.SIN_CONEXION
        pendientes.visibility = if (n > 0 || sinRed) View.VISIBLE else View.GONE
        pendientes.text = "Sin conexión: $n ubicaciones guardadas en el teléfono. Se enviarán en orden al volver la señal."
        gps.text = if (ServicioGPS.enEjecucion) "● GPS activo · enviando cada 10 s" else "○ GPS detenido"
        gps.setTextColor(if (ServicioGPS.enEjecucion) Colores.VERDE else Colores.ROJO)
        try {
            val r = api.recorridoActivo()
            if (r.code() == 404) { cerrado(); return }
            r.body()?.let { mostrar(it) }
        } catch (_: Exception) { /* sin conexión: se mantiene lo último mostrado */ }
    }

    private fun mostrar(r: RecorridoInfo) {
        p.subtitulo("Ruta ${r.ruta.codigo} · ${r.ruta.nombre}")
        datos.text = "Vehículo ${r.vehiculo.numero_interno} · ${r.vehiculo.placa}\nInicio: ${r.fecha_inicio.substring(11, 16)}"
        velocidad.text = formatoVelocidad(r.velocidad_promedio)   // CP-0203-04
    }

    /** CU-206: confirmar; Cancelar deja todo igual (CP-0205-01). */
    private fun confirmarFinalizar() = confirmar("Finalizar recorrido", "Se dejará de compartir tu ubicación. ¿Quieres finalizar?", "Finalizar") {
        tarea {
            val r = ServicioGPS.sincronizador(this, id).vaciar()          // CP-0205-02: primero las pendientes
            if (r == Envio.SIN_CONEXION) { aviso("No fue posible conectar con el servidor. Intenta de nuevo."); return@tarea }
            val fin = api.finalizar(id)
            ServicioGPS.detener(this)                                       // CP-0205-03: se retira la notificación
            AlmacenLocal(this).limpiar(id)
            sesion.recorridoActivo = -1
            resumen(fin)
        }
    }

    private fun resumen(r: RecorridoInfo) {
        AlertDialog.Builder(this).setTitle("Recorrido finalizado")
            .setMessage("Ruta ${r.ruta.codigo}\nInicio: ${r.fecha_inicio.substring(11, 16)}\nFin: ${r.fecha_fin?.substring(11, 16)}\n" +
                "Duración: ${r.duracion_minutos} min\nUbicaciones enviadas: ${r.ubicaciones_registradas}")
            .setCancelable(false).setPositiveButton("Aceptar") { _, _ -> irA(UIIniciarRecorrido::class.java, limpiar = true) }.show()
    }

    private fun cerrado() {
        ServicioGPS.detener(this); sesion.recorridoActivo = -1
        aviso("El recorrido ya no está en curso"); irA(UIIniciarRecorrido::class.java, limpiar = true)
    }
}
