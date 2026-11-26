package co.buscerca.app.dominio

/**
 * Reglas de la app que no dependen de Android, para poder probarlas con JUnit en el computador.
 * Los mensajes son los mismos de los criterios de aceptación.
 */
object Mensajes {
    const val SIN_PERMISO = "No se puede iniciar el recorrido sin el permiso de ubicación"
    const val SIN_CONEXION = "No fue posible conectar con el servidor"
    const val NOVEDAD_SIN_CONEXION = "No fue posible enviar el reporte"
    const val NOVEDAD_OK = "Novedad reportada"
    const val TIPO_OBLIGATORIO = "Selecciona el tipo de novedad"
    const val MIN_LETRAS = "Escribe al menos 3 letras"
    const val RASTREO_DETENIDO = "El rastreo se detuvo: activa la ubicación"
    const val RECORRIDO_TERMINADO = "Este recorrido ya terminó"
}

/** HU-0201: el botón Iniciar recorrido solo se habilita con ruta y vehículo (CP-0201-01, CP-0201-03). */
object ReglasRecorrido {
    fun puedeIniciar(idRuta: Int?, idVehiculo: Int?) = idRuta != null && idVehiculo != null

    /** Devuelve el mensaje que impide iniciar o null si se puede llamar a la API. */
    fun validarInicio(idRuta: Int?, idVehiculo: Int?, permisoUbicacion: Boolean): String? = when {
        !puedeIniciar(idRuta, idVehiculo) -> "Selecciona la ruta y el vehículo"
        !permisoUbicacion -> Mensajes.SIN_PERMISO
        else -> null
    }

    const val INTERVALO_MS = 10_000L   // RN-202: una ubicación cada 10 segundos
}

/** HU-0204: validaciones del formulario de novedad (CP-0204-02 y CP-0204-03). */
object ValidadorNovedad {
    const val MAX_COMENTARIO = 200

    fun validar(idTipo: Int?, comentario: String): String? = when {
        idTipo == null -> Mensajes.TIPO_OBLIGATORIO
        comentario.length > MAX_COMENTARIO -> "El comentario admite máximo 200 caracteres"
        else -> null
    }

    /** El campo de texto no deja escribir más de 200 caracteres. */
    fun recortar(texto: String) = texto.take(MAX_COMENTARIO)
}

/** HU-0301: validación del texto antes de enviar la búsqueda (RN-301, CP-0301-02). */
object ValidadorBusqueda {
    fun letrasEfectivas(texto: String) = texto.count { it.isLetter() }
    fun validar(texto: String): String? = if (letrasEfectivas(texto) < 3) Mensajes.MIN_LETRAS else null
}

/** HU-0305: alias de favoritos (RN-310, CP-0305-04). */
object ValidadorFavorito {
    const val MAX_ALIAS = 30
    fun validarAlias(alias: String): String? = if (alias.trim().length > MAX_ALIAS) "El alias admite máximo 30 caracteres" else null
}

/** Formato de la velocidad que ve el conductor (CP-0203-04). */
fun formatoVelocidad(kmh: Double?): String = if (kmh == null) "— km/h" else "${Math.round(kmh)} km/h"

/** Módulo 01: validaciones de registro, recuperación y perfil (las mismas reglas que la API). */
object ValidadorCuenta {
    private val CORREO = Regex("^[^@\\s]+@[^@\\s]+\\.[A-Za-z]{2,}$")
    const val CLAVE_DEBIL = "La contraseña debe tener mínimo 8 caracteres, con letras y números"

    fun correo(c: String): String? = if (CORREO.matches(c.trim())) null else "Escribe un correo válido"
    fun contrasena(c: String): String? = if (c.length >= 8 && c.any { it.isLetter() } && c.any { it.isDigit() }) null else CLAVE_DEBIL
    fun nombre(n: String): String? = if (n.trim().length in 3..80) null else "Escribe tu nombre completo (entre 3 y 80 caracteres)"
    fun telefono(t: String): String? = if (t.isBlank() || Regex("\\d{7,10}").matches(t.trim())) null else "El teléfono debe tener entre 7 y 10 dígitos"
    fun coinciden(a: String, b: String): String? = if (a == b) null else "Las contraseñas no coinciden"

    fun registro(nombre: String, correo: String, clave: String, confirmacion: String, telefono: String) =
        nombre(nombre) ?: correo(correo) ?: contrasena(clave) ?: coinciden(clave, confirmacion) ?: telefono(telefono)
}
