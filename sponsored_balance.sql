-- Add read-only balance access. Does not change budgets, usage or counters.
begin;
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
commit;
