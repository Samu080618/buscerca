"""Servicios REST del Módulo 01: Autenticación y Perfiles (Sprint 1)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.control.control_perfil import ControlPerfil
from app.control.control_sesion import ControlSesion, usuario_actual, usuario_opcional
from app.datos.conexion_bd import obtener_bd

router = APIRouter(prefix="/api", tags=["Módulo 01 — Autenticación y Perfiles"])


class Credenciales(BaseModel):
    correo: str
    contrasena: str


class Registro(BaseModel):
    nombre: str
    correo: str
    contrasena: str
    rol: str = "PASAJERO"
    documento: str | None = None
    telefono: str | None = None


class Correo(BaseModel):
    correo: str


class Restablecer(BaseModel):
    correo: str
    codigo: str
    nueva: str


class DatosPerfil(BaseModel):
    nombre: str
    telefono: str | None = None
    direccion: str | None = None


class CambioClave(BaseModel):
    actual: str
    nueva: str


@router.post("/auth/registro", status_code=201)
def registro(d: Registro, solicitante=Depends(usuario_opcional), bd=Depends(obtener_bd)):
    return ControlSesion.registrar(bd, d.model_dump(), solicitante)


@router.post("/auth/login")
def login(c: Credenciales, bd=Depends(obtener_bd)):
    return ControlSesion.iniciar_sesion(bd, c.correo, c.contrasena)


@router.post("/auth/recuperar")
def recuperar(c: Correo, bd=Depends(obtener_bd)):
    return ControlSesion.solicitar_codigo(bd, c.correo)


@router.post("/auth/restablecer")
def restablecer(d: Restablecer, bd=Depends(obtener_bd)):
    return ControlSesion.restablecer(bd, d.correo, d.codigo, d.nueva)


@router.post("/auth/logout")
def logout(u=Depends(usuario_actual), bd=Depends(obtener_bd)):
    return ControlSesion.cerrar_sesion(bd, u)


@router.get("/auth/yo")
def yo(u=Depends(usuario_actual), bd=Depends(obtener_bd)):
    p = ControlPerfil.consultar(bd, u)
    return {"id": p["id_usuario"], "nombre": p["nombre"], "rol": p["rol"]}


@router.get("/perfil")
def perfil(u=Depends(usuario_actual), bd=Depends(obtener_bd)):
    return ControlPerfil.consultar(bd, u)


@router.patch("/perfil")
def editar(d: DatosPerfil, u=Depends(usuario_actual), bd=Depends(obtener_bd)):
    return ControlPerfil.actualizar(bd, u, d.nombre, d.telefono, d.direccion)


@router.post("/perfil/contrasena")
def cambiar_clave(d: CambioClave, u=Depends(usuario_actual), bd=Depends(obtener_bd)):
    return ControlPerfil.cambiar_contrasena(bd, u, d.actual, d.nueva)
