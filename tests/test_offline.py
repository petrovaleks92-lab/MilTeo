import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub=open(os.path.join(HERE,'stub8.js'),encoding='utf-8').read()
ok=True
def check(name, cond):
    global ok; ok = ok and bool(cond); print(('PASS ' if cond else 'FAIL ')+name)
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':390,'height':780},has_touch=True,is_mobile=True)
    pg=ctx.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase.min.js',lambda r:r.fulfill(body=stub,content_type='text/javascript'))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}")
    pg.goto(URL); pg.wait_for_timeout(800)
    check('Start ohne Banner', pg.evaluate("document.getElementById('net').hidden"))
    # 1) Normales Speichern klappt, Feld wird geleert
    pg.evaluate("switchTab('todos')")
    pg.click('#in-todos'); pg.keyboard.type('Zahnarzt anrufen'); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    check('online: Aufgabe gespeichert', pg.evaluate("__db.entries.some(e=>e.data.text==='Zahnarzt anrufen')"))
    check('online: Feld geleert', pg.evaluate("$('in-todos').value")=='')
    check('online: Eintrag sichtbar', 'Zahnarzt anrufen' in pg.inner_text('#list-todos'))
    # 2) Netz weg: Text bleibt stehen, Banner, Hinweis
    pg.evaluate("__fail=true")
    pg.click('#in-todos'); pg.keyboard.type('Brief schreiben'); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    check('offline: Text bleibt im Feld', pg.evaluate("$('in-todos').value")=='Brief schreiben')
    check('offline: nicht gespeichert', not pg.evaluate("__db.entries.some(e=>e.data.text==='Brief schreiben')"))
    check('offline: Banner sichtbar', not pg.evaluate("document.getElementById('net').hidden"))
    print('   Banner:', pg.inner_text('#net')); print('   Toast :', pg.inner_text('#toast'))
    # 3) Abhaken scheitert -> Anzeige springt zurück
    pg.click('[data-act=toggle][data-id=e0]'); pg.wait_for_timeout(400)
    check('offline: Abhaken zurückgesetzt', pg.evaluate("entries.find(e=>e.id==='e0').data.done")==False)
    check('offline: Anzeige zeigt nicht erledigt', pg.evaluate("document.querySelector('[data-act=toggle][data-id=e0]').getAttribute('aria-checked')")=='false')
    # 4) Löschen scheitert -> Eintrag kommt zurück
    pg.click('[data-act=del][data-id=e0]'); pg.wait_for_timeout(300)
    check('Löschen: vorerst weg (Rückgängig-Fenster)', pg.evaluate("!entries.some(e=>e.id==='e0')"))
    pg.evaluate("commitPending()"); pg.wait_for_timeout(500)
    check('offline: gelöschter Eintrag kehrt zurück', pg.evaluate("entries.some(e=>e.id==='e0')"))
    check('offline: Eintrag auch auf dem Server noch da', pg.evaluate("__db.entries.some(e=>e.id==='e0')"))
    # 5) Keine Toast-Flut beim Abfragen
    pg.evaluate("document.getElementById('toast').hidden=true")
    n0=pg.evaluate("__calls.length"); pg.evaluate("loadEntries()"); pg.wait_for_timeout(300)
    check('Abfrage offline zeigt keinen Toast', pg.evaluate("document.getElementById('toast').hidden"))
    # 6) Termin-Formular offline
    pg.evaluate("switchTab('events')"); pg.click('[data-fold=fold-new]')
    pg.click('#in-etitle'); pg.keyboard.type('Elternabend'); pg.fill('#in-edate','2030-05-05'); pg.click('#f-event button[type=submit]'); pg.wait_for_timeout(400)
    check('offline: Termintitel bleibt', pg.evaluate("$('in-etitle').value")=='Elternabend')
    # 7) Netz zurück
    pg.evaluate("__fail=false"); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.wait_for_timeout(600)
    check('online wieder: Banner weg', pg.evaluate("document.getElementById('net').hidden"))
    pg.click('#f-event button[type=submit]'); pg.wait_for_timeout(500)
    check('Termin nach Wiederverbindung gespeichert', pg.evaluate("__db.entries.some(e=>e.data.title==='Elternabend')"))
    check('Titel danach geleert', pg.evaluate("$('in-etitle').value")=='')
    pg.evaluate("switchTab('todos')"); pg.click('#in-todos'); pg.keyboard.type('Brief'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    # 8) Sprache: Banner übersetzt
    pg.evaluate("__fail=true; loadEntries()"); pg.wait_for_timeout(300)
    pg.evaluate("changeLang('fr')"); pg.wait_for_timeout(200)
    print('   FR Banner:', pg.inner_text('#net'))
    check('Banner französisch', 'Pas de connexion' in pg.inner_text('#net'))
    pg.evaluate("changeLang('de')")
    # 9) Doppelklick: nur ein Eintrag
    pg.evaluate("__fail=false; loadEntries()"); pg.wait_for_timeout(300)
    pg.evaluate("switchTab('shop')"); pg.click('#in-shop'); pg.keyboard.type('Brot')
    pg.evaluate("const f=document.getElementById('f-shop'); f.requestSubmit(); f.requestSubmit();"); pg.wait_for_timeout(600)
    check('Doppelt-Absenden: genau 1 Eintrag', pg.evaluate("__db.entries.filter(e=>e.data.text==='Brot').length")==1)
    check('keine JS-Fehler', not errs); print(errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER')
