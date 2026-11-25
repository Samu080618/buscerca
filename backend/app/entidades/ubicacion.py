class Ubicacion:
    @staticmethod
    def guardar(bd, id_recorrido, latitud, longitud, velocidad, fecha_hora) -> int | None:
        """Guarda la coordenada, proyecta su kilómetro sobre el trazado de la ruta y devuelve su id.
        Devuelve None si ya existía (RN-204: sin duplicados)."""
        fila = bd.consultar_uno(
            """INSERT INTO ubicacion (id_recorrido, latitud, longitud, posicion, velocidad, fecha_hora, km_en_ruta)
               SELECT %(r)s, %(lat)s, %(lon)s, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography, %(vel)s, %(f)s,
                      CASE WHEN ru.trazado IS NULL THEN NULL ELSE
                        round((ST_LineLocatePoint(ru.trazado::geometry, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326))
                               * ST_Length(ru.trazado) / 1000)::numeric, 2) END
               FROM recorrido r JOIN ruta ru USING (id_ruta) WHERE r.id_recorrido = %(r)s
               ON CONFLICT (id_recorrido, fecha_hora) DO NOTHING
               RETURNING id_ubicacion""",
            {"r": id_recorrido, "lat": latitud, "lon": longitud, "vel": velocidad, "f": fecha_hora})
        return fila["id_ubicacion"] if fila else None

    @staticmethod
    def lecturas_desde(bd, id_recorrido, desde, hasta):
        return bd.consultar(
            "SELECT velocidad FROM ubicacion WHERE id_recorrido = %s AND fecha_hora > %s AND fecha_hora <= %s",
            (id_recorrido, desde, hasta))

    @staticmethod
    def actualizar_velocidad_promedio(bd, id_ubicacion, valor):
        bd.ejecutar("UPDATE ubicacion SET velocidad_promedio = %s WHERE id_ubicacion = %s", (valor, id_ubicacion))

    @staticmethod
    def ultima(bd, id_recorrido):
        return bd.consultar_uno(
            """SELECT latitud, longitud, velocidad, velocidad_promedio, km_en_ruta, fecha_hora
               FROM ubicacion WHERE id_recorrido = %s ORDER BY fecha_hora DESC LIMIT 1""", (id_recorrido,))

    @staticmethod
    def listar(bd, id_recorrido):
        return bd.consultar("SELECT * FROM ubicacion WHERE id_recorrido = %s ORDER BY fecha_hora", (id_recorrido,))
