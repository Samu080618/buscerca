"""Inicio de sesión (Módulo 01)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.control.control_sesion import ControlSesion, usuario_actual
from app.datos.conexion_bd import obtener_bd
from app.entidades.usuario import Usuario

router = APIRouter(prefix="/api/auth", tags=["Módulo 01 — Sesión"])


class Credenciales(BaseModel):
    correo: str
    contrasena: str


@router.post("/login")
def login(c: Credenciales, bd=Depends(obtener_bd)):
    return ControlSesion.iniciar_sesion(bd, c.correo, c.contrasena)


@router.get("/yo")
def yo(u=Depends(usuario_actual), bd=Depends(obtener_bd)):
    d = Usuario.buscar(bd, u["id"])
    return {"id": d["id_usuario"], "nombre": d["nombre"], "rol": d["rol"]}
