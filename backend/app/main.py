"""API REST de BusCerca (capa lógica). Ejecutar: uvicorn app.main:app --host 0.0.0.0 --port 8000"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import conductor, pasajero, sesion

app = FastAPI(title="BusCerca API", version="0.3.0",
              description="Módulo 02 (Panel del Conductor) y Módulo 03 (Panel del Pasajero).")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(sesion.router)
app.include_router(conductor.router)
app.include_router(pasajero.router)


@app.get("/", include_in_schema=False)
def inicio():
    return {"app": "BusCerca API", "documentacion": "/docs"}


@app.get("/api/salud", tags=["General"])
def salud():
    return {"estado": "ok"}


@app.on_event("startup")
def arrancar_demo():
    if os.getenv("SIMULAR_BUSES") == "1":
        from app import demo
        demo.iniciar()
