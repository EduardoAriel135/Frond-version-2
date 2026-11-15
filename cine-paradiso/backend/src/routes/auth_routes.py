"""Endpoints de autenticación y registro de usuarios."""

from flask import Blueprint, g
from ..http_utils import respuesta_json, obtener_body_json
from ..security import hashear_password, verificar_password, generar_token, requiere_autenticacion
from ..errors import NoAutorizado, Conflicto, PeticionInvalida
from ..repos import usuarios_repo, compras_repo

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/registro", methods=["POST"])
def registro():
    """Registra un nuevo cliente en el sistema (S20)."""
    datos = obtener_body_json(campos_requeridos=["nombre", "email", "password"])

    nombre = datos["nombre"].strip()
    email = datos["email"].strip().lower()
    password = datos["password"]

    if len(password) < 6:
        raise PeticionInvalida("La contraseña debe tener al menos 6 caracteres")

    existente = usuarios_repo.buscar_por_email(email)
    if existente:
        raise Conflicto("Ya existe un usuario registrado con ese correo electrónico")

    password_hash = hashear_password(password)
    usuario_id = usuarios_repo.crear_usuario(nombre, email, password_hash, rol="cliente")
    token = generar_token(usuario_id, email, rol="cliente")

    return respuesta_json(
        datos={
            "token": token,
            "usuario": {
                "id": usuario_id,
                "nombre": nombre,
                "email": email,
                "rol": "cliente"
            }
        },
        mensaje="Usuario registrado exitosamente",
        status=201
    )


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Inicia sesión y genera un token Bearer (S20, S21)."""
    datos = obtener_body_json(campos_requeridos=["email", "password"])

    email = datos["email"].strip().lower()
    password = datos["password"]

    usuario = usuarios_repo.buscar_por_email(email)
    if not usuario or not verificar_password(password, usuario["password_hash"]):
        raise NoAutorizado("Correo electrónico o contraseña incorrectos")

    token = generar_token(usuario["id"], usuario["email"], usuario["rol"])

    return respuesta_json(
        datos={
            "token": token,
            "usuario": {
                "id": usuario["id"],
                "nombre": usuario["nombre"],
                "email": usuario["email"],
                "rol": usuario["rol"]
            }
        },
        mensaje="Inicio de sesión exitoso"
    )


@auth_bp.route("/usuarios/me", methods=["GET"])
@requiere_autenticacion()
def obtener_perfil():
    """Obtiene los datos del usuario autenticado actual."""
    usuario_id = g.usuario_actual["usuario_id"]
    usuario = usuarios_repo.buscar_por_id(usuario_id)
    if not usuario:
        raise NoAutorizado("Usuario no encontrado")

    return respuesta_json(datos=usuario)


@auth_bp.route("/usuarios/me/historial", methods=["GET"])
@requiere_autenticacion()
def obtener_historial_usuario():
    """Obtiene el historial de compras y películas vistas del cliente (S22)."""
    usuario_id = g.usuario_actual["usuario_id"]

    compras_raw = compras_repo.listar_compras_de_usuario(usuario_id)
    compras = []
    for c in compras_raw:
        entradas_db = compras_repo.listar_entradas_de_compra(c["id"])
        servicios_db = compras_repo.listar_servicios_de_compra(c["id"])

        butacas = [f"{chr(64 + e['fila'])}{e['columna']}" for e in entradas_db]
        servicios = [{"nombre": s["nombre"], "cantidad": s["cantidad"]} for s in servicios_db]

        compras.append({
            "id": c["id"],
            "fecha": c["fecha"],
            "estado": c["estado"],
            "pelicula": c["pelicula_titulo"],
            "local": c["local_nombre"],
            "sala": c["sala_nombre"],
            "inicio": c["funcion_inicio"],
            "butacas": butacas,
            "servicios": servicios,
            "total": float(c["total"]),
            "qr_token": c["qr_token"]
        })

    peliculas_vistas = compras_repo.listar_peliculas_vistas_de_usuario(usuario_id)

    return respuesta_json(datos={
        "compras": compras,
        "peliculas_vistas": peliculas_vistas
    })

