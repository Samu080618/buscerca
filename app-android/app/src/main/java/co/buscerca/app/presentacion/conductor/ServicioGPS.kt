package co.buscerca.app.presentacion.conductor

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import co.buscerca.app.R
import co.buscerca.app.datos.AlmacenLocal
import co.buscerca.app.datos.ClienteApi
import co.buscerca.app.datos.Coordenada
import co.buscerca.app.datos.Lote
import co.buscerca.app.datos.Sesion
import co.buscerca.app.dominio.ColaPendientes
import co.buscerca.app.dominio.Envio
import co.buscerca.app.dominio.Mensajes
import co.buscerca.app.dominio.ReglasRecorrido
import co.buscerca.app.dominio.Sincronizador
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * CU-202 Transmitir ubicación. Servicio en primer plano: toma el GPS cada 10 segundos (RN-202), también con la
 * pantalla bloqueada, y muestra la notificación permanente de rastreo. Sin conexión guarda en AlmacenLocal (CU-203).
 */
class ServicioGPS : Service(), LocationListener {

    companion object {
        private const val CANAL = "rastreo"
        private const val ID_NOTIFICACION = 202
        @Volatile var ultima: Location? = null; private set
        @Volatile var enEjecucion = false; private set
        @Volatile var ultimoEnvio: Envio? = null; private set

        fun iniciar(ctx: Context, idRecorrido: Int) {
            val i = Intent(ctx, ServicioGPS::class.java).putExtra("id", idRecorrido)
            if (Build.VERSION.SDK_INT >= 26) ctx.startForegroundService(i) else ctx.startService(i)
        }

        fun detener(ctx: Context) { ctx.stopService(Intent(ctx, ServicioGPS::class.java)) }

        val formato get() = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)

        /** Crea el sincronizador que usan el servicio y la pantalla al finalizar (CP-0205-02). */
        fun sincronizador(ctx: Context, idRecorrido: Int): Sincronizador {
            val almacen = AlmacenLocal(ctx)
            val cola = object : ColaPendientes {
                override fun guardar(c: Coordenada) = almacen.guardar(idRecorrido, c)
                override fun pendientes(limite: Int) = almacen.pendientes(idRecorrido, limite)
                override fun eliminar(ids: List<Long>) = almacen.eliminar(ids)
            }
            return Sincronizador(cola) { lote ->
                try {
                    val r = ClienteApi.de(ctx).enviarUbicaciones(idRecorrido, Lote(lote))
                    when (r.code()) { 201 -> Envio.OK; 401 -> Envio.SESION_VENCIDA; 404, 409 -> Envio.RECORRIDO_CERRADO; else -> Envio.SIN_CONEXION }
                } catch (_: IOException) { Envio.SIN_CONEXION }
            }
        }
    }

    private val alcance = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val manejador = Handler(Looper.getMainLooper())
    private var idRecorrido = -1
    private lateinit var sincronizador: Sincronizador

    private val ciclo = object : Runnable {
        override fun run() {
            tomarYEnviar()
            manejador.postDelayed(this, ReglasRecorrido.INTERVALO_MS)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val id = intent?.getIntExtra("id", -1)?.takeIf { it > 0 } ?: Sesion(this).recorridoActivo
        if (id <= 0) { stopSelf(); return START_NOT_STICKY }
        mostrarNotificacion()
        if (enEjecucion && id == idRecorrido) return START_STICKY
        idRecorrido = id
        sincronizador = sincronizador(this, id)
        try {
            val lm = getSystemService(LOCATION_SERVICE) as LocationManager
            lm.requestLocationUpdates(LocationManager.GPS_PROVIDER, ReglasRecorrido.INTERVALO_MS, 0f, this, Looper.getMainLooper())
        } catch (_: SecurityException) {
            avisarDetenido(); return START_NOT_STICKY   // E2: el conductor retiró el permiso
        }
        enEjecucion = true
        manejador.removeCallbacks(ciclo)
        manejador.postDelayed(ciclo, ReglasRecorrido.INTERVALO_MS)
        return START_STICKY
    }

    override fun onLocationChanged(location: Location) { ultima = location }
    @Deprecated("Requerido en API < 30") override fun onStatusChanged(p: String?, s: Int, e: android.os.Bundle?) = Unit
    override fun onProviderEnabled(provider: String) = Unit
    override fun onProviderDisabled(provider: String) = Unit

    /** Un ciclo de CU-202: si hay una lectura reciente del GPS, se guarda y se envía todo lo pendiente. */
    private fun tomarYEnviar() {
        val loc = ultima ?: return                                             // A2: GPS sin señal, se omite el ciclo
        if (System.currentTimeMillis() - loc.time > 2 * ReglasRecorrido.INTERVALO_MS) return
        val c = Coordenada(loc.latitude, loc.longitude, if (loc.hasSpeed()) loc.speed * 3.6 else null, formato.format(Date()))
        alcance.launch {
            val r = sincronizador.registrar(c)
            ultimoEnvio = r
            if (r == Envio.RECORRIDO_CERRADO) manejador.post { stopSelf() }       // E1: el recorrido ya no está en curso
        }
    }

    private fun canal() {
        if (Build.VERSION.SDK_INT >= 26) {
            val nm = getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(NotificationChannel(CANAL, "Rastreo del recorrido", NotificationManager.IMPORTANCE_LOW))
        }
    }

    private fun notificacion(texto: String): Notification {
        canal()
        val abrir = PendingIntent.getActivity(this, 0, Intent(this, UIRecorridoEnCurso::class.java).putExtra("id", idRecorrido),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val b = if (Build.VERSION.SDK_INT >= 26) Notification.Builder(this, CANAL) else Notification.Builder(this)
        return b.setContentTitle("BusCerca: recorrido en curso").setContentText(texto)
            .setSmallIcon(R.drawable.ic_bus).setOngoing(true).setContentIntent(abrir).build()
    }

    private fun mostrarNotificacion() {
        val n = notificacion("Compartiendo tu ubicación cada 10 segundos")
        if (Build.VERSION.SDK_INT >= 29) startForeground(ID_NOTIFICACION, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
        else startForeground(ID_NOTIFICACION, n)
    }

    private fun avisarDetenido() {
        getSystemService(NotificationManager::class.java).notify(ID_NOTIFICACION + 1, notificacion(Mensajes.RASTREO_DETENIDO))
        stopSelf()
    }

    override fun onDestroy() {
        manejador.removeCallbacks(ciclo)
        try { (getSystemService(LOCATION_SERVICE) as LocationManager).removeUpdates(this) } catch (_: Exception) {}
        enEjecucion = false; ultima = null
        alcance.cancel()
        stopForeground(STOP_FOREGROUND_REMOVE)   // CP-0205-03: la notificación desaparece al finalizar
        super.onDestroy()
    }
}
