"""CU-16 Guardar favorito y CU-17 Administrar favoritos (RN-310 y RN-311)."""
from app import reloj
from app.entidades.favorito import Favorito
from app.entidades.paradero import Paradero, RutaParadero
from app.entidades.ruta import Ruta
from app.errores import ErrorNegocio

MAX_FAVORITOS = 10
MAX_ALIAS = 30


def _validar_alias(alias):
    if alias is not None and len(alias.strip()) > MAX_ALIAS:
        raise ErrorNegocio(400, "El alias admite máximo 30 caracteres")
    return alias.strip() if alias and alias.strip() else None


def _publico(f):
    return {**f, "disponible": f["ruta_estado"] != "Inactiva", "aviso": "Ruta no disponible" if f["ruta_estado"] == "Inactiva" else None}


class ControlFavoritos:
    @staticmethod
    def listar(bd, usuario):
        return [_publico(f) for f in Favorito.listar(bd, usuario["id"])]

    @staticmethod
    def guardar(bd, usuario, tipo, id_ruta, id_paradero, alias) -> dict:
        tipo = (tipo or "").upper()
        if tipo not in ("RUTA", "PARADERO"):
            raise ErrorNegocio(400, "Tipo de favorito no válido")
        alias = _validar_alias(alias)
        if tipo == "RUTA" and (not id_ruta or Ruta.consultar(bd, id_ruta) is None):
            raise ErrorNegocio(400, "Ruta no válida")
        if tipo == "PARADERO" and (not id_paradero or Paradero.consultar(bd, id_paradero) is None):
            raise ErrorNegocio(400, "Paradero no válido")
        if id_ruta and id_paradero and RutaParadero.consultar(bd, id_ruta, id_paradero) is None:
            raise ErrorNegocio(400, "El paradero no pertenece a la ruta")
        if Favorito.existe(bd, usuario["id"], tipo, id_ruta, id_paradero):
            raise ErrorNegocio(409, "Ya está en tus favoritos")
        if Favorito.contar(bd, usuario["id"]) >= MAX_FAVORITOS:
            raise ErrorNegocio(409, "Llegaste al máximo de 10 favoritos. Elimina uno para guardar otro")
        id_f = Favorito.guardar(bd, usuario["id"], tipo, id_ruta, id_paradero, alias, reloj.ahora())
        return _publico(Favorito.consultar_propio(bd, id_f, usuario["id"]))

    @staticmethod
    def _propio(bd, usuario, id_favorito):
        f = Favorito.consultar_propio(bd, id_favorito, usuario["id"])
        if f is None:  # RN-311: no revela si existe para otro usuario
            raise ErrorNegocio(404, "Favorito no encontrado")
        return f

    @staticmethod
    def consultar(bd, usuario, id_favorito):
        return _publico(ControlFavoritos._propio(bd, usuario, id_favorito))

    @staticmethod
    def renombrar(bd, usuario, id_favorito, alias):
        ControlFavoritos._propio(bd, usuario, id_favorito)
        Favorito.renombrar(bd, id_favorito, _validar_alias(alias))
        return _publico(Favorito.consultar_propio(bd, id_favorito, usuario["id"]))

    @staticmethod
    def eliminar(bd, usuario, id_favorito):
        ControlFavoritos._propio(bd, usuario, id_favorito)
        Favorito.eliminar(bd, id_favorito)
