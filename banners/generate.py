#!/usr/bin/env python3
"""FolioFlux banner templates: GitHub, LinkedIn, X and Open Graph.

Pure HTML/CSS + SVG rendered with headless Chrome. Uses only the fonts in ../typography/fonts and
the Python standard library (Pillow is optional; when present it strips PNG metadata).

  python3 banners/generate.py              # every template
  python3 banners/generate.py og x         # some of them

Edit HEADLINE, HIGHLIGHT and LINE below to change the copy. Rules: magenta at most once per image,
labels on green or magenta are black, no figures unless they are real or tagged SAMPLE DATA.
"""
import html, os, random, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), 'typography', 'fonts')

HEADLINE, HIGHLIGHT = 'Every number,', 'Traceable'
LINE = 'The AI finance workspace for freelancers, small teams and their accountants'
URL, TAG = 'folioflux.com', 'Free in early access'

BLACK, CARD, GREEN, MAGENTA, PAPER = '#000000', '#141414', '#2BBC62', '#FF00DD', '#F4F3EE'
MUTED, BOUNDARY, HAIRLINE, SHADE = '#B3B3B3', '#666666', '#2A2A2A', '#C9C9C4'


def css():
    f = lambda p: 'file://' + os.path.join(FONTS, p)
    return f'''
@font-face{{font-family:Archivo;src:url({f('variable/Archivo-Variable.ttf')});font-weight:100 900;font-stretch:62% 125%}}
@font-face{{font-family:'Instrument Sans';src:url({f('variable/InstrumentSans-Variable.ttf')});font-weight:400 700;font-stretch:75% 100%}}
@font-face{{font-family:'Fragment Mono';src:url({f('static/FragmentMono-Regular.ttf')})}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:{BLACK};color:#fff;overflow:hidden;-webkit-font-smoothing:antialiased;font-family:'Instrument Sans'}}
.frame{{position:relative;overflow:hidden;background:{BLACK}}}
.d{{font-family:Archivo;font-weight:800;font-stretch:64%;line-height:.82;letter-spacing:-.005em;white-space:nowrap}}
.m{{font-family:'Fragment Mono'}}
.hl{{display:inline-block;padding:.12em .22em .08em;border-radius:2px;color:#000;font-family:'Fragment Mono';font-size:.5em;font-stretch:100%;
  font-weight:400;letter-spacing:0;line-height:1;text-transform:uppercase;vertical-align:.36em;white-space:nowrap}}
.line{{font-family:'Fragment Mono';color:{MUTED};letter-spacing:.12em;text-transform:uppercase;white-space:nowrap}}
.tag{{display:inline-flex;align-items:center;white-space:nowrap;border-radius:2px;font-family:'Fragment Mono';text-transform:uppercase;line-height:1;
  letter-spacing:.12em;border:1px solid {BOUNDARY};color:#fff;background:{BLACK}}}
.lockup{{display:inline-flex;align-items:center;font-family:Archivo;font-weight:800;font-stretch:87.5%;letter-spacing:-.02em;color:#fff}}
'''


def mark(size):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="{BLACK}"/>'
            f'<rect x="1" y="1" width="62" height="62" rx="13" fill="none" stroke="{HAIRLINE}" stroke-width="2"/>'
            f'<rect x="17" y="14" width="10" height="36" rx="1.5" fill="#fff"/><rect x="17" y="14" width="31" height="10" rx="1.5" fill="#fff"/>'
            f'<rect x="31" y="29" width="17" height="9" rx="1.5" fill="{GREEN}"/></svg>')


def lockup(size):
    """Mark, then the wordmark at 0.62 of its height, 0.3 of it apart."""
    return f'<span class="lockup" style="gap:{size * .3:.1f}px;font-size:{size * .62:.1f}px">{mark(size)}FolioFlux</span>'


def field(w, h, seed, gap=6, fade=(0.0, 0.45)):
    """Ledger field: faint lanes with streaks, fading in from the left. Decorative only."""
    r = random.Random(seed)
    lanes, streaks = [], {}
    for i in range(int(h // gap)):
        y = gap / 2 + i * gap
        lanes.append(f'M0 {y}H{w}')
        for _ in range(r.choice((0, 0, 1, 1, 2))):
            length = 30 + r.random() * 200
            x = r.random() * (w + length) - length
            op = r.choice((0.08, 0.15, 0.3, 0.55, 0.9))
            streaks.setdefault(op, []).append(f'M{max(x, 0):.1f} {y}H{min(x + length, w):.1f}')
    paths = f'<path d="{"".join(lanes)}" stroke="{SHADE}" stroke-opacity=".05"/>'
    paths += ''.join(f'<path d="{"".join(d)}" stroke="{SHADE}" stroke-opacity="{op}"/>' for op, d in streaks.items())
    return (f'<svg width="{w}" height="{h}" style="position:absolute;left:0;top:0"><defs><linearGradient id="g" x1="0" x2="1">'
            f'<stop offset="0" stop-color="#fff" stop-opacity="{fade[0]}"/><stop offset="{fade[1]}" stop-color="#fff" stop-opacity="{fade[0]}"/>'
            f'<stop offset="1" stop-color="#fff"/></linearGradient><mask id="mk"><rect width="{w}" height="{h}" fill="url(#g)"/></mask></defs>'
            f'<g stroke-width="1" fill="none" mask="url(#mk)">{paths}</g></svg>')


def thread(x1, x2, y, w, h, width=1.5, r=4.5):
    return (f'<svg style="position:absolute;left:0;top:0" width="{w}" height="{h}"><path d="M{x1} {y}H{x2}" stroke="{GREEN}" stroke-width="{width}"/>'
            f'<circle cx="{x2}" cy="{y}" r="{r}" fill="{GREEN}"/></svg>')


def headline(size, accent=MAGENTA, stacked=False):
    br = '<br>' if stacked else ' '
    return f'<h1 class="d" style="font-size:{size}px">{html.escape(HEADLINE)}{br}<span class="hl" style="background:{accent}">{html.escape(HIGHLIGHT)}</span>.</h1>'


# ------------------------------------------------------------------ templates: (name, w, h, scales, body)

def github_banner():
    """README banner, 1280x360 (exported @2x). Matches the org profile banner: green highlight."""
    W, H = 1280, 360
    body = f'''{field(W, H, 7)}
<div style="position:absolute;left:72px;top:56px">{lockup(40)}</div>
<div style="position:absolute;left:72px;top:128px">{headline(104, GREEN)}
 <div class="line" style="margin-top:26px;font-size:16px">{LINE}</div></div>
{thread(72, 520, 306, W, H)}
<div style="position:absolute;right:56px;bottom:38px;display:flex;gap:12px;align-items:center">
 <span class="m" style="font-size:15px;color:{PAPER};letter-spacing:.06em">{URL}</span><span class="tag" style="font-size:13px;padding:8px 10px">{TAG}</span></div>'''
    return 'github/folioflux-github-banner-1280x360', W, H, (2,), body


def github_social():
    """Repository social preview, 1280x640 (GitHub: Settings > Social preview). Green highlight, matching the org banner."""
    W, H, P = 1280, 640, 80
    body = f'''{field(W, H, 11)}
<div style="position:absolute;left:{P}px;top:{P}px">{lockup(56)}</div>
<div style="position:absolute;left:{P}px;top:250px">{headline(136, GREEN)}
 <div class="line" style="margin-top:34px;font-size:19px">{LINE}</div></div>
<div style="position:absolute;left:{P}px;right:{P}px;bottom:{P - 10}px;display:flex;justify-content:space-between;align-items:center">
 <span class="m" style="font-size:20px;color:{PAPER};letter-spacing:.06em">{URL}</span><span class="tag" style="font-size:17px;padding:10px 12px">{TAG}</span></div>'''
    return 'github/folioflux-social-preview-1280x640', W, H, (1,), body


def linkedin_cover():
    """LinkedIn company page cover, 1128x191 (exported @1x and @2x). The page logo covers the bottom-left, so the left ~300 px stays quiet."""
    W, H = 1128, 191
    body = f'''{field(W, H, 102, fade=(0.0, 0.42))}
{thread(330, 760, 153, W, H, r=4)}
<div style="position:absolute;left:330px;top:34px">{headline(74)}
 <div class="line" style="margin-top:20px;font-size:12px">{LINE}</div></div>
<div style="position:absolute;right:40px;bottom:26px"><span class="tag" style="font-size:12px;padding:7px 9px">{TAG}</span></div>'''
    return 'linkedin/folioflux-linkedin-cover-1128x191', W, H, (1, 2), body


def x_header():
    """X (Twitter) header, 1500x500. The avatar covers the bottom-left and phones crop top and bottom, so copy sits centre-right."""
    W, H = 1500, 500
    body = f'''{field(W, H, 23, fade=(0.0, 0.3))}
<div style="position:absolute;left:400px;top:128px">{headline(118)}
 <div class="line" style="margin-top:30px;font-size:16px">{LINE}</div></div>
{thread(400, 880, 356, W, H)}
<div style="position:absolute;right:64px;bottom:72px;display:flex;gap:12px;align-items:center">
 <span class="m" style="font-size:16px;color:{PAPER};letter-spacing:.06em">{URL}</span><span class="tag" style="font-size:14px;padding:8px 10px">{TAG}</span></div>'''
    return 'x/folioflux-x-header-1500x500', W, H, (1,), body


def og():
    """Open Graph / link preview card, 1200x630."""
    W, H, P = 1200, 630, 72
    body = f'''{field(W, H, 31)}
<div style="position:absolute;left:{P}px;top:{P}px">{lockup(52)}</div>
<div style="position:absolute;left:{P}px;top:232px">{headline(128)}
 <div class="line" style="margin-top:32px;font-size:17px">{LINE}</div></div>
{thread(P, 520, 520, W, H)}
<div style="position:absolute;right:{P}px;bottom:{P - 2}px;display:flex;gap:12px;align-items:center">
 <span class="m" style="font-size:18px;color:{PAPER};letter-spacing:.06em">{URL}</span><span class="tag" style="font-size:15px;padding:9px 11px">{TAG}</span></div>'''
    return 'og/folioflux-og-1200x630', W, H, (1,), body


TEMPLATES = {'github': github_banner, 'social': github_social, 'linkedin': linkedin_cover, 'x': x_header, 'og': og}

# ------------------------------------------------------------------ rendering


def chrome():
    for name in ('google-chrome', 'chromium', 'chromium-browser', 'chrome'):
        if shutil.which(name):
            return name
    raise SystemExit('Google Chrome or Chromium is required on PATH')


def strip(path):
    try:
        from PIL import Image
    except ImportError:
        return
    im = Image.open(path); im.load(); im.convert('RGB').save(path, 'PNG', optimize=True)


def render(name, w, h, scales, body):
    doc = (f'<!doctype html><html><head><meta charset="utf-8"><style>{css()} body{{width:{w}px;height:{h}px}} '
           f'.frame{{width:{w}px;height:{h}px}}</style></head><body><div class="frame">{body}</div></body></html>')
    os.makedirs(os.path.join(HERE, os.path.dirname(name)), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, 'page.html')
        open(page, 'w').write(doc)
        for s in scales:
            out = os.path.join(HERE, f'{name}{"" if s == 1 else f"@{s}x"}.png')
            subprocess.run([chrome(), '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', f'--force-device-scale-factor={s}',
                            '--allow-file-access-from-files', '--virtual-time-budget=3000', f'--window-size={w},{h}', f'--screenshot={out}', 'file://' + page],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            strip(out)
            print(os.path.relpath(out, HERE))


if __name__ == '__main__':
    for key in sys.argv[1:] or TEMPLATES:
        render(*TEMPLATES[key]())
