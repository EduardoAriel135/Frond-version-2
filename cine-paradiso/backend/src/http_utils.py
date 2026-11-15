"""Utilidades auxiliares para controladores HTTP y respuestas JSON."""

from datetime import datetime, date
from decimal import Decimal
from flask import jsonify, request

from .errors import PeticionInvalida


def formatear_valor(valor):
    """Convierte tipos especiales como Decimal, datetime y date a formato serializable en JSON."""
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


def serializar_entidad(entidad: dict) -> dict:
    """Convierte todos los valores de un registro a formatos JSON estándar."""
    if not entidad:
        return entidad
    return {clave: formatear_valor(valor) for clave, valor in entidad.items()}


def serializar_lista(lista: list) -> list:
    """Convierte una lista de registros para JSON."""
    return [serializar_entidad(item) for item in lista]


def respuesta_json(datos=None, mensaje=None, status=200):
    """Genera una respuesta JSON consistente en toda la API."""
    cuerpo = {}
    if mensaje is not None:
        cuerpo["mensaje"] = mensaje
    if datos is not None:
        if isinstance(datos, list):
            cuerpo["datos"] = serializar_lista(datos)
            cuerpo["total"] = len(datos)
        elif isinstance(datos, dict):
            cuerpo["datos"] = serializar_entidad(datos)
        else:
            cuerpo["datos"] = datos

    return jsonify(cuerpo), status


def obtener_body_json(campos_requeridos=None) -> dict:
    """Obtiene y valida el JSON enviado en el body de la petición."""
    if not request.is_json:
        raise PeticionInvalida("La petición debe tener Content-Type: application/json")

    datos = request.get_json(silent=True)
    if datos is None:
        raise PeticionInvalida("El cuerpo de la petición contiene un JSON inválido o está vacío")

    if campos_requeridos:
        faltantes = [campo for campo in campos_requeridos if campo not in datos or datos[campo] is None]
        if faltantes:
            raise PeticionInvalida(f"Faltan campos obligatorios: {', '.join(faltantes)}")

    return datos
