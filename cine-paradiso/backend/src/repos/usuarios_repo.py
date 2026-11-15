"""Repositorio de usuarios con sentencias SQL explícitas."""

from ..db import obtener_uno, ejecutar_consulta


def buscar_por_email(email: str):
    """Busca un usuario por su dirección de email."""
    sql = "SELECT id, nombre, email, password_hash, rol FROM usuarios WHERE email = %s"
    return obtener_uno(sql, (email,))


def buscar_por_id(usuario_id: int):
    """Busca un usuario por su ID primario."""
    sql = "SELECT id, nombre, email, rol FROM usuarios WHERE id = %s"
    return obtener_uno(sql, (usuario_id,))


def crear_usuario(nombre: str, email: str, password_hash: str, rol: str = "cliente") -> int:
    """Inserta un nuevo usuario y devuelve su ID generado."""
    sql = """
        INSERT INTO usuarios (nombre, email, password_hash, rol)
        VALUES (%s, %s, %s, %s)
    """
    return ejecutar_consulta(sql, (nombre, email, password_hash, rol))
