-- Execute uma vez no SQL Editor do Supabase.
-- Cria armazenamento publico e permanente para as fotos do catalogo.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('catalogo-imagens', 'catalogo-imagens', true, 10485760, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do update set public = excluded.public, file_size_limit = excluded.file_size_limit, allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "catalogo_imagens_select" on storage.objects;
drop policy if exists "catalogo_imagens_insert" on storage.objects;
drop policy if exists "catalogo_imagens_update" on storage.objects;

create policy "catalogo_imagens_select" on storage.objects for select to anon using (bucket_id = 'catalogo-imagens');
create policy "catalogo_imagens_insert" on storage.objects for insert to anon with check (bucket_id = 'catalogo-imagens');
create policy "catalogo_imagens_update" on storage.objects for update to anon using (bucket_id = 'catalogo-imagens') with check (bucket_id = 'catalogo-imagens');
