"""Inicio de sesión y verificación del token (Módulo 01, usado por los módulos 02 y 03)."""
from datetime import timedelta

import jwt
from fastapi import Depends, Header

from app import config, reloj
from app.datos.conexion_bd import obtener_bd
from app.entidades.usuario import Usuario
from app.errores import ErrorNegocio


class ControlSesion:
    @staticmethod
    def iniciar_sesion(bd, correo: str, contrasena: str) -> dict:
        u = Usuario.buscar_por_correo(bd, correo)
        if u is None or not Usuario.verificar_contrasena(u, contrasena):
            raise ErrorNegocio(401, "Correo o contraseña incorrectos")
        token = jwt.encode({"sub": str(u["id_usuario"]), "rol": u["rol"],
                            "exp": reloj.ahora() + timedelta(minutes=config.JWT_MINUTOS)}, config.JWT_SECRETO, algorithm="HS256")
        return {"token": token, "usuario": {"id": u["id_usuario"], "nombre": u["nombre"], "rol": u["rol"]}}

    @staticmethod
    def validar_token(token: str) -> dict:
        try:
            datos = jwt.decode(token, config.JWT_SECRETO, algorithms=["HS256"], options={"verify_exp": False})
        except jwt.PyJWTError:
            raise ErrorNegocio(401, "Sesión no válida")
        if datos["exp"] < reloj.ahora().timestamp():
            raise ErrorNegocio(401, "La sesión venció; inicia sesión de nuevo")
        return {"id": int(datos["sub"]), "rol": datos["rol"]}


def usuario_actual(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise ErrorNegocio(401, "Inicia sesión para continuar")
    return ControlSesion.validar_token(authorization[7:])


def requiere_rol(*roles: str):
    def dependencia(usuario: dict = Depends(usuario_actual)) -> dict:
        if usuario["rol"] not in roles:
            raise ErrorNegocio(403, "Tu perfil no tiene acceso a esta opción")
        return usuario
    return dependencia


__all__ = ["ControlSesion", "usuario_actual", "requiere_rol", "obtener_bd"]
