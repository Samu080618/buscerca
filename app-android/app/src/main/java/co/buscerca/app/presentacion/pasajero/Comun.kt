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
    p.pestana("Salir", false) { cerrarSesion() }
}

/** Ubicación del pasajero para sugerir el paradero de abordaje (RN-303). Sin permiso usa Cogua centro. */
fun PantallaBase.ubicacionPasajero(): Pair<Double, Double> {
    val permiso = checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
    if (permiso) {
        val lm = getSystemService(LocationManager::class.java)
        try {
            for (prov in listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)) {
                lm.getLastKnownLocation(prov)?.let { return it.latitude to it.longitude }
            }
        } catch (_: SecurityException) {}
    }
    return 5.0641 to -73.9790
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
