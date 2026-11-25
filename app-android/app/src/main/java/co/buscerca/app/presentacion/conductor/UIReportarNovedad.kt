package co.buscerca.app.presentacion.conductor

import android.os.Bundle
import android.text.Editable
import android.text.InputFilter
import android.text.InputType
import android.text.TextWatcher
import android.widget.RadioButton
import android.widget.RadioGroup
import co.buscerca.app.datos.NuevaNovedad
import co.buscerca.app.dominio.Mensajes
import co.buscerca.app.dominio.ValidadorNovedad
import co.buscerca.app.presentacion.*
import java.io.IOException

/** CU-205 Reportar novedad (HU-0204). */
class UIReportarNovedad : PantallaBase() {

    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        val id = intent.getIntExtra("id", sesion.recorridoActivo)
        val p = Pantalla(this, "Reportar novedad", "Se enviará con tu ubicación actual")
        val c = p.contenido
        c.agregar(texto("Tipo de novedad", 14f, Colores.GRIS, true), 16)
        val tipos = RadioGroup(this)
        c.agregar(tipos, 4)
        val errorTipo = texto("", 13f, Colores.ROJO); c.agregar(errorTipo, 2)
        c.agregar(texto("Comentario (opcional)", 14f, Colores.GRIS, true), 12)
        val comentario = campo("Ej.: llanta pinchada, esperamos 20 min", InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE).apply {
            filters = arrayOf(InputFilter.LengthFilter(ValidadorNovedad.MAX_COMENTARIO))   // CP-0204-03
            minLines = 3; setSingleLine(false)
        }
        val contador = texto("0/200", 12f, Colores.GRIS)
        comentario.addTextChangedListener(object : TextWatcher {
            override fun afterTextChanged(s: Editable?) { contador.text = "${s?.length ?: 0}/200" }
            override fun beforeTextChanged(s: CharSequence?, a: Int, b: Int, d: Int) = Unit
            override fun onTextChanged(s: CharSequence?, a: Int, b: Int, d: Int) = Unit
        })
        c.agregar(comentario, 4); c.agregar(contador, 2)
        val error = texto("", 14f, Colores.ROJO); c.agregar(error, 8)
        val ids = mutableMapOf<Int, Int>()
        val enviar = boton("Enviar reporte") {}
        enviar.setOnClickListener {
            error.text = ""; errorTipo.text = ""
            val idTipo = ids[tipos.checkedRadioButtonId]
            val msg = ValidadorNovedad.validar(idTipo, comentario.text.toString())
            if (msg != null) { if (msg == Mensajes.TIPO_OBLIGATORIO) errorTipo.text = msg else error.text = msg; return@setOnClickListener }  // CP-0204-02
            enviar.isEnabled = false
            val loc = ServicioGPS.ultima
            tarea({ e, m -> enviar.isEnabled = true; error.text = if (e is IOException) Mensajes.NOVEDAD_SIN_CONEXION else m }) {  // CP-0204-05: el formulario se conserva
                val r = api.reportarNovedad(id, NuevaNovedad(idTipo, comentario.text.toString().ifBlank { null }, loc?.latitude, loc?.longitude))
                aviso(r.mensaje); finish()
            }
        }
        c.agregar(enviar, 8)
        c.agregar(botonBorde("Cancelar") { finish() }, 8)
        tarea({ _, m -> error.text = m }) {
            api.tiposNovedad().forEach { t ->
                val rb = RadioButton(this).apply { text = t.descripcion; textSize = 16f; this.id = android.view.View.generateViewId() }
                ids[rb.id] = t.id_tipo_novedad; tipos.addView(rb)
            }
        }
    }
}
