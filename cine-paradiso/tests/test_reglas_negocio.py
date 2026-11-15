"""Pruebas automatizadas de reglas de negocio de Cine Paradiso (Cátedra Lanzillotta - FIUBA)."""

import pytest
import sys
from pathlib import Path

# Agregar raíz del proyecto y backend al path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app import crear_app
from src.qr_utils import generar_qr_base64, generar_qr_bytes


@pytest.fixture
def cliente():
    """Fixture que provee un cliente de prueba de Flask."""
    app = crear_app()
    app.config["TESTING"] = True
    with app.test_client() as cliente:
        yield cliente


def test_generacion_qr_local_offline():
    """Verifica que la generación de código QR en Python produzca un PNG válido sin internet."""
    token = "token_prueba_secreto_cine_paradiso_12345"
    
    # 1. Prueba de Data URI Base64
    b64_qr = generar_qr_base64(token)
    assert b64_qr.startswith("data:image/png;base64,")
    assert len(b64_qr) > 100

    # 2. Prueba de bytes PNG binarios
    png_bytes = generar_qr_bytes(token)
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_registro_rechaza_password_corta(cliente):
    """Verifica que el endpoint de registro rechace contraseñas de menos de 6 caracteres."""
    resp = cliente.post("/auth/registro", json={
        "nombre": "Estudiante Test",
        "email": "test@fiuba.uba.ar",
        "password": "123"  # Menos de 6 caracteres
    })
    assert resp.status_code == 400
    datos = resp.get_json()
    assert "La contraseña debe tener al menos 6 caracteres" in datos.get("mensaje", "")


def test_registro_rechaza_campos_faltantes(cliente):
    """Verifica que el registro falle si faltan datos requeridos."""
    resp = cliente.post("/auth/registro", json={
        "nombre": "Incompleto"
    })
    assert resp.status_code == 400


def test_compra_rechaza_mas_de_seis_entradas(cliente):
    """Verifica el cumplimiento estricto del Supuesto S3: máximo 6 entradas por compra."""
    # Generamos un token temporal para simular usuario autenticado
    from src.security import generar_token
    token = generar_token(usuario_id=1, email="test@cine.com", rol="cliente")
    
    # Intentamos comprar 7 entradas
    siete_butacas = [{"fila": 1, "columna": i} for i in range(1, 8)]
    resp = cliente.post(
        "/compras",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "funcion_id": 1,
            "butacas": siete_butacas
        }
    )
    assert resp.status_code == 400
    datos = resp.get_json()
    assert "máximo 6 entradas" in datos.get("mensaje", "").lower()


def test_compra_rechaza_cero_entradas(cliente):
    """Verifica que no se pueda enviar una compra sin seleccionar butacas."""
    from src.security import generar_token
    token = generar_token(usuario_id=1, email="test@cine.com", rol="cliente")

    resp = cliente.post(
        "/compras",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "funcion_id": 1,
            "butacas": []
        }
    )
    assert resp.status_code == 400


def test_endpoint_health(cliente):
    """Verifica que el endpoint de salud responda con JSON válido."""
    resp = cliente.get("/api/health")
    assert resp.status_code in (200, 500)
    datos = resp.get_json()
    assert "status" in datos.get("datos", {})
