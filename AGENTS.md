# KenTender Repository Instructions

KenTender is a modular public-procurement platform built on Frappe/ERPNext v16. Treat this repository as production-oriented, governance-sensitive software: preserve legal/process meaning, app boundaries, permissions, auditability, and test evidence.

## Instruction precedence and conflicts

Apply guidance in this order:

1. The user's current explicit request and acceptance criteria.
2. The task-specific implementation pack or specification explicitly named by the user.
3. The closest applicable nested `AGENTS.md` or `AGENTS.override.md`.
4. This repository-level file.
5. Current, non-archived architecture and module documentation.

Do not infer that the words “never” or “do not” in an older document automatically override a newer explicit instruction. If two applicable sources materially conflict, stop before editing, identify the exact conflict and affected files, and ask for direction.

Archived documents and retired code are historical reference only unless the task explicitly targets them.

## Repository boundary

- The repository root is `frappe-bench/apps/kentender_v1/`; it is a container repository, not a Frappe app named `kentender_v1`.
- Frappe apps are the top-level `kentender_*` directories in this repository. Bench exposes them through symlinks under the repository's `apps/` directory; see `docs/architecture/mono-repo-v2.md` and the root `Makefile`.
- Work only inside this repository unless the task explicitly requires inspection elsewhere.
- Treat sibling bench apps (`frappe`, `erpnext`, `hrms`, and third-party apps) as read-only references. Do not modify them unless the user explicitly authorizes a framework or upstream-app change.
- Do not inspect or expose secrets, site configuration, private files, environment directories, database dumps, or logs unless the task specifically requires them. Never print credentials or tokens.
- Generated or transient directories such as `node_modules/`, `playwright-report/`, `test-results/`, caches, and built assets are not source files. Do not hand-edit or commit generated output unless the repository intentionally tracks it.

## App set and dependency direction

The allowed v3 apps are:

- `kentender_core`
- `kentender_strategy`
- `kentender_budget`
- `kentender_procurement`
- `kentender_suppliers`
- `kentender_governance`
- `kentender_compliance`
- `kentender_stores`
- `kentender_assets`
- `kentender_integrations`
- `kentender_transparency`

Do not create another app or parallel replacement module unless explicitly approved.

The primary dependency direction is:

`core -> strategy -> budget -> procurement -> stores -> assets`

Side apps (`suppliers`, `governance`, `compliance`, `integrations`, and `transparency`) consume published interfaces. Respect ownership and the detailed map in `docs/architecture/dependency-map-v3.md`.

- Do not add reverse dependencies or deep imports into another app's internals.
- Put shared primitives and cross-app contracts in the owning public interface, normally `kentender_core` when genuinely cross-cutting.
- Do not move behavior between apps merely to make an implementation easier.
- Before a cross-app change, identify the owning app, consumers, public contract, and dependency impact.

## Read only the context the task needs

Start with repository inspection and the files or implementation pack named in the task. Do not load every architecture document by default.

Read `docs/architecture/README.md` for routing when the relevant source is unclear. Read these documents when the change is architecture-sensitive, cross-app, or introduces a domain/workflow boundary:

- `docs/architecture/kentender_architecture_rules_v3.md`
- `docs/architecture/global-architecture-v3.md`
- `docs/architecture/dependency-map-v3.md`

Read `docs/prompts/architecture/architecture-restructure-cursor-prompt-pack.md` only for an explicitly requested architecture restructure or phased ticket from that pack. Despite its filename, treat it as a task specification, not as automatically loaded Cursor behaviour.

For module work, prefer the current PRD, domain/state model, role-permission matrix, UI specification, seed specification, and tests for that module. Ignore superseded drafts in `archive/` directories unless asked to compare or recover them.

If documentation, tests, and current code disagree materially, do not silently select one. Report the mismatch and use the user's stated task as the controlling scope.

## Working method

### Before editing

1. Inspect the relevant repository area and `git status`; preserve all existing user changes.
2. Confirm the task mode:
   - For review, explanation, planning, or diagnosis, do not implement unless explicitly asked.
   - For a requested change or build, implement it and validate it.
3. Trace the existing implementation before proposing a new one. Reuse established services, APIs, components, test helpers, and patterns.
4. Define the smallest coherent change. Do not mix unrelated cleanup, speculative refactoring, or future phases into the task.
5. For a substantive change, state briefly before the first edit:
   - goal and acceptance criteria;
   - affected apps and likely files;
   - explicit scope exclusions;
   - validation plan.

Use Plan mode for ambiguous, multi-app, migration, workflow, permission, or architecture-sensitive work. A small localized correction does not require a ceremonial plan.

### While editing

- Make the smallest maintainable change that fully satisfies the requirement.
- Preserve public behaviour and compatibility outside the stated scope.
- Do not create duplicate modules, compatibility scaffolding, shadow workflows, or temporary bypasses unless explicitly required.
- Do not invent missing business rules, roles, approvals, workflow states, identifiers, or legal outcomes. Surface the decision needed.
- Do not add or upgrade production dependencies without explaining the need and receiving approval.
- Do not modify unrelated files, reformat broad areas, or overwrite user changes.
- Do not run destructive Git operations. Do not commit, push, merge, rebase, or amend unless explicitly requested.
- Comments should explain non-obvious business or technical reasons, not restate the code.

### Before completion

1. Review the complete diff for scope creep, permission gaps, architectural violations, and accidental generated-file changes.
2. Run the narrowest relevant checks first, then the appropriate broader tests for affected contracts.
3. Never claim a test or manual flow passed unless it was actually run. Report blocked or skipped validation with the reason.
4. Confirm that the result matches the named requirement or acceptance criteria—not merely that the code compiles.

## Frappe engineering rules

- Keep business logic in explicit Python service modules, not in DocType controllers, page JavaScript, or client-only handlers.
- Keep DocType controllers thin: lifecycle delegation, invariant enforcement, and calls into the owning service layer.
- Expose cross-layer operations through explicit, minimal APIs with stable inputs and outputs.
- Enforce critical validation, authorization, scope, state transitions, and financial/business rules on the server. Client validation may improve UX but is never the sole control.
- Use Frappe's permission and ORM facilities unless a reviewed exception is required. Do not bypass permissions or write directly to the database for convenience.
- Make retriable actions idempotent where duplicate execution could create approvals, reservations, submissions, awards, ledger effects, or audit events.
- Preserve audit trails and actor/time/reason data for material workflow decisions.
- Do not invent hidden workflow states. User-visible status, server state, permitted actions, and audit history must agree.
- Use explicit patches/migrations for persistent schema or data changes. Do not disguise migrations as runtime side effects.
- Keep APIs and services independent of a particular page where the capability is a domain operation.

For Frappe-managed scaffolding:

- Create apps with `bench new-app`.
- Create sites with `bench new-site`.
- Generate DocType scaffolds through Frappe's standard creation/export flow.
- Do not simulate unavailable generator output by handwriting framework scaffolds.
- If a required generator cannot be run safely, provide the exact command and report the blocker instead of fabricating the result.

## Product and workflow rules

- Preserve the canonical business traceability chain: Strategy -> Budget -> Demand/Requisition -> Plan -> Tender -> Bid -> Evaluation -> Award -> Contract -> Inspection -> Stores/Assets.
- Preserve app ownership, record lineage, approval evidence, and role/organizational scope across that chain.
- Do not simplify away governance, reservations, role queues, exception handling, reapproval, or audit behaviour merely to complete a happy path.
- Material changes to an approved requirement, value, funding, timing, procurement route, evaluation, or award must follow the applicable amendment/reapproval rules; do not mutate an approved baseline silently.
- Every server action must define eligible source state, required role/scope, validation, resulting state, audit effect, and failure behaviour.
- No module is considered implementation-ready solely because screens exist. Follow the applicable PRD, domain/state model, role-permission matrix, UI specification, seed specification, and smoke contracts.

## UI and navigation

- Prefer the approved workspace-first pattern: landing/workspace -> queue -> detail/workspace -> guided builder or form. Do not fall back to raw DocType-first UX where a product workspace is specified.
- Stitch output is approved design input, not production architecture. Hand-port it into maintainable Frappe pages, components, CSS, and APIs. Do not ship static mock shells, iframes, duplicated fake data, or client-side business behaviour copied from a mockup.
- Preserve the repository's design tokens, accessibility behaviour, responsive layout, test IDs, and established shared components.
- Avoid developer-oriented instructions in end-user UI. Copy must describe the user's decision, evidence, consequence, and next action.

For workbench-to-builder/form navigation, use the shared `kentender_core` shell and the canonical specification:

`docs/prompts/strategy/1. ken_tender_frappe_context_preserving_form_navigation_pattern.md`

When applicable:

1. Register the module consistently in `kentender_core/kentender_core/module_registry.py` and `kentender_core/public/js/kt_module_registry.js`.
2. Mount `kentender_core.kt_shell.mountHeader()` on builders and guided forms.
3. Use `kentender_core.kt_state` to save and restore workbench context.
4. Expose `data-testid="back-to-workbench"` through the shared shell.
5. Cover the return path with `tests/ui/helpers/moduleShell.ts` and `expectBackToWorkbench`.
6. Do not use `frappe.set_route("/desk")` or raw `location.assign` as the primary exit path.

Strategy-specific current rule: the primary UX is the Strategy Management workspace (`strategy_workspace.js`) with Plan Info, Structure, Review, and Audit tabs. The legacy `/app/strategy-builder/<plan>` route redirects to the workspace Structure tab and is not the primary editing surface.

For Workbench typography changes, follow:

`docs/prompts/architecture/KenTender Workbench Typography v1.0.md`

Use the established `--kt-wb-*` tokens rather than introducing ad hoc typography values.

## Procurement layout

Procurement subdomains live below `kentender_procurement/kentender_procurement/` (for example, `demand_intake/`). Follow `kentender_procurement/PROCUREMENT_INTERNAL_STRUCTURE.md`; do not flatten subdomains or place procurement-owned logic in another app.

## Testing and validation

Every substantive story or correction must consider:

- service/domain behaviour;
- validation and invariants;
- permissions and organizational scope;
- allowed and forbidden workflow transitions;
- failure and exception paths;
- audit effects;
- critical UI flow where UI behaviour changed;
- cross-app contract tests where a public interface changed.

Add or update focused tests with the implementation. High-risk funding, submission, evaluation, award, contract, permission, amendment, and audit flows require both positive and negative coverage.

Run `bench` from `/home/midasuser/frappe-bench`. Determine exact test commands from the repository's current scripts and documentation rather than inventing commands.

For asset builds, use the repository wrapper only:

```bash
./scripts/bench-with-node.sh build --app <app>
```

Do not run plain `bench build` or app-level Yarn builds; the wrapper supplies the required Node version. Run the wrapper from the repository root unless its own help/documentation states otherwise.

For Frappe core patches, source patches live under `patches/frappe/`. Apply them only when the task explicitly requires a tracked core patch:

```bash
./scripts/apply-frappe-patches.sh
./scripts/bench-with-node.sh build --app frappe
```

Do not edit the bench-local `apps/frappe` copy as an untracked shortcut.

## Current temporary and retired areas

- The IT Tender Configuration Wizard v1/v2 was retired in July 2026. Historical code is under `archive/it-std-wizard-retired-2026-07/`. Do not reactivate or extend it. The STD Engine remains active.
- The August 2026 MVP-1 Budget teardown removed legacy Budget DocTypes and `kentender_budget.seed.*` implementations. Budget seed entry points intentionally return a skipped result with reason `mvp1-budget-teardown` until the rebuild under `docs/mvp-1/02_budget/` is implemented.
- `kentender_budget.seeds.works_master_budget_seed.upsert_works_master_budget` remains only as a compatibility skip stub. Do not treat it as an active seeding implementation.

## Completion report

End implementation tasks with a concise, evidence-based report containing:

- files changed;
- behaviour implemented;
- tests/checks run and their results;
- tests not run and why;
- manual verification still required;
- intentional exclusions or future-phase work not implemented;
- assumptions, unresolved questions, or risks.

Do not describe a task as complete while required validation is failing or a material requirement remains unresolved.

## Code review rules

When reviewing changes, prioritize behavioural and governance defects over style. Flag:

- cross-app ownership or dependency violations;
- business logic in controllers or client-only code;
- missing server-side permission, scope, validation, or transition checks;
- silent mutation of approved baselines;
- hidden states or UI/server action mismatches;
- missing negative-path, permission, workflow, or audit tests;
- raw Desk navigation that breaks workspace context;
- edits to retired, archived, generated, framework, or unrelated files;
- claims of validation unsupported by executed checks.

Report findings by severity with file references and concrete consequences. If no material finding exists, say so and identify any residual testing risk.
