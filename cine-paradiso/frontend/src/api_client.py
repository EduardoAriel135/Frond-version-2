"""Cliente HTTP para comunicación entre servidores (Frontend -> Backend vía requests).

Cumple estrictamente con la restricción de la cátedra:
Toda llamada al backend se realiza exclusivamente desde Python usando la librería `requests`.
El navegador nunca realiza peticiones directas (prohibido fetch/axios).
"""

import requests
from flask import session
from .config import Config


class ApiError(Exception):
    """Excepción para errores devueltos por el backend."""
    def __init__(self, mensaje, status_code=500, detalles=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status_code = status_code
        self.detalles = detalles or []


def _obtener_headers(token=None):
    """Construye las cabeceras HTTP incluyendo el token de sesión si existe."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    # Prioridad: token explícito, o token guardado en la sesión de Flask
    token_actual = token or session.get("auth_token")
    if token_actual:
        headers["Authorization"] = f"Bearer {token_actual}"
    return headers


def api_request(metodo: str, endpoint: str, params=None, json_data=None, token=None):
    """Ejecuta una petición HTTP contra la API REST del backend."""
    url = f"{Config.BACKEND_API_URL}/{endpoint.lstrip('/')}"
    headers = _obtener_headers(token)

    try:
        respuesta = requests.request(
            method=metodo.upper(),
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=8
        )

        datos = respuesta.json() if respuesta.content else {}

        if not respuesta.ok:
            mensaje = datos.get("mensaje") or datos.get("error") or f"Error del servidor ({respuesta.status_code})"
            raise ApiError(mensaje=mensaje, status_code=respuesta.status_code, detalles=datos.get("detalles"))

        return datos

    except requests.exceptions.ConnectionError:
        raise ApiError(
            mensaje="No se pudo establecer conexión con el Backend (¿está corriendo en el puerto 5000?)",
            status_code=503
        )
    except requests.exceptions.Timeout:
        raise ApiError(
            mensaje="El Backend demoró demasiado en responder (timeout)",
            status_code=504
        )
    except requests.exceptions.RequestException as e:
        raise ApiError(
            mensaje=f"Error en la comunicación con el Backend: {str(e)}",
            status_code=500
        )


def get(endpoint: str, params=None, token=None):
    """Helper para peticiones GET."""
    return api_request("GET", endpoint, params=params, token=token)


def post(endpoint: str, json_data=None, token=None):
    """Helper para peticiones POST."""
    return api_request("POST", endpoint, json_data=json_data, token=token)


def patch(endpoint: str, json_data=None, token=None):
    """Helper para peticiones PATCH."""
    return api_request("PATCH", endpoint, json_data=json_data, token=token)


def delete(endpoint: str, token=None):
    """Helper para peticiones DELETE."""
    return api_request("DELETE", endpoint, token=token)
