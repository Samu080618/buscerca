package co.buscerca.app.presentacion.conductor

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.Spinner
import co.buscerca.app.datos.NuevoRecorrido
import co.buscerca.app.dominio.Mensajes
import co.buscerca.app.dominio.ReglasRecorrido
import co.buscerca.app.presentacion.*
import retrofit2.HttpException

/** CU-201 Iniciar recorrido (HU-0201). */
class UIIniciarRecorrido : PantallaBase() {
    private lateinit var rutas: Spinner
    private lateinit var vehiculos: Spinner
    private lateinit var iniciar: android.widget.Button
    private lateinit var error: android.widget.TextView
    private var idRuta: Int? = null
    private var idVehiculo: Int? = null

    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        val p = Pantalla(this, "Iniciar recorrido", "Hola, ${sesion.nombre ?: "conductor"}")
        val c = p.contenido
        rutas = Spinner(this); vehiculos = Spinner(this)
        c.agregar(texto("Ruta", 14f, Colores.GRIS, true), 18); c.agregar(rutas, 4)
        c.agregar(texto("Vehículo", 14f, Colores.GRIS, true), 16); c.agregar(vehiculos, 4)
        c.agregar(cajaAviso("Al iniciar, BusCerca enviará tu ubicación cada 10 segundos mientras el recorrido esté en curso, también con la pantalla bloqueada.", Colores.VERDE_CLARO), 18)
        error = texto("", 14f, Colores.ROJO); c.agregar(error, 10)
        iniciar = boton("Iniciar recorrido") { pedirPermisoEIniciar() }
        c.agregar(iniciar, 10)
        p.pestana("Cerrar sesión", false) { cerrarSesion() }
        actualizarBoton()
        cargar()
    }

    private fun cargar() = tarea {
        val activo = api.recorridoActivo()
        if (activo.isSuccessful) { abrirEnCurso(activo.body()!!.id_recorrido); return@tarea }  // A3 / RN-201
        val op = api.opciones()
        rutas.adapter = adaptador(listOf("Selecciona la ruta") + op.rutas.map { it.toString() })
        vehiculos.adapter = adaptador(listOf("Selecciona el vehículo") + op.vehiculos.map { it.toString() })
        rutas.onItemSelectedListener = seleccion { idRuta = if (it == 0) null else op.rutas[it - 1].id_ruta }
        vehiculos.onItemSelectedListener = seleccion { idVehiculo = if (it == 0) null else op.vehiculos[it - 1].id_vehiculo }
    }

    private fun adaptador(items: List<String>) = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, items)

    private fun seleccion(f: (Int) -> Unit) = object : AdapterView.OnItemSelectedListener {
        override fun onItemSelected(p: AdapterView<*>?, v: View?, pos: Int, id: Long) { f(pos); actualizarBoton() }
        override fun onNothingSelected(p: AdapterView<*>?) = Unit
    }

    /** CP-0201-01: el botón permanece deshabilitado hasta elegir ruta y vehículo. */
    private fun actualizarBoton() {
        val ok = ReglasRecorrido.puedeIniciar(idRuta, idVehiculo)
        iniciar.isEnabled = ok; iniciar.alpha = if (ok) 1f else 0.45f
    }

    private fun tienePermiso() = checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED

    private fun pedirPermisoEIniciar() {
        error.text = ""
        if (tienePermiso()) { iniciarRecorrido(); return }
        val permisos = mutableListOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
        if (Build.VERSION.SDK_INT >= 33) permisos += "android.permission.POST_NOTIFICATIONS"
        requestPermissions(permisos.toTypedArray(), 7)  // A2: el sistema solicita el permiso
    }

    override fun onRequestPermissionsResult(codigo: Int, permisos: Array<out String>, resultados: IntArray) {
        super.onRequestPermissionsResult(codigo, permisos, resultados)
        val msg = ReglasRecorrido.validarInicio(idRuta, idVehiculo, tienePermiso())
        if (msg == Mensajes.SIN_PERMISO) error.text = msg else if (msg == null) iniciarRecorrido()  // E1 (CP-0201-03)
    }

    private fun iniciarRecorrido() {
        iniciar.isEnabled = false
        tarea({ e, m ->
            actualizarBoton()
            if (e is HttpException && e.code() == 409 && m.startsWith("Ya tienes")) { aviso(m); cargar() } else error.text = m
        }) {
            val r = api.iniciarRecorrido(NuevoRecorrido(idRuta, idVehiculo))
            ServicioGPS.iniciar(this, r.id_recorrido)
            abrirEnCurso(r.id_recorrido)
        }
    }

    private fun abrirEnCurso(id: Int) {
        sesion.recorridoActivo = id
        irA(UIRecorridoEnCurso::class.java) { putExtra("id", id) }
        finish()
    }
}
