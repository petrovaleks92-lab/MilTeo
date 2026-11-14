import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub = open(os.path.join(HERE, 'stub.js'), encoding='utf-8').read()
ok = True
def check(name, cond):
    global ok; ok = ok and bool(cond); print(('PASS ' if cond else 'FAIL ') + name)
INIT = """window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}};
Object.defineProperty(window,'PushManager',{value:function(){},configurable:true});
Object.defineProperty(Notification,'permission',{get:()=>'denied',configurable:true});
Notification.requestPermission=async()=>'denied';"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for twa in (False, True):
        ctx = b.new_context(viewport={'width': 390, 'height': 780}); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route('**/supabase.min.js', lambda r: r.fulfill(body=stub, content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
        pg.add_init_script(INIT + ("sessionStorage.setItem('milteo_twa','1');" if twa else ""))
        pg.goto(URL); pg.wait_for_timeout(1000)
        pg.evaluate("switchTab('family')"); pg.wait_for_timeout(500)
        pg.evaluate("refreshPushUI()"); pg.wait_for_timeout(300)
        txt = pg.inner_text('#push-status')
        check('TWA=%s: Schalter steht auf Aus bei blockiert' % twa, not pg.evaluate("document.getElementById('sw-push').checked"))
        check('TWA=%s: Hinweistext passend (%s)' % (twa, txt[:50]), ('Android' in txt) == twa and 'blockiert' in txt)
        check('TWA=%s: keine JS-Fehler %s' % (twa, errs), not errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER'); sys.exit(0 if ok else 1)
