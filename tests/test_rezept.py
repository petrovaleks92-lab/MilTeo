import os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
base = open(os.path.join(HERE, 'stub7.js'), encoding='utf-8').read()
extra = """
window.__db.entries.find(e => e.id === 'e2').data.steps = ['Backofen auf 180 °C (Ober-/Unterhitze) vorheizen.', 'Hackfleisch 8 Minuten anbraten.', 'Im Ofen 25 Minuten backen, danach 10 Min. ruhen lassen.', 'Servieren.'];
"""
stub = base + extra
ok = True
def check(n, c):
    global ok; ok = ok and bool(c); print(('PASS ' if c else 'FAIL ') + n)
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 900}, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/supabase.min.js', lambda r: r.fulfill(body=stub, content_type='text/javascript'))
    pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}};")
    pg.goto(URL); pg.wait_for_timeout(800); pg.evaluate("switchTab('shop')"); pg.wait_for_timeout(300)
    pg.click('[data-act=dish][data-id=e2]'); pg.wait_for_timeout(200)
    pg.click('[data-act=recipe][data-id=e2]'); pg.wait_for_timeout(300)
    check('Schritte sichtbar', pg.locator('li.step').count() == 4)
    tts = pg.locator('.step .tt').all_inner_texts(); print('   hervorgehoben:', tts)
    check('Temperatur und Zeiten hervorgehoben', any('180' in t for t in tts) and any('25 Minuten' in t for t in tts) and any('10 Min' in t for t in tts))
    info = pg.inner_text('.rinfo'); print('   Auf einen Blick:', info.replace('\n', ' '))
    check('«Auf einen Blick» zeigt Temperatur und Zeit', '180' in info and '25 Minuten' in info)
    pg.click('li.step[data-i="0"]'); pg.click('li.step[data-i="2"]'); pg.wait_for_timeout(200)
    check('2 Schritte abgehakt', pg.locator('li.step.done').count() == 2)
    pg.reload(); pg.wait_for_timeout(900); pg.evaluate("switchTab('shop')"); pg.wait_for_timeout(300)
    check('nach Neuladen: Rezept noch offen', pg.locator('li.step').count() == 4)
    done = pg.evaluate("[...document.querySelectorAll('li.step.done')].map(e=>e.dataset.i)")
    check('nach Neuladen: Häkchen 1 und 3 erhalten', done == ['0', '2'])
    pg.on('dialog', lambda d: d.accept())
    pg.click('[data-act=recipe-new][data-id=e2]'); pg.wait_for_timeout(500)
    check('«Rezept neu erstellen» löscht Häkchen', pg.evaluate("JSON.parse(localStorage.getItem('milteo_recipe_state')).d").__len__() == 0)
    check('keine JS-Fehler', not errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER'); raise SystemExit(0 if ok else 1)
