# Departmental Needs — gap analysis against NDS-CHG-001 v1.1

**Authority:** `KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1.1.md` (approved 28 Aug 2026; supersedes v1.0 in full).
**Upstream control contract:** `../00_common/KenTender_E2E-REQ-001_Departmental_Requirement_to_Tender_Preparation_Control_Contract_v0.2.md`.
**Companions:** `03_NDS_Rebuild_Implementation_Plan.md`, `IMPLEMENTATION_TRACKER.md`.
**Analysis date:** 2026-08-29
**Implementation under review:** `kentender_procurement/kentender_procurement/departmental_needs/` (+ `setup/`, `public/js/`, `public/css/`, `tests/ui/smoke/departmental_needs/`).

## 1. Executive summary

The v1.0 → v1.1 **document** diff is small: one field rename (`business_justification` → `expected_operational_result`, now carried downstream into Planning), a role-model simplification (delete `Departmental Review Delegate` and `Needs Configuration Manager`; use native Frappe permissions only), a new KEBS seed profile (§14.6), and two new sections (§19 E2E-REQ-001 conformance, §20 approval effect). All nine modified `.dc.html` artboards carry only that rename plus new help text on the two editable instances.

The **code** gap is far larger and mostly pre-dates v1.1. The live module was built against an older, heavier model — several source files cite `NDS-CHG-002`, a document that no longer exists anywhere in `docs/`. NDS-CHG-001 v1.1 §1.1 "Conflict and disposition register" explicitly disposes of most of what the code still contains: the item child table, attachments, indicative cost/currency, delivery location, free-text `Other` unit, `Partially included` usage, and the extra roles. The spec's own header sets the posture: *"Clean correction in place; no compatibility layer."*

Verdict: this is a **rebuild in place**, on the same pattern already executed for Strategy (STR-CHG-001 v1.3), Budget (BUD-CHG-001 v1.2), STD Configuration (STD-CHG-001 v1.3) and PE/FY Maintenance (CFG-CHG-002) — not a rename patch. The transactional mechanics in `services/lifecycle.py` are sound and are the main asset worth carrying forward.

## 2. What changed between v1.0 and v1.1 (document-level)

| # | Change | Spec anchor | Code impact |
|---|---|---|---|
| 1 | `business_justification` → `expected_operational_result`; value is now carried **read-only into Planning and downstream lineage** (in v1.0 it explicitly stopped at Departmental Needs) | §1.1 row, §2.2, §4.3, §7.1, §7.2 | Field rename **plus** a payload/behaviour change. 34 references across 18 files. |
| 2 | Accepted event bumped `DepartmentalNeedAccepted.v1` → **`.v2`**, now including the expected operational result | §7.1, NDS-AC-038 | Event schema change; Planning consumer must move with it. |
| 3 | `Departmental Need Requester` role → **`Departmental Author`** | §5.1, §6, NDS-BR-005 | Role rename across fixtures, page roles, permissions, seeds, tests. |
| 4 | **Delete** `Departmental Review Delegate` role; an acting HoD uses the same `Head of User Department` role + a time-bound native User Permission | §1.1, §6, §12.2, §14.2, NDS-AC-042 | Role deletion + delegation mechanism replacement. |
| 5 | **Delete** `Needs Configuration Manager` role; the Procurement Planner maintains the PE/FY intake window | §1.1, §6, §8.2, §10, §12.7, NDS-AC-043 | Role deletion + intake-window ownership move. |
| 6 | Permission source must be **native Frappe Role / Workflow permission / User Permission only** — no Capability Profile, no Operational Scope Assignment, no parallel store | §1.1, §6, §9 (`NDS_SCOPE_DENIED`), NDS-AC-044 | Replaces this module's entire authorization approach. |
| 7 | Requirement type is classified by the **Procurement Planner** (not a "DPP Validator") | §7.3 | Terminology only; no NDS code owns this. |
| 8 | New **KEBS first-slice profile** — `SRC-KEBS-ICT-001/002/003` | §14.6, NDS-AC-045 | New seed profile. |
| 9 | New **§19 E2E-REQ-001 conformance** table (8 non-drift controls) | §19 | No direct code; becomes a release-gate checklist. |
| 10 | New acceptance criteria **NDS-AC-038 – NDS-AC-045**; NDS-AC-022 and NDS-AC-024 reworded | §15 | 8 new criteria to evidence. |
| 11 | Accepted-withdrawal wording: "existing Planning amendment route" → "governed Planning **successor-version** route" | §5.3 | Vocabulary alignment with PLN-CHG-001 v1.1. |

Unchanged between v1.0 and v1.1: all lifecycle tables (§5.1–5.3), all 21 invariants (NDS-BR-001–021) except actor labels, all service contracts (§8) except the intake-window control description, routes (§10), the design contract's 14 artboard definitions (§11) except the renamed field, §12 interaction requirements except role wording, §13 audit, §16 constraints, §17 prohibited shortcuts.

## 3. §1.1 disposition register — row-by-row verdict against current code

Each row of the spec's conflict register, checked against what exists today.

| Spec disposition | Present in code? | Evidence | Verdict |
|---|---|---|---|
| One Need = one requirement; quantity/unit belong to the Need (drop multi-line items) | **Yes — violated** | `doctype/departmental_need_item/` is a full doctype linked many-to-one; `lifecycle.py::_items()` replaces a whole item set per save; create page renders an add/remove item table | Delete doctype + item UI + item validation |
| Remove Planner combine/split/partial allocation of Need lines | Partly | `procurement_planning/services/need_allocations.py` + `Plan Need Allocation` doctype | Reconcile with Planning (full-quantity only) |
| Remove `Partially included` usage | **Yes — violated** | `services/usage.py::planning_usage()` returns `Partially included` | Reduce to `Not included` / `Fully included` |
| Remove delivery/use location | **Yes — violated** | `departmental_need.json` → `delivery_or_use_location`; `_validate_submission` requires it | Delete field, validation, UI row |
| Remove supporting attachments | **Yes — violated** | `doctype/departmental_need_attachment/` + `services/attachments.py` (237 lines) + upload/remove UI + `tests/test_departmental_needs_attachments.py` | Delete doctype, service, API surface, UI, tests |
| Remove indicative estimate, Budget Line, funding source, currency | **Yes — violated** | `departmental_need.json` → `indicative_cost`, `currency`; decimal/positive validation in `_validate_submission`; cost card in create page | Delete fields, validation, UI card |
| Remove free-text `Other` unit | **Yes — violated** | `departmental_need_item.json` → `unit_code` Select includes `Other` + `other_unit` Data; `constants.py::UNIT_CODES` | Replace with governed unit catalogue Link |
| Remove requirement type / procurement category | No | Not present | Compliant — keep it that way (static scan) |
| Remove Strategy reference | No | Not present | Compliant |
| Remove generic source/authority/evidence/notes/contact | No | Not present | Compliant |
| Remove Budget Officer / Accounting Officer workspaces | **Yes — violated** | `setup/departmental_needs_page.py:19-30` grants page access to `Budget Officer`, `Accounting Officer` | Remove from page roles (NDS-AC-023) |
| Remove Procurement Planner landing page | **Yes — violated** | Same file grants `Procurement Planner` the module landing page | Planner keeps only the read-only accepted-source deep link (NDS-UI-06) |
| Replace 4 summary cards + separate action/waiting sections + advanced filters with one table + minimal filters | **Yes — violated** | `public/js/departmental_needs_page.js` renders 4 summary cards, a "Work requiring action" table **and** a main table; `workspace.py::get_workspace()` computes the four counts | Collapse to §11.2 shape |
| Remove shared-task claim/release/support-lookup | Partly | No claim/release, but `workspace.py::get_support_need()` + `authorization_diagnostics.authorize_support_record_view` is a support-lookup path | Remove support-lookup surface |
| Replace `/departmental-needs`, `/desk/departmental-needs`, `/demands` with §10 canonical routes; no redirect | **Yes — violated** | Current Desk pages: `departmental-needs`, `departmental-needs-new`, `departmental-needs-edit`, `departmental-needs-review`, `departmental-needs-detail` — none match §10's path-segment routes | Re-route all 8 screens (NDS-AC-030) |
| Accepted Need is immutable **but** a reviewed successor may replace it | **Yes — missing** | `lifecycle.py::update_need` rejects anything outside `{Draft, Returned}` (`NDS_CONTENT_LOCKED`); no successor concept exists at all | Build the whole §5.2 successor lifecycle |
| Accepted withdrawal only via reviewed request; Active Plan dependency cleared first | Partly | `request_withdrawal` / `approve_withdrawal` exist and block on allocations, but no `Decline`, no `Awaiting planning clearance`, no persisted request record | Complete §5.3 |
| Needs intake window is owned by this module and separate from Planning's window | **Yes — violated** | `services/context.py` (29 lines) only calls `financial_context.resolve_fiscal_year` and maps future/past to errors — there is **no intake window record at all** | Build `NeedsIntakeWindow` doctype + NDS-UI-08 |
| Planning payload excludes Strategy / requirement type / generic evidence | Compliant on exclusions | — | Payload still needs the `.v2` rename/addition |
| Accepted Need is **not** the exclusive source of a DPP entry | Planning-side | Owned by PLN-CHG-001 v1.1 | Cross-module; verify no NDS-side assumption |
| `business_justification` → `expected_operational_result`, carried downstream | **Yes — violated** | 34 refs across 18 files | Rename + propagate |
| Delete `Departmental Review Delegate` role | **Yes — violated** | `setup/departmental_needs_page.py:26`; `notifications.py::_review_recipients()` resolves `Authorization Delegation` delegates; `tests/test_departmental_needs_completeness_gaps.py` asserts "delegate can review within scope" | Delete role + delegation path; replace with scoped User Permission |
| Delete `Needs Configuration Manager` role | Not present as a role, but its function is unowned | No intake-window admin exists at all | Assign to Procurement Planner when NDS-UI-08 is built |
| Native Frappe permissions only — no capability/scope-assignment store | **Yes — violated** | `departmental_need.json` has `permissions: []`; `services/permissions.py` (102 lines) routes every check through `kentender_core.services.authorization_policy`; `constants.py` defines 9 custom capability strings | Replace with native Role + User Permission |
| No legacy Demand migration/compatibility | Compliant in this module | `tests/test_departmental_needs_completeness_gaps.py` already asserts no Requisition/Tender references | Keep; note the pre-existing unrelated `kentender_procurement.demands` import failure in `kentender_core/seeds/kentender_mvp_v1/users.py` |

## 4. Domain model diff (§4)

### 4.1 Spec entities vs. implemented doctypes

| Spec entity (§4) | Implemented as | Gap |
|---|---|---|
| `NeedsIntakeWindow` (§4.1) | **Nothing** — `services/context.py` derives open/closed from generic fiscal-year flags | Build doctype (`procuring_entity_id`, `financial_year_id`, `opens_at`, `closes_at`; at most one per PE/FY; Scheduled/Open/Closed derived, never stored) |
| `DepartmentalNeed` (§4.2) — thin root | `Departmental Need` — flat record holding **all** content | Slim to root: `current_state`, `current_version_id`, `current_accepted_version_id`, `record_version`, immutable PE/OU/FY, framework `owner` |
| `DepartmentalNeedVersion` (§4.3) | **Nothing** — no versioning; `revision_no` Int counted from audit events | Build doctype with the six user values + `version_number`, `based_on_version_id`, `version_status` (7 values incl. `Superseded`), `content_hash` |
| `DepartmentalNeedReviewTask` (§4.4) | Generic `Workflow Task` from `kentender_core` | Decide: keep the core engine and project a typed read, or add a module doctype. Needs `task_type` ∈ {Initial acceptance, Successor acceptance, Withdrawal} and `decision_token` |
| `DepartmentalNeedDecision` (§4.5) | `Departmental Need Review` — audit log **and** idempotency ledger in one | Split concerns; reasons only for Return / Do-not-take-forward / Request-withdrawal / Decline-withdrawal |
| `NeedWithdrawalRequest` (§4.6) | **Nothing** — state lives only in a Workflow Task + log row | Build doctype with 4-value `status` incl. `Awaiting planning clearance`, `planning_dependency_version`, 20–1,000 char reason |
| `NeedPlanningUsageProjection` (§4.7) | Computed on read in `services/usage.py` from `Plan Need Allocation` | Acceptable as a projection, but must drop `Partially included` and carry `active_plan_id` / `active_plan_item_id` / `source_event_id` |

### 4.2 `Departmental Need` field-by-field

| Current field | Type | Spec disposition |
|---|---|---|
| `need_reference` | Data | **Keep** — matches §4.2 `NDS-{PE}-{FY}-{4 digits}` |
| `title` | Data | **Move** to `DepartmentalNeedVersion` (5–160 chars) |
| `procuring_entity` | Link | Keep on root; make immutable |
| `pe_fy_context` | Link | **Delete** — unused; §4.2 has no such field |
| `organisation_unit` | Link | Keep on root as `org_unit_id`; immutable |
| `target_financial_year` | **Data** | Keep as **Link** to `Financial Year` (currently a plain string — a real defect) |
| `submitted_by` | Link User | **Delete** — §4.2 says use the framework `owner` field, "do not create a duplicate originator field" |
| `business_justification` | Long Text | **Replace** with version-level `description` **and** `expected_operational_result`, 10–1,000 chars each |
| `required_by_date` | Date | **Move** to version |
| `delivery_or_use_location` | Data | **Delete** (§1.1, §17) |
| `indicative_cost` | Currency | **Delete** (§1.1, §17) |
| `currency` | Link | **Delete** (§1.1, §17) |
| `status` | Select | **Keep** as `current_state`; same six values |
| `revision_no` | Int | **Delete** — replaced by `version_number` on the version record |
| `submitted_at` / `last_decision_at` | Datetime | Move to decision/version records |
| `concurrency_token` | Data | **Keep**, rename to `record_version` (§4.2) |
| `fixture_namespace` | Data | Keep (test-seed scoping; not user data) |
| *(missing)* | | Add `current_version_id`, `current_accepted_version_id` |

Also missing: `indicative_quantity` and `unit_id` — today they live per-item on `Departmental Need Item`, which the spec deletes. They become single version-level fields (quantity > 0, ≤ 3 decimals; unit a Link to the governed catalogue).

## 5. Lifecycle and command gaps (§5, §8.2)

`services/lifecycle.py` (467 lines) implements a genuinely good transactional pattern — idempotency-key replay check → `SELECT … FOR UPDATE` row lock → optimistic token check → ownership/capability check → state guard → validation → mutate → audit event with before/after hashes → routed task dispatch. **Keep this pattern.** The gaps are in coverage and rule detail.

| §8.2 command | Today | Gap |
|---|---|---|
| `save_need_draft` | `create_need` / `update_need` | Rename/reshape; must generate version 1, not a flat record |
| `submit_need_version` | `submit_need` | Must lock an immutable version + `content_hash`; validation bounds wrong (see below) |
| `return_need_version` | `review_need(decision="return")` | Must create the **copied correction Draft successor** server-side (§5.1, NDS-AC-011) — today the same record is reopened |
| `accept_need_version` | `review_need(decision="accept")` | Must handle initial **and** successor acceptance + supersession lineage |
| `decline_need_version` | `review_need(decision="decline")` | Must leave an earlier accepted version current when declining a successor |
| `withdraw_unaccepted_need` | `withdraw_need` | Roughly present |
| `create_accepted_need_successor` | **Missing** | Whole §5.2 flow absent |
| `cancel_accepted_need_successor` | **Missing** | NDS-AC-033 unimplementable today |
| `request_accepted_need_withdrawal` | `request_withdrawal` | No persisted request record; no `NDS_WITHDRAWAL_ALREADY_OPEN` guard |
| `decide_accepted_need_withdrawal` | `approve_withdrawal` only | **No decline, no `Awaiting planning clearance`, no re-evaluate** (§5.3 has 5 rows; 1 is implemented) |
| `save_needs_intake_window` | **Missing** | No window record, no screen, no owner |
| `project_need_planning_usage` | **Missing** | Usage is computed by reading Planning's table directly — §3 forbids querying a downstream table; it must arrive as an ordered idempotent event |

Validation-bound mismatches in `_validate_submission()`:

| Rule | Code today | Spec |
|---|---|---|
| Justification length | 50–2,000 chars, one field | `description` 10–1,000 **and** `expected_operational_result` 10–1,000, separate fields (§4.3) |
| Title length | not bounded | 5–160 chars (§4.3) |
| Quantity decimals | per item, unbounded | ≤ 3 decimals, > 0 (§4.3) |
| Location | **required** | Field deleted (§1.1) |
| Cost decimals | ≤ 2, positive | Field deleted (§1.1) |
| Attachments must be `Clean` | enforced | Attachments deleted (§1.1) |
| Return/decline reason | 20–1,000 ✓ | Matches NDS-BR-011 — keep |

## 6. Permission gaps (§6)

| Spec requirement | Today |
|---|---|
| Native Frappe Role + Workflow permission + User Permission only | Custom capability engine; `Departmental Need` doctype has `permissions: []` by deliberate design (`setup/departmental_needs_doctypes.py` — `CONTROLLED_PERMISSIONS = []`, commented "even support reads must pass through the audited projection") |
| Exactly 5 roles: Departmental Author, Head of User Department, Procurement Planner, Auditor, System Administrator | Page grants 8 roles incl. `Departmental Need Requester`, `Departmental Review Delegate`, `Budget Officer`, `Accounting Officer` |
| Acting HoD = same role + time-bound scoped User Permission | `Authorization Delegation` records resolved in `notifications.py::_review_recipients()`; delegate-review asserted by an existing test |
| Procurement Planner maintains intake window, gets no Need decision | Planner has a module landing page and no window to maintain |
| Budget Officer / Accounting Officer get nothing (NDS-AC-023) | Both hold page access |

This is the largest single architectural change in the rebuild, and it runs **against** the precedent set by CFG-CHG-002 and STR-CHG-001, which both deliberately adopted `authorization_policy`. NDS-CHG-001 v1.1 §6, §1.1 and NDS-AC-044 override that precedent for this module only. Flagged as a decision to record, not to silently resolve — see the plan's decision register.

## 7. Screen and route gaps (§10, §11, §12)

21 artboards exist under `design/`. Current implementation: 5 vanilla-JS Frappe Desk pages (jQuery + hand-built DOM strings), **not** Vue-in-Desk — despite Vue-in-Desk being the validated standard (`AGENTS.md` §6) already used by Strategy, Budget, STD Config and PE/FY.

| § 10 screen | Route required | Today | Gap |
|---|---|---|---|
| NDS-UI-01 Requester workspace | `/app/departmental-needs` | `departmental_needs_page.js` | Route matches; content wrong (4 summary cards, dual tables, unbound filter/download buttons) |
| NDS-UI-02 Department review | `/app/departmental-needs/review` | **Missing** | Queue + department-register tab (NDS-DES-02, 02b) absent |
| NDS-UI-03 Need editor | `/app/departmental-needs/new`, `/{ref}/edit` | `departmental_needs_create_page.js` (create+edit modes) | Wrong routes; renders items table, attachments, cost, location; must also serve successor drafts (NDS-DES-08) |
| NDS-UI-04 Need detail | `/app/departmental-needs/{ref}` | `departmental_needs_detail_page.js` | Generic — no Submitted waiting notice (DES-05), no Accepted variant (DES-07), no Create-update / Request-withdrawal actions, no View Plan Item |
| NDS-UI-05 Review task | `/app/departmental-needs/review/{task}` | `departmental_needs_review_page.js` | Closest match; wrong route; must add successor-review variant (DES-09) |
| NDS-UI-06 Accepted source detail | `/{ref}/accepted/{n}` | **Missing** | Planning deep link has no target |
| NDS-UI-07 Withdrawal review | `/review/{task}/withdrawal` | **Missing** | DES-12a/12b have no implementation; withdrawal tasks are unreachable from any screen |
| NDS-UI-08 Intake window | `/app/departmental-needs/intake-window` | **Missing** | DES-10 has no implementation |

Also missing: NDS-DES-11 withdrawal-request dialog (so `request_withdrawal` is unreachable from the UI entirely), and the five distinct workspace states NDS-DES-14a–e (one generic loading/blocked/empty set exists).

## 8. Events, seeds, tests

- **Events:** `DepartmentalNeedAccepted` is not emitted as a versioned outbox payload; `DepartmentalNeedSuperseded.v1` and `DepartmentalNeedWithdrawn.v1` do not exist. §7.1 requires transactional-outbox delivery, idempotent and ordered per Need.
- **Notifications:** `services/notifications.py` covers submit / return / accept / decline only — no withdrawal-decision events (§8.2 requires them).
- **Seeds:** `seeds/kentender_mvp_r1.py` predates §14; needs the four exact Needs with their exact descriptions/expected results, the separate Planning-usage / successor / withdrawal profiles (§14.4, §14.5), and the new KEBS profile (§14.6).
- **Tests:** 9 Python test modules + 4 Playwright specs cover the *current* model in depth, including behaviours the spec now prohibits (`test_departmental_needs_attachments.py` in full; the delegate-review case in `test_departmental_needs_completeness_gaps.py`). These are rewrites, not extensions. The four `doctype/*/test_*.py` files are empty stubs.
- **§15.1 minimum coverage** additionally requires visual regression at 1440 × 1024 for every artboard, modal and workspace state — no such layer exists today.

## 9. Documentation hygiene

- `design/uploads/KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1.1.md` is a **stale pre-approval draft** — identical to the approved copy except `Status | Proposed for approval` and a conditional §20. It is design-canvas input, not authority. Reconcile or remove so nobody implements from it.
- Source files citing `NDS-CHG-002` (`services/notifications.py:1`, `services/attachments.py`, `kt_cl_surface_registry.js`, `departmental_needs_create_page.js:191`) reference a document that does not exist in `docs/`. `departmental_needs_create_page.js:191` also cites an "NDS-CHG-002 Phase 9 coverage map" that exists nowhere in the repo. All such references must be corrected to NDS-CHG-001 v1.1 during the rebuild.
- No implementation tracker existed for this module before this pass (unlike Strategy, STD Config and PE/FY).

## 10. Known open questions carried into the plan

1. ~~**Owning app.**~~ **RESOLVED — firm Project Owner decision, 2026-08-29.** Departmental Needs and Procurement Planning remain **separate modules within `kentender_procurement`**. Planning consumes Accepted Needs **only** through the published handoff contract; direct access to Departmental Needs DocTypes, tables or internal services is **prohibited and enforced by automated architecture tests** (tracker row NDS-910). No additional Frappe app is introduced. The §3 boundary is therefore executable, not conventional.
2. **Permission engine.** §6/NDS-AC-044 mandates native Frappe permissions, contradicting the `authorization_policy` precedent adopted by CFG-CHG-002 and STR-CHG-001. The spec is the authority for this module; the divergence should be recorded so the platform-level split stays visible.
3. **Review task modelling.** Whether `DepartmentalNeedReviewTask` becomes a module doctype or a typed projection over `kentender_core`'s generic `Workflow Task`. The generic engine already provides routing, tokens and atomic completion; a typed read may satisfy §4.4 without a parallel task store.
4. **Usage projection direction.** §3 forbids querying downstream tables, but `services/usage.py` reads `Plan Need Allocation` directly. Fixing this requires a Planning-published event (`NeedPlanningUsageChanged.v1`) — cross-module work that must be sequenced with PLN-CHG-001 v1.1.
