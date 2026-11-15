"""Consultas SQL puras para estadísticas y dashboards del Backoffice (S1, S10, S22)."""

from ..db import obtener_todos, obtener_uno


def ocupacion_por_pelicula():
    """Calcula la ocupación promedio y total de butacas vendidas por película."""
    sql = """
        SELECT
            p.id,
            p.titulo,
            COUNT(DISTINCT f.id) AS total_funciones,
            COUNT(e.id) AS butacas_vendidas,
            COALESCE(SUM(e.precio), 0) AS recaudacion_entradas
        FROM peliculas p
        LEFT JOIN funciones f ON f.pelicula_id = p.id
        LEFT JOIN entradas e ON e.funcion_id = f.id AND e.cancelada = 0
        WHERE p.activa = 1
        GROUP BY p.id, p.titulo
        ORDER BY butacas_vendidas DESC
    """
    return obtener_todos(sql)


def ventas_por_genero():
    """Agrupa la recaudación y entradas vendidas por género cinematográfico."""
    sql = """
        SELECT
            g.id,
            g.nombre AS genero,
            COUNT(e.id) AS entradas_vendidas,
            COALESCE(SUM(e.precio), 0) AS total_recaudado
        FROM generos g
        JOIN pelicula_genero pg ON pg.genero_id = g.id
        JOIN peliculas p ON p.id = pg.pelicula_id
        JOIN funciones f ON f.pelicula_id = p.id
        LEFT JOIN entradas e ON e.funcion_id = f.id AND e.cancelada = 0
        GROUP BY g.id, g.nombre
        ORDER BY total_recaudado DESC
    """
    return obtener_todos(sql)


def resumen_cancelaciones():
    """Métricas de compras canceladas versus confirmadas/usadas."""
    sql = """
        SELECT
            estado,
            COUNT(*) AS cantidad,
            COALESCE(SUM(total), 0) AS monto_total
        FROM compras
        GROUP BY estado
    """
    return obtener_todos(sql)


def franjas_horarias_mas_vendidas():
    """Analiza la cantidad de entradas vendidas según la hora de inicio de la función."""
    sql = """
        SELECT
            HOUR(f.inicio) AS hora,
            COUNT(e.id) AS cantidad_entradas
        FROM funciones f
        JOIN entradas e ON e.funcion_id = f.id AND e.cancelada = 0
        GROUP BY HOUR(f.inicio)
        ORDER BY cantidad_entradas DESC
    """
    return obtener_todos(sql)
