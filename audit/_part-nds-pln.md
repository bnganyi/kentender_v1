# Part nds-pln — Departmental Needs and Procurement Planning findings

All claims are static (code and documents read; nothing was run). Paths are relative to the repo root `/home/midasuser/frappe-bench/apps/kentender_v1`; `NDS/` = `kentender_procurement/kentender_procurement/departmental_needs`, `PLN/` = `kentender_procurement/kentender_procurement/procurement_planning`. Docs: NDS = `docs/mvp-1-r1/01_departmental_needs/KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_16.md` (Approved 3 Oct 2026); PLN = `docs/mvp-1-r1/04_planning/KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_29.md` (Approved 3 Oct 2026). Neither document marks any rule cited below as proposed or pending, so no finding carries "divergence from proposed spec".

| ID | Severity | Title |
|---|---|---|
| AUD-NDS-001 | High | A Need whose accepted revision is a successor drops out of Planning's source list; Planning then deletes its Draft entry and never publishes the "Update required" position |
| AUD-NDS-002 | Duplicate (see AUD-HND-002) | Withdrawal approval checks one revision's local cache, treats "no projection" as clear, and calls no Planning validator |
| AUD-NDS-003 | Medium | AO, HOPF and Planner receive an author's unsent Draft successor through get_departmental_need |
| AUD-NDS-004 | Medium | A superseded accepted revision cannot be read at its own route; the page shows the current revision |
| AUD-NDS-005 | Medium | "Awaiting planning clearance" is unreachable from the UI; approve-while-included raises instead of recording the block |
| AUD-NDS-006 | Medium | A Returned correction can be resubmitted after intake closes; the next-step answer says it cannot |
| AUD-NDS-007 | Medium | Acceptance does not recheck the unit or the content hash |
| AUD-NDS-008 | Medium | Unknown save/submit outcome is not resolved; a refresh mints a new key and can create a second root |
| AUD-NDS-009 | Medium | Disposition event uses a different enum and sequence than the approved wire contract |
| AUD-NDS-010 | Medium | The Planning-event consumer lacks the versioning, conflict, ownership and ordering rules of §7.4–7.5 |
| AUD-NDS-011 | Medium | check_accepted_need_withdrawal_dependency has no permission check |
| AUD-NDS-012 | Low | Successor / withdrawal mutual exclusion is enforced late, with the wrong code, and without a stale-source check |
| AUD-NDS-013 | Low | Intake and usage ordering compares timestamps as strings |
| AUD-NDS-014 | Low | Usage projection keeps a third value "Not proceeding" |
| AUD-NDS-015 | Low | The Procurement Planner is given a full Needs workspace |
| AUD-NDS-016 | Low | The Vue app reads error meaning from message text |
| AUD-NDS-017 | Low | §7.1 lists a PE id in the accepted payload; §3/§4.2/§1.1 say the PE is implicit |
| AUD-NDS-018 | Low | Withdrawn Needs cannot be found from the register (owner decision open) |
| AUD-NDS-019 | Low | NDS §14 seed fixture differs from the executable two-year seed world |
| AUD-PLN-001 | Medium | Active-plan funding is never marked stale when the Budget changes; Requisition authorisation keeps passing |
| AUD-PLN-002 | High | Hold-then-withdraw-for-correction sequence dead-ends |
| AUD-PLN-003 | High | A classification correction does not mark or block an affected Draft Plan Item |
| AUD-PLN-004 | High | An absent reservation rule is reported as "Required allocation met" and does not block submission |
| AUD-PLN-005 | Medium | Strategy snapshot is taken at Plan Item save, not at final approval, and ignores the plan's fiscal year |
| AUD-PLN-006 | Medium | Successor submission and activation recheck neither scope lock nor consumed value; removal takes no reason |
| AUD-PLN-007 | Medium | Approved removals re-queue the source; removed items stay in the reviewed totals but not in the published plan |
| AUD-PLN-008 | Medium | A correction request can be "Resolved" against the unchanged Active Version |
| AUD-PLN-009 | Medium | ReturnPlanVersion records no collective resolution and caps the reason at 500 |
| AUD-PLN-010 | Medium | Segregation chain omits SavePlanVersionDetails and the funding-reuse request |
| AUD-PLN-011 | Medium | Splitting confirmation is free text with no related-item set, rule Version or stale-finding check |
| AUD-PLN-012 | Medium | "Fixture-verified — not production law" passes every verification gate (spec gap) |
| AUD-PLN-013 | Low | Late-activation read labels ordinary successors as late and offers an action that then fails |
| AUD-PLN-014 | Low | Planning raises a Finance notification where the spec says Planning sends none |
| AUD-PLN-015 | Low | A withdrawn initial departmental plan leaves a stale Need position at NDS |
| AUD-PLN-016 | Low | Return issue entry ids are not validated |
| AUD-PLN-017 | Low | PLN_BASELINE_LOCKED is raised for only two edit shapes |
| AUD-PLN-018 | Low | WithdrawDepartmentalSubmission cannot withdraw a Submitted plan; spec is ambiguous (spec gap) |
| AUD-PLN-019 | Low | Combination rule: PLN §5.6.2 and PLN18-AC-055 disagree; code adds an undocumented origin restriction |
| AUD-PLN-020 | Low | Technical-operator "Your turn" contradicts PLN27-AC-009 (spec defect) |
| AUD-PLN-021 | Low | Statutory withdrawal for correction skips the segregation check (spec gap) |
| AUD-PLN-022 | Low | Departmental plan is auto-created on Need acceptance (spec gap) |

### AUD-NDS-001 — A Need whose accepted revision is a successor drops out of Planning's source list; Planning then deletes its Draft entry and never publishes the "Update required" position
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §7.2, §5.5, NDS-BR-013, NDS15-XD-001; PLN v1.29 §5.1.2 and §7.3 (position published "after every departmental-plan command and every Need acceptance") · **Module(s):** NDS, PLN · **Sources:** trace-needs C-08; sweep-handoffs F-5
**Evidence**
- `NDS/services/lifecycle.py:806-811` — `if superseded: event = publish_superseded(...) else: event = publish_accepted(doc, version)`; a successor acceptance writes only `DepartmentalNeedSuperseded.v1`.
- `NDS/services/events.py:253-290` — `current_accepted_events` returns only the `Departmental Need Event` row with `"event_type": EVENT_ACCEPTED` and `"need_revision": row.current_accepted_revision` (line 281). No such row exists for a successor, so the Need is skipped. Test `NDS/tests/test_departmental_needs_events.py:228` (`..._publishes_supersession_not_a_second_accepted`) pins that no second accepted event exists.
- `PLN/services/needs_intake.py:163-170` — `payload = by_need.pop(cstr(row.need), None); if payload is None: frappe.delete_doc("Departmental Plan Entry", row.name, force=True, ...)`: the Draft entry of the omitted Need is deleted (its funding specification goes with it). `refresh_draft_entries` is called from `PLN/services/dpp_read.py:174,445` and `dpp_lifecycle.py:220-310`.
- `PLN/services/needs_intake.py:279-316` — `need_positions` also builds positions from `current_accepted_sources`, so the same omission means no "Update required" (with carried revision) position can ever be produced for a successor-accepted Need, not merely a delayed one.
- `PLN/services/dpp_autostart.py:57` — `if cstr(doc.get("event_type")) != EVENT_ACCEPTED: return`; the superseded event triggers nothing.
**Rule:** NDS §7.2 "Accepted Need successor: Makes the old source stale for new/current Planning use … successor refreshes six facts"; PLN §5.1.2 position table "Update required (with the earlier revision it carries, if any)", which exists only for successor revisions; NDS15-XD-001 "every Need acceptance".
**Reproduction / failing test sketch:** (static; not run, test site) 1. Accept Need N revision 1 for department D; let the autostarted Draft DPP take N in. 2. Author `create_accepted_need_successor`, edit, submit; HoD `accept_need_revision` (successor). 3. Call `events.current_accepted_events(financial_year=FY, organisation_unit=D)`: N is absent. 4. Open the department's Draft plan (`dpp_read` refresh) or call `needs_intake.refresh_draft_entries(version)`: the Need-origin entry for N is deleted. 5. `get_need_planning_status(N)`: no `planning_intake`. Failing assertion: the payload for N has `accepted_version_id == <successor revision>`.
**Impact:** After any successor acceptance the department's Draft plan silently loses that Need (and any funding already entered), and an already-accepted departmental plan is never told to update, re-opening the late-accepted-Need dead end for revisions.
**Verification:** CONFIRMED — `lifecycle.py:808-811` publishes only `DepartmentalNeedSuperseded.v1` for a successor, `events.py:277-288` selects strictly `EVENT_ACCEPTED` rows keyed on the current revision (so the Need drops out of `needs_intake.current_accepted_sources`), and `needs_intake.py:~160-168` deletes any Draft entry whose Need is absent from that set; no other producer writes an accepted event for a successor.

### AUD-NDS-002 — [DUPLICATE of AUD-HND-002] Withdrawal approval checks one revision's local cache, treats "no projection" as clear, and calls no Planning validator
**Severity:** Duplicate · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §5.3, §8.3 (`validate_accepted_need_withdrawal_for_decision`), NDS-BR-016, NDS11-AC-019/073/074, NDS11-XD-003 · **Module(s):** NDS, PLN · **Sources:** trace-needs C-02
**Evidence**
- `NDS/services/lifecycle.py:976-977` — `detail = planning_usage_detail(cstr(need), cstr(accepted_revision)); included = detail["usage"] == USAGE_FULL`.
- `NDS/services/lifecycle.py:1107` — `dependency = check_withdrawal_dependency(doc.name, request.accepted_revision)`: only the revision pinned by the request is examined.
- `NDS/services/usage.py:82` — `"usage": cstr(row.get("usage") or USAGE_NOT_INCLUDED)`: a Need with no projection row for that revision reads "Not included", so `included` is False; the `recorded` flag the same function returns is ignored by the check.
- Grep of the repository finds no call to or definition of `validate_accepted_need_withdrawal_for_decision`; the approval reads the local `Need Planning Usage Projection` under a Need row lock only.
**Rule:** NDS §5.3 "The decision checks the stable Need **across all accepted revisions**, not just the revision named by the request or the local usage card." and "Unknown, stale, failed or gapped dependency evidence blocks approval; never treat absence of a local projection as clearance." §8.3 requires an owner validator "serialized with Plan activation". NDS11-XD-003 (line 1944) names the Planning-side validator as an open cross-document dependency, so the missing owner call is the document's own owed work; the revision-scope and absence-as-clear defects are not.
**Reproduction / failing test sketch:** (static; not run) 1. Need N, revision R1 `Fully included` in an Active plan (projection row on R1). 2. Successor R2 accepted (no projection row on R2). 3. Author `request_accepted_need_withdrawal` (pins R2). 4. Another HoD `decide_accepted_need_withdrawal(decision="approve")`: `check_withdrawal_dependency(N, R2)` finds no row, `included=False`, approval commits and N is Withdrawn while R1 is still in the Active plan. Test sketch: seed the row on R1, accept R2, assert `approve` raises `NDS_ACTIVE_PLAN_DEPENDENCY`. Second sketch: Need with no projection row and an event gap must fail closed (`NDS_PLANNING_DEPENDENCY_UNAVAILABLE` is not defined anywhere in `NDS/errors.py`).
**Impact:** A Need that is part of an Active Annual Plan can be withdrawn, publishing `DepartmentalNeedWithdrawn.v1` and orphaning an Active plan allocation, whenever the check runs against a revision with no projection row or Planning's event stream lags.
**Verification:** CONFIRMED — `lifecycle.py:976-977,1107-1111` check only `request.accepted_revision`'s projection (`usage.py:82` defaults an absent row to "Not included"), the successor-accept path leaves the older revision's `Fully included` row untouched, and the NDS §5.3 / NDS-BR-016 / line 1581 text is verbatim as quoted; the Planning-side validator is the document's own owed work (line 650) but the revision-scope and absence-as-clear defects stand. Overlaps AUD-HND-002.

### AUD-NDS-003 — AO, HOPF and Planner receive an author's unsent Draft successor through get_departmental_need
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 header amendment and §6.1 ("Unsent author Draft access remains unchanged"); OVS v0.6 §4.1 NDS row ("unsent author Drafts remain under existing access"); NDS §6 (Planner reads current accepted revisions) · **Module(s):** NDS · **Sources:** trace-needs C-14
**Evidence**
- `NDS/services/permissions.py:126-140` — Accepted Needs are readable by the Planner (`"planning"`, line 134) and, through `_oversight_office`, by AO/HOPF for `OVERSIGHT_READ_STATES` (`NDS/constants.py:159` includes Accepted).
- `NDS/services/workspace.py:749` — `"current_revision": _version_facts(doc.current_revision)` is returned unconditionally to every profile; `_version_facts` (`workspace.py:77-99`) returns title, description, quantity and the rest of `REVISION_CONTENT_FIELDS`. For an Accepted Need with an open update, `current_revision` is the Draft/Returned/Submitted successor.
**Rule:** NDS header amendment: "Unsent author Draft access remains unchanged"; OVS §4.1: "unsent author Drafts remain under existing access".
**Reproduction / failing test sketch:** (static; not run) Accepted Need N; owner `create_accepted_need_successor` then `save_need_draft(need=N, title="Private draft title", ...)`; AO (or HOPF, or Planner) calls `get_departmental_need(need=N)`; `current_revision.title == "Private draft title"`. `test_ovs_needs_reads.py` asserts only the access profile and actions, not content.
**Impact:** Roles that the documents say must not see unsent author drafts can read their content (Needs have no funding data, so sensitivity is limited to requirement text and quantity).

### AUD-NDS-004 — A superseded accepted revision cannot be read at its own route; the page shows the current revision
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §12.4 / NDS-UI-06, §8.1 `get_departmental_need` (optional accepted revision), NDS-DES-07-HISTORICAL, NDS11-AC-069 · **Module(s):** NDS (Vue) · **Sources:** trace-needs C-15
**Evidence**
- `NDS/services/workspace.py:643` — `def get_need(*, need: str, user: str | None = None)`: no revision parameter; usage and disposition are built for `doc.current_accepted_revision` only (lines 758-761).
- `NDS` Vue `public/js/departmental_needs/DepartmentalNeeds.vue:381-388` — `pinnedRevision` returns `accepted` when the number matches and otherwise `return accepted || null;` (line 387), i.e. the CURRENT accepted revision object.
- `components/NeedDetailScreen.vue:421-426` — `isHistoricalRevision` is true only when `pinnedRevision.name !== acceptedRevision.name`; with the fallback above both are the same object, so it is never true and the "has been superseded" notice (line 93) is unreachable.
**Rule:** NDS §12.4: the Planning deep link "fixes the accepted revision in the route. If it is superseded, the page remains historically readable and clearly labels the current accepted revision without redirecting or rewriting the requested revision."
**Reproduction / failing test sketch:** (static; not run) Need with R1 superseded by R2; open `/app/departmental-needs/<ref>/accepted/1`: the Required-by date and title shown are R2's. Test: change R2's required-by, load the R1 route, assert R1's value and the superseded notice. `accepted-source.spec.ts:43` asserts only the URL and `data-reference`.
**Impact:** A Planner following a Plan Item's link to the revision the plan actually used reads different requirement facts than the plan holds, with no warning.

### AUD-NDS-005 — "Awaiting planning clearance" is unreachable from the UI; approve-while-included raises instead of recording the block
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §5.3 table (Evaluate), §8.2 `decide_accepted_need_withdrawal` ("approve, block for clearance or decline atomically"), §12.6 ("the command records/retains Awaiting planning clearance"), §5.5, §7.6 · **Module(s):** NDS · **Sources:** trace-needs C-20
**Evidence**
- `NDS/services/lifecycle.py:1039` — `request_withdrawal` always creates the request with `"status": WITHDRAWAL_AWAITING_REVIEW`.
- `NDS/services/lifecycle.py:1111-1115` — `if decision == "approve": if dependency["included"]: fail("NDS_ACTIVE_PLAN_DEPENDENCY", ...)` raises and rolls back; nothing is recorded.
- `NDS/services/lifecycle.py:1138-1152` — only an explicit `decision == "evaluate"` sets `WITHDRAWAL_AWAITING_CLEARANCE`.
- `public/js/departmental_needs/DepartmentalNeeds.vue:1142,1195` — the app sends only `decideWithdrawal("decline")` and `decideWithdrawal("approve")`; a grep for `evaluate` in the Vue app finds nothing outside specs.
**Rule:** NDS §8.2 (line 634) and §12.6 (line 1410): "If an Active Plan dependency exists, the command records/retains `Awaiting planning clearance`, returns the exact Plan/Plan Item reference …".
**Reproduction / failing test sketch:** (static; not run) Need included in the Active plan; author requests withdrawal; HoD opens the review in the browser: only Decline is offered, status stays "Awaiting review"; calling `decide_accepted_need_withdrawal(decision="approve")` returns `NDS_ACTIVE_PLAN_DEPENDENCY` and no status change. Tests `T-LC:1238` and `T-DE:137` reach the state only by calling `evaluate` directly.
**Impact:** The Planner's "Decide whether the annual plan keeps this need" turn and the author's "Waiting for a Planning change" item (`NDS/services/guidance.py:249-263` for the Planner turn; the author waiting item is in `NDS/services/my_work_provider.py`) are unreachable in a browser-driven flow, so a blocked withdrawal never reaches the Planner.

### AUD-NDS-006 — A Returned correction can be resubmitted after intake closes; the next-step answer says it cannot
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §12.7 (line 1418: "At the close instant, initial creation, initial submission and resubmission of an unaccepted Returned initial Need are blocked"), NDS-BR-003 (line 422: "Submission stays blocked while the flag is closed"), NDS11-AC-054 (line 1675), NDS12-AC-017 (line 1742), NDS11-CHG-015 (line 1894) · **Module(s):** NDS · **Sources:** trace-needs C-03
**Evidence**
- `NDS/services/lifecycle.py:663-669` — `elif prior in {STATE_DRAFT, STATE_RETURNED}: ... if prior == STATE_DRAFT: require_open_intake(doc.financial_year)`; the Returned branch is not gated.
- `NDS/services/guidance.py:168-203` — for Draft and Returned alike, closed intake yields `NDS_INTAKE_NOT_OPEN` / "New submissions are closed"; the code is therefore internally inconsistent.
- Pinned the other way by `NDS/tests/test_departmental_needs_lifecycle.py:478` (`test_a_returned_correction_may_be_resubmitted_after_the_window_closes`) and `NeedEditorScreen.spec.js:65`.
**Rule:** NDS §12.7 and NDS11-CHG-015 ("preserve save/correction while initial submit/resubmit stays blocked"). `FOLLOW_UPS.md` FU-18 (4 Sep 2026) recorded the ambiguity against v1.6; the later amendments settled it as "blocked", and BR-002/BR-003 still use the narrower word "initial", which should be reconciled (SPEC DEFECT note).
**Reproduction / failing test sketch:** (static; not run) Need returned for correction; CFG closes needs submission for the FY; `submit_need_revision(need, expected_version, idempotency_key)` returns `current_state == "Submitted"`; expected `NDS_INTAKE_NOT_OPEN`.
**Impact:** After the legal close instant a department can still push a returned Need into review, and the screen's own guidance contradicts the command.

### AUD-NDS-007 — Acceptance does not recheck the unit or the content hash
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §8.2 `accept_need_revision` ("Recheck exact reviewer task, current unit, content hash and concurrency"), §4.9 ("Current UOM eligibility is rechecked at acceptance through the owner contract"), NDS11-AC-081 · **Module(s):** NDS · **Sources:** trace-needs C-04
**Evidence**
- `NDS/services/lifecycle.py:703-815` — `review_need` rechecks reviewer, maker-checker, task token and record version; it never calls `_validate_submission` (defined at 445, called only at 675 inside `submit_need`) or `_content_hash` (defined at 184).
- `NDS/services/events.py:77` — the accepted payload copies the stored `content_hash` and the unit id unchecked.
**Rule:** NDS §8.2 (line 628) and §4.9 (line 332), NDS11-AC-081 "checked at submission and acceptance".
**Reproduction / failing test sketch:** (static; not run) Submit a Need on unit `Each`; set `UOM.enabled = 0` for `Each`; HoD accepts; acceptance succeeds and `DepartmentalNeedAccepted.v2` carries the now-ineligible unit. Test: same sequence must raise at `accept`.
**Impact:** A Need can be accepted onto a unit that the governed catalogue no longer allows, and Planning receives it.

### AUD-NDS-008 — Unknown save/submit outcome is not resolved; a refresh mints a new key and can create a second root
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §8.4 (resolve or replay the same request with its unchanged key before any other write; persist the attempt correlation across refresh), NDS12-AC-008 · **Module(s):** NDS (Vue) · **Sources:** trace-needs C-16
**Evidence**
- `public/js/departmental_needs/DepartmentalNeeds.vue:734-757` — on an ambiguous failure of `submit`/`save-before-submit` the handler sets `submitUnknown.value = true` (line 756) and stops; nothing replays the request. A plain `save` that fails ambiguously only shows the error summary.
- `public/js/departmental_needs/data/needsApi.js:79` — `newIdempotencyKey(action)` mints a fresh UUID for every attempt; grep finds no `sessionStorage`/`localStorage` use for an attempt key in `DepartmentalNeeds.vue` or `data/`.
**Rule:** NDS §8.4 "Resolve/replay the same creation/save request with its unchanged key/payload before submitting or creating another record"; NDS12-AC-008.
**Reproduction / failing test sketch:** (static; not run) New form; drop the network after the server commits `save_need_draft` (no response); refresh and repeat the save: a second Need with a new reference is created because the key differs. `NeedEditorScreen.spec.js:126` only renders the notice.
**Impact:** Duplicate Need roots after a lost response; the "Checking the existing request…" wording promises a check that does not happen.

### AUD-NDS-009 — Disposition event uses a different enum and sequence than the approved wire contract
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §4.8 (line 311) and §7.4 (line 560: "Exact enum `Proceeding` or `Not proceeding this financial year`"); PLN v1.29 §7.6 (line 1037) · **Module(s):** NDS, PLN · **Sources:** trace-needs C-10; trace-planning F-13 (sweep-handoffs F-7 describes the same enum root cause and is owned by the hnd part)
**Evidence**
- `NDS/services/usage.py:256,329-330` — `DISPOSITION_NOT_PROCEEDING = "Not proceeding"`; any other value raises `NDS_FIELD_REQUIRED`. The doctype Select options are `Proceeding\nNot proceeding` (`NDS/doctype/need_planning_disposition_projection/need_planning_disposition_projection.json:18`).
- `PLN/services/dpp_validation.py:254` — the producer passes the same short constant, so producer and consumer agree with each other, not with the document.
- `PLN/services/dpp_validation.py:244,257` — `producer_sequence` is the DPP `submission_number` shared by every Need of the department; PLN §7.6 (line 1037) says it "is allocated transactionally per stable Need's disposition stream".
**Rule:** NDS §7.4 (line 560) and PLN §7.6 (line 1037), quoted above.
**Reproduction / failing test sketch:** (static; not run) As a Procurement Planner call `project_need_planning_disposition(departmental_need=N, need_revision=R, dpp_submission=S, disposition="Not proceeding this financial year", reason="<20+ chars>", source_event_id="e1", producer_sequence=1)`: returns `NDS_FIELD_REQUIRED`. Test: the in-repo producer's value must equal the approved enum string.
**Impact:** Any producer or consumer built to the approved contract is rejected; the two in-repo sides agree only because both diverge.

### AUD-NDS-010 — The Planning-event consumer lacks the versioning, conflict, ownership and ordering rules of §7.4–7.5
**Severity:** Medium · **Classification:** CODE DEFECT (the document marks the coordinated producer/consumer work as outstanding in NDS11-XD-001/002, which bounds severity) · **Doc:** NDS v1.16 §7.4 (line 556 `schema_version`; line 574 "Different payload under the same ID/sequence conflicts; preserve evidence and reject"), §7.5 · **Module(s):** NDS · **Sources:** trace-needs C-24 (and the authentication aspect of C-09, whose caller-identity part is owned by xc-authz item 12)
**Evidence**
- `NDS/services/usage.py:303-372` — no `schema_version` parameter or field exists for the disposition event.
- `NDS/services/usage.py:348-349` — `if frappe.db.exists(DISPOSITION_DOCTYPE, {"source_event_id": event_id}): return {... "idempotent": True ...}` for ANY payload; usage does the same at line 205; the intake projection never compares the id.
- `NDS/services/usage.py:340-342` — only `Departmental Need` existence is checked; `need_revision` is a plain Link (revision need not belong to the Need) and the disposition controller is an empty class (`need_planning_disposition_projection.py`, `pass`), so a disposition can name a revision of another Need or any submission id.
- `NDS/services/usage.py:350-353` — ordering key is `revision::submission`, not the Need's stream; usage has no sequence and orders on a caller-supplied `source_event_time` string (line 207).
- No retention of pending or gapped events, no replay; error codes `NDS_PLANNING_EVENT_INVALID`, `NDS_PLANNING_SYNC_PENDING`, `NDS_PLANNING_DEPENDENCY_UNAVAILABLE` are absent from `NDS/errors.py` (NDS §9 lists them).
**Rule:** NDS §7.4 (rejected/quarantined unknown schema; exact Need/revision/submission verification) and §7.5 (conflicting duplicates rejected with evidence; gap or out-of-order retained, never guessed; replay).
**Reproduction / failing test sketch:** (static; not run) As Planner: `project_need_planning_disposition(departmental_need=N1, need_revision=<a revision of N2>, dpp_submission="x", disposition="Proceeding", source_event_id="e", producer_sequence=1)` succeeds; repeating `source_event_id="e"` with `disposition="Not proceeding"` returns `idempotent: True` and changes nothing instead of conflicting.
**Impact:** Disposition and usage facts that gate withdrawal (see AUD-NDS-002) can be wrong or silently dropped without evidence.

### AUD-NDS-011 — check_accepted_need_withdrawal_dependency has no permission check
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 NDS-BR-019 ("direct routes … use the same server-side scope predicate"), §9 `NDS_SCOPE_DENIED` ("Disclose no protected record data") · **Module(s):** NDS · **Sources:** trace-needs C-07
**Evidence**
- `NDS/api.py:54` — `check_accepted_need_withdrawal_dependency = frappe.whitelist()(lifecycle.check_withdrawal_dependency)` (not guest; any logged-in account).
- `NDS/services/lifecycle.py:966-997` — the function calls neither `actor(...)` nor `require_view`; it returns `active_plan`, `active_plan_item` and `dependency_version` for any Need/revision names supplied.
**Rule:** NDS-BR-019 and §9 as quoted.
**Reproduction / failing test sketch:** (static; not run) Any signed-in user: `GET /api/method/kentender_procurement.departmental_needs.api.check_accepted_need_withdrawal_dependency?need=<need name>&accepted_revision=<revision name>` returns the Active plan and plan item of a Need the caller cannot read.
**Impact:** Disclosure of Plan/Plan-Item identifiers and inclusion status of any Need to any authenticated account (limited sensitivity; names must be guessed or learned elsewhere).

### AUD-NDS-012 — Successor / withdrawal mutual exclusion is enforced late, with the wrong code, and without a stale-source check
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §5.2/§5.3 (lines 414: "an accepted successor and a withdrawal request are mutually exclusive open changes; creation of either checks this under the stable Need lock"; "A changed accepted pointer fails approval with a stale-source result"), §9 `NDS_OPEN_SOURCE_CHANGE_EXISTS` (line 700), NDS11-AC-028/076 · **Module(s):** NDS · **Sources:** trace-needs C-05 (with rows 69, 70, 79)
**Evidence**
- `NDS/services/lifecycle.py:889` — `create_accepted_need_successor` checks only `_open_successor(doc)`.
- `NDS/services/lifecycle.py:1025` — `request_withdrawal` checks only `_open_withdrawal_request(doc.name)`.
- `NDS/doctype/departmental_need_review_task/departmental_need_review_task.py:26-42` — the single-open-task rule later raises `NDS_STATE_CONFLICT` (not the specified code, which is absent from `NDS/errors.py`) when the successor is submitted.
- `NDS/services/lifecycle.py:1107` — approval never compares `request.accepted_revision` with `doc.current_accepted_revision`; `NDS_SOURCE_STALE` is used only at `NDS/services/workspace.py:497` for the Planning read.
**Rule:** NDS §5.2/§5.3 as quoted.
**Reproduction / failing test sketch:** (static; not run) Accepted Need: `request_accepted_need_withdrawal` then `create_accepted_need_successor`: both succeed; `submit_need_revision` of the update then fails with "An open review task already exists". Reverse: with a Draft successor open, the withdrawal request succeeds and approval later withdraws the Draft (`lifecycle.py:1120-1127`).
**Impact:** Update tasks can be orphaned and users get the wrong error late; no data corruption path was found because the task rule still blocks submission.

### AUD-NDS-013 — Intake and usage ordering compares timestamps as strings
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §4.11 / NDS15-AC-001 ("an older `source_event_time` never replaces a newer one") · **Module(s):** NDS · **Sources:** trace-needs C-11
**Evidence**
- `NDS/services/usage.py:480` — `if existing.source_event_time and str(occurred) < str(existing.source_event_time):` (usage at line 207 is identical).
- `source_event_time` is an unvalidated string parameter of the whitelisted endpoint (`usage.py:436-445`); the stored value stringifies as `YYYY-MM-DD HH:MM:SS`; an ISO `T` value sorts after it (`T` > space).
**Rule:** NDS15-AC-001 as quoted.
**Reproduction / failing test sketch:** (static; not run) As Planner project position A with `source_event_time="2026-11-28 09:00:00"`, then position B with `"2026-11-28T08:00:00"`: B (older) replaces A. In-process Planning passes `now_datetime()` objects and is unaffected.
**Impact:** An older position can overwrite a newer one when an external caller uses a different timestamp format.

### AUD-NDS-014 — Usage projection keeps a third value "Not proceeding"
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §4.7 (line 296: "Only `Not included` or `Fully included`"), §17 · **Module(s):** NDS · **Sources:** trace-needs C-12
**Evidence**
- `NDS/constants.py:141-143` — `USAGE_NOT_PROCEEDING = "Not proceeding"`; `USAGE_VALUES = frozenset({USAGE_NOT_INCLUDED, USAGE_FULL, USAGE_NOT_PROCEEDING})`.
- `NDS/services/usage.py:186` — the usage endpoint accepts it; the usage doctype Select lists three options (`need_planning_usage_projection.json:49`); pinned by `T-CT:446`.
**Rule:** NDS §4.7 line 296 and §17; accepted exclusions belong to the disposition projection (§4.8).
**Reproduction / failing test sketch:** (static; not run) Planner calls `project_need_planning_usage(..., usage="Not proceeding", not_proceeding_reason="...")`: accepted although §4.7 allows two values.
**Impact:** A legacy v1.12 value can be written into a stream the spec reserves for confirmed Active-inclusion facts.

### AUD-NDS-015 — The Procurement Planner is given a full Needs workspace
**Severity:** Low · **Classification:** CODE DEFECT (the in-repo tests pin the build; owner to confirm which side is intended) · **Doc:** NDS v1.16 §1.1 ("Procurement Planner Departmental Needs landing page: Remove"), §10 (line 715: "it does not create a Planner landing page"), NDS11-AC-084 (line 1705: "no new Needs workspace") · **Module(s):** NDS · **Sources:** trace-needs C-13
**Evidence**
- `NDS/services/permissions.py:130-134` — Planner can view every Accepted Need; `permissions.py:306` resolves every active unit for site-wide roles including Planner.
- `NDS/services/workspace.py:217-370` — `get_workspace` returns a READY register for that principal.
- `public/js/departmental_needs/components/WorkspaceScreen.vue:51-55` — the Forbidden copy lists "Procurement Planner" among the responsibilities that open the page; the doc's DENIED copy names Author, HoD and Auditor.
- Pinned by `T-PM:737`, `T-NV:337`, `WorkspaceScreen.spec.js:52`.
**Rule:** NDS §1.1/§10/NDS11-AC-084 as quoted.
**Reproduction / failing test sketch:** (static; not run) User with only Procurement Planner: `get_needs_workspace()` returns `ok: True` with rows.
**Impact:** A removed landing page persists; no data beyond the Planner's documented accepted-Need read is exposed.

### AUD-NDS-016 — The Vue app reads error meaning from message text
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** NDS v1.16 §9 (line 702: "Errors are stable service results, not inferred from … free-text exception messages") · **Module(s):** NDS (Vue) · **Sources:** trace-needs C-17
**Evidence**
- `public/js/departmental_needs/DepartmentalNeeds.vue:907` — `intake_closed: /submission is not open/i.test(errorSummary.value)`.
- `DepartmentalNeeds.vue:648` and `:757` — `/not found\.?$/i.test(e.message || "")` decides "masked" versus "load-failure" and the authority-changed path.
- Grep for "not saved" in non-spec Vue/JS finds no occurrence, so the specified "Your changes were not saved." sentence is not produced.
**Rule:** NDS §9 line 702 as quoted.
**Reproduction / failing test sketch:** (static; not run) Reword the server message for `NDS_INTAKE_NOT_OPEN`: the "intake closed" branch no longer fires.
**Impact:** UI behaviour silently changes with message wording; no server-side effect.

### AUD-NDS-017 — §7.1 lists a PE id in the accepted payload; §3/§4.2/§1.1 say the PE is implicit
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** NDS v1.16 §7.1 (line 514 "PE, OU and FY IDs") versus line 254 ("The site PE is implicit") and NDS-BR-001 (line 420) · **Module(s):** NDS · **Sources:** trace-needs C-18, trace-needs row 126
**Evidence**
- `NDS/services/events.py:62-87` — `accepted_payload` carries `org_unit_id` and `financial_year_id` only; pinned by `T-EV:149`.
- NDS lines 254 and 420 state the PE is implicit and never selected; line 514 lists a PE id in the same event.
**Rule:** the document contradicts itself.
**Reproduction / failing test sketch:** n/a (document inconsistency; a conformance test written to line 514 would fail, one written to line 254 would pass).
**Impact:** Consumers cannot tell whether a PE id is owed; no runtime consequence today.

### AUD-NDS-018 — Withdrawn Needs cannot be found from the register (owner decision open)
**Severity:** Low · **Classification:** SPEC GAP — decision for the owner: is the register, the technical search, or the route the discovery path for Withdrawn Needs? · **Doc:** NDS v1.16 header amendment ("Keep accepted, declined, withdrawn and superseded records discoverable under current permission"); OVS FOLLOW_UPS FU-OVS-58 (Open) · **Module(s):** NDS · **Sources:** trace-needs C-19
**Evidence**
- `NDS/services/workspace.py:319` — `if not allowed or doc.current_state == STATE_WITHDRAWN: continue`.
- `docs/mvp-1-r1/17_oversight_visibility/…FOLLOW_UPS.md` line 92 — "Needs: should a withdrawn Need be findable? The workspace drops them … Low — decision, Project Owner, Open".
**Rule:** header amendment as quoted; the document does not say where discovery happens.
**Reproduction / failing test sketch:** (static; not run) Withdraw an accepted Need; `get_needs_workspace` no longer lists it and no status filter offers it.
**Impact:** An author or auditor cannot locate a withdrawn Need except by typing its route.

### AUD-NDS-019 — NDS §14 seed fixture differs from the executable two-year seed world
**Severity:** Low · **Classification:** SPEC DEFECT (approved NDS §14 versus the seed runbook's two-year world; SEED-002 is itself proposed) · **Doc:** NDS v1.16 §14.1-§14.3 (design clock 24 Nov 2026, close 25 Nov 2026 23:59 EAT, four Needs with fixed titles) · **Module(s):** NDS, core seeds · **Sources:** trace-needs C-21
**Evidence**
- `kentender_core/kentender_core/seeds/calendar.py:32` — `AS_AT = "2027-06-18 10:00:00"`.
- `NDS/seeds/kentender_mvp_r1.py:106-125` — `YEAR_NEEDS` replays the §14 chronology 364 days earlier in year 1 and uses different titles and quantities in year 2; the file's own comment records the deliberate shift.
**Rule:** NDS §14.1 states the fixed clock and prerequisites; the build does not reproduce them.
**Reproduction / failing test sketch:** n/a (document-versus-fixture divergence; `T-SD` pins the seed, not §14).
**Impact:** None at runtime; the approved fixture description does not describe the data testers see.

### AUD-PLN-001 — Active-plan funding is never marked stale when the Budget changes; Requisition authorisation keeps passing
**Severity:** Medium (was High; Budget `check_funding` still gates the money at authorisation) · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.3.4 (line 512: "While current funding evidence for an Active Plan is stale, new Requisition authorisation remains blocked."), PLN18-AC-033 · **Module(s):** PLN, REQ · **Sources:** trace-planning F-23
**Evidence**
- `PLN/services/plan_requisition.py:268,282` — eligibility uses `funding_confirmed = version.funding_state == "Confirmed"`, the stored column only; `:486` `authorise_requisition_drawdown` checks `funding_state ... != "Confirmed"` the same way.
- `PLN/services/plan_finance.py:89-104` — `funding_is_current` (digest comparison against the decided basis) exists but has no caller in the Requisition path (callers: `plan_finance.py:154`, `publication_pipeline.py:230`, `next_step.py`, `plan_governance.py:217,433`, `plan_read.py`).
- `PLN/services/plan_finance.py:342` sets `Stale` for an Active Version only inside `return_from_finance`; `plan_read.py:1159-1160` computes staleness for a Draft only and never writes.
**Rule:** PLN §5.3.4 line 512 as quoted; PLN18-AC-033 "its independent current affordability … checks continue to apply".
**Reproduction / failing test sketch:** (static; not run) Active plan with funding Confirmed. Reduce the Budget Line Version `approved_amount` below the planned total. `get_requisition_eligible_plan_item(...)` still returns `eligible: True`; HOPF `authorise_requisition_drawdown` succeeds and locks scope. `test_plan_requisition.py:247` sets `funding_state` by direct DB write, so production staleness is never exercised.
**Impact:** New Requisition authorisations proceed against Plan funding evidence the document says must block them (Budget's own reservation checks at the later gate are separate and were not assessed here).
**Verification:** CORRECTED — severity High -> Medium: the code claim holds (`plan_requisition.py:268,486` read only the stored `funding_state`; `funding_is_current` has no Requisition-path caller), but `authorise.py:112-117` calls Budget `check_funding` (`budget_check_reserve_contracts.py:206-248`, per-line available >= required) and refuses with `REQ_FUNDING_UNAVAILABLE`, so no money can be reserved beyond Budget's own availability; what is lost is the documented evidence-state block, not a funds bypass.

### AUD-PLN-002 — Hold-then-withdraw-for-correction sequence dead-ends
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.2.3 (lines 459-460), §5.7 (line 812: "Material defect held; confirmed unpublished … Accounting Officer: Your turn — Request withdrawal for correction"), U13-UNPUBLISHED-DEFECT (line 1937) · **Module(s):** PLN · **Sources:** trace-planning F-25
**Evidence**
- `PLN/services/publication_pipeline.py:352-353` — `existing = _active_hold(version.name); if existing: return {"ok": True, "idempotent": True, "action": "held", "hold": existing}`: the existing hold is returned unchanged whatever its kind.
- `PLN/services/treasury.py:157-158` — `request_plan_withdrawal` calls `hold_plan_publication(... hold_kind="Withdrawal request" ...)` and then creates the statutory task using the returned hold name.
- `PLN/services/treasury.py:200` — `withdraw_approved_plan_for_correction` requires `hold_kind == "Withdrawal request"`, else `PLN_WITHDRAWAL_NOT_PERMITTED`.
**Rule:** PLN §5.2.3/§5.7: after a hold (system "Detected invalidity" or AO correction request) the AO's next step is to request withdrawal; the statutory authority then withdraws.
**Reproduction / failing test sketch:** (static; not run) AO calls `hold_plan_publication(hold_kind="Accounting Officer correction request")`; AO calls `request_plan_withdrawal` (reuses the existing hold, creates the task); statutory approver calls `withdraw_approved_plan_for_correction`: refused. Tests (`test_plan_publication.py:314,430`) exercise hold and withdrawal separately, never in sequence.
**Impact:** The documented recovery path for a defective, unpublished approved plan cannot be completed once any hold exists; the plan stays locked.
**Verification:** CONFIRMED — `publication_pipeline.py:352-353` returns the existing Active hold unchanged, `treasury.py:157-158` builds the withdrawal task on that hold, `treasury.py:200` demands `hold_kind == "Withdrawal request"`, and the only code that sets `hold_state` to Released is `treasury.py:217` (grep `hold_state`), so a pre-existing "Accounting Officer correction request"/"Detected invalidity" hold has no exit; the AO hold is also the `hold_plan_publication` API default (`api.py:466-469`).

### AUD-PLN-003 — A classification correction does not mark or block an affected Draft Plan Item
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.1.6.6, PLN21-AC-004 (line 2650: "an affected mutable Draft item becomes Source correction required and cannot continue until explicitly dissolved and re-formed") · **Module(s):** PLN · **Sources:** trace-planning F-09
**Evidence**
- `PLN/services/dpp_classification.py:307-337` — `source_correction_required(plan_item_id)` implements the classification-aware test; a repository search finds callers only in `PLN/tests/test_dpp_classification_correction.py:278,290,332`.
- `PLN/services/plan_read.py:285-296` — the function actually used by `plan_workbench.py:396`, `plan_governance.py:427`, `publication_pipeline.py:227` and `plan_read.py:378` compares only the DPP entry's source signature (`plan_read.py:196-203`, fields in `ENTRY_SOURCE_FIELDS` carry no requirement type or category), so a classification correction never trips it.
**Rule:** PLN §5.1.6.6 and PLN21-AC-004 as quoted.
**Reproduction / failing test sketch:** (static; not run) Accept a DPP entry typed Works; `form_plan_items`; `correct_accepted_requirement_classification` to Non-consulting services; then save the item, request funding, sign and submit: no `PLN_SOURCE_CORRECTION_REQUIRED`; the approved plan carries Works while the effective classification is Services. Failing test: after the correction, `plan_read.source_correction_required(entry)` or `plan_readiness(...)["blockers"]` must report the item.
**Impact:** A plan can be approved with a procurement category, method, schedule and reservation computed on a superseded classification.
**Verification:** CONFIRMED — `dpp_classification.py:~440-540` writes only the correction row and returns `draft_items` as information (no item flag/state change), `dpp_classification.source_correction_required` is called only from tests, and the production gates use `plan_read.source_correction_required` (`plan_read.py:285-296`) whose source signature (`:196-203`) excludes classification; no readiness check compares the item's requirement type with `effective_classification`.

### AUD-PLN-004 — An absent reservation rule is reported as "Required allocation met" and does not block submission
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.5.3.1 (line 755: "Block Sign and submit Annual Plan where a verified mandatory planning allocation is unmet or its calculation basis is missing"; line 761: "absence of verified mandatory configuration cannot be reported as success"), PLN18-AC-069, PLN18-AC-072 · **Module(s):** PLN, core (regulatory reference) · **Sources:** trace-planning F-01
**Evidence**
- `kentender_core/kentender_core/services/regulatory_reference.py:1216-1231` — `_single_in_force` returns `None` unless exactly one in-force Reservation rule exists; `_empty` sets `reservation.target_percent: None` (line 1118).
- `PLN/services/readiness.py:308` — `"mandatory": bool(target)`, so no rule gives `mandatory: False`.
- `PLN/services/plan_read.py:422` — `if stage == "submission" and items and share["mandatory"]:` is the only place the reservation blocker is raised; and `plan_read.py:806-807` — `if not share["mandatory"] or share["met"]: reservation_result = "Required allocation met"`.
**Rule:** PLN §5.5.3.1 and PLN18-AC-072 as quoted ("Missing mandatory method/schedule/reservation configuration or basis blocks the affected submission/action").
**Reproduction / failing test sketch:** (static; not run) Site with no in-force "Reservation rules" version for the FY (or two overlapping ones). Complete a plan, obtain Finance confirmation, `submit_consolidated_plan` as HOPF: no `PLN_RESERVATION_SHORTFALL` or `PLN_REFERENCE_UNAVAILABLE`; U07 shows "Required allocation met". `test_plan_workbench.py:928` covers an in-force but unverified rule only.
**Impact:** The statutory reserved-procurement check is silently skipped when its configuration is missing or ambiguous, and the screen reports success.
**Verification:** CONFIRMED — `regulatory_reference.py:1170,1216-1231` yields no reservation doc unless exactly one in-force rule exists, so `target_percent` is None and `readiness.py:308` gives `mandatory: False`; `plan_read.py:422` raises the blocker only when `mandatory` and `plan_read.py:806-807` renders "Required allocation met" for `not mandatory`; no other blocker covers an absent/ambiguous rule (PLN §5.5.3.1 line 761 and PLN18-AC-072 quoted correctly).

### AUD-PLN-005 — Strategy snapshot is taken at Plan Item save, not at final approval, and ignores the plan's fiscal year
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §7.4 (line 1021: "The snapshot call belongs to final Plan approval, not item formation … must not append duplicate Strategy snapshot evidence on retry"), line 1019 ("At final statutory approval, call STR `create_strategy_snapshot` …"), PLN-RI-033, §7.3 (line 1008 lists "FY/Plan period" as an input) · **Module(s):** PLN, STR · **Sources:** trace-planning F-16; sweep-handoffs F-9
**Evidence**
- `PLN/services/plan_workbench.py:516` — `strategy_gateway.snapshot_objective(objective_id=..., correlation_key=f"{item.plan_item_id}:{idempotency_key}")` inside `save_plan_item`; the key changes with every save.
- `PLN/services/strategy_gateway.py:64-75` — `snapshot_objective` calls `create_strategy_snapshot`; repository search finds no other caller.
- `PLN/services/plan_governance.py:517` (`approve_annual_plan`) and `PLN/services/publication_pipeline.py:48-62` (`commit_approved_plan`) never call STR; `strategy_approval_snapshot` is set to an objective path string (`publication_pipeline.py:62`).
- `PLN/services/strategy_gateway.py:32` — `resolve_strategy_context(as_of_date=frappe.utils.today())`; the plan's fiscal year is not passed, and `:33-34` swallows every exception into "" (shown as "no objectives").
**Rule:** PLN §7.4 lines 1019-1021 as quoted. For the fiscal-year point, line 1021 also says a new selection "must use the current eligible Strategy version", so the date-based choice is arguable; the missing FY input (line 1008) is the stated divergence.
**Reproduction / failing test sketch:** (static; not run) Change one item's objective twice with different idempotency keys: two STR snapshots/audit events are created while the plan is a Draft; approve: no snapshot id is stored and a changed Strategy version with the same objective id passes `_require_positive_predicates`.
**Impact:** Duplicate Strategy evidence on every edit and no deterministic approval-time lineage match.

### AUD-PLN-006 — Successor submission and activation recheck neither scope lock nor consumed value; removal takes no reason
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.4.4 (lines 555-556, 560: "Also enforce §5.4.6 at successor submission and activation"), PLN-RI-070, PLN18-AC-035, §7.2 (line 975: `RemovePlanItemInSuccessor` takes "Draft successor item ID; reason") · **Module(s):** PLN · **Sources:** trace-planning F-19
**Evidence**
- `PLN/services/publication_pipeline.py:218-238` — `_activation_blockers` checks only source correction, `funding_is_current` and predecessor change; no consumed-quantity, funding-identity or `scope_lock` test (`scope_lock.guard` is never called from this module).
- `PLN/services/plan_publication.py:137-140` — `_no_downstream_use` is true unless an Active `Plan Drawdown Reference` exists; no Tender hand-off, commitment, contract or permanent scope-lock test.
- `PLN/services/plan_publication.py:143-161` and `PLN/api.py:519` — `remove_plan_item_in_successor(plan_item, expected_record_version, idempotency_key)` has no reason parameter.
**Rule:** PLN §5.4.4 items 4-5 and the sentence at line 560, as quoted; line 975.
**Reproduction / failing test sketch:** (static; not run) Authorise a Requisition on item X (scope lock set), reverse the drawdown fully, `begin_plan_update`, `remove_plan_item_in_successor(X)`: allowed (`_no_downstream_use` true) although X is scope-locked; submit and activate: no recheck. Also: a source added to X in the successor Draft before a Requisition is authorised on the predecessor passes activation after the lock appears.
**Impact:** A successor can drop or enlarge an item that downstream procurement already relies on, because the checks run only at edit time.

### AUD-PLN-007 — Approved removals re-queue the source; removed items stay in the reviewed totals but not in the published plan
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.4.4 item 6 (line 557: "Treat an approved removal as an explicit accounted-for exclusion; do not immediately place the same source back in the consolidation queue.") · **Module(s):** PLN · **Sources:** trace-planning F-18
**Evidence**
- `PLN/services/plan_publication.py:74` — at activation the removed item's allocations are set to `allocation_state = "Removed in successor"`.
- `PLN/services/plan_read.py:264-267` — `_allocated_dpp_entries` counts only allocations in ("Draft", "Active"); `PLN/services/plan_governance.py:200-209` (`_validate_ready_to_submit`) then refuses submission of the next successor Draft until every accepted entry is allocated, so the removed source returns to the queue.
- `PLN/services/plan_publication.py:161` — in the successor Draft, removal sets `item_state = "Removed in successor"` while allocations stay "Draft"; `PLN/services/readiness.py:171,276` count items `!= "Dissolved"` (affordability and the reservation denominator) and `PLN/services/plan_governance.py:139,195` freeze them into the reviewed snapshot, whereas `PLN/services/plan_json.py:117` publishes only Draft/Active items.
**Rule:** PLN line 557 as quoted; PLN §5.5.3.1 (reservation share is of "the exact current complete" plan value).
**Reproduction / failing test sketch:** (static; not run) Active V1 with item X; V2 Draft removes X; submit, approve, activate V2; open V3 Draft: X's source shows unallocated and V3 submission is refused until re-allocated. Separately, in V2 Draft X still counts in `line_totals` and in `reservation_allocations` frozen into `submitted_snapshot`, but is absent from the V2 published JSON.
**Impact:** Finance and the Accounting Officer review a larger plan than the one published, and a removal is not durable across the next update.

### AUD-PLN-008 — A correction request can be "Resolved" against the unchanged Active Version
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.4.5 (line 572: "Resolve is allowed only after a referenced correcting Plan Version is Active and the correction result identifies the replacement eligible lineage … Close without change requires a reason"), PLN18-UX-23 · **Module(s):** PLN, REQ · **Sources:** trace-planning F-24
**Evidence**
- `PLN/services/plan_requisition.py:760-830` — `resolve_plan_item_correction_request` requires only that `correcting_plan_version` is Active (`:794`) and holds an Active item with the replacement id; it never requires it to differ from, or follow, the request's own plan version.
- `PLN/services/plan_requisition.py:714-724` — the gate is the Procurement Planner role.
**Rule:** line 572 as quoted; releasing the hold "without change" is the separate reasoned outcome.
**Reproduction / failing test sketch:** (static; not run) Correction request recorded against Active V1; Planner calls `resolve_plan_item_correction_request(correction_request, correcting_plan_version=V1, ...)`: status Resolved, hold recomputed, `PlanItemCorrectionOutcome.v1` sent to REQ with replacement lineage equal to the stopped version. Tests cover only a Draft target and a genuine successor (`test_plan_requisition.py:659,707`).
**Impact:** A Planner can release the authorisation hold and tell REQ a correction happened with no change and no recorded reason.

### AUD-PLN-009 — ReturnPlanVersion records no collective resolution and caps the reason at 500
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §7.2 (line 971: "required collective resolution where applicable"), §6.1 (line 855: "Board and Council decisions retain their collective resolution reference"), §4.1 (line 145: other reasons "capped at 1,000") · **Module(s):** PLN · **Sources:** trace-planning F-02 (item-context part dropped, see below)
**Evidence**
- `PLN/services/plan_governance.py:624` — signature `(task, reason, task_token, idempotency_key, user)`; `PLN/api.py:405` exposes the same four parameters; the stored decision is created with `return_reason=reason` and no `resolution_reference` (`plan_governance.py:642` calling `_decision`, which accepts `resolution_reference` at line 395).
- `PLN/services/plan_governance.py:631` — `if not (10 <= len(reason) <= 500)`.
- By contrast `approve_annual_plan` (`:535-536`) and `withdraw_approved_plan_for_correction` (`treasury.py:194-195`) require the reference for collective capacities.
**Rule:** PLN lines 971, 855, 145 as quoted.
**Reproduction / failing test sketch:** (static; not run) Site configured with a Board/Council statutory capacity: the statutory recorder calls `return_plan_version(task, reason="…10+ chars…", task_token, key)`: accepted, decision stored without a resolution reference. A 600-character reason: `PLN_ENTRY_INCOMPLETE`.
**Impact:** A collective statutory return carries no resolution evidence; reasons between 501 and 1,000 characters are refused.

### AUD-PLN-010 — Segregation chain omits SavePlanVersionDetails and the funding-reuse request
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §6.4 (line 892: "Author Annual Plan content, form/dissolve items, request Finance, or sign formal submission" blocks later Finance/AO/statutory decisions) · **Module(s):** PLN · **Sources:** trace-planning F-04
**Evidence**
- `PLN/services/planning_authorization.py:68-78` — `PLANNER_CHAIN_COMMANDS` lists FormPlanItems, DissolvePlanItem, SavePlanItem, ConfirmSplittingAdvisory, RequestPlanFundingConfirmation, SubmitConsolidatedPlan, SubmitCorrectedPlan, RemovePlanItemInSuccessor, BeginPlanUpdate; not `SavePlanVersionDetails` (journaled at `PLN/services/plan_workbench.py:568`).
- `PLN/services/plan_finance.py:189-199` — the reuse path of `RequestPlanFundingConfirmation` is journaled against a `Plan Finance Basis Reuse` document; `planning_authorization.py:380` builds `journal_targets = set(chain) | set(items) | set(tasks)`, which excludes it. A correction Draft's owner is excluded from the Planner set (`planning_authorization.py:373-374`).
**Rule:** PLN §6.4 as quoted.
**Reproduction / failing test sketch:** (static; not run) On a correction Draft, user P (Planner and Finance Confirmation Officer) calls `request_plan_funding_confirmation` and the earlier basis is reused (`action: confirmation_reused`); a different user signs and submits. `is_segregated(P, ACTION_FINANCE_DECIDE, plan_version=...)` is False and P can confirm funding for a plan P requested.
**Impact:** A narrow maker-checker gap on correction chains; other chain commands are covered.

### AUD-PLN-011 — Splitting confirmation is free text with no related-item set, rule Version or stale-finding check
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §7.2 (line 963: "reasoned response … Retain assessment evidence; … stale finding rejected"), PLN18-AC-074 (line 2436: "retains related records, rule Version and justification") · **Module(s):** PLN · **Sources:** trace-planning F-20
**Evidence**
- `PLN/services/plan_workbench.py:575-598` — `confirm_splitting_advisory(plan_version, confirmation, ...)` stores a 10-500 character string in `splitting_confirmation` (`:585,592`); no finding id, related item set or rule Version is accepted or stored; no stale-finding rejection.
**Rule:** lines 963 and 2436 as quoted.
**Reproduction / failing test sketch:** (static; not run) Confirm the advisory with any 10-character text while the related items later change: accepted; the stored value cannot show which items or rule Version it answered.
**Impact:** Legally material splitting accountability is not evidenced as specified (the advisory is advisory; mandatory method rules still block).

### AUD-PLN-012 — "Fixture-verified — not production law" passes every verification gate (spec gap)
**Severity:** Medium · **Classification:** SPEC GAP — decision for the owner: may a rule or profile whose status is `Fixture-verified — not production law` satisfy the production gates, or must a site mode reject it? · **Doc:** PLN v1.29 §10.2 (line 1444: "do not display the profile as a verified legal reference"), §5.5.3.1 line 761 ("absence of verified mandatory configuration cannot be reported as success"); CFG-CHG-002 v0.18 CFG17-AC-002 (line 1031) · **Module(s):** PLN, core · **Sources:** trace-planning F-26
**Evidence**
- `kentender_core/kentender_core/services/procurement_settings.py:42-43` — `VERIFICATION_FIXTURE = "Fixture-verified — not production law"`.
- `PLN/services/profiles.py:38` — `VERIFIED_STATUSES = (settings.VERIFICATION_FIXTURE, settings.VERIFICATION_VERIFIED)`, used at `PLN/services/readiness.py:291`, `PLN/services/profiles.py:98` and `PLN/services/plan_requisition.py:147`.
**Rule:** the documents prohibit displaying fixture rules as verified and forbid reporting missing verified configuration as success, but do not say whether the fixture status satisfies a gate.
**Reproduction / failing test sketch:** (static; not run) Seed the Open Tender profile and reservation rule with the fixture status; every submission and Requisition gate treats them as verified.
**Impact:** A production site carrying fixture-status rules passes all verification gates with no switch to reject them.

### AUD-PLN-013 — Late-activation read labels ordinary successors as late and offers an action that then fails
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §4.7 (line 275: explanation belongs to the initial Plan Version), PLN18-UX-29 (line 2532: "normal in-year successor not mislabelled late") · **Module(s):** PLN · **Sources:** trace-planning F-28
**Evidence**
- `PLN/services/plan_read.py:2357-2359` — `applicable = bool(year_start and activated_at and getdate(activated_at) >= getdate(year_start))` for any Version; `:2381` `"can_explain": applicable and has_site_role(AO)`.
- `PLN/services/plan_governance.py:249-250` — `record_late_activation_explanation` refuses a successor (`based_on_version` set) with `PLN_STALE_WRITE`.
**Rule:** PLN18-UX-29 as quoted.
**Reproduction / failing test sketch:** (static; not run) Activate Version 2 mid-year; `get_publication_task` for it returns `late_activation.applicable: True, can_explain: True` for the AO; submitting an explanation yields `PLN_STALE_WRITE`.
**Impact:** Misleading late label and a dialog that cannot succeed.

### AUD-PLN-014 — Planning raises a Finance notification where the spec says Planning sends none
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §7.7 (line 1044: "Notification: none from Planning in any row"), PLN23-AC-001 (line 2676), PLN27-AC-007 (line 2715: "Planning sends no notification") · **Module(s):** PLN · **Sources:** trace-planning F-08
**Evidence**
- `PLN/services/plan_finance.py:232,236-251` — `_notify_finance_officers` calls `notifications.notify_task(... event_type="planning.finance_requested" ...)` after every `RequestPlanFundingConfirmation` that creates a task.
**Rule:** lines 1044, 2676, 2715 as quoted.
**Reproduction / failing test sketch:** (static; not run) Request funding confirmation on a complete plan: a `planning.finance_requested` notification log is emitted for each Finance Confirmation Officer.
**Impact:** A producer the approved spec excludes is active.

### AUD-PLN-015 — A withdrawn initial departmental plan leaves a stale Need position at NDS
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §5.1.2 position table (line 342: "an initial plan withdrawn before acceptance → No update needed") · **Module(s):** PLN, NDS · **Sources:** trace-planning F-10
**Evidence**
- `PLN/services/dpp_lifecycle.py:699` — `envelope.bump(root, current_state="Withdrawn", current_version="")`; line 704 then calls `publish_need_positions`.
- `PLN/services/needs_intake.py:287` — `if not root or not root.current_version: return "", []`, so no position is sent.
**Rule:** line 342 as quoted.
**Reproduction / failing test sketch:** (static; not run) Need N is "After current submission" against a returned initial Draft; HoD withdraws the Draft; NDS keeps "After current submission" for N.
**Impact:** The Need page can keep telling the Planner to "Finish reviewing" a plan that no longer exists.

### AUD-PLN-016 — Return issue entry ids are not validated
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 PLN19-UX-009 (line 2563: "validated exact entry or whole-submission scope") · **Module(s):** PLN · **Sources:** trace-planning F-12
**Evidence**
- `PLN/services/dpp_validation.py:93-96` — `"entry_id": cstr(row.get("entry_id")).strip() or None` is stored as given; it is never compared with the submission's entry snapshots. The gate is the Procurement Planner role.
**Rule:** line 2563 as quoted.
**Reproduction / failing test sketch:** (static; not run) `return_departmental_plan(task, issues=[{"entry_id": "DPPE-NOPE", "correction_required": "x"}], ...)` is recorded.
**Impact:** A return can point the department at a non-existent entry.

### AUD-PLN-017 — PLN_BASELINE_LOCKED is raised for only two edit shapes
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** PLN v1.29 §8 / PLN18-AC-118 (a locked baseline "cannot be changed by any command once the owning Version has left Draft") · **Module(s):** PLN · **Sources:** trace-planning F-06
**Evidence**
- `PLN/services/plan_workbench.py:386-390` — `if version.version_status != "Draft" and any(k in values for k in ("baseline_invitation_date", *schedule.PERIOD_FIELDS)): fail("PLN_BASELINE_LOCKED")`; every other edit on a non-Draft Version raises `PLN_STALE_WRITE` (line 390).
**Rule:** the cited criterion; the edit is still refused, only the contract code differs.
**Reproduction / failing test sketch:** (static; not run) `save_plan_item` changing `title` on an Active Version returns `PLN_STALE_WRITE`, not `PLN_BASELINE_LOCKED`.
**Impact:** Wrong error code only.

### AUD-PLN-018 — WithdrawDepartmentalSubmission cannot withdraw a Submitted plan; spec is ambiguous (spec gap)
**Severity:** Low · **Classification:** SPEC GAP — decision for the owner: may the HoD withdraw a Submitted (awaiting Procurement review) departmental plan? · **Doc:** PLN v1.29 §5.1.5 (line 389 "Mutable candidate"), §7.2 (line 954 "submitted evidence never reopened"), §7.7 (line 1048: the Procurement review item clears on "Accepted, returned or withdrawn") · **Module(s):** PLN · **Sources:** trace-planning F-14
**Evidence**
- `PLN/services/dpp_lifecycle.py:693` — `if version.version_status not in ("Draft", "Returned") or cstr(root.current_version) != version.name: fail("PLN_DPP_STALE", ...)`.
**Rule:** the document says both that only a mutable candidate is withdrawn and that the review item clears on withdrawal, which presumes a Submitted plan can be withdrawn.
**Reproduction / failing test sketch:** (static; not run) HoD calls `withdraw_departmental_submission` on a Submitted version: `PLN_DPP_STALE`.
**Impact:** A submitted plan awaiting review cannot be recalled; the implementation follows the narrower reading.

### AUD-PLN-019 — Combination rule: PLN §5.6.2 and PLN18-AC-055 disagree; code adds an undocumented origin restriction
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** PLN v1.29 §5.6.2 (line 784: "same FY, Procurement Budget Line and currency"), PLN18-AC-055 (line 2417: "reject different Budgets or currencies") · **Module(s):** PLN · **Sources:** trace-planning F-21
**Evidence**
- `PLN/services/plan_workbench.py:104-109` — `COMBINATION_DIMENSIONS` = budget (the Procurement Budget, not the line), classification, unit, origin (Need versus direct requirement); the comment at lines 98-103 records "the Procurement Budget (not the individual line) carries the currency".
- `PLN/tests/test_plan_workbench.py:250` combines sources across two budget lines.
**Rule:** the two document sentences name different dimensions; no document sentence names "origin".
**Reproduction / failing test sketch:** n/a (document inconsistency; code follows the acceptance criterion, not §5.6.2).
**Impact:** Testers cannot tell which rule is authoritative; the origin restriction blocks combining a Need-origin and a direct source of the same category.

### AUD-PLN-020 — Technical-operator "Your turn" contradicts PLN27-AC-009 (spec defect)
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** PLN v1.29 §5.7 (line 811) and §7.7 (line 1061) versus PLN27-AC-009 (line 2717) · **Module(s):** PLN · **Sources:** trace-planning F-32
**Evidence**
- `PLN/services/next_step.py:476-482` — the authorised technical operator gets `KIND_YOUR_TURN` ("Retry publication" / "Check the publication result").
- PLN lines 811 and 1061 give that operator "Your turn"; PLN27-AC-009 says "Administrator and System Manager never receive Your turn or a fix from any Planning next-step answer."
**Rule:** the document contradicts itself; the code follows §5.7 (the comment at `next_step.py:479-480` calls it the one named exception).
**Reproduction / failing test sketch:** n/a (document inconsistency).
**Impact:** None at runtime; one of the two sentences must be corrected.

### AUD-PLN-021 — Statutory withdrawal for correction skips the segregation check (spec gap)
**Severity:** Low · **Classification:** SPEC GAP — decision for the owner: is "Withdraw for correction" covered by §6.4's "approve/return as statutory authority"? · **Doc:** PLN v1.29 §6.4 (line 892) · **Module(s):** PLN · **Sources:** trace-planning F-33
**Evidence**
- `PLN/services/treasury.py:176-210` — `withdraw_approved_plan_for_correction` calls `require_site_role(ROLE_PLAN_STATUTORY_APPROVER, actor)` and checks the collective reference, but never `require_not_segregated(... ACTION_STATUTORY_DECIDE ...)`; `approve_annual_plan` does (`plan_governance.py:532`).
**Rule:** §6.4 lists approve and return, not withdrawal.
**Reproduction / failing test sketch:** (static; not run) A user who signed the plan as Planner and holds the statutory role calls `withdraw_approved_plan_for_correction` on a held plan: not refused for segregation.
**Impact:** Possible maker-checker gap on the statutory withdrawal decision, depending on the owner's reading.

### AUD-PLN-022 — Departmental plan is auto-created on Need acceptance (spec gap)
**Severity:** Low · **Classification:** SPEC GAP — decision for the owner: may Need acceptance create the department's Draft plan without an Author/HoD "Start departmental plan" command? · **Doc:** PLN v1.29 §5.1.5 (line 383: "No DPP; permitted initial intake | Start departmental plan | Author or HoD"), §4.2 invariant 1 ("no creation from a read") · **Module(s):** PLN · **Sources:** trace-planning F-34
**Evidence**
- `PLN/services/dpp_autostart.py:57-70` — `on_need_event` calls `dpp_lifecycle.ensure_departmental_plan` on every `DepartmentalNeedAccepted.v2`.
- `PLN/services/dpp_lifecycle.py:244-319` — creates the root and Draft Submission 1 with no intake-window check and records the accepting user as actor; the docstring states this is deliberate and says "the intake window still governs every submission".
**Rule:** the document describes only the manual start.
**Reproduction / failing test sketch:** (static; not run) Accept a Need for a department with no plan: a Departmental Plan root and Draft version exist afterwards without any Planning command.
**Impact:** None found beyond an undocumented event-driven creation; pinned by `test_dpp_autostart.py:109-179`.

## Dropped / downgraded

- trace-needs C-01 (client `user` parameter) — owned by xc-authz item 1; C-06 (DocPerm write/create) — xc-authz item 4; C-09 (projection endpoints open to any human Planner, caller-chosen values) — xc-authz item 12 (the consumer-machinery half is in AUD-NDS-010); C-22 (float quantity, no UOM precision) — xc-core item 7; C-23 (replay answered before authorisation) — xc-core item 11. Not written here.
- trace-needs P-01..P-06 (grouped Partial/Untested rows: CFG verdict re-implementation and `NDS_CONTEXT_REQUIRED` for a disabled FY, hash omits UOM basis, decision keeps assignment id but no snapshot, `Need Withdrawal Request` not registered with technical search, workspace paging, untested transitions) — not promoted: each is either a missing test or a Low partial with no defect shown against a quoted rule; not re-verified individually.
- trace-needs C-05's stale-source sub-claim (row 79) is folded into AUD-NDS-012 rather than written separately.
- trace-planning F-02 — downgraded High to Medium (AUD-PLN-009). The "affected_item_version_id" part was DROPPED: PLN §7.2 line 971 calls it "optional" and PLN19-UX-010 keeps whole-Plan return valid, so its absence is not a defect. The missing collective resolution on return and the 500-character cap were re-verified.
- trace-planning F-05 (segregation pairs untested) — missing tests are not findings.
- trace-planning F-13 — merged into AUD-NDS-009; sweep-handoffs F-9 — merged with F-16 into AUD-PLN-005 (its fiscal-year argument is kept but noted as arguable, because PLN line 1021 asks for the "current eligible Strategy version").
- trace-planning F-22 (Open Tender pre-selected on item formation) — DROPPED: the pre-selection is only an initial value; `PLN/services/readiness.py:399-428` still blocks submission with `PLN_METHOD_NOT_ADMISSIBLE` / `PLN_REFERENCE_UNAVAILABLE` when no complete profile permits it, so PLN18-AC-101 is met at the gate.
- trace-planning F-32 second half ("technical operator has no My Work item") — DROPPED: no rule in PLN §7.7 requires one and the claim was not provable from a quoted sentence.
- trace-planning F-16, F-19 — severity lowered from "Medium-High" to Medium after re-reading (checks exist at edit time; the gaps are at submission/activation).
- trace-planning F-11, F-17, F-27, F-29, F-30, F-31, F-03, F-07, F-15 — owned by xc-authz / xc-core per the ownership map; not written here.
- sweep-handoffs F-7 (disposition event contract) — owned by hnd; AUD-NDS-009 states the same enum root cause from the Needs/Planning side and cross-references it.

## Calibration notes

Needs
- **kwargs transport fields — present.** `NDS/api.py:62-74` defines `_TRANSPORT_FIELDS = frozenset({"cmd","csrf_token","_"})` and `_command_args`; `save_need_draft` (`api.py:77-90`) and the return/accept/decline endpoints (`api.py:112-126`) strip them before calling the keyword-only services. Pinned by `T-CT:667-797` (dynamic call plus an AST scan, as reported by trace-needs; not re-run). Separate hazard: the explicit `user` parameter of the same endpoints (xc-authz item 1).
- **Intake scope — present.** The offered year is the one effectively open year (`NDS/services/context.py:118-137`, core `site_configuration.py:1315-1337`, which takes `limit_page_length=1` among flagged years at line 1324) and the offered departments are the Author's own units (`context.py:170-192`); browsing years come only from visible Needs. Residual: `_open_intake_year` depends on CFG's one-open-year invariant.
- **Late-accepted Need — present for initial acceptance, absent for successor acceptance.** Intake projection, positions and the backfill patch exist (`NDS/services/usage.py:436-489`; `PLN/services/needs_intake.py:279-345`; `PLN/services/dpp_autostart.py:70-81`); a successor acceptance publishes no position and drops the Need from the source list (AUD-NDS-001).
- **Optimistic lock — present.** The editor stamps the next `expected_version` synchronously from the save response (`DepartmentalNeeds.vue:784-800`); the server bumps `record_version` in `_bump` and refuses a mismatch or empty value in `_check_version` (`NDS/services/lifecycle.py:254-266`). The Python layer has no direct test of save-then-submit; the browser spec is the only pin (trace-needs).
- **AO/HOPF reads — partly present.** `can_view` gives AO/HOPF the Submitted, Accepted and Not-taken-forward states only (`permissions.py:136-140`, `constants.py:159`), but `get_need` exposes the Draft successor of an Accepted Need (AUD-NDS-003).

Planning
- **Reservation denominator — present, one gap.** Denominator is the eligible value of the exact plan Version (`PLN/services/readiness.py:249-321`, docstring at 253-264: the Budget is not an input); the review reads the frozen snapshot (`plan_governance.py:195`). Gap: an absent rule reports success (AUD-PLN-004).
- **Frozen snapshot read — present.** `reservation_allocations` is written into `submitted_snapshot` at `plan_governance.py:195` and read back from it by the governance reads (`plan_read.py:2075-2076`).
- **Four base designations — present.** `PLN/services/readiness.py:37` `BASE_RESERVATION_CATEGORIES` and `readiness.py:125-128` (offered categories); enforcement in `plan_workbench.py` `_validate_reservation` is per trace-planning and was not re-opened.
- **Departmental correction route — service layer present.** No service lets the Planner change a purchase's cost (`plan_workbench.py:45-52` allow-list; allocations copied from accepted values); over-budget lines offer Request budget revision and Request departmental plan update (`PLN/services/guards.py:140-161`). The guarantee holds only at the service layer while Desk/REST writes on Plan Source Allocation are open (owned by xc-authz item 4).
- **Late-need positions — present** (see Needs calibration); gaps AUD-NDS-001, AUD-PLN-015.
- **Three-counter vocabulary — present as display only**, wire keys unchanged (`needs_intake.py:48-62`, `dpp_lifecycle.py` submission numbers, `plan_read.py` "Version n"); no test asserts it globally.
