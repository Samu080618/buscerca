package co.buscerca.app.dominio

import co.buscerca.app.datos.Coordenada
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test

/** CU-203: almacenamiento sin conexión y envío en orden (CP-0202-03, CP-0204-05 y CP-0205-02). */
class SincronizadorTest {

    private class ColaMemoria : ColaPendientes {
        val filas = linkedMapOf<Long, Coordenada>(); var sig = 1L
        override fun guardar(c: Coordenada) { if (filas.values.none { it.fecha_hora == c.fecha_hora }) filas[sig++] = c }
        override fun pendientes(limite: Int) = filas.entries.sortedBy { it.value.fecha_hora }.take(limite).map { it.key to it.value }
        override fun eliminar(ids: List<Long>) { ids.forEach { filas.remove(it) } }
    }

    private fun c(seg: Int) = Coordenada(5.05, -73.98, 30.0, "2026-11-05T06:%02d:%02d".format(seg / 60, seg % 60))

    @Test fun cp_0202_03_sinConexionGuardaYLuegoEnviaEnOrden() = runBlocking {
        val cola = ColaMemoria(); val enviadas = mutableListOf<String>(); var hayRed = false
        val s = Sincronizador(cola) { lote -> if (!hayRed) Envio.SIN_CONEXION else { enviadas += lote.map { it.fecha_hora }; Envio.OK } }
        (0 until 12).forEach { assertEquals(Envio.SIN_CONEXION, s.registrar(c(10 * it))) }   // 2 minutos en modo avión
        assertEquals(12, cola.filas.size)
        hayRed = true
        assertEquals(Envio.OK, s.registrar(c(120)))
        assertEquals(13, enviadas.size)
        assertEquals(enviadas.sorted(), enviadas)          // en orden de captura
        assertEquals(enviadas.toSet().size, enviadas.size) // sin duplicados
        assertEquals(0, cola.filas.size)
    }

    @Test fun cp_0205_02_vaciarEnviaLasPendientesAntesDeFinalizar() = runBlocking {
        val cola = ColaMemoria(); listOf(30, 10, 20).forEach { cola.guardar(c(it)) }
        val enviadas = mutableListOf<String>()
        assertEquals(Envio.OK, Sincronizador(cola) { l -> enviadas += l.map { it.fecha_hora }; Envio.OK }.vaciar())
        assertEquals(listOf(c(10), c(20), c(30)).map { it.fecha_hora }, enviadas)
    }

    @Test fun recorridoCerradoDetieneElEnvio() = runBlocking {
        val cola = ColaMemoria()
        assertEquals(Envio.RECORRIDO_CERRADO, Sincronizador(cola) { Envio.RECORRIDO_CERRADO }.registrar(c(0)))
        assertEquals(1, cola.filas.size)
    }
}
