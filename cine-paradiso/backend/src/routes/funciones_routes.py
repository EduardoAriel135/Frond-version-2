"""Endpoints de funciones y disponibilidad de butacas."""

from flask import Blueprint
from ..http_utils import respuesta_json
from ..errors import RecursoNoEncontrado
from ..repos import funciones_repo

funciones_bp = Blueprint("funciones", __name__)


@funciones_bp.route("/funciones/<int:funcion_id>", methods=["GET"])
def obtener_funcion(funcion_id: int):
    """Obtiene los detalles de una función específica."""
    funcion = funciones_repo.buscar_por_id(funcion_id)
    if not funcion or not funcion["activa"]:
        raise RecursoNoEncontrado("Función no encontrada o inactiva")

    return respuesta_json(datos=funcion)


@funciones_bp.route("/funciones/<int:funcion_id>/butacas", methods=["GET"])
def obtener_butacas_funcion(funcion_id: int):
    """Devuelve las dimensiones de la sala y las butacas ocupadas para esta función."""
    funcion = funciones_repo.buscar_por_id(funcion_id)
    if not funcion or not funcion["activa"]:
        raise RecursoNoEncontrado("Función no encontrada o inactiva")

    ocupadas = funciones_repo.obtener_butacas_ocupadas(funcion_id)
    ocupadas_set = {(b["fila"], b["columna"]) for b in ocupadas}

    return respuesta_json(
        datos={
            "funcion_id": funcion["id"],
            "sala_id": funcion["sala_id"],
            "sala_nombre": funcion["sala_nombre"],
            "filas": funcion["filas"],
            "columnas": funcion["columnas"],
            "capacidad": funcion["capacidad"],
            "precio_unitario": funcion["precio"],
            "ocupadas": [{"fila": f, "columna": c} for f, c in ocupadas_set],
            "cantidad_ocupadas": len(ocupadas_set),
            "cantidad_disponibles": funcion["capacidad"] - len(ocupadas_set)
        }
    )
