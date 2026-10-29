import os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub = open(os.path.join(HERE, 'stub.js'), encoding='utf-8').read()
ok = True
def check(n, c):
    global ok; ok = ok and bool(c); print(('PASS ' if c else 'FAIL ') + n)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 390, 'height': 780})
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    msgs = []; accept = {'v': False}
    def on_dialog(d):
        msgs.append(d.message); (d.accept() if accept['v'] else d.dismiss())
    pg.on('dialog', on_dialog)
    pg.route('**/supabase.min.js', lambda r: r.fulfill(body=stub, content_type='text/javascript'))
    pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}")
    pg.goto(URL); pg.wait_for_timeout(1000)
    pg.evaluate("window.__calls=0; sb.functions.invoke=async(n,o)=>{if(o&&o.body&&o.body.mode==='extract')window.__calls++; return {data:{events:[]}}}")
    run = "(async()=>{const f=new File(['x'],'a.pdf',{type:'application/pdf'}); const r=await extractFrom(f,'events'); return r})()"
    r = pg.evaluate(run)
    check('Frage erscheint vor dem ersten Upload', len(msgs) == 1 and 'Google' in msgs[0])
    check('Abgelehnt: nichts gesendet', r.get('error') == 'cancel' and pg.evaluate('window.__calls') == 0)
    accept['v'] = True
    r = pg.evaluate(run)
    check('Zugestimmt: wird gesendet', pg.evaluate('window.__calls') == 1 and not r.get('error'))
    r = pg.evaluate(run)
    check('Frage kommt nicht nochmals', len(msgs) == 2 and pg.evaluate('window.__calls') == 2)
    check('Datenschutz: Chat nicht an Google', 'Nachrichten im Chat werden nicht an Google gesendet' in pg.evaluate("document.getElementById('priv-body').textContent"))
    check('Keine JS-Fehler', not errs); print(errs)
    b.close()
print('OK' if ok else 'FEHLER'); raise SystemExit(0 if ok else 1)
