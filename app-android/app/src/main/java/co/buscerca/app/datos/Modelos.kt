package co.buscerca.app.datos

// Objetos que viajan entre la app y la API REST (los nombres coinciden con el JSON del servidor).

data class Credenciales(val correo: String, val contrasena: String)
data class UsuarioSesion(val id: Int, val nombre: String, val rol: String)
data class RespuestaLogin(val token: String, val usuario: UsuarioSesion)

// ---------- Módulo 02: Panel del Conductor ----------
data class RutaItem(val id_ruta: Int, val codigo: String, val nombre: String, val origen: String, val destino: String) {
    override fun toString() = "$codigo $nombre"
}
data class VehiculoItem(val id_vehiculo: Int, val placa: String, val numero_interno: String, val tipo: String) {
    override fun toString() = "$numero_interno · $placa · $tipo"
}
data class Opciones(val rutas: List<RutaItem>, val vehiculos: List<VehiculoItem>)
data class NuevoRecorrido(val id_ruta: Int?, val id_vehiculo: Int?)
data class RutaCorta(val id: Int, val codigo: String, val nombre: String)
data class VehiculoCorto(val id: Int, val placa: String, val numero_interno: String)
data class RecorridoInfo(
    val id_recorrido: Int, val estado: String, val ruta: RutaCorta, val vehiculo: VehiculoCorto,
    val fecha_inicio: String, val fecha_fin: String?, val velocidad_promedio: Double? = null,
    val ubicaciones_registradas: Int? = null, val duracion_minutos: Int? = null,
)
data class Coordenada(val latitud: Double, val longitud: Double, val velocidad: Double?, val fecha_hora: String)
data class Lote(val coordenadas: List<Coordenada>)
data class ResultadoLote(val recibidas: Int, val guardadas: Int, val duplicadas: Int, val velocidad_promedio: Double?)
data class TipoNovedad(val id_tipo_novedad: Int, val descripcion: String) { override fun toString() = descripcion }
data class NuevaNovedad(val id_tipo_novedad: Int?, val comentario: String?, val latitud: Double?, val longitud: Double?)
data class NovedadRegistrada(val id_novedad: Int, val mensaje: String)

// ---------- Módulo 03: Panel del Pasajero ----------
data class Eta(val estado: String, val minutos: Double?, val aproximado: Boolean, val texto: String)
data class Bus(
    val id_recorrido: Int, val numero_interno: String, val placa: String, val latitud: Double, val longitud: Double,
    val senal: String, val etiqueta: String?, val eta: Eta?,
)
data class Abordaje(val id_paradero: Int, val nombre: String, val metros: Int)
data class DestinoParadero(val id_paradero: Int, val nombre: String)
data class ProximoBus(val numero_interno: String, val eta: Eta, val indicador: String)
data class ResultadoRuta(
    val id_ruta: Int, val codigo: String, val nombre: String, val sentido: String, val abordaje: Abordaje,
    val destino: DestinoParadero, val vehiculos_operando: Int, val proximo_bus: ProximoBus?, val proxima_salida: String?,
)
data class Busqueda(val texto: String, val resultados: List<ResultadoRuta>, val mensaje: String?)
data class ParaderoRuta(val id_paradero: Int, val nombre: String, val latitud: Double, val longitud: Double, val orden: Int)
data class Trazado(
    val id_ruta: Int, val codigo: String, val nombre: String, val estado: String,
    val trazado: List<List<Double>>, val paraderos: List<ParaderoRuta>, val refresco_segundos: Int,
)
data class BusesRuta(val id_ruta: Int, val buses: List<Bus>, val mensaje: String?, val proxima_salida: String?, val refresco_segundos: Int)
data class Conductor(val nombre: String, val foto_url: String?)
data class Ficha(
    val id_recorrido: Int, val numero_interno: String, val placa: String, val tipo: String, val empresa: String,
    val conductor: Conductor, val hora_salida: String, val estado: String,
)
data class ParaderoInfo(val id_paradero: Int, val nombre: String, val municipio: String)
data class Llegadas(val paradero: ParaderoInfo, val llegadas: List<Bus>, val mensaje: String?, val proxima_salida: String?)
data class Favorito(
    val id_favorito: Int, val tipo: String, val id_ruta: Int?, val id_paradero: Int?, val alias: String?,
    val ruta_codigo: String?, val ruta_nombre: String?, val paradero_nombre: String?, val disponible: Boolean, val aviso: String?,
) {
    val titulo get() = alias ?: listOfNotNull(ruta_codigo, paradero_nombre).joinToString(" · ")
}
data class NuevoFavorito(val tipo: String, val id_ruta: Int?, val id_paradero: Int?, val alias: String?)
data class Renombrar(val alias: String?)
