-- Run in the EXISTING counter project. Existing counts are never reset.
begin;
create table if not exists public.sponsored_settings (
 singleton boolean primary key default true check(singleton),
 enabled boolean not null default true,
 monthly_micro_usd bigint not null default 6250000 check(monthly_micro_usd between 0 and 6250000)
);
insert into public.sponsored_settings(singleton) values(true) on conflict do nothing;
create table if not exists public.sponsored_months (
 month date primary key, used_micro_usd bigint not null default 0 check(used_micro_usd >= 0)
);
create table if not exists public.sponsored_requests (
 request_id uuid primary key, month date not null references public.sponsored_months,
 is_owner boolean not null, charged_micro_usd bigint not null default 160000,
 created_at timestamptz not null default now(), settled boolean not null default false,
 completed boolean not null default false
);
alter table public.sponsored_settings enable row level security;
alter table public.sponsored_months enable row level security;
alter table public.sponsored_requests enable row level security;
revoke all on public.sponsored_settings, public.sponsored_months, public.sponsored_requests from public, anon, authenticated;

create or replace function public.reserve_sponsored_request(p_request_id uuid, p_is_owner boolean)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare cfg public.sponsored_settings%rowtype; m date; spent bigint;
begin
 if p_request_id is null or p_is_owner is null then raise exception 'Missing request'; end if;
 -- One shared lock serializes admission, settlement and month transitions.
 select * into strict cfg from public.sponsored_settings where singleton for update;
 if not cfg.enabled or (now() at time zone 'Asia/Tokyo')::date > date '2027-01-31' then
   return jsonb_build_object('allowed',false,'reason','disabled');
 end if;
 if exists(select 1 from public.sponsored_requests where request_id=p_request_id) then
   return jsonb_build_object('allowed',false,'reason','duplicate');
 end if;
 m := date_trunc('month',now() at time zone 'Asia/Tokyo')::date;
 insert into public.sponsored_months(month) values(m) on conflict do nothing;
 select used_micro_usd into spent from public.sponsored_months where month=m;
 if spent + 160000 > cfg.monthly_micro_usd then
   return jsonb_build_object('allowed',false,'reason','budget');
 end if;
 if exists(select 1 from public.sponsored_requests where created_at > now()-interval '10 seconds') then
   return jsonb_build_object('allowed',false,'reason','busy');
 end if;
 insert into public.sponsored_requests(request_id,month,is_owner) values(p_request_id,m,p_is_owner);
 update public.sponsored_months set used_micro_usd=used_micro_usd+160000 where month=m;
 return jsonb_build_object('allowed',true);
end; $$;

create or replace function public.settle_sponsored_request(p_request_id uuid, p_actual_micro_usd bigint, p_completed boolean)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare r public.sponsored_requests%rowtype; charge bigint; counts jsonb;
begin
 if p_completed is null or p_actual_micro_usd < 0 then raise exception 'Invalid result'; end if;
 perform 1 from public.sponsored_settings where singleton for update;
 select * into strict r from public.sponsored_requests where request_id=p_request_id for update;
 if not r.settled then
   charge := coalesce(p_actual_micro_usd,r.charged_micro_usd);
   update public.sponsored_months set used_micro_usd=used_micro_usd-r.charged_micro_usd+charge where month=r.month;
   update public.sponsored_requests set charged_micro_usd=charge, settled=true, completed=p_completed where request_id=p_request_id;
   -- Unexpected telemetry/price bounds: stop new admissions, never hide an overrun.
   if charge > r.charged_micro_usd then update public.sponsored_settings set enabled=false where singleton; end if;
   if p_completed then
     counts := public.record_atcoder_request(p_request_id,r.is_owner);
   end if;
 end if;
 if counts is null then
   select jsonb_build_object('owner',owner_count,'others',others_count,'total',owner_count+others_count)
   into counts from public.atcoder_request_totals where singleton;
 end if;
 return jsonb_build_object('counts',counts,'used_micro_usd',
   (select used_micro_usd from public.sponsored_months where month=r.month));
end; $$;
revoke all on function public.reserve_sponsored_request(uuid,boolean) from public,anon,authenticated;
revoke all on function public.settle_sponsored_request(uuid,bigint,boolean) from public,anon,authenticated;
grant execute on function public.reserve_sponsored_request(uuid,boolean) to service_role;
grant execute on function public.settle_sponsored_request(uuid,bigint,boolean) to service_role;
create or replace function public.get_sponsored_balance()
returns jsonb language sql stable security definer set search_path = '' as $$
 select jsonb_build_object(
   'month', to_char(date_trunc('month', now() at time zone 'Asia/Tokyo'), 'YYYY-MM'),
   'monthly_micro_usd', s.monthly_micro_usd,
   'used_micro_usd', coalesce(m.used_micro_usd, 0),
   'enabled', s.enabled
 )
 from public.sponsored_settings s
 left join public.sponsored_months m
   on m.month = date_trunc('month', now() at time zone 'Asia/Tokyo')::date
 where s.singleton = true;
$$;
revoke all on function public.get_sponsored_balance() from public, anon, authenticated;
grant execute on function public.get_sponsored_balance() to service_role;
create or replace function public.reserve_sponsored_request_v2(p_request_id uuid, p_is_owner boolean)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare cfg public.sponsored_settings%rowtype; m date; spent bigint;
begin
 if p_request_id is null or p_is_owner is null then raise exception 'Missing request'; end if;
 -- One shared lock serializes admission, settlement and month transitions.
 select * into strict cfg from public.sponsored_settings where singleton for update;
 if not cfg.enabled or (now() at time zone 'Asia/Tokyo')::date > date '2027-01-31' then
   return jsonb_build_object('allowed',false,'reason','disabled');
 end if;
 if exists(select 1 from public.sponsored_requests where request_id=p_request_id) then
   return jsonb_build_object('allowed',false,'reason','duplicate');
 end if;
 m := date_trunc('month',now() at time zone 'Asia/Tokyo')::date;
 insert into public.sponsored_months(month) values(m) on conflict do nothing;
 select used_micro_usd into spent from public.sponsored_months where month=m;
 if spent + 320000 > cfg.monthly_micro_usd then
   return jsonb_build_object('allowed',false,'reason','budget');
 end if;
 if exists(select 1 from public.sponsored_requests where created_at > now()-interval '10 seconds') then
   return jsonb_build_object('allowed',false,'reason','busy');
 end if;
 insert into public.sponsored_requests(request_id,month,is_owner,charged_micro_usd) values(p_request_id,m,p_is_owner,320000);
 update public.sponsored_months set used_micro_usd=used_micro_usd+320000 where month=m;
 return jsonb_build_object('allowed',true,'reserved_micro_usd',320000);
end; $$;
revoke all on function public.reserve_sponsored_request_v2(uuid,boolean) from public,anon,authenticated;
grant execute on function public.reserve_sponsored_request_v2(uuid,boolean) to service_role;
commit;
