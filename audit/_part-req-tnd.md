# Part req-tnd — Requisition (AUD-REQ) and Tenders (AUD-TND) findings

Method: every finding below was re-opened at the cited file and line on 6 Oct 2026 (static reading only; nothing was run). Docs: REQ-CHG-001 v1.14 (`docs/mvp-1-r1/06_requisitions/KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_14.md`), TPR-CHG-001 v0.17 (`docs/mvp-1-r1/11_tenders/KenTender_TPR-CHG-001_Tenders_v0_17.md`). Path prefixes: `REQ/` = `kentender_procurement/kentender_procurement/procurement_requisitions/`, `TND/` = `kentender_procurement/kentender_procurement/tenders/`, `CORE/` = `kentender_core/kentender_core/` (all under the repo root `apps/kentender_v1/`).

| ID | Severity | Title |
|---|---|---|
| AUD-REQ-001 | High | `record_handoff_consumption` endpoint lets a Procurement Officer or HOPF mark any authorised handoff consumed by a Tender that does not exist |
| AUD-REQ-002 | High | HoD maker-checker is enforced only on the Awaiting branch; a Draft can be certified by an Author who later became HoD (and "preparing directly" is never checked) |
| AUD-REQ-003 | Medium | Preparer can also be the Procurement authoriser (no "self-authorisation" check beyond `submitted_by`) |
| AUD-REQ-004 | Medium | HoD submission from "Awaiting Department Approval" skips the section 7.2 rechecks |
| AUD-REQ-005 | Medium | Category applicability of technical characteristics is not enforced server-side |
| AUD-REQ-006 | Medium | Brand/restrictive-term Blocking finding is applied only to technical TEXT rows |
| AUD-REQ-007 | Medium | Draft and in-review requisitions are readable by every site-wide role |
| AUD-REQ-008 | Medium | "Purchase ready for requisition" does not clear for an occupied item and the start surfaces carry no hold wording |
| AUD-REQ-009 | Medium | `funding_source` is not sent to Budget and is not in the handoff |
| AUD-REQ-010 | Medium | Supporting files: no private/ownership check, "Not scanned" accepted, no download predicate |
| AUD-REQ-011 | Low | Item/service dates are validated at write time only |
| AUD-REQ-012 | Low | `GetRequisitionHistory` omits drawdown/reservation/reversal/consumption evidence; outbox is never relayed |
| AUD-REQ-013 | Low | Closed error codes with no raise site; "internally contradictory" Blocking finding unimplemented |
| AUD-REQ-014 | Low | Planning outcome sequence gaps are not detected |
| AUD-REQ-015 | Low | HOPF lead directive survives only the immediate successor Draft |
| AUD-REQ-016 | Low | Direct read of Budget's Funding Reservation table and import of a private Planning helper |
| AUD-TND-001 | High | An addendum can become effective (deadline rewritten, definition activated) after the submission period has closed |
| AUD-TND-002 | High | A late final channel confirmation strands the Tender with no governed exit |
| AUD-TND-003 | Medium | Accounting Officer can still authorise publication after returning the package; the return item is orphaned |
| AUD-TND-004 | Medium | Non-material addendum rows for clarification deadline and others have no effect on the Tender or definition |
| AUD-TND-005 | Medium | The conflicting-confirmation audit event is written and then rolled back with the refusal |
| AUD-TND-006 | Medium | A Planning refusal of the invitation actual is recorded and never retried |
| AUD-TND-007 | Medium | Package-digest recomputation makes every unauthorised Tender Version fragile to any new CATALOGUE control |
| AUD-TND-008 | Medium | "Prepared by" for segregation is only the person who started the Tender |
| AUD-TND-009 | Medium | Cancellation grounds are a code-owned, unverified list |
| AUD-TND-010 | Medium | Publication/addendum evidence is accepted with "Not scanned" |
| AUD-TND-011 | Low | Reopen of an approved Tender skips the compatibility recheck |
| AUD-TND-012 | Low | Doc says one publication authorisation per approved Version; code allows several after withdrawal |
| AUD-TND-013 | Low | A true concurrent StartTender returns a conflict error, not the first Tender's identity |
| AUD-TND-014 | Low | Back saves a dirty Draft silently; no "Leave without saving?" |
| AUD-TND-015 | Low | "Contact administrator" control is absent |
| AUD-TND-016 | Low | Late-amendment window is a hard-coded 7 days, not a configured/verified rule |
| AUD-TND-017 | Low | Two TPR section 5.2 / AC rules have no field or server rule behind them |
| AUD-TND-018 | Low | Certified lead and contributing OU identifiers are not on `GetTender` |
| AUD-TND-019 | Low | "Authorise publication" is offered when no publication rule exists |

---

### AUD-REQ-001 — `record_handoff_consumption` endpoint lets a Procurement Officer or HOPF mark any authorised handoff consumed by a Tender that does not exist
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §9.2, §10.2 `RecordHandoffConsumption` · **Module(s):** Requisitions, Tenders · **Sources:** trace-requisition F-04
**Evidence**
- `REQ/api.py:271-280` — `@frappe.whitelist()` `record_handoff_consumption(handoff_name, tender, tender_version, template_key, template_version, idempotency_key)`; gate is only `any(authz.has_site_role(role) for role in TENDER_CALLER_ROLES)`.
- `REQ/services/requisition_roles.py:37` — `TENDER_CALLER_ROLES = (ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)`.
- `REQ/services/handoff.py:105-137` — forwards `tender` straight into `doc.tender = cstr(tender)`, sets `consumed_at`, calls `records.release_slot(root)`; no lookup that the Tender exists or that the call is inside a Tender transaction.
- `REQ/doctype/authorised_requisition_handoff/authorised_requisition_handoff.json:76-77` — `tender` is a plain `Data` field, not a Link, so Frappe does not validate it either.
- `REQ/services/authorise.py:183-185` — `if handoff_doc.consumed_at: fail("REQ_HANDOFF_CONSUMED", ...)`: once set, revocation is permanently refused.
- `REQ/tests/test_requisitions_api_requests.py:101` — the suite itself consumes a handoff over HTTP with the fabricated id `TND-0001`.
- `TND/services/draft_commands.py:102-103` — a real `start_tender` on that handoff now hits `if handoff_doc.consumed_at: fail("TND_HANDOFF_CONFLICT")`.
**Rule:** REQ §9.2 "Tender Preparation consumes the exact handoff idempotently through REQ's `RecordHandoffConsumption` owner command within the same transaction as Draft Tender creation ... If TPR creation fails, consumption rolls back too." §10.2: "Owner-authorized TPR command ... atomic with Tender creation". HOPF is not a Tender starter (Tenders refuses HOPF at start, `TND/tests/test_lifecycle.py:126-131`).
**Reproduction / failing test sketch:** (static; not run) 1. On the test site authorise a requisition (`fx.authorise`). 2. As a user holding Procurement Officer (or Head of Procurement Function) POST `kentender_procurement.procurement_requisitions.api.record_handoff_consumption` with `handoff_name=<handoff>`, `tender="NOPE"`, `tender_version="x"`, `template_key="IT-EQUIPMENT-OPEN-V1"`, `template_version="1.1"`, a fresh `idempotency_key` -> expect refusal; today returns `action: consumed`. 3. As HOPF call `revoke_unconsumed_authorisation` -> `REQ_HANDOFF_CONSUMED`. 4. As an Officer call Tenders `start_tender(handoff)` -> `TND_HANDOFF_CONFLICT`.
**Impact:** One Procurement Officer can strand any authorised requisition: the Tender can never be started from that handoff, the HOPF can no longer revoke it, and the Budget reservation behind it cannot be released through the governed route. Reachable by any holder of the two roles.
**Verification:** CONFIRMED — `REQ/api.py:271-280` gates only on the two TENDER_CALLER_ROLES and `REQ/services/handoff.py:105-137` sets `doc.tender` from the request with no Tender lookup; no hook, controller or Link field intervenes, and `authorise.py:183-185` then blocks revocation.

### AUD-REQ-002 — HoD maker-checker is enforced only on the Awaiting branch; a Draft can be certified by an Author who later became HoD (and "preparing directly" is never checked)
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §7.3 bullet 1, §7.1 (Draft / Submit to Procurement), REQ19-AC-045 · **Module(s):** Requisitions · **Sources:** trace-requisition F-02; sweep-sod F9
**Evidence**
- `REQ/services/lifecycle.py:261-262` — `if cstr(version.prepared_by) == actor and cstr(version.prepared_capacity) != ROLE_HEAD_OF_USER_DEPARTMENT: fail("REQ_SOD_BLOCKED")`, inside the `if root.current_state == "Awaiting Department Approval":` branch that starts at line 253.
- `REQ/services/lifecycle.py:267-270` — `elif root.current_state == "Draft": ... lock(root, version, package_version, target_status="Submitted to Procurement")`: no check on `prepared_by` or `prepared_capacity`; the only gate is `_lead_hod(root, actor)` at line 247.
- `REQ/services/draft_commands.py:56-65,127,177` — `prepared_capacity` is chosen by trying HoD first across *any* contributing unit, then Author, and is stored; it records the capacity the actor happened to hold, not the capacity exercised in the lead unit.
- `REQ/tests/test_home_provider.py:258-270` — builds exactly the Author-turned-HoD case but only asserts `assertRaises(Exception)` on the Awaiting path.
**Rule:** §7.3 "A Departmental Author cannot complete the Head of User Department decision on the same Version unless the actor is independently assigned the Head of User Department role and prepared the Requisition directly in that capacity." §7.1 row "Draft | Submit to Procurement | Head of User Department preparing directly". REQ19-AC-045 "Dual-role actors exercise exact current capacity with no self-authorisation."
**Reproduction / failing test sketch:** (static; not run) 1. A holds Departmental Author in the lead OU only; A prepares and completes a Draft (`prepared_capacity = "Departmental Author"`). 2. Grant A Head of User Department in the lead OU (`administration.grant(...)`, as `test_home_provider.py:262`). 3. As A call `submit_requisition_to_procurement(requisition, expected_record_version, key)` while the root is still `Draft` -> succeeds, `submitted_by = A`, a Procurement task is created, no departmental-approval task ever existed. 4. The same call after `send_for_department_approval` raises `REQ_SOD_BLOCKED`. Expected: step 3 raises `REQ_SOD_BLOCKED`. Also: a different lead HoD can certify an Author's Draft directly, skipping the departmental task, because "preparing directly" is never tested.
**Impact:** An Author who is also (or becomes) HoD certifies their own work for the whole department, defeating the first maker-checker stage; the HOPF authorisation (a different person, `authorise.py:104`) still stands, which is why this is High rather than Critical.
**Verification:** CORRECTED — core case holds (`REQ/services/lifecycle.py:253-270`: the `prepared_by`/`prepared_capacity` check exists only in the Awaiting branch; the Draft branch only calls `lock`). Secondary claim (a different lead HoD certifying an Author's Draft) is narrower than written: `REQ/services/read.py:473-476` deliberately offers Submit to Procurement on a Draft to any lead HoD who is not a lead Author, so that is a spec-ambiguity (§7.1 "preparing directly") rather than a pure code bug; severity High kept for the Author-turned-HoD case.

### AUD-REQ-003 — Preparer can also be the Procurement authoriser (no "self-authorisation" check beyond `submitted_by`)
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** REQ-CHG-001 v1.14 REQ19-AC-045, §7.3 bullet 4, §5.2 · **Module(s):** Requisitions · **Sources:** trace-requisition F-02 (F-02b part)
**Evidence**
- `REQ/services/authorise.py:103-104` — `if cstr(version.submitted_by) == actor: fail("REQ_SOD_BLOCKED")` is the only actor comparison; `prepared_by` is never compared.
- `REQ/services/lifecycle.py:213-235` — the actor who sends a Draft for department approval is written only to the command journal (`_journal`), not to the Version or a decision.
**Rule:** §7.3 bullet 4 only blocks the authoriser from being "recorded as the departmental submitting authority". REQ19-AC-045 adds "HOPF alone cannot prepare a departmental Draft. Dual-role actors exercise exact current capacity with no self-authorisation." The documents do not say whether the preparer (or sender) of a Draft may later be its Procurement authoriser.
**Decision the owner must make:** may an actor who prepared or sent a Draft authorise it as HOPF (dual-role Author + HOPF)? If not, `authorise_requisition` must also compare `prepared_by` and a recorded "sent by" actor.
**Reproduction / failing test sketch:** (static; not run) 1. User U holds Departmental Author (lead OU) and Head of Procurement Function; U prepares and sends a Draft; a different lead HoD approves and submits. 2. U calls `authorise_requisition` -> succeeds (`submitted_by` is the HoD).
**Impact:** A dual-role actor can carry a requisition from preparation to funded authorisation with only one other person (the HoD) in the chain.

### AUD-REQ-004 — HoD submission from "Awaiting Department Approval" skips the section 7.2 rechecks
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §7.2 · **Module(s):** Requisitions · **Sources:** trace-requisition F-05
**Evidence**
- `REQ/services/lifecycle.py:253-266` — the Awaiting branch only checks the task, the SoD rule and flips the already locked Version/package to "Submitted to Procurement" with `envelope.bump(...)`; it never calls `lock()` (lines 78-96: Planning eligibility, `compatibility.require_compatible`, `validation.validate`, digest) or `validation.validate`.
- `REQ/services/lifecycle.py:267-270` — only the Draft branch calls `lock(...)`.
**Rule:** §7.2 "Before departmental routing **or submission**, the server rechecks: ... current Planning eligibility and open balance; every field and row control ...; zero Blocking findings; supporting-file security and digest; product suitability ...; and canonical content digest."
**Reproduction / failing test sketch:** (static; not run) 1. Send a Draft for department approval. 2. Before the HoD acts, make the item ineligible (record a Planning correction request on it, or switch the template release off). 3. HoD calls `submit_requisition_to_procurement(..., task=<open task>)` -> succeeds and creates a Procurement task. Expected: `PLN_ITEM_AUTHORISATION_HELD`/`REQ_PRODUCT_UNSUPPORTED`/`REQ_PLAN_INELIGIBLE`.
**Impact:** An unauthorisable Version reaches the HOPF queue; the authorise-time recheck (`authorise.py:40-61`) still blocks money movement, so the cost is a dead task and a misleading status.

### AUD-REQ-005 — Category applicability of technical characteristics is not enforced server-side
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §6.3, REQ19-AC-009, §14.3 · **Module(s):** Requisitions · **Sources:** trace-requisition F-06
**Evidence**
- `REQ/services/catalogue.py:89` and `:151` — `Characteristic.applies(equipment_category)` and `characteristics_for(category)` exist; a repo-wide grep over non-test `*.py` in the module finds no caller (only `tests/test_catalogue.py:60-61`).
- `REQ/services/draft_commands.py:507-520` (`_visible_technical`) and `:731-743` (`add_technical_requirement`) look the key up in `CATALOGUE_BY_KEY` and validate the value only; the item category is never consulted.
- `REQ/services/validation.py:234-236` — only checks that the key exists in the catalogue (`CONTROL_INVALID` otherwise).
- `REQ/services/catalogue.py:123` — `print_speed` is declared `frozenset({"Printer"})`.
- `REQ/tests/test_draft_commands.py:159-172` — pins that after changing Laptop to Desktop the Confirmed rows are kept.
**Rule:** §6.3 "Only characteristics applicable to the selected category are offered." REQ19-AC-009 "Only category-applicable characteristics and their released controls are accepted." §14.3 "Changing an equipment category revalidates its characteristics."
**Reproduction / failing test sketch:** (static; not run) 1. Draft with Monitor items. 2. `add_technical_requirement(values={"characteristic_key": "print_speed", "applies_to_scope": "All items", "value": 30, ...})` -> accepted as a Confirmed row; passes `validation._technical_support`; enters the handoff `technical_requirements`. Expected `REQ_CONTROL_INVALID`.
**Impact:** A Printer-only obligation can be imposed on monitors (and Laptop-only rows survive a category change), so the Tender inherits requirements that do not apply to the goods.

### AUD-REQ-006 — Brand/restrictive-term Blocking finding is applied only to technical TEXT rows
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §6.3 rules, §6.5 Blocking findings, REQ19-AC-018 · **Module(s):** Requisitions · **Sources:** trace-requisition F-29 row 75
**Evidence**
- `REQ/services/validation.py:250` — `if ch.control == TEXT and restrictive_terms.is_restrictive(text_value, reason=row.get("reason", "")):` is the only call site of `is_restrictive` in the module (grep over `services/*.py`).
- Free-text fields that reach the Tender and are not scanned: item `item_name`/`intended_use`, acceptance `pass_condition`, related-service `required_result`/`quantity_or_coverage`, supporting-material `title`/`purpose`, and the `other` value of non-TEXT controls (`catalogue.py:210-212,226-229`).
- `REQ/services/restrictive_terms.py:13-24` — the detector exists (brand and platform lists).
**Rule:** §6.3 "A brand, model, proprietary certification or named technology triggers a Blocking finding unless the text includes an approved `or equivalent` treatment and a recorded functional reason." §6.5: "a brand or restrictive term lacks permitted equivalent treatment" is Blocking. REQ19-AC-018 "Brand/restrictive wording without permitted equivalence treatment blocks submission."
**Reproduction / failing test sketch:** (static; not run) 1. Draft; add an acceptance requirement with `pass_condition="Delivered units must be Dell Latitude 5440 devices"` (or an item named "Dell Latitude 5440"). 2. `validate_requisition` -> no `RESTRICTIVE_TERM` finding; submission and authorisation succeed. Expected: Blocking finding.
**Impact:** Brand-restrictive wording, a legally sensitive defect in a tender specification, passes every REQ gate outside the one control type scanned and flows into the handoff.

### AUD-REQ-007 — Draft and in-review requisitions are readable by every site-wide role
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** REQ-CHG-001 v1.14 §8 role table, §7.5 invariant 15 · **Module(s):** Requisitions · **Sources:** trace-requisition F-08
**Evidence**
- `REQ/services/requisition_roles.py:27` — `SITE_WIDE_ROLES = (HOPF, Procurement Planner, Procurement Officer, Auditor)`.
- `REQ/services/requisition_authorization.py:124-142` (`require_requisition_reader`) returns for any of those roles for any state; `:262-271` (`_site_wide_condition`) gives them an unrestricted list condition.
- `REQ/services/read.py:166-195` — the workspace `register` includes Draft roots for readers; `REQ/services/draft_commands.py:924-930` (`validate_requisition`) returns findings and a preview digest to any reader.
- `REQ/tests/test_requisition_authorization.py:65-69` — pins the Auditor reading a prepared requisition as intended.
**Rule:** §8: Procurement Officer "No Draft right in Requisitions by virtue of this role"; Planner "Neutral read of Planning lineage and drawdown projection"; HOPF "View the complete submitted Requisition". §7.5 invariant 15: unauthorised requests reveal no record. The document is silent on whether "no Draft right" and "neutral read" cover reading Draft content.
**Decision the owner must make:** may Planner, Procurement Officer and Auditor (site-wide) read Draft and in-review content, or only Submitted/Authorised/Revoked states (as the Accounting Officer oversight read is restricted by `OVERSIGHT_READ_STATES`)?
**Reproduction / failing test sketch:** (static; not run) As a Procurement Officer, `get_requisition_workspace()` lists every department's Drafts in `register`; `get_requisition_record(<draft>)` returns the editor projection read-only.
**Impact:** Unsubmitted departmental work (requirements, quantities, values) is visible site-wide.

### AUD-REQ-008 — "Purchase ready for requisition" does not clear for an occupied item and the start surfaces carry no hold wording
**Severity:** Medium · **Classification:** CODE DEFECT (tension with doc §13.13; see note) · **Doc:** REQ-CHG-001 v1.14 §9.1C, REQ112-AC-002, REQ112-AC-004 · **Module(s):** Requisitions · **Sources:** trace-requisition F-09; F-29 rows 158-160
**Evidence**
- `REQ/services/read.py:228-246` — when `records.open_root_for(...)` returns a root, the row is still appended with an `existing` link unless that root is in the actor's own `your_work` (line 236, Drafts only); Awaiting, Submitted and Authorised roots therefore leave the item in the Ready list.
- `REQ/services/read.py:238-246` and `:305-356` (`get_start_preview`) — neither the ready row nor the preview contains a hold field; the word "hold" occurs in `read.py` only at 634-663 (authorisation task).
- `kentender_procurement/kentender_procurement/public/js/procurement_requisitions/components/WorkspaceScreen.vue:165-166` (existing rows listed separately) and `StartDialog.vue`: no hold wording (grep `-i hold` over both returns nothing).
**Rule:** §9.1C "Clears when: ... a Requisition root occupies the stable item's open slot"; REQ112-AC-002 "The item clears when a root occupies the open slot"; §9.1C Correction hold "Its row states the existing hold wording from §9.1 beside **Start requisition**"; REQ112-AC-004 "remains listed with the hold wording". Note: §13.13 also defines an "Existing open requisition" state with action "Open existing requisition", so the doc is not fully consistent about whether an occupied item stays in the list as a pointer.
**Reproduction / failing test sketch:** (static; not run) 1. Author sends a Draft for department approval; `get_requisition_workspace()` still lists the Plan Item in `ready_to_start` with `existing`. 2. Record a Planning correction request on a different eligible item; its Ready row carries no hold text and the start preview has no hold state.
**Impact:** Users are told a purchase is ready when a requisition already occupies it, and are not warned that authorisation is on hold until the Authorise step.

### AUD-REQ-009 — `funding_source` is not sent to Budget and is not in the handoff
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §5.12, §9.1A · **Module(s):** Requisitions, Budget, Planning · **Sources:** trace-requisition F-10; F-29 row 154
**Evidence**
- `REQ/services/authorise.py:62-72` (`funding_rows`) — each Budget row has `budget_line, plan_source_allocation, drawdown_line_id, source_organisation_unit, amount` and no `funding_source`.
- `kentender_budget/kentender_budget/services/budget_check_reserve_contracts.py:160-170` normalises a missing `funding_source` to `""`, and `:196` — `if row["funding_source"] and row["funding_source"] != entry["line_version"].funding_source:` (BUD-BR-008) never fires for REQ.
- `REQ/services/handoff.py:49,62-89` — per-line `budget_line` only; no funding source anywhere in the payload.
- `kentender_procurement/kentender_procurement/procurement_planning/services/plan_requisition.py:234-259` — the Planning projection carries `budget_line` but no funding source (grep `funding_source` in `procurement_planning/doctype` also finds nothing).
**Rule:** §5.12 "planned method, schedule, Budget Line and funding source". §9.1A "REQ supplies its exact Version ... funding source/currency/precision with the array."
**Reproduction / failing test sketch:** (static; not run) Authorise any requisition and read `Authorised Requisition Handoff.payload_json`: no `funding_source`; call `check_funding` with a deliberately wrong `funding_source` for the same lines to show Budget would refuse it, whereas REQ never supplies one.
**Impact:** Budget's allocation-versus-line funding-source equality is never exercised for requisitions and the Tender does not see the funding source; the Budget Line itself fixes the source, so the blast radius is limited.

### AUD-REQ-010 — Supporting files: no private/ownership check, "Not scanned" accepted, no download predicate
**Severity:** Medium · **Classification:** SPEC GAP (scan fallback) with CODE DEFECT (private/ownership) · **Doc:** REQ-CHG-001 v1.14 §5.10, §8 final paragraph · **Module(s):** Requisitions, Core · **Sources:** trace-requisition F-15
**Evidence**
- `CORE/services/file_integrity.py:71-74,82` — `scanner_result` returns `NOT_SCANNED` ("Not scanned — no scanner configured", line 27) when no scanner hook answers; `check_file` (lines 89-119) rejects only an `Infected` verdict (line 119-120) and never reads `File.is_private`, `attached_to_*` or owner.
- `REQ/services/files.py:20-30` and `REQ/services/draft_commands.py:889-893` — `add_supporting_material` runs `files.check_file(values.get("file"))` on any File name supplied and stores `file_digest`.
- `kentender_procurement/kentender_procurement/hooks.py:192` — the only `kt_file_scanners` entry is the BDS simulation-only test scanner; `hooks.py:457-459` registers only `File.on_trash`, no read predicate for Files.
**Rule:** §5.10 `file_id` "Required private Frappe File"; `file_digest` "Generated after malware and readability checks." §8 "Every list, count, direct route, file download and command applies the same registered predicate." Decision for the owner: whether a file with "Not scanned" may be attached or must fail closed when no scanner is configured.
**Reproduction / failing test sketch:** (static; not run) 1. As user A upload a public (`is_private = 0`) `.pdf`. 2. As user B (Departmental Author) call `add_supporting_material` naming A's File -> accepted, digest returned, check_result "Not scanned — no scanner configured". 3. Name any other readable private PDF File of another module -> also accepted and its SHA-256 is stored on the requisition (a content oracle).
**Impact:** A requisition can reference a public or someone else's file as a governed obligation document with no malware verdict; reviewers downstream may be unable to read it, and its digest becomes part of the immutable Version.

### AUD-REQ-011 — Item/service dates are validated at write time only
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §5.6, §5.8 · **Module(s):** Requisitions · **Sources:** trace-requisition F-16
**Evidence**
- `REQ/services/draft_commands.py:244-245` — `save_requisition_summary` assigns `version.latest_delivery_date` with no comparison to existing item or service dates.
- `REQ/services/draft_commands.py:295-297` and `:789-791` — the item/service date checks run only when those rows are written.
- `REQ/services/validation.py:158-177` — compares only the Version date to the Plan boundary and required-by date.
**Rule:** §5.6 `latest_delivery_date` "Defaults from Version; may be earlier, never later." §5.8 `completion_date` "not later than the package delivery date."
**Reproduction / failing test sketch:** (static; not run) Items dated 30 Sep, Version date 30 Sep; `save_requisition_summary(values={"latest_delivery_date": "<15 Sep>"})`; `validate_requisition` -> no finding; submit and authorise succeed; the handoff carries items dated after the package date.
**Impact:** The Tender inherits item dates later than the requisition's own latest delivery date.

### AUD-REQ-012 — `GetRequisitionHistory` omits drawdown/reservation/reversal/consumption evidence; outbox is never relayed
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §10.1, §9.2, §15 · **Module(s):** Requisitions · **Sources:** trace-requisition F-17; F-29 row 242
**Evidence**
- `REQ/services/read.py:914-926` — returns versions, decisions, correction outcomes and `Requisition Event` rows only.
- `REQ/services/handoff.py:105-137` — consumption writes no event or history row.
- `REQ/services/events.py:58` — `acknowledge` has no caller anywhere in the app; `EVENT_WITHDRAWN` (events.py:21) has no publisher (publishers: `authorise.py:145` authorised, `authorise.py:201` revoked, `correction.py:143`, `lifecycle.py:435`).
**Rule:** §10.1 `GetRequisitionHistory` "Versions, decisions, drawdown, reservation, reversal, upstream-correction and handoff-consumption evidence." §9.2 "publishes ... through the transactional outbox." §15 audit list includes "outbox publication and retry evidence; Tender handoff consumption".
**Reproduction / failing test sketch:** (static; not run) Authorise then consume; `get_requisition_history` has no consumption or reservation entry; `Requisition Event` rows stay `Pending` indefinitely.
**Impact:** An auditor cannot reconstruct consumption or reservation history from the module's own history read; events are persisted but never delivered or acknowledged.

### AUD-REQ-013 — Closed error codes with no raise site; "internally contradictory" Blocking finding unimplemented
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §11, §6.5 · **Module(s):** Requisitions · **Sources:** trace-requisition F-21; F-29 rows 82, 202, 206
**Evidence**
- `REQ/services/errors.py:25,30` — `REQ_QUANTITY_MISMATCH` and `REQ_REQUIREMENT_RESTRICTIVE` are defined; no `fail("REQ_QUANTITY_MISMATCH"...)`/`REQ_REQUIREMENT_RESTRICTIVE` call exists in the module; the conditions surface as findings `QUANTITY_MISMATCH` (`validation.py:215`) and `RESTRICTIVE_TERM` (`:250`) and are raised as `REQ_BLOCKING_FINDINGS`.
- `REQ/services/validation.py` has no rule for "a requirement is internally contradictory" (grep `contradict` finds nothing).
**Rule:** §11 closed error list incl. `REQ_QUANTITY_MISMATCH` ("Item and drawdown quantities do not reconcile. Show the affected line.") and `REQ_REQUIREMENT_RESTRICTIVE`; §6.5 Blocking: "a requirement is internally contradictory".
**Reproduction / failing test sketch:** (static; not run) Make item quantities not equal a drawdown line; `lifecycle.send_for_department_approval` raises `REQ_BLOCKING_FINDINGS` (detail holds `QUANTITY_MISMATCH`), never `REQ_QUANTITY_MISMATCH`.
**Impact:** A client keyed on the documented codes never receives them; the contradictory-requirement block cannot fire.

### AUD-REQ-014 — Planning outcome sequence gaps are not detected
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §9.1B (dedup/ordering paragraph), REQ19-AC-067 · **Module(s):** Requisitions, Planning · **Sources:** trace-requisition F-22
**Evidence**
- `REQ/services/correction.py:122-127` — only `if last is not None and int(event["producer_sequence"]) <= int(last): return _invalid(...)`; a skipped sequence is accepted silently and no replay/pending path exists.
**Rule:** §9.1B "Gap/out-of-order delivery triggers owner replay or an authoritative versioned snapshot; preserve last-confirmed status with a pending indication."
**Reproduction / failing test sketch:** (static; not run) Record outcome with `producer_sequence=1`, then one with `producer_sequence=5` for the same `correction_request_id` -> accepted with no pending indication.
**Impact:** A lost intermediate outcome is never detected; requesters see a status that may not reflect Planning's.

### AUD-REQ-015 — HOPF lead directive survives only the immediate successor Draft
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** REQ-CHG-001 v1.14 §7.3A · **Module(s):** Requisitions · **Sources:** trace-requisition F-23
**Evidence**
- `REQ/services/lifecycle.py:140` — `"lead_routing_directive": lead_directive or None` on the copied Version; a later Return calls `copy_draft_successor` without a directive, so it is cleared.
- `REQ/services/draft_commands.py:204-212` — `_refresh_lead` returns early only `if version.lead_routing_directive`, otherwise recomputes the default and can change `root.lead_org_unit_id`.
**Rule:** §7.3A "Refresh the derived default after a Draft drawdown change, unless an explicit HOPF return directive fixes the new lead." The doc does not say how long a directive binds. Decision for the owner: does the directive persist across later returns?
**Reproduction / failing test sketch:** (static; not run) HOPF changes lead to OU-B (directive set); OU-B's HoD returns the successor; a drawdown amount save on the new Draft recomputes the lead back to the largest-value OU.
**Impact:** The lead department can silently revert after a second return.

### AUD-REQ-016 — Direct read of Budget's Funding Reservation table and import of a private Planning helper
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** REQ-CHG-001 v1.14 §3, §19; AGENTS.md §2 (cross-app via published service/API) · **Module(s):** Requisitions, Budget · **Sources:** trace-requisition F-28; F-29 row 5
**Evidence**
- `REQ/services/read.py:745` — `frappe.db.get_value("Funding Reservation", line.get("reservation_id"), "generated_reference")` reads a Budget table directly (Budget is a different app, `kentender_budget`).
- `REQ/services/funding_gateway.py:76` — `from kentender_procurement.procurement_planning.services.budget_gateway import _system_principal` imports a private (underscore) helper of another module (same app, but not a published surface).
(Reads of `Annual Plan`, `Plan Item`, `Tender` at `read.py:186,188,435,738` are inside the same app `kentender_procurement`, so only the Budget read is cross-app.)
**Rule:** REQ §3/§19 cross-app access through published owner services; AGENTS.md §2 "Cross-app interaction uses an explicit public service or API owned by the relevant app."
**Reproduction / failing test sketch:** static: grep `Funding Reservation` in `procurement_requisitions/services/read.py`.
**Impact:** Display-only coupling to Budget's table layout; no money moves.

---

### AUD-TND-001 — An addendum can become effective (deadline rewritten, definition activated) after the submission period has closed
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §4.8, §5.1 (Close submission period), §5.6 · **Module(s):** Tenders, Bid Submission · **Sources:** trace-tenders F-03
**Evidence**
- `TND/services/submission_close.py:57-93` — `close_tender_submission_period` closes a `Published — open` Tender and freezes `effective_submission_deadline` into the handoff; it does not look at addenda in `Awaiting publication confirmation`.
- `TND/services/channel_confirmation.py:160-161` — `confirm_channel` refuses only `if root.overall_status == "Cancelled" and subject_type != SUBJECT_CANCELLATION`; there is no `Published — open` guard on addendum confirmations.
- `TND/services/addenda.py:452-465` — `_all_channels_confirmed` sets the addendum `Issued`, calls `bid_definition.activate(root, doc.successor_bid_definition, at=issued_at)` (line 461) and `envelope.bump(root, submission_deadline=doc.revised_submission_deadline)` (lines 463-465).
**Rule:** §4.8: the addendum, its deadline and successor definition become effective "only when the HOPF confirms every required channel"; §5.1 "Close submission period ... Sets Submission period ended and emits immutable downstream contract"; §5.6 "BDS cannot see an awaiting-confirmation definition as current."
**Reproduction / failing test sketch:** (static; not run) In `TND/tests/test_open_period.py` style: 1. Issue a deadline-extending addendum with channels outstanding. 2. Advance `frappe.flags.kt_tenders_clock` past the original deadline; `submission_close.close_due_submission_periods()` -> Tender `Submission period ended`, handoff frozen. 3. HOPF confirms the last addendum channel -> `Tender.submission_deadline` moves later and a new Effective definition is activated on a closed Tender. Expected: refusal or a defined outcome; today no `TND_*` error.
**Impact:** The closed Tender's deadline and effective definition diverge from the frozen submission handoff that Bid Submission and Bid Opening already consumed, a legally material inconsistency on a live procurement.
**Verification:** CONFIRMED — `TND/services/addenda.py:452-465` activates the definition and rewrites `submission_deadline` with no tender-status guard, `TND/services/channel_confirmation.py:160-161` guards only Cancelled, and `submission_close.py:57-93` never consults awaiting addenda.

### AUD-TND-002 — A late final channel confirmation strands the Tender with no governed exit
**Severity:** High · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §5.5 item 6, §7 · **Module(s):** Tenders · **Sources:** trace-tenders F-04
**Evidence**
- `TND/services/publication.py:156-159` — `confirm_tender_published` fails `TND_PUBLICATION_PERIOD_INVALID` when `published_at` plus the minimum period is after the deadline.
- `TND/services/publication.py:208-211` — `withdraw_publication_authorisation` refuses once any channel is Confirmed (`TND_PUBLICATION_WITHDRAWAL_BLOCKED`).
- `TND/services/lifecycle.py:290-291` — `reopen_approved_tender` refuses once `root.publication` is set (`TND_PUBLICATION_STARTED`).
- `TND/services/cancellation.py:52-56` — `_require_open` allows cancellation only from `Published — open`.
- `TND/tests/test_publication.py:438-456` — the test's own next step is to re-submit the same final channel with an earlier default `available_at` to get past the refusal.
**Rule:** §5.5(6) "If the applicable minimum period would be breached, the Tender cannot become Published until a lawful revised deadline is issued in the same immutable publication package." No §7 command issues such a revised deadline.
**Decision the owner must make:** name the command that issues a revised deadline inside the same publication package (or a governed withdrawal) for the case where three channels are already confirmed.
**Reproduction / failing test sketch:** (static; not run) Authorise publication; confirm three channels; confirm the fourth with `available_at` later than deadline minus minimum days -> `TND_PUBLICATION_PERIOD_INVALID`; `withdraw_publication_authorisation` -> `TND_PUBLICATION_WITHDRAWAL_BLOCKED`; `reopen_approved_tender` -> `TND_PUBLICATION_STARTED`; `cancel_tender` -> `TND_STALE_VERSION`.
**Impact:** The Tender can only progress if the HOPF attests a different (earlier) availability time than the real one, which invites false attestation; otherwise it is stuck in "Publication authorised".
**Verification:** CONFIRMED — the final confirmation's failure rolls back (test `TND/tests/test_publication.py:438-456` leaves the row Awaiting), and every exit is closed: `publication.py:208-211` withdraw, `lifecycle.py:290-291` reopen, `cancellation.py:52-56` cancel, `correction.py:52-53` request-correction (`root.publication` set) and `publication.py:250` return_approved_tender.

### AUD-TND-003 — Accounting Officer can still authorise publication after returning the package; the return item is orphaned
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §5.1, TPR16-AC-015 · **Module(s):** Tenders · **Sources:** trace-tenders F-02
**Evidence**
- `TND/services/read.py:414` — only the read hides the control (`... and not handoffs.open_for(root, handoffs.RETURNED_BY_AO) ...`).
- `TND/services/publication.py:49-77` — `authorise_tender_publication` checks status, segregation, `ao_task` (only if `task` is passed), digest; no test of an open `RETURNED_BY_AO` hand-off. `return_approved_tender` cancels the AO authorisation task (`publication.py:255`) so `ao_task` is `None` afterwards.
- `TND/services/publication.py:108` — on authorisation only `REVIEW_WITHDRAWN` hand-offs are closed; `TND/services/lifecycle.py:290-291,301` — Reopen (which would close `RETURNED_BY_AO`) is refused once `root.publication` is set.
**Rule:** §5.1 "While the return is open the Accounting Officer has neither **Authorise publication** nor **Return**." TPR16-AC-015 "...is offered neither **Authorise publication** nor **Return**. Reopen, or a Requisition correction, clears the hand-off."
**Reproduction / failing test sketch:** (static; not run) 1. AO `return_approved_tender(reason>=20 chars)`. 2. AO `authorise_tender_publication(tender, expected_record_version=<returned record_version>, idempotency_key=<new>)` with no `task` -> commits. 3. HOPF My Work still shows "Review Tender ... returned by the Accounting Officer"; Reopen is refused with `TND_PUBLICATION_STARTED`. Expected: step 2 raises `TND_STALE_VERSION`.
**Impact:** A server call (not the UI) lets the AO bypass the HOPF correction they just requested; the HOPF is left with a task that can never clear.

### AUD-TND-004 — Non-material addendum rows for clarification deadline and others have no effect on the Tender or definition
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §3, §4.8, §4.9, §5.6 · **Module(s):** Tenders · **Sources:** trace-tenders F-06
**Evidence**
- `TND/services/addenda.py:71-72` — `clarification_deadline` and `submission_deadline` are offered as non-material `affected_reference` rows.
- `TND/services/bid_definition.py:58` (`_ADDENDUM_TARGETS`, otherwise unused) and `:281-301` — `apply_addenda` applies only `delivery_location`, `tender_title`, `inspection_location`, `contract_contact_office`, `pre_tender_meeting`, plus the submission deadline when `deadline_extension_required`.
- `TND/services/addenda.py:462-465` — updates only `submission_deadline`; no code writes `Tender.clarification_deadline` after publication (grep `clarification_deadline` in `TND/services` shows writes only at `lifecycle.py:144` and `publication.py:110`).
- `TND/services/clarifications.py:73-76` — `TND_CLARIFICATION_LATE` is judged against `root.clarification_deadline`.
**Rule:** §4.8/§5.6 the successor definition is built "from the current effective definition plus this exact addendum"; §3/§4.9 a clarification at or after the stated clarification deadline is rejected.
**Reproduction / failing test sketch:** (static; not run) Draft an addendum with `affected_reference_key="clarification_deadline"`, a revised value, reason (20+ chars) and materiality statement; issue and confirm all channels. The issued notice states the new clarification deadline, but `Tender.clarification_deadline` and the Effective definition are unchanged, so `receive_tender_clarification` still rejects questions after the old deadline.
**Impact:** The published addendum says one thing and the system enforces another, so bidders can be told a deadline moved that the system still applies; likewise a corrected `inspection_location` is free text without validation (`addenda.py:190-204`).

### AUD-TND-005 — The conflicting-confirmation audit event is written and then rolled back with the refusal
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §5.8 item 10, §12.1 · **Module(s):** Tenders · **Sources:** trace-tenders F-07 (the generic denial-event root cause is owned by the xc-core part, "denial events never written / rolled back on throw")
**Evidence**
- `TND/services/channel_confirmation.py:183-190` — `events.emit(... event_type="ConfirmationConflictRejected" ...)` is immediately followed by `fail("TND_PUBLICATION_ALREADY_CONFIRMED", ...)`; the emit is outside `envelope.atomic`, so it lives in the request transaction that the raised error rolls back (Frappe rolls back an uncaught exception in a whitelisted request; static reasoning, not run).
- `TND/tests/test_publication.py:347-354` — passes only because the test catches the exception inside one test transaction before asserting `events.exists(...)`.
**Rule:** §5.8(10) "a conflicting confirmation is rejected and preserved for audit." §12.1 "Rejected commands record a security or operational audit fact where policy requires it."
**Reproduction / failing test sketch:** (static; not run) Via HTTP call `confirm_publication_channel` for a Confirmed channel with a different `available_at`; get the refusal; query `Tender Event` for `ConfirmationConflictRejected` -> expected one row, today none.
**Impact:** The audit trail required for conflicting confirmations is lost in production although the test suite shows it as present.

### AUD-TND-006 — A Planning refusal of the invitation actual is recorded and never retried
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §5.5 item 7, TPR09-AC-079, TPR-IMP-033 · **Module(s):** Tenders, Planning · **Sources:** trace-tenders F-08
**Evidence**
- `TND/services/planning_gateway.py:50-55` — on `ProcurementPlanningError` the event is `mark_rejected` and the function returns `{"ok": False, ...}`.
- `TND/services/publication.py:142-148,175` — `confirm_tender_published` returns early once `publication_status == Published`, and the only caller of `publish_invitation_actual` is `publication.py:175`; the only other caller is a test (`TND/tests/test_publication.py:381`).
- `kentender_procurement/kentender_procurement/hooks.py:481-500` — the scheduler jobs listed include no Planning-event retry.
**Rule:** TPR09-AC-079 "Owner-contract failure ... supports safe idempotent recovery." §5.5(7) "Planning receives exactly one actual invitation event for `published_at`."
**Reproduction / failing test sketch:** (static; not run) Make `schedule.record_tender_milestone_actual` raise `ProcurementPlanningError` during the final channel confirmation; the Tender becomes Published, the `TenderPublished` event is `Rejected`, nothing later re-sends it and Planning never records the actual date.
**Impact:** Planning's schedule can permanently miss the actual invitation date for a published Tender.

### AUD-TND-007 — Package-digest recomputation makes every unauthorised Tender Version fragile to any new CATALOGUE control
**Severity:** Medium · **Classification:** CODE DEFECT (latent) · **Doc:** TPR-CHG-001 v0.17 §4.2, TPR16-AC-018 · **Module(s):** Tenders · **Sources:** trace-tenders F-05
**Evidence**
- `TND/services/controls.py:247-259` — `normalise` emits a key (None when blank) for every field in `CATALOGUE`; `TND/services/serializer.py:293-300` (`officer_state`) normalises the stored payload through it.
- `TND/services/controls.py:41` — the only exemption is `DIGEST_OMIT_WHEN_EMPTY = ("shortened_period_reason",)`, applied at `TND/services/serializer.py:451-453`.
- `TND/services/lifecycle.py:238` (approval) and `TND/services/publication.py:77` (authorisation) compare the live recomputed `package_digest` with the stored one; `TND/services/review.py:155-160` recomputes the inherited snapshot digest live.
- `TND/services/errors.py:76` — the failure surfaces as the generic `TND_STALE_VERSION` ("Another user changed this Tender. Reload before continuing.").
**Rule:** §4.2 `package_digest` covers "every inherited/officer/generated value"; v0.16 left the shortened-period reason out while empty so earlier Versions "still verify"; TPR16-AC-018.
**Reproduction / failing test sketch:** (static; not run) Monkeypatch one extra optional entry into `controls.CATALOGUE`; recompute `serializer.package_digest` for a stored Submitted or Approved Version; it differs from `version.package_digest`, so `approve_tender_package`/`authorise_tender_publication` fail `TND_STALE_VERSION`. Published Tenders are not affected (nothing recomputes the digest after publication; confirmations compare stored digests, `publication.py:150-151`).
**Impact:** The next control added to the catalogue (or any change to grouping or the v1.4 translation in `snapshot._handoff_v14_names`) silently invalidates every in-flight Tender, with a misleading error, until each is returned or reopened and reworked.

### AUD-TND-008 — "Prepared by" for segregation is only the person who started the Tender
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §6, TPR09-AC-035/AC-039 · **Module(s):** Tenders · **Sources:** trace-tenders F-13; sweep-sod F5
**Evidence**
- `TND/services/draft_commands.py:128` — `prepared_by` set only at StartTender; `:152-189` (`save_tender_draft`) requires `authz.require_officer` and never records the editor; `TND/services/lifecycle.py:87,185,299` carry `prepared_by` forward unchanged.
- `TND/services/lifecycle.py:205-211` and its callers (`lifecycle.py:225`, `publication.py:62,252`) test only `prepared_by`, `submitted_by`, `approved_by`.
**Rule:** §6 "The person who prepared or submitted a Version cannot approve it as HOPF ... Checks use the immutable Version audit, not role labels alone." The document does not define "prepared" (creator or every editor). Decision for the owner: does "prepared" include every person who saved a value (journalled in `TenderDraftSaved` events, which carry the editor)?
**Reproduction / failing test sketch:** (static; not run) Officer O1 starts the Tender; user H (Procurement Officer + Head of Procurement Function) edits values with `save_tender_draft`; O1 submits; H calls `approve_tender_package` -> allowed (`prepared_by = O1`, `submitted_by = O1`).
**Impact:** A person who substantively authored the package can approve it as HOPF.

### AUD-TND-009 — Cancellation grounds are a code-owned, unverified list
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §4.10, §5.7, TPR09-AC-066 · **Module(s):** Tenders · **Sources:** trace-tenders F-09
**Evidence**
- `TND/services/cancellation.py:34-45` — `GROUNDS_SOURCE = "... s.63(1) — wording verification pending (FOLLOW_UPS FU-06)"` and a fixed tuple of eight grounds.
- `TND/services/cancellation.py:71,119` — `if ground not in GROUND_LABELS: fail(...)` is the only validation (recommend and cancel); no applicability, verification status or configuration lookup.
**Rule:** §4.10 `ground` "One configured, verified lawful ground from the applicable rule set." §5.7 "A configured verified lawful ground and specific reason are mandatory." The document names no reference kind or configuration surface for the grounds. Decision for the owner: where the verified ground set is configured (and whether the code list stays as a fallback until verified).
**Reproduction / failing test sketch:** (static; not run) AO `cancel_tender(ground="FORCE_MAJEURE", reason=<20+ chars>, ...)` on any `Published — open` Tender -> accepted.
**Impact:** A final, irreversible cancellation can rest on a ground whose wording the code itself marks unverified.

### AUD-TND-010 — Publication/addendum evidence is accepted with "Not scanned"
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §4.7, TPR09-AC-050 · **Module(s):** Tenders, Core (shared root cause with AUD-REQ-010) · **Sources:** trace-tenders F-21
**Evidence**
- `TND/services/channel_confirmation.py:172` — `file_integrity.check_file(cstr(evidence_file).strip(), fail=...)` is the evidence check for every channel confirmation.
- `CORE/services/file_integrity.py:71-74,82,118-120` — with no scanner answering, `check_result` is "Not scanned — no scanner configured" and only an `Infected` verdict fails.
- `kentender_procurement/kentender_procurement/hooks.py:192` — the only `kt_file_scanners` entry is the simulation-only BDS test scanner.
**Rule:** TPR09-AC-050 "Uploaded evidence is scanned, digested and retained; failed or rejected uploads cannot confirm a channel." The document does not say whether unscanned evidence may confirm publication. Decision for the owner: fail closed when no scanner is configured, or accept and display "Not scanned".
**Reproduction / failing test sketch:** (static; not run) On a site without `kt_bds_simulation_environment`, confirm a publication channel with a valid PDF; the confirmation succeeds with `evidence_check_result = "Not scanned — no scanner configured"`.
**Impact:** The legal publication evidence may be an unscanned file; the first channel confirmation that publishes a Tender does not meet AC-050 as written.

### AUD-TND-011 — Reopen of an approved Tender skips the compatibility recheck
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §5.3 · **Module(s):** Tenders · **Sources:** trace-tenders F-01
**Evidence**
- `TND/services/lifecycle.py:296` — `template_binding.require_bound(version, "continue")` is the only guard; `compatibility.require_supported` appears at `lifecycle.py:125` (submit), `:233` (approve) and `publication.py:70` (authorise) but not in `reopen_approved_tender` (`lifecycle.py:278-311`).
- `TND/services/compatibility.py:90-130` — the nine checks run on the stored snapshot plus the bound release (`support`) and the live `_is_county_entity()`, so only release support and the Site county flag can differ at reopen.
**Rule:** §5.3 "Compatibility is rechecked at Draft creation, submission, approval, reopening and publication authorisation against the exact immutable owner facts applicable to that action."
**Reproduction / failing test sketch:** (static; not run) Approve a Tender with a County-residents restriction; change `Site Procuring Entity.entity_is_county` to 0 (or switch the release's county support off); HOPF `reopen_approved_tender` -> succeeds, creating a Draft that will fail only at submit.
**Impact:** Limited: the copied Draft is rechecked at submission, so the rule violation is a missed early refusal.

### AUD-TND-012 — Doc says one publication authorisation per approved Version; code allows several after withdrawal
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** TPR-CHG-001 v0.17 §4.6 vs §5.11 · **Module(s):** Tenders · **Sources:** trace-tenders F-14
**Evidence**
- Doc line 312 (§4.6) "One publication authorisation per approved Version."; doc line 692 (§5.11, Withdraw) "Tender reopened for correction or a new authorisation decision."
- `TND/services/publication.py:222` — withdrawal sets `publication=None` and returns the root to `Approved`; `:56-60` then lets the same approved Version be authorised again, creating a second `Tender Publication` row.
**Rule:** the two doc statements conflict; the owner must state "one active authorisation" or forbid re-authorisation.
**Reproduction / failing test sketch:** (static; not run) Authorise, withdraw before any confirmation, authorise again -> two `Tender Publication` rows reference one `Tender Version`.
**Impact:** Ambiguity about the number of publication records per Version; no money or approval is affected.

### AUD-TND-013 — A true concurrent StartTender returns a conflict error, not the first Tender's identity
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 TPR09-AC-007 · **Module(s):** Tenders, Requisitions · **Sources:** trace-tenders F-15
**Evidence**
- `TND/services/draft_commands.py:96-103,135` — the "already consumed/existing" checks run before any lock; two concurrent starts both build a Tender inside `envelope.atomic("start")` and the loser hits `REQ_HANDOFF_CONFLICT` in consumption, surfaced as `TND_HANDOFF_CONFLICT` (rolled back).
**Rule:** TPR09-AC-007 "Concurrent or repeated `StartTender` requests for one handoff produce one Tender and return its identity."
**Reproduction / failing test sketch:** (static; not run) Two sessions call `start_tender` for one handoff with different idempotency keys at the same time; one returns `TND_HANDOFF_CONFLICT`; sequential repeats return `existing` (`TND/tests/test_lifecycle.py:118-124`).
**Impact:** Exactly one Tender survives; the loser sees an error rather than the identity, a retry resolves it.

### AUD-TND-014 — Back saves a dirty Draft silently; no "Leave without saving?"
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §11.1 item 10, §11.3 · **Module(s):** Tenders · **Sources:** trace-tenders F-17
**Evidence**
- `kentender_procurement/kentender_procurement/public/js/tenders/Tenders.vue:475-485` — `onEditorBack` calls `api.saveTenderDraft(...)` when `editorRef.value.isDirty()` and then navigates; grep `Leave without saving` over `public/js/tenders` (excluding `dist/`) finds nothing.
**Rule:** §11.1(10) "Cancel and Back close the current transient surface without saving." §11.3 "Closing a page with unsaved ... changes gives **Leave without saving?** with Stay / Leave. No autosave is implied."
**Reproduction / failing test sketch:** (static; not run) Edit a Tender details field and press Back: a `SaveTenderDraft` call and a `TenderDraftSaved` event are produced and no prompt appears.
**Impact:** An unintended edit is persisted and audited without the user's confirmation.

### AUD-TND-015 — "Contact administrator" control is absent
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §11.2 (Contact administrator), TPR10-IMP-007 · **Module(s):** Tenders · **Sources:** trace-tenders F-18
**Evidence**
- Doc line 1466 "Contact administrator | Opens the configured support instruction; it grants no permission and changes nothing."
- `kentender_procurement/kentender_procurement/public/js/tenders/` contains no "Contact administrator" (case-insensitive grep over `*.vue`/`*.js`, excluding `dist/`).
**Rule:** §11.2 control list; TPR10-IMP-007 "Consume CFG v0.16 public portal support/legal-link projection for bidder-safe Tenders surfaces".
**Reproduction / failing test sketch:** static: grep as above.
**Impact:** Users hitting a blocked or forbidden state have no governed route to the support instruction.

### AUD-TND-016 — Late-amendment window is a hard-coded 7 days, not a configured/verified rule
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §4.8 (`deadline_extension_required`), §5.6, §21 counsel item · **Module(s):** Tenders · **Sources:** trace-tenders F-22
**Evidence**
- `TND/services/addenda.py:50-54,109-110,221` — `LATE_AMENDMENT_DAYS = 7` with the comment "Statutory figure verification pending"; `required = ... (current - now) < timedelta(days=LATE_AMENDMENT_DAYS)`.
- Doc line 2257 (counsel item): PPADA s.75(5) "requires the deadline to be extended when an addendum is issued with less than one third of the preparation time remaining ... not built or verified here".
**Rule:** §4.8 `deadline_extension_required` "Generated from issue timing and the applicable rule." The doc names no source for the rule. Decision for the owner: fixed days, one-third of the period, or a configured rule row.
**Reproduction / failing test sketch:** (static; not run) Tender with a 30-day period; issue an addendum with 8 days remaining -> no deadline extension required by the code, although one-third of 30 days is 10.
**Impact:** The extension trigger may be wrong for periods other than 21 days.

### AUD-TND-017 — Two TPR section 5.2 / AC rules have no field or server rule behind them
**Severity:** Low · **Classification:** SPEC GAP · **Doc:** TPR-CHG-001 v0.17 §5.2 (tender security row), TPR09-AC-014 · **Module(s):** Tenders · **Sources:** trace-tenders F-23
**Evidence**
- Doc line 474 "Tender security amount | Money, exact 2-decimal KES | Positive and within governed rule." vs `TND/services/controls.py:56` (`min_exclusive: 0` only) and `TND/services/review.py:197-198` (positive check only): no governed rule is named or read.
- Doc line 1721 TPR09-AC-014 "A physical meeting requires date/time, venue and access instructions" vs `TND/services/controls.py:58-61` (date/time, mode, venue link, online joining text) and §5.2 doc lines 476-478, which list no "access instructions" field.
(The issue-date rule "cannot precede publication readiness", doc line 467, is superseded by the v0.16 sentence in the same row that counts the period from the later of issue date and authorisation, so it is not claimed here.)
**Rule:** the two doc statements name rules no §5.2 field or rule source implements. Decision for the owner: name the governed tender-security rule source; add an access-instructions field or amend AC-014.
**Reproduction / failing test sketch:** static: set `tender_security_amount` to any positive amount; it passes. No physical-meeting access field exists.
**Impact:** Spec/implementation mismatch without a defect in existing behaviour.

### AUD-TND-018 — Certified lead and contributing OU identifiers are not on `GetTender`
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 header (OVS owner amendment), OVS-CHG-001 v0.6 §4.1 · **Module(s):** Tenders · **Sources:** trace-tenders F-24
**Evidence**
- Doc line 7: "Expose certified lead and contributing OU identifiers from the exact consumed REQ Version through the read model; do not invent independent editable copies."
- `TND/services/read.py:665-674` — the `tender` object in `get_tender` carries name, reference, titles, status, dates, publication, cancellation, template fields; no `lead_org_unit` or `contributing_org_unit_ids` (they are fetched only for the workspace list at `read.py:49-52`, and `tender_row` at `read.py:111` does not return them).
- `TND/services/draft_commands.py:110-118` and `TND/services/snapshot.py:116-125` — stored once at Start; lead falls back to the first contributor when no certification is carried (`snapshot.py:124-125`) and is stored null if the OU row does not exist (`draft_commands.py:118`).
**Rule:** header quote above.
**Reproduction / failing test sketch:** static: call `get_tender` for a started Tender; the response has no lead or contributor field.
**Impact:** The owner read model for oversight consumers must read the Tender columns directly instead of the published read.

### AUD-TND-019 — "Authorise publication" is offered when no publication rule exists
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TPR-CHG-001 v0.17 §5.10 (guard reasons), §11.1(1), §10.15 "Publication not configured" · **Module(s):** Tenders · **Sources:** trace-tenders F-27
**Evidence**
- `TND/services/read.py:379-393,414-418` — `period_problem` returns `None` when no minimum resolves, so `allowed_actions` appends `authorise_publication`; it does not consult `configuration_gateway.resolve_publication_rule`.
- `TND/services/publication.py:78` — the command itself raises `TND_PUBLICATION_RULE_UNAVAILABLE` via `resolve_publication_rule` (`configuration_gateway.py:72-79`), and the publication read shows it only as `rule_error`/`can_configure` (`publication.py:298-317`), not as a next-step blocker (`guidance.py` references seven `TND_*` codes, not this one).
**Rule:** §11.1(1) "every control is offered only when the command layer would accept it for this actor in this exact state"; doc line 664 "Authorise publication with no effective rule | `TND_PUBLICATION_RULE_UNAVAILABLE` ...".
**Reproduction / failing test sketch:** (static; not run) With no Open Tender publication rule in force, an Approved Tender's AO sees `allowed_actions` containing `authorise_publication`; pressing it raises `TND_PUBLICATION_RULE_UNAVAILABLE`.
**Impact:** A dead-end control shown to the Accounting Officer; the command refuses safely.

---

## Dropped / downgraded

- trace-requisition F-27 (no migration for section 20 cutover) -> DROPPED: §20 asks for inspection and controlled migration of live records and says existing Versions "remain immutable and are rendered through the new result-first disclosure"; it names no mandatory patch, and validation computes the three tasks dynamically. No provable rule violation; the TPR rejection of legacy v1.3 handoffs (`TND/services/handoff_gateway.py:77-78`) is the handoff-version issue owned by the hnd part.
- trace-requisition F-29 residual rows: row 5 -> folded into AUD-REQ-016 (and narrowed: `Annual Plan`/`Plan Item`/`Tender` reads are same-app); row 17, 24, 44, 58, 62 (root field `reservation_ids`, `Superseded` no trigger, task display field, requirement-type proxy, Planning hard-coded KES/1) -> DROPPED, doc-silent or by-design with no rule violated; row 30/60 (county id equals base id; overlap treatment never checked on the REQ side) -> DROPPED, `compatibility.py:97-105` does check county support and rule availability, and the duplicate id is how Planning publishes one regulatory reference (see Calibration notes 2); row 41 (subjectivity heuristic) -> DROPPED, SPEC GAP below the Low floor; rows 49, 56 -> owned elsewhere (hnd / xc-core money); row 75 -> promoted to AUD-REQ-006; rows 82, 202, 206 -> AUD-REQ-013; row 134 -> folded into AUD-REQ-007; rows 148, 150, 249 -> test/evidence gaps; row 158-160 -> AUD-REQ-008; row 165, 175 -> API naming only; row 168 -> display read, owned by xc-core item 7; row 236, 238, 240, 283, 284, 286-292 -> UI/usability/evidence rows not assessable by static reading; row 242 -> AUD-REQ-012; row 248 -> same as F-27.
- trace-requisition F-02b -> kept separately as AUD-REQ-003 and classified SPEC GAP (the doc's AC-045 phrase "no self-authorisation" is not defined for preparer-as-authoriser).
- trace-requisition F-17 outbox part -> kept in AUD-REQ-012 at Low (no consumer reads the events; Tenders pulls the handoff).
- trace-tenders F-20 (clarification `received_at` supplied by caller) -> DROPPED: `receive_tender_clarification` is gated to the registered producer identity (`candidate_gateway.require_producer(user)`, `TND/services/clarifications.py:57`), and doc line 381 describes `received_at` as the inbound receipt instant supplied with the question.
- trace-tenders F-25 (post-close cancellation absent) -> DROPPED as a finding: the doc itself marks the v0.14 post-close route proposed and owner-gated ("until then v0.13 is the operational baseline", doc line 1965); code matches the gate (`TND/services/cancellation.py:52-56`). Recorded in Calibration notes as "divergence from proposed spec".
- trace-tenders F-26 (`Tender Event` payload rewritten on rejection) -> DROPPED: the row is an outbox record with a mutable `status`; `mark_rejected` (`TND/services/events.py:116-121`) adds `rejection_reason` to the payload of a delivery record, not to a business audit event.
- trace-tenders F-28 (representative-user, accessibility, property tests absent) -> DROPPED: process/test gap, not a code or doc defect.
- trace-tenders F-01 -> DOWNGRADED Medium to Low and reproduction corrected (compatibility runs on the stored snapshot, so changing the live handoff, as the source suggested, does not affect reopen; only release support and the Site county flag can differ), see AUD-TND-011.
- trace-tenders F-02, F-06 -> kept at Medium; F-03 kept at High (legally material: closed Tender's deadline rewritten); F-04 re-classified from CODE DEFECT to SPEC GAP (no governed command named by the doc) but held at High under the "documented flow dead-ends" rule.
- Not mine, not written: trace-tenders F-10, F-16 (hnd), F-11, F-12 (xc-authz 13), F-19 (xc-core 6); trace-requisition F-01, F-07 (xc-authz 5), F-03, F-12 (xc-core 1), F-11, F-20 (xc-core 7), F-14 (xc-core 11), F-18, F-19, F-24, F-25 (hnd), F-26 (skip). AUD-TND-005 is the Tenders instance of the xc-core cluster "denial events never written / rolled back on throw"; AUD-REQ-010 and AUD-TND-010 share `CORE/services/file_integrity.py:71-82` and are kept as two findings because the governing rules and owners differ.

## Calibration notes

**Requisition**
1. Handoff v1.4 names (REQ -> Tenders): present, producer and consumer agree. Producer `REQ/services/handoff.py:31` (`HANDOFF_VERSION = "1.4"`), `:70` `reservation_category` (no `reservation_category_value`), `:62` `strategic_objective_id`, `:75` grouped `warranty_support`, `:83` `departmental_certification`, `:87` `procurement_authorisation`. Consumer `TND/services/snapshot.py:36-61` (`_handoff_v14_names`) translates exactly these (`reservation_category_value` from `reservation_category`, `strategic_objective`, six warranty facts, `decisions`) and `snapshot.build` (`:64-70`) applies it; Tenders accepts only version "1.4". Pin is indirect: `TND/tests/test_gateway_contracts.py:28-38,42-47` checks that the producer's *source text* contains each key literal (not a run) and `HANDOFF_KEYS` omits `county_resident_reservation` and `reservation_rule_snapshot_ids`; no test authorises a Youth requisition and asserts the published Tender carries category "Youth" or the 36-month warranty. Not regressed; doc still says v1.3 (hnd-owned spec defect).
2. County/rule snapshot fields: present in the handoff (`REQ/services/handoff.py:70-71`: `county_resident_reservation`, `reservation_rule_snapshot_ids`; filled at `REQ/services/draft_commands.py:127-130` from Planning's `reservation_rule` and `county_rule`). Residual: when County applies, `snapshot_ids` is `[rule.snapshot_id, county.snapshot_id]` and Planning sets both to the same regulatory reference (`procurement_planning/services/plan_requisition.py:154,165`), so the list holds one id twice; `TND/services/compatibility.py:112` (`len(_rule_ids(payload)) < 2`) is satisfied by the duplicate, not by a distinct overlap-rule verification. Rule version number and verification status stay in the Version basis snapshot, not the handoff.
3. Certified lead OU through onward links: present. `REQ/services/lifecycle.py:278` freezes `certified_lead_org_unit_id` at submission; `REQ/services/handoff.py:83-84` carries it in `departmental_certification.lead_org_unit_id`; `TND/services/snapshot.py:116-125` `lead_unit` prefers it (falls back to the first contributor only when no certification is carried); `TND/services/draft_commands.py:110-118` stores it on the Tender; `TND/services/tender_authorization.py:154-166,299-305` honour lead plus contributors for record reads. Residual gaps are AUD-TND-018 (not on `GetTender`) and the lead-only list scope (`tender_authorization.py:257`, owned by xc-authz 13).

**Tenders**
4. v1.4 translation end to end: seam present and unit-pinned (`TND/tests/test_snapshot_contract.py:42-85` with a hand-written v1.4 payload); end-to-end behavioural pin absent (see note 1). Reservation reaches the render (`serializer.py:375`), compatibility and definition (`bid_definition.py:222`), warranty reaches `serializer.warranty_support` (`:241-249`).
5. 7-day minimum vs 21-day default: present and working. `TND/services/configuration_gateway.py:127-146` returns `(minimum_days, default_days)` for the `bid_opening` row; `TND/services/review.py:125-150` makes below-minimum a Must fix and 7-21 days a Must fix only while `shortened_period_reason` is empty, then a Review note; the authorisation check is `TND/services/publication.py:78-82` and the final-confirmation check `:156-159`. Patch `CORE/patches/v1_28/open_tender_preparation_minimum.py:24-35` fills only rows with no minimum, is registered (`CORE/patches.txt:24`) and idempotent by reading; no test calls its `execute()`; HOPF-approval re-detection and the no-minimum profile case are not pinned by tests (`TND/tests/test_publication.py:108-120,133-223` cover review, between-minimum-and-usual, authorisation).
6. Digest drift with a new CATALOGUE control: confirmed present for approved/unauthorised Versions (AUD-TND-007); mitigated for exactly one control (`DIGEST_OMIT_WHEN_EMPTY`); published Tenders unaffected.
7. Method-eligibility editor: outside TPR v0.17 (Tenders only tests `planned_method == "Open Tender"`, `TND/services/compatibility.py:127`). Configuration owns it (`CORE/services/procurement_settings.py:287-348` in-place correction only while `method_profile_editable`, else `CFG_CATALOGUE_IN_USE`; `:387-445` registers a superseding version); tests `CORE/tests/test_procurement_settings.py:126,164,191-222`. Not audited further here.
8. Cancellation guards and replay: pre-close route calls the Award guard (`TND/services/cancellation.py:127-132`, fail-closed on Unknown in `award/services/authority.py:76-93`) but a refusal is surfaced as `TND_MUST_FIX`; replay by key (`envelope.py:44-56`), second cancel returns `TND_CANCELLED` (`cancellation.py:53-54`). Post-close Cancel Tender, `TND_AWARD_STATUS_UNAVAILABLE`, `TND_CANCEL_GROUND_UNVERIFIED`, `TND_CANCEL_TOO_LATE` do not exist: divergence from proposed spec (TPR14 is owner-gated, doc line 1965), not a defect. No Tenders test covers the guard refusal or replay (only Award's own `award/tests/test_awd_authority.py:19-37`).
9. OVS lead plus contributor read: record reads (`reader_mode`, `has_permission`) honour lead plus contributors; list scope is lead-only (`TND/services/tender_authorization.py:257`); department-mode payload over-discloses (`TND/services/read.py:674,681`); both owned by xc-authz 13; `GetTender` omits the ids (AUD-TND-018).
