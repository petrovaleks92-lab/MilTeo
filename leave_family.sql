create or replace function public.leave_family()
returns void
language plpgsql
security definer
set search_path to 'public'
as $$
begin
  if auth.uid() is null then
    raise exception 'not signed in';
  end if;
  delete from public.members where user_id = auth.uid();
end;
$$;

revoke all on function public.leave_family() from public, anon;
grant execute on function public.leave_family() to authenticated;
