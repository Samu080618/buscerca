class Vehiculo:
    @staticmethod
    def listar_disponibles(bd):
        """Vehículos que no están en un recorrido EN CURSO."""
        return bd.consultar(
            """SELECT v.id_vehiculo, v.placa, v.numero_interno, v.tipo FROM vehiculo v
               WHERE NOT EXISTS (SELECT 1 FROM recorrido r WHERE r.id_vehiculo = v.id_vehiculo AND r.id_estado = 1)
               ORDER BY v.numero_interno""")

    @staticmethod
    def consultar(bd, id_vehiculo: int):
        return bd.consultar_uno("SELECT * FROM vehiculo WHERE id_vehiculo = %s", (id_vehiculo,))
