"""Seguridad, hashing de contraseñas y validación de tokens de autenticación."""

import functools
from flask import request, g
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from .config import Config
from .errors import NoAutorizado, AccesoProhibido

_serializador = URLSafeTimedSerializer(Config.SECRET_KEY)


def hashear_password(password: str) -> str:
    """Genera un hash seguro para la contraseña del usuario (scrypt o pbkdf2)."""
    return generate_password_hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    """Compara una contraseña en texto plano contra su hash almacenado."""
    return check_password_hash(password_hash, password)


def generar_token(usuario_id: int, email: str, rol: str) -> str:
    """Genera un token de autenticación firmado y seguro."""
    datos = {
        "usuario_id": usuario_id,
        "email": email,
        "rol": rol
    }
    return _serializador.dumps(datos, salt="auth-token")


def decodificar_token(token: str) -> dict:
    """Valida y decodifica un token de autenticación."""
    try:
        max_age = Config.EXPIRACION_TOKEN_HORAS * 3600
        return _serializador.loads(token, salt="auth-token", max_age=max_age)
    except SignatureExpired:
        raise NoAutorizado("La sesión ha expirado. Por favor ingresa nuevamente.")
    except BadSignature:
        raise NoAutorizado("Token de autenticación inválido o alterado.")


def requiere_autenticacion(roles_permitidos=None):
    """
    Decorador para proteger endpoints de la API.
    roles_permitidos: Lista opcional con roles autorizados, ej: ['administrador']
    """
    def decorador(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            header_autorizacion = request.headers.get("Authorization", "")
            if not header_autorizacion.startswith("Bearer "):
                raise NoAutorizado("Se requiere encabezado Authorization: Bearer <token>")

            token = header_autorizacion.split(" ", 1)[1].strip()
            datos_usuario = decodificar_token(token)

            # Si se especificaron roles permitidos, verificamos el rol del usuario
            if roles_permitidos and datos_usuario.get("rol") not in roles_permitidos:
                raise AccesoProhibido("No posees los permisos necesarios para realizar esta acción")

            # Inyectamos el usuario autenticado en el contexto global de Flask
            g.usuario_actual = datos_usuario
            return f(*args, **kwargs)
        return wrapper
    return decorador
