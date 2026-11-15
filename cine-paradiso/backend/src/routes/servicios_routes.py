"""Endpoints para consulta y administración de servicios adicionales."""

from flask import Blueprint
from ..http_utils import respuesta_json
from ..repos import servicios_repo

servicios_bp = Blueprint("servicios", __name__)


@servicios_bp.route("/servicios", methods=["GET"])
def listar_servicios():
    """Devuelve la lista de servicios activos para la compra opcional."""
    servicios = servicios_repo.listar_activos()
    return respuesta_json(datos=servicios)
