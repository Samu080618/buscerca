class Ruta:
    @staticmethod
    def listar_activas(bd):
        return bd.consultar("SELECT id_ruta, codigo, nombre, origen, destino FROM ruta WHERE estado = 'Activa' ORDER BY codigo")

    @staticmethod
    def consultar(bd, id_ruta: int):
        return bd.consultar_uno(
            """SELECT id_ruta, codigo, nombre, origen, destino, estado, velocidad_historica_kmh,
                      ST_AsGeoJSON(trazado)::json AS trazado
               FROM ruta WHERE id_ruta = %s""", (id_ruta,))
