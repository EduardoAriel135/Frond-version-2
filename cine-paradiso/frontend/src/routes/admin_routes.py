"""Controlador de rutas del Backoffice de Administrador (renderizado Jinja2)."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..api_client import get, post, patch, ApiError

admin_bp = Blueprint("admin", __name__)


def _verificar_rol_admin():
    """Valida que el usuario tenga rol administrador."""
    usuario = session.get("usuario")
    if not usuario or usuario.get("rol") != "administrador":
        flash("Acceso restringido: requiere permisos de Administrador.", "danger")
        return False
    return True


@admin_bp.route("/admin/dashboard")
def dashboard():
    """Panel de control y métricas del cine (ocupación, ventas, cancelaciones)."""
    if not _verificar_rol_admin():
        return redirect(url_for("public.login"))

    estadisticas = {}
    try:
        resp = get("/admin/estadisticas")
        estadisticas = resp.get("datos", {})
    except ApiError as e:
        flash(f"Error al cargar métricas: {e.mensaje}", "warning")

    return render_template("admin/dashboard.html", stats=estadisticas)


@admin_bp.route("/admin/validar-qr", methods=["GET", "POST"])
def validar_qr():
    """Página de escaneo y validación de código QR en la entrada a la sala (S18, S19)."""
    if not _verificar_rol_admin():
        return redirect(url_for("public.login"))

    resultado_validacion = None

    if request.method == "POST":
        token = request.form.get("qr_token", "").strip()
        if not token:
            flash("Debe ingresar o escanear un código QR válido.", "warning")
        else:
            try:
                resp = post("/compras/validar-qr", json_data={"qr_token": token})
                resultado_validacion = resp.get("datos", {})
                flash("¡Ingreso validado con éxito! Pase habilitado.", "success")
            except ApiError as e:
                flash(f"Error de validación: {e.mensaje}", "danger")

    return render_template("admin/validar_qr.html", resultado=resultado_validacion)


@admin_bp.route("/admin/servicios", methods=["GET", "POST"])
def abm_servicios():
    """ABM de servicios adicionales (comida, bebidas, estacionamiento, VIP)."""
    if not _verificar_rol_admin():
        return redirect(url_for("public.login"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio_str = request.form.get("precio", "0")

        try:
            precio = float(precio_str)
            post("/admin/servicios", json_data={
                "nombre": nombre,
                "descripcion": descripcion,
                "precio": precio
            })
            flash(f"Servicio '{nombre}' agregado exitosamente.", "success")
        except ValueError:
            flash("El precio ingresado no es válido.", "danger")
        except ApiError as e:
            flash(e.mensaje, "danger")

        return redirect(url_for("admin.abm_servicios"))

    servicios = []
    try:
        resp = get("/admin/servicios")
        servicios = resp.get("datos", [])
    except ApiError as e:
        flash(e.mensaje, "danger")

    return render_template("admin/servicios.html", servicios=servicios)


@admin_bp.route("/admin/servicios/<int:servicio_id>/toggle", methods=["POST"])
def alternar_servicio(servicio_id: int):
    """Baja lógica o reactivación de un servicio."""
    if not _verificar_rol_admin():
        return redirect(url_for("public.login"))

    activo_actual = request.form.get("activo") == "1"
    nuevo_estado = not activo_actual

    try:
        patch(f"/admin/servicios/{servicio_id}/estado", json_data={"activo": nuevo_estado})
        accion = "activado" if nuevo_estado else "dado de baja"
        flash(f"Servicio {accion} correctamente.", "info")
    except ApiError as e:
        flash(e.mensaje, "danger")

    return redirect(url_for("admin.abm_servicios"))
