-- Upgrade reservation for 32,768 output tokens; preserve existing usage and limits.
begin;
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
