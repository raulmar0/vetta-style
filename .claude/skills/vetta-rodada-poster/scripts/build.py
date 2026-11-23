#!/usr/bin/env python3
"""Vetta rodada poster — config JSON -> post (1080x1440) + story (1080x1920).

Usage:
  python3 build.py <config.json> [--out DIR] [--render] [--formats post,story]
  python3 build.py --logo-info <logo.png> [...]   # print detected logo metrics

Fixed style (do not change per event): Vetta purple bg, blurred-foliage top extension, top fade
(30% softened), bottom multiply grade, light teal->violet tint, faint topographic contours,
Work Sans lowercase headline with teal dot, gradient line icons, logos aligned to the 135/945 margins.
"""
import argparse, html as H, json, math, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W = 1080
ROW_L, ROW_R = 135, 945          # every element aligns to these two lines
SCALE = 2                        # background image is built at 2x
FORMATS = {                      # S/B = shift of top/bottom blocks vs. post (story safe zones)
    'post':  dict(H=1440, S=0,   B=0),
    'story': dict(H=1920, S=196, B=292),
}
LOGO_AREA = 15000                # default optical size (px^2 of visible bbox) ~ Vetta logo
MIN_GAP = 72                     # min space between neighbouring logos (separator sits in the middle)
TOP_SOFT = 0.7                   # top fade intensity (approved: 30% softer than the bottom mirror)

# ---------------------------------------------------------------- icons (24x24 line glyphs)
ICONS = {
    'fecha':     '<rect x="3.5" y="4.5" width="17" height="16" rx="3"/><path d="M3.5 9.5h17M8 2.5v4M16 2.5v4"/><rect x="13.2" y="13" width="3.6" height="3.6" rx=".8" fill="currentColor" stroke="none"/>',
    'hora':      '<circle cx="12" cy="13.5" r="7.5"/><path d="M10 2.5h4M12 2.5v3.5M12 13.5l3-3M18.5 6.5l1.4-1.4"/>',
    'tienda':    '<path d="M4 10v10h16V10M3 10l1.8-5.5h14.4L21 10z"/><path d="M3 10c0 1.6 1.3 2.4 3 2.4S9 11.6 9 10c0 1.6 1.3 2.4 3 2.4s3-.8 3-2.4c0 1.6 1.3 2.4 3 2.4s3-.8 3-2.4M10 20v-5h4v5"/>',
    'montana':   '<path d="M2 19l6.5-10 4 6 3-4.5L22 19z"/><path d="M8.5 9l1.6 2.4"/>',
    'nivel':     '<path d="M6 13l6-5 6 5M6 18l6-5 6 5M6 8l6-5 6 5"/>',
    'pin':       '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.6"/>',
    'ruta':      '<circle cx="6" cy="19" r="2.4"/><circle cx="18" cy="5" r="2.4"/><path d="M8.4 19H17a3.5 3.5 0 0 0 0-7H7a3.5 3.5 0 0 1 0-7h8.6"/>',
    'distancia': '<path d="M3 12h18M6 8.5 2.5 12 6 15.5M18 8.5l3.5 3.5-3.5 3.5"/>',
    'ritmo':     '<path d="M3.5 17a8.5 8.5 0 1 1 17 0"/><path d="M12 17l4.5-5.5"/><circle cx="12" cy="17" r="1.3" fill="currentColor" stroke="none"/>',
    'cafe':      '<path d="M4 9.5h12v4.5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M16 11h1.5a2.5 2.5 0 0 1 0 5H16M8 3.5c0 1.4 1.4 1.6 1.4 3M12 3.5c0 1.4 1.4 1.6 1.4 3"/>',
    'bici':      '<circle cx="5.5" cy="16" r="3.6"/><circle cx="18.5" cy="16" r="3.6"/><path d="M5.5 16 9 9h6.5l3 7M9 9l3.5 7h-7M12.5 16l3-7M13.5 6.5h3"/>',
    'grupo':     '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.6 2.7-6 6-6s6 2.4 6 6"/><path d="M16 5.2a3 3 0 0 1 0 5.6M18 14.3c1.8.8 3 2.8 3 5.7"/>',
    'info':      '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.01"/>',
}
ALIAS = {'cita': 'hora', 'horario': 'hora', 'reloj': 'hora', 'lugar': 'tienda', 'salida': 'tienda',
         'ubicacion': 'pin', 'punto': 'pin', 'perfil': 'montana', 'altimetria': 'montana',
         'km': 'distancia', 'velocidad': 'ritmo', 'pace': 'ritmo', 'coffee': 'cafe', 'bike': 'bici'}

def icon_svg(name):
    key = ALIAS.get(name, name)
    if key not in ICONS:
        sys.exit(f'icono desconocido "{name}". Disponibles: {", ".join(sorted(ICONS))}')
    return f'<svg class="i" viewBox="0 0 24 24" aria-hidden="true">{ICONS[key]}</svg>'

# ---------------------------------------------------------------- logos
def logo_metrics(path, alpha_thr=20):
    im = Image.open(path).convert('RGBA')
    a = np.array(im)[:, :, 3]
    if a.min() > 200:
        print(f'  ! {os.path.basename(path)} no tiene transparencia: usa un PNG con fondo transparente', file=sys.stderr)
    mask = a > alpha_thr
    rows = mask.any(axis=1); cols = mask.any(axis=0)
    ys = np.nonzero(rows)[0]; xs = np.nonzero(cols)[0]
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    min_gap = max(3, int(0.02 * im.height))
    bands, start, last = [], None, None
    for y in range(y0, y1 + 1):
        if rows[y]:
            if start is None:
                start = y
            elif y - last - 1 >= min_gap:
                bands.append((start, last)); start = y
            last = y
    bands.append((start, last))
    hs = [b - a_ for a_, b in bands]
    has_sub = len(bands) >= 2 and hs[-1] < 0.45 * max(hs[:-1])
    base = bands[-2][1] if has_sub else y1
    return dict(w=im.width, h=im.height, x0=x0, x1=x1, y0=y0, y1=y1, base=base, sub=y1, has_sub=has_sub, bands=bands)

def prepare_logos(logos, base_dir):
    out = []
    for L in logos:
        src = resolve(L['src'], base_dir)
        m = logo_metrics(src)
        if 'baseline_row' in L: m['base'] = int(L['baseline_row']); m['has_sub'] = m['base'] < m['sub']
        if 'subline_bottom_row' in L: m['sub'] = int(L['subline_bottom_row'])
        vis_w, vis_h = m['x1'] - m['x0'], m['y1'] - m['y0']
        s = L.get('scale') or math.sqrt(LOGO_AREA / (vis_w * vis_h)) * L.get('size', 1.0)
        out.append(dict(src=src, alt=L.get('alt', os.path.basename(src)), white=L.get('force_white', False), m=m, s=s))
    return out

def place_logos(logos):
    """visible-left x for each logo. Odd count: middle one centred on the page."""
    for _ in range(40):
        ws = [(L['m']['x1'] - L['m']['x0']) * L['s'] for L in logos]
        n = len(ws)
        if n == 1:
            xs = [W / 2 - ws[0] / 2]; gaps = [999]
        elif n % 2 == 1:
            k = n // 2; mid = W / 2 - ws[k] / 2
            gl = (mid - ROW_L - sum(ws[:k])) / k
            gr = (ROW_R - (mid + ws[k]) - sum(ws[k + 1:])) / k
            xs, x = [], ROW_L
            for w in ws[:k]: xs.append(x); x += w + gl
            xs.append(mid); x = mid + ws[k] + gr
            for w in ws[k + 1:]: xs.append(x); x += w + gr
            gaps = [gl, gr]
        else:
            g = (ROW_R - ROW_L - sum(ws)) / (n - 1)
            xs, x = [], ROW_L
            for w in ws: xs.append(x); x += w + g
            gaps = [g]
        if min(gaps) >= MIN_GAP:
            return xs, ws
        for L in logos: L['s'] *= 0.96
    sys.exit('los logos no caben en el renglón; quita alguno o baja "size"')

def logos_html(logos, BL, separators=False, layout='auto'):
    if layout == 'corner-stack':
        shrink = 0.86 if len(logos) >= 2 else 1.0
        gap = 24
        bot_y = BL + 22
        items = []
        for L in logos:
            m, s = L['m'], L['s'] * shrink
            items.append((L, m, s, (m['x1'] - m['x0']) * s, (m['y1'] - m['y0']) * s))
        col_w = max(vw for *_, vw, _ in items)
        col_x = ROW_R - col_w
        cur_bot = bot_y
        parts = []
        for L, m, s, vw, vh in reversed(items):
            lx = col_x + (col_w - vw) / 2
            top_vis = cur_bot - vh
            style = f'left:{lx - m["x0"] * s:.2f}px;top:{top_vis - m["y0"] * s:.2f}px;width:{m["w"] * s:.2f}px;height:{m["h"] * s:.2f}px'
            if L['white']: style += ';filter:brightness(0) invert(1)'
            parts.append(f'<img src="{file_url(L["src"])}" alt="{H.escape(L["alt"])}" style="{style}" data-vis-w="{vw:.2f}" data-x0="{m["x0"] * s:.2f}" data-bottom-y="{bot_y:.2f}">')
            cur_bot = top_vis - gap
        parts.reverse()
        return '\n    '.join(parts)
    xs, ws = place_logos(logos)
    parts = []
    for L, x in zip(logos, xs):
        m, s = L['m'], L['s']
        if m['has_sub']:   # mid-point between wordmark baseline and subline bottom sits on BL+11
            by = BL + 11 - (m['sub'] - m['base']) * s / 2
        else:              # single-line logo: its bottom sits on the wordmark baseline
            by = BL
        style = f'left:{x - m["x0"] * s:.2f}px;top:{by - m["base"] * s:.2f}px;width:{m["w"] * s:.2f}px;height:{m["h"] * s:.2f}px'
        if L['white']: style += ';filter:brightness(0) invert(1)'
        vis_w = (m['x1'] - m['x0']) * s
        bot_y = by + (m['sub'] - m['base']) * s if m['has_sub'] else by
        parts.append(f'<img src="{file_url(L["src"])}" alt="{H.escape(L["alt"])}" style="{style}" data-vis-w="{vis_w:.2f}" data-x0="{m["x0"] * s:.2f}" data-bottom-y="{bot_y:.2f}">')
    if separators:
        for i in range(len(xs) - 1):
            mid = (xs[i] + ws[i] + xs[i + 1]) / 2
            parts.append(f'<i class="sep" style="left:{mid - 1:.2f}px;top:{BL - 66}px"></i>')
    return '\n    '.join(parts)

# ---------------------------------------------------------------- photo background
def make_bg(src, Hh, top, zoom, focus_x, clean_rows, out_path):
    im = Image.open(src).convert('RGB'); sw, sh = im.size
    CW, CH = W * SCALE, Hh * SCALE; y0 = int(round(top * SCALE))
    need = (CH - y0) * sw / (sh * CW)                 # zoom needed to reach the bottom edge
    z = max(1.0, zoom, need)
    if z > zoom + 1e-6 and zoom >= 1.0 and need > 1.0:
        print(f'  ! zoom subido a {z:.3f} para cubrir hasta abajo', file=sys.stderr)
    pw = int(round(CW * z)); ph = int(round(pw * sh / sw))
    big = im.resize((pw, ph), Image.LANCZOS)
    xo = int(round((pw - CW) * focus_x))
    photo = big.crop((xo, 0, xo + CW, min(ph, CH - y0)))
    canvas = Image.new('RGB', (CW, CH)); canvas.paste(photo, (0, y0))
    if y0 > 0:
        band = max(8, min(photo.height, int(round(clean_rows * SCALE))))
        tile = photo.crop((0, 0, CW, band)); y, flip = y0, True
        while y > 0:                                    # mirror-tile the clean top band upward
            t = tile.transpose(Image.FLIP_TOP_BOTTOM) if flip else tile
            y -= t.height
            if y < 0: t = t.crop((0, -y, CW, t.height)); y = 0
            canvas.paste(t, (0, y)); flip = not flip
        blur = canvas.filter(ImageFilter.GaussianBlur(12 * SCALE))
        a = np.zeros(CH); r1 = min(CH, y0 + 160 * SCALE)
        a[y0:r1] = np.linspace(0, 1, r1 - y0); a[r1:] = 1
        mask = Image.fromarray((np.repeat(a[:, None], CW, 1) * 255).astype('uint8'))
        canvas = Image.composite(canvas, blur, mask)
    canvas.save(out_path, quality=92)

# ---------------------------------------------------------------- topographic contours
def topo_paths(Hh, seed=4, step=6, levels=22):
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:Hh + step:step, 0:W + step:step].astype(float)
    f = np.zeros_like(xs); ky = Hh / 1440
    for (cx, cy, sx, sy, a, amp) in [(820, 260, 260, 120, -.55, 1.0), (260, 420, 300, 110, -.45, .85), (980, 980, 220, 160, -.6, .7),
                                      (120, 1180, 260, 120, -.5, .75), (560, 760, 180, 90, -.3, .45)]:
        cy *= ky
        xr = (xs - cx) * np.cos(a) - (ys - cy) * np.sin(a); yr = (xs - cx) * np.sin(a) + (ys - cy) * np.cos(a)
        f += amp * np.exp(-(xr / sx) ** 2 - (yr / sy) ** 2)
    for _ in range(6):
        fx, fy = rng.uniform(.004, .012, 2); ph = rng.uniform(0, 6.3, 2)
        f += .07 * np.sin(xs * fx + ph[0]) * np.sin(ys * fy + ph[1])
    paths = []
    for li, L in enumerate(np.linspace(f.min(), f.max(), levels + 2)[1:-1]):
        b = (f > L).astype(int)
        idx = b[:-1, :-1] * 8 + b[:-1, 1:] * 4 + b[1:, 1:] * 2 + b[1:, :-1]
        out = []
        for (i, j) in zip(*np.nonzero((idx > 0) & (idx < 15))):
            v = [f[i, j], f[i, j + 1], f[i + 1, j + 1], f[i + 1, j]]
            p = [(j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1)]
            pts = []
            for e in range(4):
                a_, c = e, (e + 1) % 4
                if (v[a_] > L) != (v[c] > L):
                    t = (L - v[a_]) / (v[c] - v[a_])
                    pts.append(((p[a_][0] + t * (p[c][0] - p[a_][0])) * step, (p[a_][1] + t * (p[c][1] - p[a_][1])) * step))
            if len(pts) >= 2: out.append('M%.0f %.0fL%.0f %.0f' % (pts[0] + pts[1]))
            if len(pts) == 4: out.append('M%.0f %.0fL%.0f %.0f' % (pts[2] + pts[3]))
        major = li % 5 == 2
        paths.append(f'<path d="{"".join(out)}" stroke="{"url(#tg)" if major else "#fff"}" stroke-opacity="{.175 if major else .0425}" stroke-width="{2.2 if major else 1.3}"/>')
    return ''.join(paths)

# ---------------------------------------------------------------- page
FONTS = 'https://fonts.googleapis.com/css2?family=Work+Sans:wght@400;500;600;700&display=swap'
LAYOUT_JS = r'''<script>
(async function(){
  const ROW_L=135, ROW_R=945, W=1080, S=+document.body.dataset.s;
  try{ await document.fonts.load('700 200px "Work Sans"'); await document.fonts.load('600 26px "Work Sans"'); await document.fonts.load('400 30px "Work Sans"'); await document.fonts.ready; }catch(e){}
  function ink(text, weight, size, ls){            // ink bounds vs. advance box, measured on a canvas
    const c=document.createElement('canvas'), pad=Math.ceil(size);
    let x=c.getContext('2d'); x.font=weight+' '+size+'px "Work Sans"'; x.letterSpacing=ls+'px';
    const adv=x.measureText(text).width;
    c.width=Math.ceil(adv+pad*2); c.height=Math.ceil(size*2);
    x=c.getContext('2d'); x.font=weight+' '+size+'px "Work Sans"'; x.letterSpacing=ls+'px'; x.fillText(text,pad,Math.round(size*1.4));
    const d=x.getImageData(0,0,c.width,c.height).data; let L=c.width, R=-1;
    for(let i=0;i<c.width;i++){ for(let j=0;j<c.height;j++){ if(d[(j*c.width+i)*4+3]>127){ if(i<L)L=i; R=i; break; } } }
    return {offR: adv-(R+1-pad), inkW: R+1-L};
  }
  const h1=document.querySelector('h1'), lines=[...h1.querySelectorAll('.ln')], REF=200;
  const m=lines.map(l=>ink(l.textContent,700,REF,-0.045*REF));
  const fs=Math.min(+h1.dataset.max, REF*(ROW_R-ROW_L)/Math.max(...m.map(v=>v.inkW)));
  h1.style.fontSize=fs+'px';
  h1.style.top=(127.5+S-(8.5/149.76)*fs)+'px';      // keeps a 30px gap under the label
  lines.forEach((l,i)=>{ l.style.marginRight=(-m[i].offR*fs/REF)+'px'; });
  const lab=document.querySelector('.label'), lm=ink(lab.textContent.toUpperCase(),600,26,5.2);
  lab.style.right=(W-ROW_R-lm.offR)+'px';
  const ll=document.body.dataset.logoLayout||'auto', imgs=[...document.querySelectorAll('.logos img')], det=document.querySelector('.details');
  if(ll==='corner-stack' && imgs.length>=1 && det){
    const botY=+imgs[0].dataset.bottomY, Hh=+document.body.dataset.h;
    det.style.bottom=(Hh-botY-4).toFixed(2)+'px';
  }else if(imgs.length===1 && ll!=='stacked' && det){
    const img=imgs[0], visW=+img.dataset.visW, x0=+img.dataset.x0, botY=+img.dataset.bottomY, Hh=+document.body.dataset.h;
    const cornerLeft=ROW_R-visW, detRight=(ROW_L-0.5)+det.offsetWidth;
    if(ll==='corner' || detRight+44<=cornerLeft){
      img.style.left=(cornerLeft-x0).toFixed(2)+'px';
      det.style.bottom=(Hh-botY-4).toFixed(2)+'px';
    }
  }
  document.body.dataset.ready='1';
})();
(function(){const r=document.body.getBoundingClientRect(),w=r.width,h=r.height;function fit(){const s=Math.min(innerWidth/w,innerHeight/h,1);const b=document.body.style;b.transform='scale('+s+')';b.transformOrigin='top left';b.position='absolute';b.left=((innerWidth-w*s)/2)+'px';b.top=((innerHeight-h*s)/2)+'px';}fit();addEventListener('resize',fit);})();
</script>'''

def stops(rgb, pts):
    return ','.join(f'rgba({rgb},{min(a, 1):.3f}) {y:.0f}px' for y, a in pts)

def page(cfg, fmt, logos, bg_name, base_dir):
    c = FORMATS[fmt]; Hh, S, B = c['H'], c['S'], c['B']
    soft = cfg.get('top_soft', TOP_SOFT)
    tf = [(y, a * soft) for y, a in [(0, .8), (S, .8), (S + 200, .62), (S + 374, .45), (S + 500, .2), (S + 634, 0)]]
    grade = stops('36,33,73', [(0, .5 * soft), (S, .5 * soft), (S + 432, 0), (806 + B, 0), (1066 + B, .55)]) \
        + f',rgba(28,25,64,.94) {1440 + B}px' + (f',rgba(28,25,64,.94) {Hh}px' if Hh > 1440 + B else '')
    fx, fy = cfg.get('topo_focus', [38, 58])
    if fmt == 'story':
        shift = cfg['photo'].get('story_top', cfg['photo'].get('top', 200) + 150) - cfg['photo'].get('top', 200)
        fy = (fy / 100 * 1440 + shift) / Hh * 100
    lines = [H.escape(s) for s in cfg['headline'].split('\n')]
    if cfg.get('headline_dot', True): lines[-1] += '<span class="dot">.</span>'
    h1 = ''.join(f'<span class="ln">{l}</span>' for l in lines)
    rows = '\n    '.join(f'<div class="row">{icon_svg(d["icon"])}<span>{H.escape(d["text"])}</span></div>' for d in cfg['details'])
    topo = ''
    if cfg.get('topo', True):
        topo = f'''<svg class="topo" viewBox="0 0 {W} {Hh}" aria-hidden="true">
    <defs><linearGradient id="tg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#77c1cf"/><stop offset="1" stop-color="#9c66bf"/></linearGradient>
    <radialGradient id="hole" cx="{fx}%" cy="{fy:.1f}%" r="46%"><stop offset="0" stop-color="#000"/><stop offset=".55" stop-color="#000"/><stop offset="1" stop-color="#fff"/></radialGradient>
    <mask id="m"><rect width="{W}" height="{Hh}" fill="url(#hole)"/></mask></defs>
    <g fill="none" stroke-linecap="round" mask="url(#m)">{topo_paths(Hh, cfg.get('topo_seed', 4))}</g>
  </svg>'''
    css = f'''
:root{{--teal:#77c1cf;--violet:#9668b8;--mist:#cfe8ec}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{Hh}px;overflow:hidden;position:relative;background:#1d1a46;color:#fff;
  font-family:'Work Sans',ui-sans-serif,system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
.photo{{position:absolute;inset:0;background:url('{bg_name}') 0 0/{W}px {Hh}px no-repeat;filter:brightness(1.06) contrast(1.05) saturate(.85)}}
.topfade{{position:absolute;inset:0;background:linear-gradient(180deg,{stops('33,28,84', tf)})}}
.grade{{position:absolute;inset:0;mix-blend-mode:multiply;background:linear-gradient(180deg,{grade})}}
.tint{{position:absolute;inset:0;background:linear-gradient(150deg,#77c1cf 0%,#9668b8 100%);mix-blend-mode:color;opacity:.16}}
.topo{{position:absolute;inset:0;width:{W}px;height:{Hh}px}}
.label{{position:absolute;top:{74 + S}px;right:{W - ROW_R - 8}px;font-size:26px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;white-space:nowrap}}
h1{{position:absolute;top:{119 + S}px;right:{W - ROW_R}px;text-align:right;font-weight:700;font-size:150px;line-height:.86;letter-spacing:-.045em;
  white-space:nowrap;text-shadow:0 6px 40px rgba(10,10,30,.35)}}
h1 .ln{{display:block}}
h1 .dot{{color:var(--teal)}}
.details{{position:absolute;bottom:{Hh - (1204 + B)}px;left:{ROW_L - 0.5}px;font-size:30px;line-height:1.36;font-variant-numeric:tabular-nums;
  text-shadow:0 2px 14px rgba(10,10,30,.75)}}
.details .row{{display:flex;align-items:center;gap:16px;white-space:nowrap}}
.details .i{{width:32px;height:32px;flex:none;fill:none;stroke:url(#ig);stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round;color:#9fd3dc;
  filter:drop-shadow(0 2px 8px rgba(10,10,30,.6))}}
.logos img{{position:absolute;display:block}}
.logos .sep{{position:absolute;width:2px;height:92px;background:rgba(255,255,255,.5)}}
@media print{{*{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
@media screen{{html{{height:100vh;display:flex;justify-content:center;align-items:center;background:#0f1010}}body{{flex-shrink:0}}}}
'''
    return f'''<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>{H.escape(cfg['headline'].replace(chr(10), ' '))} — {fmt}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<style>{css}</style></head>
<body data-w="{W}" data-h="{Hh}" data-s="{S}" data-logo-layout="{H.escape(cfg.get('logo_layout', 'auto'))}">
  <svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><linearGradient id="ig" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#77c1cf"/><stop offset="1" stop-color="#b08ad6"/></linearGradient></defs></svg>
  <div class="photo" role="img" aria-label="{H.escape(cfg['photo'].get('alt', 'Foto del evento'))}"></div>
  <div class="topfade"></div>
  <div class="grade"></div>
  <div class="tint"></div>
  {topo}
  <div class="label">{H.escape(cfg['label'])}</div>
  <h1 data-max="{cfg.get('headline_max_px', 190)}">{h1}</h1>
  <div class="details">{rows}</div>
  <div class="logos">
    {logos_html(logos, 1356 + B, cfg.get('separators', False), cfg.get('logo_layout', 'auto'))}
  </div>
{LAYOUT_JS}
</body></html>'''

# ---------------------------------------------------------------- helpers / main
KIT_ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))

def resolve(p, base_dir):
    p = os.path.expanduser(p)
    if os.path.isabs(p):
        if os.path.exists(p): return p
        sys.exit(f'no existe: {p}')
    for root in (base_dir, os.getcwd(), KIT_ROOT):
        full = os.path.normpath(os.path.join(root, p))
        if os.path.exists(full): return full
    sys.exit(f'no existe: {p} (buscado en {base_dir}, {os.getcwd()} y {KIT_ROOT})')

def file_url(p):
    return Path(p).resolve().as_uri()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config', nargs='?')
    ap.add_argument('--out')
    ap.add_argument('--render', action='store_true')
    ap.add_argument('--formats')
    ap.add_argument('--logo-info', nargs='+')
    a = ap.parse_args()
    if a.logo_info:
        for p in a.logo_info:
            m = logo_metrics(p); vw, vh = m['x1'] - m['x0'], m['y1'] - m['y0']
            print(f'{p}\n  bandas={m["bands"]} baseline_row={m["base"]} subline_bottom_row={m["sub"]} subline={m["has_sub"]} '
                  f'escala_auto={math.sqrt(LOGO_AREA / (vw * vh)):.4f}')
        return
    if not a.config: ap.error('falta config.json')
    cfg_path = os.path.abspath(a.config); base = os.path.dirname(cfg_path)
    cfg = json.load(open(cfg_path))
    for k in ('label', 'headline', 'details', 'photo', 'logos'):
        if k not in cfg: sys.exit(f'config sin "{k}"')
    slug = cfg.get('slug') or os.path.splitext(os.path.basename(cfg_path))[0]
    out = os.path.abspath(a.out or cfg.get('out') or os.path.join(os.getcwd(), 'posters', slug))
    os.makedirs(out, exist_ok=True)
    fmts = (a.formats or ','.join(cfg.get('formats', ['post', 'story']))).split(',')
    ph = cfg['photo']; src = resolve(ph['src'], base)
    logos = prepare_logos(cfg['logos'], base)
    htmls = []
    for fmt in fmts:
        if fmt not in FORMATS: sys.exit(f'formato desconocido: {fmt}')
        top = ph.get('top', 200) if fmt == 'post' else ph.get('story_top', ph.get('top', 200) + 150)
        bg = f'{slug}-{fmt}-bg.jpg'
        make_bg(src, FORMATS[fmt]['H'], top, ph.get('zoom', 1.0), ph.get('focus_x', 0.5), ph.get('clean_top_rows', 120), os.path.join(out, bg))
        for L in logos: L['s0'] = L.get('s0', L['s']); L['s'] = L['s0']   # same sizes in every format
        path = os.path.join(out, f'{slug}-{fmt}.html')
        open(path, 'w').write(page(cfg, fmt, logos, bg, base))
        htmls.append(path); print('html', path, flush=True)
    if a.render:
        subprocess.run(['node', os.path.join(HERE, 'render.js')] + htmls, check=True)

if __name__ == '__main__':
    main()
