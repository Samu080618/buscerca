package co.buscerca.app.dominio

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/** Pruebas del Módulo 01 (HU-0101 registro, HU-0103 recuperación, HU-0104 perfil). */
class ValidadorCuentaTest {
    @Test fun registroValidoNoDevuelveError() {
        assertNull(ValidadorCuenta.registro("Laura Gómez", "laura@correo.co", "Clave2026", "Clave2026", "3101234567"))
    }

    @Test fun correoInvalidoSeRechaza() {
        assertEquals("Escribe un correo válido", ValidadorCuenta.correo("laura@correo"))
    }

    @Test fun contrasenaSinNumerosEsDebil() {
        assertEquals(ValidadorCuenta.CLAVE_DEBIL, ValidadorCuenta.contrasena("soloLetras"))
        assertEquals(ValidadorCuenta.CLAVE_DEBIL, ValidadorCuenta.contrasena("Ab1"))
    }

    @Test fun confirmacionDistintaSeRechaza() {
        assertEquals("Las contraseñas no coinciden",
            ValidadorCuenta.registro("Laura Gómez", "laura@correo.co", "Clave2026", "Clave2027", ""))
    }

    @Test fun telefonoOpcionalPeroConFormato() {
        assertNull(ValidadorCuenta.telefono(""))
        assertEquals("El teléfono debe tener entre 7 y 10 dígitos", ValidadorCuenta.telefono("12ab"))
    }

    @Test fun nombreMuyCortoSeRechaza() {
        assertEquals("Escribe tu nombre completo (entre 3 y 80 caracteres)", ValidadorCuenta.nombre("Al"))
    }
}
