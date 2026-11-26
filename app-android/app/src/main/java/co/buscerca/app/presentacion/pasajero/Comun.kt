package co.buscerca.app.presentacion.pasajero

import android.Manifest
import android.app.AlertDialog
import android.content.pm.PackageManager
import android.location.LocationManager
import co.buscerca.app.datos.NuevoFavorito
import co.buscerca.app.dominio.ValidadorFavorito
import co.buscerca.app.presentacion.*

/** Barra inferior del pasajero. */
fun PantallaBase.pestanasPasajero(p: Pantalla, activa: String) {
    p.pestana("🔍 Buscar", activa == "buscar") { if (activa != "buscar") irA(UIBuscarRutas::class.java, limpiar = true) }
    p.pestana("★ Favoritos", activa == "favoritos") { if (activa != "favoritos") irA(UIFavoritos::class.java) }
    p.pestana("👤 Perfil", activa == "perfil") { irA(co.buscerca.app.presentacion.cuenta.UIPerfil::class.java) }
}

/** Punto de referencia de la zona de servicio (a 350 m de Cogua centro). */
val ZONA_SERVICIO = 5.0641 to -73.9790
const val RADIO_ZONA_KM = 30f

/**
 * Ubicación del pasajero para sugerir el paradero de abordaje (RN-303).
 * Sin permiso, o si el celular está fuera de la zona de servicio (por ejemplo, en la sustentación en Bogotá),
 * usa el punto de referencia de Cogua centro para que la búsqueda tenga sentido.
 */
fun PantallaBase.ubicacionPasajero(): Pair<Double, Double> {
    val permiso = checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
    if (permiso) {
        val lm = getSystemService(LocationManager::class.java)
        try {
            for (prov in listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)) {
                val loc = lm.getLastKnownLocation(prov) ?: continue
                val d = FloatArray(1)
                android.location.Location.distanceBetween(loc.latitude, loc.longitude, ZONA_SERVICIO.first, ZONA_SERVICIO.second, d)
                return if (d[0] / 1000f <= RADIO_ZONA_KM) loc.latitude to loc.longitude else ZONA_SERVICIO
            }
        } catch (_: SecurityException) {}
    }
    return ZONA_SERVICIO
}

/** CU-16 Guardar favorito con alias opcional (RN-310). */
fun PantallaBase.guardarFavorito(idRuta: Int?, idParadero: Int?, sugerido: String) {
    val alias = campo("Alias (opcional, máx. 30)").apply { setText(sugerido) }
    AlertDialog.Builder(this).setTitle("Guardar en favoritos").setView(alias).setNegativeButton("Cancelar", null)
        .setPositiveButton("Guardar") { _, _ ->
            val a = alias.text.toString()
            ValidadorFavorito.validarAlias(a)?.let { aviso(it); return@setPositiveButton }
            tarea {
                api.guardarFavorito(NuevoFavorito(if (idRuta != null) "RUTA" else "PARADERO", idRuta, idParadero, a.ifBlank { null }))
                aviso("Guardado en tus favoritos")
            }
        }.show()
}
