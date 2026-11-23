---
name: vetta-rodada-poster
description: Genera pósters de rodadas y eventos de Vetta Pro Cycling en el estilo aprobado "topográfico + foto" (el de "la huasteca."). Produce post 1080×1440 y story 1080×1920 en PNG (1x y 2x) a partir de un JSON con el nombre de la ruta, la etiqueta, los datos con iconos, una foto de fotos/ y cualquier número de logos de brand/logos/. Úsalo cuando pidan un póster, flyer, post o story de una rodada o evento de Vetta, o cuando quieran cambiar textos, ruta, foto o patrocinadores.
---

# Vetta · póster de rodada (estilo topográfico)

El diseño ya está aprobado. Este skill **solo cambia contenidos**; el estilo es fijo y lo genera el script.

```
.claude/skills/vetta-rodada-poster/
  scripts/build.py                 config.json → HTML (+ fondo extendido) y, con --render, PNG
  scripts/render.js                HTML → PNG 1x y 2x (Playwright)
  examples/rodada-la-huasteca.json ejemplo 1 línea + 3 logos
  examples/huasteca-lateral.json   ejemplo 2 líneas + 3 logos sobre picos de montaña
  examples/sube-de-nivel.json      ejemplo 2 líneas + solo logo Vetta (evergreen)
```

## Primer uso (dependencias)

Antes de renderizar por primera vez en una computadora nueva, verifica si ya existen `.venv` y `node_modules` en la raíz del kit. Si faltan, corre `./setup.sh` (macOS/Linux) o `.\setup.ps1` (Windows).

Para ejecutar Python, usa `.venv/bin/python3` si existe (en Windows `.venv\Scripts\python.exe`), o `python3` si `Pillow` y `numpy` ya están instalados globalmente.

## Flujo

1. **Reúne el contenido** del evento que te pase el usuario (y consulta `brand/brand.md` si necesitas tono, datos oficiales o canales de Vetta): nombre de la ruta, tipo y distancia, fecha, horarios, punto de salida, ruta, nivel, foto y marcas/patrocinadores.
   - Si el usuario no eligió foto, revisa las disponibles en `fotos/` y sugiere/elige una foto vertical cuyo sujeto deje espacio libre arriba para el titular.
2. **Crea la configuración** en `posters/<slug>.json` tomando como base `.claude/skills/vetta-rodada-poster/examples/rodada-la-huasteca.json`.
   - Las rutas de `photo.src` y `logos[].src` pueden escribirse directo desde la raíz del kit (ej. `"fotos/mi-foto.jpg"`, `"brand/logos/vetta-logo-white.png"`), o relativas al JSON, o absolutas.
3. **Construye y renderiza** desde la raíz del kit:
   ```bash
   PYTHON=$([ -x .venv/bin/python3 ] && echo .venv/bin/python3 || echo python3)
   $PYTHON .claude/skills/vetta-rodada-poster/scripts/build.py posters/<slug>.json --render
   ```
   La salida va a `posters/<slug>/` (cámbiala con `--out DIR`):
   - `<slug>-post.png` (1080×1440) y `<slug>-story.png` (1080×1920);
   - `2x/` con las versiones a 2160 px de ancho (para publicar);
   - los HTML y los fondos `*-bg.jpg` generados.

   Usa `--formats post` o `--formats story` para generar uno solo.
4. **Revisa los PNG** (ábrelos con tu herramienta de lectura de imágenes) con la checklist de abajo. Ajusta el JSON y vuelve a correr hasta que todo pase.
5. **Entrega** las rutas de los PNG de `2x/` (para publicar) y de `1x`.

## Config (JSON)

| Campo | Qué es |
|---|---|
| `slug` | Nombre de archivos/carpeta. Por defecto, el nombre del JSON. |
| `label` | Línea chica arriba a la derecha; se muestra en MAYÚSCULAS. Ej. `"Rodada grupal · 80km"`. |
| `headline` | Nombre de la ruta en minúsculas. Usa `\n` para partirlo en dos líneas (ej. `"presa\nrompepicos"`). El tamaño se ajusta solo para que la línea más ancha ocupe exactamente el ancho entre márgenes, hasta un máximo de 190 px (`headline_max_px`). Si queda muy chico (<110 px) en una línea, pártelo en dos. |
| `headline_dot` | Punto teal al final (`true` por defecto). |
| `details` | Lista de `{ "icon": "...", "text": "..." }`, de 3 a 6 renglones. Se apilan hacia arriba desde encima de los logos. Usa textos cortos en minúsculas (respetando siglas y nombres propios); cada renglón debe caber en una sola línea (~30 caracteres). |
| `photo.src` | Foto (normalmente en `fotos/`). |
| `photo.top` | Y (px) donde empieza la foto en el post (200 por defecto). Súbela o bájala para que el titular no tape caras. |
| `photo.story_top` | Igual para la story (por defecto `top + 150`). |
| `photo.zoom`, `photo.focus_x` | Acercamiento (≥1) y encuadre horizontal (0 = izquierda, 0.5 = centro, 1 = derecha). Si la foto no alcanza a cubrir hasta abajo, el zoom sube solo. |
| `photo.clean_top_rows` | Cuántos px de la parte superior de la foto son fondo limpio (árboles, cielo, pared, **sin personas**). Esa franja se refleja y desenfoca para rellenar arriba de la foto. Default 120. Si arriba se ve un reflejo raro, bájalo. |
| `logos` | Lista ordenada de izquierda a derecha (normalmente en `brand/logos/`). Pon a **Vetta al centro** cuando el número de logos sea impar. |
| `top_soft` | Intensidad del fade morado superior. Default 0.7 (aprobado). Súbelo a 1.0–1.25 si la foto tiene cielo claro arriba. |
| `separators` | Líneas verticales entre logos (`false` por defecto; sin divisores). |
| `logo_layout` | Distribución del pie: `"auto"` (por defecto), `"corner"`, `"corner-stack"` o `"stacked"`. En `"auto"`, si hay **1 solo logo** y cabe junto a los datos (con ≥44 px de respiro), pone el logo en la esquina inferior derecha (`x=945`) y baja los datos a la esquina inferior izquierda (`x=135`); si hay **2+ logos** o el texto es muy ancho, mantiene el diseño apilado clásico (datos arriba, logos abajo). Con `"corner-stack"`, apila 2 logos verticalmente en la esquina inferior derecha (uno arriba del otro) con los datos abajo a la izquierda. |
| `topo_focus`, `topo_seed` | Centro del "hueco" sin curvas de nivel, en % del post (default `[38, 58]`; ponlo sobre las personas), y semilla del patrón. |

### Iconos

| Icono | Uso | Alias |
|---|---|---|
| `fecha` | calendario | |
| `hora` | cronómetro | `cita`, `horario`, `reloj` |
| `tienda` | tienda/punto de salida | `lugar`, `salida` |
| `pin` | ubicación | `ubicacion`, `punto` |
| `montana` | ruta de montaña/perfil | `perfil`, `altimetria` |
| `ruta` | recorrido A→B | |
| `distancia` | km | `km` |
| `nivel` | nivel/dificultad | |
| `ritmo` | velocidad promedio | `velocidad`, `pace` |
| `cafe` | parada de café | `coffee` |
| `bici` | tipo de bici | `bike` |
| `grupo` | grupo/cupo | |
| `info` | nota general | |

Si hace falta un icono nuevo, agrégalo al diccionario `ICONS` de `build.py`. Debe ser un glifo de línea en una cuadrícula 24×24, sin relleno salvo detalles de `fill="currentColor"`.

### Logos

- Usa un **PNG con transparencia** en versión blanca (`brand/logos/`). Si solo existe la versión oscura, agrega `"force_white": true`.
- **Tamaño:** por defecto todos tienen la misma área visual (~la del logo Vetta). Para afinar uno usa `"size": 1.1` (más grande) o `0.9`, o fija `"scale"` (px por px del PNG) si ya está aprobado (`vetta-logo-white.png`: `0.3729`, `bsmx-logo-white.png`: `0.45`, `rusela-logo-white.png`: `0.5238`).
- **Alineación vertical:** el script detecta las bandas del PNG (ícono / wordmark / sublínea). Revisa lo detectado con `python3 .claude/skills/vetta-rodada-poster/scripts/build.py --logo-info <logo.png>`. Si un logo tiene descendentes o bandas raras, corrígelo con `"baseline_row"` y `"subline_bottom_row"`.
- **Distribución horizontal:** el primer logo empieza en x=135 y el último termina en x=945. Con un número impar de logos, el del medio queda centrado. Lo recomendable es de 1 a 5 logos.

## Estilo fijo (no cambiar por evento)

- Márgenes x=135 y x=945.
- Paleta Vetta: fondo `#1d1a46`, fade superior morado `(33,28,84)`, degradado inferior multiply `#242149`, tinte teal `#77c1cf` → violeta `#9668b8` al 16%, punto del titular en teal.
- Curvas de nivel ilustrativas muy tenues ocultas sobre las personas.
- Tipografía: Work Sans 700 en minúsculas para el titular (`-0.045em`), Work Sans 600 en mayúsculas para la etiqueta (`0.2em`), datos a 30 px con iconos de trazo en degradado.
- Story: respeta las zonas de la interfaz de Instagram (nada importante antes de y≈260 ni después de y≈1680).

## Checklist de revisión

- [ ] El titular y la etiqueta no tapan caras ni cascos. Si los tapan, sube `photo.top` (y `story_top`).
- [ ] Los datos no caen sobre zonas muy claras (manubrios blancos, cielo). Si caen, ajusta `top`, `zoom` o `focus_x`.
- [ ] El relleno de arriba no muestra reflejos de personas. Si los muestra, baja `clean_top_rows`.
- [ ] Logos alineados, de tamaño parecido y sin chocar. Si no, ajusta `size` o `scale`.
- [ ] Textos correctos, con acentos y en minúsculas (salvo siglas como BSMX y nombres propios).
- [ ] En la story, nada importante en los 260 px de arriba ni en los 240 px de abajo.

## Dependencias

- Python 3.9+ con `Pillow` y `numpy` (instalables con `./setup.sh` o `pip install -r requirements.txt`).
- Node 18+ con `playwright` y Chromium (`npm install && npx playwright install chromium`).
- Internet para cargar `Work Sans` desde Google Fonts al renderizar.
