"""Endpoints del flujo de compra, cancelación y validación de QR."""

import secrets
from datetime import datetime, timedelta
from flask import Blueprint, g, Response
from ..http_utils import respuesta_json, obtener_body_json
from ..security import requiere_autenticacion
from ..errors import RecursoNoEncontrado, PeticionInvalida, Conflicto, AccesoProhibido
from ..repos import compras_repo, funciones_repo, servicios_repo
from ..qr_utils import generar_qr_bytes

compras_bp = Blueprint("compras", __name__)


@compras_bp.route("/compras", methods=["POST"])
@requiere_autenticacion(roles_permitidos=["cliente", "administrador"])
def realizar_compra():
    """Registra una nueva compra con pago simulado (S1, S2, S3, S16, S17)."""
    usuario_id = g.usuario_actual["usuario_id"]
    datos = obtener_body_json(campos_requeridos=["funcion_id", "butacas"])

    funcion_id = datos["funcion_id"]
    butacas_solicitadas = datos["butacas"]
    servicios_solicitados = datos.get("servicios", [])

    if not isinstance(butacas_solicitadas, list) or len(butacas_solicitadas) == 0:
        raise PeticionInvalida("Debe seleccionar al menos una butaca")

    if len(butacas_solicitadas) > 6:
        raise PeticionInvalida("Una compra admite como máximo 6 entradas (S3)")

    funcion = funciones_repo.buscar_por_id(funcion_id)
    if not funcion or not funcion["activa"]:
        raise RecursoNoEncontrado("Función no encontrada o no disponible")

    # Calculamos el total de entradas
    precio_unitario_entrada = float(funcion["precio"])
    total_entradas = precio_unitario_entrada * len(butacas_solicitadas)

    butacas_preparadas = []
    for b in butacas_solicitadas:
        if "fila" not in b or "columna" not in b:
            raise PeticionInvalida("Cada butaca debe especificar 'fila' y 'columna'")
        butacas_preparadas.append({
            "fila": int(b["fila"]),
            "columna": int(b["columna"]),
            "precio": precio_unitario_entrada
        })

    # Calculamos el total de servicios opcionales (S5)
    total_servicios = 0.0
    servicios_preparados = []
    for s in servicios_solicitados:
        s_id = s.get("servicio_id")
        cantidad = int(s.get("cantidad", 1))
        if cantidad <= 0:
            continue
        servicio_db = servicios_repo.buscar_por_id(s_id)
        if not servicio_db or not servicio_db["activo"]:
            raise PeticionInvalida(f"El servicio {s_id} no está disponible")

        precio_unitario = float(servicio_db["precio"])
        total_servicios += precio_unitario * cantidad
        servicios_preparados.append({
            "servicio_id": s_id,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario
        })

    total_general = total_entradas + total_servicios
    qr_token = secrets.token_urlsafe(32)  # Token aleatorio de un solo uso (S17)

    compra_id = compras_repo.registrar_compra_completa(
        usuario_id=usuario_id,
        funcion_id=funcion_id,
        total=total_general,
        qr_token=qr_token,
        butacas=butacas_preparadas,
        servicios=servicios_preparados
    )

    return respuesta_json(
        datos={
            "compra_id": compra_id,
            "qr_token": qr_token,
            "total": total_general,
            "estado": "activa"
        },
        mensaje="Compra realizada con éxito",
        status=201
    )


@compras_bp.route("/compras/<int:compra_id>", methods=["GET"])
@requiere_autenticacion()
def ver_compra(compra_id: int):
    """Obtiene los detalles de una compra, sus entradas y sus servicios."""
    compra = compras_repo.buscar_compra_por_id(compra_id)
    if not compra:
        raise RecursoNoEncontrado("Compra no encontrada")

    # Un cliente solo puede ver sus propias compras; los administradores pueden ver todas
    usuario_actual = g.usuario_actual
    if usuario_actual["rol"] != "administrador" and compra["usuario_id"] != usuario_actual["usuario_id"]:
        raise AccesoProhibido("No tienes permiso para ver esta compra")

    entradas = compras_repo.listar_entradas_de_compra(compra_id)
    servicios = compras_repo.listar_servicios_de_compra(compra_id)
    compra["entradas"] = entradas
    compra["servicios"] = servicios

    return respuesta_json(datos=compra)


@compras_bp.route("/compras/<int:compra_id>/cancelacion", methods=["POST"])
@requiere_autenticacion()
def cancelar_compra_endpoint(compra_id: int):
    """Cancela una compra completa liberando las butacas si es hasta 2hs antes (S13, S14)."""
    compra = compras_repo.buscar_compra_por_id(compra_id)
    if not compra:
        raise RecursoNoEncontrado("Compra no encontrada")

    usuario_actual = g.usuario_actual
    if usuario_actual["rol"] != "administrador" and compra["usuario_id"] != usuario_actual["usuario_id"]:
        raise AccesoProhibido("No tienes permiso para cancelar esta compra")

    if compra["estado"] != "activa":
        raise Conflicto(f"La compra no se puede cancelar porque ya está {compra['estado']}")

    inicio_funcion = compra["funcion_inicio"]
    ahora = datetime.now()
    if ahora > (inicio_funcion - timedelta(hours=2)):
        raise Conflicto("Solo se permite cancelar hasta 2 horas antes de la función (S13)")

    compras_repo.cancelar_compra(compra_id)

    return respuesta_json(mensaje="Compra cancelada con éxito. Las butacas han sido liberadas.")


@compras_bp.route("/compras/validar-qr", methods=["POST"])
@requiere_autenticacion(roles_permitidos=["administrador"])
def validar_qr_endpoint():
    """Valida y quema el QR de una compra al ingresar a la sala (S17, S18, S19)."""
    datos = obtener_body_json(campos_requeridos=["qr_token"])
    qr_token = datos["qr_token"].strip()

    compra = compras_repo.buscar_compra_por_token_qr(qr_token)
    if not compra:
        raise RecursoNoEncontrado("Código QR inválido o no reconocido")

    if compra["estado"] == "cancelada":
        raise Conflicto("El código QR corresponde a una compra cancelada")

    if compra["estado"] == "usada":
        raise Conflicto("El código QR ya fue utilizado anteriormente")

    # Ventana de validación: desde 60 min antes hasta 30 min después del inicio (S19)
    inicio_funcion = compra["funcion_inicio"]
    ahora = datetime.now()
    inicio_ventana = inicio_funcion - timedelta(minutes=60)
    fin_ventana = inicio_funcion + timedelta(minutes=30)

    if ahora < inicio_ventana:
        raise Conflicto("Aún no se puede validar el QR: la ventana abre 60 minutos antes de la función")
    if ahora > fin_ventana:
        raise Conflicto("La ventana de validación del QR expiró (hasta 30 minutos después del inicio)")

    compras_repo.marcar_qr_usado(compra["id"])

    return respuesta_json(
        datos={
            "compra_id": compra["id"],
            "pelicula": compra["pelicula_titulo"],
            "sala": compra["sala_nombre"],
            "local": compra["local_nombre"],
            "cliente": compra["usuario_nombre"],
            "estado": "usada"
        },
        mensaje="Ingreso validado correctamente. QR quemado."
    )


@compras_bp.route("/compras/<int:compra_id>/qr", methods=["GET"])
def descargar_qr_imagen(compra_id: int):
    """Devuelve la imagen PNG del código QR generada localmente en Python (Endpoint #33)."""
    compra = compras_repo.buscar_compra_por_id(compra_id)
    if not compra:
        raise RecursoNoEncontrado("Compra no encontrada")

    png_bytes = generar_qr_bytes(compra["qr_token"])
    return Response(png_bytes, mimetype="image/png")

