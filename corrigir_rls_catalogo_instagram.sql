-- Execute este arquivo no SQL Editor do Supabase se aparecer erro 42501/RLS
-- na importacao ou edicao do catalogo do Instagram.

alter table singelo_catalogo_instagram enable row level security;

drop policy if exists "catalogo_publico_select" on singelo_catalogo_instagram;
drop policy if exists "catalogo_admin_select" on singelo_catalogo_instagram;
drop policy if exists "catalogo_admin_insert" on singelo_catalogo_instagram;
drop policy if exists "catalogo_admin_update" on singelo_catalogo_instagram;
drop policy if exists "catalogo_admin_delete" on singelo_catalogo_instagram;

-- O catalogo publico precisa ler apenas produtos ativos.
create policy "catalogo_publico_select"
on singelo_catalogo_instagram
for select
to anon
using (active = true);

-- O sistema administrativo usa a mesma chave anon pelo Streamlit,
-- por isso precisa gravar e revisar os produtos importados.
create policy "catalogo_admin_select"
on singelo_catalogo_instagram
for select
to anon
using (true);

create policy "catalogo_admin_insert"
on singelo_catalogo_instagram
for insert
to anon
with check (true);

create policy "catalogo_admin_update"
on singelo_catalogo_instagram
for update
to anon
using (true)
with check (true);

create policy "catalogo_admin_delete"
on singelo_catalogo_instagram
for delete
to anon
using (true);