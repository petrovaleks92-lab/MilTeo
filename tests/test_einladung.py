import os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub=open(os.path.join(HERE,'stub.js'),encoding='utf-8').read()
ok=True
def check(n,c):
    global ok; ok = ok and bool(c); print(('PASS ' if c else 'FAIL ')+n)
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':390,'height':780},has_touch=True,is_mobile=True)
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase.min.js',lambda r:r.fulfill(body=stub,content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}; window.__opened=[]; window.open=(u)=>{window.__opened.push(u); return null}; Object.defineProperty(navigator,'share',{value:undefined})")
    pg.goto(URL); pg.wait_for_timeout(1000)
    pg.evaluate("__db.entries=[]; loadEntries()"); pg.wait_for_timeout(500)
    check('Einführung bei leerer Familie sichtbar', pg.evaluate("!$('home-intro').hidden"))
    pg.click('#home-intro-ok'); pg.wait_for_timeout(200)
    check('Einführung weg nach «Verstanden»', pg.evaluate("$('home-intro').hidden"))
    pg.reload(); pg.wait_for_timeout(1000); pg.evaluate("__db.entries=[]; loadEntries()"); pg.wait_for_timeout(500)
    check('Einführung bleibt weg nach Neuladen', pg.evaluate("$('home-intro').hidden"))
    pg.evaluate("memberCount=1; document.getElementById('fam-code').textContent='ABC123'; renderHome()")
    check('Einladungs-Karte sichtbar wenn allein', pg.evaluate("!$('home-invite').hidden"))
    pg.click('#home-wa'); pg.wait_for_timeout(200)
    u=pg.evaluate("window.__opened[0]||''")
    check('WhatsApp-Link mit Code '+u[:60], u.startswith('https://wa.me/?text=') and 'ABC123' in u)
    pg.evaluate("memberCount=3; renderHome()")
    check('Einladungs-Karte weg bei mehreren Mitgliedern', pg.evaluate("$('home-invite').hidden"))
    pg.evaluate("window.__opened=[]"); pg.evaluate("switchTab('family')"); pg.wait_for_timeout(300); pg.click('#fam-wa'); pg.wait_for_timeout(200)
    check('WhatsApp-Knopf im Familien-Bereich', pg.evaluate("window.__opened.length")==1)
    check('Keine JS-Fehler '+str(errs), not errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER'); raise SystemExit(0 if ok else 1)
