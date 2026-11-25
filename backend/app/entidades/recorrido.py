EN_CURSO, FINALIZADO, PROGRAMADO, CANCELADO = 1, 2, 3, 4

_SELECT = """SELECT r.id_recorrido, r.id_usuario, r.id_vehiculo, r.id_ruta, r.id_estado, e.descripcion AS estado,
                    r.fecha_inicio, r.fecha_fin, ru.codigo AS ruta_codigo, ru.nombre AS ruta_nombre,
                    v.placa, v.numero_interno
             FROM recorrido r JOIN estado_recorrido e USING (id_estado)
             JOIN ruta ru USING (id_ruta) JOIN vehiculo v USING (id_vehiculo)"""


class Recorrido:
    @staticmethod
    def consultar(bd, id_recorrido: int):
        return bd.consultar_uno(_SELECT + " WHERE r.id_recorrido = %s", (id_recorrido,))

    @staticmethod
    def consultar_activo(bd, id_usuario: int):
        return bd.consultar_uno(_SELECT + " WHERE r.id_usuario = %s AND r.id_estado = 1", (id_usuario,))

    @staticmethod
    def crear(bd, id_usuario, id_ruta, id_vehiculo, fecha_inicio) -> int:
        return bd.consultar_uno(
            """INSERT INTO recorrido (id_usuario, id_ruta, id_vehiculo, id_estado, fecha_inicio)
               VALUES (%s, %s, %s, 1, %s) RETURNING id_recorrido""",
            (id_usuario, id_ruta, id_vehiculo, fecha_inicio))["id_recorrido"]

    @staticmethod
    def finalizar(bd, id_recorrido: int, fecha_fin):
        bd.ejecutar("UPDATE recorrido SET id_estado = 2, fecha_fin = %s WHERE id_recorrido = %s", (fecha_fin, id_recorrido))

    @staticmethod
    def en_curso_de_ruta(bd, id_ruta: int):
        return bd.consultar(_SELECT + " WHERE r.id_ruta = %s AND r.id_estado = 1", (id_ruta,))

    @staticmethod
    def proxima_salida(bd, id_ruta: int, desde):
        return bd.consultar_uno(
            "SELECT fecha_inicio FROM recorrido WHERE id_ruta = %s AND id_estado = 3 AND fecha_inicio >= %s ORDER BY fecha_inicio LIMIT 1",
            (id_ruta, desde))
