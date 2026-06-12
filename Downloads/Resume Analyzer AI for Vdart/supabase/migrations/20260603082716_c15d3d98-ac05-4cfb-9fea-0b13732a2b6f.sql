
-- Roles enum
create type public.app_role as enum ('job_seeker', 'recruiter', 'admin');

-- Profiles
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  full_name text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
grant select, insert, update on public.profiles to authenticated;
grant all on public.profiles to service_role;
alter table public.profiles enable row level security;
create policy "profiles_select_own" on public.profiles for select to authenticated using (auth.uid() = id);
create policy "profiles_update_own" on public.profiles for update to authenticated using (auth.uid() = id);
create policy "profiles_insert_own" on public.profiles for insert to authenticated with check (auth.uid() = id);

-- User roles (separate table)
create table public.user_roles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  role public.app_role not null,
  created_at timestamptz not null default now(),
  unique(user_id, role)
);
grant select on public.user_roles to authenticated;
grant all on public.user_roles to service_role;
alter table public.user_roles enable row level security;
create policy "user_roles_select_own" on public.user_roles for select to authenticated using (auth.uid() = user_id);

create or replace function public.has_role(_user_id uuid, _role public.app_role)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.user_roles where user_id = _user_id and role = _role)
$$;

-- Auto-create profile + default role on signup
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name', split_part(new.email,'@',1)));
  insert into public.user_roles (user_id, role)
  values (new.id, coalesce((new.raw_user_meta_data->>'role')::public.app_role, 'job_seeker'));
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Resumes
create table public.resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  raw_text text not null,
  file_name text,
  ats_score int,
  health_score int,
  skills jsonb default '[]'::jsonb,
  experience jsonb default '[]'::jsonb,
  education jsonb default '[]'::jsonb,
  suggestions jsonb default '[]'::jsonb,
  missing_keywords jsonb default '[]'::jsonb,
  summary text,
  analyzed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
grant select, insert, update, delete on public.resumes to authenticated;
grant all on public.resumes to service_role;
alter table public.resumes enable row level security;
create policy "resumes_owner_all" on public.resumes for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "resumes_recruiter_select" on public.resumes for select to authenticated using (public.has_role(auth.uid(), 'recruiter'));

-- Job descriptions
create table public.job_descriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  company text,
  raw_text text not null,
  required_skills jsonb default '[]'::jsonb,
  created_at timestamptz not null default now()
);
grant select, insert, update, delete on public.job_descriptions to authenticated;
grant all on public.job_descriptions to service_role;
alter table public.job_descriptions enable row level security;
create policy "jd_owner_all" on public.job_descriptions for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Match results
create table public.match_results (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  resume_id uuid not null references public.resumes(id) on delete cascade,
  job_description_id uuid not null references public.job_descriptions(id) on delete cascade,
  match_score int not null,
  skill_match jsonb default '{}'::jsonb,
  missing_skills jsonb default '[]'::jsonb,
  matched_skills jsonb default '[]'::jsonb,
  recommendation text,
  created_at timestamptz not null default now()
);
grant select, insert, update, delete on public.match_results to authenticated;
grant all on public.match_results to service_role;
alter table public.match_results enable row level security;
create policy "match_owner_all" on public.match_results for all to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
