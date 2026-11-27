create or replace function private.guard_source_version_immutability()
returns trigger
language plpgsql
as $$
begin
  if tg_op = 'DELETE' then
    raise exception 'Source versions are immutable and cannot be deleted';
  end if;

  if row(
    old.source_id, old.version_number, old.content_sha256, old.page_title,
    old.final_url, old.content_type, old.publication_date, old.effective_date,
    old.fetched_at, old.text_char_count, old.extracted_text, old.metadata,
    old.created_at
  ) is distinct from row(
    new.source_id, new.version_number, new.content_sha256, new.page_title,
    new.final_url, new.content_type, new.publication_date, new.effective_date,
    new.fetched_at, new.text_char_count, new.extracted_text, new.metadata,
    new.created_at
  ) then
    raise exception 'Source version content and provenance fields are immutable';
  end if;

  return new;
end;
$$;

revoke all on function private.guard_source_version_immutability() from public, anon, authenticated;
create trigger source_versions_immutable
before update or delete on private.source_versions
for each row execute function private.guard_source_version_immutability();
