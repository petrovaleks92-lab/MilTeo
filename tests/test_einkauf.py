import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub=open(os.path.join(HERE,'stub.js'),encoding='utf-8').read()
ok=True
def check(name, cond):
    global ok; ok = ok and bool(cond); print(('PASS ' if cond else 'FAIL ')+name)
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':390,'height':780},has_touch=True,is_mobile=True)
    pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)+' @ '+str(getattr(e,'stack',''))[:400]))
    pg.route('**/supabase.min.js',lambda r:r.fulfill(body=stub,content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**',lambda r:r.fulfill(body='',content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}; localStorage.setItem('milteo_tab','shop')")
    pg.goto(URL); pg.wait_for_timeout(1000)
    pg.evaluate("__db.entries=[]; loadEntries()"); pg.wait_for_timeout(500)
    def add(t,q=''):
        pg.evaluate("([t,q])=>{$('in-shop').value=t;$('in-shop-qty').value=q;$('f-shop').requestSubmit()}",[t,q]); pg.wait_for_timeout(450)
    n=lambda:pg.evaluate("__db.entries.filter(e=>e.kind==='shop').length")
    for t in ['Milch','Bananen','Brot','Pouletbrust','Spaghetti','Toilettenpapier','Wasser','Glace','Zahnpasta','Apfelsaft','Olivenöl','Kokosmilch','Xyz Ding']: add(t)
    check('13 Artikel gespeichert', n()==13)
    cats=pg.evaluate("[...document.querySelectorAll('#list-shop .cat-h')].map(e=>e.textContent.trim())")
    print(cats)
    check('Gruppen vorhanden und sortiert', len(cats)>=7 and cats[-1].endswith('Sonstiges'))
    g=lambda t:pg.evaluate("t=>{const e=__db.entries.find(x=>x.data.text===t); return guessCat(t)}",t)
    exp={'Milch':'dairy','Bananen':'veg','Brot':'bake','Pouletbrust':'meat','Spaghetti':'pantry','Toilettenpapier':'house','Wasser':'drink','Glace':'frozen','Zahnpasta':'house','Apfelsaft':'drink','Olivenöl':'pantry','Xyz Ding':'other'}
    bad={k:g(k) for k,v in exp.items() if g(k)!=v}; check('Kategorien erraten '+str(bad), not bad)
    # Duplikat
    add('milch'); check('Duplikat (andere Schreibweise) nicht doppelt', n()==13 and 'steht schon' in pg.inner_text('#toast'))
    add('MILCH','2 l'); check('Menge wird ergänzt', pg.evaluate("__db.entries.find(e=>e.data.text==='Milch').data.qty")=='2 l' and n()==13)
    pg.click('#list-shop .row:has-text("Brot") [data-act=toggle]'); pg.wait_for_timeout(500)
    add('Brot'); d=pg.evaluate("__db.entries.find(e=>e.data.text==='Brot').data"); check('Erledigter Artikel kommt zurück statt Duplikat', n()==13 and not d['done'] and 'wieder' in pg.inner_text('#toast'))
    # Suche
    check('Suchfeld sichtbar ab 6 Artikeln', pg.evaluate("!$('shop-q').hidden"))
    pg.evaluate("$('shop-q').textContent='milch'; $('shop-q').dispatchEvent(new Event('input',{bubbles:true}))"); pg.wait_for_timeout(200)
    r=pg.evaluate("[...document.querySelectorAll('#list-shop .row .txt')].map(e=>e.firstChild.textContent)"); check('Suche findet Milch und Kokosmilch '+str(r), sorted(r)==['Kokosmilch','Milch'])
    pg.evaluate("$('shop-q').textContent='qqq'; $('shop-q').dispatchEvent(new Event('input',{bubbles:true}))"); pg.wait_for_timeout(200)
    check('Nichts gefunden', 'Nichts gefunden' in pg.inner_text('#list-shop'))
    pg.evaluate("$('shop-q').textContent=''; $('shop-q').dispatchEvent(new Event('input',{bubbles:true}))"); pg.wait_for_timeout(200)
    # Kategorie ändern
    pg.click('#list-shop .row:has-text("Xyz Ding") [data-act=edit]'); pg.wait_for_timeout(300)
    pg.select_option('#ed-cat','house'); pg.evaluate("document.querySelector('.ed-form').requestSubmit()"); pg.wait_for_timeout(500)
    check('Kategorie manuell gesetzt', pg.evaluate("__db.entries.find(e=>e.data.text==='Xyz Ding').data.cat")=='house')
    pg.click('#list-shop .row:has-text("Xyz Ding") [data-act=edit]'); pg.wait_for_timeout(300)
    pg.select_option('#ed-cat',''); pg.evaluate("document.querySelector('.ed-form').requestSubmit()"); pg.wait_for_timeout(500)
    check('Kategorie wieder automatisch', 'cat' not in pg.evaluate("__db.entries.find(e=>e.data.text==='Xyz Ding').data"))
    # Häufig gekauft: 2x abhaken -> Chip
    for _ in range(2):
        pg.click('#list-shop .row:has-text("Wasser") [data-act=toggle]'); pg.wait_for_timeout(450)
        pg.click('#list-shop .row:has-text("Wasser") [data-act=toggle]'); pg.wait_for_timeout(450)   # wieder offen
    check('Kein Chip solange Wasser offen ist', pg.evaluate("$('shop-freq').hidden"))
    pg.click('#list-shop .row:has-text("Wasser") [data-act=toggle]'); pg.wait_for_timeout(450)
    pg.click('#list-shop .row:has-text("Wasser") [data-act=del]'); pg.wait_for_timeout(6800)
    print('FREQ',pg.evaluate("JSON.stringify(freqLoad())"), pg.evaluate("$('shop-freq').outerHTML.slice(0,200)"), pg.evaluate("entries.filter(e=>e.kind==='shop').map(e=>e.data.text).join(',')"))
    check('Chip «Wasser» erscheint', 'Wasser' in pg.inner_text('#shop-freq') and 'häufig gekauft' in pg.inner_text('#shop-freq').lower())
    pg.click('#shop-freq [data-freq]'); pg.wait_for_timeout(600)
    pg.wait_for_timeout(1500); print('AFTER',pg.evaluate("__db.entries.filter(e=>e.kind==='shop').map(e=>e.data.text).join(',')"), pg.evaluate("$('shop-freq').hidden"), pg.evaluate("entries.filter(e=>e.kind==='shop').map(e=>e.data.text+':'+e.data.done).join(',')"))
    check('Chip fügt Artikel hinzu', pg.evaluate("__db.entries.some(e=>e.data.text==='Wasser')") and pg.evaluate("$('shop-freq').hidden"))
    # Gericht bleibt oben
    pg.evaluate("__db.entries.push({id:'dd',family_id:'f',kind:'shop',data:{type:'dish',text:'Lasagne',servings:4,items:[{name:'Hackfleisch',amount:'500 g',done:False}]},created_at:new Date().toISOString()}); loadEntries()".replace('False','false')); pg.wait_for_timeout(500)
    first=pg.evaluate("document.querySelector('#list-shop ul > li').className"); check('Gericht steht oben', 'dish' in first)
    pg.evaluate("$('shop-q').textContent='hackfleisch'; $('shop-q').dispatchEvent(new Event('input',{bubbles:true}))"); pg.wait_for_timeout(200)
    check('Suche findet Zutat im Gericht', 'Lasagne' in pg.inner_text('#list-shop'))
    pg.evaluate("$('shop-q').textContent=''; $('shop-q').dispatchEvent(new Event('input',{bubbles:true}))")
    pg.evaluate("switchTab('shop')"); pg.select_option('#sel-lang','en') if False else None
    check('keine JS-Fehler', not errs); print(errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER')
