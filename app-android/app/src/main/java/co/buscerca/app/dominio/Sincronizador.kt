package co.buscerca.app.dominio

import co.buscerca.app.datos.Coordenada

/** Dónde se guardan las coordenadas pendientes (en la app: AlmacenLocal con SQLite). */
interface ColaPendientes {
    fun guardar(c: Coordenada)
    fun pendientes(limite: Int = 200): List<Pair<Long, Coordenada>>
    fun eliminar(ids: List<Long>)
}

/** Resultado de intentar enviar un lote a la API. */
enum class Envio { OK, SIN_CONEXION, RECORRIDO_CERRADO, SESION_VENCIDA }

/**
 * CU-202 y CU-203: cada coordenada se guarda primero en la cola y luego se envía todo lo pendiente
 * en orden de captura. Si no hay conexión, la cola se conserva y se reintenta en el siguiente ciclo (RN-204).
 */
class Sincronizador(private val cola: ColaPendientes, private val enviar: suspend (List<Coordenada>) -> Envio) {

    suspend fun registrar(c: Coordenada): Envio {
        cola.guardar(c)
        return vaciar()
    }

    /** Envía las pendientes por lotes, en orden. Se usa también antes de finalizar (CP-0205-02). */
    suspend fun vaciar(): Envio {
        while (true) {
            val lote = cola.pendientes()
            if (lote.isEmpty()) return Envio.OK
            val ordenado = lote.sortedBy { it.second.fecha_hora }
            val r = enviar(ordenado.map { it.second })
            if (r != Envio.OK) return r
            cola.eliminar(ordenado.map { it.first })
        }
    }
}
