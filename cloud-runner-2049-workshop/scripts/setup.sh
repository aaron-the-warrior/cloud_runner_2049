#!/usr/bin/env bash
# ==============================================================================
# Cloud Runner 2049 Workshop - Setup Script (Bash / Linux / macOS / Cloud Shell)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "🏁 ========================================================"
echo "   Iniciando Setup para Cloud Runner 2049 Workshop"
echo "=========================================================="

cd "${PROJECT_ROOT}"

# 1. Verificar herramientas base
echo -e "\n🔍 [1/5] Verificando entorno de Python..."
if command -v uv &> /dev/null; then
    USE_UV=true
    echo "✅ 'uv' detectado: $(uv --version)"
elif command -v python3 &> /dev/null; then
    USE_UV=false
    echo "⚠️ 'uv' no encontrado. Se usará python3 estándar: $(python3 --version)"
    echo "💡 Sugerencia: instala uv para instalaciones ultrarrápidas: https://astral.sh/uv"
else
    echo "❌ Error: Python 3.11+ o 'uv' es requerido. Por favor instálalo."
    exit 1
fi

# 2. Creación del entorno virtual (.venv)
echo -e "\n📦 [2/5] Configurando entorno virtual (.venv)..."
if [ ! -d ".venv" ]; then
    if [ "$USE_UV" = true ]; then
        uv venv .venv
    else
        python3 -m venv .venv
    fi
    echo "✅ Entorno virtual creado en .venv"
else
    echo "ℹ️  El entorno virtual .venv ya existe."
fi

# Activar entorno virtual
# shellcheck disable=SC1091
source .venv/bin/activate
echo "✅ Entorno virtual activado."

# 3. Instalación de dependencias
echo -e "\n📥 [3/5] Instalando dependencias del proyecto..."
if [ "$USE_UV" = true ]; then
    uv pip install -e .
else
    pip install --upgrade pip
    pip install -e .
fi
echo "✅ Dependencias instaladas correctamente."

# 4. Verificación de variables de entorno (.env)
echo -e "\n⚙️  [4/5] Verificando configuración de entorno (.env)..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  Se ha creado .env a partir de .env.example."
        echo "👉 IMPORTANTE: Edita .env y coloca tus claves (GOOGLE_API_KEY o credenciales de GCP)."
    else
        echo "❌ Advertencia: No se encontró .env.example."
    fi
else
    echo "✅ Archivo .env detectado."
fi

# 5. Validación de Google Cloud SDK (gcloud)
echo -e "\n☁️  [5/5] Validando Google Cloud CLI (gcloud)..."
if command -v gcloud &> /dev/null; then
    GCLOUD_ACCOUNT=$(gcloud config get-value account 2>/dev/null || true)
    GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
    if [ -n "${GCLOUD_ACCOUNT}" ] && [ "${GCLOUD_ACCOUNT}" != "(unset)" ]; then
        echo "✅ Sesión gcloud activa: ${GCLOUD_ACCOUNT}"
        echo "📁 Proyecto gcloud actual: ${GCLOUD_PROJECT:-'(sin proyecto configurado)'}"
    else
        echo "⚠️  gcloud está instalado pero no tiene una sesión activa."
        echo "👉 Ejecuta: 'gcloud auth application-default login' si deseas usar Vertex AI."
    fi
else
    echo "ℹ️  'gcloud' no está instalado en el PATH. (Opcional si solo usas Google AI Studio API Keys)."
fi

echo -e "\n🎉 ========================================================"
echo "   ¡Setup completado con éxito!"
echo "   Para comenzar:"
echo "     source .venv/bin/activate"
echo "     python starter/agent.py"
echo "=========================================================="
