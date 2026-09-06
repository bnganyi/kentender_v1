# Departmental Needs — gap analysis against NDS-CHG-001 v1.6

**Authority:** `KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_6.md` (approved 3 September 2026; supersedes v1.4 and all earlier versions, in full).
**Governed by:** `KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_1.md` for design-input mechanics, page behaviour, shared fixtures, universal prohibitions and error-contract conventions; `KenTender_AUTH-ADR-001_Role-Bound_Business_Responsibility_and_Organisational_Scope_v1_6.md` for authorization.
**Statutory cross-check:** `KenTender_LAW-REG-001_Statutory_Correction_Register_v1_0.md` §7/§8 confirms **no change** to Departmental Needs — it has no statutory standing and remains internal consultation. This rebuild is an AUTH-ADR-001/CFG-CHG-002 alignment pass only, not a domain-rule change.
**Companions:** `03_NDS_Rebuild_Implementation_Plan.md`, `IMPLEMENTATION_TRACKER.md`.
**Analysis date:** 2026-09-04
**Implementation under review:** `kentender_procurement/kentender_procurement/departmental_needs/` (+ `setup/`, `public/js/departmental_needs/`, `public/css/departmental_needs_industry.css`, `tests/ui/smoke/departmental_needs/`) — the code built and closed against **NDS-CHG-001 v1.1** (28 Aug 2026, tracker closed 29 Aug 2026: 246 Python tests, 23 Playwright specs, 16 vitest tests green).

## 1. Executive summary

The **module's own** business rules are essentially settled. NDS-CHG-001 v1.6's foundational §1.1 disposition register — one Need per requirement, no item table, no attachments, no cost/currency/location, `Not included`/`Fully included` only, native permissions instead of a capability store, the six-field version model, the full successor and withdrawal lifecycles — is the **same register the v1.1 code was already built and verified against**. That work does not need repeating: it is confirmed present by the closed v1.1 tracker and this analysis's own re-check in §3.

What actually moved between v1.1 and v1.6 is the **authorization and configuration substrate underneath every module in the system**, and Departmental Needs has not followed it:

1. **AUTH-ADR-001 advanced from a per-module "native Frappe permissions" choice to a single mandatory cross-app model** (v1.6): one site = one Procuring Entity; a role-bound `User Responsibility Assignment`, resolved through `kentender_core.services.authorization`, is the *sole* source of business authority; Frappe User Permission grants none. NDS-CHG-001 v1.6 §6 states this in the module's own voice, and adds an entirely new **§16.4 "Required AUTH-ADR-001 v1.6 correction slice"** — a 13-step migration checklist that did not exist in v1.1. The v1.1-era decision to use native Role + User Permission (recorded in this module's own tracker as diverging "from CFG-CHG-002 and STR-CHG-001, which both adopted `kentender_core.services.authorization_policy`") compared against a now-*also*-retired capability-profile engine, not against today's resolver. That decision is superseded by the approved v1.6 text and is not being carried forward — see Gap Analysis §5 and the Implementation Plan's decision D2.
2. **The site moved to one-PE-implicit.** `procuring_entity` is removed from every NDS doctype; the multi-PE User-Permission scoping the v1.1 code relies on throughout is retired along with it.
3. **Fiscal Year and Unit move onto ERPNext's native doctypes.** NDS's own bespoke `Financial Year` and `Unit Of Measure` doctypes — both built during the v1.1 pass — are replaced by ERPNext's `Fiscal Year` (with two `kentender_*` flag fields CFG-CHG-002 already ships) and `UOM`.
4. **The `Needs Intake Window` doctype is deleted outright**, replaced by the two Fiscal Year flag fields above, owned and maintained exclusively through `/app/system-setup`. Departmental Needs becomes a read-only consumer with no configuration screen of its own (§11.11 explicitly reserves this).
5. A handful of read-contract renames and additions on the API surface (§8.1), and small fixture/actor alignment to the KT-STD-001 §8.3 shared register.

Verdict: this is a **correction-in-place**, on the same pattern already used for Budget's BUD-CHG-001 v1.3 and Strategy's own AUTH-ADR-001 v1.6 cutover — not a rebuild from scratch. The command surface (§8.2), the transactional pattern in `services/lifecycle.py`, and the Vue-in-Desk/Industry frontend are all sound assets to keep. The work is concentrated in the authorization layer and the three doctype/field substitutions above.

## 2. What changed, document-level (v1.1 → v1.6)

NDS-CHG-001 v1.6 is a full-replacement document ("supersedes v1.4 and all earlier versions, in full") — it is not read as a delta against v1.1. Its own §1.1 "New in v1.6" table is the authoritative statement of what is new since the version immediately preceding it, and is reproduced here against the live code:

| # | Change | Spec anchor | Code impact |
|---|---|---|---|
| 1 | Needs-submission flag gains an optional close instant (`kentender_needs_submission_closes_at`) alongside the existing open Boolean, both now living on ERPNext's `Fiscal Year`, not a module-owned window record | §1.1, §4.1 | The **whole `Needs Intake Window` doctype is retired**, not just extended — see §5 below |
| 2 | Closing intake blocks creation/initial submission only; existing Draft/Returned versions stay editable and saveable (NDS-BR-003) | §1.1, §16.4.12 | Behavioural — verify `_validate_submission`/`save_need_draft` still allow saves on a closed flag |
| 3 | Unit catalogue moves to ERPNext `UOM` (`enabled=1`), replacing the KenTender-governed `Unit Of Measure` doctype | §1.1, §4.3, §7.1 | Retarget `Departmental Need Version.unit` Link; drop the custom doctype |
| 4 | `Procurement Budget Line` naming per BUD-CHG-001 v1.3 §1.1 | §1.1 | Citation only — Departmental Needs never stores a Budget Line; no NDS code change |
| 5 | No Procuring Entity row anywhere on any artboard (KT-STD-001 §2.3) | §1.1 | Every NDS-DES artboard and its Vue port must drop the PE context line/selector |
| 6 | Closed-input rules, verification protocol, release evidence and universal prohibitions now cited from KT-STD-001 v1.1 rather than restated | §1.1 | Documentation only |
| 7 | Bespoke fixture actors `amina.hassan@moh.example.test` and `auditor.moh@example.test` replaced by the KT-STD-001 §8.3 shared register — Amina Hassan is dropped (duplicated Mercy Kilonzo's assignment), Auditor becomes Naomi Chebet | §1.1, §14.2 | Seed/actor rewrite — see §8 below |
| 8 | Citations bumped to AUTH-ADR-001 v1.6, CFG-CHG-002 v0.6, BUD-CHG-001 v1.3, STR-CHG-001 v1.6 | §1.1 | Documentation, but AUTH-ADR-001 v1.6 specifically is **not** a citation-only change — see §5 |

The original foundational disposition register (§1.1's first table — one Need per requirement, no items, no attachments, no cost/currency/location, native permissions, etc.) is unchanged text carried through every version since v1.0. It is re-verified against the current code in §3, not re-derived here.

**Not captured by the "New in v1.6" table, but the largest gap in this analysis:** the module's own §16.4 "Required AUTH-ADR-001 v1.6 correction slice" is new content in this version — a 13-step numbered checklist that did not exist as a named section in the code's governing v1.1 document. It is the closest thing the spec provides to a ready-made phase plan for the authorization half of this rebuild, and Gap Analysis §5 and the Implementation Plan follow its numbering directly.

## 3. §1.1 foundational disposition register — re-verified against current code

Every row already closed by the v1.1 rebuild and not reopened by v1.6:

| Spec disposition | Status |
|---|---|
| One Need = one requirement; quantity/unit on the Need, no item child table | **Compliant.** `Departmental Need Item` was dropped in the v1.1 cutover (`patches/nds_chg_001_v11_drop_retired_need_doctypes.py`); the two directories left on disk are empty. |
| No attachments | **Compliant.** `Departmental Need Attachment` and `services/attachments.py` were deleted in v1.1. |
| `Not included` / `Fully included` only, no `Partially included` | **Compliant.** `Need Planning Usage Projection.usage` is a two-value Select. |
| No delivery/use location, no cost/currency, no free-text `Other` unit | **Compliant** on the first two; the free-text unit was replaced with a governed Link — **but to the wrong catalogue** (KenTender's own `Unit Of Measure` instead of ERPNext `UOM` — this is a v1.6-introduced correction, tracked in §5/§7 below, not a regression). |
| No requirement type, procurement category, Strategy reference, generic source/authority/evidence/notes/contact | **Compliant.** None present. |
| No Budget Officer / Accounting Officer / duplicate Planner workspace | **Compliant.** `setup/departmental_needs_page.py`'s `LANDING_ROLES` holds only the six approved roles. |
| One role-appropriate table, minimal filters, no summary cards | **Compliant.** `WorkspaceScreen.vue` / `ReviewScreen.vue` match §11.2/§11.3. |
| No separate "Review tasks" work-queue menu | **Compliant**, and ahead of the letter of even v1.1: reviewer work already surfaces through `kentender_core`'s `kt_my_work_providers` hook (`departmental_needs/services/my_work_provider.py`) rather than a menu entry — this is exactly what v1.6 §10 now also states explicitly. |
| Canonical §10 routes, no `/demands`/legacy alias | **Compliant.** All eight routes exist under `/app/departmental-needs/*` (Frappe's own `/app`→`/desk` platform redirect is not a compatibility alias). |
| Accepted Need immutable, correctable only through a reviewed successor | **Compliant.** The full §5.2 successor lifecycle exists (`create_accepted_need_successor`, `cancel_accepted_need_successor`, successor return/accept/decline). |
| Accepted withdrawal only via reviewed request, Active Plan dependency cleared first | **Compliant.** `Need Withdrawal Request` implements all four statuses including `Awaiting planning clearance`; `decide_accepted_need_withdrawal` implements approve/evaluate/decline. |
| Acting HoD via one dated Acting assignment, no delegate role | **Compliant in spirit, wrong mechanism.** `Departmental Review Delegate` is gone and there is no separate approval level — but "one dated Acting assignment" today means a **time-bound native User Permission row**, not a `User Responsibility Assignment` with `appointment_type = Acting`. This is the D2 gap (§5). |
| Native permissions only, no capability/scope-assignment store | **Half true, half now-obsolete.** The v1.1 rebuild correctly removed the *pre-v1.1* `Capability Profile` / `Operational Scope Assignment` engine. But "native permissions" in v1.1 was implemented as **Frappe User Permission across PE/OU/FY dimensions**, which AUTH-ADR-001 v1.6 §1.1 now also retires as a business-authority source ("None of the following is an authority source... a Frappe User Permission"). See §5. |
| No legacy Demand migration/compatibility | **Compliant.** No Requisition/Tender reference; architecture guard (`test_departmental_needs_architecture.py`) still passes. |

Net: the v1.1 rebuild's domain-model and lifecycle work holds. The gap is authorization plus the three doctype substitutions below.

## 4. Domain model diff (§4)

| Spec entity / field (§4) | Today | Gap |
|---|---|---|
| `DepartmentalNeed` — no `procuring_entity` field (§1.1 v1.5-derived rule, restated) | `departmental_need.json` carries `procuring_entity` (Link, immutable) and every command validates OU-within-PE | **Delete the field.** The site has one PE, resolved implicitly; scoping becomes OU-only through the resolver. |
| `DepartmentalNeed.financial_year_id` — "the canonical ERPNext `Fiscal Year`" (§3, §4.2) | `financial_year` Links to KenTender's own `Financial Year` doctype (`kentender_core/.../doctype/financial_year/`), deliberately *not* ERPNext's, per `services/context.py`'s own docstring | **Retarget the Link to ERPNext `Fiscal Year`.** This is the same doctype AUTH-ADR-001 v1.6 §6 mandates site-wide; `kentender_core` already carries the two flag fields on it (see §5.3 below) — no new core schema needed, only NDS's own field retarget and every query that currently joins on the bespoke doctype. |
| `DepartmentalNeedVersion.unit_id` — "governed unit... ERPNext `UOM`... `enabled = 1`" (§4.3, §1.1) | `unit` Links to KenTender's own `Unit Of Measure` doctype, built during v1.1 Phase 1 (tracker row NDS-111) apparently because no native equivalent was found at the time | **Retarget to ERPNext `UOM`.** A native equivalent exists and always did; this was a v1.1-era defect the v1.6 spec now names explicitly. |
| `NeedsIntakeWindow` — **removed entirely** (§4.1, §16.4.11, §17) | `Needs Intake Window` is a live doctype (`opens_at`, `closes_at`, unique per PE/FY), with `save_needs_intake_window`/`get_needs_intake_window` commands and an owning screen (`IntakeWindowScreen.vue`, NDS-UI-08) | **Delete the doctype, its two commands, its screen and its route.** Replace with a read-only `get_needs_submission_state` contract reading `Fiscal Year.kentender_needs_submission_open`/`_closes_at` via `kentender_core.services.site_configuration`. |
| `Departmental Need Review Task` / `Departmental Need Decision` scope fields | Both carry `procuring_entity` alongside `organisation_unit`/`financial_year` | Drop the PE field on both; `Decision` also gains "exact User Responsibility Assignment ID and snapshot" (§4.5) in place of today's ad hoc `effective_assignment`/`scope` free-text Data fields once the resolver supplies a real assignment ID to record. |
| `DepartmentalNeedAccepted.v2` payload (§7.1) | Carries `procuring_entity` (PE ID) alongside OU/FY IDs | Drop the PE field from the published payload; §7.1's field list is OU/FY only, no PE. |

Field-naming note: v1.6 §4's prose uses `_id`-suffixed names (`need_id`, `org_unit_id`, `financial_year_id`, `unit_id`). `User Responsibility Assignment` — defined in the very same AUTH-ADR-001 v1.6 — uses plain names (`organisation_unit`, `business_role`, not `organisation_unit_id`). This gap analysis treats the `_id` suffixes as conceptual/documentation naming, not a literal schema mandate, and recommends **keeping the existing field names** (`organisation_unit`, `financial_year`, `unit`, `need_id`/`need_reference` already match) rather than a churn-only rename — recorded as decision D7 in the Implementation Plan so it is a deliberate choice, not a silent omission.

## 5. Authorization gap (§6, §16.4) — the largest item in this rebuild

**Current state**, confirmed by direct inspection:

- `kentender_procurement/kentender_procurement/departmental_needs/services/permissions.py` implements every scope check (`in_scope`, `permitted_values`, `require_create`, `require_author_command`, `require_review_command`, `require_intake_window_command`) on top of `frappe.get_all("User Permission", filters={"user": user, "allow": doctype}, ...)`, across `Procuring Entity` / `Organisation Unit` / `Financial Year` dimensions.
- `services/my_work_provider.py` and `services/notifications.py` call `permissions.in_scope(...)` directly, propagating the same dependency into My Work and notification-recipient resolution.
- A repo-wide grep for `kentender_core.services.authorization`, `require_responsibility`, `authorise_record` or `User Responsibility Assignment` inside `kentender_procurement` returns **zero hits**. Departmental Needs has never called the AUTH-ADR-001 resolver.
- By contrast, `kentender_budget/kentender_budget/services/budget_authorization.py` already does — `authorise_record(user=..., business_role=..., organisation_unit=..., purpose=PURPOSE_COMMAND)` from `kentender_core.services.authorization`, raising through `kentender_core.services.responsibility_errors.fail(...)` on denial. Strategy's `strategy_authorization.py` mirrors it. This is the pattern to match.
- `kentender_core/services/business_role_registry.py::REGISTRY` — the code-owned business-role registry AUTH-ADR-001 v1.6 §4.4 requires — **already contains `Departmental Author` and `Head of User Department`** as `scope_type = "Organisation Unit"`, citing `NDS-CHG-001 v1.4` in a source comment. This confirms the registry side of the cutover was anticipated ahead of this module's own migration; it needs its citation bumped to v1.6 and confirmation that `Procurement Planner` (Site-wide) and `Auditor` are present too.
- The acting-HoD mechanism today is "the same role + a time-bound scoped `User Permission` row" (existence = the time bound, per the v1.1 tracker's own decision log). AUTH-ADR-001 v1.6 §4.5 instead expresses this as one `User Responsibility Assignment` row with `appointment_type = Acting`, `effective_from`/`effective_to` and a required `authority_reference` — a real, queryable, auditable record rather than a User Permission's presence/absence.
- The v1.1 tracker's own recorded reason for choosing native permissions ("diverges from CFG-CHG-002 and STR-CHG-001, which both adopted `kentender_core.services.authorization_policy`") named the **wrong comparator**: `authorization_policy` is the legacy `ResourceContext`/`Capability Profile` engine that AUTH-ADR-001 itself retires everywhere (`kentender_core/services/authorization_diagnostics.py`, explicitly marked legacy). It was never a comparison against `kentender_core.services.authorization` (the resolver), which did not yet govern this module's spec at the time. NDS-CHG-001 v1.6 §6 — "User Responsibility Assignment is the sole source of the role-to-site-wide/OU relationship... Frappe User Permission... grant[s] no Departmental Needs authority" — and §16.4's explicit correction-slice checklist are unambiguous and postdate that reasoning. This gap analysis does not treat it as an open question.

**What §16.4's 13-step checklist requires, mapped to the current code** (this becomes the Implementation Plan's Phase 2 work list verbatim):

| §16.4 step | Target |
|---|---|
| 1. Replace User Permission/module-local scope logic with the shared resolver + assignment ID | `services/permissions.py` — full rewrite onto `authorise_record`/`require_responsibility` |
| 2. Remove FY/PE from `required_dimensions()`, remove FY/PE grant checks, remove any `allowed_years` gate | `services/context.py`, `services/permissions.py` |
| 3. `selectable_financial_years()` returns years represented by existing authorised records (filter only, not authority) | `services/context.py` / `services/workspace.py` |
| 4. Implement `list_need_create_targets()` — active Departmental Author OU assignments × the one FY with the flag open | New function, `services/context.py` or `api.py` |
| 5. Cut every list/count/detail/task/file/export/command scope check over in one slice, no fallback | Cross-cutting — `permissions.py`, `workspace.py`, `lifecycle.py` call sites |
| 6. Stop seeds/profiles creating User Permission/Financial-Year-grant authority; create `User Responsibility Assignment` rows instead | `seeds/kentender_mvp_r1.py`, `seeds/profiles.py`, `seeds/playwright_ui_fixtures.py` |
| 7. Clean obsolete rows only after code/seeds no longer read the old stores | Sequencing note for the Implementation Plan, not a Phase-1 action |
| 8. Cartesian-product regression: Grace as Author in one OU and acting HoD in another must not cross | New test in the rewritten permissions suite |
| 9. Verify multi-FY browsing without annual permission edits, create only while the flag is open, never trapped by a remembered year | Test + `context.py` behaviour |
| 10. Verify a parent-OU HoD assignment covers named descendants but never a sibling | Test, using `kentender_core.services.authorization.descendants_of` |
| 11. Remove `NeedsIntakeWindow`, its routes/commands/seeds/tests; remove all `PE Fiscal Year Context` reads | `services/context.py` currently reads `PE Fiscal Year Context` via `selectable_financial_years()` — confirmed present, must go |
| 12. Verify closing the flag blocks create/submit but leaves Draft/Returned editable; opening another FY leaves at most one open flag after one atomic command | Test against `kentender_core.services.site_configuration` |
| 13. Verify `kentender_needs_submission_closes_at` closes intake with the same effect as a manual close, and a command issued after close-but-before-reload is rejected server-side | Test |

**Error-contract note:** AUTH-ADR-001 v1.6 §10 defines its own closed code set (`AUTH_RESPONSIBILITY_REQUIRED`, `AUTH_SCOPE_REQUIRED`, etc.) via `kentender_core.services.responsibility_errors`, explicitly described as "the shared vocabulary of the resolver, not a replacement for a module's published error contract." Departmental Needs keeps its own closed §9 code set (`NDS_SCOPE_DENIED`, `NDS_CONTEXT_REQUIRED`, ...) and should catch `ResponsibilityError`/its `.code` at the service boundary and remap onto the existing `NDS_*` codes, rather than leaking `AUTH_*` codes to the client — the module's own `errors.py::fail()` already enforces a closed set and should be the single remap point.

## 6. Configuration substrate already built (reduces this rebuild's scope)

Two pieces of infrastructure this module needs **already exist in `kentender_core`**, installed ahead of this rebuild:

- `kentender_core/kentender_core/install.py::_ensure_fiscal_year_flag_fields` (wired via `after_migrate`) creates `kentender_needs_submission_open` (Check), `kentender_needs_submission_closes_at` (Datetime), `kentender_flag_changed_by`/`kentender_flag_changed_at` on ERPNext's `Fiscal Year` — exactly the two fields §4.1 specifies, plus audit fields.
- `kentender_core/services/site_configuration.py` already implements `open_needs_submission()` / `close_needs_submission()` / `close_due_needs_submissions()` (admin-gated writes) and a read function returning the currently-open Fiscal Year and its close instant.

Departmental Needs' own work here is purely **consumption**: `get_needs_submission_state()` reads through `site_configuration`, and every create/submit command rechecks the flag server-side inside its own transaction (NDS-BR-002, unchanged behaviour from today, just re-pointed at the new source). No new Fiscal-Year-flag infrastructure needs building.

## 7. Command and read-contract diff (§8)

The §8.2 command set is essentially unchanged from what v1.1 already built — `save_need_draft`, `submit_need_version`, `return_need_version`, `accept_need_version`, `decline_need_version`, `withdraw_unaccepted_need`, `create_accepted_need_successor`, `cancel_accepted_need_successor`, `request_accepted_need_withdrawal`, `decide_accepted_need_withdrawal`, `project_need_planning_usage` all already exist under their §8.2 names. The diff is entirely on the read side:

| §8.1 contract | Today | Gap |
|---|---|---|
| `resolve_needs_scope` | `resolve_needs_contexts` (PE/OU/FY-context-shaped) | Rename and reshape to the resolver's assignment/OU-scope shape; drop PE entirely |
| `list_needs_financial_years` | Not present under this name (`selectable_financial_years` exists internally) | Expose as its own §8.1 contract, ERPNext-Fiscal-Year-backed, filter-only |
| `list_need_create_targets` | Not present | New — §16.4 step 4 |
| `get_needs_submission_state` | Not present (`get_needs_intake_window` exists instead) | New, reading the Fiscal Year flag read-only |
| `get_needs_intake_window` | Present | **Delete** |
| `save_needs_intake_window` | Present | **Delete** |
| Everything else in §8.1 (`get_needs_workspace`, `get_departmental_need`, `get_departmental_review_task`, `get_current_accepted_need`, `check_accepted_need_withdrawal_dependency`) | Present under matching or near-matching names | Drop `procuring_entity` from filters/output; otherwise reusable |

## 8. UI diff (§10, §11)

The frontend is **already** Vue-in-Desk on the Industry design system (`DepartmentalNeeds.vue` root, `WorkspaceScreen.vue`, `ReviewScreen.vue`, `NeedEditorScreen.vue`, `NeedDetailScreen.vue`, `ReviewTaskScreen.vue`, `WithdrawalReviewScreen.vue`, `ContextPicker.vue`, `IntakeWindowScreen.vue`, dialogs), correctly *not* registered in `kt_cl_surface_registry.js`/`STITCH_DESK_SURFACES` (confirmed deliberate, documented convention shared with Budget, Strategy, Planning and System Setup — an already-verified override of the generic AUTH-ADR-001 §14.5 instruction). No shell or registry rework is needed. The concrete gaps:

- `ContextPicker.vue` currently resolves a PE **and** OU pair (the v1.1-era `CTX-CHG-001` "working context" layer, `kt_working_procuring_entity`/`kt_needs_org_unit`/`kt_needs_financial_year` user defaults). The PE dimension must be dropped entirely — KT-STD-001 §2.3 and NDS-CHG-001 v1.6 §1.1 both prohibit a Procuring Entity control on any screen.
- `IntakeWindowScreen.vue` and its `/intake-window` route are deleted outright. §11.11 explicitly reserves no NDS-owned configuration screen; any Fiscal-Year-flag display becomes a read-only line in the existing context strip (§11.2's "Open intake" row), sourced from `get_needs_submission_state`, not a page.
- `NeedEditorScreen.vue`'s unit source moves from the KenTender `Unit Of Measure` doctype to ERPNext `UOM`.
- Every NDS-DES artboard's fixture-context PE line is already outside the rendered artboard per KT-STD-001 §2.2 ("Fixture context ... is data outside the artboard ... It is not rendered") — confirmed by spot-checking §11.2–11.16 of the v1.6 spec, none of which show a PE row inside a card or table. No artboard content itself needs redrawing; only the live Vue components' PE selector/state need removing.
- NDS-DES-15 "Create need for" dialog (multi-OU choice) must be driven by `list_need_create_targets`, not the current context-resolution flow.

Playwright specs `departmental-needs-intake-window.spec.ts` and `departmental-needs-scheduled-window.spec.ts` (the latter tests the `Scheduled` intake state, which no longer exists once the doctype is deleted) are retired outright, not updated. The remaining five specs need their fixture setup and assertions updated for the single-PE, resolver-backed context.

## 9. Seeds, actors and tests

- **Actors.** Current seed creates `grace.wanjiku`, `peter.kimani`, `julia.njeri` (acting, via a scoped User Permission), `amina.hassan` (a bespoke Planner-duplicate actor — not the KT-STD-001 register's Accounting Officer), `mercy.kilonzo` (read-only Planner), `auditor.moh@example.test`. Per v1.6 §1.1 "New in v1.6" and KT-STD-001 §8.3: **drop** `amina.hassan@moh.example.test` from this module's fixtures entirely (it duplicated Mercy Kilonzo's assignment and has no module-specific role here), **replace** `auditor.moh@example.test` with `naomi.chebet@moh.example.test`, keep Grace/Peter/Julia/Mercy as named in §14.2 — each needs a `User Responsibility Assignment` (via the `kentender_core` grant command, not a raw insert) in place of today's `User Permission` rows.
- **Seed mechanics.** The seed already correctly drives real commands rather than inserting rows directly (`seeds/kentender_mvp_r1.py`, matching KT-STD-001 §8.6) — this pattern survives. The specific commands it needs to call change: `User Responsibility Assignment` grants instead of `_user_permission(...)` inserts, the seeded Fiscal Year becomes ERPNext's `Fiscal Year` opened via `site_configuration.open_needs_submission`, and units resolve against ERPNext `UOM` rows (`Programme`, `Each`) rather than the custom `Unit Of Measure` doctype.
- **Tests.** `test_departmental_needs_permissions.py` (771 lines) is organized entirely around `frappe.get_all("User Permission", ...)` manipulation and cross-PE isolation via a second `PE-CGKIS` fixture — this is a rewrite target, not a patch, including inverting its own `test_the_module_consults_no_parallel_permission_store` guard (today it forbids the *old* capability engine; it must come to forbid `User Permission` as an authority source instead, while *requiring* `kentender_core.services.authorization` usage). `test_departmental_needs_domain_model.py` (371 lines) asserts `procuring_entity` presence/immutability and intake-window uniqueness — both need removing and replacing with ERPNext-Fiscal-Year/UOM assertions. `test_departmental_needs_static_scan.py` needs its prohibited-concept list extended to include `Needs Intake Window`, `procuring_entity`, the custom `Financial Year`/`Unit Of Measure` doctypes, and any remaining `User Permission` authority read.
- **Open v1.1 follow-ups not part of this rebuild's scope**, recorded so they aren't rediscovered: FU-01 (Playwright fixture serialization), FU-02 (production-mode build never exercised — worth closing opportunistically once this rebuild reaches its own UI verification phase, since a fresh build is needed anyway), FU-03/04 (validation layering), FU-05 (stale pre-approval upload draft), FU-06 (a missing Procurement Home pipeline-count contract — v1.6 adds nothing to §8.1 that would close it), FU-09/FU-10/FU-13 (framework-level UI quirks). **FU-11** *is* addressed by this rebuild: the `Financial Year` User Permission mechanism it describes is exactly what §16.4 step 3 replaces (see `FOLLOW_UPS.md`).

## 10. Known open items carried into the plan

1. **Field-naming convention (D7).** Resolved in this analysis (§4) in favour of the existing plain-name convention; recorded as a decision rather than silently applied so a future reader does not "fix" it back toward the spec's `_id`-suffixed prose.
2. **Planning is not yet on AUTH-ADR-001 or this pattern.** `procurement_planning/services/authority.py` still runs on `User Permission` and the same legacy `Financial Year` doctype NDS is retiring, and the Planning spec itself is two versions behind what's approved (`v1.2` implemented vs. `PLN-CHG-001 v1.9` approved). This does not block NDS's own cutover — Planning consumes Departmental Needs only through the one-directional published-event contract (§7), which is unaffected by NDS's internal authorization mechanism — but a future session should not assume Planning's own scope checks are already aligned when building the next module against it.
3. **Budget is one version behind** (`v1.3` implemented vs. `BUD-CHG-001 v1.4` approved, which moves funding reservation to Procurement Requisition). Out of scope here; NDS only cites Budget for the `Procurement Budget Line` naming (§1.1 row 4), which is already correct at v1.3.
