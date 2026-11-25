package co.buscerca.app.dominio

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Pruebas de la lógica de la app que acompañan a los casos de prueba de la API. */
class ReglasTest {

    @Test fun cp_0201_01_botonDeshabilitadoSinRutaOVehiculo() {
        assertFalse(ReglasRecorrido.puedeIniciar(null, null))
        assertFalse(ReglasRecorrido.puedeIniciar(7, null))
        assertFalse(ReglasRecorrido.puedeIniciar(null, 1))
        assertTrue(ReglasRecorrido.puedeIniciar(7, 1))
    }

    @Test fun cp_0201_03_sinPermisoNoInicia() {
        assertEquals("No se puede iniciar el recorrido sin el permiso de ubicación", ReglasRecorrido.validarInicio(7, 1, false))
        assertNull(ReglasRecorrido.validarInicio(7, 1, true))
    }

    @Test fun cp_0202_01_intervaloDe10Segundos() = assertEquals(10_000L, ReglasRecorrido.INTERVALO_MS)

    @Test fun cp_0203_04_formatoDeVelocidad() {
        assertEquals("24 km/h", formatoVelocidad(24.0))
        assertEquals("— km/h", formatoVelocidad(null))
    }

    @Test fun cp_0204_02_tipoObligatorio() = assertEquals("Selecciona el tipo de novedad", ValidadorNovedad.validar(null, "Llanta pinchada"))

    @Test fun cp_0204_03_comentarioMaximo200() {
        assertEquals(200, ValidadorNovedad.recortar("x".repeat(201)).length)
        assertEquals("El comentario admite máximo 200 caracteres", ValidadorNovedad.validar(1, "x".repeat(201)))
        assertNull(ValidadorNovedad.validar(1, "x".repeat(200)))
    }

    @Test fun cp_0301_02_minimoTresLetras() {
        listOf("Ro", "  r ", "12345", "R-0").forEach { assertEquals("Escribe al menos 3 letras", ValidadorBusqueda.validar(it)) }
        assertNull(ValidadorBusqueda.validar("rodamontal"))
        assertNull(ValidadorBusqueda.validar("La Cabaña"))
    }

    @Test fun cp_0305_04_aliasMaximo30() {
        assertEquals("El alias admite máximo 30 caracteres", ValidadorFavorito.validarAlias("x".repeat(31)))
        assertNull(ValidadorFavorito.validarAlias("x".repeat(30)))
    }
}
