import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub = open(os.path.join(HERE, 'stub.js'), encoding='utf-8').read()
ok = True
def check(name, cond):
    global ok; ok = ok and bool(cond); print(('PASS ' if cond else 'FAIL ') + name)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 360, 'height': 780}, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/supabase.min.js', lambda r: r.fulfill(body=stub, content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}; localStorage.setItem('milteo_lang','ar')")
    pg.goto(URL); pg.wait_for_timeout(1000)
    check('Sprache ar: dir=rtl, lang=ar', pg.evaluate("document.documentElement.dir+','+document.documentElement.lang") == 'rtl,ar')
    check('Kachel «Einkauf» ist übersetzt', 'المشتريات' in pg.inner_text('body'))
    for tab in ['home', 'shop', 'todos', 'timers', 'events', 'chat', 'family']:
        pg.evaluate("switchTab('%s')" % tab); pg.wait_for_timeout(250)
        w = pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
        check('%s: kein Querscrollen %s' % (tab, w), w[0] <= w[1])
    ar = pg.evaluate("document.querySelectorAll('[data-i18n]').length")
    pg.evaluate("I18N.set('de')"); check('Zurück auf Deutsch: dir=ltr', pg.evaluate("document.documentElement.dir") == 'ltr')
    pg.evaluate("I18N.set('ar')"); check('Wieder Arabisch: dir=rtl', pg.evaluate("document.documentElement.dir") == 'rtl')
    check('Sprachwahl enthält العربية', pg.evaluate("I18N.LANGS.some(l=>l[0]==='ar'&&l[1]==='العربية')"))
    check('Einheiten: 2 EL → 2 م.ك', pg.evaluate("I18N.unit('2 EL')") == '2 م.ك')
    check('keine JS-Fehler: %s' % errs, not errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER'); sys.exit(0 if ok else 1)
