-- Schritt 10: Rollen (Admin / Mitglied) und Familien-Verwaltung
-- Nur ERGÄNZUNGEN: 1 neue Spalte, 1 Hilfsfunktion, 2 neue Funktionen, 5 angepasste Funktionen.
-- Es wird KEINE Zeile gelöscht und KEINE Tabelle/Spalte entfernt.

-- 1. Neue Spalte "role" (alle bestehenden Personen starten als 'member')
alter table public.members add column if not exists role text not null default 'member';
alter table public.members drop constraint if exists members_role_check;
alter table public.members add constraint members_role_check check (role in ('admin','member'));

-- 2. Wer pro Familie zuerst beigetreten ist (= Ersteller), wird Admin
update public.members m set role = 'admin'
where (m.family_id, m.created_at) in (select family_id, min(created_at) from public.members group by family_id);

-- 3. Hilfsfunktion: hat eine Familie keinen Admin mehr, wird die am längsten dabei seiende Person Admin
create or replace function public._ensure_admin(p_family uuid) returns void
language plpgsql security definer set search_path to 'public' as $$
begin
  if p_family is null then return; end if;
  if exists (select 1 from public.members where family_id = p_family)
     and not exists (select 1 from public.members where family_id = p_family and role = 'admin') then
    update public.members set role = 'admin'
    where user_id = (select user_id from public.members where family_id = p_family order by created_at limit 1);
  end if;
end $$;
revoke all on function public._ensure_admin(uuid) from public, anon, authenticated;

-- 4. Familie erstellen: die erstellende Person ist Admin
create or replace function public.create_family(p_display text) returns text
language plpgsql security definer set search_path to 'public' as $$
declare
  chars text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  c text; fid uuid;
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  if exists (select 1 from public.members where user_id = auth.uid()) then raise exception 'already in a family'; end if;
  loop
    c := '';
    for i in 1..8 loop c := c || substr(chars, 1 + floor(random() * length(chars))::int, 1); end loop;
    exit when not exists (select 1 from public.families where code = c);
  end loop;
  insert into public.families (code) values (c) returning id into fid;
  insert into public.members (user_id, family_id, display_name, role)
  values (auth.uid(), fid, left(coalesce(p_display, ''), 40), 'admin');
  return c;
end $$;

-- 5. Beitreten: neue Personen sind Mitglieder; wer dieselbe Familie nochmals betritt, behält die Rolle;
--    wer die Familie wechselt, wird Mitglied und die alte Familie bekommt bei Bedarf einen neuen Admin
create or replace function public.join_family_v2(p_code text, p_display text) returns text
language plpgsql security definer set search_path to 'public' as $$
declare fid uuid; fails int; old uuid;
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  fails := (select count(*) from public.join_attempts where user_id = auth.uid() and created_at > now() - interval '1 hour');
  if fails >= 8 then return 'throttled'; end if;
  fid := (select id from public.families where code = upper(regexp_replace(coalesce(p_code,''),'[^A-Za-z0-9]','','g')));
  if fid is null then insert into public.join_attempts(user_id) values (auth.uid()); return 'invalid'; end if;
  old := (select family_id from public.members where user_id = auth.uid());
  insert into public.members as mm (user_id, family_id, display_name)
  values (auth.uid(), fid, left(coalesce(p_display,''),40))
  on conflict (user_id) do update set family_id = excluded.family_id, display_name = excluded.display_name,
    role = case when mm.family_id = excluded.family_id then mm.role else 'member' end;
  if old is not null and old <> fid then perform public._ensure_admin(old); end if;
  return 'ok';
end $$;

create or replace function public.join_family(p_code text, p_display text) returns void
language plpgsql security definer set search_path to 'public' as $$
declare fid uuid; old uuid;
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  select id into fid from public.families where code = upper(regexp_replace(coalesce(p_code, ''), '[^A-Za-z0-9]', '', 'g'));
  if fid is null then raise exception 'invalid code'; end if;
  old := (select family_id from public.members where user_id = auth.uid());
  insert into public.members as mm (user_id, family_id, display_name)
  values (auth.uid(), fid, left(coalesce(p_display, ''), 40))
  on conflict (user_id) do update set family_id = excluded.family_id, display_name = excluded.display_name,
    role = case when mm.family_id = excluded.family_id then mm.role else 'member' end;
  if old is not null and old <> fid then perform public._ensure_admin(old); end if;
end $$;

-- 6. Familie verlassen / Konto löschen: danach hat die Familie immer einen Admin
create or replace function public.leave_family() returns void
language plpgsql security definer set search_path to 'public' as $$
declare f uuid;
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  f := (select family_id from public.members where user_id = auth.uid());
  delete from public.members where user_id = auth.uid();
  perform public._ensure_admin(f);
end $$;

create or replace function public.delete_my_account() returns void
language plpgsql security definer set search_path to 'public', 'auth' as $$
declare f uuid;
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  f := (select family_id from public.members where user_id = auth.uid());
  delete from auth.users where id = auth.uid();
  perform public._ensure_admin(f);
end $$;

-- 7. Neuer Familiencode: nur Admins
create or replace function public.regenerate_family_code() returns text
language plpgsql security definer set search_path to 'public' as $$
declare chars text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; c text; fid uuid;
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  fid := (select family_id from public.members where user_id = auth.uid() and role = 'admin');
  if fid is null then raise exception 'not allowed'; end if;
  loop
    c := '';
    for i in 1..8 loop c := c || substr(chars, 1 + floor(random()*length(chars))::int, 1); end loop;
    exit when not exists (select 1 from public.families where code = c);
  end loop;
  update public.families set code = c where id = fid;
  return c;
end $$;

-- 8. Neu: Rolle ändern (nur Admins, nur in der eigenen Familie, der letzte Admin bleibt Admin)
create or replace function public.set_member_role(p_user uuid, p_role text) returns void
language plpgsql security definer set search_path to 'public' as $$
declare f uuid;
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  if p_role not in ('admin','member') then raise exception 'invalid role'; end if;
  f := (select family_id from public.members where user_id = auth.uid() and role = 'admin');
  if f is null then raise exception 'not allowed'; end if;
  if not exists (select 1 from public.members where user_id = p_user and family_id = f) then raise exception 'not in family'; end if;
  if p_role = 'member' and not exists (select 1 from public.members where family_id = f and role = 'admin' and user_id <> p_user) then
    raise exception 'last admin';
  end if;
  update public.members set role = p_role where user_id = p_user and family_id = f;
end $$;

-- 9. Neu: Person aus der Familie entfernen (nur Admins; ihre Einträge bleiben erhalten; sich selbst über "Familie verlassen")
create or replace function public.remove_member(p_user uuid) returns void
language plpgsql security definer set search_path to 'public' as $$
declare f uuid;
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  f := (select family_id from public.members where user_id = auth.uid() and role = 'admin');
  if f is null then raise exception 'not allowed'; end if;
  if p_user = auth.uid() then raise exception 'use leave_family'; end if;
  if not exists (select 1 from public.members where user_id = p_user and family_id = f) then raise exception 'not in family'; end if;
  delete from public.members where user_id = p_user and family_id = f;
end $$;

-- 10. Nur angemeldete Personen dürfen die neuen Funktionen aufrufen
revoke all on function public.set_member_role(uuid, text) from public, anon;
revoke all on function public.remove_member(uuid) from public, anon;
grant execute on function public.set_member_role(uuid, text) to authenticated;
grant execute on function public.remove_member(uuid) to authenticated;
