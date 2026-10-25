import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub=open(os.path.join(HERE,'stub7.js'),encoding='utf-8').read()
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
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}; window.__good='AltesPasswort9';")
    pg.goto(URL); pg.wait_for_timeout(800)
    # Passwortregeln
    r=pg.evaluate("['abc','12345678','aaaaaaaa','Passwort','password123','Sonne&Berg42'].map(pwProblem)")
    check('Regeln: kurz/Zahlen/gleich/bekannt abgelehnt', all(r[:5]) and r[5]=='')
    # Passwort ändern
    pg.evaluate("switchTab('family')"); pg.click('[data-fold=fold-acc]'); pg.click('#btn-pw')
    check('Formular erscheint', pg.locator('#f-pw').count()==1)
    pg.fill('#pw-cur','falsch'); pg.fill('#pw-new','Sonne&Berg42'); pg.fill('#pw-new2','Sonne&Berg42'); pg.click('#f-pw button'); pg.wait_for_timeout(400)
    print('   ',pg.inner_text('#pw-msg'))
    check('falsches aktuelles PW: Fehler, kein updateUser', 'stimmt nicht' in pg.inner_text('#pw-msg') and not pg.evaluate("window.__upd"))
    pg.fill('#pw-cur','AltesPasswort9'); pg.fill('#pw-new2','Anders&Berg42'); pg.click('#f-pw button'); pg.wait_for_timeout(300)
    check('ungleiche Wiederholung abgelehnt', 'stimmen nicht' in pg.inner_text('#pw-msg') and not pg.evaluate("window.__upd"))
    pg.fill('#pw-new','12345678'); pg.fill('#pw-new2','12345678'); pg.click('#f-pw button'); pg.wait_for_timeout(300)
    check('schwaches neues PW abgelehnt', 'einfach' in pg.inner_text('#pw-msg') and not pg.evaluate("window.__upd"))
    pg.fill('#pw-new','Sonne&Berg42'); pg.fill('#pw-new2','Sonne&Berg42'); pg.click('#f-pw button'); pg.wait_for_timeout(500)
    check('richtig: updateUser mit neuem PW', pg.evaluate("JSON.stringify(window.__upd)")=='[{"password":"Sonne&Berg42"}]')
    check('Formular danach weg', pg.locator('#f-pw').count()==0)
    # Registrierung mit schwachem Passwort
    # Konto löschen: falsches PW
    pg.click('#btn-del'); pg.fill('#del-pw','falsch'); pg.click('#f-del button'); pg.wait_for_timeout(400)
    check('Löschen falsches PW: kein rpc', not pg.evaluate("(window.__rpc||[]).includes('delete_my_account')") and 'stimmt nicht' in pg.inner_text('#del-msg'))
    # Server-Fehler
    pg.evaluate("window.__rpcErr=true"); pg.fill('#del-pw','AltesPasswort9'); pg.click('#f-del button'); pg.wait_for_timeout(500)
    print('   ',pg.inner_text('#del-msg'))
    check('Löschen Serverfehler: freundliche Meldung, bleibt in App', 'konnte nicht gelöscht' in pg.inner_text('#del-msg') and pg.evaluate("document.getElementById('screen-app').hidden")==False)
    check('keine technische Meldung sichtbar', 'fk violation' not in pg.inner_text('body'))
    # Erfolg
    pg.evaluate("window.__rpcErr=false; localStorage.setItem('milteo_x','1'); localStorage.setItem('milteo_lang','de')")
    pg.fill('#del-pw','AltesPasswort9'); pg.click('#f-del button'); pg.wait_for_timeout(4000)
    check('gelöscht: rpc aufgerufen', pg.evaluate("window.__rpc.includes('delete_my_account')"))
    check('gelöscht: Anmeldeseite sichtbar', pg.evaluate("!!document.getElementById('screen-auth') && !document.getElementById('screen-auth').hidden && document.getElementById('screen-auth').isConnected"))
    check('gelöscht: lokale Daten weg, Sprache bleibt', pg.evaluate("localStorage.getItem('milteo_x')===null && localStorage.getItem('milteo_lang')==='de'"))
    print('   Toast:', pg.inner_text('#toast'))
    # Registrierung schwach
    pg.click('#auth-toggle'); pg.fill('#in-name','X'); pg.fill('#in-email','x@y.ch'); pg.fill('#in-pw','12345678'); pg.click('#auth-submit'); pg.wait_for_timeout(300)
    check('Registrierung: schwaches PW blockiert', 'einfach' in pg.inner_text('#auth-msg') and not pg.evaluate("window.__signup"))
    pg.fill('#in-pw','kurz'); pg.click('#auth-submit'); pg.wait_for_timeout(200)
    check('Registrierung: <8 blockiert', '8 Zeichen' in pg.inner_text('#auth-msg'))
    pg.fill('#in-pw','Sonne&Berg42'); pg.click('#auth-submit'); pg.wait_for_timeout(300)
    check('Registrierung: gutes PW geht durch', bool(pg.evaluate("window.__signup")))
    check('keine JS-Fehler', not errs); print(errs)
    # Datenschutz sichtbar & französisch (neue Seite mit Sitzung)
    pg2=ctx.new_page(); pg2.route('**/supabase.min.js',lambda r:r.fulfill(body=stub,content_type='text/javascript')); pg2.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg2.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}; localStorage.setItem('milteo_lang','fr')")
    pg2.goto(URL); pg2.wait_for_timeout(800)
    pg2.evaluate("switchTab('family')"); pg2.click('[data-fold=fold-priv]'); pg2.wait_for_timeout(200)
    t=pg2.inner_text('#fold-priv'); print('   FR:', t[:260].replace('\n',' | '))
    check('Datenschutz auf Französisch', 'Protection des données' in t and 'Supabase' in t)
    pg2.screenshot(path='n2.png', full_page=True)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER')
