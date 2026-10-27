create table if not exists public.bookmarks (
  user_id uuid not null references auth.users(id) on delete cascade,
  publication_id text not null,
  created_at timestamptz not null default now(),
  primary key (user_id, publication_id)
);
alter table public.bookmarks enable row level security;
revoke all on public.bookmarks from anon, authenticated;
grant select, insert, delete on public.bookmarks to authenticated;
create policy "Read own bookmarks" on public.bookmarks for select to authenticated using ((select auth.uid()) = user_id);
create policy "Insert own bookmarks" on public.bookmarks for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "Delete own bookmarks" on public.bookmarks for delete to authenticated using ((select auth.uid()) = user_id);
