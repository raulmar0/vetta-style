# Logos de marca y patrocinadores

Coloca aquí los logos en formato **PNG con fondo transparente** (preferentemente en versión blanca, ej. `vetta-logo-white.png`, `bsmx-logo-white.png`, etc.).

- Si solo tienes un logo en versión oscura, puedes usarlo igual agregando `"force_white": true` en el JSON del póster.
- El script `build.py` calcula automáticamente el tamaño óptico y alinea las líneas base de todos los logos al margen `x=135`–`945`.
- Puedes revisar las bandas detectadas de cualquier logo con:
  ```bash
  python3 .claude/skills/vetta-rodada-poster/scripts/build.py --logo-info brand/logos/tu-logo.png
  ```
