-- Raise the monthly allowance to USD 6.25 (JPY 1,000 at 160 JPY/USD).
-- Existing usage, reservations and counters are preserved.
begin;
alter table public.sponsored_settings
  drop constraint if exists sponsored_settings_monthly_micro_usd_check;
alter table public.sponsored_settings
  add constraint sponsored_settings_monthly_micro_usd_check
  check (monthly_micro_usd between 0 and 6250000);
alter table public.sponsored_settings
  alter column monthly_micro_usd set default 6250000;
update public.sponsored_settings
  set monthly_micro_usd = 6250000
  where singleton = true;
commit;
