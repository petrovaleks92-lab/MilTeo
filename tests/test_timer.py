import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub=open(os.path.join(HERE,'stub.js'),encoding='utf-8').read(); ok=True
def check(n,c):
    global ok; ok=ok and bool(c); print(('PASS ' if c else 'FAIL ')+n)
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':390,'height':780},has_touch=True,is_mobile=True)
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase.min.js',lambda r:r.fulfill(body=stub,content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}; localStorage.setItem('milteo_tab','timers')")
    pg.goto(URL); pg.wait_for_timeout(900)
    pg.evaluate("__db.entries=[]; loadEntries()"); pg.wait_for_timeout(400)
    pg.evaluate("$('in-tlabel').value='Ofen'; $('in-tmin').value='10'; $('f-timer').requestSubmit()"); pg.wait_for_timeout(700)
    d=pg.evaluate("__db.entries.find(e=>e.kind==='timers').data"); check('Dauer gespeichert', d.get('dur')==600000)
    pg.click('[data-act=tpause]'); pg.wait_for_timeout(500)
    d=pg.evaluate("__db.entries.find(e=>e.kind==='timers').data"); check('Pausiert: Rest gespeichert, Ende weit weg', d['paused'] and 590000<=d['left']<=600000 and d['end']>Date_now if False else d['paused'] and 590000<=d['left']<=600000)
    check('Anzeige Pausiert', 'Pausiert' in pg.inner_text('#list-timers'))
    pg.wait_for_timeout(1500); l1=pg.evaluate("__db.entries[0].data.left")
    check('Rest läuft nicht weiter', l1==d['left'])
    pg.evaluate("switchTab('home')"); pg.wait_for_timeout(300); check('Startseite: pausiert', 'pausiert' in pg.inner_text('#ti-timers'))
    pg.evaluate("switchTab('timers')"); pg.click('[data-act=tplus]'); pg.wait_for_timeout(500)
    d2=pg.evaluate("__db.entries[0].data"); check('+1 Minute im Pausenmodus', d2['left']==d['left']+60000)
    pg.click('[data-act=tresume]'); pg.wait_for_timeout(500)
    d3=pg.evaluate("__db.entries[0].data"); check('Fortgesetzt', (not d3['paused']) and 0<d3['end']-pg.evaluate("Date.now()")<=d2['left']+500 and 'left' not in d3)
    pg.evaluate("__db.entries[0].data.end=Date.now()-1000; loadEntries()"); pg.wait_for_timeout(700)
    check('Abgelaufen: Nochmal-Knopf', pg.locator('[data-act=trestart]').count()==1)
    pg.click('[data-act=trestart]'); pg.wait_for_timeout(500)
    d4=pg.evaluate("__db.entries[0].data"); check('Nochmal startet volle Dauer', 590000<d4['end']-pg.evaluate("Date.now()")<=600500 and d4['notified']==False)
    check('keine JS-Fehler', not errs); print(errs); b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER')
