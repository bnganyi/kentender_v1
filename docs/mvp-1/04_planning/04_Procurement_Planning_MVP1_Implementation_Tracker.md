# Procurement Planning MVP-1 Implementation Tracker

**Document ID:** PLANNING-MVP1-IMPL-TRACKER-2.0  
**Status:** Active — C00–C07 Done; PLN-NFR-001–005 Done  
**Date:** 13 August 2026  
**Supersedes:** [retired/04_Procurement_Planning_MVP1_Implementation_Tracker.md](retired/04_Procurement_Planning_MVP1_Implementation_Tracker.md) (REQ ≤1.5 / contribution-era Gate 05)

## Goal

Realign Procurement Planning to the **approved streamlined operating model** so that:

> **Approved Demand → Planner completes Plan Item → Finance confirms funding → Head of Procurement approves Plan Version → Tender take-up**

**Done looks like:** contribution / generic treatment / Demand-stage Finance duplicate / silent PE fallbacks **gone**; **every** Planning screen — **PLN-UI-01…10, PLN-UI-05A, and PLN-UI-07A** — is a **full literal Stitch re-implementation** of the approved `ui_design/*.html` (Stitch v2.0 for 05/05A; v1.9 canvases otherwise), not a touch-up of the contribution-era fixtures; live services bound; canonical seed v2.7 arithmetic green twice; Cursor pack v1.8 DoD + AC matrix evidenced by automated tests — not Administrator smoke or title-only guards.

**UI scope lock (non-negotiable):** Stitch v2.0 (05 overflow + 05A) and v1.9 remaining canvases have **substantial** composition/workflow changes across the whole journey. Tracker work must **re-implement all screens**. Selective “fix UI-04 / UI-08 only” or “re-verify existing fixtures” is **wrong** and is not UI Done for any skipped screen.

---

## Documentation read gate (mandatory before any ticket)

| Doc | Role |
|---|---|
| [KenTender_MVP_Cross_Module_Operating_Model_v1.1.md](../00_common/KenTender_MVP_Cross_Module_Operating_Model_v1.1.md) | **Controlling** business model (PO-approved) |
| [Procurement_Planning_MVP1_Requirements_v1.9.md](Procurement_Planning_MVP1_Requirements_v1.9.md) | Behaviour / FR / AC / removals (incl. PLN-FR-066…069A, PLN-UI-05A) |
| [Procurement_Planning_MVP1_Stitch_Prompts_v2.0.md](Procurement_Planning_MVP1_Stitch_Prompts_v2.0.md) | Screen contracts (05 overflow + 05A) |
| [ui_design/](ui_design/) | **Approved Stitch HTML** — UI source of truth (`PLN-UI-01`…`10`, `PLN-UI-05A_*`, `PLN-UI-07A`) |
| [Procurement_Planning_MVP1_Cursor_Implementation_Pack_v1.8.md](Procurement_Planning_MVP1_Cursor_Implementation_Pack_v1.8.md) | Ordered Cursor Prompts 01–07 |
| [KenTender_Cursor_Direct_MVP_Correction_Pack_v1.0.md](KenTender_Cursor_Direct_MVP_Correction_Pack_v1.0.md) | Cross-module correction mandate |
| [KenTender_MVP_Canonical_Demo_Data_Contract_v2.7.md](../00_common/KenTender_MVP_Canonical_Demo_Data_Contract_v2.7.md) | Seed identities + SCN-PLN-ADD-001 / SCN-PLN-REMOVE-001 / FUND-SHORT |
| [KenTender_Cross_Module_Authorization_Surface_Design_and_Cursor_Pack_v1.0.md](../00_common/KenTender_Cross_Module_Authorization_Surface_Design_and_Cursor_Pack_v1.0.md) | Neutral vs task surfaces |
| [00_KenTender_Procuring_Entity_and_Organisation_Scope_Model.md](../00_common/00_KenTender_Procuring_Entity_and_Organisation_Scope_Model.md) | PE/OU scope |
| Disposition audit `99_audit/00`–`09` | Repo locations for Keep / Correct / Remove |

**Precedence:** CMOM v1.1 → REQ v1.9 → Stitch HTML + prompts v2.0 → Cursor pack v1.8 → Demo contract v2.7 → Auth surface pack → Org scope → repo conventions that do not conflict.

**Historical packs (≤ REQ 1.8 / Stitch 1.9 / Cursor 1.7 / Demo 2.6) remain valid for canvases not changed in v2.0; Plan Item removal follows v1.9 / v2.0 / v1.8 / v2.7.** Contribution-era GATE_05 is superseded — do not treat those Done rows as current Done.

---

## How to use this tracker

1. Update only **Status** and **Evidence**. Do not delete rows — use **Out of scope** / **Blocked**.
2. **UI Done** requires **all** of § UI rigor below — gate-green alone is insufficient. **Every** `PLN-UI-01…10` / `07A` row must reach Done via a **full Stitch re-implementation**; none are exempt because an older fixture already exists.
3. Domain/service **Done** only with named automated tests green on `kentender.midas.com`.
4. Do not start a UI row before its service dependencies are Done or Partial with an explicit note — but **do not** treat an old fixture as satisfying the UI row.
5. Prefer clean teardown/reseed over compatibility shims (Correction Pack §1). No dual-write; no renamed contribution.
6. **Do not** narrow correction gates to “the changed bits” of a few screens. Gate C03–C06 each **fully re-port** every screen assigned to that gate.

### Status vocabulary

| Status | Meaning |
|---|---|
| Not started | No work under this baseline |
| In progress | Active coding |
| Partial | First pass; DoD incomplete (for UI: legacy fixture may still be mounted — **not** Stitch v1.9 Done) |
| Re-implement required | Screen must be fully re-ported from Stitch v1.9; existing fixture is **not** authority |
| Done | Evidence filled; tests green; for UI: **full** literal Stitch v1.9 match + Playwright + chrome |
| Blocked | Cannot proceed; note blocker |
| Out of scope | Explicitly deferred (see § Deferred) |
| Remove-pending | Exists in repo; must be deleted under this baseline |
| Keep | Retained **domain** foundation only; **never** use Keep for a Stitch screen row |

---

## UI rigor and locked patterns (non-negotiable)

Apply on **every** `PLN-UI-*` / `PLN-UIC-*` row. Violations = not Done.

| Rule | Source | Required evidence |
|---|---|---|
| **Literal Stitch port** | `.cursor/rules/kentender-stitch-literal-port.mdc` | Fixture/`<main>` matches `ui_design/PLN-UI-XX.html` DOM hierarchy + **retain Stitch utility classes**; no lean BEM approximation |
| **No Tailwind CDN in Desk** | Stitch desk chrome | Shared chrome CSS + module CSS under `.kt-cl-shell .kt-pln-root` |
| **Desk chrome registry** | `kentender-stitch-desk-chrome.mdc` | Surface in `stitch_desk_chrome_registry.py` + `assertStitchDeskChrome` / chrome gate |
| **Form errors** | `kentender-form-errors.mdc` | `{ok:false, errors:{field}}` + `ktFormErrors` inline; **no** Message dialog for field validation |
| **No truncate** of legal identity | `kentender-no-truncate-legal-data.mdc` | OU / title / code / money wrap or scroll — no ellipsis on decision data |
| **Reference display** | dropdown/reference standard | Store `id`; show `name` + `code`; never raw PK |
| **Task vs record** | Auth surface pack + CMOM §11 | Unauthorised task actions/routes **absent** + server deny — not disabled forms |
| **Workspace pattern** (list/detail if used) | `kentender-workspace-pattern-lock.mdc` | Master-detail contracts + testids |
| **Table footer** (list tables) | stitch desk table footer | Shared pagination footer helper where Stitch shows pager |
| **Visual side-by-side** | stitch-literal-port | Stitch HTML vs Desk canvas before UI Done |
| **Playwright** | TDD quality gate | Surface opens; contract testids; role denial; no Message dialog on field errors |

**Construction order for each screen (apply to UI-01…10 and 07A — no exceptions):** open approved HTML → **replace** fixture/`<main>` with literal port (+ overlays) → `kt-stitch-canvas` / testids / bind hooks only → chrome registry → live-bind → visual side-by-side vs Stitch → Playwright. Incremental CSS/string patches on the contribution-era layout **do not** count.

**PLN-UI-07 renumbering:** Contribution drawer is **removed**. **PLN-UI-07 / 07A** are Finance confirmation (sufficient / shortfall). Do not revive contribution under a new label.

**Full-screen inventory (all mandatory):**

| Screen | Gate | Must re-implement |
|---|---|---|
| PLN-UI-01 Workspace | C03 | Yes — full canvas |
| PLN-UI-02 Create / register Plan | C03 | Yes — full canvas |
| PLN-UI-03 Empty Draft builder | C03 | Yes — full canvas |
| PLN-UI-04 Add approved Demands (+ formation) | C03 | Yes — full dialog/canvas |
| PLN-UI-05 Draft with Plan Items | C03 | Yes — full canvas |
| PLN-UI-05A Remove / propose-removal confirm | C03 | Yes — overlay (Draft / Finance / Active) |
| PLN-UI-06 Plan Item editor | C04 | Yes — full canvas |
| PLN-UI-07 Finance confirm (sufficient) | C05 | Yes — full task surface |
| PLN-UI-07A Finance confirm (shortfall) | C05 | Yes — full task surface |
| PLN-UI-08 HoP review / approve | C05 | Yes — full canvas |
| PLN-UI-09 Approved Plan + implementation | C06 | Yes — full canvas |
| PLN-UI-10 Draft update overview | C06 | Yes — full canvas |

---

## Current repo baseline (from disposition audit)

| Area | State vs this baseline |
|---|---|
| Plan / Version / Item / Allocation / Plan Decision / validate / approve (professional) | **Keep** foundations; Correct gates/readiness |
| Departmental Submission + `submit_departmental_contribution` + old UI-07 drawer + contrib submit gate | **Removed** (C02 / REM-001…005) |
| Demand-stage BO confirmation as Planning prerequisite | **Correct** — Finance after Plan Item only |
| PLN-UI-01…10 + 07A fixtures / Desk mounts | **UI-01…10 Done** (Stitch v1.9 + UI-05A v2.0 + UI-07/07A Finance + UI-08 HoP review + UI-09 Approved + UI-10 Draft update). |
| PLN-UI-07 / 07A Finance | **UI-07 Done** (literal Stitch drawer + SVC-007). **UI-07A Done** (SCN-PLN-FUND-SHORT-001 + recovery; `make ui-planning-finance-gate`) |
| PLN-UI-09 / 10 | **UI-09 Done**; **UI-10 Done** (draft-update canvas) |
| PE-MOH / Admin inflation (Budget/Home/Strategy) | Cross-module Correct (Correction Pack A) — track under shared + Planning consumers |
| Canonical seed contribution/treatment rows | **Removed** from active schema/UI (C02); seed rebuild to Demo v2.7 is C07 Done |

---

## Correction gates (Cursor pack v1.7)

| ID | Gate | Cursor Prompt | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-GATE-C00 | Baseline lock | — | Docs above accepted | Done | This tracker + CMOM 1.1 / REQ 1.8 / Stitch 1.9 / Cursor 1.7 |
| PLN-GATE-C01 | Scope + task authority | Prompt 01 | C00 | Done | `test_planning_task_capability` (7) + matrix/PE + Playwright `planning-task-route-denial.spec.ts` (5); `make ui-planning-scope-auth-gate` |
| PLN-GATE-C02 | Remove superseded structures | Prompt 02 | C01 | Done | `test_planning_contribution_absent` (5); submit/decision/gate05 + layout forbid; migrate + patch drop DocType; `make ui-planning-approval-gate` green; builder/editor Playwright (no pref/contrib); Finance submit gate deferred C05 |
| PLN-GATE-C03 | **Full re-implement** PLN-UI-01…05 (+ formation services) | Prompt 03 | C02 | Done | UI-01…05 Stitch v1.9 ports; layout guard + Playwright + `make ui-planning-builder-gate` green; AC-016 Done (server reject + Combine disabled) |
| PLN-GATE-C04 | **Full re-implement** PLN-UI-06 Plan Item editor | Prompt 04 | C03 | Done | Literal Stitch v1.9 editor; layout guard + `planning-plan-item-editor.spec.ts` + `test_update_plan_item` (8) + `make ui-planning-builder-gate` green; Request Finance completeness only (no SVC-007 task) |
| PLN-GATE-C05 | **Full re-implement** PLN-UI-07 / 07A / 08 + Finance/professional services | Prompt 05 | C04 | Done | UI-07 + UI-07A + UI-08 literal Stitch; SVC-007…011; `test_submit_plan_for_review` 4/4; `test_record_plan_decision` 5/5; `test_approve_plan_version_gate05` 5/5; layout guard UI-08; Playwright `planning-plan-review.spec.ts` 3/3 + `assertStitchDeskChrome`; `planning-finance-confirm.spec.ts` |
| PLN-GATE-C06 | **Full re-implement** PLN-UI-09 / 10 + successor/publish/handoff | Prompt 06 | C05 | Done | **UI-09 + UI-10 Done** (literal Stitch + SVC-012…015 + `get_plan_update` / `save_plan_update`). Seed SCN-ADD arithmetic closed in C07 |
| PLN-GATE-C07 | Canonical seed + regression close-out | Prompt 07 | C06 | Done | SEED-001/002/004/005 + REM-009 + SVC-016 + AC-013/020; `test_scn_pln_add_001` 7/7; `test_planning_mvp_seed_contract`; `make ui-planning-mvp1-gate`. **NFR-001–004 Done** (`planning-a11y.spec.ts` 4/4; `make ui-planning-a11y-gate`) |

**Makefile targets:** `ui-planning-contribution-gate` removed (C02); absence covered by `test_planning_contribution_absent` inside `ui-planning-approval-gate`. **`ui-planning-finance-gate` added (C05 UI-07)**. **`ui-planning-mvp1-gate` added (C07)** — chrome once + seed/SCN/REM + AC-013 Playwright.

---

## 1. Removals (`PLN-REM-*`)

| ID | Work item | Exact targets (repo) | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-REM-001 | Departmental Submission DocType + writers | `doctype/departmental_submission/`; seeds; clear helpers | C01 | Done | DocType folder deleted; `c02_drop_departmental_submission` patch; seed clear no longer references DS; migrate `kentender.midas.com` |
| PLN-REM-002 | Contribution services/API | `submit_departmental_contribution`, `get_departmental_contribution`, whitelist | C01 | Done | Services deleted; API whitelist gone; `test_planning_contribution_absent` import/API asserts |
| PLN-REM-003 | Contribution UI + gate | `contribution_drawer.js`, builder bind, `prepare_planning_gate05_ui` contrib, `ui-planning-contribution-gate`, Playwright contrib | C02 | Done | Drawer/spec deleted; builder CTA `submit-for-review`; contrib Makefile target removed; layout forbid markers |
| PLN-REM-004 | Contribution readiness on submit | `submit_plan_for_review` contribution prerequisite + copy | C02 | Done | Ready-only gate; `test_planner_submits_for_review_without_contribution`; Finance confirm = C05 |
| PLN-REM-005 | Contributor contribution capability | Planning Contributor contrib asserts / USA where only for contrib | C02 | Done | `CAP_DEPT_CONTRIB_TASK` / frozensets / assert removed; role may remain for ADD_DEMAND |
| PLN-REM-006 | Generic Plan Item treatment/statutory fields | Retired `statutory_*` / `planned_treatment_value` / `value_treatment_note` — finish schema purge | C02 | Done | Fields removed from `procurement_plan_item_version.json`; meta absence tests |
| PLN-REM-007 | Item-level preference scheme editors (superseded) | Writable preference/reservation scheme / target-group / planned-value if present | C02 | Done | Editor Preference UI removed; `update_plan_item` ignores preference keys; schema fields read-only for coverage |
| PLN-REM-008 | Tests that only prove contribution | Replace with Finance/professional coverage; do not delete coverage volume | C02 | Done | Contrib suite deleted; absence + rewired Gate05 helpers; approval/builder gates green |
| PLN-REM-009 | Active references search | Grep schema/services/UI/seeds/tests for Submission/contribution/OU_SIGNOFF | C07 | Done | `test_planning_rem009_absent` — no active writers; absence tests + layout forbids + DTO stub keys only |

---

## 2. Shared / permissions (`PLN-PERM-*`)

| ID | Work item | Notes | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-PERM-001 | Zero / one / multi PE deliberate selection | PLN-FR-002…004; no PE-MOH invent | C01 | Done | `test_resolve_pe_for_create_zero_one_multi` + `test_planning_pe_scope_selection` |
| PLN-PERM-002 | Admin alone no operational authority | PLN-FR-084 | C01 | Done | `test_admin_without_usa_*` + matrix Admin deny; USA-only `actor_planning_roles` |
| PLN-PERM-003 | Record vs task vs mutation projection | Auth pack; PLN-FR-080…083 | C01 | Done | `get_plan_review` surface task/neutral; omit CTAs in `bindPlanningReview`; contrib task capability |
| PLN-PERM-004 | Finance task capability | Budget Officer only; deny Requester/Planner/HoD/Viewer/Admin-without-task | C05 | Done | `assert_can_open_finance_task` + `test_plan_item_finance.test_planner_requester_admin_denied`; Playwright planner cannot open drawer; BO Page.roles on builder/workspace |
| PLN-PERM-005 | Professional approval capability | Head of Procurement / configured authority | C05 | Done | `test_reviewer_cannot_approve_plan` + `test_reviewer_and_approver_task_surface`; Playwright `planning-task-route-denial.spec.ts` Reviewer Recommend ≠ Approve |
| PLN-PERM-006 | Direct-route + API denial tests | Playwright + service negatives | C01, C05 | Done (Planning-scoped C01 + UI-07) | `planning-task-route-denial.spec.ts`; Finance: `planning-finance-confirm.spec.ts` planner deny + service 403 |

---

## 3. Domain / services (`PLN-SVC-*`)

| ID | Work item | Capability (REQ §12.1) | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-SVC-001 | Workspace projection | Scoped workspace | C03 | Keep / Correct | Existing `get_planning_workspace` — revalidate |
| PLN-SVC-002 | Register annual Plan | create/register | C03 | Keep | |
| PLN-SVC-003 | List eligible Demands | Eligibility | C03 | Done | `proposed_funding` + Planning Ready status fields; multi-select UI-04 |
| PLN-SVC-004 | Add Demand(s) + formation | Atomic one/multi Separate|Combine | C03 | Done | Multi `demands` + `separate`\|`combined` in one confirm; legacy Need-Item separate retained; Gate04 tests green |
| PLN-SVC-005 | Update Plan Item | Save Draft Item Version; no source reselect; admitted fields only | C04 | Done | REQ §9.4 register; HoD facts rejected; Multi-year extra fields not required; Request Finance completeness (`test_update_plan_item` 8/8) |
| PLN-SVC-006 | Validate Plan | Issue-led Ready | C04 | Keep / Correct | Finance confirmation as readiness input |
| PLN-SVC-007 | Request / record Finance confirm|return | PLN-FR-040…049; reuse Demand Funding Allocation + Budget reserve | C05 | Done | `test_plan_item_finance` 10/10; request idempotent; confirm reserves/reuses RSV; return requires reason; shortfall reject; stale; draft remove cancels Awaiting |
| PLN-SVC-008 | Finance shortfall behaviour | No confirm/partial/override; same-task recovery | C05 | Done | `test_scn_pln_fund_short_001` 4/4; `test_plan_item_finance` 13/13 (`test_scn_shortfall_*` 80/25/55 + `PLN_INSUFFICIENT_FUNDING` + recovery after `release_reservation`); Playwright 07A; `make ui-planning-finance-gate` |
| PLN-SVC-009 | Submit for review | Ready + **current Finance** for all items; **no** contribution | C05 | Done | `test_submit_plan_for_review` 4/4 (`test_submit_blocked_until_finance_confirmed`); `finance_not_confirmed_error`; prep confirms funding before submit |
| PLN-SVC-010 | Record professional decision | Return / Approve trail | C05 | Done | `test_record_plan_decision` 5/5 (recommend / return comment / role deny / stale token); Stitch **Return to planner** |
| PLN-SVC-011 | Approve Plan Version | Atomic lock / Effective / supersede | C05 | Done | `test_approve_plan_version_gate05` 5/5 (`test_approve_denied_when_finance_not_confirmed`); Finance re-check on approve |
| PLN-SVC-012 | Open/reuse/cancel Draft successor | Quiet successor | C06 | Done | Reuses `open_or_create_plan_revision` + `add_demand_to_plan`; UI-09 Add Plan Item; `test_get_plan_implementation.test_successor_notice_after_add_to_approved`; Playwright successor banner |
| PLN-SVC-013 | Publish / export Approved | Publication evidence | C06 | Done | `test_publish_approved_plan` 2/2 (Published event; failure keeps Approved); UI-09 Export CTA |
| PLN-SVC-014 | Tender handoff snapshot | Immutable handoff | C06 | Done | `test_create_planning_handoff_snapshot` 2/2 (immutable JSON; idempotent; blocks propose); UI-09 take-up read — no TM2 Tender create |
| PLN-SVC-015 | Implementation / audit projections | Derived downstream | C06 | Done | `test_get_plan_implementation` 4/4; take-up Not taken up / omit progress when no downstream; no invented realised value |
| PLN-SVC-016 | Capability → service map | Cursor §5 naming rule — one public name per behaviour | C07 | Done | See C07 close-out capability map (report only; no alias services) |
| PLN-SVC-017 | Remove Plan Item from plan | `remove_plan_item_from_plan` — server-derived draft exclude / propose Active; no hard-delete | C03 | Done | `test_remove_plan_item` 12/12; `release_draft_finance_effects` cancels Awaiting (`test_draft_remove_cancels_awaiting_task`); UI-09 Propose overflow reuses 05A (omit when handoff) |

---

## 4. UI screens (`PLN-UI-*` / `PLN-UIC-*`)

Stitch source: `ui_design/PLN-UI-XX.html` (07A: `PLN-UI-07A.html`).

**Authority:** Stitch v2.0 HTML is the UI contract for **PLN-UI-05 overflow + PLN-UI-05A**; Stitch v1.9 HTML remains the contract for other listed screens. Pre-correction fixtures may remain mounted until each gate lands; they are **not** Done evidence. Status **Re-implement required** means a full literal port is still outstanding even if Playwright smoke exists against the old canvas.

| ID | Screen | Stitch HTML | Depends on | Status | Evidence / exit |
|---|---|---|---|---|---|
| PLN-UI-01 | Planning workspace | `PLN-UI-01.html` | SVC-001, PERM-001 | Done | Literal Stitch v1.9 port; helper + plan strip + work select/search + `attachPagination`; layout guard + `planning-workspace.spec.ts`; `make ui-planning-workspace-gate` green |
| PLN-UI-02 | Create annual Plan | `PLN-UI-02.html` | SVC-002 | Done | Literal Stitch v1.9 port (numbered sections, input-glow, calendar period, sticky Create/`add_task`); no Budget field; inline errors; layout guard + `planning-register.spec.ts`; `make ui-planning-workspace-gate` green |
| PLN-UI-03 | Empty Draft builder | `PLN-UI-03.html` | UI-01 | Done | Literal Stitch empty canvas + **standardized horizontal summary strip** (Total Planned Value, Validation Status, dividers; no icon grid); layout guard + `planning-builder.spec.ts`; `make ui-planning-workspace-gate` green |
| PLN-UI-04 | Add approved Demands | `PLN-UI-04.html` | SVC-003/004 | Done | Corrected Stitch 7-col table (no absolute selection td); literal dialog + multi-select Separate\|Combine; proposed funding DTO; layout guard + `planning-add-demand.spec.ts`; `make ui-planning-builder-gate` green |
| PLN-UI-05 | Draft with Plan Item | `PLN-UI-05.html` | UI-04, SVC-006 | Done | Literal Stitch v1.9 populated builder (Desk crumbs only — no in-canvas trail, issue strip, 8-col table + live Finance status, filler row, sticky footer); empty UI-03 preserved; **v2.0 overflow** `more_vert` **Remove from draft** when `can_remove_from_draft`; layout guard + `planning-builder.spec.ts`; `make ui-planning-builder-gate`; Finance confirm CTA for BO is UI-07 |
| PLN-UI-05A | Remove / propose-removal confirm | `PLN-UI-05A_Draft.html`, `_Finance.html`, `_Active.html` | UI-05, SVC-017 | Done | Literal three-variant overlay + `ktFormErrors` reason; no Delete / source checkboxes; layout guard + `planning-builder.spec.ts` 05A; `make ui-planning-builder-gate` green; visual vs Stitch 05A Draft. UI-09 Propose overflow reuses this overlay; draft remove cancels Awaiting via SVC-007 |
| PLN-UI-06 | Plan Item editor | `PLN-UI-06.html` | SVC-005 | Done | Literal Stitch v1.9 port (Procurement approach, Indicative lotting, Planned schedule, Approved source, Request Finance footer; Desk crumbs only); layout guard + `planning-plan-item-editor.spec.ts`; `make ui-planning-builder-gate` green; visual vs `PLN-UI-06.html`; Request Finance now creates Awaiting task (SVC-007) |
| PLN-UI-07 | Finance confirm — sufficient | `PLN-UI-07.html` | SVC-007, PERM-004 | Done | Literal Stitch right-side drawer on builder; live `get_plan_finance_task` / confirm / return; `ktFormErrors` on reason; layout guard + `planning-finance-confirm.spec.ts` 3/3; `make ui-planning-finance-gate` green; visual vs `PLN-UI-07.html` |
| PLN-UI-07A | Finance confirm — shortfall | `PLN-UI-07A.html` | SVC-008 | Done | Same-task 07A drawer (no Confirm node); live 80/25/55 + Insufficient funding; Resolve `budget_funding_route` → Budget activity; `ktFormErrors` return; SCN-PLN-FUND-SHORT-001 + recovery; Playwright `planning-finance-confirm.spec.ts` 07A 3/3; `make ui-planning-finance-gate` green |
| PLN-UI-08 | HoP review / approve | `PLN-UI-08.html` | SVC-009…011 | Done | Literal Stitch `procurement-plan-review`: title **Review and approve procurement plan**; Finance Confirmed strip + Finance column; issues first; gavel **Professional approval**; **Return to planner** / **Approve plan** (Reviewer **Recommend approval**); coverage omit-if-empty; layout guard; `planning-plan-review.spec.ts` 3/3 + `assertStitchDeskChrome` |
| PLN-UI-09 | Approved Plan + implementation | `PLN-UI-09.html` | SVC-012…015 | Done | Literal Stitch `procurement-plan-approved`: title, Open Plan · Approved Version N · read-only helper, Add Plan Item / Export, 5 KPIs, 8-col implementation table, publication card; successor banner only with Draft; workspace Approved → UI-09; Continue/View changes → UI-10; layout guard `test_plan_approved_fixture_markers`; Playwright `planning-plan-approved.spec.ts` 4/4 + `assertStitchDeskChrome` |
| PLN-UI-10 | Draft update overview | `PLN-UI-10.html` | SVC-012, UI-04 | Done | Literal Stitch `procurement-plan-update`: title **Plan update**, Draft · Needs attention, Run validation, Approved-remains-active banner, dual totals + change, Update context + reason, 7-col Changes table, unchanged expand, issue strip, Cancel / Save / Submit; never-approved Drafts stay on builder; successor builder redirects here; `test_get_plan_update` 7/7; layout guard `test_plan_update_fixture_markers`; Playwright `planning-plan-update.spec.ts` 3/3 + `assertStitchDeskChrome`; UI-09 Continue → `/procurement-plan-update` |
| PLN-UIC-001 | Stitch Desk chrome for **all** Planning routes | Registry + gates | Each UI | Done | 7 Planning Desk routes in `STITCH_DESK_SURFACES` + `stitch-desk-chrome.spec.ts`; overlays keep host-spec `assertStitchDeskChrome`; `make ui-stitch-desk-chrome-gate` green (Python 3/3 + Playwright 26/26) |
| PLN-UIC-002 | Inline form errors (return/confirm notes, formation reason, removal reason) | ktFormErrors | UI-02/04/05A/07/08 | Done | UI-02/05A/07/07A/08 + UI-04 Combine empty reason → `[data-kt-field-error="formation_reason"]`; no Message dialog (`planning-add-demand.spec.ts`) |
| PLN-UIC-003 | Layout / Stitch contract guards | `test_planning_ui_stitch_layout_guard` | Each UI | Done | UI-01…10 + 05A + 07A markers; `data-kt-field-error` on formation_reason / update_reason; approved + update page JS in `test_assets_exist`; 17/17 green |

---

## 5. Seed (`PLN-SEED-*`)

| ID | Work item | Notes | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-SEED-001 | Rebuild Planning seed to Demo Contract v2.7 | 455m item; Finance **after** Plan Item; no contribution/treatment | C02, C05 | Done | `test_planning_mvp_seed_contract` + `validate.py` (`planning.rsv_0001_after_plan_item`, `planning.no_scn_item_at_base`); double-run `run_kentender_mvp_v1` |
| PLN-SEED-002 | SCN-PLN-ADD-001 | V1 operational; V2 535m; RSV-MOH-0002 after Finance | C06 | Done | `test_scn_pln_add_001` 7/7 — Demand 019 Planning Ready **no RSV**; `stop_before_finance` Draft 535m + V1/Tender live; Finance then `RSV-MOH-0002`; approve V2 |
| PLN-SEED-002A | SCN-PLN-REMOVE-001 | Draft-only remove PPI-MOH-2027-022; restore 455m + DMD-019 eligibility | SVC-017, UI-05A | Done | `test_scn_pln_remove_001` 3/3; reason exact Demo v2.7 §7.8 |
| PLN-SEED-003 | SCN-PLN-FUND-SHORT-001 | Optional shortfall; no partial reserve | C05 | Done | `test_scn_pln_fund_short_001` 4/4; `RSV-MOH-SHORT-001` 55m; no `RSV-MOH-0002` while short; reset restores HWD availability |
| PLN-SEED-004 | Personas USA | Requester, HoD, Planner, BO, HoP, Viewer — explicit PE/OU | C01 | Done | `test_seed_004_persona_usa` — Requester+HoD (`Business Approver`) DHP/HRMD; Planner/BO/HoP/Viewer PE-MOH |
| PLN-SEED-005 | Idempotent double-run + Kisumu isolation | validate.py | C07 | Done | `test_idempotent_second_run` + `test_scn_add_double_run_no_duplicates`; `validate.py` `include_scn_add`; county Demand unplanned |

---

## 6. Acceptance criteria (`PLN-AC-*`)

Map to REQ v1.9 §16. Mark Done only with test IDs.

| ID | Criterion (summary) | Primary proof | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-AC-001 | Multi-PE deliberate; zero blocks; one visible | Scope tests | PERM-001 | Done | `test_resolve_pe_for_create_zero_one_multi` + `test_single_pe_forces_assignment` + `test_zero_scope_blocks_create`; Playwright UI-01 PE filter assigned PE only (`planning-workspace.spec.ts`); UI-02 zero/one/multi (`planning-register.spec.ts`) |
| PLN-AC-002 | One Demand → one Plan Item; formation hidden | SVC-004 + UI-04 | C03 | Done | Playwright: formation hidden for single selection |
| PLN-AC-003 | UI-06 no Demand reselect | UI-06 + layout | C04 | Done | Layout guard forbids Add another Demand; Playwright `planning-plan-item-editor.spec.ts` |
| PLN-AC-004 | Editor field register only | UI-06 + REM | C04 | Done | Layout guard + fixture: no preference/contribution/multi-year extra; `test_update_plan_item` |
| PLN-AC-005 | Cannot edit HoD facts in Planning | SVC-005 negatives | C04 | Done | `test_hod_owned_facts_rejected` |
| PLN-AC-006 | Planning Ready ≠ Finance approval | Lifecycle | C05 | Done | Completeness does not set Confirmed (`test_completeness_does_not_confirm_finance`) |
| PLN-AC-007 | BO Confirm / pending shortfall / Return; unauth deny | UI-07/07A | C05 | Done | `planning-finance-confirm.spec.ts` BO confirm + return inline error + planner deny; `test_shortfall_rejects_confirm`; 07A omits Confirm |
| PLN-AC-008 | Confirm reserves atomically; becomes Stale | SVC-007 | C05 | Done | `test_confirm_reserves_and_retry_is_idempotent` + `test_stale_after_amount_change` |
| PLN-AC-009 | Submit needs Finance; never contribution | SVC-009 | C05 | Done | `test_submit_blocked_until_finance_confirmed`; complete item without Finance → `{ok:false}`; after confirm → In review; no contribution gate |
| PLN-AC-010 | HoP Approve/Return; unauth deny task form | UI-08 | C05 | Done | `test_record_plan_decision` + Playwright reviewer Return inline error / Approver Approve / planner no task CTAs |
| PLN-AC-011 | Approved immutable | SVC-011 | C05 | Done | `test_04_immutable_approved_version` + `test_approved_version_rejects_update_plan_item` |
| PLN-AC-012 | Add to Approved → quiet Draft successor | SVC-012 | C06 | Done | `test_successor_notice_after_add_to_approved`; Playwright successor banner + Continue → UI-10; Add reuses UI-04 |
| PLN-AC-013 | V1 + Tender operational during V2 Draft | SCN-ADD | C06 | Done | `test_draft_535m_v1_and_tender_remain_operational`; Playwright `planning-plan-approved.spec.ts` + `planning-plan-update.spec.ts` AC-013 (`stop_before_finance`) |
| PLN-AC-014 | Multi same-OU Combine + reason + lineage | UI-04 | C03 | Done | `test_multi_demand_combined_same_ou_requires_reason` |
| PLN-AC-015 | Multi Separate → real Items; no cosmetic Keep separate | UI-04 | C03 | Done | `test_multi_demand_separate_creates_n_items` + Need-Item separate path |
| PLN-AC-016 | Cross-OU Combine rejected | SVC-004 | C03 | Done | `test_multi_demand_combined_mixed_ou_rejected` + `test_multi_demand_separate_mixed_ou_creates_two_items`; Playwright UI-04 Combine disabled + callout (`planning-add-demand.spec.ts`) |
| PLN-AC-017 | Derived coverage omit-if-empty | UI-08 | C05 | Done | `get_plan_review` `statutory_coverage` empty when no designation; fixture section hidden; Playwright `kt-pln-ui08-statutory` hidden |
| PLN-AC-018 | Strategy SVC pass-through unchanged | Handoff | C06 | Done | `test_copies_demand_strategy_and_pvc_snapshots` + `test_strategy_and_pvc_writes_ignored_from_editor`; seed V1 IV backfill from Demand labels |
| PLN-AC-019 | Tender take-up Active only + snapshot | SVC-014 | C06 | Done | `test_create_planning_handoff_snapshot` 2/2; UI-09 reads take-up (`Tender active` + code); omit Propose when handoff; Playwright handoff case |
| PLN-AC-020 | Seed twice + arithmetic | SEED-005 | C07 | Done | `test_scn_add_double_run_no_duplicates` — 455 / 535 / 80; one 022 / one RSV-0002 |
| PLN-AC-021 | Neutral view ≠ task forms | PERM-003/006 | C01 | Done | `test_viewer_neutral_read_mutation_and_task_denied`; Playwright Viewer no UI-08 task CTAs + no UI-07 Confirm (`planning-task-route-denial.spec.ts`, `planning-finance-confirm.spec.ts`) |
| PLN-AC-022 | Shortfall exact deficit; no override; same-task recovery | UI-07A | C05 | Done | `test_scn_shortfall_task_is_80_25_55` + `test_scn_shortfall_confirm_rejects_without_reserving` + `test_scn_shortfall_recovers_after_releasing_hold`; Playwright 07A money + no Confirm + recovery |
| PLN-AC-023 | Draft-only remove from UI-05/10; history kept; Demand eligible | UI-05A + SCN-REMOVE | C03 | Done | `test_remove_plan_item` draft-only + Playwright 05A; `test_scn_pln_remove_001`; UI-10 overflow **Remove from update** → 05A (`planning-plan-update.spec.ts` last-Added → No changes remain) |
| PLN-AC-024 | Finance-confirmed draft remove cancels task / releases once | SVC-017 + SVC-007 | C05 | Done | `test_draft_remove_cancels_awaiting_task`; owned RSV release in `cancel_awaiting_or_release_owned` |
| PLN-AC-025 | Propose Active removal; Approved stays live; Demand not eligible | SVC-017 | C03 | Done | `test_active_propose_does_not_restore_eligibility_until_approve`; UI-09 overflow → 05A for eligible Active; omit Propose when handoff (`planning-plan-approved.spec.ts`) |
| PLN-AC-026 | Successor approve applies removal; new handoff blocks | SVC-011 + SVC-017 | C05 | Done | `test_active_propose_does_not_restore_eligibility_until_approve` (approve → Removed + Demand eligible) + `test_concurrent_handoff_blocks_successor_approval` |
| PLN-AC-027 | Tender/downstream: no action + reject; combined whole only | SVC-017 | C03 | Done | `test_active_with_handoff_rejected` + `test_combined_item_removed_as_whole`; UI-09 omit Propose (`planning-plan-approved.spec.ts` handoff + Viewer cases) |

---

## 7. NFR / quality

| ID | Work item | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-NFR-001 | Server-side scope on every read/mutation | C01 | Done | `test_moh_planner_cannot_access_county_scope`; `test_county_planner_cannot_mutate_moh_plan`; `test_county_planner_cannot_read_moh_builder_review_or_update`; `test_county_planner_cannot_publish_or_handoff_moh_plan`; `test_planning_permissions_matrix` 6/6; workspace soft-filter `test_planning_workspace_api` (no `PLN_SCOPE_DENIED` on list load) |
| PLN-NFR-002 | Atomic Finance / approve / handoff + idempotent retry | C05–C06 | Done | `test_request_finance_creates_awaiting_idempotently`; `test_confirm_reserves_and_retry_is_idempotent`; `test_happy_path_effective_once`; handoff second call `idempotent` in `test_creates_immutable_snapshot_and_blocks_propose_removal`; `test_publish_keeps_plan_approved` retry `idempotent`; `test_idempotent_retry_no_second_audit`; SCN `test_second_run_idempotent`; seed `test_idempotent_second_run` |
| PLN-NFR-003 | Concurrency / stale version protection | C05 | Done | `test_09_stale_version_protection`; `test_stale_concurrency_token_rejected` (remove); `test_stale_after_amount_change`; `test_save_plan_update_stale_token_rejected`; `test_stale_concurrency_token_rejected` (decision) |
| PLN-NFR-004 | a11y: labels, keyboard, focus, error association | **Each** UI-01…10/07A re-impl | Done | `planning-a11y.spec.ts` 4/4 (UI-01 labels/keyboard/focus; UI-02/06/08 `aria-invalid` + `aria-describedby`); `ktFormErrors` associates error slots; `make ui-planning-a11y-gate`. Not WCAG 2.1 AA / axe-core |
| PLN-NFR-005 | No Message dialog for field validation | UIC-002 | Done | UI-02/04/05A/07/07A/08 Playwright: empty required field → inline `ktFormErrors`; no Message dialog |

---

## 8. Deferred (Out of scope for this tracker)

| Item | Source |
|---|---|
| Annual departmental-plan batch certification | CMOM §5.4 / Correction Pack §13 |
| Cross-OU aggregation | REQ / CMOM |
| Targeted HoD reapproval **inside** Planning | REQ §8.3 — use Demand amendment instead |
| Contribution replacement of any kind | Explicitly banned |
| PVO rules engine / advanced dashboards | Correction Pack §13 |
| Live reservation→commitment convert before Tender/Contract | Correction Pack §13 |

---

## Cursor gate map

| Cursor Prompt | Tracker coverage | Exit (UI = **all** assigned screens fully re-ported) |
|---|---|---|
| 01 | PLN-GATE-C01, PERM-*, AC-001/021 | Scope + task surfaces correct |
| 02 | PLN-GATE-C02, REM-* | Contribution/treatment absent |
| 03 | C03, **UI-01 + 02 + 03 + 04 + 05**, SVC-001…004, AC-002/014…016 | **All five** formation-journey screens live as Stitch v1.9 ports |
| 04 | C04, **UI-06**, SVC-005, AC-003…005 | Editor **fully** re-implemented; field register only |
| 05 | C05, **UI-07 + 07A + 08**, SVC-007…011, AC-006…011/017/022 | Finance + HoP canvases **fully** re-implemented |
| 06 | C06, **UI-09 + 10**, SVC-012…015, AC-012…013/018…019 | Approved + draft-update canvases **fully** re-implemented |
| 07 | C07, SEED-*, REM-009, AC-020, SVC-016 | Seed + full regression; **UI-01…10/07A all Done** |

---

## Implementation order (all screens)

Domain gates C01–C02 are Done. Remaining work **must** re-implement **every** Stitch screen — not a subset.

1. **C03 — PLN-UI-01, 02, 03, 04, 05** — Full literal ports for workspace, register, empty builder, add-Demand/formation dialog, populated builder (plus SVC-001…004).  
2. **C04 — PLN-UI-06** — Done (literal Stitch v1.9 editor + SVC-005 field register).  
3. **C05 — PLN-UI-07, 07A, 08** — Done (Finance drawers + HoP review canvas; SVC-007…011; Finance submit/approve gates).  
4. **C06 — PLN-UI-09, 10** — Done (approved canvas + draft-update overview; SVC-012…015 + `get_plan_update` / `save_plan_update`).  
5. **C07** — Done (Demo v2.7 seed + SCN-ADD live services + AC-013/020). NFR-004 a11y remains open.

**Anti-pattern (forbidden):** treating C03 as “UI-04 multi-select only”, C05 as “wire Finance strip into old UI-08”, or skipping UI-01/02/03/09/10 because “fixtures already exist”.

Do not mark any UI Done without literal Stitch match + Playwright + chrome where registered.

---

## PLN-GATE-C07 close-out (Prompt 07)

**Authority:** CMOM v1.1 → REQ v1.9 → Demo v2.7 → Cursor Prompt 07. Tracker “v2.6” wording is superseded.

**Seed / SCN**
- Base `KENTENDER_MVP_V1`: Approved V1 + Active `PPI-MOH-2027-021` @ KES 455m; `RSV-MOH-0001` after Plan Item; no 022 / no contribution.
- `SCN-PLN-ADD-001` live services: Demand 019 corrected 80m Planning Ready **without reservation**; `add_demand_to_plan` → Draft V2 535m; `confirm_plan_item_funding` → exactly one `RSV-MOH-0002`; `approve_plan_version` supersedes V1. `TND-MOH-2027-008` stay-up unchanged. No TM2 Tender. Demands `approve_and_reserve` not called for 019.
- Stop points: `stop_before_finance` (REMOVE / FUND-SHORT / AC-013); `stop_before_approve` (after Finance); default = approve V2.
- Double-run: no duplicate plan/item/RSV; 455 / 535 / 80 arithmetic.

**PLN-SVC-016 capability → public service (one name; no aliases)**

| Capability | Public service | Primary test |
|---|---|---|
| Workspace projection | `get_planning_workspace` | `test_planning_workspace_api` |
| Register annual Plan | `create_procurement_plan` | `test_planning_register_api` |
| List eligible Demands | `list_eligible_demands` | `test_list_eligible_demands` |
| Add Demand(s) + formation | `add_demand_to_plan` | `test_add_demand_to_plan_gate04` |
| Update Plan Item | `update_plan_item` | `test_update_plan_item` |
| Validate Plan | `validate_plan` | `test_validate_plan` |
| Request / confirm / return Finance | `request_plan_item_finance` / `confirm_plan_item_funding` / `return_plan_item_from_finance` | `test_plan_item_finance` |
| Submit for review | `submit_plan_for_review` | `test_submit_plan_for_review` |
| Record professional decision | `record_plan_decision` | `test_record_plan_decision` |
| Approve Plan Version | `approve_plan_version` | `test_approve_plan_version_gate05` |
| Open/reuse Draft successor | `open_or_create_plan_revision` | `test_get_plan_implementation` |
| Publish / export Approved | `publish_approved_plan` | `test_publish_approved_plan` |
| Tender handoff snapshot | `create_planning_handoff_snapshot` | `test_create_planning_handoff_snapshot` |
| Implementation projection | `get_plan_implementation` | `test_get_plan_implementation` |
| Draft update overview / save | `get_plan_update` / `save_plan_update` | `test_get_plan_update` |
| Remove Plan Item | `remove_plan_item_from_plan` | `test_remove_plan_item` |

**Deferred:** none for NFR-004 (Prompt 07 item 13 closed). SVC-001/002/006 remain Keep/Correct (revalidate, not open tickets). Demands `approve_and_reserve` still reserves (Demands leftover; not rewritten).

**Commands:** `bench --site kentender.midas.com run-tests --module kentender_procurement.procurement_planning.tests.test_scn_pln_add_001` (7/7); `test_planning_mvp_seed_contract`; `test_scn_pln_remove_001`; `test_scn_pln_fund_short_001`; `test_planning_rem009_absent`; `make ui-planning-mvp1-gate`.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-13 | **Tracker header cleanup** — C00–C07 + NFR-001–005 Done; drop stale C07-remaining / UI-07A Partial / AC-016 Partial / NFR-004 deferred wording from live rows. |
| 2026-08-13 | **PLN-NFR-001 / 002 / 003 / 004 Done** — county-vs-MOH read/publish/handoff isolation (`test_planning_cross_entity_isolation` 5/5) + permissions matrix 6/6; Finance/approve/handoff/publish/remove/SCN/seed idempotent retries cited; stale tokens on save update + decision; `planning-a11y.spec.ts` 4/4 + `ktFormErrors` `aria-invalid`/`aria-describedby`; `make ui-planning-a11y-gate`. **NFR-005 unchanged.** Not WCAG AA. |
| 2026-08-13 | **PLN-AC-001 / 011 / 016 / 018 / 021 / 026 / 027 + PERM-005 Done** — mixed-OU Combine reject + UI disable; Demand strategy/PVC pass-through (ignore Planning writes); PE/immutability/neutral/removal evidence; Reviewer cannot Approve. **NFR-004 remains Not started.** |
| 2026-08-13 | **PLN-GATE-C07 / SEED-001/002/004/005 / REM-009 / SVC-016 / AC-013 / AC-020 Done** — Demo v2.7 canonical seed; SCN-ADD live services (no Demand-stage RSV-0002); Draft 535m while V1 + `TND-MOH-2027-008` live; Finance then RSV-0002; double-run idempotent; `validate.py` SCN-ADD mode; USA personas; REM-009 grep; `make ui-planning-mvp1-gate`. **NFR-004 remains Not started.** |
| 2026-08-13 | **PLN-UIC-001 / UIC-002 / UIC-003 / NFR-005 Done** — `make ui-stitch-desk-chrome-gate` green (26 Playwright surfaces); UI-04 Combine without reason shows inline `formation_reason` (no Message); layout guard asserts UI-01…10 + 05A/07A error slots and approved/update page assets. **SEED-002 / AC-013 / AC-020 / C07 remain open.** |
| 2026-08-13 | **PLN-UI-10 / PLN-GATE-C06 Done** — literal Stitch Draft Plan update (`procurement-plan-update`); `get_plan_update` / `save_plan_update`; successor submit requires planner reason; Added labels; UI-09 Continue/View → UI-10; builder successor redirects here; `test_get_plan_update` 6/6; `test_submit_plan_for_review` 4/4; layout guard `test_plan_update_fixture_markers`; Playwright `planning-plan-update.spec.ts` 3/3 + UI-09 Continue → `/procurement-plan-update`. **SEED-002 / AC-013 / AC-020 / C07 remain open** (canonical 535m arithmetic). |
| 2026-08-13 | **PLN-UI-09 / PLN-SVC-012…015 / PLN-AC-012 / AC-019 / AC-025 Done** — literal Stitch Approved Plan (`procurement-plan-approved`); quiet successor + publish/export + handoff snapshot + implementation DTO; workspace Approved → UI-09; Add → UI-04; Propose → 05A; Continue → builder until UI-10; `test_get_plan_implementation` 4/4; `test_publish_approved_plan` 2/2; `test_create_planning_handoff_snapshot` 2/2; layout guard; Playwright `planning-plan-approved.spec.ts` 4/4 + `assertStitchDeskChrome`. **UI-10 and GATE-C06 remain open.** |
| 2026-08-13 | **PLN-UI-08 / PLN-SVC-009…011 / PLN-AC-009 / AC-010 / AC-017 / PLN-GATE-C05 Done** — literal Stitch HoP review (`Review and approve procurement plan`, Finance Confirmed strip + Finance column, issues first, gavel rail, Return to planner); submit/approve require current Finance Confirmed; coverage omit-if-empty; `test_submit_plan_for_review` 4/4; `test_record_plan_decision` 4/4; `test_approve_plan_version_gate05` 5/5; layout guard; Playwright `planning-plan-review.spec.ts` 3/3 + `assertStitchDeskChrome`. UI-09/10 remain C06. |
| 2026-08-13 | **PLN-UI-05A / PLN-SVC-017 Done** — Plan Item removal (REQ v1.9 / Stitch v2.0 / Cursor v1.8 / Demo v2.7): `remove_plan_item_from_plan` (no hard-delete; server-derived mode); UI-05 overflow + 05A Draft/Finance/Active overlay; `ktFormErrors` reason; SCN-PLN-REMOVE-001 3/3; `test_remove_plan_item` 12/12; layout + Playwright 05A; `make ui-planning-builder-gate` green. UI-09 Propose entry remains C06. |
| 2026-08-12 | **PLN-UI-06 Done** / **PLN-GATE-C04 Done** — literal Stitch v1.9 Plan Item editor (Procurement approach, Indicative lotting, Planned schedule, Approved source, Request Finance completeness; Desk crumbs only); SVC-005 + AC-003/004/005; layout guard + `planning-plan-item-editor.spec.ts` + `make ui-planning-builder-gate` green; visual vs `PLN-UI-06.html`; Finance task / UI-07 remains C05 |
| 2026-08-12 | **Planning canvas chrome** — dropped in-canvas Stitch breadcrumbs (Desk `Home > …` owns the trail); tightened canvas top padding to 0.5rem on all Planning surfaces; layout guard + `planning-builder.spec.ts` + `make ui-planning-builder-gate` green |
| 2026-08-12 | **PLN-UI-05 Done** / **PLN-GATE-C03 Done** — literal Stitch v1.9 populated builder (breadcrumb + dot lifecycle, issue strip, 8-col table with Finance/`Not requested`, filler row, Run validation enabled / Submit disabled); empty UI-03 preserved; layout guard + `planning-builder.spec.ts` + `make ui-planning-builder-gate` green; visual vs `PLN-UI-05.html`; Finance confirm remains C05 |
| 2026-08-12 | **PLN-UI-04 Done** — corrected Stitch 7-col table (drop absolute selection td); literal dialog + multi-select Separate\|Combine; `proposed_funding` on list_eligible; layout guard + Playwright + `make ui-planning-builder-gate` green; C03 still In progress (UI-05) |
| 2026-08-12 | **PLN-UI-03 summary strip revised** — standardized compact horizontal strip (Total Planned Value / Validation Status / `h-8` dividers; drop icon tiles); bind plain `N of M` + Stitch validation pill; layout guard + Playwright + `make ui-planning-workspace-gate` green |
| 2026-08-12 | **PLN-UI-03 Done** — literal Stitch v1.9 empty builder (Open Plan meta, Finance Confirmed summary, search-first filters, assignment_late empty, sticky footer); C03 still In progress (UI-04…05) |
| 2026-08-12 | **PLN-UI-02 Done** — literal Stitch v1.9 register port (1./2. sections, input-glow, calendar period, sticky Create/`add_task`); no Budget field; layout guard + `planning-register.spec.ts`; `make ui-planning-workspace-gate` green; C03 still In progress (UI-03…05) |
| 2026-08-12 | **PLN-UI-01 Done** — literal Stitch v1.9 workspace port (scope helper, plan strip, work select+search, table footer/`attachPagination`); C03 In progress (UI-02…05 remain) |
| 2026-08-12 | **UI scope correction** — every PLN-UI-01…10 + 07A is **Re-implement required** (full Stitch v1.9 literal port). Tracker no longer implies selective re-ports of a few screens; C03–C06 exit = all assigned canvases Done |
| 2026-08-11 | **PLN-GATE-C02 Done** — Departmental Submission + contribution UI/API/capability removed; statutory schema purged; preference editor writes stopped; submit = Ready-only until C05 Finance; REM-001…008 Done |
| 2026-08-11 | Tracker 2.0 created for REQ 1.8 / Stitch 1.9 / Cursor 1.7 / CMOM 1.1; contribution-era tracker retired |
