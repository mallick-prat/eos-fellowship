"""Build index.html and apply.html from src/.

    python3 tools/build.py            # writes index.html and apply.html at the repo root
    python3 tools/build.py --preview  # also writes preview/ for the claude.ai artifact copy

Everything the pages need is inlined (images as data URIs), so each page is one
self-contained file. Edit src/site.json for sessions, the Sheet endpoint and the
tagline; src/links.json for LinkedIn/company links and mentor titles; and
src/templates/ for the page itself.
"""
import base64, html, json, os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
ASSETS = os.path.join(SRC, 'assets')
TEMPLATES = os.path.join(SRC, 'templates')

cfg = json.load(open(os.path.join(SRC, 'site.json'), encoding='utf-8'))
links = json.load(open(os.path.join(SRC, 'links.json'), encoding='utf-8'))
esc = lambda s: html.escape(s, quote=True)
read = lambda *p: open(os.path.join(*p), encoding='utf-8').read()


def data_uri(name):
    mime = {'webp': 'image/webp', 'png': 'image/png', 'jpg': 'image/jpeg'}[name.rsplit('.', 1)[1]]
    with open(os.path.join(ASSETS, name), 'rb') as f:
        return 'data:%s;base64,%s' % (mime, base64.b64encode(f.read()).decode())


def gcal(title, start, end, details, loc=''):
    q = {'action': 'TEMPLATE', 'text': title, 'dates': start + '/' + end, 'ctz': 'America/New_York', 'details': details}
    if loc:
        q['location'] = loc
    return 'https://calendar.google.com/calendar/render?' + urllib.parse.urlencode(q)


def session_cards():
    cards = []
    for s in cfg['sessions']:
        rsvp = 'https://partiful.com/e/' + s['partiful']
        d = s['date'].replace('-', '')
        cal = gcal('Eos Fellowship info session at ' + s['school'], d + 'T' + s['start'] + '00', d + 'T' + s['end'] + '00',
                   'RSVP: ' + rsvp, s['where'])
        # all sessions are in Eastern time after the Nov 1 DST change
        end_iso = '%sT%s:%s:00-05:00' % (s['date'], s['end'][:2], s['end'][2:])
        start_iso = '%sT%s:%s-05:00' % (s['date'], s['start'][:2], s['start'][2:])
        school = s['school']
        cards.append(f'''          <li class="session" data-end="{end_iso}">
            <a class="poster" href="{esc(rsvp)}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true"><img src="{data_uri(s['poster'])}" alt="" width="600" height="600"></a>
            <h3 class="s-school">{school}</h3>
            <p class="s-when"><time datetime="{start_iso}">{s['day']}</time> · <span class="nw">{s['time']}</span></p>
            <p class="s-where">{esc(s['where'] or 'Location shared after you RSVP')}</p>
            <div class="s-act"><a class="btn btn-rubric" href="{esc(rsvp)}" target="_blank" rel="noopener">RSVP<span class="sr"> for {school}</span> <span class="arr" aria-hidden="true">→</span></a><a class="s-cal" href="{esc(cal)}" target="_blank" rel="noopener">Add to calendar<span class="sr"> for {school}</span></a></div>
            <p class="s-past">This session has passed.</p>
          </li>''')
    return '\n'.join(cards)


def link_roster(body):
    """Names -> LinkedIn, affiliations -> company sites, mentor titles before the company."""
    def person(m):
        name = m.group(1)
        url = links['people'].get(name)
        if not url:
            return m.group(0)
        return f'<a class="nm" href="{esc(url)}" target="_blank" rel="noopener" title="{esc(name)} on LinkedIn">{name}</a>'
    body = re.sub(r'<span class="nm">([^<]+)</span>', person, body)

    def affiliation(m):
        parts = re.split(r'(, |/)', m.group(1))
        out = ''.join(
            p if p in (', ', '/') else
            (f'<a href="{esc(links["companies"][p])}" target="_blank" rel="noopener">{p}</a>' if p in links['companies'] else p)
            for p in parts)
        return f'<span class="af">{out}</span>'
    body = re.sub(r'<span class="af">([^<]+)</span>', affiliation, body)

    for name, title in links.get('titles', {}).items():
        body = body.replace(f'>{name}</a><span class="af">',
                            f'>{name}</a><span class="af"><span class="ti">{esc(title)}</span><span class="sep"> · </span>', 1)
    # organizer names in the info-sessions paragraph
    for name in ('Andrea Wang', 'Adam Zhou', 'Joshua Browder', 'Prat Mallick'):
        url = links['people'].get(name)
        if url:
            body = body.replace(name + ' (', f'<a href="{esc(url)}" target="_blank" rel="noopener" title="{esc(name)} on LinkedIn">{name}</a> (', 1)
    return body


SUBS = {
    'bgbg': data_uri('bgbg.png'), 'parchment': data_uri('parchment.jpg'), 'border': data_uri('border.webp'),
    'T': data_uri('t_scriptores_historiae_augustae.webp'), 'A': data_uri('a_scriptores_historiae_augustae.webp'),
    'E': data_uri('e_scriptores_historiae_augustae.webp'),
    'snail': data_uri('bruges_book_of_hours_1510-1525_snailberries_sm.webp'),
    'rabbit': data_uri('breviary_of_renaud_1302-1303_rabbit2_sm.webp'),
    'hedgehog': data_uri('book_of_hours_france_paris_1420-1425_hedgehog_sm.webp'),
    'bird': data_uri('french_book_of_hours_14birdreader_sm.webp'),
    'divider': data_uri('luttrell_bird_dividerpng_sm.webp'),
    'snailwoman': data_uri('heures_de_jacques_de_rambures_1460_snailwoman.webp'),
    'SUN_SIL': read(ASSETS, 'sun_sil.d'), 'SUN_INK': read(ASSETS, 'sun_ink.d'), 'WORD': read(ASSETS, 'word.d'),
    'SESSIONS': session_cards(),
}
HEAD, SCRIPT = read(TEMPLATES, 'head.html'), read(TEMPLATES, 'script.html')


def page(body, title, base, endpoint):
    p = (HEAD.replace('%%TITLE%%', title).replace('%%B%%', base)
         + link_roster(body) + SCRIPT.replace('%%SHEET_ENDPOINT%%', endpoint))
    for k, v in SUBS.items():
        p = p.replace('%%' + k + '%%', v)
    assert '%%' not in p, [l[:80] for l in p.splitlines() if '%%' in l][:3]
    return p


def hosted(p, og_title, path):
    """Full document with icons, canonical URL and link-preview tags in <head>."""
    p = p.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
    i = p.index('<svg class="defs"')
    head_part, body_part = p[:i], p[i:]
    base, desc = cfg['base_url'], cfg['tagline']
    url = base + '/' + path
    meta = f'''<link rel="canonical" href="{url}">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="theme-color" content="#121735">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Eos Fellowship">
<meta property="og:title" content="{esc(og_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{base}/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The gilded Eos sun beside the words Eos Fellowship, inside a medieval manuscript border">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(og_title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{base}/og.jpg">
'''
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}</style>\n'
            + meta + head_part + '</head><body>' + body_part + '</body></html>')


def write(path, text):
    with open(os.path.join(ROOT, path), 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'{path:28} {len(text.encode()):>9,} bytes')


index_body, apply_body = read(TEMPLATES, 'index.body.html'), read(TEMPLATES, 'apply.body.html')
endpoint = cfg['sheet_endpoint']
write('index.html', hosted(page(index_body, 'Eos Fellowship', '', endpoint), 'Eos Fellowship', ''))
write('apply.html', hosted(page(apply_body, 'Eos Fellowship Application', 'index.html', endpoint),
                           'Apply to the Eos Fellowship', 'apply.html'))

if '--preview' in sys.argv:
    # claude.ai artifact copy: the main page has no skeleton (the viewer adds one) and
    # the form has no endpoint, because the artifact sandbox blocks outside requests
    os.makedirs(os.path.join(ROOT, 'preview'), exist_ok=True)
    write('preview/eos-fellowship.html', page(index_body, 'Eos Fellowship', '', ''))
    write('preview/apply.html', '<!doctype html><html lang="en"><head><meta charset="utf-8">'
          '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
          '<style>:root{color-scheme:light}body{margin:0}img{max-width:100%}</style></head><body>'
          + page(apply_body, 'Eos Fellowship Application', 'index.html', '') + '</body></html>')
