"""Reloj del sistema. Las pruebas lo fijan para que las reglas que dependen del tiempo
(RN-206, RN-306 y RN-308) den siempre el mismo resultado."""
from datetime import datetime

_fijo: datetime | None = None


def ahora() -> datetime:
    return _fijo if _fijo is not None else datetime.now().replace(microsecond=0)


def fijar(momento: datetime | None) -> None:
    global _fijo
    _fijo = momento
