package co.buscerca.app.presentacion.pasajero

import android.app.AlertDialog
import co.buscerca.app.dominio.Mensajes
import co.buscerca.app.presentacion.PantallaBase
import retrofit2.HttpException

/** CU-14 Consultar datos del vehículo (HU-0303): ficha con los 7 datos públicos de RN-307. */
object UIDetalleVehiculo {
    fun mostrar(p: PantallaBase, idRecorrido: Int, alTerminar: () -> Unit) {
        p.tarea({ e, m ->
            if (e is HttpException && e.code() == 410) { p.aviso(Mensajes.RECORRIDO_TERMINADO); alTerminar() } else p.aviso(m)   // CP-0303-03
        }) {
            val f = p.api.ficha(idRecorrido)
            AlertDialog.Builder(p).setTitle("Bus ${f.numero_interno} · ${f.placa}")
                .setMessage("Tipo: ${f.tipo}\nEmpresa: ${f.empresa}\nConductor: ${f.conductor.nombre}\nSalió a las ${f.hora_salida}\nEstado: ${f.estado}")
                .setPositiveButton("Cerrar", null).show()
        }
    }
}
