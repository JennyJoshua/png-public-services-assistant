create schema if not exists private;

revoke all on schema private from public;
revoke all on schema private from anon, authenticated;
grant usage on schema private to service_role;

create table private.source_registry (
    id uuid primary key default gen_random_uuid(),
    source_key text not null unique,
    registered_url text not null unique,
    canonical_url text,
    institution text not null,
    topic text not null,
    authority_profile text,
    source_class text not null default 'unverified_unsafe'
      check (source_class in ('approved_authoritative','recognised_institutional','general_web','unverified_unsafe')),
    status text not null default 'pending_review'
      check (status in ('pending_review','active','broken','superseded','excluded')),
    status_reason text,
    active_version_id uuid,
    last_attempt_at timestamptz,
    last_success_at timestamptz,
    next_refresh_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table private.source_refresh_runs (
    id uuid primary key default gen_random_uuid(),
    trigger_type text not null default 'scheduled'
      check (trigger_type in ('scheduled','manual','startup','retry')),
    workflow_run_id text,
    workflow_run_url text,
    status text not null default 'running'
      check (status in ('running','completed','partial','failed')),
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    source_count integer not null default 0 check (source_count >= 0),
    fetched_count integer not null default 0 check (fetched_count >= 0),
    activated_count integer not null default 0 check (activated_count >= 0),
    held_count integer not null default 0 check (held_count >= 0),
    excluded_count integer not null default 0 check (excluded_count >= 0),
    failure_count integer not null default 0 check (failure_count >= 0),
    summary jsonb not null default '{}'::jsonb
);

create table private.source_versions (
    id uuid primary key default gen_random_uuid(),
    source_id uuid not null references private.source_registry(id) on delete restrict,
    version_number integer not null check (version_number > 0),
    content_sha256 text not null check (content_sha256 ~ '^[a-f0-9]{64}$'),
    page_title text not null,
    final_url text not null,
    content_type text not null,
    publication_date date,
    effective_date date,
    fetched_at timestamptz not null,
    text_char_count integer not null check (text_char_count >= 0),
    extracted_text text not null,
    version_state text not null default 'candidate'
      check (version_state in ('candidate','accepted','held','rejected','superseded')),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (source_id, version_number),
    unique (source_id, content_sha256)
);

alter table private.source_registry
  add constraint source_registry_active_version_fk
  foreign key (active_version_id) references private.source_versions(id)
  on delete restrict;

create table private.source_assessment_decisions (
    id uuid primary key default gen_random_uuid(),
    source_id uuid not null references private.source_registry(id) on delete restrict,
    version_id uuid references private.source_versions(id) on delete restrict,
    refresh_run_id uuid references private.source_refresh_runs(id) on delete set null,
    policy_version text not null,
    action text not null check (action in ('activate','hold','exclude')),
    source_class text not null
      check (source_class in ('approved_authoritative','recognised_institutional','general_web','unverified_unsafe')),
    confidence numeric(4,3) check (confidence >= 0 and confidence <= 1),
    hard_gates jsonb not null default '{}'::jsonb,
    reasons jsonb not null default '[]'::jsonb,
    assessment_input jsonb not null default '{}'::jsonb,
    decided_at timestamptz not null default now()
);

create table private.source_refresh_results (
    id uuid primary key default gen_random_uuid(),
    refresh_run_id uuid not null references private.source_refresh_runs(id) on delete cascade,
    source_id uuid not null references private.source_registry(id) on delete restrict,
    version_id uuid references private.source_versions(id) on delete restrict,
    outcome text not null
      check (outcome in ('unchanged','candidate_created','activated','held','excluded','fetch_failed','skipped')),
    http_status integer,
    final_url text,
    error_code text,
    error_message text,
    duration_ms integer check (duration_ms is null or duration_ms >= 0),
    created_at timestamptz not null default now(),
    unique (refresh_run_id, source_id)
);

create table private.source_exceptions (
    id uuid primary key default gen_random_uuid(),
    source_id uuid not null references private.source_registry(id) on delete restrict,
    version_id uuid references private.source_versions(id) on delete restrict,
    refresh_run_id uuid references private.source_refresh_runs(id) on delete set null,
    category text not null,
    severity text not null default 'warning'
      check (severity in ('info','warning','critical')),
    status text not null default 'open'
      check (status in ('open','retrying','resolved','closed')),
    attempt_count integer not null default 0 check (attempt_count >= 0),
    next_retry_at timestamptz,
    details jsonb not null default '{}'::jsonb,
    first_seen_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    resolved_at timestamptz
);

create index source_registry_status_idx on private.source_registry(status);
create index source_registry_next_refresh_idx on private.source_registry(next_refresh_at);
create index source_versions_source_created_idx on private.source_versions(source_id, created_at desc);
create index source_decisions_source_decided_idx on private.source_assessment_decisions(source_id, decided_at desc);
create index source_refresh_runs_started_idx on private.source_refresh_runs(started_at desc);
create index source_refresh_results_run_idx on private.source_refresh_results(refresh_run_id);
create index source_exceptions_retry_idx on private.source_exceptions(status, next_retry_at);

alter table private.source_registry enable row level security;
alter table private.source_refresh_runs enable row level security;
alter table private.source_versions enable row level security;
alter table private.source_assessment_decisions enable row level security;
alter table private.source_refresh_results enable row level security;
alter table private.source_exceptions enable row level security;

revoke all on all tables in schema private from public, anon, authenticated;
grant select, insert, update, delete on all tables in schema private to service_role;
alter default privileges in schema private
  revoke all on tables from public, anon, authenticated;
alter default privileges in schema private
  grant select, insert, update, delete on tables to service_role;
