"""Repositorio de compras y entradas con transacciones seguras en SQL puro."""

from ..db import obtener_todos, obtener_uno, transaccion


def buscar_compra_por_id(compra_id: int):
    """Devuelve los datos de una compra por su ID."""
    sql = """
        SELECT
            c.id, c.usuario_id, c.funcion_id, c.fecha, c.total,
            c.estado, c.qr_token, c.fecha_cancelacion, c.fecha_validacion,
            u.nombre AS usuario_nombre, u.email AS usuario_email,
            p.titulo AS pelicula_titulo, f.inicio AS funcion_inicio,
            s.nombre AS sala_nombre, l.nombre AS local_nombre
        FROM compras c
        JOIN usuarios u ON u.id = c.usuario_id
        JOIN funciones f ON f.id = c.funcion_id
        JOIN peliculas p ON p.id = f.pelicula_id
        JOIN salas s ON s.id = f.sala_id
        JOIN locales l ON l.id = s.local_id
        WHERE c.id = %s
    """
    return obtener_uno(sql, (compra_id,))


def buscar_compra_por_token_qr(qr_token: str):
    """Busca una compra a partir de su token único codificado en el código QR."""
    sql = """
        SELECT
            c.id, c.usuario_id, c.funcion_id, c.fecha, c.total,
            c.estado, c.qr_token, c.fecha_cancelacion, c.fecha_validacion,
            u.nombre AS usuario_nombre, u.email AS usuario_email,
            p.titulo AS pelicula_titulo, f.inicio AS funcion_inicio,
            s.nombre AS sala_nombre, l.nombre AS local_nombre
        FROM compras c
        JOIN usuarios u ON u.id = c.usuario_id
        JOIN funciones f ON f.id = c.funcion_id
        JOIN peliculas p ON p.id = f.pelicula_id
        JOIN salas s ON s.id = f.sala_id
        JOIN locales l ON l.id = s.local_id
        WHERE c.qr_token = %s
    """
    return obtener_uno(sql, (qr_token,))


def listar_entradas_de_compra(compra_id: int):
    """Obtiene las butacas compradas en una orden."""
    sql = """
        SELECT id, funcion_id, fila, columna, precio, cancelada
        FROM entradas
        WHERE compra_id = %s
    """
    return obtener_todos(sql, (compra_id,))


def listar_servicios_de_compra(compra_id: int):
    """Obtiene los servicios contratados en una orden."""
    sql = """
        SELECT cs.servicio_id, s.nombre, cs.cantidad, cs.precio_unitario
        FROM compra_servicios cs
        JOIN servicios s ON s.id = cs.servicio_id
        WHERE cs.compra_id = %s
    """
    return obtener_todos(sql, (compra_id,))


def registrar_compra_completa(usuario_id, funcion_id, total, qr_token, butacas, servicios):
    """
    Registra de forma atómica la compra, sus entradas y servicios asociados.
    Si alguna butaca ya estuviera ocupada, el trigger de MySQL aborta la transacción.
    """
    with transaccion() as cursor:
        # 1. Insertar compra principal
        cursor.execute(
            """
            INSERT INTO compras (usuario_id, funcion_id, total, estado, qr_token)
            VALUES (%s, %s, %s, 'activa', %s)
            """,
            (usuario_id, funcion_id, total, qr_token)
        )
        compra_id = cursor.lastrowid

        # 2. Insertar entradas (butacas)
        for b in butacas:
            cursor.execute(
                """
                INSERT INTO entradas (compra_id, funcion_id, fila, columna, precio)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (compra_id, funcion_id, b["fila"], b["columna"], b["precio"])
            )

        # 3. Insertar servicios adicionales
        for s in servicios:
            cursor.execute(
                """
                INSERT INTO compra_servicios (compra_id, servicio_id, cantidad, precio_unitario)
                VALUES (%s, %s, %s, %s)
                """,
                (compra_id, s["servicio_id"], s["cantidad"], s["precio_unitario"])
            )

        return compra_id


def cancelar_compra(compra_id: int):
    """Marca la compra como cancelada (lo que dispara el trigger que libera las butacas)."""
    with transaccion() as cursor:
        cursor.execute(
            """
            UPDATE compras
            SET estado = 'cancelada', fecha_cancelacion = NOW()
            WHERE id = %s AND estado = 'activa'
            """,
            (compra_id,)
        )
        return cursor.rowcount > 0


def marcar_qr_usado(compra_id: int):
    """Marca la compra como usada al ingresar a la sala tras validar el QR."""
    with transaccion() as cursor:
        cursor.execute(
            """
            UPDATE compras
            SET estado = 'usada', fecha_validacion = NOW()
            WHERE id = %s AND estado = 'activa'
            """,
            (compra_id,)
        )
        return cursor.rowcount > 0


def listar_compras_de_usuario(usuario_id: int):
    """Devuelve todas las compras realizadas por un cliente ordenadas cronológicamente."""
    sql = """
        SELECT
            c.id, c.fecha, c.total, c.estado, c.qr_token,
            p.id AS pelicula_id, p.titulo AS pelicula_titulo, p.poster_url,
            f.inicio AS funcion_inicio,
            s.nombre AS sala_nombre,
            l.nombre AS local_nombre
        FROM compras c
        JOIN funciones f ON f.id = c.funcion_id
        JOIN peliculas p ON p.id = f.pelicula_id
        JOIN salas s ON s.id = f.sala_id
        JOIN locales l ON l.id = s.local_id
        WHERE c.usuario_id = %s
        ORDER BY c.fecha DESC
    """
    return obtener_todos(sql, (usuario_id,))


def listar_peliculas_vistas_de_usuario(usuario_id: int):
    """Devuelve las películas que el cliente efectivamente vio (compras con estado 'usada', S22)."""
    sql = """
        SELECT DISTINCT
            p.id AS pelicula_id,
            p.titulo,
            p.poster_url,
            p.duracion_min,
            p.clasificacion,
            MAX(c.fecha_validacion) AS fecha_vista
        FROM compras c
        JOIN funciones f ON f.id = c.funcion_id
        JOIN peliculas p ON p.id = f.pelicula_id
        WHERE c.usuario_id = %s
          AND c.estado = 'usada'
        GROUP BY p.id, p.titulo, p.poster_url, p.duracion_min, p.clasificacion
        ORDER BY fecha_vista DESC
    """
    return obtener_todos(sql, (usuario_id,))

