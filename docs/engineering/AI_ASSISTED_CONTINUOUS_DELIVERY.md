# AI-Assisted Continuous Delivery (AI-ACD)
## Portfolio Operating Procedure v1.0 — Pilot

**Status:** Proposed operating standard for owner review  
**Pilot repository:** `JennyJoshua/png-public-services-assistant`  
**Tracking issue:** #31  
**Applies to:** Current and future software projects using GitHub, Supabase, Render, or comparable services  
**Primary objective:** Deliver useful, reliable software in small verified increments while reducing rework, repeated handovers, avoidable failures and unnecessary owner interruptions.

This procedure governs how work is delivered. It does not override a project's approved product requirements, architecture, backlog, security rules, licensing obligations or approval gates.

---

## 1. Operating principles

1. **One source of truth:** GitHub is the authoritative record for code, tasks, decisions, reviews and delivery evidence. Chat conversations coordinate work but must not be the only home for durable project decisions.
2. **Small batches:** Implement the smallest independently testable change that advances an approved outcome. Prefer work that can be reviewed in hours or a few days, not large multi-week branches.
3. **Inspect before changing:** Confirm repository, default branch, current commit, working branches, open PRs/issues, relevant files and existing tests before implementation.
4. **Reuse before rebuilding:** Search for existing components, scripts, workflows, schemas and decisions. Do not duplicate functioning infrastructure.
5. **Automate repeatable checks:** CI should run deterministic checks on every PR. Do not rely on memory or manual assurances.
6. **Evidence before claims:** Report what was actually changed and which checks actually ran. A successful build does not prove production readiness.
7. **Secure and reversible by default:** Minimise permissions, protect secrets, avoid destructive operations and define recovery before risky changes.
8. **No unapproved scope drift:** Technical implementation choices must remain within the approved project baseline.
9. **Free-first:** Prefer existing free capabilities and avoid paid services, upgrades or new recurring costs without explicit approval.
10. **Stop on blocked prerequisites:** Do not build downstream features on an unresolved failing test, unknown schema, unverified hosting assumption or missing required decision.

## 2. Roles and decision rights

### Project owner
- Sets product priorities, business rules and acceptance outcomes.
- Approves material scope or architecture changes.
- Explicitly approves production deployments, production-impacting configuration changes, destructive actions, paid services/upgrades and hosted database migrations.
- Reviews and approves implementation PRs for merge under the project's existing rules.
- Supplies credentials or performs account-side steps when access is unavailable; secrets must never be pasted into issues or source files.

### ChatGPT — delivery lead
- Maintains the project plan and coordinates implementation, testing, review and release preparation.
- Inspects the current repository before each implementation batch.
- Makes routine technical decisions within the approved scope.
- Creates and updates GitHub Issues/PRs and project documentation where authorised.
- Reviews changes independently of the implementation summary and checks the evidence.
- Raises only decisions that require owner input.
- Does not claim access, execution, test results or deployment success that has not been verified.

### Other AI/coding agents
- Are assigned one bounded task with repository, branch, scope, acceptance criteria and expected evidence.
- Must report files changed, commits/PRs, tests run, results, known limitations and unverified items.
- Must not independently merge, deploy, run destructive operations or expand scope.
- Avoid parallel agents editing the same files or implementing overlapping tasks.

### External services
- GitHub stores source and delivery records and runs CI.
- Supabase provides database/auth/storage where selected by the project.
- Render (or approved host) runs application services.
- Service dashboards are operational interfaces, not substitutes for version-controlled source configuration and migration history.

## 3. Standard delivery lifecycle

### Gate 0 — Project and task readiness

Before a new project or major phase:
- Confirm product objective, target users, MVP boundary and business rules.
- Identify approved architecture, constraints, licensing and data/security requirements.
- Identify hosting, database and AI-provider dependencies.
- Record decisions and unresolved questions in GitHub.
- Establish a definition of done and the first measurable milestone.

Before an individual task starts, its GitHub Issue must state:
- User or system outcome.
- In-scope and explicitly out-of-scope work.
- Acceptance criteria that can be checked.
- Likely affected components/files, if known.
- Required tests and evidence.
- Database, security, hosting or migration impact.
- Dependencies and approval requirements.

If a prerequisite is unresolved, mark the issue blocked and work on the prerequisite instead.

### Gate 1 — Repository inspection

At the start of each implementation batch:
- Confirm repository full name, default branch and latest main commit.
- Inspect current branch and uncommitted/unfinished work where tool access permits.
- Review relevant source files, manifests, lockfiles, tests and CI workflows.
- Check open issues, open PRs, recent merges and latest CI results.
- Identify existing conventions and avoid conflicting parallel work.
- Compare the proposed change with the approved architecture and backlog.

Never rely solely on an old chat handover when the live repository can be inspected.

### Gate 2 — Implementation

- Create a short-lived branch from the latest appropriate base.
- Use a descriptive branch name, e.g. `feat/<issue>-short-name`, `fix/<issue>-short-name` or `docs/<issue>-short-name`.
- Implement one coherent change per branch/PR.
- Avoid unrelated formatting, refactors or dependency changes.
- Keep changes small enough to understand and review.
- Add or update tests alongside the behaviour they protect.
- Keep secrets, personal data and generated private datasets out of commits.
- Link every PR to its tracking Issue.

Do not start another implementation task in the same project while the current task has unresolved CI failures or an unreviewed dependency. Portfolio focus should normally be one active implementation stream at a time; parallel work is an exception for independent, non-conflicting tasks.

### Gate 3 — Automated verification

Every PR must run the relevant checks for its stack. Use the repository's existing toolchain and lockfiles.

**Frontend**
- Deterministic dependency installation (e.g. `npm ci` when a valid npm lockfile exists).
- Type checking.
- Lint/format checks.
- Unit/component tests where present.
- Production build.

**Backend**
- Locked/reproducible dependency installation where supported.
- Unit and integration tests.
- Type/lint checks where configured.
- API contract and input-validation tests.
- Security-sensitive tests for authentication, authorisation and data access.

**Database (when applicable)**
- Migration syntax and ordering checks.
- Apply migrations to a disposable/local test database.
- Verify schema, constraints, indexes and foreign keys.
- Test Row Level Security policies as the relevant roles, including unauthorised access.
- Verify application compatibility with the changed schema.
- Never treat a successful SQL parse as proof of correct access control.

**General**
- CI should run on every pull request targeting the protected integration branch.
- Use explicit least-privilege workflow permissions.
- Use dependency caching only when based on the actual lockfile.
- Cancel obsolete duplicate CI runs where safe.
- Pin third-party actions to reviewed immutable versions/SHA where practical.
- Add secret/dependency/code scanning when supported without introducing unapproved paid services.
- Keep required checks distinct from optional preview/deploy integrations.
- A canceled external preview check is not a passing test; determine whether the actual required CI jobs passed.

If any required check fails, stop feature expansion. Diagnose the first failing cause, fix it, rerun the relevant checks and record the result. Do not merge around a failure without an explicit, documented exception from the owner.

### Gate 4 — Independent review

Before asking for owner review, the delivery lead checks:
- PR diff against the target branch.
- Scope and approved-baseline compliance.
- Correctness, edge cases and regression risks.
- Security, privacy, secrets and permissions.
- Database/hosting/production impact.
- Tests and CI results on the latest commit.
- Documentation and rollback implications.
- Whether the PR is appropriately small and can be understood.

The PR description must include:
1. What changed and why.
2. Issue link and acceptance criteria.
3. Files/components affected.
4. Tests run and exact results.
5. Security/data/DB/hosting impact.
6. Deployment impact and rollback notes.
7. Known limitations and unverified assumptions.
8. Explicit statement of any required owner approval.

### Gate 5 — Owner review and merge

- Present the PR link, concise review result, CI evidence, risks and requested decision.
- Never merge solely because CI is green.
- Preserve the project's explicit owner-approval requirements.
- Do not use auto-merge to bypass the owner approval gate.
- After approval and merge, verify the merge commit and resulting branch state.
- Close the linked Issue only when its acceptance criteria are met.

### Gate 6 — Deployment and runtime verification

- Confirm the intended environment, branch, commit and deployment trigger.
- Check environment variables by name/presence only; never expose secret values.
- Confirm health/readiness endpoints and service logs.
- Deploy to a non-production target first where available and approved.
- Production deployment requires explicit owner approval.
- After deployment, verify the running version, health endpoint, core user journey and relevant error logs.
- If verification fails, stop further rollout and follow the recovery plan.
- Record the deployed commit and verification evidence in the PR/Issue.

### Gate 7 — Completion and learning

A task is done only when:
- Acceptance criteria are met.
- Required tests pass on the final commit.
- Review and required approvals are complete.
- The change is merged through the approved process.
- Deployment is verified if deployment was in scope.
- Relevant documentation and tracking records are updated.
- Remaining risks or follow-up tasks are explicit.

Capture repeated failures as regression tests or process improvements, not just one-off fixes.

---

## 4. Supabase operating standard

For projects using Supabase:

1. Treat migration files committed to GitHub as the source of truth for schema evolution.
2. Use separate development/test and production environments where available and affordable.
3. Create migrations for schema, policies, functions, triggers and other database changes; avoid undocumented dashboard-only schema edits.
4. Test migrations against a disposable/local database before hosted application.
5. Test RLS using anon, authenticated and privileged roles as applicable. Confirm both permitted and denied access.
6. Keep service-role keys and database credentials server-side and out of client bundles, issues, logs and commits.
7. Back up or confirm recovery options before risky production data changes.
8. Obtain explicit owner approval before applying hosted/production migrations or destructive data changes.
9. Prefer forward-fix migrations for production recovery. A down migration is not automatically safe, especially after data has changed.
10. Reconcile any unavoidable emergency dashboard change back into a reviewed migration promptly.

A migration passing locally is not authorisation to apply it to production.

## 5. Render and hosting operating standard

For projects using Render:

1. Keep deployment configuration and build/start commands documented and version-controlled where supported.
2. Distinguish static sites, web services, background workers and databases; do not assume their persistence or pricing is the same.
3. Do not assume a free service's local filesystem is durable. Use persistent storage only after verifying availability, cost and project approval.
4. Use environment groups/secrets securely; never commit secret values.
5. Define health checks and a lightweight smoke-test path.
6. Verify the deployed commit and runtime logs after release.
7. Document application rollback to a known-good commit/release.
8. Treat database migrations separately from application rollback. Restoring old application code does not reverse a schema change.
9. Do not create paid services, upgrade plans, alter production environment settings or trigger production-impacting deployment without explicit approval.
10. Do not interpret missing metrics as zero usage; label unavailable telemetry accurately.

## 6. Security and data handling

- Apply least privilege to GitHub tokens, CI permissions, Supabase roles and service credentials.
- Never commit API keys, service-role keys, passwords, private learner/customer data or production database exports.
- Use synthetic or anonymised fixtures in tests.
- Validate user input and external content; treat retrieved documents and web pages as untrusted data.
- Protect against prompt injection by separating data from instructions and enforcing deterministic application controls.
- Minimise logs; do not log full private conversations or uploaded documents unless explicitly required and approved.
- Review dependency changes for necessity, licence, maintenance and known vulnerabilities.
- Report a suspected secret exposure or security incident immediately; rotate/revoke affected credentials through the owner-approved process.

## 7. Approval matrix

| Action | Default authority |
|---|---|
| Inspect repository, read files, review CI | Delivery lead |
| Create/update scoped Issues and documentation | Delivery lead |
| Routine implementation within approved scope | Delivery lead |
| Run non-production tests that do not incur cost or affect real data | Delivery lead |
| Create implementation branch and PR | Delivery lead |
| Merge PR / change main | Explicit owner approval |
| Production deployment or production configuration change | Explicit owner approval |
| Hosted/production Supabase migration | Explicit owner approval |
| Destructive data, repository or infrastructure action | Explicit owner approval |
| Paid service, upgrade or recurring commitment | Explicit owner approval |
| Material product, scope or architecture change | Explicit owner approval |
| Share credentials or sensitive data with another agent | Not permitted without explicit, secure owner-directed process |

Project-specific rules may be stricter and always take precedence.

## 8. AI handover and capability-failure rule

- Prefer direct work from the repository and GitHub records over repeated manual handovers.
- Delegate only a bounded task with exact expected outputs.
- Require agents to return commit/PR links and test evidence, not just a narrative claim.
- Do not ask multiple agents to edit the same branch or files concurrently.
- If a required capability is unavailable, state the limitation and stop the dependent work rather than inventing results.
- For this owner's data-analysis rule: if the dedicated Data Analysis capability is unavailable for a task that genuinely requires it, stop that analysis and prepare a ready-to-paste handover for the user's designated alternative workflow. Ordinary repository inspection, code review and deterministic tests may continue if they do not depend on that capability.

## 9. Delivery metrics

Establish a baseline during the pilot before setting numerical targets. Track:
- Issue cycle time (start to accepted completion).
- PR lead time (opened to merged).
- First-pass required-CI success rate.
- Reopened/reworked issues and escaped defects.
- Deployment success and rollback frequency.
- Time to restore service after a failure.
- Blocked time caused by missing decisions, access or dependencies.

Use trends to identify bottlenecks. Do not reward raw PR count or code volume; a small, correct change is more valuable than a large change that creates rework.

## 10. Pilot rollout plan — PNG Public Services Assistant

This pilot changes the delivery process only. The approved Bounded Adaptive RAG Technical Architecture and Interface Specification v1.0 and its seven-batch implementation backlog remain the controlling product/technical baseline.

### Pilot step 1 — Process baseline and records
- Adopt this SOP after owner review.
- Reconcile stale issue/PR status, beginning with Batch 0 issue #15 and the already merged PRs #29 and #30.
- Add reusable issue and PR templates only after inspecting existing templates and avoiding duplication.
- Record a baseline for task cycle time, CI first-pass success and rework using available evidence.

### Pilot step 2 — CI reliability improvements
- Review the existing `.github/workflows/ci.yml` against this SOP.
- Evaluate switching from `npm install --ignore-scripts` to `npm ci` because a package lockfile exists.
- Ensure npm caching keys use the lockfile.
- Add safe concurrency cancellation and least-privilege permissions where appropriate.
- Verify CI runs for PRs and the intended branch patterns.
- Preserve backend and frontend checks; do not weaken or remove existing tests.
- Deliver workflow changes as a separate PR with CI evidence. Do not merge automatically.

### Pilot step 3 — Review and security templates
- Add a concise PR template and issue template if equivalent templates do not already exist.
- Include acceptance criteria, test evidence, data/security impact, deployment and rollback fields.
- Evaluate secret/dependency scanning available on the current GitHub plan; do not assume paid features are available.

### Pilot step 4 — Database and hosting readiness standards
- Document the repository-specific Supabase/Render status and exact safeguards only after inspecting the actual linked project configuration.
- Do not create a Supabase project, run migrations, alter Render configuration, trigger a production deployment or purchase a service as part of this process pilot.
- Keep the existing Batch 0 non-production hosting validation and RAG backlog in their existing tracking issues.

### Pilot step 5 — Measure and decide
- Run the SOP for at least three completed small delivery tasks or one full delivery batch, whichever provides sufficient evidence.
- Compare cycle time, CI first-pass rate and rework with the baseline.
- Record what reduced effort and what introduced overhead.
- Revise the SOP before portfolio-wide rollout if evidence supports changes.

### Pilot exit criteria
- A small task can be traced from Issue to PR, CI, review, merge approval and (where applicable) verified deployment.
- No owner approval gate is bypassed.
- CI and test evidence is reproducible.
- Stale project status is reconciled.
- The measured workflow is simpler or more reliable than the baseline.
- A reusable starter/template backlog is ready for the remaining repositories.

---

## 11. Portfolio rollout after the pilot

After pilot acceptance:
1. Extract generic issue/PR templates and CI patterns into a reusable starter.
2. Apply the SOP to each repository only after a repository-specific inspection.
3. Adapt CI to each framework rather than copying incompatible commands.
4. Preserve each project's own architecture, business rules, hosting and security requirements.
5. Prioritise active projects; do not launch a simultaneous portfolio-wide refactor.
6. Review delivery metrics monthly and update the standard only when evidence justifies it.

**Versioning:** This is v1.0 proposed for pilot. Changes to this operating standard are documented with a short rationale and owner approval where they affect decision rights or approval gates.
