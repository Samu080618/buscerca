class TipoNovedad:
    @staticmethod
    def listar(bd):
        return bd.consultar("SELECT id_tipo_novedad, descripcion FROM tipo_novedad ORDER BY id_tipo_novedad")

    @staticmethod
    def existe(bd, id_tipo) -> bool:
        return bd.consultar_uno("SELECT 1 FROM tipo_novedad WHERE id_tipo_novedad = %s", (id_tipo,)) is not None


class Novedad:
    @staticmethod
    def guardar(bd, id_recorrido, id_tipo, comentario, latitud, longitud, fecha_hora) -> int:
        return bd.consultar_uno(
            """INSERT INTO novedad (id_recorrido, id_tipo_novedad, comentario, latitud, longitud, fecha_hora)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_novedad""",
            (id_recorrido, id_tipo, comentario, latitud, longitud, fecha_hora))["id_novedad"]

    @staticmethod
    def ultima_de_recorrido(bd, id_recorrido):
        return bd.consultar_uno(
            """SELECT t.descripcion AS tipo, n.comentario, n.fecha_hora FROM novedad n JOIN tipo_novedad t USING (id_tipo_novedad)
               WHERE n.id_recorrido = %s ORDER BY n.fecha_hora DESC LIMIT 1""", (id_recorrido,))
