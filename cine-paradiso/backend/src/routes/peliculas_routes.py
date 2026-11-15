"""Endpoints de cartelera y películas."""

from flask import Blueprint
from ..http_utils import respuesta_json
from ..errors import RecursoNoEncontrado
from ..repos import peliculas_repo, funciones_repo

peliculas_bp = Blueprint("peliculas", __name__)


@peliculas_bp.route("/cartelera", methods=["GET"])
def obtener_cartelera():
    """Devuelve las películas vigentes en cartelera."""
    peliculas = peliculas_repo.listar_cartelera_vigente()
    return respuesta_json(datos=peliculas)


@peliculas_bp.route("/peliculas/<int:pelicula_id>", methods=["GET"])
def obtener_pelicula(pelicula_id: int):
    """Obtiene el detalle completo de una película."""
    pelicula = peliculas_repo.buscar_por_id(pelicula_id)
    if not pelicula or not pelicula["activa"]:
        raise RecursoNoEncontrado("Película no encontrada o inactiva")

    funciones = funciones_repo.listar_por_pelicula(pelicula_id)
    pelicula["funciones"] = funciones

    return respuesta_json(datos=pelicula)
