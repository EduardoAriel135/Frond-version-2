"""Repositorio de funciones con sentencias SQL explícitas."""

from ..db import obtener_todos, obtener_uno, ejecutar_consulta


def listar_por_pelicula(pelicula_id: int):
    """Devuelve las funciones futuras activas para una película determinada."""
    sql = """
        SELECT
            f.id, f.pelicula_id, f.sala_id, f.inicio, f.precio,
            s.nombre AS sala_nombre, s.capacidad AS sala_capacidad,
            l.id AS local_id, l.nombre AS local_nombre
        FROM funciones f
        JOIN salas s ON s.id = f.sala_id
        JOIN locales l ON l.id = s.local_id
        WHERE f.pelicula_id = %s
          AND f.activa = 1
          AND f.inicio > NOW()
        ORDER BY f.inicio ASC
    """
    return obtener_todos(sql, (pelicula_id,))


def buscar_por_id(funcion_id: int):
    """Obtiene los detalles de una función puntual."""
    sql = """
        SELECT
            f.id, f.pelicula_id, f.sala_id, f.inicio, f.precio, f.activa,
            p.titulo AS pelicula_titulo, p.duracion_min,
            s.nombre AS sala_nombre, s.filas, s.columnas, s.capacidad,
            l.id AS local_id, l.nombre AS local_nombre
        FROM funciones f
        JOIN peliculas p ON p.id = f.pelicula_id
        JOIN salas s ON s.id = f.sala_id
        JOIN locales l ON l.id = s.local_id
        WHERE f.id = %s
    """
    return obtener_uno(sql, (funcion_id,))


def obtener_butacas_ocupadas(funcion_id: int):
    """Devuelve la lista de coordenadas de butacas ya vendidas y no canceladas para la función."""
    sql = """
        SELECT fila, columna
        FROM entradas
        WHERE funcion_id = %s
          AND cancelada = 0
    """
    return obtener_todos(sql, (funcion_id,))


def crear_funcion(pelicula_id: int, sala_id: int, inicio: str, precio: float):
    """Inserta una nueva función respetando el campo DATETIME."""
    sql = """
        INSERT INTO funciones (pelicula_id, sala_id, inicio, precio, activa)
        VALUES (%s, %s, %s, %s, 1)
    """
    return ejecutar_consulta(sql, (pelicula_id, sala_id, inicio, precio))
