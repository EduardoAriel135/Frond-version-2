"""Repositorio de servicios adicionales (comida, bebidas, estacionamiento, VIP)."""

from ..db import obtener_todos, obtener_uno, ejecutar_consulta


def listar_activos():
    """Devuelve los servicios opcionales activos disponibles para la compra."""
    sql = "SELECT id, nombre, descripcion, precio FROM servicios WHERE activo = 1 ORDER BY nombre ASC"
    return obtener_todos(sql)


def buscar_por_id(servicio_id: int):
    """Busca un servicio por su ID."""
    sql = "SELECT id, nombre, descripcion, precio, activo FROM servicios WHERE id = %s"
    return obtener_uno(sql, (servicio_id,))


def crear_servicio(nombre: str, descripcion: str, precio: float):
    """Crea un nuevo servicio en el catálogo."""
    sql = "INSERT INTO servicios (nombre, descripcion, precio, activo) VALUES (%s, %s, %s, 1)"
    return ejecutar_consulta(sql, (nombre, descripcion, precio))


def listar_todos():
    """Devuelve todos los servicios (activos e inactivos) para el panel de administración."""
    sql = "SELECT id, nombre, descripcion, precio, activo FROM servicios ORDER BY id ASC"
    return obtener_todos(sql)


def actualizar_servicio(servicio_id: int, nombre: str, descripcion: str, precio: float, activo: int):
    """Actualiza los datos y estado de un servicio."""
    sql = """
        UPDATE servicios
        SET nombre = %s, descripcion = %s, precio = %s, activo = %s
        WHERE id = %s
    """
    return ejecutar_consulta(sql, (nombre, descripcion, precio, activo, servicio_id))


def cambiar_estado(servicio_id: int, activo: int):
    """Baja o reactivación lógica de un servicio (S5)."""
    sql = "UPDATE servicios SET activo = %s WHERE id = %s"
    return ejecutar_consulta(sql, (activo, servicio_id))

