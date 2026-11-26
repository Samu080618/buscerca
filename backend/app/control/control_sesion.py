"""Módulo 01 — Autenticación y Perfiles: registro (HU-0101), inicio de sesión (HU-0102),
recuperación de contraseña (HU-0103) y cierre de sesión seguro (HU-0105)."""
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, Header

from app import config, reloj
from app.datos.conexion_bd import ConexionBD, obtener_bd
from app.entidades.usuario import Perfil, RecuperacionContrasena, TokenRevocado, Usuario
from app.errores import ErrorNegocio

ROLES_REGISTRO = ("PASAJERO", "CONDUCTOR", "ADMINISTRADOR")
CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
VIGENCIA_CODIGO = timedelta(minutes=15)
MAX_INTENTOS = 5


def validar_contrasena(clave: str):
    if len(clave or "") < 8 or not re.search(r"[A-Za-z]", clave) or not re.search(r"\d", clave):
        raise ErrorNegocio(400, "La contraseña debe tener mínimo 8 caracteres, con letras y números")


def validar_nombre(nombre: str) -> str:
    n = " ".join((nombre or "").split())
    if not 3 <= len(n) <= 80:
        raise ErrorNegocio(400, "Escribe tu nombre completo (entre 3 y 80 caracteres)")
    return n


class ControlSesion:
    @staticmethod
    def registrar(bd, datos: dict, solicitante: dict | None) -> dict:
        nombre = validar_nombre(datos.get("nombre"))
        correo = (datos.get("correo") or "").strip().lower()
        if not CORREO.match(correo):
            raise ErrorNegocio(400, "Escribe un correo válido")
        validar_contrasena(datos.get("contrasena"))
        rol = (datos.get("rol") or "PASAJERO").upper()
        if rol not in ROLES_REGISTRO:
            raise ErrorNegocio(400, "Rol no válido")
        if rol == "ADMINISTRADOR" and (solicitante is None or solicitante["rol"] != "ADMINISTRADOR"):
            raise ErrorNegocio(403, "Solo un administrador puede crear otro administrador")
        if Usuario.buscar_por_correo(bd, correo):
            raise ErrorNegocio(409, "El correo ya está registrado")
        id_u = Usuario.crear(bd, nombre, correo, datos["contrasena"], rol, datos.get("documento"), datos.get("telefono"))
        return {"id": id_u, "nombre": nombre, "correo": correo, "rol": rol, "mensaje": "Cuenta creada. Ya puedes iniciar sesión"}

    @staticmethod
    def iniciar_sesion(bd, correo: str, contrasena: str) -> dict:
        u = Usuario.buscar_por_correo(bd, (correo or "").strip())
        if u is None or not Usuario.verificar_contrasena(u, contrasena or ""):
            raise ErrorNegocio(401, "Correo o contraseña incorrectos")
        exp = reloj.ahora() + timedelta(minutes=config.JWT_MINUTOS)
        token = jwt.encode({"sub": str(u["id_usuario"]), "rol": u["rol"], "jti": uuid.uuid4().hex, "exp": exp.timestamp()},
                           config.JWT_SECRETO, algorithm="HS256")
        return {"token": token, "usuario": {"id": u["id_usuario"], "nombre": u["nombre"], "rol": u["rol"]}}

    @staticmethod
    def decodificar(token: str) -> dict:
        try:
            datos = jwt.decode(token, config.JWT_SECRETO, algorithms=["HS256"], options={"verify_exp": False})
        except jwt.PyJWTError:
            raise ErrorNegocio(401, "Sesión no válida")
        if datos["exp"] < reloj.ahora().timestamp():
            raise ErrorNegocio(401, "La sesión venció; inicia sesión de nuevo")
        return datos

    @staticmethod
    def validar_token(bd, token: str) -> dict:
        datos = ControlSesion.decodificar(token)
        if datos.get("jti") and TokenRevocado.esta_revocado(bd, datos["jti"]):  # HU-0105
            raise ErrorNegocio(401, "La sesión fue cerrada; inicia sesión de nuevo")
        return {"id": int(datos["sub"]), "rol": datos["rol"], "jti": datos.get("jti"), "exp": datos["exp"]}

    @staticmethod
    def cerrar_sesion(bd, usuario: dict) -> dict:
        if usuario.get("jti"):
            TokenRevocado.revocar(bd, usuario["jti"], datetime.fromtimestamp(usuario["exp"]))
        return {"mensaje": "Sesión cerrada"}

    @staticmethod
    def solicitar_codigo(bd, correo: str) -> dict:
        """HU-0103: genera un código de 6 dígitos válido 15 minutos. La respuesta es la misma exista o no
        el correo, para no revelar qué cuentas existen. Con DEMO_CODIGO=1 (sin servidor de correo) el código
        se devuelve en la respuesta para la demostración."""
        resp = {"mensaje": "Si el correo está registrado, te enviamos un código de 6 dígitos válido por 15 minutos"}
        u = Usuario.buscar_por_correo(bd, (correo or "").strip())
        if u:
            codigo = f"{secrets.randbelow(1_000_000):06d}"
            RecuperacionContrasena.crear(bd, u["id_usuario"], codigo, reloj.ahora() + VIGENCIA_CODIGO)
            if os.getenv("DEMO_CODIGO") == "1":
                resp["codigo_demo"] = codigo
        return resp

    @staticmethod
    def restablecer(bd, correo: str, codigo: str, nueva: str) -> dict:
        u = Usuario.buscar_por_correo(bd, (correo or "").strip())
        rec = u and RecuperacionContrasena.vigente(bd, u["id_usuario"], reloj.ahora())
        if not rec or rec["intentos"] >= MAX_INTENTOS:
            raise ErrorNegocio(400, "El código no es válido o ya venció; solicita uno nuevo")
        if not bcrypt.checkpw((codigo or "").encode(), rec["codigo_hash"].encode()):
            RecuperacionContrasena.sumar_intento(bd, rec["id_recuperacion"])
            bd.confirmar()
            raise ErrorNegocio(400, "El código no es válido o ya venció; solicita uno nuevo")
        validar_contrasena(nueva)
        Perfil.cambiar_contrasena(bd, u["id_usuario"], nueva)
        RecuperacionContrasena.marcar_usado(bd, rec["id_recuperacion"])
        return {"mensaje": "Contraseña actualizada. Ya puedes iniciar sesión"}


def usuario_actual(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise ErrorNegocio(401, "Inicia sesión para continuar")
    bd = ConexionBD()
    try:
        return ControlSesion.validar_token(bd, authorization[7:])
    finally:
        bd.cerrar()


def usuario_opcional(authorization: str | None = Header(default=None)) -> dict | None:
    return usuario_actual(authorization) if authorization else None


def requiere_rol(*roles: str):
    def dependencia(usuario: dict = Depends(usuario_actual)) -> dict:
        if usuario["rol"] not in roles:
            raise ErrorNegocio(403, "Tu perfil no tiene acceso a esta opción")
        return usuario
    return dependencia


__all__ = ["ControlSesion", "usuario_actual", "usuario_opcional", "requiere_rol", "obtener_bd", "validar_contrasena", "validar_nombre"]
