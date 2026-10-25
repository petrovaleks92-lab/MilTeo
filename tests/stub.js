(() => {
  window.__db = { entries: [
    {id:'e0',family_id:'f',kind:'todos',data:{text:'Fenster putzen',done:false,by:'Mama'},created_at:new Date().toISOString()},
    {id:'e1',family_id:'f',kind:'shop',data:{text:'Milch',done:false},created_at:new Date().toISOString()},
    {id:'e2',family_id:'f',kind:'shop',data:{type:'dish',text:'Lasagne',servings:4,items:[{name:'Hackfleisch',amount:'500 g',done:false}]},created_at:new Date().toISOString()}] };
  window.__fail = !!window.__failInit; window.__calls = [];
  const NET = { message: 'TypeError: Failed to fetch', details: '', hint: '', code: '' };
  let seq = 10;
  const builder = (t) => {
    let op = 'select', payload = null, id = null;
    const run = () => {
      window.__calls.push(op + ':' + t);
      if (window.__fail) return { data: null, error: NET };
      if (t === 'entries') {
        if (op === 'insert') { const row = { id: 'n' + (seq++), created_at: new Date().toISOString(), ...payload }; window.__db.entries.push(row); return { data: row, error: null }; }
        if (op === 'update') { const e = window.__db.entries.find(x => x.id === id); if (e) e.data = payload.data; return { data: null, error: null }; }
        if (op === 'delete') { window.__db.entries = window.__db.entries.filter(x => x.id !== id); return { data: null, error: null }; }
        return { data: JSON.parse(JSON.stringify(window.__db.entries)), error: null };
      }
      return { data: [], error: null };
    };
    const p = new Proxy({}, { get: (_, k) => {
      if (k === 'then') return (res) => res(run());
      if (k === 'maybeSingle') return async () => { if (t === 'members' && window.__failMembers) return { data: null, error: NET }; if (t === 'members') return { data: { family_id: 'f', families: { code: 'ABC' }, display_name: 'Ich' }, error: null }; if (t === 'entries') { window.__calls.push('maybeSingle:entries'); if (window.__fail) return { data: null, error: NET }; const e = window.__db.entries.find(x => x.id === id); return { data: e ? { data: JSON.parse(JSON.stringify(e.data)) } : null, error: null }; } return { data: null, error: null }; };
      if (k === 'single') return async () => run();
      return (...a) => { if (['insert','update','delete'].includes(k)) { op = k; payload = a[0]; } if (k === 'eq' && a[0] === 'id') id = a[1]; return p; };
    } });
    return p;
  };
  window.supabase = { createClient: () => ({
    auth: { getSession: async () => ({ data: { session: window.__sess || null } }), onAuthStateChange: () => ({ data: { subscription: {} } }), signOut: async () => { window.__out=(window.__out||0)+1; return {}; }, signInWithPassword: async ({password}) => (window.__good===password ? {error:null} : {error:{message:'Invalid login credentials'}}), signUp: async (o) => { window.__signup=o; return {error:null}; }, updateUser: async (o) => { window.__upd=(window.__upd||[]).concat([o]); return {error:null}; } },
    from: builder, rpc: async (n) => { window.__rpc=(window.__rpc||[]).concat([n]); return n==='delete_my_account' && window.__rpcErr ? {data:null,error:{message:'fk violation'}} : {data:[],error:null}; }, channel: (n) => { const ch = { on(t, f, cb) { (window.__rt = window.__rt || []).push([f.table, cb]); return ch; }, subscribe(cb) { window.__rtStatus = cb; setTimeout(() => cb && cb('SUBSCRIBED'), 0); return ch; } }; return ch; }, removeChannel() { window.__removed = (window.__removed || 0) + 1; },
    functions: { invoke: async () => ({ data: {}, error: null }) }, storage: { from: () => ({}) } }) };
})();
