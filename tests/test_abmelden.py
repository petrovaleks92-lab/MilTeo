import os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
base = open(os.path.join(HERE, 'stub7.js'), encoding='utf-8').read()
extra = """
(() => { const o = window.supabase.createClient;
  window.supabase.createClient = (...a) => { const c = o(...a); let cb = null; window.__so = [];
    c.auth.onAuthStateChange = (f) => { cb = f; return {data:{subscription:{}}}; };
    c.auth.getSession = async () => ({ data: { session: window.__sess || null } });
    c.auth.signOut = async (opt) => { window.__so.push(opt && opt.scope || 'global');
      if (window.__netfail && !(opt && opt.scope === 'local')) return { error: { message: 'Failed to fetch' } };
      if (window.__hang && !(opt && opt.scope === 'local')) return new Promise(() => {});
      window.__sess = null; if (cb) cb('SIGNED_OUT', null); return { error: null }; };
    return c; }; })();
"""
stub = base + extra
ok = True
def check(n, c):
    global ok; ok = ok and bool(c); print(('PASS ' if c else 'FAIL ') + n)
vis = lambda pg, i: pg.evaluate("(i)=>{const e=document.getElementById(i);return !!e&&!e.hidden&&e.isConnected}", i)
def run(b, flag):
    pg = b.new_context(viewport={'width': 390, 'height': 780}, has_touch=True, is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/supabase.min.js', lambda r: r.fulfill(body=stub, content_type='text/javascript'))
    pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}};" + flag)
    pg.goto(URL); pg.wait_for_timeout(800); pg.evaluate("switchTab('family')"); pg.click('#btn-logout')
    return pg, errs
with sync_playwright() as p:
    b = p.chromium.launch()
    pg, errs = run(b, ''); pg.wait_for_timeout(2500)
    check('normal: Startseite nach Abmelden', vis(pg, 'screen-landing') and not errs)
    pg, errs = run(b, 'window.__netfail=true;'); pg.wait_for_timeout(2500)
    check('Netzfehler: trotzdem abgemeldet (lokal)', vis(pg, 'screen-landing') and 'local' in pg.evaluate('window.__so'))
    pg, errs = run(b, 'window.__hang=true;'); pg.wait_for_timeout(8000)
    check('Server antwortet nicht: nach 5 s lokal abgemeldet', vis(pg, 'screen-landing') and 'local' in pg.evaluate('window.__so'))
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER'); raise SystemExit(0 if ok else 1)
