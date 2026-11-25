"""CU-202 Transmitir ubicación, CU-203 (pendientes enviadas en lote) y CU-204 Calcular velocidad promedio."""
from datetime import timedelta
from decimal import Decimal

from app.entidades.recorrido import Recorrido
from app.entidades.ubicacion import Ubicacion
from app.errores import ErrorNegocio

VENTANA = timedelta(minutes=5)       # RN-206
VEL_MIN, VEL_MAX = 0, 120            # RN-206: lecturas válidas


class ControlUbicacion:
    @staticmethod
    def verificar_en_curso(bd, usuario: dict, id_recorrido: int) -> dict:
        r = Recorrido.consultar(bd, id_recorrido)
        if r is None:
            raise ErrorNegocio(404, "Recorrido no encontrado")
        if r["id_usuario"] != usuario["id"] or r["id_estado"] != 1:  # RN-203 y RN-205
            raise ErrorNegocio(409, "El recorrido no está en curso")
        return r

    @staticmethod
    def calcular_promedio(lecturas: list) -> Decimal | None:
        validas = [Decimal(str(v)) for v in lecturas if v is not None and VEL_MIN <= float(v) <= VEL_MAX]
        if not validas:
            return None
        return (sum(validas) / len(validas)).quantize(Decimal("0.01"))

    @staticmethod
    def registrar_ubicaciones(bd, usuario: dict, id_recorrido: int, coordenadas: list[dict]) -> dict:
        ControlUbicacion.verificar_en_curso(bd, usuario, id_recorrido)
        if not coordenadas:
            raise ErrorNegocio(400, "No se recibieron coordenadas")
        for c in coordenadas:
            if not (-90 <= c["latitud"] <= 90 and -180 <= c["longitud"] <= 180):
                raise ErrorNegocio(400, "Coordenada fuera de rango")
        guardadas = duplicadas = 0
        promedio = None
        for c in sorted(coordenadas, key=lambda x: x["fecha_hora"]):  # RN-204: en orden de captura
            id_u = Ubicacion.guardar(bd, id_recorrido, c["latitud"], c["longitud"], c.get("velocidad"), c["fecha_hora"])
            if id_u is None:
                duplicadas += 1
                continue
            guardadas += 1
            lecturas = Ubicacion.lecturas_desde(bd, id_recorrido, c["fecha_hora"] - VENTANA, c["fecha_hora"])
            promedio = ControlUbicacion.calcular_promedio([x["velocidad"] for x in lecturas])
            Ubicacion.actualizar_velocidad_promedio(bd, id_u, promedio)
        return {"recibidas": len(coordenadas), "guardadas": guardadas, "duplicadas": duplicadas, "velocidad_promedio": promedio}

    @staticmethod
    def consultar_velocidad(bd, usuario: dict, id_recorrido: int) -> dict:
        r = Recorrido.consultar(bd, id_recorrido)
        if r is None or r["id_usuario"] != usuario["id"]:
            raise ErrorNegocio(404, "Recorrido no encontrado")
        ult = Ubicacion.ultima(bd, id_recorrido)
        return {"velocidad_promedio": ult and ult["velocidad_promedio"], "fecha_hora": ult and ult["fecha_hora"]}
