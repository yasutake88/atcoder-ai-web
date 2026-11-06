-- Run once in the dedicated Supabase project's SQL Editor.
-- No prompts, submitted code, AI responses, API keys or administrator PINs are stored.
begin;
create table if not exists public.atcoder_request_events (
    request_id uuid primary key,
    is_owner boolean not null
);
alter table public.atcoder_request_events enable row level security;
revoke all on public.atcoder_request_events from public, anon, authenticated;

create table if not exists public.atcoder_request_totals (
    singleton boolean primary key default true check (singleton),
    owner_count bigint not null default 0 check (owner_count >= 0),
    others_count bigint not null default 0 check (others_count >= 0)
);
alter table public.atcoder_request_totals enable row level security;
revoke all on public.atcoder_request_totals from public, anon, authenticated;
insert into public.atcoder_request_totals(singleton) values (true)
on conflict do nothing;

create or replace function public.record_atcoder_request(p_request_id uuid, p_is_owner boolean)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    inserted_count integer;
    own bigint;
    other bigint;
begin
    if p_request_id is null or p_is_owner is null then
        raise exception 'Request id and category are required';
    end if;
    -- A row lock serializes concurrent updates. Both event and totals commit together.
    perform 1 from public.atcoder_request_totals where singleton = true for update;
    insert into public.atcoder_request_events(request_id, is_owner)
    values (p_request_id, p_is_owner) on conflict do nothing;
    get diagnostics inserted_count = row_count;
    if inserted_count = 1 then
        update public.atcoder_request_totals
        set owner_count = owner_count + case when p_is_owner then 1 else 0 end,
            others_count = others_count + case when p_is_owner then 0 else 1 end
        where singleton = true;
    end if;
    select owner_count, others_count into own, other
    from public.atcoder_request_totals where singleton = true;
    return jsonb_build_object('owner', own, 'others', other, 'total', own + other);
end;
$$;
revoke all on function public.record_atcoder_request(uuid, boolean) from public, anon, authenticated;
grant execute on function public.record_atcoder_request(uuid, boolean) to service_role;
commit;
