package co.buscerca.app.presentacion

import android.app.Activity
import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.text.InputType
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.ViewGroup.LayoutParams.MATCH_PARENT
import android.view.ViewGroup.LayoutParams.WRAP_CONTENT
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/** Colores y piezas de interfaz comunes (mismo estilo de los diseños del documento). */
object Colores {
    val VERDE = Color.parseColor("#0E7C66")
    val VERDE_OSCURO = Color.parseColor("#0B5E4E")
    val VERDE_CLARO = Color.parseColor("#E3F2EE")
    val ROJO = Color.parseColor("#C0392B")
    val NARANJA = Color.parseColor("#D9822B")
    val AMARILLO_CLARO = Color.parseColor("#FFF4D6")
    val GRIS = Color.parseColor("#56636B")
    val GRIS_CLARO = Color.parseColor("#9AA6AD")
    val TEXTO = Color.parseColor("#263238")
    val FONDO = Color.parseColor("#F4F6F7")
}

fun Context.dp(v: Int) = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v.toFloat(), resources.displayMetrics).toInt()

fun fondo(color: Int, radio: Int, borde: Int? = null, ctx: Context) = GradientDrawable().apply {
    setColor(color); cornerRadius = ctx.dp(radio).toFloat()
    if (borde != null) setStroke(ctx.dp(1), borde)
}

fun Context.texto(s: String, tam: Float = 15f, color: Int = Colores.TEXTO, negrita: Boolean = false) = TextView(this).apply {
    text = s; textSize = tam; setTextColor(color); if (negrita) setTypeface(typeface, Typeface.BOLD)
}

fun Context.boton(s: String, color: Int = Colores.VERDE, accion: () -> Unit) = Button(this).apply {
    text = s; isAllCaps = false; textSize = 16f; setTextColor(Color.WHITE)
    background = fondo(color, 10, ctx = context); minHeight = dp(52)
    setOnClickListener { accion() }
}

fun Context.botonBorde(s: String, color: Int = Colores.VERDE, accion: () -> Unit) = Button(this).apply {
    text = s; isAllCaps = false; textSize = 15f; setTextColor(color)
    background = fondo(Color.WHITE, 10, color, context); minHeight = dp(48)
    setOnClickListener { accion() }
}

fun Context.campo(pista: String, tipo: Int = InputType.TYPE_CLASS_TEXT) = EditText(this).apply {
    hint = pista; inputType = tipo; textSize = 16f; setSingleLine(tipo != InputType.TYPE_TEXT_FLAG_MULTI_LINE)
    background = fondo(Color.WHITE, 8, Colores.GRIS_CLARO, context); setPadding(dp(12), dp(12), dp(12), dp(12))
}

fun Context.tarjeta() = LinearLayout(this).apply {
    orientation = LinearLayout.VERTICAL; background = fondo(Color.WHITE, 12, Color.parseColor("#E0E5E8"), context)
    setPadding(dp(14), dp(12), dp(14), dp(12))
}

fun Context.cajaAviso(s: String, color: Int = Colores.AMARILLO_CLARO, textoColor: Int = Colores.TEXTO) = texto(s, 14f, textoColor).apply {
    background = fondo(color, 8, ctx = context); setPadding(dp(12), dp(10), dp(12), dp(10))
}

fun LinearLayout.agregar(v: View, arriba: Int = 10, alto: Int = WRAP_CONTENT): View {
    addView(v, LinearLayout.LayoutParams(MATCH_PARENT, alto).apply { topMargin = context.dp(arriba) })
    return v
}

/** Estructura de una pantalla: barra superior verde, contenido con desplazamiento y barra inferior opcional. */
class Pantalla(val activity: Activity, titulo: String, subtitulo: String? = null, desplazable: Boolean = true) {
    val raiz = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL; setBackgroundColor(Colores.FONDO) }
    val cabecera = LinearLayout(activity).apply {
        orientation = LinearLayout.VERTICAL; setBackgroundColor(Colores.VERDE)
        setPadding(activity.dp(18), activity.dp(22), activity.dp(18), activity.dp(16))
    }
    val tituloView = activity.texto(titulo, 22f, Color.WHITE, true)
    val subtituloView = activity.texto(subtitulo ?: "", 14f, Color.parseColor("#D6EFE8"))
    val contenido = LinearLayout(activity).apply {
        orientation = LinearLayout.VERTICAL; setPadding(activity.dp(16), activity.dp(6), activity.dp(16), activity.dp(16))
    }
    val inferior = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL; setBackgroundColor(Color.WHITE); gravity = Gravity.CENTER }

    init {
        cabecera.addView(tituloView); cabecera.addView(subtituloView)
        if (subtitulo == null) subtituloView.visibility = View.GONE
        raiz.addView(cabecera, LinearLayout.LayoutParams(MATCH_PARENT, WRAP_CONTENT))
        val cuerpo: View = if (desplazable) ScrollView(activity).apply { addView(contenido) } else contenido
        raiz.addView(cuerpo, LinearLayout.LayoutParams(MATCH_PARENT, 0, 1f))
        raiz.addView(inferior, LinearLayout.LayoutParams(MATCH_PARENT, WRAP_CONTENT))
        activity.setContentView(raiz)
    }

    fun subtitulo(s: String) { subtituloView.text = s; subtituloView.visibility = View.VISIBLE }

    /** Barra inferior con pestañas (pasajero) o acciones. */
    fun pestana(etiqueta: String, activa: Boolean, accion: () -> Unit) {
        val t = activity.texto(etiqueta, 14f, if (activa) Colores.VERDE else Colores.GRIS, activa).apply {
            gravity = Gravity.CENTER; setPadding(0, activity.dp(14), 0, activity.dp(14)); setOnClickListener { accion() }
        }
        inferior.addView(t, LinearLayout.LayoutParams(0, WRAP_CONTENT, 1f))
    }
}
