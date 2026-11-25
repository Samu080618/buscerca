_SELECT = """SELECT f.id_favorito, f.tipo, f.id_ruta, f.id_paradero, f.alias, f.fecha_creacion,
                    ru.codigo AS ruta_codigo, ru.nombre AS ruta_nombre, ru.estado AS ruta_estado, p.nombre AS paradero_nombre
             FROM favorito f LEFT JOIN ruta ru USING (id_ruta) LEFT JOIN paradero p USING (id_paradero)"""


class Favorito:
    @staticmethod
    def listar(bd, id_pasajero):
        return bd.consultar(_SELECT + " WHERE f.id_pasajero = %s ORDER BY f.fecha_creacion, f.id_favorito", (id_pasajero,))

    @staticmethod
    def contar(bd, id_pasajero) -> int:
        return bd.consultar_uno("SELECT count(*) AS n FROM favorito WHERE id_pasajero = %s", (id_pasajero,))["n"]

    @staticmethod
    def existe(bd, id_pasajero, tipo, id_ruta, id_paradero) -> bool:
        return bd.consultar_uno(
            """SELECT 1 FROM favorito WHERE id_pasajero = %s AND tipo = %s
               AND COALESCE(id_ruta, 0) = COALESCE(%s, 0) AND COALESCE(id_paradero, 0) = COALESCE(%s, 0)""",
            (id_pasajero, tipo, id_ruta, id_paradero)) is not None

    @staticmethod
    def guardar(bd, id_pasajero, tipo, id_ruta, id_paradero, alias, fecha) -> int:
        return bd.consultar_uno(
            """INSERT INTO favorito (id_pasajero, tipo, id_ruta, id_paradero, alias, fecha_creacion)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_favorito""",
            (id_pasajero, tipo, id_ruta, id_paradero, alias, fecha))["id_favorito"]

    @staticmethod
    def consultar_propio(bd, id_favorito, id_pasajero):
        return bd.consultar_uno(_SELECT + " WHERE f.id_favorito = %s AND f.id_pasajero = %s", (id_favorito, id_pasajero))

    @staticmethod
    def renombrar(bd, id_favorito, alias):
        bd.ejecutar("UPDATE favorito SET alias = %s WHERE id_favorito = %s", (alias, id_favorito))

    @staticmethod
    def eliminar(bd, id_favorito):
        bd.ejecutar("DELETE FROM favorito WHERE id_favorito = %s", (id_favorito,))
