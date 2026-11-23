#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: necesitas Python 3.9+ instalado (https://www.python.org/downloads/)." >&2
  exit 1
fi
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "Error: necesitas Node.js 18+ y npm instalados (https://nodejs.org/)." >&2
  exit 1
fi

echo "1/3 Creando entorno virtual de Python (.venv) e instalando Pillow + numpy..."
python3 -m venv .venv
.venv/bin/python3 -m pip install --upgrade pip >/dev/null
.venv/bin/pip install -r requirements.txt

echo "2/3 Instalando Playwright (Node.js)..."
npm install

echo "3/3 Descargando Chromium para Playwright..."
npx playwright install chromium

echo ""
echo "Listo. Ya puedes pedirle a tu agente que cree pósters con el skill vetta-rodada-poster."
