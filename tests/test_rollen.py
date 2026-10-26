import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
URL = 'file://' + ROOT + '/index.html'
from playwright.sync_api import sync_playwright
base = open(os.path.join(HERE, 'stub7.js'), encoding='utf-8').read()
# Mitglieder mit Rollen + aufgezeichnete Rollen-Aufrufe
extra = """
(() => {
  const orig = window.supabase.createClient;
  window.__members = [
    {user_id:'me', display_name:'Ich', created_at:'2026-01-01', role:'admin'},
    {user_id:'u2', display_name:'Papa', created_at:'2026-01-02', role:'member'},
    {user_id:'u3', display_name:'Oma', created_at:'2026-01-03', role:'admin'}];
  window.__roleCalls = []; window.__roleErr = null; window.__noRoleCol = false;
  window.supabase.createClient = (...a) => {
    const c = orig(...a); const of = c.from; const orpc = c.rpc;
    c.from = (t) => {
      if (t !== 'members') return of(t);
      let cols = '';
      const p = new Proxy({}, { get: (_, k) => {
        if (k === 'then') return (res) => res(window.__noRoleCol && /role/.test(cols) ? {data:null,error:{message:'column role does not exist'}} : {data: JSON.parse(JSON.stringify(window.__members)), error:null});
        if (k === 'maybeSingle') return async () => ({ data: window.__nofam ? null : { family_id:'f', families:{code:'ABCD-EFGH'}, display_name:'Ich' }, error:null });
        return (...x) => { if (k === 'select') cols = x[0]; return p; };
      }});
      return p;
    };
    c.rpc = async (n, args) => {
      if (n === 'set_member_role' || n === 'remove_member' || n === 'regenerate_family_code') {
        window.__roleCalls.push([n, args]);
        if (window.__roleErr) return {data:null, error:{message: window.__roleErr}};
        return {data: n === 'regenerate_family_code' ? 'NEUE-CODE' : null, error:null};
      }
      return orpc(n, args);
    };
    return c;
  };
})();
"""
stub = base + extra
ok = True
def check(name, cond):
    global ok; ok = ok and bool(cond); print(('PASS ' if cond else 'FAIL ') + name)
def mk(b, init, url=URL):
    ctx = b.new_context(viewport={'width':390,'height':780}, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.route('**/supabase.min.js', lambda r: r.fulfill(body=stub, content_type='text/javascript'))
    pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.add_init_script(init)
    pg.on('dialog', lambda d: d.accept())
    pg.goto(url); pg.wait_for_timeout(800)
    return pg, errs
SESS = "window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}};"
with sync_playwright() as p:
    b = p.chromium.launch()
    # Admin-Sicht
    pg, errs = mk(b, SESS)
    pg.evaluate("switchTab('family')"); pg.wait_for_timeout(500)
    t = pg.inner_text('#list-members')
    check('Rollen-Abzeichen sichtbar', 'Admin' in t and 'Mitglied' in t)
    check('Admin sieht Buttons für andere (2x2), nicht für sich', pg.locator('[data-mrole]').count() == 2 and pg.locator('[data-mrem]').count() == 2)
    check('Neuer-Code-Knopf sichtbar für Admin', pg.is_visible('#fam-newcode'))
    pg.click('[data-mrole=u2]'); pg.wait_for_timeout(300)
    check('Zum Admin machen -> rpc set_member_role admin', pg.evaluate("JSON.stringify(window.__roleCalls[0])") == '["set_member_role",{"p_user":"u2","p_role":"admin"}]')
    pg.click('[data-mrem=u2]'); pg.wait_for_timeout(300)
    check('Entfernen -> rpc remove_member', pg.evaluate("JSON.stringify(window.__roleCalls[1])") == '["remove_member",{"p_user":"u2"}]')
    pg.evaluate("window.__roleErr='last admin'"); pg.click('[data-mrole=u3]'); pg.wait_for_timeout(300)
    toast = pg.inner_text('#toast') if pg.locator('#toast').count() else ''
    print('   Toast:', toast)
    check('Fehler «last admin» freundlich', 'mindestens ein Admin' in toast)
    pg.evaluate("window.__roleErr='not allowed'"); pg.click('#fam-newcode'); pg.wait_for_timeout(300)
    toast = pg.inner_text('#toast')
    check('Fehler «not allowed» freundlich, kein Technik-Text', 'nur Admins' in toast and 'not allowed' not in toast)
    check('keine JS-Fehler (Admin)', not errs)
    # Normales Mitglied
    pg, errs = mk(b, SESS + "window.__pre=1;")
    pg.evaluate("window.__members[0].role='member'; window.__members[1].role='admin'; loadMembers()"); pg.evaluate("switchTab('family')"); pg.wait_for_timeout(600)
    check('Mitglied: keine Verwaltungs-Buttons', pg.locator('[data-mrole]').count() == 0 and pg.locator('[data-mrem]').count() == 0)
    check('Mitglied: Neuer-Code-Knopf versteckt, Hinweis da', not pg.is_visible('#fam-newcode') and pg.is_visible('#fam-admin-only'))
    check('Mitglied: Einladung teilen weiterhin da', pg.is_visible('#fam-share'))
    # Alter Stand ohne Rollen-Spalte (Fallback)
    pg, errs = mk(b, SESS + "window.__noRoleCol=true;")
    pg.evaluate("switchTab('family')"); pg.wait_for_timeout(500)
    check('ohne Rollen-Spalte: Liste trotzdem da, Code-Knopf bleibt', 'Papa' in pg.inner_text('#list-members') and pg.is_visible('#fam-newcode') and not errs)
    # Einladung teilen (Fallback Zwischenablage)
    pg, errs = mk(b, SESS + "window.__cp=null; Object.defineProperty(navigator,'share',{value:undefined,configurable:true}); Object.defineProperty(navigator,'clipboard',{value:{writeText:async t=>{window.__cp=t}},configurable:true});")
    pg.evaluate("switchTab('family')"); pg.click('#fam-share'); pg.wait_for_timeout(300)
    cp = pg.evaluate("window.__cp") or ''
    print('   Zwischenablage:', cp.replace('\n', ' | '))
    check('Einladungstext enthält Code und Link ?code=', 'ABCD-EFGH' in cp and '?code=ABCD-EFGH' in cp)
    # Link ?code= füllt Beitrittsfeld
    pg, errs = mk(b, "window.__sess={user:{id:'neu',email:'n@b.ch',user_metadata:{name:'Neu'}}}; window.__nofam=1;", URL + '?code=WXYZ-1234')
    fv = pg.evaluate("document.getElementById('in-code').value")
    check('Einladungslink füllt Code-Feld vor', fv == 'WXYZ-1234' and 'code=' not in pg.url)
    b.close()
print('ALLES BESTANDEN' if ok else 'FEHLER')
raise SystemExit(0 if ok else 1)
