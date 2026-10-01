create table if not exists public.notes (
  id uuid primary key default gen_random_uuid(), title text not null default 'Untitled',
  content text not null default '', category text, tags text[] not null default '{}',
  note_type text not null default 'note' check (note_type in ('note','todo')),
  is_starred boolean not null default false, created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table if not exists public.todos (
  id uuid primary key default gen_random_uuid(), note_id uuid not null references public.notes(id) on delete cascade,
  text text not null, position integer not null default 0, completed boolean not null default false,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.note_files (
  id uuid primary key default gen_random_uuid(), note_id uuid references public.notes(id) on delete cascade,
  file_name text not null, storage_path text not null unique, mime_type text, file_size bigint not null default 0,
  created_at timestamptz not null default now()
);
create table if not exists public.password_entries (
  id uuid primary key default gen_random_uuid(), name text not null, username text,
  encrypted_password text not null, url text, encrypted_notes text, category text,
  is_starred boolean not null default false, created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists notes_updated_idx on public.notes(updated_at desc);
create index if not exists notes_starred_idx on public.notes(is_starred desc, updated_at desc);
create index if not exists todos_note_idx on public.todos(note_id, position);
create index if not exists note_files_note_idx on public.note_files(note_id);
create index if not exists passwords_starred_idx on public.password_entries(is_starred desc, updated_at desc);
insert into storage.buckets (id, name, public) values ('notes-files', 'notes-files', false) on conflict (id) do nothing;
create or replace function public.get_app_usage() returns table(database_bytes bigint, storage_bytes bigint)
language sql security definer set search_path = public, storage as $$
  select pg_database_size(current_database()), coalesce((select sum(coalesce((metadata->>'size')::bigint,0)) from storage.objects where bucket_id='notes-files'),0)::bigint;
$$;
create or replace function public.set_updated_at() returns trigger language plpgsql as $$ begin new.updated_at=now(); return new; end; $$;
drop trigger if exists notes_updated_at on public.notes;
create trigger notes_updated_at before update on public.notes for each row execute function public.set_updated_at();
drop trigger if exists todos_updated_at on public.todos;
create trigger todos_updated_at before update on public.todos for each row execute function public.set_updated_at();
drop trigger if exists password_entries_updated_at on public.password_entries;
create trigger password_entries_updated_at before update on public.password_entries for each row execute function public.set_updated_at();
