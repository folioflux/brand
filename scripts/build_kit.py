#!/usr/bin/env python3
"""Builds the FolioFlux brand kit from colors/tokens.json and the fonts in typography/fonts.

Writes:
  logo/svg/*.svg         the mark and the lockups (wordmark outlined, no font needed)
  logo/png/*.png         PNG exports at several sizes
  logo/previews/*.png    the lockup on dark and on light
  colors/tokens.css      CSS custom properties
  colors/swatches/*.png  one swatch per color, plus palette.png
  typography/specimen.png

Needs: Python 3.10+, fonttools, uharfbuzz, Pillow, and Google Chrome or Chromium on PATH.
  pip install fonttools uharfbuzz pillow
  python3 scripts/build_kit.py
"""
import json, os, shutil, subprocess, tempfile
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
import uharfbuzz as hb
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, 'typography', 'fonts')
TOKENS = json.load(open(os.path.join(ROOT, 'colors', 'tokens.json')))
CORE = {k: v['$value'] for k, v in TOKENS['color']['core'].items()}
SUPPORT = {k: v['$value'] for k, v in TOKENS['color']['support'].items()}
BLACK, WHITE, GREEN, INK, HAIRLINE = CORE['black'], CORE['white'], CORE['green'], SUPPORT['ink'], SUPPORT['hairline']

# ------------------------------------------------------------------ geometry (64-unit grid)
M = 64
F_SHAPES = [(17, 14, 10, 36, WHITE), (17, 14, 31, 10, WHITE), (31, 29, 17, 9, GREEN)]


def mark_body(tile_rx=14, outline=False, ox=0.0, oy=0.0):
    tile = f'<rect x="{ox}" y="{oy}" width="64" height="64" rx="{tile_rx}" fill="{BLACK}"/>'
    if outline:  # a hairline inside the tile so it holds its edge on black
        tile += f'<rect x="{ox + 1}" y="{oy + 1}" width="62" height="62" rx="{max(tile_rx - 1, 0)}" fill="none" stroke="{HAIRLINE}" stroke-width="2"/>'
    return tile + ''.join(f'<rect x="{ox + x}" y="{oy + y}" width="{w}" height="{h}" rx="1.5" fill="{c}"/>' for x, y, w, h, c in F_SHAPES)


def svg(w, h, body, title='FolioFlux'):
    w, h = round(w, 2), round(h, 2)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{body}</svg>\n')


def wordmark_path(size, tracking=-0.02):
    """'FolioFlux' in Archivo SemiCondensed ExtraBold, shaped with HarfBuzz (kerning) and outlined."""
    path = os.path.join(FONTS, 'static', 'Archivo-ExtraBold-SemiCondensed.ttf')
    blob = hb.Blob.from_file_path(path)
    font = hb.Font(hb.Face(blob))
    buf = hb.Buffer(); buf.add_str('FolioFlux'); buf.guess_segment_properties()
    hb.shape(font, buf, {'kern': True, 'liga': True})
    tt = TTFont(path); gs = tt.getGlyphSet(); upm = tt['head'].unitsPerEm; order = tt.getGlyphOrder()
    s = size / upm
    pen = SVGPathPen(gs, ntos=lambda v: f'{v:.2f}'.rstrip('0').rstrip('.'))
    bounds = BoundsPen(gs)
    x = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        t = (s, 0, 0, -s, x + pos.x_offset * s, 0)  # baseline at y=0, y down
        gs[name].draw(TransformPen(pen, t)); gs[name].draw(TransformPen(bounds, t))
        x += pos.x_advance * s + tracking * size
    xmin, ymin, xmax, ymax = bounds.bounds
    return pen.getCommands(), (xmin, ymin, xmax, ymax)


def lockup(text_color, outline=False):
    """Mark + wordmark: wordmark at 0.62 of the mark's height, 0.3 of the mark apart, optically centred."""
    d, (xmin, ymin, xmax, ymax) = wordmark_path(M * 0.62)
    gap = M * 0.3
    tx = M + gap - xmin
    ty = M / 2 - (ymin + ymax) / 2
    w = M + gap + (xmax - xmin)
    body = mark_body(outline=outline) + f'<path transform="translate({tx:.2f} {ty:.2f})" fill="{text_color}" d="{d}"/>'
    return svg(w, M, body), w


def wordmark_only(text_color):
    d, (xmin, ymin, xmax, ymax) = wordmark_path(M * 0.62)
    return svg(xmax - xmin, ymax - ymin, f'<path transform="translate({-xmin:.2f} {-ymin:.2f})" fill="{text_color}" d="{d}"/>')

# ------------------------------------------------------------------ rendering


def chrome():
    for name in ('google-chrome', 'chromium', 'chromium-browser', 'chrome'):
        if shutil.which(name):
            return name
    raise SystemExit('Google Chrome or Chromium is required on PATH')


def render(html, out, w, h, scale=1, transparent=False):
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, 'page.html')
        open(page, 'w').write(html)
        args = [chrome(), '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
                f'--force-device-scale-factor={scale}', '--allow-file-access-from-files', '--virtual-time-budget=3000',
                f'--window-size={w},{h}', f'--screenshot={out}', 'file://' + page]
        if transparent:
            args.insert(2, '--default-background-color=00000000')
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    clean_png(out, (round(w * scale), round(h * scale)))


def clean_png(path, size=None):
    """Re-encode without metadata chunks (no text, time or colour-profile chunks)."""
    im = Image.open(path); im.load()
    if size and im.size != size:
        im = im.crop((0, 0) + size)
    if im.mode == 'RGBA' and im.getextrema()[3] == (255, 255):
        im = im.convert('RGB')
    im.save(path, 'PNG', optimize=True)


def fontface(base):
    f = lambda p: 'file://' + os.path.join(FONTS, p)
    return f'''<style>
@font-face{{font-family:Archivo;src:url({f('variable/Archivo-Variable.ttf')});font-weight:100 900;font-stretch:62% 125%}}
@font-face{{font-family:'Instrument Sans';src:url({f('variable/InstrumentSans-Variable.ttf')});font-weight:400 700;font-stretch:75% 100%}}
@font-face{{font-family:'Fragment Mono';src:url({f('static/FragmentMono-Regular.ttf')})}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:transparent;overflow:hidden;-webkit-font-smoothing:antialiased;font-family:'Instrument Sans'}}
.d{{font-family:Archivo;font-weight:800}} .m{{font-family:'Fragment Mono'}}
{base}</style>'''


def img_page(svg_path, w, h, bg='transparent', pad=0):
    return (f'<!doctype html><html><head><meta charset="utf-8">{fontface("")}</head><body style="width:{w}px;height:{h}px;background:{bg}">'
            f'<div style="width:{w}px;height:{h}px;display:flex;align-items:center;justify-content:center;padding:{pad}px">'
            f'<img src="file://{svg_path}" style="max-width:100%;max-height:100%;width:100%;height:100%;object-fit:contain"></div></body></html>')

# ------------------------------------------------------------------ build steps


def build_logo():
    d = os.path.join(ROOT, 'logo', 'svg')
    files = {
        'folioflux-mark.svg': svg(M, M, mark_body()),
        'folioflux-mark-on-dark.svg': svg(M, M, mark_body(outline=True)),
        'folioflux-mark-square.svg': svg(M, M, mark_body(tile_rx=0)),
        'folioflux-wordmark-white.svg': wordmark_only(WHITE),
        'folioflux-wordmark-ink.svg': wordmark_only(INK),
    }
    lk_dark, lw = lockup(WHITE, outline=True)
    lk_light, _ = lockup(INK)
    files['folioflux-lockup-on-dark.svg'] = lk_dark
    files['folioflux-lockup-on-light.svg'] = lk_light
    for name, content in files.items():
        open(os.path.join(d, name), 'w').write(content)

    p = os.path.join(ROOT, 'logo', 'png')
    for s in (16, 32, 64, 128, 256, 512, 1024):
        render(img_page(os.path.join(d, 'folioflux-mark.svg'), s, s), os.path.join(p, f'folioflux-mark-{s}.png'), s, s, transparent=True)
    for s in (128, 512, 1024):
        render(img_page(os.path.join(d, 'folioflux-mark-on-dark.svg'), s, s), os.path.join(p, f'folioflux-mark-on-dark-{s}.png'), s, s, transparent=True)
    for s in (400, 1024):  # full-bleed square for avatars (LinkedIn, X, GitHub crop it themselves)
        render(img_page(os.path.join(d, 'folioflux-mark-square.svg'), s, s, bg=BLACK), os.path.join(p, f'folioflux-avatar-{s}.png'), s, s)
    ratio = lw / M
    for h in (64, 128, 256):
        w = round(h * ratio)
        for v in ('on-dark', 'on-light'):
            render(img_page(os.path.join(d, f'folioflux-lockup-{v}.svg'), w, h), os.path.join(p, f'folioflux-lockup-{v}-{h}.png'), w, h, transparent=True)

    pv = os.path.join(ROOT, 'logo', 'previews')
    for v, bg in (('on-dark', BLACK), ('on-light', CORE['paper'])):
        render(img_page(os.path.join(d, f'folioflux-lockup-{v}.svg'), 800, 360, bg=bg, pad=110), os.path.join(pv, f'lockup-{v}.png'), 800, 360, scale=2)
    # clear space diagram: dashed box at 0.25 of the mark's height around the mark
    cs = 0.25 * 160
    html = (f'<!doctype html><html><head><meta charset="utf-8">{fontface("")}</head><body style="width:800px;height:360px;background:{CORE["paper"]}">'
            f'<div style="position:relative;width:800px;height:360px">'
            f'<div style="position:absolute;left:{400 - 80 - cs}px;top:{180 - 80 - cs}px;width:{160 + 2 * cs}px;height:{160 + 2 * cs}px;border:1.5px dashed {SUPPORT["boundary"]}"></div>'
            f'<img src="file://{os.path.join(d, "folioflux-mark.svg")}" style="position:absolute;left:320px;top:100px;width:160px;height:160px">'
            f'<div class="m" style="position:absolute;left:{400 + 80 + cs + 16}px;top:{180 - 80 - cs}px;font-size:13px;letter-spacing:.12em;color:{INK};text-transform:uppercase;line-height:1.6">Clear space<br>¼ of the mark<br>on every side<br><br><span style="color:{SUPPORT["paper-muted"]}">Min size 16 px</span></div>'
            f'</div></body></html>')
    render(html, os.path.join(pv, 'clear-space.png'), 800, 360, scale=2)


def build_css():
    t = TOKENS
    lines = ['/* FolioFlux brand tokens. Generated from tokens.json by scripts/build_kit.py; edit tokens.json, not this file. */', '', ':root {']
    for group in ('core', 'support'):
        for k, v in t['color'][group].items():
            lines.append(f'  --ff-{k}: {v["$value"]};')
    lines.append('')
    for k, v in t['font'].items():
        fam = ', '.join(f'"{x}"' if ' ' in x else x for x in v['$value'])
        lines.append(f'  --ff-font-{k}: {fam};')
    lines.append('')
    for k, v in t['radius'].items():
        lines.append(f'  --ff-radius-{k}: {v["$value"]};')
    for i, v in enumerate(t['spacing']['$value']):
        lines.append(f'  --ff-space-{i + 1}: {v};')
    lines.append('}')
    for theme in ('dark', 'light'):
        sel = ':root,\n[data-theme="dark"]' if theme == 'dark' else '[data-theme="light"]'
        lines += ['', sel + ' {']
        lines += [f'  --ff-ui-{k}: {v["$value"]};' for k, v in t['color']['theme'][theme].items()]
        lines.append('}')
    open(os.path.join(ROOT, 'colors', 'tokens.css'), 'w').write('\n'.join(lines) + '\n')


def lum(hexv):
    r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def build_swatches():
    out = os.path.join(ROOT, 'colors', 'swatches')
    allc = list(CORE.items()) + list(SUPPORT.items())
    for name, hexv in allc:
        fg = INK if lum(hexv) > 0.18 else WHITE
        border = f'border:1px solid {HAIRLINE};' if hexv.upper() in (BLACK, '#141414', '#1A1A1A') else ('border:1px solid #DCDCD8;' if lum(hexv) > 0.8 else '')
        html = (f'<!doctype html><html><head><meta charset="utf-8">{fontface("")}</head><body style="width:240px;height:160px">'
                f'<div style="width:240px;height:160px;background:{hexv};border-radius:12px;{border}position:relative;color:{fg}">'
                f'<div class="m" style="position:absolute;left:16px;bottom:34px;font-size:13px;letter-spacing:.12em;text-transform:uppercase">{name.replace("-", " ")}</div>'
                f'<div class="m" style="position:absolute;left:16px;bottom:14px;font-size:13px;letter-spacing:.06em;opacity:.8">{hexv}</div></div></body></html>')
        render(html, os.path.join(out, f'{name}.png'), 240, 160, scale=2, transparent=True)
    # palette strip of the core colors, proportional to use
    weights = [('black', 6), ('card', 3), ('green', 2), ('paper', 2), ('white', 1.4), ('magenta', .6)]
    tot = sum(w for _, w in weights)
    cells = ''.join(f'<div style="flex:{w};background:{CORE[n]};position:relative">'
                    f'<span class="m" style="position:absolute;left:12px;bottom:10px;font-size:12px;letter-spacing:.06em;color:{INK if lum(CORE[n]) > .18 else WHITE}">{CORE[n] if w >= 1 else ""}</span></div>' for n, w in weights)
    html = (f'<!doctype html><html><head><meta charset="utf-8">{fontface("")}</head><body style="width:960px;height:120px">'
            f'<div style="display:flex;width:960px;height:120px;border-radius:12px;overflow:hidden;border:1px solid {HAIRLINE}">{cells}</div></body></html>')
    render(html, os.path.join(out, 'palette.png'), 960, 120, scale=2, transparent=True)


def build_specimen():
    html = (f'<!doctype html><html><head><meta charset="utf-8">{fontface("")}</head><body style="width:1200px;height:440px;background:{BLACK};color:{WHITE}">'
            f'<div style="position:relative;width:1200px;height:440px;padding:64px">'
            f'<div class="m" style="font-size:14px;letter-spacing:.12em;color:{SUPPORT["muted"]};text-transform:uppercase">Display · Archivo 800 · width 64%</div>'
            f'<div class="d" style="font-size:120px;font-stretch:64%;line-height:.82;margin-top:18px">Every number, traceable.</div>'
            f'<div style="display:flex;gap:64px;margin-top:56px">'
            f'<div style="flex:1"><div class="m" style="font-size:14px;letter-spacing:.12em;color:{SUPPORT["muted"]};text-transform:uppercase">Body · Instrument Sans 400 / 600</div>'
            f'<p style="font-size:22px;line-height:1.45;margin-top:14px;color:#E0E0E0">The AI finance workspace for freelancers, small teams and their accountants. <b style="font-weight:600;color:{WHITE}">Every figure opens the rows behind it.</b></p></div>'
            f'<div style="flex:1"><div class="m" style="font-size:14px;letter-spacing:.12em;color:{SUPPORT["muted"]};text-transform:uppercase">Labels · Fragment Mono</div>'
            f'<p class="m" style="font-size:20px;line-height:1.6;margin-top:14px;letter-spacing:.12em;text-transform:uppercase">Free in early access<br><span style="color:{SUPPORT["muted"]}">0123456789 · folioflux.com</span></p></div></div>'
            f'</div></body></html>')
    render(html, os.path.join(ROOT, 'typography', 'specimen.png'), 1200, 440, scale=1)


if __name__ == '__main__':
    build_css(); build_logo(); build_swatches(); build_specimen()
    print('done')
