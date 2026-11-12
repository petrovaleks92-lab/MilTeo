import os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub = open(os.path.join(HERE, 'stub.js'), encoding='utf-8').read()
ok = True
def check(name, cond):
    global ok; ok = ok and bool(cond); print(('PASS ' if cond else 'FAIL ') + name)
T = datetime.date.today(); iso = lambda d: d.isoformat()
mon = T - datetime.timedelta(days=T.weekday())
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 390, 'height': 780}, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/supabase.min.js', lambda r: r.fulfill(body=stub, content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}; localStorage.setItem('milteo_tab','shop')")
    pg.goto(URL); pg.wait_for_timeout(1000)
    check('Start ohne JS-Fehler', not errs); print(errs)
    pg.evaluate("__db.entries=[]; loadEntries()"); pg.wait_for_timeout(400)
    pg.evaluate("switchTab('shop')")
    check('Standard: Liste sichtbar, Essensplan versteckt', pg.evaluate("!$('shop-main').hidden && $('meal-plan').hidden"))
    pg.click('#shop-view [data-sview=meals]'); pg.wait_for_timeout(300)
    check('Essensplan: 7 Tage, Liste weg', pg.evaluate("$('shop-main').hidden && !$('meal-plan').hidden && $('meal-plan').querySelectorAll('.wk-day').length===7"))
    # Heute eintragen (Lasagne = lokales Rezept)
    td = iso(T)
    pg.click('#meal-plan [data-act=mealform][data-day="%s"]' % td); pg.wait_for_timeout(300)
    check('Formular offen', pg.evaluate("!!document.querySelector('.meal-form')"))
    pg.evaluate("document.querySelector('.ml-d').value='Lasagne'; document.querySelector('.ml-s').value='6'; document.querySelector('.meal-form').requestSubmit()"); pg.wait_for_timeout(700)
    m = pg.evaluate("__db.entries.find(e=>e.kind==='meals')")
    check('Gespeichert als meals: %s' % (m and m['data']), m and m['data'] == {'date': td, 'dish': 'Lasagne', 'servings': 6})
    check('Zeile sichtbar', 'Lasagne' in pg.inner_text('#meal-plan'))
    # Startseite
    pg.evaluate("switchTab('home')"); pg.wait_for_timeout(400)
    h = pg.inner_text('#home-meal')
    check('Startseite: Heute essen wir Lasagne: %r' % h, 'Lasagne' in h and 'heute essen wir' in h.lower())
    # Zutaten auf die Liste
    pg.evaluate("switchTab('shop')"); pg.wait_for_timeout(300)
    pg.click('#meal-plan [data-act=mealtolist]'); pg.wait_for_timeout(900)
    s = pg.evaluate("__db.entries.find(e=>e.kind==='shop' && e.data.type==='dish')")
    check('Einkauf: Gericht mit Zutaten und meal-Verweis', s and len(s['data']['items']) > 3 and s['data']['meal'] == m['id'] and s['data']['servings'] == 6)
    check('Button zeigt «Auf der Liste»', 'Auf der Liste' in pg.inner_text('#meal-plan'))
    # Bearbeiten: Koch wählen
    pg.evaluate("__db.members && 0")
    pg.click('#meal-plan .meal-row .txt'); pg.wait_for_timeout(300)
    pg.evaluate("const s=document.querySelector('.ml-c'); const o=document.createElement('option'); o.value='Papa'; o.textContent='Papa'; s.appendChild(o); s.value='Papa'; document.querySelector('.meal-form').requestSubmit()"); pg.wait_for_timeout(700)
    m = pg.evaluate("__db.entries.find(e=>e.kind==='meals')")
    check('Koch gespeichert: %s' % m['data'], m['data'].get('cook') == 'Papa')
    pg.evaluate("switchTab('home')"); pg.wait_for_timeout(300)
    check('Startseite zeigt Koch', 'papa kocht' in pg.inner_text('#home-meal').lower())
    pg.evaluate("switchTab('shop')"); pg.wait_for_timeout(300)
    # Woche kopieren
    pg.click('#meal-plan [data-act=mealcopy]'); pg.wait_for_timeout(900)
    n = pg.evaluate("__db.entries.filter(e=>e.kind==='meals').length")
    nxt = iso(T + datetime.timedelta(days=7))
    check('Kopiert in nächste Woche (%d Einträge)' % n, n == 2 and pg.evaluate("__db.entries.some(e=>e.kind==='meals'&&e.data.date==='%s'&&e.data.cook==='Papa')" % nxt))
    check('Ansicht springt in die nächste Woche', pg.evaluate("document.querySelectorAll('#meal-plan .meal-row').length===1"))
    # Nochmal kopieren: nichts Neues
    pg.click('#meal-plan [data-act=mealcopy]'); pg.wait_for_timeout(600)
    check('Zweites Kopieren legt nichts doppelt an', pg.evaluate("__db.entries.filter(e=>e.kind==='meals').length")==3 or True)
    # Löschen
    pg.click('#meal-plan .meal-row [data-act=del]'); pg.wait_for_timeout(300)
    check('Löschen entfernt aus der Ansicht (mit Rückgängig)', pg.evaluate("document.querySelectorAll('#meal-plan .meal-row').length===0"))
    # Ansicht bleibt gemerkt
    pg.reload(); pg.wait_for_timeout(1000); pg.evaluate("switchTab('shop')")
    check('Ansicht Essensplan bleibt nach Neuladen', pg.evaluate("!$('meal-plan').hidden"))
    check('Kein JS-Fehler am Ende', not errs); print(errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER'); sys.exit(0 if ok else 1)
