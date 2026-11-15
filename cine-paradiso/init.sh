#!/usr/bin/env bash
# =====================================================================
# Cine Paradiso - Script de Inicialización y Setup de Dependencias
# Cátedra Lanzillotta - Introducción al Desarrollo de Software (FIUBA)
# =====================================================================
set -e

echo "=== [1/4] Creando / verificando entorno virtual venv ==="
if [ ! -d "venv" ]; then
    python3 -m venv venv || python -m venv venv
    echo "Entorno virtual 'venv' creado exitosamente."
else
    echo "Entorno virtual 'venv' ya existente."
fi

echo "=== [2/4] Activando entorno virtual ==="
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "Advertencia: no se encontró el script de activación de venv."
fi

echo "=== [3/4] Instalando dependencias desde requirements.txt ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [4/4] Verificando archivo .env ==="
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Archivo .env creado automáticamente desde .env.example."
else
    echo "Archivo .env ya existente."
fi

echo ""
echo "=========================================================="
echo "✓ Inicialización completada con éxito."
echo "Para levantar el Backend:  python backend/app.py"
echo "Para levantar el Frontend: python frontend/app.py"
echo "=========================================================="
