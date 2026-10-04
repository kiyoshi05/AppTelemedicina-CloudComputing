"""Llamadas HTTP a otros microservicios dentro de la red de Docker."""
import os

import httpx
from fastapi import HTTPException, status

PACIENTES_URL = os.getenv("PACIENTES_URL", "http://localhost:8001")
MEDICOS_URL = os.getenv("MEDICOS_URL", "http://localhost:8002")
TIMEOUT = 5.0


def _get(url: str):
    """Devuelve el JSON, None si el recurso no existe, o 503 si el servicio no responde."""
    try:
        respuesta = httpx.get(url, timeout=TIMEOUT)
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Servicio no disponible: {url}")
    if respuesta.status_code == status.HTTP_404_NOT_FOUND:
        return None
    if respuesta.is_error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Error consultando {url}")
    return respuesta.json()


def obtener_paciente(paciente_id: int):
    return _get(f"{PACIENTES_URL}/{paciente_id}")


def obtener_medico(medico_id: int):
    return _get(f"{MEDICOS_URL}/{medico_id}")


def obtener_horario(medico_id: int) -> list[str]:
    return _get(f"{MEDICOS_URL}/{medico_id}/horario") or []
