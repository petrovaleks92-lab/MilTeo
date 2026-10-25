import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub=open(os.path.join(HERE,'stub.js'),encoding='utf-8').read()
ok=True
def check(name, cond):
    global ok; ok = ok and bool(cond); print(('PASS ' if cond else 'FAIL ')+name)
URL=URL
def newpage(ctx, init=''):
    pg=ctx.new_page(); pg.errs=[]
    pg.on('pageerror',lambda e:pg.errs.append(str(e)))
    pg.route('**/supabase.min.js',lambda r:r.fulfill(body=stub,content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}};"+init)
    return pg
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':390,'height':780},has_touch=True,is_mobile=True)
    pg=newpage(ctx,"window.__empty=true"); pg.goto(URL); pg.wait_for_timeout(800)
    pg.evaluate("__db.entries=[]; loadEntries()"); pg.wait_for_timeout(600)
    # leere Ansichten mit Aktion
    pg.evaluate("switchTab('shop')"); t=pg.inner_text('#list-shop')
    check('Einkauf leer: Text + Knopf', 'noch leer' in t and pg.locator('#list-shop [data-go=shop]').count()==1)
    pg.click('#list-shop [data-go=shop]'); pg.wait_for_timeout(250)
    check('Knopf fokussiert das Eingabefeld', pg.evaluate("document.activeElement && document.activeElement.id")=='in-shop')
    pg.evaluate("switchTab('todos')"); check('Aufgaben leer', 'Erstelle eine Aufgabe' in pg.inner_text('#list-todos') and pg.locator('#list-todos [data-go=todos]').count()==1)
    pg.evaluate("switchTab('events')"); check('Termine leer', 'nächsten Termin' in pg.inner_text('#list-events'))
    pg.click('#list-events [data-go=events]'); pg.wait_for_timeout(250)
    check('Termin-Knopf öffnet Formular', pg.evaluate("!document.getElementById('fold-new').classList.contains('closed') && document.activeElement.id")=='in-etitle')
    pg.evaluate("switchTab('chat')"); check('Chat leer', 'Schreibe deiner Familie' in pg.inner_text('#list-chat'))
    pg.evaluate("switchTab('timers')"); check('Timer leer', 'Timer starten' in pg.inner_text('#list-timers'))
    pg.evaluate("switchTab('home')")
    check('Startseite ohne Aufgaben: keine Karte', pg.evaluate("document.getElementById('home-open').hidden"))
    # Menge hinzufügen
    pg.evaluate("switchTab('shop')")
    pg.click('#in-shop'); pg.keyboard.type('Milch'); pg.click('#in-shop-qty'); pg.keyboard.type('2 l'); pg.keyboard.press('Enter'); pg.wait_for_timeout(700)
    d=pg.evaluate("__db.entries.find(e=>e.data.text==='Milch').data")
    check('Menge gespeichert', d.get('qty')=='2 l')
    check('Felder geleert', pg.evaluate("$('in-shop').value==='' && $('in-shop-qty').value===''"))
    check('Menge sichtbar', '2 l' in pg.inner_text('#list-shop'))
    # ohne Menge
    pg.click('#in-shop'); pg.keyboard.type('Brot'); pg.keyboard.press('Enter'); pg.wait_for_timeout(600)
    check('ohne Menge: kein qty-Feld', 'qty' not in pg.evaluate("__db.entries.find(e=>e.data.text==='Brot').data"))
    # Bearbeiten per Antippen
    pg.click('[data-act=edit]:has-text("Milch")'); pg.wait_for_timeout(300)
    check('Editor erscheint mit Werten', pg.evaluate("document.querySelector('.ed-form .ed-t').textContent")=='Milch' and pg.evaluate("document.querySelector('.ed-form .ed-q').textContent")=='2 l')
    check('Editor-Felder sind normale Textflächen (kein Autofill)', pg.evaluate("document.querySelector('.ed-form .ed-t').isContentEditable"))
    # Realtime-Neuladen während des Bearbeitens zerstört die Eingabe nicht
    pg.evaluate("document.querySelector('.ed-form .ed-t').textContent='Vollmilch'")
    pg.evaluate("__db.entries.push({id:'zz',family_id:'f',kind:'shop',data:{text:'Eier',done:false},created_at:new Date().toISOString()}); loadEntries()"); pg.wait_for_timeout(700)
    check('Eingabe bleibt bei Neuladen erhalten', pg.evaluate("document.querySelector('.ed-form .ed-t')?.textContent")=='Vollmilch')
    pg.evaluate("document.querySelector('.ed-form .ed-q').textContent='3 l'")
    pg.focus('.ed-form .ed-t'); pg.keyboard.press('Enter'); pg.wait_for_timeout(700)
    d=pg.evaluate("__db.entries.find(e=>e.data.text==='Vollmilch')?.data")
    check('Bearbeiten gespeichert (Text + Menge)', d and d.get('qty')=='3 l')
    check('Editor geschlossen, neue Eintrag "Eier" sichtbar', pg.locator('.ed-form').count()==0 and 'Eier' in pg.inner_text('#list-shop'))
    # Menge entfernen, Abbrechen
    pg.click('[data-act=edit]:has-text("Vollmilch")'); pg.evaluate("document.querySelector('.ed-form .ed-q').textContent=''"); pg.focus('.ed-form .ed-t'); pg.keyboard.press('Enter'); pg.wait_for_timeout(600)
    check('Menge entfernt', 'qty' not in pg.evaluate("__db.entries.find(e=>e.data.text==='Vollmilch').data"))
    pg.click('[data-act=edit]:has-text("Brot")'); pg.click('[data-act=ed-cancel]'); pg.wait_for_timeout(300)
    check('Abbrechen ändert nichts', pg.locator('.ed-form').count()==0 and pg.evaluate("!!__db.entries.find(e=>e.data.text==='Brot')"))
    pg.click('[data-act=edit]:has-text("Brot")'); pg.evaluate("document.querySelector('.ed-form .ed-t').textContent=''"); pg.focus('.ed-form .ed-t'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    check('Leerer Text wird nicht gespeichert', pg.evaluate("!!__db.entries.find(e=>e.data.text==='Brot')") and pg.locator('.ed-form').count()==1)
    pg.click('[data-act=ed-cancel]')
    # Zutat im Gericht bearbeiten
    pg.evaluate("__db.entries.push({id:'d1',family_id:'f',kind:'shop',data:{type:'dish',text:'Lasagne',servings:4,items:[{name:'Hack',amount:'500 g',done:false},{name:'Tomaten',amount:'400 g',done:false}]},created_at:new Date().toISOString()}); openDishes.add('d1'); loadEntries()"); pg.wait_for_timeout(700)
    pg.click('[data-act=edit][data-id=d1][data-i="1"]'); pg.evaluate("document.querySelector('.ed-form .ed-t').textContent='Pelati'; document.querySelector('.ed-form .ed-q').textContent='800 g'"); pg.focus('.ed-form .ed-t'); pg.keyboard.press('Enter'); pg.wait_for_timeout(700)
    it=pg.evaluate("__db.entries.find(e=>e.id==='d1').data.items")
    check('Zutat bearbeitet (Name + Menge), andere unverändert', it[1]['name']=='Pelati' and it[1]['amount']=='800 g' and it[0]['name']=='Hack')
    # Startseite: Schnellaktionen + offene Aufgaben
    pg.evaluate("__db.entries.push({id:'t1',family_id:'f',kind:'todos',data:{text:'Fenster putzen',done:false},created_at:new Date().toISOString()}); loadEntries()"); pg.wait_for_timeout(600)
    pg.evaluate("switchTab('home')")
    check('Karte Offene Aufgaben', not pg.evaluate("document.getElementById('home-open').hidden") and 'Fenster putzen' in pg.inner_text('#home-open'))
    pg.click('#home-qa [data-go=todos]'); pg.wait_for_timeout(300)
    check('Schnellaktion: Aufgaben + Fokus', pg.evaluate("currentTab")=='todos' and pg.evaluate("document.activeElement.id")=='in-todos')
    # Zuletzt besuchte Seite
    pg.evaluate("switchTab('events')"); pg.evaluate("route({user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}})"); pg.wait_for_timeout(600)
    check('Anmelde-Ereignis beim Zurückkehren ändert die Seite nicht', pg.evaluate("currentTab")=='events')
    pg.reload(); pg.wait_for_timeout(900)
    check('Neustart öffnet die zuletzt besuchte Seite', pg.evaluate("currentTab")=='events')
    pg.go_back(); pg.wait_for_timeout(600)
    check('Zurück-Taste führt zur Startseite', pg.evaluate('currentTab')=='home')
    pg.evaluate("switchTab('chat')"); pg.reload(); pg.wait_for_timeout(800)
    check('Chat wird auch wiederhergestellt', pg.evaluate("currentTab")=='chat')
    check('keine JS-Fehler', not pg.errs); print(pg.errs)
    # Start ohne Verbindung
    pg2=newpage(ctx,"window.__failMembers=true; window.__failInit=true"); pg2.goto(URL); pg2.wait_for_timeout(900)
    check('Start ohne Verbindung: App öffnet mit Hinweis', pg2.evaluate("!document.getElementById('screen-app').hidden") and pg2.evaluate("!document.getElementById('net').hidden"))
    check('keine JS-Fehler (offline Start)', not pg2.errs); print(pg2.errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER')
