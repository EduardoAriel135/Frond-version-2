"""Rutas públicas y de clientes del frontend (renderizado con Jinja2)."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..api_client import get, post, ApiError

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    """Página de inicio: Cartelera de películas activas."""
    peliculas = []
    error_msg = None
    try:
        respuesta = get("/cartelera")
        peliculas = respuesta.get("datos", [])
    except ApiError as e:
        error_msg = e.mensaje

    return render_template("public/index.html", peliculas=peliculas, error_backend=error_msg)


@public_bp.route("/pelicula/<int:pelicula_id>")
def pelicula_detalle(pelicula_id: int):
    """Ficha detallada de la película y horarios de funciones."""
    try:
        respuesta = get(f"/peliculas/{pelicula_id}")
        pelicula = respuesta.get("datos", {})
        return render_template("public/pelicula.html", pelicula=pelicula)
    except ApiError as e:
        flash(e.mensaje, "danger")
        return redirect(url_for("public.index"))


@public_bp.route("/funcion/<int:funcion_id>/butacas", methods=["GET", "POST"])
def seleccionar_butacas(funcion_id: int):
    """Página de selección de butacas y servicios adicionales."""
    # Requiere que el usuario esté autenticado para comprar
    if "auth_token" not in session:
        flash("Por favor inicia sesión o regístrate para comprar tus entradas.", "info")
        return redirect(url_for("public.login", next=request.url))

    if request.method == "POST":
        # Procesa la compra enviada por el formulario HTML (sin fetch/axios)
        butacas_seleccionadas_raw = request.form.getlist("butacas")  # ej: ["3-5", "3-6"]
        if not butacas_seleccionadas_raw:
            flash("Debes seleccionar al menos una butaca.", "warning")
            return redirect(request.url)

        butacas = []
        for item in butacas_seleccionadas_raw:
            partes = item.split("-")
            if len(partes) == 2:
                butacas.append({"fila": int(partes[0]), "columna": int(partes[1])})

        # Recopilamos servicios seleccionados
        servicios = []
        for key in request.form:
            if key.startswith("servicio_"):
                s_id = int(key.replace("servicio_", ""))
                cantidad = int(request.form.get(key, 0))
                if cantidad > 0:
                    servicios.append({"servicio_id": s_id, "cantidad": cantidad})

        payload = {
            "funcion_id": funcion_id,
            "butacas": butacas,
            "servicios": servicios
        }

        try:
            resultado = post("/compras", json_data=payload)
            compra_id = resultado["datos"]["compra_id"]
            flash("¡Compra realizada con éxito! Tu código QR está listo.", "success")
            return redirect(url_for("public.ver_comprobante", compra_id=compra_id))
        except ApiError as e:
            flash(e.mensaje, "danger")
            return redirect(request.url)

    # GET: Cargar datos de la función y de la sala
    try:
        resp_butacas = get(f"/funciones/{funcion_id}/butacas")
        sala_info = resp_butacas.get("datos", {})

        resp_servicios = get("/servicios")
        servicios = resp_servicios.get("datos", [])

        # Para facilitar el renderizado en Jinja2, armamos una matriz de ocupación
        filas = sala_info.get("filas", 0)
        columnas = sala_info.get("columnas", 0)
        ocupadas = {(b["fila"], b["columna"]) for b in sala_info.get("ocupadas", [])}

        return render_template(
            "public/butacas.html",
            sala=sala_info,
            filas=range(1, filas + 1),
            columnas=range(1, columnas + 1),
            ocupadas=ocupadas,
            servicios=servicios
        )
    except ApiError as e:
        flash(e.mensaje, "danger")
        return redirect(url_for("public.index"))


@public_bp.route("/compra/<int:compra_id>")
def ver_comprobante(compra_id: int):
    """Muestra el comprobante con los detalles de compra y el código QR."""
    if "auth_token" not in session:
        flash("Debes iniciar sesión para ver tus compras.", "info")
        return redirect(url_for("public.login"))

    try:
        resp = get(f"/compras/{compra_id}")
        compra = resp.get("datos", {})
        return render_template("cliente/comprobante.html", compra=compra)
    except ApiError as e:
        flash(e.mensaje, "danger")
        return redirect(url_for("public.index"))


@public_bp.route("/compra/<int:compra_id>/cancelar", methods=["POST"])
def cancelar_compra(compra_id: int):
    """Cancela una compra hasta 2 horas antes de la función (S13, S14)."""
    try:
        post(f"/compras/{compra_id}/cancelacion")
        flash("Tu compra ha sido cancelada exitosamente y las butacas han sido liberadas.", "success")
    except ApiError as e:
        flash(e.mensaje, "danger")

    return redirect(url_for("public.ver_comprobante", compra_id=compra_id))


# ---------------------------------------------------------------------
# Rutas de Autenticación
# ---------------------------------------------------------------------
@public_bp.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión para clientes y administradores."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        try:
            resultado = post("/auth/login", json_data={"email": email, "password": password})
            datos = resultado.get("datos", {})
            session["auth_token"] = datos["token"]
            session["usuario"] = datos["usuario"]
            flash(f"¡Bienvenido, {datos['usuario']['nombre']}!", "success")

            next_url = request.args.get("next") or url_for("public.index")
            return redirect(next_url)
        except ApiError as e:
            flash(e.mensaje, "danger")

    return render_template("auth/login.html")


@public_bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Registro de nuevas cuentas de clientes."""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        try:
            resultado = post("/auth/registro", json_data={
                "nombre": nombre,
                "email": email,
                "password": password
            })
            datos = resultado.get("datos", {})
            session["auth_token"] = datos["token"]
            session["usuario"] = datos["usuario"]
            flash("¡Registro completado con éxito! Tu cuenta está activa.", "success")
            return redirect(url_for("public.index"))
        except ApiError as e:
            flash(e.mensaje, "danger")

    return render_template("auth/registro.html")


@public_bp.route("/perfil")
def perfil():
    """Perfil del cliente: historial de consumos y películas vistas (S22)."""
    if "auth_token" not in session:
        flash("Debes iniciar sesión para acceder a tu perfil.", "info")
        return redirect(url_for("public.login", next=request.url))

    try:
        resp = get("/usuarios/me/historial")
        historial = resp.get("datos", {})
        return render_template(
            "cliente/perfil.html",
            usuario=session.get("usuario"),
            compras=historial.get("compras", []),
            peliculas_vistas=historial.get("peliculas_vistas", [])
        )
    except ApiError as e:
        flash(e.mensaje, "danger")
        return redirect(url_for("public.index"))


@public_bp.route("/logout")
def logout():
    """Cierra la sesión del usuario actual."""
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("public.index"))

