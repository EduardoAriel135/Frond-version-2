"""Gestión de conexiones a MySQL mediante sentencias SQL explícitas (sin ORM)."""

from contextlib import contextmanager
import pymysql
import pymysql.cursors
from flask import g

from .config import Config
from .errors import ApiError, Conflicto, PeticionInvalida


def crear_conexion():
    """Crea y devuelve una nueva conexión a MySQL usando PyMySQL."""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )


def obtener_db():
    """Obtiene o reutiliza la conexión a la base de datos asociada a la petición actual."""
    if "db" not in g:
        try:
            g.db = crear_conexion()
        except pymysql.MySQLError as e:
            raise ApiError(f"No se pudo conectar a la base de datos MySQL: {str(e)}")
    return g.db


def cerrar_db(error=None):
    """Cierra la conexión al finalizar el ciclo de vida de la petición de Flask."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def transaccion():
    """Context manager para ejecutar operaciones SQL dentro de una transacción segura."""
    conexion = obtener_db()
    try:
        with conexion.cursor() as cursor:
            yield cursor
        conexion.commit()
    except pymysql.err.IntegrityError as e:
        conexion.rollback()
        codigo_error, mensaje = e.args
        # 1062: Duplicate entry (clave primaria o índice único duplicado)
        if codigo_error == 1062:
            raise Conflicto(f"Registro duplicado: {mensaje}")
        # 1644: Error disparado por SIGNAL SQLSTATE '45000' en triggers/stored procedures
        if codigo_error == 1644:
            raise Conflicto(mensaje)
        raise PeticionInvalida(f"Violación de integridad en base de datos: {mensaje}")
    except pymysql.err.OperationalError as e:
        conexion.rollback()
        codigo_error, mensaje = e.args
        if codigo_error == 1644:
            raise Conflicto(mensaje)
        raise ApiError(f"Error operativo en base de datos: {mensaje}")
    except Exception:
        conexion.rollback()
        raise


def ejecutar_consulta(sql, params=None):
    """Ejecuta una sentencia de inserción, actualización o eliminación (INSERT/UPDATE/DELETE)."""
    with transaccion() as cursor:
        cursor.execute(sql, params or ())
        return cursor.lastrowid


def obtener_uno(sql, params=None):
    """Ejecuta una consulta SELECT y devuelve una única fila (como diccionario) o None."""
    conexion = obtener_db()
    with conexion.cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchone()


def obtener_todos(sql, params=None):
    """Ejecuta una consulta SELECT y devuelve una lista de filas (diccionarios)."""
    conexion = obtener_db()
    with conexion.cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchall()
