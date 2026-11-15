"""Repositorio de películas con sentencias SQL explícitas."""

from ..db import obtener_todos, obtener_uno, ejecutar_consulta


def listar_cartelera_vigente():
    """Devuelve las películas vigentes activas con funciones disponibles."""
    sql = """
        SELECT DISTINCT
            p.id, p.tmdb_id, p.titulo, p.sinopsis, p.poster_url,
            p.duracion_min, p.clasificacion, p.vigente_desde, p.vigente_hasta
        FROM peliculas p
        JOIN funciones f ON f.pelicula_id = p.id
        WHERE p.activa = 1
          AND f.activa = 1
          AND f.inicio > NOW()
          AND CURRENT_DATE() BETWEEN p.vigente_desde AND p.vigente_hasta
        ORDER BY p.titulo ASC
    """
    return obtener_todos(sql)


def buscar_por_id(pelicula_id: int):
    """Obtiene los detalles de una película específica por su ID."""
    sql = """
        SELECT
            id, tmdb_id, titulo, sinopsis, poster_url,
            duracion_min, clasificacion, vigente_desde, vigente_hasta, activa
        FROM peliculas
        WHERE id = %s
    """
    return obtener_uno(sql, (pelicula_id,))


def crear_pelicula(tmdb_id, titulo, sinopsis, poster_url, duracion_min, clasificacion, vigente_desde, vigente_hasta):
    """Registra una nueva película en el catálogo."""
    sql = """
        INSERT INTO peliculas (
            tmdb_id, titulo, sinopsis, poster_url,
            duracion_min, clasificacion, vigente_desde, vigente_hasta, activa
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
    """
    return ejecutar_consulta(
        sql,
        (tmdb_id, titulo, sinopsis, poster_url, duracion_min, clasificacion, vigente_desde, vigente_hasta)
    )
