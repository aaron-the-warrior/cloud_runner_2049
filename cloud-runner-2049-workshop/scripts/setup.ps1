# ==============================================================================
# Cloud Runner 2049 Workshop - Setup Script (PowerShell / Windows)
# ==============================================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "🏁 ========================================================" -ForegroundColor Cyan
Write-Host "   Iniciando Setup para Cloud Runner 2049 Workshop" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location -Path $ProjectRoot

# 1. Verificar herramientas base
Write-Host "`n🔍 [1/5] Verificando entorno de Python..." -ForegroundColor Yellow
$UseUv = $false
if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    $UseUv = $true
    $UvVersion = uv --version
    Write-Host "✅ 'uv' detectado: $UvVersion" -ForegroundColor Green
} elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
    $PyVersion = python --version
    Write-Host "⚠️ 'uv' no encontrado. Se usará python estándar: $PyVersion" -ForegroundColor Yellow
    Write-Host "💡 Sugerencia: instala uv ejecutando 'winget install astral-sh.uv' o 'irm https://astral.sh/uv/install.ps1 | iex'" -ForegroundColor Gray
} else {
    Write-Error "❌ Error: Python 3.11+ o 'uv' es requerido en el PATH de Windows."
}

# 2. Creación del entorno virtual (.venv)
Write-Host "`n📦 [2/5] Configurando entorno virtual (.venv)..." -ForegroundColor Yellow
$VenvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvPath)) {
    if ($UseUv) {
        uv venv .venv
    } else {
        python -m venv .venv
    }
    Write-Host "✅ Entorno virtual creado en .venv" -ForegroundColor Green
} else {
    Write-Host "ℹ️  El entorno virtual .venv ya existe." -ForegroundColor Cyan
}

# Activar entorno virtual en la sesión actual
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    & $ActivateScript
    Write-Host "✅ Entorno virtual activado (.venv)." -ForegroundColor Green
} else {
    Write-Warning "No se pudo localizar el script de activación en $ActivateScript"
}

# 3. Instalación de dependencias
Write-Host "`n📥 [3/5] Instalando dependencias del proyecto..." -ForegroundColor Yellow
if ($UseUv) {
    uv pip install -e .
} else {
    python -m pip install --upgrade pip
    pip install -e .
}
Write-Host "✅ Dependencias instaladas correctamente." -ForegroundColor Green

# 4. Verificación de variables de entorno (.env)
Write-Host "`n⚙️  [4/5] Verificando configuración de entorno (.env)..." -ForegroundColor Yellow
$EnvFile = Join-Path $ProjectRoot ".env"
$EnvExample = Join-Path $ProjectRoot ".env.example"

if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile
        Write-Host "⚠️  Se ha copiado .env.example a .env." -ForegroundColor Yellow
        Write-Host "👉 IMPORTANTE: Edita .env y coloca tus claves (GOOGLE_API_KEY o credenciales de GCP)." -ForegroundColor Magenta
    } else {
        Write-Warning "No se encontró el archivo .env.example."
    }
} else {
    Write-Host "✅ Archivo .env detectado." -ForegroundColor Green
}

# 5. Validación de Google Cloud SDK (gcloud)
Write-Host "`n☁️  [5/5] Validando Google Cloud CLI (gcloud)..." -ForegroundColor Yellow
if (Get-Command "gcloud" -ErrorAction SilentlyContinue) {
    $Account = (gcloud config get-value account 2>$null)
    $Project = (gcloud config get-value project 2>$null)
    if ($Account -and $Account -ne "(unset)") {
        Write-Host "✅ Sesión gcloud activa: $Account" -ForegroundColor Green
        Write-Host "📁 Proyecto gcloud actual: $Project" -ForegroundColor Green
    } else {
        Write-Host "⚠️  gcloud está instalado pero no tiene una sesión activa." -ForegroundColor Yellow
        Write-Host "👉 Ejecuta: 'gcloud auth application-default login' si deseas usar Vertex AI." -ForegroundColor Gray
    }
} else {
    Write-Host "ℹ️  'gcloud' no está instalado en el PATH. (Opcional si usas Google AI Studio API Key)." -ForegroundColor Gray
}

Write-Host "`n🎉 ========================================================" -ForegroundColor Green
Write-Host "   ¡Setup completado con éxito!" -ForegroundColor Green
Write-Host "   Para comenzar:" -ForegroundColor Cyan
Write-Host "     .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "     python starter\agent.py" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
