-- Lesebestätigung im Familien-Chat: pro Person ein Zeitstempel «gelesen bis».
-- Nur ERGÄNZUNG: 1 neue Tabelle, es wird nichts geändert oder gelöscht.
create table if not exists public.message_reads (
  family_id uuid not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  last_read_at timestamptz not null default now(),
  primary key (family_id, user_id)
);
alter table public.message_reads enable row level security;

drop policy if exists message_reads_select on public.message_reads;
create policy message_reads_select on public.message_reads for select to authenticated
  using (family_id = public.my_family());

drop policy if exists message_reads_insert on public.message_reads;
create policy message_reads_insert on public.message_reads for insert to authenticated
  with check (user_id = auth.uid() and family_id = public.my_family());

drop policy if exists message_reads_update on public.message_reads;
create policy message_reads_update on public.message_reads for update to authenticated
  using (user_id = auth.uid() and family_id = public.my_family())
  with check (user_id = auth.uid() and family_id = public.my_family());

-- Echtzeit, damit die Häkchen sofort umspringen
do $$ begin
  alter publication supabase_realtime add table public.message_reads;
exception when duplicate_object then null; end $$;
