-- TrioAgents bookkeeping: Supabase database setup.
-- Run once in Supabase: SQL Editor -> New query -> paste this file -> Run.
-- Safe to run again: it only creates what is missing and replaces functions/policies.

-- =========================================================================
-- 1. User profiles (who is approved, who is admin)
-- =========================================================================
create table if not exists public.profiles (
  id          uuid primary key references auth.users (id) on delete cascade,
  email       text,
  full_name   text,
  approved    boolean     not null default false,
  is_admin    boolean     not null default false,
  created_at  timestamptz not null default now()
);

alter table public.profiles enable row level security;

-- New sign-ups get a profile automatically. The very first user becomes the
-- approved admin; everyone after that waits for admin approval.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  is_first boolean;
begin
  perform pg_advisory_xact_lock(727274);  -- avoid two "first" users at once
  select not exists (select 1 from public.profiles) into is_first;
  insert into public.profiles (id, email, full_name, approved, is_admin)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name'),
    is_first,
    is_first
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Helper checks used by the security rules below.
create or replace function public.is_approved()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select coalesce((select approved from public.profiles where id = auth.uid()), false);
$$;

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select coalesce((select approved and is_admin from public.profiles where id = auth.uid()), false);
$$;

-- Admins cannot remove their own admin rights or approval (prevents lock-out).
create or replace function public.protect_own_admin()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.id = auth.uid() and (new.is_admin is distinct from old.is_admin
                              or new.approved is distinct from old.approved) then
    raise exception 'You cannot change your own approval or admin rights';
  end if;
  return new;
end;
$$;

drop trigger if exists profiles_protect_own_admin on public.profiles;
create trigger profiles_protect_own_admin
  before update on public.profiles
  for each row execute function public.protect_own_admin();

-- Profile rules: you can see your own profile; admins see and change everyone's.
drop policy if exists "profiles: read own or admin" on public.profiles;
create policy "profiles: read own or admin" on public.profiles
  for select to authenticated
  using (id = auth.uid() or public.is_admin());

drop policy if exists "profiles: admin updates" on public.profiles;
create policy "profiles: admin updates" on public.profiles
  for update to authenticated
  using (public.is_admin())
  with check (public.is_admin());

drop policy if exists "profiles: admin deletes others" on public.profiles;
create policy "profiles: admin deletes others" on public.profiles
  for delete to authenticated
  using (public.is_admin() and id <> auth.uid());

-- No insert policy: profiles are only created by the sign-up trigger.

-- =========================================================================
-- 2. Bookkeeping data
-- One row per record. "collection" is agents / cases / pays / lines / settings,
-- "data" holds the record exactly as the app uses it.
-- =========================================================================
create table if not exists public.records (
  collection  text        not null check (collection in ('agents', 'cases', 'pays', 'lines', 'settings')),
  id          text        not null,
  data        jsonb       not null,
  updated_at  timestamptz not null default now(),
  updated_by  uuid        default auth.uid(),
  primary key (collection, id)
);

alter table public.records enable row level security;

create or replace function public.touch_record()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := now();
  new.updated_by := auth.uid();
  return new;
end;
$$;

drop trigger if exists records_touch on public.records;
create trigger records_touch
  before insert or update on public.records
  for each row execute function public.touch_record();

-- Only approved users can read or change data.
drop policy if exists "records: approved users" on public.records;
create policy "records: approved users" on public.records
  for all to authenticated
  using (public.is_approved())
  with check (public.is_approved());

-- Logged-out visitors get nothing at all.
revoke all on public.records  from anon;
revoke all on public.profiles from anon;

-- Live updates: every open browser is told about changes immediately.
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'records'
  ) then
    alter publication supabase_realtime add table public.records;
  end if;
end;
$$;

-- =========================================================================
-- 3. Keep-alive
-- Free Supabase projects pause after a week with no activity. The GitHub
-- workflow in .github/workflows/keep-supabase-awake.yml calls this every few days.
-- It returns nothing but "ok" and reads no data.
-- =========================================================================
create or replace function public.ping()
returns text
language sql
stable
as $$ select 'ok'::text; $$;

grant execute on function public.ping() to anon;
