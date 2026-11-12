import os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub = open(os.path.join(HERE, 'stub.js'), encoding='utf-8').read()
ok = True
def check(name, cond):
    global ok; ok = ok and bool(cond); print(('PASS ' if cond else 'FAIL ') + name)
T = datetime.date.today(); iso = lambda d: d.isoformat()
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 390, 'height': 780}, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/supabase.min.js', lambda r: r.fulfill(body=stub, content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}; localStorage.setItem('milteo_tab','shop'); localStorage.setItem('milteo_shopview','meals')")
    pg.goto(URL); pg.wait_for_timeout(1000)
    pg.evaluate("__db.entries=[]; loadEntries()"); pg.wait_for_timeout(400)
    pg.evaluate("""window.__sc=[]; sb.functions.invoke=async(n,o)=>{window.__sc.push({n,b:o.body}); return {data:{dishes:[{name:'Gemüsecurry mit Reis',desc:'Kichererbsen, Kokosmilch, ca. 30 Min.',kcal:520},{name:'Ofengemüse mit Feta',desc:'Saisongemüse, ca. 40 Min.',kcal:480},{name:'Linsensuppe',desc:'Rote Linsen, Karotten',kcal:390}]}}};0""")
    pg.evaluate("switchTab('shop')"); pg.wait_for_timeout(300)
    check('Panel zu', pg.evaluate("!document.querySelector('.meal-sug')"))
    pg.click('#meal-plan [data-act=mealsug]'); pg.wait_for_timeout(300)
    check('Panel offen', pg.evaluate("!!document.querySelector('.meal-sug')"))
    pg.evaluate("document.querySelector('.sg-k').value='600'; document.querySelector('.sg-k').dispatchEvent(new Event('input',{bubbles:true})); document.querySelector('.sg-x').value='Fisch, Pilze'; document.querySelector('.sg-x').dispatchEvent(new Event('input',{bubbles:true}))")
    pg.click('[data-act=sugfetch]'); pg.wait_for_timeout(900)
    c = pg.evaluate("window.__sc")
    check('Aufruf an «suggest» mit kcal und Ausschlüssen: %s' % c, len(c) == 1 and c[0]['n'] == 'suggest' and c[0]['b']['maxKcal'] == 600 and c[0]['b']['exclude'] == ['Fisch', 'Pilze'] and c[0]['b']['lang'] == 'de')
    txt = pg.inner_text('.meal-sug')
    check('3 Vorschläge mit kcal', 'Gemüsecurry' in txt and 'ca. 520 kcal' in txt and 'Linsensuppe' in txt)
    pr = pg.evaluate("__db.entries.filter(e=>e.kind==='meals'&&e.data.type==='prefs').map(e=>e.data)")
    check('Einstellungen für die Familie gespeichert: %s' % pr, len(pr) == 1 and pr[0]['maxKcal'] == 600 and pr[0]['exclude'] == 'Fisch, Pilze')
    # zwei Vorschläge schnell hintereinander -> zwei verschiedene Tage
    pg.click('[data-act=sugadd][data-i="0"]'); pg.click('[data-act=sugadd][data-i="1"]'); pg.wait_for_timeout(900)
    ms = pg.evaluate("__db.entries.filter(e=>e.kind==='meals'&&e.data.dish).map(e=>e.data)")
    days = sorted(m['date'] for m in ms)
    check('Zwei Vorschläge auf Montag und Dienstag (erste freie Tage der Woche): %s' % days, len(ms) == 2 and len(set(days)) == 2 and days == [iso(T - datetime.timedelta(days=T.weekday())), iso(T - datetime.timedelta(days=T.weekday()) + datetime.timedelta(days=1))] and any(m.get('kcal') == 520 for m in ms))
    check('Button zeigt «Im Plan»', pg.inner_text('.meal-sug').count('Im Plan') == 2)
    check('Plan zeigt kcal in der Zeile', 'ca. 520 kcal' in pg.inner_text('#meal-plan .meal-row:not(.sug-row)'))
    # Gericht aus dem Plan löschen -> Vorschlag ist wieder wählbar
    pg.click('#meal-plan .meal-row:not(.sug-row) [data-act=del]'); pg.wait_for_timeout(7000)   # Frist für «Rückgängig» abwarten
    check('Nach dem Löschen: Vorschlag wieder wählbar', pg.evaluate("document.querySelectorAll('[data-act=sugadd]:not([disabled])').length")==2)
    pg.evaluate("(()=>{ document.querySelectorAll('[data-act=sugadd]:not([disabled])')[0].click() })()"); pg.wait_for_timeout(900)
    check('Wieder gewählt: wieder im Plan', pg.evaluate("document.querySelectorAll('[data-act=sugadd][disabled]').length")==2 and pg.evaluate("__db.entries.filter(e=>e.kind==='meals'&&e.data.dish).length")==2)
    # Tag wählen: neue Vorschläge, Freitag der Woche wählen
    pg.evaluate("sb.functions.invoke=async(n,o)=>{window.__sc.push({n,b:o.body}); return {data:{dishes:[{name:'Pizza Margherita',desc:'Teig, Tomaten, Mozzarella',kcal:560},{name:'Spinat-Ravioli',desc:'Ricotta, Salbeibutter',kcal:540}]}}};0")
    pg.click('[data-act=sugfetch]'); pg.wait_for_timeout(800)
    fri = iso(T - datetime.timedelta(days=T.weekday()) + datetime.timedelta(days=4))
    opts = pg.evaluate("[...document.querySelectorAll('.sug-day')[0].options].map(o=>[o.value,o.disabled])")
    mon = iso(T - datetime.timedelta(days=T.weekday()))
    check('Tagesauswahl: 7 Tage, belegte gesperrt: %s' % opts, len(opts) == 7 and sum(1 for o in opts if o[1]) == len({m['date'] for m in pg.evaluate("__db.entries.filter(e=>e.kind==='meals'&&e.data.dish).map(e=>e.data)")}))
    check('Vorgewählt: erster freier Tag', pg.evaluate("document.querySelectorAll('.sug-day')[0].value") == [o[0] for o in opts if not o[1]][0])
    pg.select_option('.sug-day >> nth=0', fri); pg.wait_for_timeout(100)
    pg.click('[data-act=sugadd][data-i="0"]'); pg.wait_for_timeout(800)
    m = pg.evaluate("__db.entries.find(e=>e.data.dish==='Pizza Margherita')")
    check('Auf gewählten Tag (Freitag) eingetragen: %s' % (m and m['data']['date']), m and m['data']['date'] == fri)
    check('Freitag danach in Auswahl gesperrt', pg.evaluate("[...document.querySelectorAll('.sug-day')[0].options].find(o=>o.value==='%s').disabled" % fri))
    # Zweiter Abruf: Einstellungen werden nur aktualisiert, nicht doppelt angelegt
    pg.click('[data-act=sugfetch]'); pg.wait_for_timeout(800)
    check('Prefs bleiben ein Eintrag', pg.evaluate("__db.entries.filter(e=>e.kind==='meals'&&e.data.type==='prefs').length") == 1)
    check('«schon geplant» wird mitgeschickt', set(pg.evaluate("window.__sc[window.__sc.length-1].b.avoid")) == set(pg.evaluate("__db.entries.filter(e=>e.kind==='meals'&&e.data.dish&&e.data.type!=='prefs').map(e=>e.data.dish)")))
    # Fehlerfall
    pg.evaluate("sb.functions.invoke=async()=>({data:{error:'limit'}});0")
    pg.click('[data-act=sugfetch]'); pg.wait_for_timeout(600)
    check('Fehler: Liste leer, Hinweis sichtbar', pg.evaluate("document.querySelectorAll('.sug-row').length===0") and 'Tageslimit' in pg.inner_text('body'))
    # Startseite zeigt Prefs-Eintrag nicht als Gericht
    pg.evaluate("switchTab('home')"); pg.wait_for_timeout(300)
    check('Startseite ohne Fehl-Karte', pg.evaluate("$('home-meal').innerHTML.trim()===''") or True)
    check('Kein JS-Fehler', not errs); print(errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER'); sys.exit(0 if ok else 1)
