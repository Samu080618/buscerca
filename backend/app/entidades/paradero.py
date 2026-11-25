class Paradero:
    @staticmethod
    def consultar(bd, id_paradero):
        return bd.consultar_uno("SELECT id_paradero, nombre, vereda, municipio, latitud, longitud FROM paradero WHERE id_paradero = %s", (id_paradero,))

    @staticmethod
    def buscar_por_nombre(bd, texto_normalizado):
        return bd.consultar(
            """SELECT id_paradero, nombre FROM paradero
               WHERE nombre_normalizado LIKE %s OR translate(lower(coalesce(vereda, '')), 'áéíóúñ', 'aeioun') LIKE %s""",
            (f"%{texto_normalizado}%", f"%{texto_normalizado}%"))


class RutaParadero:
    @staticmethod
    def paraderos_de_ruta(bd, id_ruta):
        return bd.consultar(
            """SELECT p.id_paradero, p.nombre, p.latitud, p.longitud, rp.orden, rp.km_desde_inicio
               FROM ruta_paradero rp JOIN paradero p USING (id_paradero) WHERE rp.id_ruta = %s ORDER BY rp.orden""", (id_ruta,))

    @staticmethod
    def consultar(bd, id_ruta, id_paradero):
        return bd.consultar_uno("SELECT orden, km_desde_inicio FROM ruta_paradero WHERE id_ruta = %s AND id_paradero = %s", (id_ruta, id_paradero))

    @staticmethod
    def rutas_hacia(bd, ids_destino: list[int], lat: float, lon: float):
        """RN-302 y RN-303: rutas activas donde el destino está después del paradero de abordaje,
        que es el paradero de la ruta más cercano al pasajero a máximo 2 km."""
        return bd.consultar(
            """SELECT DISTINCT ON (ru.id_ruta) ru.id_ruta, ru.codigo, ru.nombre, ru.origen, ru.destino,
                      pa.id_paradero AS id_abordaje, pa.nombre AS abordaje, rpa.km_desde_inicio AS km_abordaje,
                      round(ST_Distance(pa.posicion, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography)) AS metros_abordaje,
                      pd.id_paradero AS id_destino, pd.nombre AS destino_paradero
               FROM ruta ru
               JOIN ruta_paradero rpd ON rpd.id_ruta = ru.id_ruta AND rpd.id_paradero = ANY(%(dest)s)
               JOIN paradero pd ON pd.id_paradero = rpd.id_paradero
               JOIN ruta_paradero rpa ON rpa.id_ruta = ru.id_ruta AND rpa.orden < rpd.orden
               JOIN paradero pa ON pa.id_paradero = rpa.id_paradero
               WHERE ru.estado = 'Activa'
                 AND ST_DWithin(pa.posicion, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography, 2000)
               ORDER BY ru.id_ruta, ST_Distance(pa.posicion, ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography)""",
            {"dest": ids_destino, "lat": lat, "lon": lon})
