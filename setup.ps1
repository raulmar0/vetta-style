$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Necesitas Python 3.9+ instalado (https://www.python.org/downloads/)."
  exit 1
}
if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Error "Necesitas Node.js 18+ y npm instalados (https://nodejs.org/)."
  exit 1
}

Write-Host "1/3 Creando entorno virtual de Python (.venv) e instalando Pillow + numpy..."
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip | Out-Null
.\.venv\Scripts\pip.exe install -r requirements.txt

Write-Host "2/3 Instalando Playwright (Node.js)..."
npm install

Write-Host "3/3 Descargando Chromium para Playwright..."
npx playwright install chromium

Write-Host ""
Write-Host "Listo. Ya puedes pedirle a tu agente que cree pósters con el skill vetta-rodada-poster."
