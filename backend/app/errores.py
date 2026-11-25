from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder


class ErrorNegocio(HTTPException):
    """Error de una regla de negocio: se devuelve como {"detail": mensaje} con su código HTTP."""

    def __init__(self, codigo: int, mensaje: str):
        super().__init__(status_code=codigo, detail=jsonable_encoder(mensaje))
