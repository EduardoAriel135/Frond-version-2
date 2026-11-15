"""Manejo centralizado de errores y excepciones HTTP para la API."""

from flask import jsonify


class ApiError(Exception):
    """Excepción base para errores de la API."""
    codigo_estado = 500
    mensaje_predeterminado = "Error interno del servidor"

    def __init__(self, mensaje=None, detalles=None):
        super().__init__(mensaje or self.mensaje_predeterminado)
        self.mensaje = mensaje or self.mensaje_predeterminado
        self.detalles = detalles or []

    def a_diccionario(self):
        resultado = {
            "error": self.__class__.__name__,
            "mensaje": self.mensaje,
            "status": self.codigo_estado
        }
        if self.detalles:
            resultado["detalles"] = self.detalles
        return resultado


class PeticionInvalida(ApiError):
    """Error 400: Datos de entrada faltantes, incorrectos o mal formateados."""
    codigo_estado = 400
    mensaje_predeterminado = "Solicitud inválida"


class NoAutorizado(ApiError):
    """Error 401: Faltan credenciales o el token es inválido/expirado."""
    codigo_estado = 401
    mensaje_predeterminado = "Credenciales inválidas o no suministradas"


class AccesoProhibido(ApiError):
    """Error 403: El usuario autenticado no tiene permisos para esta acción."""
    codigo_estado = 403
    mensaje_predeterminado = "No tienes permiso para acceder a este recurso"


class RecursoNoEncontrado(ApiError):
    """Error 404: El recurso solicitado no existe."""
    codigo_estado = 404
    mensaje_predeterminado = "Recurso no encontrado"


class Conflicto(ApiError):
    """Error 409: Conflicto con el estado actual (ej: butaca ya ocupada o superposición)."""
    codigo_estado = 409
    mensaje_predeterminado = "Conflicto con el estado actual del recurso"


def registrar_manejadores_error(app):
    """Registra manejadores de error para que la API siempre responda en JSON."""

    @app.errorhandler(ApiError)
    def manejar_api_error(error):
        return jsonify(error.a_diccionario()), error.codigo_estado

    @app.errorhandler(400)
    def manejar_400(error):
        return jsonify({"error": "PeticionInvalida", "mensaje": str(error), "status": 400}), 400

    @app.errorhandler(404)
    def manejar_404(error):
        return jsonify({"error": "RecursoNoEncontrado", "mensaje": "Ruta no encontrada", "status": 404}), 404

    @app.errorhandler(405)
    def manejar_405(error):
        return jsonify({"error": "MetodoNoPermitido", "mensaje": "Método HTTP no permitido para esta ruta", "status": 405}), 405

    @app.errorhandler(500)
    def manejar_500(error):
        return jsonify({"error": "ErrorInterno", "mensaje": "Ocurrió un error inesperado en el servidor", "status": 500}), 500
