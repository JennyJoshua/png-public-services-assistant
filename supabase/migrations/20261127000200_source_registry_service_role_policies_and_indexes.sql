create policy service_role_full_access on private.source_registry
  for all to service_role using (true) with check (true);
create policy service_role_full_access on private.source_refresh_runs
  for all to service_role using (true) with check (true);
create policy service_role_full_access on private.source_versions
  for all to service_role using (true) with check (true);
create policy service_role_full_access on private.source_assessment_decisions
  for all to service_role using (true) with check (true);
create policy service_role_full_access on private.source_refresh_results
  for all to service_role using (true) with check (true);
create policy service_role_full_access on private.source_exceptions
  for all to service_role using (true) with check (true);

create index source_registry_active_version_idx on private.source_registry(active_version_id);
create index source_assessment_decisions_version_idx on private.source_assessment_decisions(version_id);
create index source_assessment_decisions_run_idx on private.source_assessment_decisions(refresh_run_id);
create index source_refresh_results_source_idx on private.source_refresh_results(source_id);
create index source_refresh_results_version_idx on private.source_refresh_results(version_id);
create index source_exceptions_source_idx on private.source_exceptions(source_id);
create index source_exceptions_version_idx on private.source_exceptions(version_id);
create index source_exceptions_run_idx on private.source_exceptions(refresh_run_id);
