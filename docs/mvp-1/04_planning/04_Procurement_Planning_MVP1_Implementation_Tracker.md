# Procurement Planning MVP-1 Implementation Tracker

**Document ID:** PLANNING-MVP1-IMPL-TRACKER-2.0  
**Status:** Active — correction baseline; C01–C02 Done; **all PLN-UI-01…10 + 07A require full Stitch v1.9 re-implementation** (C03–C06)  
**Date:** 12 August 2026  
**Supersedes:** [retired/04_Procurement_Planning_MVP1_Implementation_Tracker.md](retired/04_Procurement_Planning_MVP1_Implementation_Tracker.md) (REQ ≤1.5 / contribution-era Gate 05)

## Goal

Realign Procurement Planning to the **approved streamlined operating model** so that:

> **Approved Demand → Planner completes Plan Item → Finance confirms funding → Head of Procurement approves Plan Version → Tender take-up**

**Done looks like:** contribution / generic treatment / Demand-stage Finance duplicate / silent PE fallbacks **gone**; **every** Planning screen — **PLN-UI-01…10 and PLN-UI-07A** — is a **full literal Stitch re-implementation** of the approved `ui_design/*.html` (v1.9), not a touch-up of the contribution-era fixtures; live services bound; canonical seed v2.6 arithmetic green twice; Cursor pack v1.7 DoD + AC matrix evidenced by automated tests — not Administrator smoke or title-only guards.

**UI scope lock (non-negotiable):** Stitch v1.9 has **substantial** composition/workflow changes across the whole journey. Tracker work must **re-implement all screens**. Selective “fix UI-04 / UI-08 only” or “re-verify existing fixtures” is **wrong** and is not UI Done for any skipped screen.

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
| PLN-UI-01…10 + 07A fixtures / Desk mounts | **UI-01…03 Done** (Stitch v1.9). UI-04…10 + 07A remain **Re-implement required**. |
| PLN-UI-07 / 07A Finance | **Re-implement required** (new Finance task surfaces; HTML in `ui_design/`) |
| PLN-UI-09 / 10 | **Re-implement required** (approved + draft-update canvases) |
| PE-MOH / Admin inflation (Budget/Home/Strategy) | Cross-module Correct (Correction Pack A) — track under shared + Planning consumers |
| Canonical seed contribution/treatment rows | **Removed** from active schema/UI (C02); seed rebuild to v2.6 remains C07 |

---

## Correction gates (Cursor pack v1.7)

| ID | Gate | Cursor Prompt | Depends on | Status | Evidence |
|---|---|---|---|---|---|
| PLN-GATE-C00 | Baseline lock | — | Docs above accepted | Done | This tracker + CMOM 1.1 / REQ 1.8 / Stitch 1.9 / Cursor 1.7 |
| PLN-GATE-C01 | Scope + task authority | Prompt 01 | C00 | Done | `test_planning_task_capability` (7) + matrix/PE + Playwright `planning-task-route-denial.spec.ts` (5); `make ui-planning-scope-auth-gate` |
| PLN-GATE-C02 | Remove superseded structures | Prompt 02 | C01 | Done | `test_planning_contribution_absent` (5); submit/decision/gate05 + layout forbid; migrate + patch drop DocType; `make ui-planning-approval-gate` green; builder/editor Playwright (no pref/contrib); Finance submit gate deferred C05 |
| PLN-GATE-C03 | **Full re-implement** PLN-UI-01…05 (+ formation services) | Prompt 03 | C02 | In progress | **UI-01…03 Done**; UI-04…05 outstanding |
| PLN-GATE-C04 | **Full re-implement** PLN-UI-06 Plan Item editor | Prompt 04 | C03 | Not started | Full canvas replace; field register only |
| PLN-GATE-C05 | **Full re-implement** PLN-UI-07 / 07A / 08 + Finance/professional services | Prompt 05 | C04 | Not started | New Finance surfaces + full UI-08 re-port |
| PLN-GATE-C06 | **Full re-implement** PLN-UI-09 / 10 + successor/publish/handoff | Prompt 06 | C05 | Not started | Both approved + draft-update canvases |
| PLN-GATE-C07 | Canonical seed + regression close-out | Prompt 07 | C06 | Not started | All UI-01…10/07A Done before close-out |

**Makefile targets (to add/rename as work lands):** `ui-planning-contribution-gate` removed (C02); absence covered by `test_planning_contribution_absent` inside `ui-planning-approval-gate`. Add Finance gate in C05; keep/extend workspace/builder gates; add `ui-planning-finance-gate`, `ui-planning-revision-gate`, final `ui-planning-mvp1-gate`.

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
| PLN-REM-009 | Active references search | Grep schema/services/UI/seeds/tests for Submission/contribution/OU_SIGNOFF | C07 | Not started | C02 Planning-scoped grep: active callers absent (absence tests + patch + DTO stub keys only) |

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

**Authority:** Stitch v1.9 HTML is the UI contract for **every** row below. Pre-correction fixtures may remain mounted until each gate lands; they are **not** Done evidence. Status **Re-implement required** means a full literal port is still outstanding even if Playwright smoke exists against the old canvas.

| ID | Screen | Stitch HTML | Depends on | Status | Evidence / exit |
|---|---|---|---|---|---|
| PLN-UI-01 | Planning workspace | `PLN-UI-01.html` | SVC-001, PERM-001 | Done | Literal Stitch v1.9 port; helper + plan strip + work select/search + `attachPagination`; layout guard + `planning-workspace.spec.ts`; `make ui-planning-workspace-gate` green |
| PLN-UI-02 | Create annual Plan | `PLN-UI-02.html` | SVC-002 | Done | Literal Stitch v1.9 port (numbered sections, input-glow, calendar period, sticky Create/`add_task`); no Budget field; inline errors; layout guard + `planning-register.spec.ts`; `make ui-planning-workspace-gate` green |
| PLN-UI-03 | Empty Draft builder | `PLN-UI-03.html` | UI-01 | Done | Literal Stitch empty canvas + **standardized horizontal summary strip** (Total Planned Value, Validation Status, dividers; no icon grid); layout guard + `planning-builder.spec.ts`; `make ui-planning-workspace-gate` green |
| PLN-UI-04 | Add approved Demands | `PLN-UI-04.html` | SVC-003/004 | Re-implement required | C03: full dialog — multi-select + formation progressive disclosure |
| PLN-UI-05 | Draft with Plan Item | `PLN-UI-05.html` | UI-04, SVC-006 | Re-implement required | C03: full populated builder; Finance strip when wired (C05 readiness labels OK interim) |
| PLN-UI-06 | Plan Item editor | `PLN-UI-06.html` | SVC-005 | Re-implement required | C04: full canvas; field register only; Request Finance entry |
| PLN-UI-07 | Finance confirm — sufficient | `PLN-UI-07.html` | SVC-007, PERM-004 | Re-implement required | C05: full Finance task surface (new) |
| PLN-UI-07A | Finance confirm — shortfall | `PLN-UI-07A.html` | SVC-008 | Re-implement required | C05: full shortfall surface; no Confirm button |
| PLN-UI-08 | HoP review / approve | `PLN-UI-08.html` | SVC-009…011 | Re-implement required | C05: full review canvas; Finance strip; derived coverage; no contrib |
| PLN-UI-09 | Approved Plan + implementation | `PLN-UI-09.html` | SVC-012…015 | Re-implement required | C06: full approved canvas |
| PLN-UI-10 | Draft update overview | `PLN-UI-10.html` | SVC-012, UI-04 | Re-implement required | C06: full draft-update canvas |
| PLN-UIC-001 | Stitch Desk chrome for **all** Planning routes | Registry + gates | Each UI | Re-implement required | Register every route (incl. Finance); drop contrib; gate green per surface |
| PLN-UIC-002 | Inline form errors (return/confirm notes, formation reason) | ktFormErrors | UI-02/04/07/08 | Partial | UI-02 register uses `ktFormErrors` (Playwright); extend to UI-04/07/08 on re-implement |
| PLN-UIC-003 | Layout / Stitch contract guards | `test_planning_ui_stitch_layout_guard` | Each UI | Partial | UI-01…03 v1.9 markers; remaining screens still outstanding |

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
| PLN-NFR-004 | a11y: labels, keyboard, focus, error association | **Each** UI-01…10/07A re-impl | Not started | |
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
2. **C04 — PLN-UI-06** — Full Plan Item editor re-port (SVC-005).  
3. **C05 — PLN-UI-07, 07A, 08** — Full Finance + HoP review re-ports (SVC-007…011).  
4. **C06 — PLN-UI-09, 10** — Full approved + draft-update re-ports (SVC-012…015).  
5. **C07** — Seed v2.6 + regression; close only when **all** UI rows are Done.

**Anti-pattern (forbidden):** treating C03 as “UI-04 multi-select only”, C05 as “wire Finance strip into old UI-08”, or skipping UI-01/02/03/09/10 because “fixtures already exist”.

Do not mark any UI Done without literal Stitch match + Playwright + chrome where registered.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-12 | **PLN-UI-03 summary strip revised** — standardized compact horizontal strip (Total Planned Value / Validation Status / `h-8` dividers; drop icon tiles); bind plain `N of M` + Stitch validation pill; layout guard + Playwright + `make ui-planning-workspace-gate` green |
| 2026-08-12 | **PLN-UI-03 Done** — literal Stitch v1.9 empty builder (Open Plan meta, Finance Confirmed summary, search-first filters, assignment_late empty, sticky footer); C03 still In progress (UI-04…05) |
| 2026-08-12 | **PLN-UI-02 Done** — literal Stitch v1.9 register port (1./2. sections, input-glow, calendar period, sticky Create/`add_task`); no Budget field; layout guard + `planning-register.spec.ts`; `make ui-planning-workspace-gate` green; C03 still In progress (UI-03…05) |
| 2026-08-12 | **PLN-UI-01 Done** — literal Stitch v1.9 workspace port (scope helper, plan strip, work select+search, table footer/`attachPagination`); C03 In progress (UI-02…05 remain) |
| 2026-08-12 | **UI scope correction** — every PLN-UI-01…10 + 07A is **Re-implement required** (full Stitch v1.9 literal port). Tracker no longer implies selective re-ports of a few screens; C03–C06 exit = all assigned canvases Done |
| 2026-08-11 | **PLN-GATE-C02 Done** — Departmental Submission + contribution UI/API/capability removed; statutory schema purged; preference editor writes stopped; submit = Ready-only until C05 Finance; REM-001…008 Done |
| 2026-08-11 | Tracker 2.0 created for REQ 1.8 / Stitch 1.9 / Cursor 1.7 / CMOM 1.1; contribution-era tracker retired |
