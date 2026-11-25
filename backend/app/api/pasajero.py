"""Servicios REST del Módulo 03: Panel del Pasajero (Sprint 3)."""
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.control.control_busqueda import ControlBusqueda
from app.control.control_favoritos import ControlFavoritos
from app.control.control_llegada import ControlLlegada
from app.control.control_mapa import ControlMapa
from app.control.control_sesion import requiere_rol, usuario_actual
from app.datos.conexion_bd import obtener_bd

router = APIRouter(prefix="/api", tags=["Módulo 03 — Pasajero"])
pasajero = requiere_rol("PASAJERO")


class NuevoFavorito(BaseModel):
    tipo: str
    id_ruta: int | None = None
    id_paradero: int | None = None
    alias: str | None = None


class Renombrar(BaseModel):
    alias: str | None = None


@router.get("/rutas/buscar")
def buscar(texto: str = "", lat: float = 0, lon: float = 0, u=Depends(usuario_actual), bd=Depends(obtener_bd)):
    return ControlBusqueda.buscar_rutas(bd, texto, lat, lon)


@router.get("/rutas/{id_ruta}/trazado")
def trazado(id_ruta: int, u=Depends(usuario_actual), bd=Depends(obtener_bd)):
    return ControlMapa.consultar_trazado(bd, id_ruta)


@router.get("/rutas/{id_ruta}/buses")
def buses(id_ruta: int, paradero: int | None = None, u=Depends(usuario_actual), bd=Depends(obtener_bd)):
    return ControlMapa.consultar_buses(bd, id_ruta, paradero)


@router.get("/recorridos/{id_recorrido}/ficha")
def ficha(id_recorrido: int, u=Depends(usuario_actual), bd=Depends(obtener_bd)):
    return ControlMapa.consultar_ficha(bd, id_recorrido)


@router.get("/paraderos/{id_paradero}/llegadas")
def llegadas(id_paradero: int, ruta: int, u=Depends(usuario_actual), bd=Depends(obtener_bd)):
    return ControlLlegada.consultar_llegadas(bd, id_paradero, ruta)


@router.get("/favoritos")
def listar(u=Depends(pasajero), bd=Depends(obtener_bd)):
    return ControlFavoritos.listar(bd, u)


@router.post("/favoritos", status_code=201)
def guardar(datos: NuevoFavorito, u=Depends(pasajero), bd=Depends(obtener_bd)):
    return ControlFavoritos.guardar(bd, u, datos.tipo, datos.id_ruta, datos.id_paradero, datos.alias)


@router.get("/favoritos/{id_favorito}")
def consultar(id_favorito: int, u=Depends(pasajero), bd=Depends(obtener_bd)):
    return ControlFavoritos.consultar(bd, u, id_favorito)


@router.patch("/favoritos/{id_favorito}")
def renombrar(id_favorito: int, datos: Renombrar, u=Depends(pasajero), bd=Depends(obtener_bd)):
    return ControlFavoritos.renombrar(bd, u, id_favorito, datos.alias)


@router.delete("/favoritos/{id_favorito}", status_code=204)
def eliminar(id_favorito: int, u=Depends(pasajero), bd=Depends(obtener_bd)):
    ControlFavoritos.eliminar(bd, u, id_favorito)
    return Response(status_code=204)
