"""Utilidad para generar código QR en el Frontend de forma 100% offline."""

import io
import base64
import qrcode


def generar_qr_base64(datos: str) -> str:
    """Genera una imagen PNG del código QR y la devuelve como cadena Data URI en Base64."""
    if not datos:
        return ""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(datos)
    qr.make(fit=True)

    imagen = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)

    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"
