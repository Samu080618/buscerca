"""Configuración leída de variables de entorno (ver .env.example)."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://buscerca:buscerca@localhost:5432/buscerca_db")
JWT_SECRETO = os.getenv("JWT_SECRETO", "cambiar-en-produccion")
JWT_MINUTOS = int(os.getenv("JWT_MINUTOS", "720"))
