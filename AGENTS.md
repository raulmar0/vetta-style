# Vetta Style — Instrucciones para el Agente

Este lienzo genera pósters y contenido visual oficial de **Vetta Pro Cycling** en formato Instagram Post (`1080×1440` + `2x`) e Instagram Story (`1080×1920` + `2x`).

## Qué hacer cuando el usuario pida un póster
1. Lee y sigue el skill en `.claude/skills/vetta-rodada-poster/SKILL.md`.
2. Consulta `brand/brand.md` y `brand/tokens.json` para respetar la paleta, el tono y los canales oficiales de Vetta.
3. Usa las fotos que el usuario coloque en `fotos/` y los logos PNG transparentes en `brand/logos/`. Si alguna carpeta está vacía, pídele al usuario que agregue su foto o logo antes de renderizar.
4. Si faltan dependencias locales (`.venv` o `node_modules/playwright`), ejecuta `./setup.sh` (macOS/Linux) o `.\setup.ps1` (Windows) antes de renderizar.
5. Guarda cada configuración en `posters/<slug>.json`, genera los PNGs en `posters/<slug>/`, **inspecciona visualmente** los PNGs (post y story) con la checklist del skill, ajusta si hace falta y entrega las rutas de `2x/` (para publicar) y `1x`.
