# AUTH-ADR-001 — Complete Capability/Call-Site Mapping (pre-cutover inventory)

**Status:** All 9 blockers resolved 2026-08-27 (see §9). Guiding rule for every resolution: create a Frappe Role only for a real human responsibility — never for internal services, dead literals, or vague technical capabilities. Implementation in progress against these resolutions.
**Scope:** Every capability string and call site into `kentender_core.services.authorization_policy`'s five functions (`evaluate_capability`, `require_capability`, `resolve_effective_access`, `get_authorized_record_projection`, `get_available_actions`) across all 11 `kentender_*` apps, plus every `required_capability`/`task_type` value on `Workflow Routing Rule`/`Workflow Queue`/`Workflow Task`, plus administration/diagnostics capabilities. Built from three parallel research passes (2026-08-27) reading every service file, doctype JSON, seed, and test that touches this surface.

**Rule enforced while building this table (per user instruction):** no capability is auto-mapped without a real, defensible Role/scope answer. Where no defensible replacement exists, the row is marked **BLOCKED** and left for a human decision — never filled in with a guess.

## 0. Structural findings that shape every row below

1. **Two capability namespaces are not wired to the engine at all** and must NOT be folded into this migration by force:
   - `planning_permissions.py` (`plan.*` capabilities) — a **local, independent, already-Role-based** `require_capability()`/`get_available_actions()` that never touches `Operational Scope Assignment`/`Capability Profile`. It already has the richest Role-mapping artifact in the repo (`CAPABILITY_ROLES` dict).
   - `std_authorization.py` (`std_configuration.*`) — deliberately rejected wiring into the engine (PE-less global config; already Role-based). Out of scope, already ADR-compliant.
2. **Dual-path conflict — a real defect, not just documentation noise:** `plan.finance.confirm`, `plan.finance.task`, `plan.finance.return`, `plan.view`, `plan.approve`, `plan.submit`, `plan.review`, `plan.recommend`, `plan.return` are each enforced by **two independent, disconnected mechanisms** depending on code path:
   - `planning_permissions.py`'s local Role-based check (business-command layer), **and**
   - the real `authorization_policy` engine via `planning_tasks.py`'s task-scoped `evaluate_capability`/`idempotent_decision` calls, and directly in `test_authorization_gate01.py`'s fixtures.
   The same action can be authorized differently depending on which code path evaluates it. This must be resolved (pick one mechanism) before these capabilities can be given a single Role mapping — **BLOCKED**, see §3.
3. **Background jobs bypass the engine entirely already** — `reference_data_transitions.run_scheduled_context_transitions` (the only live `scheduler_events` job anywhere in the 11 apps) runs as `_SYSTEM_ACTOR = "Administrator"`, writes only audit-action strings, never calls the engine. No migration work needed here.
4. **File access and the other 7 apps are clean** — no `has_permission` hook keys "File" anywhere; the one File `doc_events` hook (CAS delete-guard) doesn't touch the engine; `kentender_governance/compliance/stores/assets/integrations/suppliers/transparency` have zero references to any of this system.
5. **`authorization_api.py` lives at `kentender_core/kentender_core/authorization_api.py`** (module root), not `services/` — a naming correction from the original plan.
6. Several capability constants found in seed/test files are **not authorization capabilities at all** — test-scenario IDs (`budget.canonical.no_rsv_0001`, `budget.cgk_*`, etc.) and workflow-state/module-path fragments (`strategy.plan_active`, `procurement_planning.api.`, etc.). Excluded from the table below; listed for the record in the research transcripts, not repeated here.

## 1. Reference Data domain (12 capabilities) — READY, no blockers

All resolve via `require_capability`/`_has_any_active_capability`, real PE (and, for Context, PE/FY) scope, already has a full mapping table from Phase 4 planning.

| Capability | Call sites | Current source | Replacement Role | Scope | State/task | Delegation | Segregation | Replacement service | Tests | Disposition |
|---|---|---|---|---|---|---|---|---|---|---|
| `reference_data.pe.create_draft` | `reference_data_permissions.py:78` (`require_pe_create_capability`, no-resource bypass) | OSA `REFDATA-STEWARD` (any-active-grant check) | Central Reference Data Steward | Global central — no scope check | PE must not yet exist | N/A | vs. `pe.approve_activate` (SoD rule) | `reference_data_permissions.py` (collapses to plain Role-membership check, see Phase 4 plan) | `test_reference_data_pe_lifecycle.py` | READY |
| `reference_data.pe.propose_amendment` | `reference_data_permissions.py:52` via `require_pe_capability` | OSA `REFDATA-STEWARD` | Central Reference Data Steward | Global central | PE state = Active | N/A | none | same | same | READY |
| `reference_data.pe.approve_activate` | `reference_data_permissions.py:52` | OSA `REFDATA-APPROVER` | Central Configuration Approver | Global central | PE state = Draft/Under Review | N/A | vs. `pe.create_draft` | same | same | READY |
| `reference_data.pe.suspend` | `reference_data_permissions.py:52` | OSA `REFDATA-APPROVER` | Central Configuration Approver | Global central | PE state = Active | N/A | none | same | same | READY |
| `reference_data.pe.reinstate` | `reference_data_permissions.py:52` | OSA `REFDATA-APPROVER` | Central Configuration Approver | Global central | PE state = Suspended | N/A | none | same | same | READY |
| `reference_data.pe.retire` | `reference_data_permissions.py:52` | OSA `REFDATA-APPROVER` | Central Configuration Approver | Global central | PE state = Active, no blocking Context | N/A | none | same | same | READY |
| `reference_data.fy.create_draft` | `reference_data_permissions.py:123` (`require_fy_capability`, no-PE bypass) | OSA `REFDATA-STEWARD` | Central Reference Data Steward | Global central | FY must not yet exist | N/A | vs. `fy.approve_available` | same | `test_reference_data_fy_lifecycle.py` | READY |
| `reference_data.fy.approve_available` | `reference_data_permissions.py:123` | OSA `REFDATA-APPROVER` | Central Configuration Approver | Global central | FY state = Draft | N/A | vs. `fy.create_draft` | same | same | READY |
| `reference_data.fy.retire` | `reference_data_permissions.py:123` | OSA `REFDATA-APPROVER` | Central Configuration Approver | Global central | FY state = Available | N/A | none | same | same | READY |
| `reference_data.context.create_draft` | `reference_data_permissions.py:184` via `require_context_capability` | OSA `REFDATA-CTX-STEWARD` | **PE Configuration Steward** (new Role — confirmed not registered anywhere; live inventory found it only as a Capability Profile display name) | PE/FY-scoped — User Permission on `PE Fiscal Year Context` (Phase 2 retrofit) | Context state = Draft/Returned | N/A | vs. `context.recommend`/`context.approve` | same | `test_reference_data_context_lifecycle.py` | READY |
| `reference_data.context.recommend` | `reference_data_permissions.py:184` | OSA `REFDATA-CTX-REVIEWER` | **Professional Configuration Reviewer / HoPF** (new Role) | PE/FY-scoped | Context state = Submitted | N/A | vs. `context.create_draft` | same | same | READY |
| `reference_data.context.approve` | `reference_data_permissions.py:184` | OSA `REFDATA-CTX-APPROVER` | **Accounting Officer** — ⚠ this Role name **already exists live** in the DB (confirmed via Phase 1's inventory run: `moh.accounting.officer@example.test` holds it), but was created by `procurement_planning`, not by this domain. Must confirm it's safe to reuse for reference_data's Accounting Officer meaning before wiring, or it silently grants reference_data authority to whoever holds planning's Accounting Officer Role. | PE/FY-scoped | Context state = Recommended | N/A | vs. `context.create_draft`/`context.recommend` | same | same | **NEEDS CONFIRMATION** (not a hard block, but do not silently reuse) |

## 2. Budget domain (11 capabilities) — READY, one gap

`budget_permissions.py` already has the cleanest native-Role precedent in the repo (`Budget Viewer/Officer/Reviewer/Authority`, `Auditor`), seeded 1:1 against these capability strings via `budget_authorization_seed.py`'s `PROFILE_CAPABILITIES`.

| Capability | Replacement Role | Scope | Disposition |
|---|---|---|---|
| `budget.list`, `.view` | Budget Viewer (+ all higher roles implicitly) | PE-scoped (`Budget.procuring_entity`, or `pe_fy_context` post-Phase-2) | READY |
| `.create`, `.edit`, `.submit` | Budget Officer | PE-scoped | READY |
| `.review`, `.return` | Budget Reviewer | PE-scoped | READY |
| `.approve` | Budget Authority | PE-scoped | READY |
| `.export` | Budget Authority (or Auditor, per `can_export_funding_performance`) | PE-scoped | READY |
| `.reserve` | **BLOCKED** — no dedicated Role. Seed's `"finance_confirmation"` Capability Profile grants this alongside `budget.list`/`.view` but is distinct from Budget Officer's profile; no `ROLE_FINANCE_CONFIRMATION`-equivalent exists. | — | **BLOCKED — needs a new Role decision** (e.g. "Budget Finance Confirmation" or fold into an existing Role — a business decision, not mine to invent) |
| `.revision.apply` | **BLOCKED** — no dedicated Role. Seed's `"revision_authority"` Capability Profile is distinct from Budget Authority's general profile. | — | **BLOCKED — same as above** |

## 3. Procurement Planning domain (`plan.*`, 12 capabilities) — BLOCKED on dual-path conflict

Per §0.2: these capabilities are enforced by two independent mechanisms today. **I have not picked a winner — that's the actual decision blocking this whole domain**, not a mapping gap.

| Capability | Mechanism A (local, Role-based) | Mechanism B (real engine, task-scoped) | Disposition |
|---|---|---|---|
| `plan.view`, `.create`, `plan_item.edit`, `.submit`, `.review`, `.approve`, `.recommend`, `.return`, `.handoff` | `planning_permissions.py` `CAPABILITY_ROLES` — already Role-based, no OSA dependency | not observed on this subset | Mechanism A is already ADR-compliant; if B never checks these, no conflict — **CONFIRM**, don't assume |
| `plan.finance.confirm`, `.finance.task`, `.finance.return` | `planning_permissions.py` `CAPABILITY_ROLES` (`ROLE_BUDGET_OFFICER` et al.) | `planning_tasks.py:89,228` real `evaluate_capability` call, task-scoped, against OSA/Capability Profile | **BLOCKED — dual enforcement is live today.** A task-level finance-confirm action could be allowed by Mechanism B (an OSA grant) while Mechanism A's Role check would deny it, or vice versa. Must decide: retire Mechanism B in favor of A's Role model (my recommendation, since A is already ADR-target-shaped and has zero OSA dependency), or the reverse. **This is a real pre-existing authorization inconsistency the ADR migration surfaced — not something to route around.** |

**Recommendation (not yet actioned, needs your confirmation):** retire the `planning_tasks.py` engine calls in favor of `planning_permissions.py`'s existing Role-based model, since (a) it's already fully native-Role-shaped, (b) it has zero `Operational Scope Assignment`/`Capability Profile` dependency to migrate, and (c) the ADR's own target state is exactly what this file already does. This would make Procurement Planning **the one domain requiring no new Role work at all** — just removing the redundant, conflicting call sites in `planning_tasks.py`, `plan_item_finance.py`, `get_plan_review.py`.

## 4. Departmental Needs domain (8 capabilities + 1 cross-domain) — READY

| Capability | Replacement Role | Scope | Disposition |
|---|---|---|---|
| `.create`, `.edit_own`, `.submit`, `.view_own` | Departmental Need Requester | PE+OU-scoped (`Departmental Need.procuring_entity`+`.organisation_unit`) | READY |
| `.view_department`, `.review` | Head of User Department (+ Departmental Review Delegate for the delegated path) | PE+OU-scoped | READY |
| `.read_accepted_for_planning` | Procurement Planner | PE-scoped | READY |
| `.oversight_read` | Budget Officer (reused; semantically loose per the research — confirm this is intentional, not accidental role reuse) | PE-scoped | **NEEDS CONFIRMATION** (working, not blocked) |
| `procurement_planning.need_allocate` (cross-domain, in `need_allocations.py`) | Procurement Planner | PE+OU-scoped | READY |

## 5. Strategy domain (3 capabilities) — READY, one legacy overlap to watch

| Capability | Replacement Role | Scope | Disposition |
|---|---|---|---|
| `strategy.plan_version.author` | Strategy Author | PE-scoped | READY |
| `strategy.plan_version.review` | Strategy Reviewer | PE-scoped | READY |
| `strategy.plan_version.approve` | Strategy Approval Authority | PE-scoped | READY |

**Watch item, not blocking:** `strategy_authorization.py`'s own docstring says legacy `Strategy Officer`/`Strategy Manager`/legacy `Planning Authority` roles (from the older `strategy_permissions.py`/`org_scope_access.py` system) are still referenced by not-yet-rebuilt `strategy_writes.py`/`strategy_contracts.py` call sites. Strategy is already mid-migration on its own; this AUTH-ADR-001 work should land on top of the *new* `strategy_authorization.py` roles, not the legacy ones — confirmed already correct, just flagging the coexistence so it isn't mistaken for a new problem.

## 6. Cross-cutting / workflow-routing capabilities — 2 of 3 BLOCKED

| Capability | Purpose | Replacement Role | Disposition |
|---|---|---|---|
| `authorization.task.reassign` (`workflow_tasks.py:177`) | Gates who may reassign ANY task, across ALL modules — a single global capability, not derived from the task's own routing rule | **BLOCKED — no Role exists anywhere in the codebase for this.** No `ROLE_*` constant, no `add_roles` call, no `CAPABILITY_ROLES`-style entry references it in any module. This is a bare, cross-cutting gate with no natural per-domain owner. | **BLOCKED — needs an explicit product/architecture decision**: a single cross-cutting "Task Reassigner"/admin-style Role, or a per-module reassignment permission derived from each task's own required capability's Role (e.g. reassigning a Budget task requires Budget Authority). I have not picked one — this changes the security model, not just naming. |
| `authorization.diagnostic.view` (`authorization_diagnostics.py:13`, only ever asserted in `test_authorization_gate04.py`) | Gates who may run the access-diagnostic tool | No Role found; also no confirmed production caller (System Manager/`ADMIN_ROLES` already bypasses this check via `_can_diagnose`'s first branch) | **BLOCKED — needs confirmation this is even a live production capability** vs. a test-only fixture that can simply be removed once cutover happens (since `ADMIN_ROLES` already gates the real diagnostic page) |
| `support.record.view` | Gates the read-only "support view" of a record, used by Departmental Needs and Procurement Planning support screens | No dedicated Frappe Role — only a Capability Profile (`CAP-NDS-SUPPORT`) assigned to `Administrator` in the seed, which itself violates AUTH-AC-012 ("Administrator cannot perform a business decision without the named Role") if support-viewing counts as a business decision | **BLOCKED — needs a new Role** (e.g. "Support Agent"/"Support Reader") rather than continuing to grant this via Administrator |

## 7. Dead/unused capability literals — no mapping needed, confirm before deleting

`plan.item.complete`, `demand.business.review`, `demand.enrich`, `demand.funding.confirm`, `demand.approve` — found only in `my_work.py`'s `_PRESENTATION` UI-label dict (workflow_tasks/my_work research pass), **zero production task ever carries these `task_type` values**. Departmental Needs' real task types are `departmental_needs.department_review`/`.withdrawal_review`, not `demand.*`. These look like either dead code from an earlier naming scheme or placeholders for unbuilt features.

**Disposition:** no Role mapping needed (nothing to migrate) — but flagging for product confirmation rather than silently deleting, since removing them could be masking an intended-but-unbuilt feature rather than genuine dead code.

## 8. `std_configuration.*` and `plan.*` (Mechanism A) — confirmed already ADR-compliant, out of scope

No further work needed on these; they don't read `Operational Scope Assignment`/`Capability Profile` at all today.

## Summary — what's actually blocking Phase 3

| # | Blocking item | Decision needed |
|---|---|---|
| 1 | `plan.*` dual-path conflict (§3) | Confirm: retire `planning_tasks.py`'s engine calls in favor of `planning_permissions.py`'s existing Role model? |
| 2 | `budget.reserve` — no Role | Name/create a Role, or fold into an existing one |
| 3 | `budget.revision.apply` — no Role | Name/create a Role, or fold into an existing one |
| 4 | `authorization.task.reassign` — no Role, cross-cutting | Single global Role, or derive from each task's own required-capability Role? |
| 5 | `authorization.diagnostic.view` — unclear if live | Confirm test-only vs. production; if test-only, drop it at cutover |
| 6 | `support.record.view` — currently granted via Administrator | Create a dedicated Role instead of using Administrator |
| 7 | `reference_data.context.approve` → reusing planning's live "Accounting Officer" Role | Confirm intentional reuse vs. needs a distinct Role name |
| 8 | `departmental_needs.oversight_read` → reusing Budget Officer Role | Confirm intentional reuse |
| 9 | Dead literals (`plan.item.complete`, `demand.*`) | Confirm genuinely dead before dropping |

Everything else (Reference Data's other 11 capabilities, Budget's other 9, Departmental Needs' other 5, Strategy's 3) is READY with a concrete Role/scope answer and no fabricated mapping.

## 9. Blocker resolutions (2026-08-27)

**1. `plan.*` dual path — RESOLVED.** `planning_permissions.py`'s native Role/User Permission model is authoritative. `planning_tasks.py`'s `evaluate_capability`/`idempotent_decision` calls into the OSA-based engine are replaced with the same canonical helper `planning_permissions.py` already uses — task functionality itself (claim/transition state machine) is unchanged, only the authorization check inside it changes source. Finance-confirm/finance-task/finance-return move off `ROLE_BUDGET_OFFICER` onto the distinct **Finance Confirmation Officer** Role, per `BUD-CHG-001 §7`/`§8.1` (confirmed real, documented spec content — not invented): "Open a specifically assigned Procurement Planning Finance task and confirm or return it. The capability grants no Budget authoring or activation authority." OSA/Capability Profile path retired for this domain once equivalence tests pass — no dual-mode period in production; the cutover is one release, not a gradual deprecation.

**2. `authorization.task.reassign` — RESOLVED.** New Role **`KenTender Task Administrator`**. `reassign_task()` in `workflow_tasks.py` requires: holder has `KenTender Task Administrator` + User Permission scoping the task's PE/FY; the target user independently holds the task's own required business Role and matching scope (re-checked via `evaluate_capability`-successor, not assumed); task state is reassignable (`Open`, unclaimed or claimed-by-someone-else per existing rules); a reason is recorded; the operation is audited. This Role carries zero business-decision authority — it cannot itself claim, transition, or decide a task, only move its assignment.

**3. Budget capabilities — RESOLVED.**
- `budget.reserve`: **retired as a user capability.** `require_budget_capability(CAP_BUDGET_RESERVE, bud)` is removed from `budget_check_reserve_contracts.py` — the reservation service is an internal call invoked only by an already-authorized Planning Finance Confirmation action (per `BUD-CHG-001 §8.1`: Procurement Planning owns "the immutable Finance decision"; Budget owns "creation of all reservations as one atomic operation" as a downstream technical effect, not a separate user-facing grant).
- `budget.revision.apply`: **retired entirely**, replaced by the existing successor-version commands already defined in `BUD-CHG-001 §6.1`: **Budget Officer** creates/edits/submits a successor version; **Budget Reviewer** returns or recommends it; **Budget Activation Authority** (new Role, real spec-documented name — confirmed via `BUD-CHG-001 §7`, not registered as a Frappe Role yet, only as a seed-fixture display name/Capability Profile key) activates or returns it at activation. `CAP_BUDGET_APPROVE`/`budget.approve` is remapped from the generic `Budget Authority` Role onto this Role, matching the spec's own table exactly.

**4. `support.record.view` — RESOLVED.** New read-only Role **`KenTender Support Analyst`**, scoped via native User Permission. May inspect records and technical metadata; cannot perform business decisions, edit governed data, or bypass workflow. Replaces the seed's current grant of this capability to `Administrator` (itself a real AUTH-AC-012 violation independently worth fixing).

**5. `authorization.diagnostic.view` — RESOLVED.** Confirmed test-only (`test_authorization_gate04.py` only; the real diagnostic page is already gated by `ADMIN_ROLES` in `_can_diagnose`'s first branch, so this literal never gates anything live). Removed rather than given a speculative Role. If a real production diagnostic surface is authorized later, it gets its own dedicated **`KenTender Access Administrator`** Role at that time — not created now.

**6. Role reuse — RESOLVED.**
- `reference_data.context.approve` → **reuse `Accounting Officer`** (intentional, confirmed already the live Role for Planning's own approval flow — `planning_permissions.py`'s `ROLE_ACCOUNTING_OFFICER`). Enforced with exact PE/FY scope (User Permission on `PE Fiscal Year Context`), eligible task, and lifecycle state — reuse of the Role name does not imply reuse of the authorization decision; each domain's own state/scope/task gate still applies independently.
- `departmental_needs.oversight_read` → **does NOT reuse `Budget Officer`** (budget responsibility does not imply Needs oversight authority). Maps instead to the existing, already-widely-used **`Auditor`** Role (confirmed live across `kentender_procurement` — tender publication, bid submissions, procurement lifecycle, STD engine read paths — the established convention in this codebase; **`Internal Auditor`** does not exist anywhere and there is no active role-normalization initiative, so `Auditor` is used rather than inventing a new name), read-only, PE-scoped.

**7. Dead capability literals — RESOLVED.** `plan.item.complete`, `demand.business.review`, `demand.enrich`, `demand.funding.confirm`, `demand.approve` confirmed via the inventory to have zero production call sites, zero persisted routing rules, zero migration dependents (Departmental Needs' real task types are `departmental_needs.department_review`/`.withdrawal_review`, never `demand.*`). Recorded here as **Retired — no production consumer**. Removed from `my_work.py`'s `_PRESENTATION` dict; any seed/test referencing only these literals removed outright — no alias, no compatibility branch.

Net effect: one authorization path (native Frappe Role + User Permission + record/task state, everywhere), 3 new Roles (`KenTender Task Administrator`, `KenTender Support Analyst`, `Budget Activation Authority`) plus 1 spec-documented Role formalized (`Finance Confirmation Officer`), 1 capability retired outright (`budget.revision.apply`), 1 capability moved from a user grant to an internal service call (`budget.reserve`), 1 speculative capability removed (`authorization.diagnostic.view`), and 5 dead literals removed — fewer concepts than the current implementation, not a renamed capability framework.
