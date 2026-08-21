# Departmental Needs MVP 1 rev 1 implementation tracker

**Authority:** `NDS-CHG-001 v0.2`  
**Status:** Partial  
**Started:** 18 August 2026  
**Current focus:** NDS-G05 (legacy retirement), while earlier gates remain Partial pending their full matrices

## Tracker rules

1. Rows are permanent and use `Planned`, `In progress`, `Partial`, `Blocked`, `Done` or `Deferred`.
2. `Done` requires named executable evidence and a passing result for the row's entire scope.
3. A passing subset never closes a gate or acceptance criterion.
4. NDS-AC-003 remains Deferred until its intake-window contract is approved.
5. NDS-CHG-002 interaction screens are not implied by completing NDS-UI-01.

## Decisions and defaults

| Decision | Locked outcome |
|---|---|
| Baseline | NDS-CHG-001 v0.2 approved 18 August 2026 |
| Route | `/desk/departmental-needs`; no `/app/departmental-needs` or Demands alias |
| Build model | Fresh/reset environment; no migration, adapter, dual read/write or fallback |
| Future years | Fail closed with `NDS_INTAKE_WINDOW_NOT_CONFIGURED` pending AC-003 |
| Accepted withdrawal | Reasoned request; departmental approval only after all downstream references clear |
| Detailed screens | Deferred to NDS-CHG-002 |

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| NDS-G00 | Baseline, plan, tracker, ownership and clean-build boundary recorded | Done | Approved ledger plus `02_Departmental_Needs_Implementation_Plan.md` and this tracker |
| NDS-G01 | Four generated records and authorization foundations pass | Partial | Four service-only DocTypes generated and synced; NDS schema tests and Core authorization G01-G04 pass. Fresh-site and full NDS negative-scope matrix remain. |
| NDS-G02 | Lifecycle, withdrawal clarification, audit, idempotency and concurrency pass | Partial | Focused lifecycle/task/idempotency test passes. Full forbidden-transition, downstream-clearance, stale-token and concurrent-decision matrix remains. |
| NDS-G03 | Live NDS-UI-01 workspace passes route, scope, responsive and accessibility tests | Partial | Live page and static UI contract test pass. Browser responsive, keyboard, accessibility and direct-route denial evidence remains; CHG-002 screens are deferred. |
| NDS-G04 | Planning eligibility, allocation, effectiveness, reversal and usage pass | Partial | Allocation and Plan-approval contract tests pass. Legacy selector replacement, combine/split UI, amendment end-to-end and wider negative matrix remain. |
| NDS-G05 | Operational Demands artifacts and consumers are absent | In progress | Navigation/registry entry replaced. Legacy hooks, schemas, services, patches, tests and cross-app consumers are still present. |
| NDS-G06 | Exact seed and full acceptance evidence pass on a fresh environment | Partial | Exact MOH seed ran and focused fixture assertion passes on the development site. Fresh-environment and full acceptance matrix remain. |
| NDS-G07 | Future-year intake-window contract satisfies NDS-AC-003 | Deferred | Contract intentionally not defined in v0.2 |

## Work register

| ID | Work item | Status | Evidence / gap |
|---|---|---|---|
| NDS-SCH-001 | Departmental Need and Departmental Need Item | Done | Generated schema; `test_schema_is_greenfield_and_excludes_procurement_controls` passes after raw permissions were removed. |
| NDS-SCH-002 | Immutable Departmental Need Review | Partial | Immutable controller, unique idempotency evidence and lifecycle coverage exist; direct mutation negative test remains. |
| NDS-SCH-003 | Planning-owned Plan Need Allocation | Partial | Generated schema and draft/effective/reversed projection test pass; full approval/amendment matrix remains. |
| NDS-AUTH-001 | Capability profiles, PE/OU assignments and review routing | Partial | Exact seed plus Core authorization G01-G04 pass; NDS-specific expired/delegate/multi-assignment matrix remains. |
| NDS-AUTH-002 | Owner, department, oversight, Planner and audited support projections | Partial | Scoped workspace and Planner read-only tests pass; Budget/Accounting and support-specific projection tests remain. |
| NDS-SVC-001 | Context, create, update and workspace projections | Partial | Services and thin whitelisted API exist; create/idempotency/live projection tests pass. Update/attachment and wider query matrix remain. |
| NDS-SVC-002 | Submit/resubmit/return/accept/decline/withdraw transitions | Partial | All commands implemented; happy-path task gating passes. Complete transition matrix remains. |
| NDS-CLR-001 | Accepted-Need withdrawal request and clearance-gated approval | Partial | Clarified no-hidden-state flow implemented and happy path passes; draft/effective/downstream reference blockage matrix remains. |
| NDS-UI-001 | Literal live NDS-UI-01 workspace port | Partial | Live JS/CSS projection and exact fixture contract pass; Playwright responsive/a11y evidence remains. |
| NDS-UI-002 | Detailed create/edit/view/review interactions | Deferred | Await NDS-CHG-002 |
| NDS-PLN-001 | Accepted Need selector and line allocation | Partial | Server selector/allocation service preserves line lineage and rejects over-allocation; Planning UI still uses the legacy selector. |
| NDS-PLN-002 | Effective/reversed allocation projection and quantity reconciliation | Partial | Plan approval activation and approved-removal reversal are integrated; focused allocation and existing Plan approval tests pass. |
| NDS-RET-001 | Remove Demands schema, services, routes, roles, assets and patches | In progress | User-facing module registry/sidebar replaced; runtime legacy artifacts remain. |
| NDS-RET-002 | Remove obsolete Strategy/Budget/Planning Demand consumers | In progress | New planning contract is integrated alongside the old contract; obsolete consumers remain. |
| NDS-SEED-001 | Exact three MOH Needs, personas and approved allocation | Partial | Seed command returned all three exact Needs and the effective PPI allocation; fresh-site/repeatability evidence remains. |

## Acceptance evidence

| ID | Status | Evidence / gap |
|---|---|---|
| NDS-AC-001 | Partial | Canonical Departmental Needs page/registry exists; legacy Demands routes remain. |
| NDS-AC-002 | Partial | Positive assignment enforcement passes; full cross-scope matrix remains. |
| NDS-AC-003 | Deferred | Intake-window schema deliberately deferred |
| NDS-AC-004 | Done | `test_schema_is_greenfield_and_excludes_procurement_controls` passes. |
| NDS-AC-005 | Partial | Routed capability/task enforcement implemented; delegate-specific NDS evidence remains. |
| NDS-AC-006 | Done | `test_submit_review_and_accepted_withdrawal_are_task_gated` asserts `Accepted for planning`. |
| NDS-AC-007 | Partial | Commands create no funding/requisition effects; explicit side-effect absence test remains. |
| NDS-AC-008 | Partial | Oversight profile exposes no command; Budget Officer UI/negative command evidence remains. |
| NDS-AC-009 | Done | `test_planner_sees_only_accepted_sources_and_cannot_edit` passes. |
| NDS-AC-010 | Partial | Shared audited support contract passes Core G04; NDS-specific audit assertion remains. |
| NDS-AC-011 | Done | `test_exact_workspace_fixture_and_separate_usage` and allocation projection test pass. |
| NDS-AC-012 | Partial | Accepted-only query and server validation implemented; explicit non-accepted allocation test remains. |
| NDS-AC-013 | Done | Allocation projection test proves Draft remains `Not included`. |
| NDS-AC-014 | Done | Allocation test asserts both Need and Need Item lineage. |
| NDS-AC-015 | Partial | No direct endpoint or schema link exists; explicit absence contract remains. |
| NDS-AC-016 | In progress | Departmental Needs implementation is greenfield, but legacy operational Demands artifacts remain in the repository. |
| NDS-AC-017 | Partial | No new migration, adapter, redirect or fallback was added; legacy teardown registrations still exist. |
| NDS-AC-018 | Partial | Generator and exact seed pass on the existing development site; fresh-environment proof remains. |
| NDS-AC-019 | Partial | Shared resource-scope tests pass; explicit Departmental Needs cross-PE/cross-department tests remain. |

## Validation evidence

| Evidence | Result |
|---|---|
| Frappe migrate after generated schema/page and controlled-permission updates | Pass on `kentender.midas.com`, 18 August 2026 |
| Departmental Needs schema/lifecycle/authorization module | 5/5 pass |
| Departmental Needs UI contract module | 1/1 pass |
| Plan Need Allocation module | 1/1 pass, including lineage and over-allocation rejection |
| Shared Core authorization gates G01-G04 | 27/27 pass |
| Existing Planning Plan-approval gate G05 | 5/5 pass |
| Procurement asset compilation | JavaScript/CSS bundle pass; overall wrapper exits 1 during Frappe translation multiprocessing with `OSError: [Errno 95] Operation not supported` |

## Blockers and deferred work

- NDS-AC-003 cannot close until a PE/FY intake-window owner and schema are approved.
- Detailed action screens cannot close until NDS-CHG-002 is supplied.
- Existing databases containing Demand records must be reset; this workstream will not create a destructive migration.
- The operational Demands implementation and obsolete Planning/Strategy/Budget consumers are still present, so NDS-G05 blocks clean-build acceptance.
- The required asset wrapper compiles the procurement bundle but cannot complete translation compilation in this environment because Python multiprocessing cannot create its socket.

## Change log

| Date | Change |
|---|---|
| 2026-08-18 | Tracker created; v0.2 approved; clean-build boundary, canonical Desk route, deferred intake window and accepted-withdrawal clarification recorded. |
| 2026-08-18 | Four controlled DocTypes, capability/task services, live workspace, Plan Need Allocation foundation and exact MOH seed added; focused and affected contract evidence recorded. Legacy retirement remains in progress. |
