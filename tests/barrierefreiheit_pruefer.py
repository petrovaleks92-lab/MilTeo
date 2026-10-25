import sys, json
from playwright.sync_api import sync_playwright
import os
HERE = os.path.dirname(os.path.abspath(__file__))
stub=open(os.path.join(HERE,'stub.js'),encoding='utf-8').read()
URL='file://' + os.path.dirname(HERE) + '/index.html'
JS = r"""
() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && !el.closest('[hidden]'); };
  const name = (el) => {
    const a = el.getAttribute('aria-label'); if (a && a.trim()) return a.trim();
    const lb = el.getAttribute('aria-labelledby'); if (lb) { const t = lb.split(' ').map(i => (document.getElementById(i) || {}).textContent || '').join(' ').trim(); if (t) return t; }
    if (el.id) { const l = document.querySelector('label[for="' + el.id + '"]'); if (l && l.textContent.trim()) return l.textContent.trim(); }
    const wrap = el.closest('label'); if (wrap && wrap.textContent.trim()) return wrap.textContent.trim();
    const t = (el.textContent || '').replace(/\s+/g, ' ').trim(); if (t) return t;
    const alt = el.getAttribute('alt'); if (alt) return alt;
    return el.getAttribute('title') || '';
  };
  const out = { noName: [], contrast: [], small: [] };
  const sel = 'button, a[href], [role=button], [role=checkbox], [role=textbox], [role=switch], input:not([type=hidden]):not([type=file]), select, textarea, [contenteditable]';
  document.querySelectorAll(sel).forEach(el => { if (!vis(el)) return; if (!name(el)) out.noName.push((el.tagName + '#' + el.id + '.' + (el.className || '')).slice(0, 80)); });
  document.querySelectorAll('button, [role=button], [role=checkbox], select, input.switch, .chip').forEach(el => { if (!vis(el)) return; const r = el.getBoundingClientRect(); if (Math.min(r.width, r.height) < 40) out.small.push((el.tagName + '#' + el.id + '.' + (el.className || '') + ' ' + Math.round(r.width) + 'x' + Math.round(r.height)).slice(0, 90)); });
  const parse = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const blend = (f, b) => ({ r: f.r * f.a + b.r * (1 - f.a), g: f.g * f.a + b.g * (1 - f.a), b: f.b * f.a + b.b * (1 - f.a), a: 1 });
  const lum = (c) => { const f = (v) => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }; return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b); };
  const bgOf = (el) => { const chain = []; for (let e = el; e; e = e.parentElement) chain.push(e); let bg = { r: 255, g: 255, b: 255, a: 1 }; const bodyBg = parse(getComputedStyle(document.body).backgroundColor); if (bodyBg && bodyBg.a > 0) bg = bodyBg; for (let i = chain.length - 1; i >= 0; i--) { const c = parse(getComputedStyle(chain[i]).backgroundColor); if (c && c.a > 0) bg = blend(c, bg); } return bg; };
  const seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode, el = n.parentElement; if (!el || !n.nodeValue.trim() || seen.has(el)) continue; if (el.closest('script,style,[hidden]') || !vis(el)) continue; seen.add(el);
    const cs = getComputedStyle(el); let fg = parse(cs.color); if (!fg) continue;
    let op = 1; for (let e = el; e; e = e.parentElement) op *= parseFloat(getComputedStyle(e).opacity); fg.a *= op;
    const bg = bgOf(el); const f = blend(fg, bg);
    const L1 = lum(f), L2 = lum(bg), ratio = (Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05);
    const size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700, large = size >= 24 || (size >= 18.66 && bold);
    if (ratio < (large ? 3 : 4.5)) out.contrast.push(ratio.toFixed(2) + ' ' + n.nodeValue.trim().slice(0, 30) + ' [' + el.tagName + '.' + (el.className || '') + ']');
  }
  return out;
}
"""
def run(scheme, width=390):
    res = {}
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={'width': width, 'height': 800}, color_scheme=scheme, has_touch=width < 700, is_mobile=width < 700)
        pg = ctx.new_page(); pg.on('pageerror', lambda e: print('ERR', e))
        pg.route('**/supabase.min.js', lambda r: r.fulfill(body=stub, content_type='text/javascript')); pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
        pg.add_init_script("window.__sess={user:{id:'me',email:'a@b.ch',user_metadata:{name:'Ich'}}}")
        pg.goto(URL); pg.wait_for_timeout(800)
        pg.evaluate("""__db.entries=[{id:'e0',family_id:'f',kind:'todos',data:{text:'Fenster putzen',done:false,by:'Mama'},created_at:new Date().toISOString()},{id:'e5',family_id:'f',kind:'todos',data:{text:'Müll raus',done:true},created_at:new Date().toISOString()},{id:'e1',family_id:'f',kind:'shop',data:{text:'Milch',qty:'2 l',done:false},created_at:new Date().toISOString()},{id:'e2',family_id:'f',kind:'shop',data:{type:'dish',text:'Lasagne',servings:4,items:[{name:'Hackfleisch',amount:'500 g',done:false},{name:'Tomaten',amount:'400 g',done:true}],steps:['Zwiebeln hacken','Alles mischen']},created_at:new Date().toISOString()},{id:'tm',family_id:'f',kind:'timers',data:{label:'Backofen',end:Date.now()+900000},created_at:new Date().toISOString()},{id:'ev',family_id:'f',kind:'events',data:{title:'Zahnarzt',date:'2030-01-02',time:'10:00',remind:15,by:'Papa'},created_at:new Date().toISOString()},{id:'tt1',family_id:'f',kind:'events',data:{type:'timetable',child:'Luca',lessons:[{d:1,from:'08:15',to:'11:30',subject:'Kindergarten',group:'Mond'},{d:2,from:'13:30',to:'15:30',subject:'Kindergarten',group:'Mond'}]},created_at:new Date().toISOString()}]; openDishes.add('e2'); recipeOpen.add('e2'); memberNames={me:'Ich',x:'Mama'}; memberCount=2; chatMsgs=[{id:'m1',family_id:'f',user_id:'o',display_name:'Mama',body:'Hallo 😀',created_at:new Date().toISOString()},{id:'m2',family_id:'f',user_id:'me',display_name:'Ich',body:'Hi',created_at:new Date().toISOString()}]; chatUnread=3; loadEntries()""")
        pg.wait_for_timeout(800)
        for tab in ['home','shop','todos','timers','events','chat','family']:
            pg.evaluate("t=>switchTab(t)", tab); pg.evaluate("renderChat(); renderHome()"); pg.wait_for_timeout(250)
            if tab == 'events': pg.evaluate("document.querySelectorAll('.fold').forEach(f=>f.classList.remove('closed'))")
            res[tab] = pg.evaluate(JS)
        # Fokus sichtbar: erste 8 Tab-Stopps
        pg.evaluate("switchTab('home')"); focus = []
        for _ in range(8):
            pg.keyboard.press('Tab'); focus.append(pg.evaluate("(() => { const e=document.activeElement; const cs=getComputedStyle(e); return (e.tagName+'#'+e.id+'.'+(e.className||'')).slice(0,40)+' outline='+cs.outlineStyle+' '+cs.outlineWidth+' shadow='+(cs.boxShadow!=='none')+' border='+cs.borderColor })()"))
        res['focus'] = focus
        b.close()
    return res
if __name__ == '__main__':
    tot = {'noName':0,'contrast':0,'small':0}
    for scheme in ['light','dark']:
        r = run(scheme); print('=====', scheme)
        for tab,v in r.items():
            if tab == 'focus': continue
            for k in tot: tot[k]+=len(v[k])
            print(tab, {k: len(v[k]) for k in v})
            for k in v:
                for x in v[k][:6]: print('    ', k, x)
        if scheme=='light':
            print('focus:'); [print('   ',x) for x in r['focus']]
    print('SUMME', tot)
