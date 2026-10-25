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
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':390,'height':780},has_touch=True,is_mobile=True)
    pg=ctx.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/supabase.min.js',lambda r:r.fulfill(body=stub,content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}")
    pg.goto(URL); pg.wait_for_timeout(900)
    # Daten vorbereiten: Gericht mit 2 Zutaten, Termin mit Server-Markierung
    pg.evaluate("""__db.entries=[
      {id:'d1',family_id:'f',kind:'shop',data:{type:'dish',text:'Lasagne',servings:4,items:[{name:'Hack',amount:'500 g',done:false},{name:'Tomaten',amount:'400 g',done:false}]},created_at:new Date().toISOString()},
      {id:'ev1',family_id:'f',kind:'events',data:{title:'Zahnarzt',date:'2030-01-02',time:'10:00',remind:15},created_at:new Date().toISOString()}]; loadEntries()""")
    pg.wait_for_timeout(700)
    check('Echtzeit-Abos angelegt (entries + members)', pg.evaluate("(window.__rt||[]).map(x=>x[0]).sort().join()")=='entries,members,messages' or pg.evaluate("(window.__rt||[]).map(x=>x[0]).sort().join()")=='entries,members')
    # Echtzeit: andere Person fügt Aufgabe ein, ohne dass wir etwas tun
    pg.evaluate("__db.entries.push({id:'t9',family_id:'f',kind:'todos',data:{text:'Von Papa',done:false,by:'Papa'},created_at:new Date().toISOString()}); __rt.filter(x=>x[0]==='entries').forEach(x=>x[1]({eventType:'INSERT'}))")
    pg.wait_for_timeout(800)
    pg.evaluate("switchTab('todos')")
    check('Echtzeit: neue Aufgabe erscheint ohne Warten auf Abfrage', 'Von Papa' in pg.inner_text('#list-todos'))
    # Verlorene Änderung verhindern
    pg.evaluate("switchTab('shop')"); pg.evaluate("openDishes.add('d1'); renderChecklist('shop')")
    # Fremde Änderung auf dem Server (unser Gerät weiss noch nichts davon)
    pg.evaluate("__db.entries.find(e=>e.id==='d1').data.items[1].done=true")
    pg.click('[data-act=item][data-id=d1][data-i="0"]'); pg.wait_for_timeout(700)
    srv=pg.evaluate("__db.entries.find(e=>e.id==='d1').data.items.map(i=>i.done)")
    check('Gleichzeitiges Abhaken: beide Zutaten auf dem Server erledigt', srv==[True,True])
    # Zutat wurde woanders gelöscht, wir haken sie ab
    pg.evaluate("__db.entries.find(e=>e.id==='d1').data.items=[{name:'Tomaten',amount:'400 g',done:true}]")
    pg.click('[data-act=item][data-id=d1][data-i="0"]'); pg.wait_for_timeout(700)
    srv=pg.evaluate("__db.entries.find(e=>e.id==='d1').data.items")
    check('Zutat inzwischen gelöscht: nichts Falsches abgehakt, kein Fehler', len(srv)==1 and srv[0]['name']=='Tomaten' and srv[0]['done']==True)
    # Zutat löschen mit Rückgängig-Fenster, richtige Zutat wird entfernt
    pg.evaluate("__db.entries.find(e=>e.id==='d1').data.items=[{name:'Hack',amount:'500 g',done:false},{name:'Tomaten',amount:'400 g',done:false},{name:'Käse',amount:'',done:false}]; loadEntries()"); pg.wait_for_timeout(600)
    pg.evaluate("__db.entries.find(e=>e.id==='d1').data.items.shift()")     # jemand löscht 'Hack' → Position verschiebt sich
    pg.click('[data-act=item-del][data-id=d1][data-i="1"]'); pg.evaluate("commitPending()"); pg.wait_for_timeout(700)
    srv=pg.evaluate("__db.entries.find(e=>e.id==='d1').data.items.map(i=>i.name)")
    check('Löschen trifft die richtige Zutat trotz verschobener Position', srv==['Käse'])
    # Server-Markierung (Erinnerung schon gesendet) bleibt erhalten
    pg.evaluate("__db.entries.find(e=>e.id==='ev1').data.reminded=true")
    pg.evaluate("switchTab('events')"); pg.click('[data-act=evedit]'); pg.click('[data-act=evhome]'); pg.wait_for_timeout(700)
    d=pg.evaluate("__db.entries.find(e=>e.id==='ev1').data")
    check('Änderung behält Server-Markierung "reminded"', d.get('reminded')==True and d.get('home')==False)
    # Eintrag fremd gelöscht, wir ändern ihn
    pg.evaluate("__db.entries=__db.entries.filter(e=>e.id!=='ev1')")
    pg.click('[data-act=evhome]'); pg.wait_for_timeout(800)
    check('Eintrag woanders gelöscht: kein Fehler, verschwindet', pg.evaluate("!entries.some(e=>e.id==='ev1')"))
    # Abfragen: Mitglieder nicht bei jedem Laden
    pg.evaluate("memberCount=2; lastMembers=Date.now()")
    n0=pg.evaluate("__calls.filter(c=>c==='select:members').length")
    for _ in range(5): pg.evaluate("loadEntries()"); pg.wait_for_timeout(150)
    n1=pg.evaluate("__calls.filter(c=>c==='select:members').length")
    check('Mitglieder werden nicht bei jedem Laden neu abgefragt', n1-n0<=1)
    # Abmelden räumt Abos auf
    pg.evaluate("unsubscribeChat()"); check('Abmelden: Echtzeit-Kanäle entfernt', pg.evaluate("window.__removed>=2"))
    check('keine JS-Fehler', not errs); print(errs); b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER')
