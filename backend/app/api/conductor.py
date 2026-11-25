"""Servicios REST del Módulo 02: Panel del Conductor (Sprint 2)."""
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.control.control_novedad import ControlNovedad
from app.control.control_recorrido import ControlRecorrido
from app.control.control_sesion import requiere_rol
from app.control.control_ubicacion import ControlUbicacion
from app.datos.conexion_bd import obtener_bd

router = APIRouter(prefix="/api", tags=["Módulo 02 — Conductor"])
conductor = requiere_rol("CONDUCTOR")


class NuevoRecorrido(BaseModel):
    id_ruta: int | None = None
    id_vehiculo: int | None = None


class Coordenada(BaseModel):
    latitud: float
    longitud: float
    velocidad: float | None = None
    fecha_hora: datetime


class Lote(BaseModel):
    coordenadas: list[Coordenada] = Field(min_length=1, max_length=500)


class NuevaNovedad(BaseModel):
    id_tipo_novedad: int | None = None
    comentario: str | None = None
    latitud: float | None = None
    longitud: float | None = None


@router.get("/recorridos/opciones")
def opciones(u=Depends(conductor), bd=Depends(obtener_bd)):
    return ControlRecorrido.consultar_opciones(bd)


@router.post("/recorridos", status_code=201)
def iniciar(datos: NuevoRecorrido, u=Depends(conductor), bd=Depends(obtener_bd)):
    return ControlRecorrido.iniciar_recorrido(bd, u, datos.id_ruta, datos.id_vehiculo)


@router.get("/recorridos/activo")
def activo(u=Depends(conductor), bd=Depends(obtener_bd)):
    return ControlRecorrido.consultar_estado(bd, u)


@router.post("/recorridos/{id_recorrido}/ubicaciones", status_code=201)
def ubicaciones(id_recorrido: int, lote: Lote, u=Depends(conductor), bd=Depends(obtener_bd)):
    return ControlUbicacion.registrar_ubicaciones(bd, u, id_recorrido, [c.model_dump() for c in lote.coordenadas])


@router.get("/recorridos/{id_recorrido}/velocidad")
def velocidad(id_recorrido: int, u=Depends(conductor), bd=Depends(obtener_bd)):
    return ControlUbicacion.consultar_velocidad(bd, u, id_recorrido)


@router.get("/tipos-novedad")
def tipos(u=Depends(conductor), bd=Depends(obtener_bd)):
    return ControlNovedad.listar_tipos(bd)


@router.post("/recorridos/{id_recorrido}/novedades", status_code=201)
def novedad(id_recorrido: int, datos: NuevaNovedad, u=Depends(conductor), bd=Depends(obtener_bd)):
    return ControlNovedad.registrar_novedad(bd, u, id_recorrido, datos.id_tipo_novedad, datos.comentario, datos.latitud, datos.longitud)


@router.patch("/recorridos/{id_recorrido}/finalizar")
def finalizar(id_recorrido: int, u=Depends(conductor), bd=Depends(obtener_bd)):
    return ControlRecorrido.finalizar_recorrido(bd, u, id_recorrido)
