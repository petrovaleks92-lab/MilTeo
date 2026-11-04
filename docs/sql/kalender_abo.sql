-- Kalender-Abo: Token pro Familie + Funktion get_calendar_token(p_reset). Edge-Funktion "cal" liefert die .ics-Datei.
-- (Bereits im Projekt angewendet, hier zur Dokumentation.)
create table if not exists public.calendar_tokens (
  family_id uuid primary key references public.families(id) on delete cascade,
  token text not null unique,
  created_at timestamptz not null default now()
);
alter table public.calendar_tokens enable row level security;
