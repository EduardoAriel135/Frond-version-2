"""Configuración del Frontend (Servidor Web Flask con Jinja2)."""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Parámetros de configuración del Frontend."""
    HOST = os.getenv("FRONTEND_HOST", "127.0.0.1")
    PORT = int(os.getenv("FRONTEND_PORT", 5001))
    DEBUG = os.getenv("FRONTEND_DEBUG", "True").lower() in ("true", "1", "yes")

    SECRET_KEY = os.getenv("FRONTEND_SECRET_KEY", "clave_secreta_sesion_frontend_cine_paradiso")

    # URL base de la API del Backend (consumida vía requests en Python)
    BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:5000").rstrip("/")
