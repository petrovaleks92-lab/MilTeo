create or replace function public.set_my_display_name(p_name text)
returns void
language plpgsql
security definer
set search_path to 'public'
as $$
begin
  if auth.uid() is null then
    raise exception 'not signed in';
  end if;
  update public.members
     set display_name = left(coalesce(p_name, ''), 40)
   where user_id = auth.uid();
end;
$$;

revoke all on function public.set_my_display_name(text) from public, anon;
grant execute on function public.set_my_display_name(text) to authenticated;
