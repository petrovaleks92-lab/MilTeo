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
URL=URL
today=datetime.date.today(); iso=lambda d:d.isoformat()
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':390,'height':780},has_touch=True,is_mobile=True)
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase.min.js',lambda r:r.fulfill(body=stub,content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}; localStorage.setItem('milteo_tab','todos')")
    pg.goto(URL); pg.wait_for_timeout(800)
    pg.evaluate("__db.entries=[]; loadEntries()"); pg.wait_for_timeout(1500)
    pg.evaluate("memberNames={me:'Ich',u2:'Luca'}; renderAll()")
    # Hinzufügen mit Optionen
    check('Optionen zunächst zu', pg.evaluate("document.getElementById('todo-opts').hidden"))
    pg.click('#todo-more'); check('Optionen offen', not pg.evaluate("document.getElementById('todo-opts').hidden") and pg.get_attribute('#todo-more','aria-expanded')=='true')
    print('OPT',pg.evaluate("[...document.querySelectorAll('#todo-as option')].map(o=>o.textContent+':'+o.value)"), pg.evaluate('JSON.stringify(memberNames)'))
    check('Zuweisen-Liste hat Mitglieder', pg.evaluate("[...document.querySelectorAll('#todo-as option')].map(o=>o.textContent).join(',')")=='Alle,Ich,Luca')
    yest=iso(today-datetime.timedelta(days=1))
    pg.evaluate("document.getElementById('in-todos').textContent=''")
    def add(text, as_='', due='', prio='', rep=''):
        pg.evaluate("t=>{const i=document.getElementById('in-todos'); if(i.value!==undefined&&i.tagName==='INPUT') i.value=t; else i.textContent=t;}", text)
        pg.select_option('#todo-as',as_); pg.fill('#todo-due',due); pg.select_option('#todo-prio',prio); pg.select_option('#todo-rep',rep)
        pg.evaluate("document.getElementById('f-todos').requestSubmit()"); pg.wait_for_timeout(500)
    add('Müll rausbringen','u2',yest,'high','weekly')
    add('Zimmer aufräumen','me',iso(today+datetime.timedelta(days=3)),'','')
    add('Einfach so')
    rows=pg.evaluate("__db.entries.filter(e=>e.kind==='todos').map(e=>e.data)")
    check('3 Aufgaben gespeichert', len(rows)==3)
    r0=[r for r in rows if r['text']=='Müll rausbringen'][0]
    check('Felder gespeichert', r0.get('assignee')=='u2' and r0.get('assigneeName')=='Luca' and r0.get('due')==yest and r0.get('prio')=='high' and r0.get('repeat')=='weekly')
    r2=[r for r in rows if r['text']=='Einfach so'][0]
    check('Ohne Optionen: keine leeren Felder', not any(k in r2 for k in ['assignee','due','prio','repeat']))
    check('Optionen nach Hinzufügen zurückgesetzt', pg.evaluate("document.getElementById('todo-due').value===''&&document.getElementById('todo-as').value===''"))
    lst=pg.inner_text('#list-todos')
    check('Überfällig-Kennzeichen, Wichtig, Person, Wiederholung', 'Überfällig' in lst and 'Wichtig' in lst and 'Luca' in lst and 'Wöchentlich' in lst)
    order=pg.evaluate("[...document.querySelectorAll('#list-todos .row .txt')].map(e=>e.firstChild.textContent)")
    check('Sortierung: überfällig zuerst, ohne Datum zuletzt', order==['Müll rausbringen','Zimmer aufräumen','Einfach so'])
    # Filter
    pg.click('[data-flt=mine]'); check('Filter Meine', pg.evaluate("[...document.querySelectorAll('#list-todos .row .txt')].map(e=>e.firstChild.textContent)")==['Zimmer aufräumen'])
    pg.click('[data-flt=late]'); check('Filter Überfällig', pg.evaluate("[...document.querySelectorAll('#list-todos .row .txt')].map(e=>e.firstChild.textContent)")==['Müll rausbringen'])
    pg.click('[data-flt=done]'); check('Filter Erledigt leer: Hinweis', 'Keine Aufgaben in diesem Filter' in pg.inner_text('#list-todos'))
    check('aria-pressed gesetzt', pg.get_attribute('[data-flt=done]','aria-pressed')=='true' and pg.get_attribute('[data-flt=all]','aria-pressed')=='false')
    pg.click('[data-flt=all]')
    # Abhaken einer wiederkehrenden Aufgabe -> neues Datum, nicht erledigt
    pg.click('#list-todos .row:has-text("Müll") [data-act=toggle]'); pg.wait_for_timeout(600)
    r0=pg.evaluate("__db.entries.find(e=>e.data.text==='Müll rausbringen').data")
    exp=iso(today+datetime.timedelta(days=6))   # gestern +7 = in 6 Tagen
    check('Wiederholung: nächstes Datum %s, nicht erledigt'%exp, r0['due']==exp and not r0['done'])
    check('Hinweis Nächste Fälligkeit', 'Nächste Fälligkeit' in pg.inner_text('#toast'))
    # normale Aufgabe abhaken -> unten
    pg.click('#list-todos .row:has-text("Zimmer") [data-act=toggle]'); pg.wait_for_timeout(500)
    order=pg.evaluate("[...document.querySelectorAll('#list-todos .row .txt')].map(e=>e.firstChild.textContent)")
    check('Erledigte unten', order[-1]=='Zimmer aufräumen')
    # Bearbeiten
    pg.evaluate("lastMembers=Date.now(); memberNames={me:'Ich',u2:'Luca'}; renderAll()")
    pg.click('#list-todos .row:has-text("Einfach") [data-act=edit]'); pg.wait_for_timeout(300)
    check('Bearbeiten zeigt Optionen', pg.locator('.ed-form .ed-opts').count()==1 and pg.evaluate("[...document.querySelectorAll('.ed-form [data-f=as] option')].length")==3)
    pg.select_option('.ed-form [data-f=as]','u2'); pg.fill('.ed-form [data-f=due]',iso(today)); pg.select_option('.ed-form [data-f=prio]','high'); pg.select_option('.ed-form [data-f=rep]','daily')
    pg.evaluate("document.querySelector('.ed-form').requestSubmit()"); pg.wait_for_timeout(600)
    r=pg.evaluate("__db.entries.find(e=>e.data.text==='Einfach so').data")
    check('Bearbeiten gespeichert', r['assignee']=='u2' and r['due']==iso(today) and r['prio']=='high' and r['repeat']=='daily')
    pg.click('#list-todos .row:has-text("Einfach") [data-act=edit]'); pg.wait_for_timeout(300)
    pg.select_option('.ed-form [data-f=as]',''); pg.fill('.ed-form [data-f=due]',''); pg.select_option('.ed-form [data-f=prio]',''); pg.select_option('.ed-form [data-f=rep]','')
    pg.evaluate("document.querySelector('.ed-form').requestSubmit()"); pg.wait_for_timeout(600)
    r=pg.evaluate("__db.entries.find(e=>e.data.text==='Einfach so').data")
    check('Optionen entfernbar', not any(k in r for k in ['assignee','assigneeName','due','prio','repeat']))
    # Startseite
    pg.evaluate("switchTab('home')"); pg.wait_for_timeout(300)
    check('Kachel zeigt offen', 'offen' in pg.inner_text('#ti-todos'))
    pg.evaluate("__db.entries.find(e=>e.data.text==='Einfach so').data.due='%s'; loadEntries()"%yest); pg.wait_for_timeout(500)
    check('Kachel zeigt überfällig', 'überfällig' in pg.inner_text('#ti-todos') and 'Überfällig' in pg.inner_text('#home-open'))
    # Englisch
    pg.evaluate("switchTab('family')"); pg.wait_for_timeout(300); pg.select_option('#sel-lang','en'); pg.wait_for_timeout(500)
    pg.evaluate("switchTab('todos')"); pg.wait_for_timeout(400)
    t=pg.inner_text('#p-todos'); print('EN:',t.replace('\n',' | ')[:300])
    check('Englisch: Filter und Kennzeichen', 'Mine' in t and 'Overdue' in t and 'Options' in t)
    check('keine JS-Fehler', not errs); print(errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER')
