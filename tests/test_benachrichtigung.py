import os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
base = open(os.path.join(HERE, 'stub7.js'), encoding='utf-8').read()
extra = """
(() => { const o = window.supabase.createClient; window.__inv = [];
  window.supabase.createClient = (...a) => { const c = o(...a);
    c.functions.invoke = async (n, opt) => { window.__inv.push([n, opt && opt.body]); return {data:{}, error: window.__invErr ? {message:'x'} : null}; };
    return c; }; })();
"""
stub = base + extra
ok = True
def check(n, c):
    global ok; ok = ok and bool(c); print(('PASS ' if c else 'FAIL ') + n)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_context(viewport={'width': 390, 'height': 780}, has_touch=True, is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/supabase.min.js', lambda r: r.fulfill(body=stub, content_type='text/javascript'))
    pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}};")
    pg.goto(URL); pg.wait_for_timeout(800)
    pg.evaluate("memberCount = 3; switchTab('shop')")
    pg.fill('#in-shop', 'Brot'); pg.press('#in-shop', 'Enter'); pg.wait_for_timeout(300)
    pg.fill('#in-shop', 'Käse'); pg.press('#in-shop', 'Enter'); pg.wait_for_timeout(500)
    check('sofort noch keine Mitteilung (wird gesammelt)', pg.evaluate("window.__inv.length") == 0)
    pg.wait_for_timeout(4500)
    inv = pg.evaluate("window.__inv")
    print('   ', inv)
    check('nach 4 s genau EIN notify-Aufruf mit beiden Einträgen', len(inv) == 1 and inv[0][0] == 'notify' and len(inv[0][1]['entry_ids']) == 2)
    pg.evaluate("memberCount = 1; window.__inv = []"); pg.fill('#in-shop', 'Milch'); pg.press('#in-shop', 'Enter'); pg.wait_for_timeout(5000)
    check('allein in der Familie: keine Mitteilung', pg.evaluate("window.__inv.length") == 0)
    pg.evaluate("switchTab('family')")
    check('Schalter «Änderungen der Familie» vorhanden', pg.locator('#sw-change').count() == 1)
    check('Link #shop öffnet Einkauf', pg.evaluate("(()=>{location.hash='#shop'; return startTab()})()") == 'shop')
    check('keine JS-Fehler', not errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER'); raise SystemExit(0 if ok else 1)
