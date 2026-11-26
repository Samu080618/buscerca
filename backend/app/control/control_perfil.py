"""HU-0104 Edición de datos del perfil."""
import re

from app.control.control_sesion import validar_contrasena, validar_nombre
from app.entidades.usuario import Perfil, Usuario
from app.errores import ErrorNegocio


class ControlPerfil:
    @staticmethod
    def consultar(bd, usuario: dict) -> dict:
        return Perfil.consultar(bd, usuario["id"])

    @staticmethod
    def actualizar(bd, usuario: dict, nombre, telefono, direccion) -> dict:
        nombre = validar_nombre(nombre)
        telefono = (telefono or "").strip() or None
        if telefono and not re.fullmatch(r"\d{7,10}", telefono):
            raise ErrorNegocio(400, "El teléfono debe tener entre 7 y 10 dígitos")
        direccion = (direccion or "").strip() or None
        if direccion and len(direccion) > 120:
            raise ErrorNegocio(400, "La dirección admite máximo 120 caracteres")
        Perfil.actualizar(bd, usuario["id"], nombre, telefono, direccion)
        return {**Perfil.consultar(bd, usuario["id"]), "mensaje": "Datos actualizados"}

    @staticmethod
    def cambiar_contrasena(bd, usuario: dict, actual: str, nueva: str) -> dict:
        u = Usuario.buscar(bd, usuario["id"])
        if not Usuario.verificar_contrasena(u, actual or ""):
            raise ErrorNegocio(400, "La contraseña actual no es correcta")
        validar_contrasena(nueva)
        Perfil.cambiar_contrasena(bd, usuario["id"], nueva)
        return {"mensaje": "Contraseña actualizada"}
