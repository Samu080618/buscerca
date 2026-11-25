package co.buscerca.app.datos

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

/**
 * CU-203: guarda en el teléfono (SQLite) las coordenadas que no se pudieron enviar.
 * Clase UbicacionPendiente del modelo lógico. Sobrevive a cierres de la app y reinicios.
 */
class AlmacenLocal(context: Context) : SQLiteOpenHelper(context.applicationContext, "buscerca_local.db", null, 1) {

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """CREATE TABLE ubicacion_pendiente (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 id_recorrido INTEGER NOT NULL,
                 latitud REAL NOT NULL, longitud REAL NOT NULL, velocidad REAL,
                 fecha_hora TEXT NOT NULL,
                 UNIQUE (id_recorrido, fecha_hora))"""
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, anterior: Int, nueva: Int) = Unit

    fun guardar(idRecorrido: Int, c: Coordenada) {
        val v = ContentValues().apply {
            put("id_recorrido", idRecorrido); put("latitud", c.latitud); put("longitud", c.longitud)
            put("velocidad", c.velocidad); put("fecha_hora", c.fecha_hora)
        }
        writableDatabase.insertWithOnConflict("ubicacion_pendiente", null, v, SQLiteDatabase.CONFLICT_IGNORE)
    }

    /** Pendientes del recorrido en orden de captura (RN-204). */
    fun pendientes(idRecorrido: Int, limite: Int = 200): List<Pair<Long, Coordenada>> {
        val lista = mutableListOf<Pair<Long, Coordenada>>()
        readableDatabase.rawQuery(
            "SELECT id, latitud, longitud, velocidad, fecha_hora FROM ubicacion_pendiente WHERE id_recorrido = ? ORDER BY fecha_hora LIMIT ?",
            arrayOf(idRecorrido.toString(), limite.toString())
        ).use { c ->
            while (c.moveToNext()) {
                val vel = if (c.isNull(3)) null else c.getDouble(3)
                lista += c.getLong(0) to Coordenada(c.getDouble(1), c.getDouble(2), vel, c.getString(4))
            }
        }
        return lista
    }

    fun contar(idRecorrido: Int): Int =
        readableDatabase.rawQuery("SELECT count(*) FROM ubicacion_pendiente WHERE id_recorrido = ?", arrayOf(idRecorrido.toString()))
            .use { c -> if (c.moveToFirst()) c.getInt(0) else 0 }

    fun eliminar(ids: List<Long>) {
        if (ids.isEmpty()) return
        writableDatabase.execSQL("DELETE FROM ubicacion_pendiente WHERE id IN (${ids.joinToString(",")})")
    }

    fun limpiar(idRecorrido: Int) {
        writableDatabase.delete("ubicacion_pendiente", "id_recorrido = ?", arrayOf(idRecorrido.toString()))
    }
}
