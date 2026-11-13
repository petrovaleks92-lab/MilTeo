import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
stub = open(os.path.join(HERE, 'stub.js'), encoding='utf-8').read()
ok = True
def check(name, cond):
    global ok; ok = ok and bool(cond); print(('PASS ' if cond else 'FAIL ') + name)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 390, 'height': 780}, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/supabase.min.js', lambda r: r.fulfill(body=stub, content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}; localStorage.setItem('milteo_tab','chat')")
    pg.goto(URL); pg.wait_for_timeout(1000)
    pg.evaluate("""myId='me'; memberNames={me:'Ich',pa:'Papa',oma:'Oma'}; readsOk=true; chatReads={};
      chatMsgs=[{id:'m1',user_id:'me',display_name:'Ich',body:'Hallo https://www.milteo.ch',created_at:'2026-11-13T10:00:00Z'},
                {id:'m2',user_id:'pa',display_name:'Papa',body:'Hi',created_at:'2026-11-13T10:05:00Z'},
                {id:'m3',user_id:'me',display_name:'Ich',body:'Wer holt Luca?',created_at:'2026-11-13T10:10:00Z'}];
      chatIds.clear(); ['m1','m2','m3'].forEach(i=>chatIds.add(i)); renderChat();""")
    tk = lambda: pg.evaluate("[...document.querySelectorAll('#list-chat .tick')].map(t=>t.textContent+(t.classList.contains('all')?'*':''))")
    check('niemand gelesen: ✓ bei eigenen, keins bei fremden: %s' % tk(), tk() == ['✓', '✓'])
    pg.evaluate("chatReads={pa:'2026-11-13T10:02:00Z'}; refreshTicks()")
    check('Papa las bis 10:02: erste ✓✓ grau, zweite ✓: %s' % tk(), tk() == ['✓✓', '✓'])
    pg.evaluate("chatReads={pa:'2026-11-13T10:20:00Z',oma:'2026-11-13T10:06:00Z'}; refreshTicks()")
    check('alle lasen erste, nur Papa die zweite: %s' % tk(), tk() == ['✓✓*', '✓✓'])
    pg.evaluate("chatReads={pa:'2026-11-13T10:20:00Z',oma:'2026-11-13T10:20:00Z'}; refreshTicks()")
    check('alle lasen alles: grün: %s' % tk(), tk() == ['✓✓*', '✓✓*'])
    pg.evaluate("chatReads={pa:'2026-11-13T10:20:00Z'}; refreshTicks(); document.querySelectorAll('#list-chat .tick')[0].click()"); pg.wait_for_timeout(200)
    check('Antippen zeigt «Gelesen von: Papa»', 'Gelesen von: Papa' in pg.inner_text('body'))
    pg.evaluate("readsOk=false; renderChat()")
    check('ohne Tabelle keine Häkchen, Link bleibt', tk() == [] and pg.evaluate("!!document.querySelector('#list-chat a.chat-link')"))
    pg.evaluate("readsOk=true; memberNames={me:'Ich'}; renderChat()")
    check('allein in der Familie: keine Häkchen', tk() == [])
    pg.evaluate("memberNames={me:'Ich',pa:'Papa'}; readsOk=true; chatReads={}; readsSent=''; currentTab='chat'; markRead()"); pg.wait_for_timeout(200)
    check('markRead setzt eigenen Stand auf letzte fremde Nachricht', pg.evaluate("chatReads.me") == '2026-11-13T10:05:00Z' and any(c.endswith(':message_reads') for c in pg.evaluate("window.__calls")))
    check('keine JS-Fehler: %s' % errs, not errs)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER'); sys.exit(0 if ok else 1)
