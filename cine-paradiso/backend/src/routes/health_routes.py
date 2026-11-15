"""Rutas de verificación de estado y conectividad."""

from flask import Blueprint
from ..http_utils import respuesta_json
from ..db import obtener_uno

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """Verifica el estado del backend y la conexión con MySQL."""
    try:
        resultado = obtener_uno("SELECT 1 AS ok, NOW() AS ahora")
        return respuesta_json(
            datos={
                "status": "online",
                "database": "conectada" if resultado else "desconocida",
                "timestamp": resultado["ahora"] if resultado else None
            },
            mensaje="Backend de Cine Paradiso funcionando correctamente"
        )
    except Exception as e:
        return respuesta_json(
            datos={
                "status": "degraded",
                "database": f"error: {str(e)}"
            },
            mensaje="Backend activo pero sin conexión a la base de datos",
            status=500
        )
