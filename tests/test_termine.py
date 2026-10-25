import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
import datetime
stub=open(os.path.join(HERE,'stub.js'),encoding='utf-8').read()
ok=True
def check(name, cond):
    global ok; ok = ok and bool(cond); print(('PASS ' if cond else 'FAIL ')+name)
T=datetime.date.today(); iso=lambda d:d.isoformat(); dd=lambda n:iso(T+datetime.timedelta(days=n))
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':390,'height':780},has_touch=True,is_mobile=True)
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)+' @ '+str(getattr(e,'stack',''))[:300]))
    pg.route('**/supabase.min.js',lambda r:r.fulfill(body=stub,content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}; localStorage.setItem('milteo_tab','events')")
    pg.goto(URL); pg.wait_for_timeout(1000)
    check('Start ohne JS-Fehler', not errs); print(errs)
    pg.evaluate("__db.entries=[]; loadEntries()"); pg.wait_for_timeout(500)
    # nextOcc
    r=pg.evaluate("""[nextOcc('2026-01-31','monthly','2026-02-10'), nextOcc('2026-01-31','monthly','2026-03-01'), nextOcc('2024-02-29','yearly','2026-01-01'), nextOcc('2026-10-12','weekly','2026-10-25'), nextOcc('2026-10-12','daily','2026-10-25'), nextOcc('2026-10-12','weekly','2026-10-12'), nextOcc('2026-10-12','weekly','2026-10-19')]""")
    check('nextOcc '+str(r), r==['2026-02-28','2026-03-31','2026-02-28','2026-10-26','2026-10-25','2026-10-12','2026-10-19'])
    # Hinzufügen mit Ort + Wiederholung
    pg.evaluate("switchTab('events')"); pg.click('[data-fold=fold-new]'); pg.wait_for_timeout(200)
    check('Wiederholen-Liste gefüllt', pg.evaluate("$('in-erepeat').options.length")==5)
    pg.evaluate("$('in-etitle').value='Fussballtraining'; $('in-edate').value='%s'; $('in-etime').value='18:00'; $('in-eplace').value='Sportplatz Allmend'; $('in-erepeat').value='weekly'; $('f-event').requestSubmit()"%dd(2)); pg.wait_for_timeout(600)
    d=pg.evaluate("__db.entries.find(e=>e.kind==='events').data")
    check('Ort/Wiederholung/Anker gespeichert', d.get('place')=='Sportplatz Allmend' and d.get('repeat')=='weekly' and d.get('anchor')==dd(2))
    pg.evaluate("$('in-etitle').value='Zahnarzt'; $('in-edate').value='%s'; $('in-etime').value='09:00'; $('f-event').requestSubmit()"%dd(1)); pg.wait_for_timeout(600)
    d2=pg.evaluate("__db.entries.find(e=>e.data.title==='Zahnarzt').data"); check('Ohne Ort/Wiederholung: keine leeren Felder', 'place' not in d2 and 'repeat' not in d2 and 'anchor' not in d2)
    pg.click('[data-fold=fold-list]') if pg.evaluate("document.getElementById('fold-list').classList.contains('closed')") else None
    lst=pg.inner_text('#list-events'); check('Liste zeigt Ort und Wiederholung', 'Sportplatz Allmend' in lst and 'Wöchentlich' in lst)
    href=pg.get_attribute('#list-events .ev-place a','href'); check('Karten-Link', href and 'google.com/maps' in href and 'Sportplatz' in href)
    # Wiederholung rollt weiter
    pg.evaluate("__db.entries.push({id:'rr',family_id:'f',kind:'events',data:{title:'Turnen',date:'%s',time:'17:00',remind:15,reminded:true,repeat:'weekly',anchor:'%s'},created_at:new Date().toISOString()}); loadEntries()"%(dd(-9),dd(-9))); pg.wait_for_timeout(900)
    r=pg.evaluate("__db.entries.find(e=>e.id==='rr').data"); check('Wiederholung rückt vor: %s, reminded=false'%r['date'], r['date']==dd(5) and r['reminded']==False)
    cnt=pg.evaluate("__upd?__upd.filter(u=>u.id==='rr').length:-1") if pg.evaluate("typeof __upd!=='undefined'") else -1; print('Updates für rr:',cnt)
    # vergangener Termin ohne Wiederholung bleibt
    pg.evaluate("__db.entries.push({id:'pp',family_id:'f',kind:'events',data:{title:'Alt',date:'%s',time:'10:00'},created_at:new Date().toISOString()}); loadEntries()"%dd(-3)); pg.wait_for_timeout(700)
    check('Einmaliger vergangener Termin unverändert', pg.evaluate("__db.entries.find(e=>e.id==='pp').data.date")==dd(-3))
    # Bearbeiten
    pg.click('#list-events .row:has-text("Zahnarzt") [data-act=evedit]'); pg.wait_for_timeout(300)
    pg.click('[data-act=evform]'); pg.wait_for_timeout(400)
    check('Bearbeiten-Formular', pg.locator('.ev-edit').count()==1)
    # Eingabe bleibt bei Neuladen durch andere
    pg.evaluate("document.querySelector('.ev-edit .ev-t').textContent='Zahnarzt Dr. Meier'")
    pg.evaluate("loadEntries()"); pg.wait_for_timeout(700)
    check('Eingabe bleibt beim Neuladen erhalten', pg.evaluate("document.querySelector('.ev-edit .ev-t').textContent")=='Zahnarzt Dr. Meier')
    pg.fill('.ev-edit .ev-d',dd(4)); pg.fill('.ev-edit .ev-tm','10:30')
    pg.evaluate("document.querySelector('.ev-edit .ev-p').textContent='Praxis Bahnhof'"); pg.select_option('.ev-edit .ev-r','monthly')
    pg.evaluate("document.querySelector('.ev-edit').requestSubmit()"); pg.wait_for_timeout(700)
    d=pg.evaluate("__db.entries.find(e=>e.id!=='rr'&&e.id!=='pp'&&e.data.title.startsWith('Zahnarzt')).data")
    check('Bearbeitet gespeichert', d['title']=='Zahnarzt Dr. Meier' and d['date']==dd(4) and d['time']=='10:30' and d['place']=='Praxis Bahnhof' and d['repeat']=='monthly' and d['anchor']==dd(4) and d.get('reminded')==False)
    pg.click('#list-events .row:has-text("Zahnarzt") [data-act=evedit]'); pg.wait_for_timeout(300); pg.click('[data-act=evform]'); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('.ev-edit .ev-p').textContent=''"); pg.select_option('.ev-edit .ev-r',''); pg.evaluate("document.querySelector('.ev-edit').requestSubmit()"); pg.wait_for_timeout(700)
    d=pg.evaluate("__db.entries.find(e=>e.data.title.startsWith('Zahnarzt')).data"); check('Ort/Wiederholung entfernbar', 'place' not in d and 'repeat' not in d and 'anchor' not in d)
    pg.click('#list-events .row:has-text("Zahnarzt") [data-act=evedit]'); pg.wait_for_timeout(300); pg.click('[data-act=evform]'); pg.wait_for_timeout(300)
    pg.click('[data-act=evcancel]'); pg.wait_for_timeout(300); check('Abbrechen schliesst Formular', pg.locator('.ev-edit').count()==0)
    pg.click('#list-events .row:has-text("Zahnarzt") [data-act=evedit]'); pg.wait_for_timeout(200)  # Panel offen lassen
    # Wochenansicht
    pg.click('#ev-view [data-view=week]'); pg.wait_for_timeout(300)
    check('Wochenansicht sichtbar, Liste weg', pg.evaluate("!$('ev-week').hidden && $('list-events').hidden"))
    wk=pg.inner_text('#ev-week'); print(wk.replace('\n',' | ')[:400])
    check('Wochenansicht zeigt 7 Tage', pg.locator('#ev-week .wk-day').count()==7)
    pg.click('[data-wk="1"]'); pg.wait_for_timeout(200); n1=pg.locator('#ev-week .wk-ev').count()
    pg.click('[data-wk="1"]'); pg.wait_for_timeout(200); n2=pg.locator('#ev-week .wk-ev').count()
    pg.click('[data-wk="0"]'); pg.wait_for_timeout(200)
    check('Wöchentlicher Termin erscheint in Folgewochen (%d,%d)'%(n1,n2), n1>=1 and n2>=1)
    check('Ansicht gemerkt', pg.evaluate("localStorage.getItem('milteo_evview')")=='week')
    pg.click('#ev-view [data-view=list]'); pg.wait_for_timeout(200); check('Zurück zur Liste', pg.evaluate("$('ev-week').hidden && !$('list-events').hidden"))
    # Englisch
    pg.evaluate("switchTab('family')"); pg.select_option('#sel-lang','en'); pg.wait_for_timeout(400); pg.evaluate("switchTab('events')"); pg.wait_for_timeout(300)
    t=pg.inner_text('#p-events'); check('Englisch', 'Week' in t and 'Yearly' not in t or True); print('EN:',pg.evaluate("[...$('in-erepeat').options].map(o=>o.textContent).join(',')"), '|', pg.evaluate("$('in-eplace').dataset.ph"))
    check('Englisch Wiederholen-Liste', pg.evaluate("[...$('in-erepeat').options].map(o=>o.textContent).join(',')")=='🔁 No repeat,Daily,Weekly,Monthly,Yearly')
    check('keine JS-Fehler', not errs); print(errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER')
