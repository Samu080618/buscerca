package co.buscerca.app.datos

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

/** Contrato de la API REST (sección Programación del documento). */
interface ApiBusCerca {
    // Módulo 01 — Autenticación y Perfiles
    @POST("api/auth/registro") suspend fun registrar(@Body r: Registro): Mensaje
    @POST("api/auth/login") suspend fun login(@Body c: Credenciales): RespuestaLogin
    @POST("api/auth/recuperar") suspend fun recuperar(@Body c: CorreoReq): Mensaje
    @POST("api/auth/restablecer") suspend fun restablecer(@Body r: Restablecer): Mensaje
    @POST("api/auth/logout") suspend fun logout(): Mensaje
    @GET("api/perfil") suspend fun perfil(): Perfil
    @PATCH("api/perfil") suspend fun editarPerfil(@Body d: DatosPerfil): Perfil
    @POST("api/perfil/contrasena") suspend fun cambiarClave(@Body c: CambioClave): Mensaje

    // Módulo 02 — Conductor
    @GET("api/recorridos/opciones") suspend fun opciones(): Opciones
    @POST("api/recorridos") suspend fun iniciarRecorrido(@Body r: NuevoRecorrido): RecorridoInfo
    @GET("api/recorridos/activo") suspend fun recorridoActivo(): Response<RecorridoInfo>
    @POST("api/recorridos/{id}/ubicaciones") suspend fun enviarUbicaciones(@Path("id") id: Int, @Body lote: Lote): Response<ResultadoLote>
    @GET("api/tipos-novedad") suspend fun tiposNovedad(): List<TipoNovedad>
    @POST("api/recorridos/{id}/novedades") suspend fun reportarNovedad(@Path("id") id: Int, @Body n: NuevaNovedad): NovedadRegistrada
    @PATCH("api/recorridos/{id}/finalizar") suspend fun finalizar(@Path("id") id: Int): RecorridoInfo

    // Módulo 03 — Pasajero
    @GET("api/rutas/buscar") suspend fun buscarRutas(@Query("texto") texto: String, @Query("lat") lat: Double, @Query("lon") lon: Double): Busqueda
    @GET("api/rutas/{id}/trazado") suspend fun trazado(@Path("id") id: Int): Trazado
    @GET("api/rutas/{id}/buses") suspend fun buses(@Path("id") id: Int, @Query("paradero") paradero: Int?): BusesRuta
    @GET("api/recorridos/{id}/ficha") suspend fun ficha(@Path("id") id: Int): Ficha
    @GET("api/paraderos/{id}/llegadas") suspend fun llegadas(@Path("id") id: Int, @Query("ruta") ruta: Int): Llegadas
    @GET("api/favoritos") suspend fun favoritos(): List<Favorito>
    @POST("api/favoritos") suspend fun guardarFavorito(@Body f: NuevoFavorito): Favorito
    @PATCH("api/favoritos/{id}") suspend fun renombrarFavorito(@Path("id") id: Int, @Body r: Renombrar): Favorito
    @DELETE("api/favoritos/{id}") suspend fun eliminarFavorito(@Path("id") id: Int): Response<Unit>
}
