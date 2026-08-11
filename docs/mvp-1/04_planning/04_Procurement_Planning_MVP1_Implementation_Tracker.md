# Procurement Planning MVP-1 Implementation Tracker

**Document ID:** PLANNING-MVP1-IMPL-TRACKER-2.0  
**Status:** Active — streamlined correction baseline; implementation not started under v1.8  
**Date:** 11 August 2026  
**Supersedes:** [retired/04_Procurement_Planning_MVP1_Implementation_Tracker.md](retired/04_Procurement_Planning_MVP1_Implementation_Tracker.md) (REQ ≤1.5 / contribution-era Gate 05)

## Goal

Realign Procurement Planning to the **approved streamlined operating model** so that:

> **Approved Demand → Planner completes Plan Item → Finance confirms funding → Head of Procurement approves Plan Version → Tender take-up**

**Done looks like:** contribution / generic treatment / Demand-stage Finance duplicate / silent PE fallbacks **gone**; PLN-UI-01…10 (+07A) are **literal Stitch ports** of `ui_design/*.html` with live services; canonical seed v2.6 arithmetic green twice; Cursor pack v1.7 DoD + AC matrix evidenced by automated tests — not Administrator smoke or title-only guards.

---

## Documentation read gate (mandatory before any ticket)

| Doc | Role |
|---|---|
| [KenTender_MVP_Cross_Module_Operating_Model_v1.1.md](../00_common/KenTender_MVP_Cross_Module_Operating_Model_v1.1.md) | **Controlling** business model (PO-approved) |
| [Procurement_Planning_MVP1_Requirements_v1.8.md](Procurement_Planning_MVP1_Requirements_v1.8.md) | Behaviour / FR / AC / removals |
| [Procurement_Planning_MVP1_Stitch_Prompts_v1.9.md](Procurement_Planning_MVP1_Stitch_Prompts_v1.9.md) | Screen contracts |
| [ui_design/](ui_design/) | **Approved Stitch HTML** — UI source of truth (`PLN-UI-01`…`10`, `PLN-UI-07A`) |
| [Procurement_Planning_MVP1_Cursor_Implementation_Pack_v1.7.md](Procurement_Planning_MVP1_Cursor_Implementation_Pack_v1.7.md) | Ordered Cursor Prompts 01–07 |
| [KenTender_Cursor_Direct_MVP_Correction_Pack_v1.0.md](KenTender_Cursor_Direct_MVP_Correction_Pack_v1.0.md) | Cross-module correction mandate |
| [KenTender_MVP_Canonical_Demo_Data_Contract_v2.6.md](../00_common/KenTender_MVP_Canonical_Demo_Data_Contract_v2.6.md) | Seed identities + SCN-PLN-ADD-001 / FUND-SHORT |
| [KenTender_Cross_Module_Authorization_Surface_Design_and_Cursor_Pack_v1.0.md](../00_common/KenTender_Cross_Module_Authorization_Surface_Design_and_Cursor_Pack_v1.0.md) | Neutral vs task surfaces |
| [00_KenTender_Procuring_Entity_and_Organisation_Scope_Model.md](../00_common/00_KenTender_Procuring_Entity_and_Organisation_Scope_Model.md) | PE/OU scope |
| Disposition audit `99_audit/00`–`09` | Repo locations for Keep / Correct / Remove |

**Precedence:** CMOM v1.1 → REQ v1.8 → Stitch HTML + prompts v1.9 → Cursor pack v1.7 → Demo contract v2.6 → Auth surface pack → Org scope → repo conventions that do not conflict.

**Historical packs (≤ REQ 1.5 / Stitch 1.6 / Cursor 1.4) and contribution-era GATE_05 are superseded** — do not treat their Done rows as current Done.

---

## How to use this tracker

1. Update only **Status** and **Evidence**. Do not delete rows — use **Out of scope** / **Blocked**.
2. **UI Done** requires **all** of § UI rigor below — gate-green alone is insufficient.
3. Domain/service **Done** only with named automated tests green on `kentender.midas.com`.
4. Do not start a UI row before its service dependencies are Done or Partial with an explicit note.
5. Prefer clean teardown/reseed over compatibility shims (Correction Pack §1). No dual-write; no renamed contribution.

### Status vocabulary

| Status | Meaning |
|---|---|
| Not started | No work under this baseline |
| In progress | Active coding |
| Partial | First pass; DoD incomplete |
| Done | Evidence filled; tests green; UI visual Stitch match where applicable |
| Blocked | Cannot proceed; note blocker |
| Out of scope | Explicitly deferred (see § Deferred) |
| Remove-pending | Exists in repo; must be deleted under this baseline |
| Keep | Retained foundation; no correction ticket unless noted |

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

**Construction order for each screen:** open approved HTML → literal-port `<main>` (+ overlays) → `kt-stitch-canvas` / testids / bind hooks only → chrome registry → live-bind → visual check → Playwright.

**PLN-UI-07 renumbering:** Contribution drawer is **removed**. **PLN-UI-07 / 07A** are Finance confirmation (sufficient / shortfall). Do not revive contribution under a new label.

---

## Current repo baseline (from disposition audit)

| Area | State vs this baseline |
|---|---|
| Plan / Version / Item / Allocation / Plan Decision / validate / approve (professional) | **Keep** foundations; Correct gates/readiness |
| Departmental Submission + `submit_departmental_contribution` + old UI-07 drawer + contrib submit gate | **Remove-pending** |
| Demand-stage BO confirmation as Planning prerequisite | **Correct** — Finance after Plan Item only |
| PLN-UI-01…06 / 08 fixtures | Exist; **Correct** to Stitch v1.9 (esp. UI-04 multi-select formation; UI-08 Finance strip; strip contrib) |
| PLN-UI-07 / 07A Finance | **Not started** (HTML exists; product not wired) |
| PLN-UI-09 / 10 | **Not started** / Partial HTML only |
| PE-MOH / Admin inflation (Budget/Home/Strategy) | Cross-module Correct (Correction Pack A) — track under shared + Planning consumers |
| Canonical seed contribution/treatment rows | **Remove-pending**; rebuild to v2.6 |

---

## Correction gates (Cursor pack v1.7)

| ID | Gate | Cursor Prompt | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-GATE-C00 | Baseline lock | — | Docs above accepted | Done | This tracker + CMOM 1.1 / REQ 1.8 / Stitch 1.9 / Cursor 1.7 |
| PLN-GATE-C01 | Scope + task authority | Prompt 01 | C00 | Done | `test_planning_task_capability` (7) + matrix/PE + Playwright `planning-task-route-denial.spec.ts` (5); `make ui-planning-scope-auth-gate` |
| PLN-GATE-C02 | Remove superseded structures | Prompt 02 | C01 | Not started | |
| PLN-GATE-C03 | Workspace, register, formation | Prompt 03 | C02 | Not started | |
| PLN-GATE-C04 | Focused Plan Item editor | Prompt 04 | C03 | Not started | |
| PLN-GATE-C05 | Finance + professional approval | Prompt 05 | C04 | Not started | |
| PLN-GATE-C06 | Approved Plan, successor, publish, handoff | Prompt 06 | C05 | Not started | |
| PLN-GATE-C07 | Canonical seed + regression close-out | Prompt 07 | C06 | Not started | |

**Makefile targets (to add/rename as work lands):** replace `ui-planning-contribution-gate` with Finance gate; keep/extend `ui-planning-approval-gate`, workspace/builder gates; add `ui-planning-finance-gate`, `ui-planning-revision-gate`, final `ui-planning-mvp1-gate`.

---

## 1. Removals (`PLN-REM-*`)

| ID | Work item | Exact targets (repo) | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-REM-001 | Departmental Submission DocType + writers | `doctype/departmental_submission/`; seeds; clear helpers | C01 | Remove-pending | |
| PLN-REM-002 | Contribution services/API | `submit_departmental_contribution`, `get_departmental_contribution`, whitelist | C01 | Remove-pending | |
| PLN-REM-003 | Contribution UI + gate | `contribution_drawer.js`, builder bind, `prepare_planning_gate05_ui` contrib, `ui-planning-contribution-gate`, Playwright contrib | C02 | Remove-pending | |
| PLN-REM-004 | Contribution readiness on submit | `submit_plan_for_review` contribution prerequisite + copy | C02 | Remove-pending | |
| PLN-REM-005 | Contributor contribution capability | Planning Contributor contrib asserts / USA where only for contrib | C02 | Remove-pending | |
| PLN-REM-006 | Generic Plan Item treatment/statutory fields | Retired `statutory_*` / `planned_treatment_value` / `value_treatment_note` — finish schema purge | C02 | Remove-pending | |
| PLN-REM-007 | Item-level preference scheme editors (superseded) | Writable preference/reservation scheme / target-group / planned-value if present | C02 | Remove-pending | |
| PLN-REM-008 | Tests that only prove contribution | Replace with Finance/professional coverage; do not delete coverage volume | C02 | Remove-pending | |
| PLN-REM-009 | Active references search | Grep schema/services/UI/seeds/tests for Submission/contribution/OU_SIGNOFF | C07 | Not started | |

---

## 2. Shared / permissions (`PLN-PERM-*`)

| ID | Work item | Notes | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-PERM-001 | Zero / one / multi PE deliberate selection | PLN-FR-002…004; no PE-MOH invent | C01 | Done | `test_resolve_pe_for_create_zero_one_multi` + `test_planning_pe_scope_selection` |
| PLN-PERM-002 | Admin alone no operational authority | PLN-FR-084 | C01 | Done | `test_admin_without_usa_*` + matrix Admin deny; USA-only `actor_planning_roles` |
| PLN-PERM-003 | Record vs task vs mutation projection | Auth pack; PLN-FR-080…083 | C01 | Done | `get_plan_review` surface task/neutral; omit CTAs in `bindPlanningReview`; contrib task capability |
| PLN-PERM-004 | Finance task capability | Budget Officer only; deny Requester/Planner/HoD/Viewer/Admin-without-task | C05 | Partial | C01 scaffold `assert_can_open_finance_task` / `assert_can_confirm_plan_funding` + planner deny; UI-07 wiring remains C05 |
| PLN-PERM-005 | Professional approval capability | Head of Procurement / configured authority | C05 | Partial | Gate 05 roles exist; C01 harden route denial for Reviewer/Approver task surface |
| PLN-PERM-006 | Direct-route + API denial tests | Playwright + service negatives | C01, C05 | Done (Planning-scoped C01) | `planning-task-route-denial.spec.ts`; Finance route denial remains C05 |

---

## 3. Domain / services (`PLN-SVC-*`)

| ID | Work item | Capability (REQ §12.1) | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-SVC-001 | Workspace projection | Scoped workspace | C03 | Keep / Correct | Existing `get_planning_workspace` — revalidate |
| PLN-SVC-002 | Register annual Plan | create/register | C03 | Keep | |
| PLN-SVC-003 | List eligible Demands | Eligibility | C03 | Keep / Correct | Multi-select support for UI-04 |
| PLN-SVC-004 | Add Demand(s) + formation | Atomic one/multi Separate|Combine | C03 | Partial | Today one-Demand + aggregate path — align to UI-04 multi-select formation in one confirm |
| PLN-SVC-005 | Update Plan Item | Save Draft Item Version; no source reselect; admitted fields only | C04 | Partial | Strip banned fields; field register REQ §9.4 |
| PLN-SVC-006 | Validate Plan | Issue-led Ready | C04 | Keep / Correct | Finance confirmation as readiness input |
| PLN-SVC-007 | Request / record Finance confirm|return | PLN-FR-040…049; reuse Demand Funding Allocation + Budget reserve | C05 | Not started | |
| PLN-SVC-008 | Finance shortfall behaviour | No confirm/partial/override; same-task recovery | C05 | Not started | |
| PLN-SVC-009 | Submit for review | Ready + **current Finance** for all items; **no** contribution | C05 | Partial | Exists; rewire gates |
| PLN-SVC-010 | Record professional decision | Return / Approve trail | C05 | Keep / Correct | |
| PLN-SVC-011 | Approve Plan Version | Atomic lock / Effective / supersede | C05 | Keep / Correct | Require Finance confirmed |
| PLN-SVC-012 | Open/reuse/cancel Draft successor | Quiet successor | C06 | Keep | |
| PLN-SVC-013 | Publish / export Approved | Publication evidence | C06 | Not started | |
| PLN-SVC-014 | Tender handoff snapshot | Immutable handoff | C06 | Partial | Schema exists; complete take-up |
| PLN-SVC-015 | Implementation / audit projections | Derived downstream | C06 | Not started | |
| PLN-SVC-016 | Capability → service map | Cursor §5 naming rule — one public name per behaviour | C07 | Not started | |

---

## 4. UI screens (`PLN-UI-*` / `PLN-UIC-*`)

Stitch source: `ui_design/PLN-UI-XX.html` (07A: `PLN-UI-07A.html`).

| ID | Screen | Stitch HTML | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-UI-01 | Planning workspace | `PLN-UI-01.html` | SVC-001, PERM-001 | Partial | Re-verify vs Stitch v1.9; chrome |
| PLN-UI-02 | Create annual Plan | `PLN-UI-02.html` | SVC-002 | Partial | Inline errors; no free-text Budget |
| PLN-UI-03 | Empty Draft builder | `PLN-UI-03.html` | UI-01 | Partial | |
| PLN-UI-04 | Add approved Demands | `PLN-UI-04.html` | SVC-003/004 | Partial | **Re-port:** multi-select + formation progressive disclosure |
| PLN-UI-05 | Draft with Plan Item | `PLN-UI-05.html` | UI-04, SVC-006 | Partial | Finance confirmed 0 of N; no contribution CTA |
| PLN-UI-06 | Plan Item editor | `PLN-UI-06.html` | SVC-005 | Partial | Field register only; Request Finance entry |
| PLN-UI-07 | Finance confirm — sufficient | `PLN-UI-07.html` | SVC-007, PERM-004 | Not started | Literal drawer port |
| PLN-UI-07A | Finance confirm — shortfall | `PLN-UI-07A.html` | SVC-008 | Not started | Same task; no Confirm button |
| PLN-UI-08 | HoP review / approve | `PLN-UI-08.html` | SVC-009…011 | Partial | Re-port: Finance strip; derived coverage; no contrib |
| PLN-UI-09 | Approved Plan + implementation | `PLN-UI-09.html` | SVC-012…015 | Not started | |
| PLN-UI-10 | Draft update overview | `PLN-UI-10.html` | SVC-012, UI-04 | Not started | |
| PLN-UIC-001 | Stitch Desk chrome for all Planning routes | Registry + gates | Each UI | Partial | Add Finance routes; drop contrib surface |
| PLN-UIC-002 | Inline form errors (return/confirm notes, formation reason) | ktFormErrors | UI-02/04/07/08 | Partial | Extend to Finance return reason |
| PLN-UIC-003 | Layout / Stitch contract guards | `test_planning_ui_stitch_layout_guard` | Each UI | Partial | Update markers for v1.9; forbid contribution markers |

---

## 5. Seed (`PLN-SEED-*`)

| ID | Work item | Notes | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-SEED-001 | Rebuild Planning seed to Demo Contract v2.6 | 455m item; Finance **after** Plan Item; no contribution/treatment | C02, C05 | Not started | |
| PLN-SEED-002 | SCN-PLN-ADD-001 | V1 operational; V2 535m; RSV-MOH-0002 after Finance | C06 | Partial | Align to post-Planning Finance |
| PLN-SEED-003 | SCN-PLN-FUND-SHORT-001 | Optional shortfall; no partial reserve | C05 | Not started | |
| PLN-SEED-004 | Personas USA | Requester, HoD, Planner, BO, HoP, Viewer — explicit PE/OU | C01 | Partial | |
| PLN-SEED-005 | Idempotent double-run + Kisumu isolation | validate.py | C07 | Not started | |

---

## 6. Acceptance criteria (`PLN-AC-*`)

Map to REQ v1.8 §16. Mark Done only with test IDs.

| ID | Criterion (summary) | Primary proof | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-AC-001 | Multi-PE deliberate; zero blocks; one visible | Scope tests | PERM-001 | Partial | |
| PLN-AC-002 | One Demand → one Plan Item; formation hidden | SVC-004 + UI-04 | C03 | Partial | |
| PLN-AC-003 | UI-06 no Demand reselect | UI-06 + layout | C04 | Partial | |
| PLN-AC-004 | Editor field register only | UI-06 + REM | C04 | Not started | |
| PLN-AC-005 | Cannot edit HoD facts in Planning | SVC-005 negatives | C04 | Not started | |
| PLN-AC-006 | Planning Ready ≠ Finance approval | Lifecycle | C05 | Not started | |
| PLN-AC-007 | BO Confirm / pending shortfall / Return; unauth deny | UI-07/07A | C05 | Not started | |
| PLN-AC-008 | Confirm reserves atomically; becomes Stale | SVC-007 | C05 | Not started | |
| PLN-AC-009 | Submit needs Finance; never contribution | SVC-009 | C05 | Not started | |
| PLN-AC-010 | HoP Approve/Return; unauth deny task form | UI-08 | C05 | Partial | |
| PLN-AC-011 | Approved immutable | SVC-011 | C05 | Keep | |
| PLN-AC-012 | Add to Approved → quiet Draft successor | SVC-012 | C06 | Keep | |
| PLN-AC-013 | V1 + Tender operational during V2 Draft | SCN-ADD | C06 | Partial | |
| PLN-AC-014 | Multi same-OU Combine + reason + lineage | UI-04 | C03 | Not started | |
| PLN-AC-015 | Multi Separate → real Items; no cosmetic Keep separate | UI-04 | C03 | Partial | |
| PLN-AC-016 | Cross-OU Combine rejected | SVC-004 | C03 | Not started | |
| PLN-AC-017 | Derived coverage omit-if-empty | UI-08 | C05 | Not started | |
| PLN-AC-018 | Strategy SVC pass-through unchanged | Handoff | C06 | Partial | |
| PLN-AC-019 | Tender take-up Active only + snapshot | SVC-014 | C06 | Not started | |
| PLN-AC-020 | Seed twice + arithmetic | SEED-005 | C07 | Not started | |
| PLN-AC-021 | Neutral view ≠ task forms | PERM-003/006 | C01 | Not started | |
| PLN-AC-022 | Shortfall exact deficit; no override; same-task recovery | UI-07A | C05 | Not started | |

---

## 7. NFR / quality

| ID | Work item | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-NFR-001 | Server-side scope on every read/mutation | C01 | Partial | |
| PLN-NFR-002 | Atomic Finance / approve / handoff + idempotent retry | C05–C06 | Partial | |
| PLN-NFR-003 | Concurrency / stale version protection | C05 | Partial | |
| PLN-NFR-004 | a11y: labels, keyboard, focus, error association | Each UI | Not started | |
| PLN-NFR-005 | No Message dialog for field validation | UIC-002 | Partial | |

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

| Cursor Prompt | Tracker coverage | Exit |
|---|---|---|
| 01 | PLN-GATE-C01, PERM-*, AC-001/021 | Scope + task surfaces correct |
| 02 | PLN-GATE-C02, REM-* | Contribution/treatment absent |
| 03 | C03, UI-01…05, SVC-001…004, AC-002/014…016 | Formation journey live |
| 04 | C04, UI-06, SVC-005, AC-003…005 | Editor field register only |
| 05 | C05, UI-07/07A/08, SVC-007…011, AC-006…011/017/022 | Finance then HoP |
| 06 | C06, UI-09/10, SVC-012…015, AC-012…013/018…019 | Successor + handoff |
| 07 | C07, SEED-*, REM-009, AC-020, SVC-016 | Seed + full regression + completion report |

---

## First implementation slice (recommended start)

1. **PLN-GATE-C01** — Planning scope + task/action projection + negative route tests.  
2. **PLN-GATE-C02 / REM-001…008** — Tear out contribution end-to-end (services, UI, gates, tests, seed clears).  
3. **PLN-UI-04 re-port** — Multi-select + formation (literal HTML).  
4. **PLN-SVC-007 + UI-07/07A** — Finance after Plan Item.  
5. **Rewire submit + UI-08** — Finance-confirmed readiness; Stitch v1.9 review canvas.

Do not mark any UI Done without literal Stitch match + Playwright + chrome where registered.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-11 | Tracker 2.0 created for REQ 1.8 / Stitch 1.9 / Cursor 1.7 / CMOM 1.1; contribution-era tracker retired |
