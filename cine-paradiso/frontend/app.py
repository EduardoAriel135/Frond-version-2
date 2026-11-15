"""Punto de entrada de la aplicación Frontend en Flask (renderizado con Jinja2)."""

from flask import Flask
from src.config import Config
from src.routes.public_routes import public_bp
from src.routes.admin_routes import admin_bp


def crear_app():
    """Fábrica de la aplicación Flask para el Frontend."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    app.config.from_object(Config)

    # Inyección de usuario en el contexto de las plantillas Jinja2
    @app.context_processor
    def inyectar_usuario():
        from flask import session
        return {"usuario_sesion": session.get("usuario")}

    # Filtro Jinja2 para formatear fechas ISO
    @app.template_filter("formato_fecha")
    def formato_fecha_filter(valor):
        if not valor:
            return ""
        # 2026-11-05T20:30:00 -> 05/11/2026 20:30 hs
        try:
            from datetime import datetime
            if "T" in valor:
                dt = datetime.fromisoformat(valor)
            else:
                dt = datetime.strptime(valor, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y a las %H:%M hs")
        except Exception:
            return valor

    # Filtro Jinja2 para convertir número de fila a letra (1->A, 2->B, ...)
    @app.template_filter("fila_letra")
    def fila_letra_filter(num_fila):
        try:
            return chr(64 + int(num_fila))
        except Exception:
            return str(num_fila)

    # Filtro Jinja2 para generar código QR en Base64 100% offline
    @app.template_filter("generar_qr")
    def generar_qr_filter(qr_token):
        from src.qr_utils import generar_qr_base64
        return generar_qr_base64(qr_token)

    # Registro de Blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    return app


app = crear_app()

if __name__ == "__main__":
    print(f"Iniciando Frontend Cine Paradiso en http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
