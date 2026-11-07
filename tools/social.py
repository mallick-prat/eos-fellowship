"""Render the social card (og.jpg), the home-screen icons (from the gold sun miniature) and the
browser-tab icons (from the logo's sun in Eos blue).

    python3 tools/social.py            # writes og.jpg, icon-192.png, apple-touch-icon.png, apple-touch-icon-precomposed.png,
                                       # and the tab icons favicon.svg, favicon.ico, favicon-32.png
    python3 tools/social.py --out DIR  # write somewhere else instead of the repo root

Needs Google Chrome (headless screenshots) and ImageMagick (`magick`) on the PATH or at
their usual macOS locations. The card's tagline comes from src/site.json.
"""
import base64, json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'src', 'assets')
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else ROOT
CHROME = shutil.which('google-chrome') or '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
MAGICK = shutil.which('magick') or 'magick'
tagline = json.load(open(os.path.join(ROOT, 'src', 'site.json'), encoding='utf-8'))['tagline']


def uri(name, mime):
    with open(os.path.join(ASSETS, name), 'rb') as f:
        return 'data:%s;base64,%s' % (mime, base64.b64encode(f.read()).decode())


sil = open(os.path.join(ASSETS, 'sun_sil.d')).read()
ink = open(os.path.join(ASSETS, 'sun_ink.d')).read()
diaper, parch, border = uri('bgbg.png', 'image/png'), uri('parchment.jpg', 'image/jpeg'), uri('border.webp', 'image/webp')
fonts = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Texturina:ital,opsz,wght@0,12..72,400;1,12..72,400&family=UnifrakturMaguntia&display=swap">'
gilt = ('<linearGradient id="gilt" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8a5e17"/><stop offset=".2" stop-color="#d9ad48"/>'
        '<stop offset=".34" stop-color="#f6e3a0"/><stop offset=".47" stop-color="#cf9f39"/><stop offset=".63" stop-color="#9c6b1c"/>'
        '<stop offset=".79" stop-color="#e8c76f"/><stop offset="1" stop-color="#a9781f"/></linearGradient>')
sun = (f'<svg viewBox="136 213 640 652" style="width:100%;height:auto;display:block;filter:drop-shadow(0 2px 2px rgba(0,0,0,.45))">'
       f'<defs>{gilt}</defs><path d="{sil}" fill="url(#gilt)"/><path d="{ink}" fill="#3a230e" fill-rule="evenodd"/></svg>')

# Tab icon: the logo's sun in Eos blue on a cream body. The gold miniature turns into a brown dot at
# 16px, and plain blue lines vanish on a dark tab bar; the cream body keeps it visible on both.
BLUE, CREAM = '#0D4285', '#f8f1de'
tab_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="118 201 676 676">'
           f'<path d="{sil.strip()}" fill="{CREAM}" stroke="{BLUE}" stroke-width="6" stroke-linejoin="round"/>'
           f'<path d="{ink.strip()}" fill="{BLUE}" fill-rule="evenodd"/></svg>\n')


def miniature(size, frame, pad, tile):
    return f'''<div style="width:{size}px;height:{size}px;box-sizing:border-box;padding:{pad}px;display:grid;place-items:center;
      background-color:#101c52;background-image:radial-gradient(circle,rgba(16,28,82,0) 38%,rgba(4,8,30,.55) 100%),url({diaper});background-size:100% 100%,{tile}px;
      border:{frame}px solid;border-image:linear-gradient(135deg,#7b5414,#f3dc8d 28%,#c89a33 46%,#7b5414 64%,#f3dc8d 84%,#c89a33) 1;
      box-shadow:0 0 0 {max(1, frame // 6)}px #2a1e16,inset 0 0 0 {max(1, frame // 4)}px rgba(255,246,222,.6)">{sun}</div>'''


k = .66  # border scale on the card
card = f'''<!doctype html><html><head><meta charset="utf-8">{fonts}<style>
html,body{{margin:0;width:1200px;height:630px;overflow:hidden}}
body{{background:#e6dfcb url({parch});background-size:450px;box-shadow:inset 0 0 90px rgba(112,80,30,.45);display:grid;place-items:center}}
.frame{{box-sizing:border-box;width:1164px;height:594px;border-style:solid;border-color:transparent;
  border-width:{120*k}px {165*k}px {180*k}px {110*k}px;border-image:url({border}) 120 165 180 110 round;
  display:flex;align-items:center;justify-content:center;gap:46px;padding:0 20px}}
h1{{margin:0;font:400 104px/0.95 "UnifrakturMaguntia",serif;color:#2a1e16;white-space:nowrap}}
h1 span{{color:#26448c}}
p{{margin:20px 0 0;max-width:600px;font:italic 400 34px/1.3 "Texturina",serif;color:#a8291b;text-wrap:balance}}
</style></head><body><div class="frame">{miniature(232, 8, 16, 44)}<div><h1><span>E</span>os Fellowship</h1>
<p>{tagline}</p></div></div></body></html>'''
icon = f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;background:#101c52}}</style></head><body>{miniature(512, 26, 40, 150)}</body></html>'

tmp = tempfile.mkdtemp()
def shot(html_text, name, w, h, transparent=False):
    src, png = os.path.join(tmp, name + '.html'), os.path.join(tmp, name + '.png')
    open(src, 'w', encoding='utf-8').write(html_text)
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--user-data-dir={tmp}/profile',
                    *(['--default-background-color=00000000'] if transparent else []),
                    '--virtual-time-budget=8000', f'--window-size={w},{h}', f'--screenshot={png}', 'file://' + src],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return png

card_png, icon_png = shot(card, 'card', 1200, 630), shot(icon, 'icon', 512, 512)
tab_png = shot('<!doctype html><html><body style="margin:0;background:transparent">'
               + tab_svg.replace('<svg ', '<svg width="512" height="512" ', 1) + '</body></html>', 'tab', 512, 512, transparent=True)
os.makedirs(OUT, exist_ok=True)
o = lambda n: os.path.join(OUT, n)
subprocess.run([MAGICK, card_png, '-strip', '-quality', '88', '-sampling-factor', '4:2:0', o('og.jpg')], check=True)
subprocess.run([MAGICK, icon_png, '-resize', '192x192', o('icon-192.png')], check=True)
subprocess.run([MAGICK, icon_png, '-resize', '180x180', o('apple-touch-icon.png')], check=True)
shutil.copyfile(o('apple-touch-icon.png'), o('apple-touch-icon-precomposed.png'))  # older iOS asks for this name
open(o('favicon.svg'), 'w', encoding='utf-8').write(tab_svg)
subprocess.run([MAGICK, tab_png, '-filter', 'Lanczos', '-resize', '32x32', o('favicon-32.png')], check=True)
subprocess.run([MAGICK, tab_png, '-filter', 'Lanczos', '-define', 'icon:auto-resize=48,32,16', o('favicon.ico')], check=True)
shutil.rmtree(tmp, ignore_errors=True)
print('wrote og.jpg and icons to', OUT)
