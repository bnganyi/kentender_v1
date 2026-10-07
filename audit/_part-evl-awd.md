# Part evl-awd — Bid Evaluation (AUD-EVL) and Award (AUD-AWD) findings

Static read of code and approved docs; nothing was run. Path prefix for code: `kentender_procurement/kentender_procurement/` (abbreviated `P/`). Evaluation services = `P/bid_evaluation/services/` (`EVS/`), Award services = `P/award/services/` (`AWS/`). Doc oracle: EVL-CHG-001 v0_5 (`docs/mvp-1-r1/15_bid_evaluation/`), AWD-CHG-001 v0_5 (`docs/mvp-1-r1/16_award/`), AUTH-ADR-001 v1_11, OVS-CHG-001 v0_6, TRUST-ADR-001 v0_2, BOP-CHG-001 v0_11.

| ID | Severity | Title |
|---|---|---|
| AUD-EVL-001 | High | A conflicted evaluator can clear their own declared conflict and regain bid access |
| AUD-EVL-002 | High | A committee-recorded qualified report on an unresolved requirement or price discrepancy can never be frozen for signing |
| AUD-EVL-003 | High | One member's evidence finding resolves a price-arithmetic discrepancy (or a missing rule) and the bid is ranked on the submitted total |
| AUD-EVL-004 | Medium | `retry_delivery` completes and hands over a report with no suspension, roster or validity recheck |
| AUD-EVL-005 | Medium | A pending opening-supplement impact does not block freezing, and a "material" impact triggers no recalculation |
| AUD-EVL-006 | Medium | A participant who is no longer an eligible member can still sign the verification report |
| AUD-EVL-007 | Medium | `return_report` has no check that the delivery is the current, unreturned one |
| AUD-EVL-008 | Medium | Opening exceptions, including "Comment for Evaluation", are handed over but never read by Evaluation |
| AUD-EVL-009 | Medium | Clarification-reply attachments bypass the shared upload integrity check |
| AUD-EVL-010 | Medium | A conflicted or unavailable member who is also the secretary keeps bid access |
| AUD-EVL-011 | Medium | Accounting Officer / Head of Procurement see committee free text and a submission version before delivery |
| AUD-EVL-012 | Medium | `ExportEvaluationRecord` / "Download report" is not a server operation |
| AUD-EVL-013 | Medium | Independent-opening-member exclusion from evaluation works in one order only |
| AUD-EVL-014 | Medium | Evaluation's funding read runs as the session user and swallows every failure |
| AUD-EVL-015 | Medium | Tenders publishes only cancellation: suspension, resumption, validity-extension, award-decision and dated-rule facts have no production producer |
| AUD-EVL-016 | Medium | The secretary reads every bid with no declaration or confidentiality acceptance |
| AUD-EVL-017 | Medium | No authoritative statutory evaluation deadline exists, so overdue highlighting is dead in production |
| AUD-EVL-018 | Low | Published rounding mode (`ROUND_HALF_UP`) is ignored by the price calculation |
| AUD-EVL-019 | Low | "Test attestation — not an electronic signature" label absent from Evaluation signing views |
| AUD-EVL-020 | Low | A verification plan never clears the chair's discussion item |
| AUD-EVL-021 | Low | A failed second package read after intake rolls everything back without recording an issue |
| AUD-EVL-022 | Low | EVL v0_5 says the Head's item clears on "return" but `ReturnEvaluationReport` carries no source event |
| AUD-EVL-023 | Low | EVL v0_5 control table, history and task-title claims are inconsistent |
| AUD-AWD-001 | High | No segregation of duties anywhere in the evaluation → opinion → award-decision chain |
| AUD-AWD-002 | High | Funding is never re-read from Budget and an unavailable funding (or validity) read permits a positive award |
| AUD-AWD-003 | Medium | Heads of Procurement can end an authoritative order or a funding restriction with free-text "evidence" |
| AUD-AWD-004 | Medium | Later restrictions and cancellation-after-notice do not reliably reach an already-delivered Contracting case |
| AUD-AWD-005 | Medium | Case `outcome` is never set to "Award", so the HoD decision summary shows no outcome |
| AUD-AWD-006 | Medium | The real Evaluation producer hard-codes every annex as available |
| AUD-AWD-007 | Medium | Contracting package "contract terms" are constant strings, not mapped tender data |
| AUD-AWD-008 | Medium | §88 validity extension and the notice's contracting window are not modelled |
| AUD-AWD-009 | Medium | The "No award" follow-up task can never be completed |
| AUD-AWD-010 | Medium | An open debrief request or missing debrief rule never blocks Contracting delivery |
| AUD-AWD-011 | Medium | Return to Evaluation dead-ends when the Head of Procurement who received the report is replaced |
| AUD-AWD-012 | Low | `RecordAwardDecision` does not read live tender status before committing |
| AUD-AWD-013 | Low | "Issue in progress" is not durable before the first outward effect and an interrupted issue has no recovery |
| AUD-AWD-014 | Low | Authority-status contract answers "no decision / not issued" from absence of a case |
| AUD-AWD-015 | Low | `retry_operation` authority ignores effective dates |
| AUD-AWD-016 | Low | Award never checks the product profile or the published award method |
| AUD-AWD-017 | Low | AWD v0_5 still carries "proposed"/"would establish" wording after approval |
| AUD-AWD-018 | Low | AWD v0_5 §15 says "Persist timestamps in UTC"; the project rule and the code store site time |

### AUD-EVL-001 — A conflicted evaluator can clear their own declared conflict and regain bid access
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §3 (roster terminology, line 67/69); EVL-A06 · **Module(s):** Evaluation · **Sources:** trace-evaluation F-1 (rows 20, 137, 198, 203); sweep-sod F7
**Evidence**
- `P/bid_evaluation/services/declaration.py:51` — `if current and current.choice == choice and choice == "No conflict to declare":` (early return only when the choice repeats; a conflict followed by "No conflict" does not hit it)
- `P/bid_evaluation/services/declaration.py:55` — `prior.status = "Superseded"` then a new Current declaration row is inserted (lines 58-63)
- `P/bid_evaluation/services/roster.py:69` — `conflict = bool(decl and decl.choice == "Declare a conflict")` is derived only from the Current declaration; `roster.py:78` returns `eligible: member and not reasons`, so the new "No conflict" row makes the member eligible again
- `P/bid_evaluation/services/declaration.py:65` — only the "Declare a conflict" branch calls `lifecycle.roster_changed` and notifies the Accounting Officer; the retraction branch (line 73-74 `member_became_eligible`) involves no AO action
- `P/bid_evaluation/services/my_work_provider.py:67-71` and `next_steps.py:120-124` derive the AO's "Resolve committee appointment" task from the same live status, so the task silently disappears
**Rule:** EVL §3 line 67: "A declared conflict stops that person's bid access immediately and creates the Accounting Officer's task"; line 69: an eligible member has "no unresolved conflict"; line 57: the Accounting Officer "deal[s] with declared conflicts". The AO's reasoned replacement is the only resolution route the document names; it does not provide for self-retraction.
**Reproduction / failing test sketch:** (static; not run) 1. On the test site appoint three members (M1..M3) to an Evaluation Case in Reviewing and have all declare "No conflict". 2. As M1 call `declare_interest(choice="Declare a conflict", conflict_description="x", confidentiality_accepted=True, idempotency_key=k1)`; `roster.status(case, M1)["conflict"]` is True, `reads.bid(..., user=M1)` is Not found, AO has "Resolve committee appointment". 3. As M1 call `declare_interest(choice="No conflict to declare", confidentiality_accepted=True, idempotency_key=k2)`. Expected: refused (AO-only resolution). Predicted: `eligible` True, `reads.bid` returns bid content, AO task gone, no AO action recorded. Also works while the report is Signing (the earlier conflict withdrew signing; the reversal restores M1 as a required signer).
**Impact:** The person whose interest is in question can lift their own recusal and read sealed bids, defeating the Accounting Officer's conflict control without a trace beyond a superseded declaration row.
**Verification:** CONFIRMED — `declaration.py:51-63` only short-circuits a repeated "No conflict" and otherwise supersedes the Current row, `roster.py:69,78` recomputes eligibility from the Current row alone, and no guard, doctype controller or test blocks the retraction (`api.declare_interest` is gated only by roster membership).

### AUD-EVL-002 — A committee-recorded qualified report on an unresolved requirement or price discrepancy can never be frozen for signing
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §4.4 (line 114), §5.5 (lines 160), EVL-A09/A17 · **Module(s):** Evaluation · **Sources:** trace-evaluation F-2 (rows 111, 112, 206, 214)
**Evidence**
- `P/bid_evaluation/services/conclusion.py:104` — `kind = "Qualified report" if result == "Needs review" else "Resolved finding"`
- `P/bid_evaluation/services/aggregate.py:71` — `human_record` feeds `conclusion` only for kinds `("Resolved finding", "Reply disposition", "Verification outcome")`; a "Qualified report" conclusion only sets the `qualified` flag (`aggregate.py:76-78`, `:112`), so the requirement stays Needs review
- `P/bid_evaluation/services/comparison.py:75-76` — a Needs-review bid leaves `pending` non-empty, so no `outcome` is produced (`:78` `if not pending:`)
- `P/bid_evaluation/services/report.py:153` — `return {"outcome": None, ..., "provisional": True}` for that case; the `QUALIFIED` outcome (`report.py:144-145`) is reachable only inside `if table["outcome"] == "Recommendation":` (`:140`), i.e. when nothing is pending
- `P/bid_evaluation/services/signing.py:70-71` — `if built["recommendation"]["provisional"]: issues.append({"item": "The comparison is provisional", ...})` makes `readiness` fail with `EVL_REPORT_INCOMPLETE`; the preceding loop (`signing.py:59`) already exempts `row["qualified"]`, showing the qualified path was intended to freeze
**Rule:** EVL §5.5 (line 160): freeze is allowed "once every required result is either resolved or explicitly included in a committee-recorded qualified outcome … A qualified report is a completed account of the issue, not a successful award recommendation"; §4.4 (line 114): "Without one, record the unresolved discrepancy and deliver an appropriately qualified report with no unsupported recommendation."
**Reproduction / failing test sketch:** (static; not run) 1. Reviewing world with one bid; leave requirement "Service location" at Needs review. 2. Full roster present in a discussion; chair calls `record_conclusion(bid=B, requirement_key=..., result="Needs review", qualified=True, reason="cannot establish the address")` (as `P/bid_evaluation/tests/test_evl_discussion.py:140`). 3. Resolve every other requirement; secretary calls `signing.send_for_signing(...)`. Expected: frozen version with outcome "Qualified report". Predicted: `EVL_REPORT_INCOMPLETE` listing "The comparison is provisional". Same for a price discrepancy (AUD-EVL-003 setup without a member finding). Add to `TestSendAndSign`: assert `report.build(doc)["recommendation"]["outcome"] == "Qualified report"` and case state Signing. Only the case-wide "No agreed recommendation" conclusion (`report.py:137`) reaches signing, which is a different outcome. No test freezes a qualified report (grep "qualified" in `P/bid_evaluation/tests/` finds only `test_evl_discussion.py:53-55,140-141`).
**Impact:** The legally required fallback for an unresolved requirement or arithmetic discrepancy cannot be produced, so the committee can only force a signable report by recording "No agreed recommendation" or by (wrongly) resolving the requirement; the evaluation can dead-end.
**Verification:** CONFIRMED — traced `conclusion.py:104` -> `aggregate.py:71-78,99` (requirement stays Needs review, responsiveness `REVIEW` at `aggregate.py:~143`) -> `comparison.py:75-78` (pending, no outcome) -> `report.py:153` (`provisional: True`) -> `signing.py:70-71` (`EVL_REPORT_INCOMPLETE`); `report.py:144-145` QUALIFIED is reachable only when nothing is pending.

### AUD-EVL-003 — One member's evidence finding resolves a price-arithmetic discrepancy (or a missing rule) and the bid is ranked on the submitted total
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §4.4 (line 114), §4.1 · **Module(s):** Evaluation · **Sources:** trace-evaluation F-6 (rows 33, 54, 206)
**Evidence**
- `P/bid_evaluation/services/rules.py:269` — `"result": REVIEW if problems else MEETS` (a submitted total that differs from the exact-decimal calculation is Needs review for `RR-PRICE-GOODS`, `checks.py:29` / `:118-121`)
- `P/bid_evaluation/services/findings.py:93-104` — `record_evidence_finding` requires only `require_member` and state Reviewing; `contrary` is true only when the automatic result is "Does not meet" (`:104`); a "Meets" finding on a Needs-review requirement creates no discussion item (`:108`)
- `P/bid_evaluation/services/aggregate.py:99` — `elif finding is not None and finding.result in (MEETS, FAILS):` makes the requirement result the member's finding (basis "Member evidence finding")
- `P/bid_evaluation/services/comparison.py:63-64` — `elif res["responsiveness"] == "Responsive" and row["financial"] == aggregate.MEETS: row["evaluated_total"] = cstr(bid.submitted_total)`; the discrepant sum is ranked and `report.build` recommends it
- The same path resolves a requirement whose rule is unavailable (`P/bid_evaluation/services/rules.py:124-126` returns Needs review "unavailable"), because the finding/conclusion overrides it
**Rule:** EVL §4.4 (line 114): "Arithmetic inconsistencies remain visible. Where the issued tender supplies a lawful disposition, apply and explain it without changing the submitted sum. Without one, record the unresolved discrepancy and deliver an appropriately qualified report with no unsupported recommendation. A committee explanation cannot substitute for a missing legal or published basis."
**Reproduction / failing test sketch:** (static; not run) 1. Build the discrepant-total world of `P/bid_evaluation/tests/test_evl_rules.py:113` (package total differs from the calculation). 2. As an eligible member call `record_evidence_finding(bid=B, requirement_key="RR-PRICE-GOODS", result="Meets", reason="ok", idempotency_key=k)`. 3. `comparison.compare(case)` ranks B with `evaluated_total == submitted_total` and `report.build` recommends B with no qualification. Test sketch: assert step 2 is refused or the outcome remains unresolved/qualified.
**Impact:** A single individual member, with no committee conclusion, can make a bid with an arithmetic discrepancy the recommended bidder at the wrong total, contrary to the document's express prohibition.
**Verification:** CONFIRMED — `findings.py:93-108` accepts a "Meets" finding on any requirement (price requirement `RR-PRICE-GOODS` is a normal requirement, `checks.py:29,118`), `aggregate.py:99` adopts it unless the automatic result is "Does not meet", and `comparison.py:63-64` then ranks the submitted total; no guard excludes calculation-type requirements.

### AUD-EVL-004 — `retry_delivery` completes and hands over a report with no suspension, roster or validity recheck
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.5 (line 164), §5.7 (line 180) · **Module(s):** Evaluation, Award · **Sources:** trace-evaluation F-3 (rows 78, 116, 207)
**Evidence**
- `P/bid_evaluation/services/signing.py:177-188` — `_complete_and_deliver` runs `recheck(doc)` (`:180`, roster + `guards.open_case`) and the validity withdrawal (`:182-185`) before `complete_record`/`deliver`; a `Paused` result leaves the case in Signing (`:181`)
- `P/bid_evaluation/services/signing.py:221-235` — `retry_delivery` checks only the secretary and `record_versions.missing_proofs`, then `out = deliver(doc, version, idempotency_key)` (`:235`), which sets `state="Report sent"` and calls `notify_consumers` (Award hand-off, `:215-217`)
**Rule:** EVL line 164: "Before freezing and again before delivery, recheck current source impact, roster, cancellation/suspension and tender validity … If the frozen report still makes that recommendation … return it to Reviewing … A suspension alone preserves the signing state but pauses completion." Line 180: suspension "pauses new committee decisions, requests and report signing".
**Reproduction / failing test sketch:** (static; not run) 1. All members sign with `simulation.set_controls(delivery_outcome="Failed")` (as `P/bid_evaluation/tests/test_evl_report.py:120`). 2. `tender_events.record_simulated_event(kind="Suspension", ...)` (or move the clock past `validity_end` for a positive recommendation). 3. Secretary calls `signing.retry_delivery(...)`. Expected `EVL_SUSPENDED` / return to Reviewing. Predicted: Delivered; Award receives a report that should be paused or withdrawn. Also the `Paused` branch (`:180-181`) leaves signed proofs whose only exit is this unguarded retry.
**Impact:** A report that must be paused (suspension) or withdrawn (expired validity, roster change) can still be delivered to the Head of Procurement and Award.

### AUD-EVL-005 — A pending opening-supplement impact does not block freezing, and a "material" impact triggers no recalculation
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.5 (line 164), §5.6 (line 174) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-8 (rows 111, 126, 209)
**Evidence**
- `P/bid_evaluation/services/correction.py:224` — a received supplement is stored with `"impact": "Pending"`
- `P/bid_evaluation/services/signing.py:47-79` — `readiness` has no reference to source-event impact (grep "impact" in `signing.py`/`lifecycle.py`/`checks.py` returns nothing); `recheck` (`signing.py:169-174`) also omits it
- `P/bid_evaluation/services/correction.py:259-262` — `assess_supplement` with "Findings need review" only calls `lifecycle.withdraw_signing(...)`; no `checks.run` or re-evaluation follows
**Rule:** EVL line 174: "Before delivery, a member must record whether they affect any finding; material changes require recalculation and, if already signing, a new report"; line 164: recheck "current source impact" before freezing and before delivery.
**Reproduction / failing test sketch:** (static; not run) 1. In Reviewing, `correction._receive_supplement(tender, "BOP-SUPP:X", supplement)` (or let `consume_supplements` run). 2. Resolve all requirements; secretary `send_for_signing`. Predicted: frozen and deliverable with the supplement impact still Pending. 3. Member `assess_supplement(impact="Findings need review")` before delivery: signing is withdrawn but the check run is not repeated, so findings/ranking are unchanged. No test covers receive/assess/head_review (EVL-A12).
**Impact:** A report can be frozen and delivered ignoring corrected opening facts that the document says must be assessed (and recalculated) first.

### AUD-EVL-006 — A participant who is no longer an eligible member can still sign the verification report
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.4 (line 152), EVL-A08 (line 668) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-11 (rows 103, 147, 205)
**Evidence**
- `P/bid_evaluation/services/diligence.py:106-108` — `record_observation` requires `user in participants(plan)` and `findings.require_member(doc, user)`
- `P/bid_evaluation/services/diligence.py:195` — `sign` checks only `if not plan or user not in participants(plan)`; no `require_member`; `my_targets` (`:177-185`) is also membership-by-target only
- `P/bid_evaluation/services/diligence.py:150` — `send_for_signing` (lead) likewise does not re-check eligibility; a roster change/conflict supersedes only the main report (`lifecycle.withdraw_signing`, `lifecycle.py:27-54`), not the verification plan
**Rule:** EVL line 152: due diligence "is carried out by named eligible members of the current evaluation committee"; EVL-A08 line 668: "scope/roster changes … are retained".
**Reproduction / failing test sketch:** (static; not run) 1. Plan with participants Grace and Ruth, observations recorded, lead freezes (`diligence.send_for_signing`). 2. Ruth `declare_interest("Declare a conflict")` or is replaced by the AO. 3. Ruth calls `diligence.sign(...)`. Expected refusal. Predicted: proofs recorded and the verification report completes (`report_state="Signed"`) with a signature from an ineligible person. `P/bid_evaluation/tests/test_evl_diligence.py:79` covers only the happy path.
**Impact:** A conflicted or replaced member's signature can complete the due-diligence record that supports the recommendation.

### AUD-EVL-007 — `return_report` has no check that the delivery is the current, unreturned one
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.6 (line 168-172), EVL-A11 · **Module(s):** Evaluation · **Sources:** trace-evaluation F-12 (rows 26, 121, 152, 208)
**Evidence**
- `P/bid_evaluation/services/correction.py:55-57` — `_delivered` returns the latest `status="Delivered"` delivery by `delivered_at`; a returned delivery keeps `status="Delivered"` (only `review_state` changes, `:114-116`)
- `P/bid_evaluation/services/correction.py:94-106` — `return_report` checks recipient, `guards.closed` and downstream status, but not `delivery.review_state` nor `doc.state`
- `P/bid_evaluation/services/correction.py:120` — `records.bump(doc, state="Reviewing", ...)` unconditionally
- `P/bid_evaluation/services/signing.py:89` — `send_for_signing` only requires `doc.state == "Reviewing"`; `lifecycle.signing_report` (`lifecycle.py:23-24`) returns one arbitrary Signing version by `get_value`
**Rule:** EVL §5.6 / EVL-A11: a return "reopens the evaluation as Reviewing and prepare[s] a new numbered report"; delivered report preserved; new version needs fresh signatures. Nothing authorises a return of an already-returned delivery while its successor is being signed.
**Reproduction / failing test sketch:** (static; not run) 1. Deliver v1; Head returns it (case Reviewing); secretary freezes v2 (case Signing, v2 collecting proofs). 2. Head calls `return_report` again with another comment. Predicted: v1 is re-marked Returned with the new comment, case state regresses to Reviewing while v2 is still in state Signing; `send_for_signing` can then freeze a v3 while v2 still holds proofs (two Signing versions; `signing_report` picks one by `get_value`). `P/bid_evaluation/tests/test_evl_oversight.py:276,298` return once only.
**Impact:** A repeated return corrupts the case/report state machine and can leave two versions in Signing.

### AUD-EVL-008 — Opening exceptions, including "Comment for Evaluation", are handed over but never read by Evaluation
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.1 (line 126), §6 (line 186) · **Module(s):** Evaluation, Bid Opening · **Sources:** trace-evaluation F-19 (row 63)
**Evidence**
- `P/bid_opening/services/completion.py:35-36,45` — the hand-off carries `"exceptions": [{..., "for_evaluation": x.exception_class == "Comment for Evaluation"}]` and each package's `render_digest`
- `P/bid_evaluation/services/intake.py:51-124` — `receive_opening_package` reads packages, register and `opening_record` only; grep `exceptions|render_digest` in `P/bid_evaluation/services/` matches only a docstring (`intake.py:10`); grep for `for_evaluation` outside Bid Opening and tests finds no consumer
- `P/public/js/bid_opening/screens/OpenBidsScreen.vue:73` — Bid Opening offers a form headed "Comment for Evaluation" whose content therefore reaches no Evaluation screen or report
**Rule:** EVL §5.1 line 126: "Accept one verified nonempty BOP completion, with unchanged packages, the issued definition/mappings, register, minutes, opening exceptions and exact source versions"; line 186: `ReceiveOpeningPackage` carries "register/minutes and exceptions".
**Reproduction / failing test sketch:** (static; not run) 1. In Bid Opening record a "Comment for Evaluation" on an entry and complete the opening. 2. After Evaluation intake, search every `reads.resolve`/`reads.bid`/report output for the comment text: absent. Test sketch: `completion` payload with one exception; after `intake.receive_opening_package` assert the exception is stored/readable by the committee.
**Impact:** Observations the opening committee explicitly directed to Evaluation are silently dropped.

### AUD-EVL-009 — Clarification-reply attachments bypass the shared upload integrity check
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.3 (line 142), §10 D06 (line 583) · **Module(s):** Evaluation, Bid Submission · **Sources:** trace-evaluation F-10 (row 92)
**Evidence**
- `P/bid_evaluation/services/clarification.py:302` — `ATTACHMENT_TYPES = ("application/pdf", "image/png", "image/jpeg")` is matched against the client-asserted `media_type` (`:317`)
- `P/bid_evaluation/services/clarification.py:316` — `base64.b64decode(..., validate=False)`; only emptiness and a 5 MB cap are checked; the bytes are stored in `attachments_json`
- `P/bid_submission/services/evidence.py:90` — Bid Submission runs every upload through `kentender_core.services.file_integrity.check_file` (`:84` `file_integrity.unreadable`); Evaluation never calls it
**Rule:** EVL line 142: "Supporting files are restricted to the question and shared upload security limits"; line 583: "configured BDS file limits and security validation".
**Reproduction / failing test sketch:** (static; not run) As an authorised supplier call `submit_clarification_reply(attachments=[{"filename":"x.pdf","media_type":"application/pdf","content_base64": base64(b"MZ\x90 not a pdf")}])`. Predicted: accepted and later exposed to committee members. Bid Submission refuses the same bytes.
**Impact:** A supplier can place an unvalidated file (any bytes labelled PDF/image) before committee members.

### AUD-EVL-010 — A conflicted or unavailable member who is also the secretary keeps bid access
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §3 (lines 59-61, 67) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-4 (row 15)
**Evidence**
- `P/bid_evaluation/services/reads.py:62` — `bids = (v["eligible"] or v["secretary"] or v["auditor"]) and not v["technical"]`
- `P/bid_evaluation/services/next_steps.py:47-56` — `viewer()` sets `secretary` independently of `conflicted`/`unavailable`
- `P/bid_evaluation/services/secretary.py:26-61` — the Head of Procurement may appoint themselves or a procurement officer; the secretary may also be an appointed member (EVL line 67)
**Rule:** EVL line 67: "A declared conflict stops that person's bid access immediately"; line 61: "Specific appointment plus conflict clearance governs committee access".
**Reproduction / failing test sketch:** (static; not run) HoP assigns member M as secretary; M declares a conflict; call `reads.bid(tender_reference, bid, user=M)` and `reads.evidence(...)`. Expected Not found; predicted: returned (`access()["bids"]` true through `secretary`).
**Impact:** The recusal of a member-secretary does not stop access to the bids they declared a conflict about.

### AUD-EVL-011 — Accounting Officer / Head of Procurement see committee free text and a submission version before delivery
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** OVS-CHG-001 v0_6 §4 (line 70); EVL-CHG-001 v0_5 §6 (technical issues) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-13 (rows 173, 177, 211)
**Evidence**
- `P/bid_evaluation/services/issues.py:48` — `safe_detail=f"{requirement['label']}: {cstr(description).strip()}"` stores the chair's free text in the platform Support Issue
- `P/bid_evaluation/services/reads.py:169-170` — `work()` returns every Support Issue of the case including `safe_detail` for `a["secretary"] or a["ao"] or a["hop"] or a["chair"]`; `resolve()` returns `out["work"] = work(doc, a)` (`:141`)
- `P/bid_evaluation/services/reads.py:82,128` — `_source(doc)` returns the first bid's `submitted_version` to AO/HoP before delivery
**Rule:** OVS v0_6 line 70: before delivery oversight sees state, committee, dates, next action, meeting counts; "Do not include bidder identities, bid counts, prices, findings, clarification content or discussion notes."
**Reproduction / failing test sketch:** (static; not run) Chair `report_issue(requirement_key=K, description="Memory rule for Afya defective")`; then `reads.resolve(tender_reference=T, user=AO)["work"]["issues"][0]["safe_detail"]` contains the bidder name and requirement label. The existing disclosure tests (`P/bid_evaluation/tests/test_evl_reads.py:40`, `test_evl_oversight.py:74`) assert absence of bidder name/total only.
**Impact:** Bidder-specific committee commentary reaches officers whom the approved visibility rule restricts to administrative facts.

### AUD-EVL-012 — `ExportEvaluationRecord` / "Download report" is not a server operation
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.5 (line 162), §7.2/§10 (lines 269, 599) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-16 (rows 109, 150, 171, 212)
**Evidence**
- `P/public/js/bid_evaluation/BidEvaluation.vue:290-292` — `case "download": go(["report","preview"]); setTimeout(() => window.print(), 800);`
- `P/bid_evaluation/api.py` — no whitelisted export method (grep `export|Export` returns nothing across its 54 functions)
**Rule:** EVL line 599: "Download report — `ExportEvaluationRecord` restricted to selected report/version and permitted annexes; original signatures and correction links preserved"; line 162: "Supporting evidence is linked and exportable".
**Reproduction / failing test sketch:** (static; not run) Open a delivered report and click Download report: the browser print dialog opens over the on-screen preview; no annexes, signature/correction links or per-export permission/log exist server-side.
**Impact:** The documented, scoped export of the signed record does not exist; users can only print what the preview shows.

### AUD-EVL-013 — Independent-opening-member exclusion from evaluation works in one order only
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** EVL-CHG-001 v0_5 §3 (line 65), §5.1 (line 126: "Appointment may exist before intake"); BOP-CHG-001 v0_11 BOP-A17 (line 401) · **Module(s):** Evaluation, Bid Opening · **Sources:** sweep-sod F6
**Evidence**
- `P/bid_evaluation/services/appointment.py:49` — `if opening.is_excluded_from_evaluation(doc.tender, user): return "opening_independent"` (checked only at evaluation-appointment time)
- `P/bid_opening/services/appointment.py:55-61` — `is_excluded_from_evaluation` looks at opening-committee rows with `excluded_from_evaluation`
- `P/bid_opening/services/appointment.py:81` and `:159` — the opening-appointment check compares the independent member only against `opening_seam.processing_actors` (`P/tenders/services/opening_seam.py:91-98`: Tender Version actors and Tender Publication authoriser); it never looks at the Evaluation roster
**Rule:** EVL line 65: "the independent opening member cannot be appointed to evaluate the same tender" (unqualified); BOP-A17: "excluded from later same-Tender Evaluation appointment". The two documents differ on order and neither addresses an Evaluation member later designated independent opening member.
**Reproduction / failing test sketch:** (static; not run) 1. AO appoints an Evaluation committee including U (allowed before intake). 2. AO then appoints U as "Independent member" of the opening committee: `validate` passes (U is not a tender processor). U sits on both. `roster.status`/`reads.py:62` never re-evaluate the exclusion.
**Impact:** The "conservative product policy" separation between opening and evaluation is order-dependent. **Owner decision needed:** state whether the exclusion is symmetric (then Bid Opening must refuse an existing Evaluation member) or only "later evaluation appointments" as BOP-A17 reads.

### AUD-EVL-014 — Evaluation's funding read runs as the session user and swallows every failure
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §4.4 (line 116), D03-FUNDING (line 380) · **Module(s):** Evaluation, Budget · **Sources:** sweep-handoffs F-15
**Evidence**
- `P/bid_evaluation/services/funding.py:35-43` — `get_funding_lineage(reservation=...)` inside `try: ... except Exception: frappe.log_error(title="Bid Evaluation funding read unavailable"); return None`
- `kentender_budget/kentender_budget/services/budget_downstream_contracts.py:61` — `require_budget_version_read_scope(version_at_creation)`; `kentender_budget/kentender_budget/services/budget_authorization.py:170-184` runs `frappe.has_permission(..., user=frappe.session.user, throw=True)`; read roles are Budget governance roles, Auditor, AO and HOPF (`budget_authorization.py:55-71`)
- `P/bid_evaluation/services/funding.py:50-52` — `compare` returns `None` when `available()` is `None`, so `comparison.compare` yields `funding: None` and the frozen report carries no funding fact
**Rule:** EVL line 116: "an authoritative budget comparison can report a shortfall"; a failed or unauthorised read is indistinguishable from "no reservations" (silent absence), and Award later treats absence as "not restricted" (AUD-AWD-002).
**Reproduction / failing test sketch:** (static; not run; permission outcome needs runtime confirmation) 1. Make a procurement-officer secretary (no Budget role) freeze a report whose Tender has reservations. 2. `funding.available(tender)` raises inside the Budget read and returns `None`; the report records no funding block and no shortfall qualification.
**Impact:** A real shortfall can vanish from the signed report depending on who triggered the read, with only an error-log row as trace.

### AUD-EVL-015 — Tenders publishes only cancellation: suspension, resumption, validity-extension, award-decision and dated-rule facts have no production producer
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §6 (line 192), §5.7 (lines 176-180) · **Module(s):** Evaluation, Award, Tenders · **Sources:** trace-evaluation row 77 (§5.7/§6 Partial); trace-award rows 66, 73, 145; related to AUD-EVL-017
**Evidence**
- `P/tenders/services/evaluation_seam.py:171-179` — `status_events` returns only a `Cancellation` event (from `root.cancellation`)
- `P/bid_evaluation/services/tender_events.py:39,119-123` — Evaluation accepts kinds `("Suspension","Resumption","Cancellation","Validity extension","Award decision","Dated rule")`, but `record_simulated_event` throws unless `simulation.enabled()`; `P/bid_evaluation/services/timers.py:40-41` reads a "Validity extension" only from such a stored event
- grep for "validity extension" in `P/tenders` (excluding tests) finds only two docstring mentions (`evaluation_seam.py:25`, `award_seam.py:10`): Tenders owns no extension record
- `P/award/services/restrictions.py:111` — `ReceiveAwardRestriction` (`receive`) has no caller outside tests; Award's only automatic restriction intake is `tenders.status_events` (`P/award/services/tender_events.py`), so Review-order/Suspension events never arrive in production
**Rule:** EVL line 192: "Tenders / downstream owner → Evaluation: Versioned suspension/cancellation/validity-extension and award-decision facts. Evaluate the event's scope and authority; never infer status from an absent consumer."
**Reproduction / failing test sketch:** (static; not run) On a non-test site suspend a tender in Tenders (if a route exists) or extend its validity: no `Evaluation Source Event`/Award issue results; only cancellation is ever consumed. After `validity_end`, `report.outcome` returns "No current recommendation — tender validity expired" with no extension path.
**Impact:** Authoritative pauses and lawful validity extensions never reach Evaluation or Award; the system will report a lawfully extended tender as expired and will not pause for a Board suspension (HOP must key it manually in Award). The producer belongs to Tenders (TPR); this is a missing hand-off.

### AUD-EVL-016 — The secretary reads every bid with no declaration or confidentiality acceptance
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** EVL-CHG-001 v0_5 §3 (lines 61, 63, 67) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-5 (secretary part), rows 15, 225
**Evidence**
- `P/bid_evaluation/services/reads.py:62` — `bids = (v["eligible"] or v["secretary"] or v["auditor"]) and not v["technical"]` (secretary grants bid access without any declaration)
- `P/bid_evaluation/services/secretary.py:26-61` — assignment requires only "Head of Procurement" or a procurement officer and an appointment reference; no declaration or confidentiality sentence
- `P/bid_evaluation/services/declaration.py:35-36` — declarations exist only for members (`user not in roster.member_users(...)` → Not found)
**Rule:** EVL line 67: each *member* personally declares and accepts confidentiality; line 61: "conflict clearance governs committee access". The document says nothing equivalent for the secretary, who reads all bids and prepares the report.
**Reproduction / failing test sketch:** (static; not run) HoP assigns procurement officer P (not a member) as secretary; P calls `reads.bid(...)` before any declaration: returned.
**Impact:** The person who organises the record can read all sealed-then-opened bids without any conflict or confidentiality statement. **Owner decision needed:** require the same declaration/confidentiality acceptance from the secretary (and say whether a conflicted secretary must be replaced).

### AUD-EVL-017 — No authoritative statutory evaluation deadline exists, so overdue highlighting is dead in production
**Severity:** Medium · **Classification:** SPEC GAP · **Doc:** EVL-CHG-001 v0_5 §5.7 (line 178) · **Module(s):** Evaluation, Tenders · **Sources:** trace-evaluation F-21 (rows 80, 81, 210)
**Evidence**
- `P/tenders/services/evaluation_seam.py:165-167` — `"evaluation_deadline": None, "evaluation_rule": None, "evaluation_rule_missing": "No authoritative dated rule for the statutory evaluation period is recorded (FU-EVL-18)."`
- `P/bid_evaluation/services/timers.py:35-47` — `overdue` can be true only if a deadline exists, which in production it never does (only the simulated "Dated rule" event sets it, `tender_events.py:119-123`)
**Rule:** EVL line 178: "Display the statutory evaluation deadline … from the authoritative dated rules. The legal computation, source and timezone must be inspectable … Overdue evaluation is highlighted to the chair and Head of Procurement". The document names no counting rule or source for the evaluation period.
**Reproduction / failing test sketch:** (static; not run) `timers.dated(doc)` on any production case: `evaluation_deadline` is None, `overdue` False; chair/HoP highlighting and the date-conflict check (`clarification.py:125-126`) never trigger.
**Impact:** The documented overdue highlight cannot occur. **Owner decision needed:** supply the governing evaluation-period rule (source, counting, timezone) and the Tenders record that carries it.

### AUD-EVL-018 — Published rounding mode (`ROUND_HALF_UP`) is ignored by the price calculation
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §4.1 (rounding from the rule) · **Module(s):** Evaluation, Bid Submission · **Sources:** trace-evaluation F-9 (row 31, 201)
**Evidence**
- `docs/mvp-1-r1/07_tender_templates/evaluation_rules/IT-EQUIPMENT-OPEN-V1.json:34` — `"rounding": "ROUND_HALF_UP"`
- `P/bid_evaluation/services/rules.py:255-256` — `(quantity * unit_price).quantize(Decimal("0.01"))` and `(before + tax).quantize(Decimal("0.01"))` use the default Decimal context (ROUND_HALF_EVEN); no code reads `numbers.rounding` (grep `ROUND_|getcontext|rounding` in `P/bid_evaluation/services/` finds nothing)
- `P/bid_submission/services/price.py:31,46` — Bid Submission quantizes with `rounding=ROUND_HALF_UP`
**Rule:** EVL §4.1: "Units, rounding, inclusive boundaries … come from the rule".
**Reproduction / failing test sketch:** (static; not run) `rules.calculate_price` with quantity "2.5" and unit price "0.01" (half-cent line): Evaluation computes 0.02, Bid Submission 0.03, so a correct bid reads "differs from calculated" and goes to Needs review. Unreachable with integer quantities and 2-dp prices.
**Impact:** Half-cent rounding disagrees between modules, creating false discrepancies in edge cases.

### AUD-EVL-019 — "Test attestation — not an electronic signature" label absent from Evaluation signing views
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** TRUST-ADR-001 v0_2 §2 (member signature row, line 31) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-17 (row 215)
**Evidence**
- `P/proceedings/test_services/attestation.py:19` and `P/award/services/opinion.py:28` define the label; no Evaluation file does (grep `test attestation|not an electronic signature` outside tests finds only `hooks.py`, `proceedings/`, `award/`, seeds)
- `P/bid_evaluation/services/signing.py:289-290` and `reads.py:263-272` return `member`, `name`, `signed_at`/`signed` only
**Rule:** TRUST §2 line 31: "UI/export labels it **Test attestation — not an electronic signature**. No fake certificate, initials image or 'signed' proof."
**Reproduction / failing test sketch:** (static; not run) Sign a report on a test site; the signing and signed views show "Signed" and a time with no attestation label.
**Impact:** A test attestation is presented as a plain signature in Evaluation (Award shows the label, `award/services/reads.py:69`).

### AUD-EVL-020 — A verification plan never clears the chair's discussion item
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §4.3 (line 104), §7.3 (line 284) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-22 (row 46, 214)
**Evidence**
- `P/bid_evaluation/services/diligence.py:47-84` — `record_plan` takes no bid/requirement and never calls `findings.clear_item` (grep `clear_item|open_item` in `diligence.py` returns nothing); `record_outcome` (`:223-255`) also never clears it
- `P/bid_evaluation/services/clarification.py:92,105-106` and `issues.py:52` do call `clear_item`
**Rule:** EVL line 104: "The discussion item clears only when its attributed resolved/qualified conclusion, specialised clarification authorisation or verification plan, or durable linked support issue is committed."
**Reproduction / failing test sketch:** (static; not run) Needs-review finding creates the chair item; chair records a verification plan and later a verification outcome; the item stays Open ("Resolve evaluation concern" remains in the chair's list, `my_work_provider.py:84-95`). The requirement itself resolves via the outcome conclusion.
**Impact:** A stale chair task persists after the documented clearing event.

### AUD-EVL-021 — A failed second package read after intake rolls everything back without recording an issue
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.1 (EVL_SOURCE_INCOMPLETE, line 306) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-24 (row 71)
**Evidence**
- `P/bid_evaluation/services/intake.py:122` — `ran = checks.run(doc, reason="Initial", idempotency_key=key)` runs inside the intake body
- `P/bid_evaluation/services/checks.py:144-148` — `checks.run` re-releases each package and, if it is not `VERIFIED`, calls `fail("EVL_SOURCE_INCOMPLETE", ...)`, which raises through `records.command`'s savepoint (`records.py:69-79`)
- `P/bid_evaluation/services/sweep.py:54-56` — the sweep rolls back, logs an error and opens no Support Issue (the issue is created only on the first load failure, `intake.py:74-89`)
**Rule:** EVL line 306: a failed intake "System creates one support issue automatically".
**Reproduction / failing test sketch:** (static; not run) Make the second release of any package return not-verified after the first succeeded (transient custody flap): the intake rows are rolled back and the sweep retries each minute with only an error-log row.
**Impact:** A transient fault between the two reads yields no support issue or waiting notice; low likelihood.

### AUD-EVL-022 — EVL v0_5 says the Head's item clears on "return" but `ReturnEvaluationReport` carries no source event
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** EVL-CHG-001 v0_5 §5.6 (line 172, 174) vs §7.2/§10 (lines 264, 589) · **Module(s):** Evaluation · **Sources:** trace-evaluation F-23, D-6 (row 125)
**Evidence**
- EVL line 172 and 174: the Head's item "clears only on their recorded review or return/correction action … identify that source event"
- EVL line 264 and 589: `ReturnEvaluationReport` takes comments only, with no source-event argument
- `P/bid_evaluation/services/correction.py:269-284` — only `head_review` clears a Head item; `return_report`/`_apply_return` (`:111-123`) never touch `head_review_state`
**Rule:** The document contradicts itself: the clearing event "return" cannot name the source event it must identify.
**Reproduction / failing test sketch:** (static; not run) After delivery a supplement creates the Head's "Review opening update" item; the Head returns the report; the item stays Open until `record_head_review` is also called.
**Impact:** None beyond a stale Head item; the Head has `RecordHeadReview` as an explicit route. Owner should either add a source-event argument to the return or drop "return" from the clearing events.

### AUD-EVL-023 — EVL v0_5 control table, history and task-title claims are inconsistent
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** EVL-CHG-001 v0_5 control table (lines 11-18), §12.1 (lines 701-710), §5.6/§7.3 vs §12.4 N10 · **Module(s):** Evaluation (document) · **Sources:** trace-evaluation D-1, D-2, D-3
**Evidence**
- `docs/mvp-1-r1/15_bid_evaluation/KenTender_EVL-CHG-001_Bid_Evaluation_v0_5.md:13` — "Version / date | 0.4 · 30 September 2026" in the v0_5 file approved 3 October (line 3); lines 15-17 cite KT-STD-001 v1.12, TPR v0.13, BOP v0.10, TRUST-ADR-001 v0.1 although line 3 states TPR v0.16 changes are incorporated and TRUST-ADR-001 v0_2 exists
- same file `:701-710` — the history table has no v0.5 row and the v0.4 row (line 710) is detached from its table by a blank line
- same file `:295-296` — chair and Head opening-update items both titled "Review opening update for {tender}", while `:751` (N10) claims "distinct titles"
**Rule:** Internal consistency of an approved document used as the oracle for the code; the code follows the doc literally (`P/bid_evaluation/services/my_work_provider.py:197,201,204`).
**Reproduction / failing test sketch:** n/a (document review; static).
**Impact:** Traceability only; the approval header (line 3) remains the authority.

### AUD-AWD-001 — No segregation of duties anywhere in the evaluation → opinion → award-decision chain
**Severity:** High · **Classification:** SPEC GAP · **Doc:** AWD-CHG-001 v0_5 §6 (line 275); AUTH-ADR-001 v1_11 §5.8 (line 320); EVL-CHG-001 v0_5 §3 · **Module(s):** Award, Evaluation, Core (registry) · **Sources:** trace-award F1 (row 129, calibration 2); sweep-sod F8; trace-evaluation F-5 (rows 224, 225; D-5)
**Evidence**
- `P/award/services/guards.py:29-42` — `require`/`require_hop`/`require_ao` check only that the user holds the role (`people.holds`)
- `P/award/services/decision.py:110` — `RecordAwardDecision` gates on `guards.require_ao(user)` only; `P/award/services/opinion.py:41,81,141` gate opinion save/sign/return on `guards.require_hop(user)` only; grep `segreg|sod_tags|conflict` in `P/award/services/*.py` finds nothing relevant
- `P/award/services/people.py:37` — `holds` calls `authorise_record(user, business_role, purpose=PURPOSE_COMMAND)` with no record, action or SoD input
- `P/bid_evaluation/services/appointment.py:43-53` — `_ineligibility` excludes only non-internal users, the same-tender opening independent member and declared-conflict persons; the Accounting Officer or Head of Procurement may be appointed chair/member, and Evaluation's signer list is carried to Award (`P/bid_evaluation/services/award_seam.py:111-112`, `signatures.members`) but never compared with the deciding AO
- `kentender_core/kentender_core/services/business_role_registry.py:147,191` — the registry's `sod_tags` for Accounting Officer (`plan_adoption`, `publication_authorisation`, `tender_cancellation`) and Head of Procurement Function (`requisition_authorisation`, `tender_approval`, …) contain no evaluation, opinion or award-decision tag
**Rule:** AUTH §5.8: "Holding two roles is not a violation; performing incompatible decisions in the same evidence chain is. Segregation is evaluated against actual actions using the registry's `sod_tags` and the owning module's rules." AWD §6: "Use AUTH's existing enforcement; add no per-tender permission grants"; "Evaluation members … acquire no Award decision power". Neither Award nor Evaluation states the incompatible-action rule, so the code has nothing to enforce.
**Reproduction / failing test sketch:** (static; not run) 1. Give one user both the Accounting Officer and Head of Procurement Function assignments. 2. As that user appoint self as evaluation chair, sign the report, then `award.api.sign_opinion` (HOP) and `award.api.record_decision(outcome="Award")` (AO): each is accepted under one identity. Failing test: after HOP+AO on one user, `decision.record` should raise `AUTH_SEGREGATION_BLOCKED`; and a user present in `snapshot["signatures"]["members"]` should be refused as deciding AO.
**Impact:** One person can evaluate, recommend, sign the professional opinion and decide the award. **Owner decision needed:** define the incompatible actions (e.g. report signer ≠ opinion signer ≠ deciding AO; AO/HoP not appointable as members) and add the `sod_tags`; the code then needs the check.
**Verification:** CONFIRMED — `guards.py:29-42` + `people.py:37-39` (`authorise_record(..., purpose=PURPOSE_COMMAND)`, no SoD input) are the only gates on `decision.py:110` and `opinion.py:41,81,141`; `authorization_native.py:~85` states segregation "stays a domain rule" and neither Award nor Evaluation (grep segreg/sod) implements one; neither AWD v0_5 nor EVL v0_5 names an incompatible-action rule, hence SPEC GAP.

### AUD-AWD-002 — Funding is never re-read from Budget and an unavailable funding (or validity) read permits a positive award
**Severity:** High · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §3 (Budget row), §5.1 (line 93), §5.5 (line 141), AWD-IF-07 (line 528) · **Module(s):** Award, Evaluation, Budget · **Sources:** trace-award F2 (rows 31, 43, 90, 222, 223); sweep-money F11
**Evidence**
- `P/award/services/checks.py:77-80` — `f = state.snapshot(state.current_report(doc)).get("funding") or {}` → `restricted = bool(qualification) or short > 0`; Award has no Budget call (grep `funding` in `P/award/services/` finds only snapshot readers)
- `P/bid_evaluation/services/award_seam.py:115` — the snapshot's funding is `recommendation.get("funding") or {}` frozen at report-signing time
- `P/bid_evaluation/services/funding.py:35-52` — `None` when no reservations exist or the Budget read raises, so the report's funding fact is absent and Award's `funding()` returns `restricted: False` (see AUD-EVL-014)
- `P/award/services/decision.py:42-52` — `positive_guards` checks holds, recommendation and `v["expired"]` only; `P/award/services/checks.py:42-47` returns `{"known": False, "expired": False}` for an unreadable validity, so an unknown validity does not block the decision (it blocks only at delivery, `P/award/services/eligibility.py:47-49`)
- Nothing re-checks funding at decision, issue (`P/award/services/notices.py:95-109` `_stop_reasons`) or delivery (`eligibility.py:50-52`)
**Rule:** AWD §5.1: "Read-only checks cover … validity, funding … Distinguish an established restriction from an unavailable check. Neither permits an unsupported positive decision."; §5.5: conditions are rechecked "at decision, actual issue and Contracting delivery"; AWD-IF-07: "read-only current funding response with explicit unknown/failure result".
**Reproduction / failing test sketch:** (static; not run) (a) Make Budget's `get_funding_lineage` raise at evaluation time; deliver the report with empty funding; AO `record_decision(outcome="Award")` succeeds with clean `positive_guards`. (b) Report-time funding sufficient; consume the reservation before the decision days later: Award still passes. Failing test: with `funding == {}` and Budget unavailable assert `decision.positive_guards` returns a funding-unknown reason.
**Impact:** An award can be decided, notified and sent to Contracting on funding that was never verified or has since been withdrawn.
**Verification:** CONFIRMED — `award/services/checks.py:~77-80` reads funding only from the frozen report snapshot and `decision.py:42-52` `positive_guards` has no funding term; `checks.py:42-47` returns `known: False, expired: False` for an unreadable validity (only a separately synced Status-unavailable issue could still block the decision, and `decision.record` does not run sync), and AWD §5.1/§3 Budget row/AWD-IF-07 require the Budget read.

### AUD-AWD-003 — Heads of Procurement can end an authoritative order or a funding restriction with free-text "evidence"
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.6 (line 151), §5.10 (lines 255-272), AC-030 · **Module(s):** Award, Tenders · **Sources:** trace-award F12 (rows 24, 75, 110, 115, 117, 210)
**Evidence**
- `P/award/services/restrictions.py:153` — evidence is required only as non-blank (`... and not proof`); `:163-167` resolves the issue for `Restriction ended` / `Owner correction confirmed`
- `P/award/services/tender_events.py:49` — release evidence from a Tenders Resumption event is stored in `detail.release_evidence` but never required or compared in `disposition`
- `P/award/services/restrictions.py:166` — `if chosen == OWNER_CONFIRMED: checks.sync(...)`; `P/award/services/checks.py:120` opens the Funding issue with `source_event=f"funding:{rep.name}"` and `P/award/services/issues.py:25-26` returns an existing (even resolved) issue for the same `source_event`, so a funding restriction resolved by the HOP is never reopened for that report
**Rule:** AWD §5.6: an authoritative order "can be marked ended only from the operative release/expiry evidence and checks for continuing restrictions"; §5.10: Restriction ended needs "operative authority evidence"; Owner correction confirmed needs "authoritative owner receipt".
**Reproduction / failing test sketch:** (static; not run) A Tenders `Suspension` event creates an authoritative hold; HOP calls `record_disposition(outcome="Restriction ended", reason="x", evidence="y")` → resolved and the package can proceed. Likewise a Funding issue: `record_disposition(outcome="Owner correction confirmed", reason="x", evidence="y")` resolves it and `sync` cannot reopen it.
**Impact:** A single role holder lifts a statutory suspension, or clears a funding restriction permanently, on unverified text. Verification of "operative evidence" is partly impossible for free text, but system-received orders carry release evidence that is ignored.

### AUD-AWD-004 — Later restrictions and cancellation-after-notice do not reliably reach an already-delivered Contracting case
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.8 (line 185), AC-020 · **Module(s):** Award, Contracting (simulated) · **Sources:** trace-award F3 (rows 73, 84, 100, 200)
**Evidence**
- `P/award/services/restrictions.py:65-68` — `try: receipt = contracting.deliver_update(update)["receipt"]` / `except contracting.ReceiverUnavailable: receipt = ""`, then the update is appended with an empty receipt (`:69-70`)
- `P/award/services/sweep.py:12-24` — the sweep steps (`intake.retry_pending`, `tender_events.sweep`, `eligibility.sweep`, `notices.retry_failed`, `events.retry_pending`, `explanation.retry_pending`) include no update retry; no support issue is opened
- `P/award/services/restrictions.py:78` and `P/award/services/corrections.py:81` are the only callers of `_later_update`; `P/award/services/tender_events.py:68-71` (cancellation after notification) and validity expiry (`checks.py:112-117`) open holds with no update to a delivered package
- `P/award/test_services/contracting_receiver.py` creates no task for an update (`_receive(..., task=False)` per trace; static)
**Rule:** AWD §5.8: "Later orders, corrections or validity changes are delivered as separate immutable updates with required consumer acknowledgement and a task"; AC-020: "A later restriction reaches the existing Contracting case".
**Reproduction / failing test sketch:** (static; not run) Deliver a package; set the receiver down (`contracting_down=1`); `record_restriction(basis="Authoritative order", evidence=...)` → ok, `pkg.updates_json` row has `receipt: ""`; restore the receiver and run `award.services.sweep.run`: no update is delivered. Also cancel the tender after delivery: no Restriction update reaches Contracting.
**Impact:** Contracting may proceed on a package that is under a later order. Latent today because the only receiver is a simulation (no Contracting module exists on this bench), but the sender's retry/incident duty is Award's.

### AUD-AWD-005 — Case `outcome` is never set to "Award", so the HoD decision summary shows no outcome
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 header (OVS-P03, line 5); OVS-CHG-001 v0_6 §4.1 · **Module(s):** Award, Tenders summary · **Sources:** trace-award F4 (rows 226, 229)
**Evidence**
- `P/award/services/decision.py:64` — `records.bump(doc, decision_status="Award recorded", current_decision=decision.name, outcome="")`; `:85` sets "No award" and `tender_events.py:77` "Cancelled"; `eligibility.py:134` sets only the cycle's outcome to "Award"
- `P/award/services/reads.py:186` — `department_record` builds `decided = {"outcome": doc.outcome, ...}`; `P/award/services/stage_summary.py:67-70` — `outcome = {"label": "Outcome", "value": doc.outcome} if doc.outcome else None` and `ss.fact("Outcome", doc.outcome)`
**Rule:** AWD header: HoD "scoped final-decision summary"; OVS v0_6 §4.1: HoD sees "final AO decision/outcome/date and a disclosed decision-reason summary".
**Reproduction / failing test sketch:** (static; not run) As AO record an Award; read `reads.department_record(doc)` (or `stage_summary.for_tender` as a Head of User Department): `decision.outcome == ""`, no Outcome badge; date and reason are present. Test sketch: after `awarded()`, the summary must contain `Outcome: Award`. `P/award/tests/test_awd_home_provider.py` asserts only the absence of notice text.
**Impact:** The approved HoD/Tender summary cannot show that an award was made.

### AUD-AWD-006 — The real Evaluation producer hard-codes every annex as available
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.1 (line 91), AC-002 · **Module(s):** Evaluation, Award · **Sources:** trace-award F8 (rows 28, 182)
**Evidence**
- `P/bid_evaluation/services/award_seam.py:113` — `"annexes": [{"name": s, "available": True} for s in (content.get("sections") or [])]`
- `P/award/services/checks.py:37` — `if any(not a.get("available") for a in snap.get("annexes") or []): return "One required annex is unavailable."`
- `P/bid_evaluation/services/award_seam.py:111` — `signatures.required` is `len(sigs)` (the number of target rows), so it cannot exceed present rows
**Rule:** AWD §5.1: "The incoming package must identify every required report signature and the exact report/annex set. A missing, mismatched or unverifiable artifact creates a source issue automatically."
**Reproduction / failing test sketch:** (static; not run) Withhold or remove an annex artefact in Evaluation: `delivered_report` still returns `available: True`, so Award's "annex unavailable" source issue can fire only through the synthetic provider (`awd_intake test_incomplete_source_opens_the_exact_issue` uses `overrides={"missing_annex": True}`).
**Impact:** The missing-annex detection required by AC-002 is vacuous with real data.

### AUD-AWD-007 — Contracting package "contract terms" are constant strings, not mapped tender data
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.8 (line 179), AC-021 · **Module(s):** Award, Contracting · **Sources:** trace-award F10 (rows 26, 92, 201)
**Evidence**
- `P/award/services/eligibility.py:85-88` — `"delivery_and_warranty": "As issued in the tender and the supplier's response", "reservation_treatment": "As recorded in the tender's reservation lineage", "performance_security": "As published in the tender (Contracting verifies before signature)", "tender_security": "As recorded at submission"`
- `P/award/services/eligibility.py:84-86` — only `quantity` and `warranty` come from the report snapshot; there is no requirement/response mapping, reservation id or security amount (the reservation ids are available via `P/tenders/services/evaluation_seam.py:202`)
**Rule:** AWD §5.8: "The package includes the issued requirement and supplier response mappings needed for the contract, delivery/warranty commitments, applicable reservation treatment, published performance-security terms, tender-security references, and all current restrictions."
**Reproduction / failing test sketch:** (static; not run) Deliver a package; inspect `content_json["contract_terms"]` — literal sentences only; `awd_delivery test_delivered` asserts only amount/warranty/quantity.
**Impact:** Contracting would have to re-key mappings, reservation lineage and security terms, contrary to AC-021.

### AUD-AWD-008 — §88 validity extension and the notice's contracting window are not modelled
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.5 (line 141), §5.8 condition 5 (line 173) · **Module(s):** Award, Tenders · **Sources:** trace-award F11 (rows 66, 89); related to AUD-EVL-015
**Evidence**
- `P/tenders/services/award_seam.py:33-37` → `P/tenders/services/evaluation_seam.py:147-166` — `validity` returns only the published validity date (no extension, prior-extension count, duration or notice evidence)
- `P/award/services/checks.py:42-49` — `validity()` computes expiry from that date only; `P/award/services/tender_events.py:13` says extensions "are read live" but no code does
- `P/award/services/eligibility.py:47-49` — condition 5 tests only `v["known"] and not v["expired"]`; grep `contracting window|extension` in `P/award/services/` matches only that comment
**Rule:** AWD §5.5: "Tenders supplies the extension decision, prior-extension count, duration and notice evidence, checked against the effective legal profile"; §5.8 cond. 5: "Tender validity and the notice's contracting window remain current".
**Reproduction / failing test sketch:** (static; not run) After a lawful extension recorded by Tenders (when that exists) the published validity date is unchanged, so `checks.validity` reports expired and Award holds with `AWD_VALIDITY_EXPIRED` permanently.
**Impact:** A lawfully extended tender is treated as expired; the notice contracting-window condition cannot be enforced.

### AUD-AWD-009 — The "No award" follow-up task can never be completed
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.7 (line 161) · **Module(s):** Award · **Sources:** trace-award row 81
**Evidence**
- `P/award/services/decision.py:80` — `next_action_owner=hop or None, next_action_state="Open"` is the only writer of `next_action_state` (grep across `P/award/` code and `P/public/js/award` finds no other assignment)
- `P/award/services/tasks.py:64`, `P/award/services/next_steps.py:318`, `P/award/services/home_provider.py:317`, `analytics_facts.py:223` — the HOP task and next-step row are shown while `next_action_state == "Open"`
**Rule:** AWD §5.7: Record no award gives "one concrete next task for HOP … Store that task's action, owner and completion evidence".
**Reproduction / failing test sketch:** (static; not run) Record a No award with `next_action="Review whether the tender should be cancelled"`; the HOP item `next:<decision>` appears; no command exists to record completion or evidence, so it never clears (`awd_decision test_no_award_follow_up` asserts only the "Open" state, `:53`).
**Impact:** A permanent open HOP task on every No-award case, with no way to close it or capture completion evidence.

### AUD-AWD-010 — An open debrief request or missing debrief rule never blocks Contracting delivery
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.6 (line 149), AC-015 · **Module(s):** Award · **Sources:** trace-award row 72; divergence from proposed spec (legal profile unverified, production gate owner-held, §15)
**Evidence**
- `P/award/services/profile.py:31` — `"debrief_rule": "Test profile: an explanation request does not extend the waiting period; an open request does not block Contracting delivery."` is the only debrief rule, a string
- `P/award/services/eligibility.py:32-58` — conditions 1-7 include no debrief condition (grep `debrief` in `eligibility.py`, `clocks.py`, `guards.py`, `checks.py` returns nothing); an explanation request is Correspondence, not an Issue, so it never reaches `issues.holding`
**Rule:** AWD §5.6: "A missing applicable rule or unresolved effect on the waiting period prevents Contracting delivery until HOP records the supported disposition."
**Reproduction / failing test sketch:** (static; not run) Supplier `request_explanation` after notice, leave it open; once conditions 1-6 are met the package is delivered.
**Impact:** Latent until a verified legal profile exists (the unverified profile already blocks delivery with `AWD_RULE_UNVERIFIED`); the debrief gate must still be built.

### AUD-AWD-011 — Return to Evaluation dead-ends when the Head of Procurement who received the report is replaced
**Severity:** Medium · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.2, §5.9 (expired authority routes work to the current holder), §7 `ReturnEvaluationReport` · **Module(s):** Award, Evaluation · **Sources:** trace-award F20 (row 37)
**Evidence**
- `P/award/services/issues.py:66-74` — `hop_for` routes Award work to the current Head of Procurement when the recipient no longer holds the responsibility
- `P/award/services/opinion.py:141,150` — `return_report` passes only `guards.require_hop(user)` (any current holder) and then calls Evaluation with that `user`
- `P/bid_evaluation/services/correction.py:96-97` — `if not delivery or delivery.recipient_user != user: raise frappe.DoesNotExistError("Not found")`
**Rule:** AWD §5.9 / AUTH: an expired or replaced authority routes the task to the current holder; the replacement HOP is the actor the document expects to Return.
**Reproduction / failing test sketch:** (static; not run) Deliver a report to HOP-1; end HOP-1's assignment and appoint HOP-2; HOP-2 (who gets the "Prepare professional opinion" task) calls `award.api.return_report(...)`: Evaluation answers Not found; Award's opinion stays unreturnable.
**Impact:** After a change of Head of Procurement a report cannot be returned for correction by the current holder; the flow dead-ends until the original recipient is restored.

### AUD-AWD-012 — `RecordAwardDecision` does not read live tender status before committing
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.5 (line 141), §7 `RecordAwardDecision`, §8 `AWD_STATUS_UNAVAILABLE` · **Module(s):** Award · **Sources:** trace-award F5 (row 137)
**Evidence**
- `P/award/services/decision.py:107-138` — `record` calls `guards.open_case(doc)` (stored `doc.cancelled`, set only when `tender_events.consume` runs, `P/award/services/tender_events.py:73-77`) and `positive_guards`; it never calls `checks.tender_status` or `tender_events.consume`
- `P/award/services/notices.py:95-101` — `_stop_reasons` reads live status, so the batch is `Stopped` after the decision and the `AwardDecisionRecorded` event are already committed (`decision.py:63-64`)
**Rule:** AWD §5.5: the system "checks conditions again at decision, actual issue and Contracting delivery"; §8: unavailable status fails closed.
**Reproduction / failing test sketch:** (static; not run) Cancel the tender in Tenders (or `set_fact(tender, cancelled=True)`) before the Award sweep consumes the event; AO `record_decision(outcome="Award")` commits the decision, delivers `AwardDecisionRecorded` to Contracting, and the batch is Stopped.
**Impact:** Within the sweep lag a decision and a Contracting event exist for an already-cancelled tender; no notice goes out.

### AUD-AWD-013 — "Issue in progress" is not durable before the first outward effect and an interrupted issue has no recovery
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.4 (line 129-131), AC-010 · **Module(s):** Award · **Sources:** trace-award F6 (rows 53-55, 190)
**Evidence**
- `P/award/services/notices.py:129-130` — `records.update(batch, state="Issuing", status="Issue in progress", ...)` and `records.bump(doc, notification_status="Issue in progress", ...)` happen inside the same command transaction (savepoint, `P/award/services/records.py:142-150`) that then runs `_dispatch` for each notice (`:142-143`)
- `P/award/services/sweep.py:12-24` — no step recovers a case with `notification_status` "Issue in progress"/"Unknown"; `notices.retry_failed` handles only `status="Failed"`
- `P/hooks.py:174` — the only transport is the test mailbox (database-transactional), so the gap is latent
**Rule:** AWD §5.4: "A worker must verify that transition before the first outward effect. In-progress or unknown status cannot be treated as no notification. Recover an interrupted issue before allowing either route to proceed."
**Reproduction / failing test sketch:** (static; not run) Patch the transport to send then raise after the first of two recipients: the whole command rolls back including the "Issue in progress" marker while the first outward send stands. Assert `notification_status != "Not issued"` afterwards.
**Impact:** With a real channel, a crash mid-issue could leave an outward notice with `Not issued` recorded, allowing the pre-notification cancellation route.

### AUD-AWD-014 — Authority-status contract answers "no decision / not issued" from absence of a case
**Severity:** Low · **Classification:** CODE DEFECT (divergence from proposed spec: AWD-IF-02 is a proposed counterpart contract, §17.2) · **Doc:** AWD-CHG-001 v0_5 §7 (line 307), AWD-IF-02 (line 523) · **Module(s):** Award, Tenders, Evaluation · **Sources:** trace-award F9 (rows 149, 152, 214, 217)
**Evidence**
- `P/award/services/authority.py:36-41` — with no case `status()` returns `decision_status "No decision recorded"`, `notification_status "Not issued"` (source "No Award case"); `tender_status` returns `None` (`:54-59`)
- `P/tenders/services/evaluation_seam.py:193-197` — with no hook answer Tenders returns `{"status": "No award decision recorded", ... "source": "Tender status"}`; no durable tender-level status record exists (grep in `P/tenders` finds none)
- `P/hooks.py:171-172` — only `tender_status` (EVL vocabulary) and `cancellation_guard` (a string, no evidence/checked time) are published; `status()` (with notification fact, revision, `checked_at`) is not exposed
**Rule:** AWD §7: "Before an Award case exists, authoritative negative values must come from a durable tender-level record … Absence of a case or a failed lookup is insufficient."
**Reproduction / failing test sketch:** (static; not run) `tenders.evaluation_seam.award_decision_status(<tender with no Award case>)` → "No award decision recorded" with no durable record.
**Impact:** Spec conformance gap with little behavioural effect today: no decision can exist before an Award case does, and no notice can exist before a case.

### AUD-AWD-015 — `retry_operation` authority ignores effective dates
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §6 (line 279) · **Module(s):** Award · **Sources:** trace-award F15 (row 128)
**Evidence**
- `P/award/services/people.py:50-52` — `technical_operators()` selects `User Responsibility Assignment` with `status="Enabled"` only and no effective-period/derived-status check
- `P/award/services/recovery.py:52` and `P/award/services/reads.py:151` — `retry_operation` authority is `user in people.technical_operators()`
**Rule:** AWD §6: "Recheck active responsibility, scope, supplier link and signature authority at every action, not just page load." Contrast `people.holders` (`people.py:40-42`), which re-validates through `holds`.
**Reproduction / failing test sketch:** (static; not run) Give a user a Technical Operator assignment whose end date has passed but whose `status` is still Enabled; call `award.api.retry_operation`: accepted.
**Impact:** An expired technical operator can trigger idempotent retry of failed notice/event deliveries.

### AUD-AWD-016 — Award never checks the product profile or the published award method
**Severity:** Low · **Classification:** CODE DEFECT · **Doc:** AWD-CHG-001 v0_5 §5.1 (lines 93-94), §3 · **Module(s):** Award, Tenders · **Sources:** trace-award rows 17, 32
**Evidence**
- `P/tenders/services/award_seam.py:30` — `"award_method": "Lowest evaluated responsive tender"` is a literal; `product_key` is returned (`:29`)
- `P/award/services/sources.py:73` stores `award_method=facts.get("award_method", "")`; grep `product_key|award_method|GOODS-IT` in `P/award/services/` finds no comparison anywhere else
**Rule:** AWD §5.1: read-only checks cover "the recommendation's consistency with the published award method"; "The supported product is template key `IT-EQUIPMENT-OPEN-V1`, product profile `GOODS-IT-SIMPLE-V1`".
**Reproduction / failing test sketch:** (static; not run) Feed Award a delivered report for a tender with a different `product_key`: no check refuses it. Upstream, Evaluation's scope gate (`P/bid_evaluation/services/preparation.py:61-66`) already limits cases to the supported product, which bounds the effect.
**Impact:** The Award-side supported-scope and award-method consistency checks do not exist.

### AUD-AWD-017 — AWD v0_5 still carries "proposed"/"would establish" wording after approval
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** AWD-CHG-001 v0_5 lines 3, 8, 471, 538, 585 · **Module(s):** Award (document) · **Sources:** trace-award S1
**Evidence**
- `docs/mvp-1-r1/16_award/KenTender_AWD-CHG-001_Award_v0_5.md:3` — "Controlling approval — 3 October 2026" with "Earlier proposed/pending wording is drafting history superseded by this record"
- same file `:8` — "The proposed technical-reader rule is OVS v0.6 §4.2" (OVS-P05 is recorded approved, OVS v0_6 line 362); `:471` AC-027 "agree on Proposed status"; `:538` "Approval of this version would establish …"; `:585` "v0.4 is the current proposed successor. Approval … remain outstanding."
**Rule:** Internal consistency of an approved document used as the oracle.
**Reproduction / failing test sketch:** n/a (document review; static).
**Impact:** Implementers cannot tell whether OVS §4.2 (technical reader qualified read) is binding for Award; the code treats every technical user as operations-only (`P/award/services/people.py`, `reads.py:198-199`).

### AUD-AWD-018 — AWD v0_5 §15 says "Persist timestamps in UTC"; the project rule and the code store site time
**Severity:** Low · **Classification:** SPEC DEFECT · **Doc:** AWD-CHG-001 v0_5 §15 (line 479) vs AGENTS.md §4.4 "Instants (owner decision 26 Sep 2026)" · **Module(s):** Award · **Sources:** trace-award S2 (row 212)
**Evidence**
- `docs/mvp-1-r1/16_award/KenTender_AWD-CHG-001_Award_v0_5.md:479` — "Persist timestamps in UTC and display the site timezone."
- `AGENTS.md:117` — "Store every instant as a naive datetime in the site timezone … Only a serialized message between modules … carries ISO-8601 UTC"
- `P/award/services/clock.py:1-11` and `P/award/services/events.py:34` — site time stored; UTC only in the event payload via `to_utc_iso`
**Rule:** The approved document contradicts the owner's later project rule.
**Reproduction / failing test sketch:** n/a (static).
**Impact:** None in code (it follows the project rule); the document should be corrected at the next version.

## Dropped / downgraded

- trace-evaluation F-5 → merged into AUD-AWD-001 (evaluator/decider segregation) and AUD-EVL-016 (secretary declaration part).
- trace-evaluation F-7 (clarification disposition vs concurrent reply) → DROPPED. The stated interleaving cannot yield a Closed request with a committed reply: `submit_reply` locks the request row (`P/bid_evaluation/services/clarification.py:354`) then bumps the Evaluation Case row (`:370`) while `record_disposition` holds the case lock (`records.lock`, `records.py:85-90`) and later saves the request row held by the reply transaction, so InnoDB deadlocks and one side errors; and a stale-snapshot reply is rejected by Frappe's `check_if_latest` (`apps/frappe/frappe/model/document.py:1012-1038`, which reads `modified` `for_update`) because the disposition bumps the case. Not provable as a data-corrupting race.
- trace-evaluation F-14 (HoD "No responsive bids" reason lists bidder names) → DROPPED: OVS v0_6 §4.1 gives the HoD the outcome and its recorded reasons; bidder names are disclosed at opening; no rule violation provable.
- trace-evaluation F-15 (frozen content immutable only by convention, digest not re-verified on read) → DROPPED: no command path mutates a frozen version's `content_json` (only `signing.py:106` on a draft; `save_narrative` edits drafts only) and the controller blocks Desk saves without the command flag; remaining exposure is the general System Manager/DB write surface owned by the xc-authz part (immutable-records cluster).
- trace-evaluation F-18 (untested paths) → skipped per map; test gaps are not findings.
- trace-evaluation F-20 (EVL_REPLY_OVERDUE / EVL_EVALUATION_OVERDUE sentences re-typed in browser) → DROPPED: the evaluation sentence is also returned by the server (`reads.py:103`), wording is identical, no behavioural consequence.
- trace-evaluation D-4 (OVS §4.2 "proposed" vs P05 approved) and D-7 (tie-break source unnamed) → DROPPED as document-wording notes without a defect (D-4 covered by AUD-AWD-017's note; D-7: code states "The published tender has no tie-break rule", `comparison.py:37`, which the doc does not contradict); D-1, D-2, D-3 → AUD-EVL-023; D-5 → AUD-AWD-001; D-6 → AUD-EVL-022.
- trace-evaluation rows 59/70/78/108/172/193 (issue holder named HoP not Tenders owner; no waiting notice to AO; suspension guard coverage of some commands; report content lacks tender/criteria versions inline; evidence re-linking; unpaged register) → not written: no document rule violated beyond doubt, or the content exists in the evidence manifest (`evidence_manifest.py:94-106`); register paging belongs to AGENTS.md §6.11 UI scope and is not a defect in the audited rule set.
- sweep-sod F6 → AUD-EVL-013 (downgraded from CODE DEFECT to SPEC GAP: BOP-A17 says "later … Evaluation appointment", so the code follows BOP; EVL §3 is unqualified).
- sweep-sod F7 → merged into AUD-EVL-001 (classified CODE DEFECT rather than SPEC GAP because eligibility requires "no unresolved conflict" and the AO is the named resolver).
- sweep-sod F8 → merged into AUD-AWD-001; sweep-money F11 → merged into AUD-AWD-002; sweep-handoffs F-15 → AUD-EVL-014.
- trace-award F7 and F16 → owned by xc-core (concurrency / idempotency); not written. Source ids F17 and F19 do not exist in trace-award.
- trace-award F13 (signed opinion / decision / closed cycle immutable only by convention) → DROPPED: `working_opinion` excludes Signed rows so `opinion.save` cannot update a signed opinion; controllers block Desk writes; same residual as the immutable-records cluster.
- trace-award F14 (`respond()` does not check `n.status == "Given"`) → DROPPED: AWD §5.9 line 202 says "current issued notice", and the notice is issued/published when the batch is Issued; the doc does not require "given" evidence before a response, so a server/read-projection mismatch is not a rule violation.
- trace-award F18 (out-of-date draft text overwritten on re-save) → DROPPED: the draft stays readable while Out of date; AWD §5.3 does not require retaining text after the HOP re-saves.
- trace-award row 126 (technical read: no "after governed release" qualified read) → DROPPED: the code is stricter than OVS §4.2, and the document marks §4.2 proposed (AUD-AWD-017).
- Downgrades by the severity scale: trace-award F3 High → Medium (Contracting receiver is a simulation; latent), F5 Medium → Low (batch is stopped by the live check at issue), F6 Medium → Low (only transport is DB-transactional test mailbox), F9 Medium → Low (no decision/notice can exist without a case); trace-evaluation F-21 recorded as SPEC GAP (Medium); F-13 Low/Medium → Medium; F-17 Low/Medium → Low; trace-award F20 Low → Medium (documented flow dead-end on a responsibility change).
- Added beyond the source candidates, each verified: AUD-EVL-015 (missing Tenders producers; from trace-evaluation row 77 and trace-award rows 66/73/145), AUD-AWD-009 (No-award follow-up cannot be completed; trace-award row 81), AUD-AWD-010 (debrief gate; trace-award row 72), AUD-AWD-016 (trace-award rows 17/32), validity-unknown part of AUD-AWD-002 (trace-award row 65).

## Calibration notes

1. Conflict declarations and evaluator segregation server-side. Present: appointment refuses non-internal, same-tender independent opening member, declared-conflict and duplicate persons together (`P/bid_evaluation/services/appointment.py:43-53`, reasons `:28-34`); a declared conflict ends eligibility and bid reads (`roster.py:69-78`, `findings.py:31-39`, `reads.py:62`). ABSENT or defective: a member can reverse their own conflict (AUD-EVL-001, `declaration.py:51-55`); a member-secretary keeps reads (AUD-EVL-010, `reads.py:62`); the secretary needs no declaration (AUD-EVL-016); no evaluator ≠ opinion signer ≠ award decider rule exists in code, docs or the role registry (AUD-AWD-001; `award/services/guards.py:29-42`, `business_role_registry.py:147,191`); opening-independent exclusion is one-directional (AUD-EVL-013).
2. Frozen/sealed evidence and report immutability. Present: the evidence manifest is frozen with the signed report and carries its own digest (`signing.py:98,114`, `evidence_manifest.py:113-126`); Award recomputes the report digest before accepting it (`award_seam.py:83`, `digest_verified`); Desk saves of Evaluation and Award records are refused without the command flag (`evaluation_report_version.py` `validate`; `award_professional_opinion.py` `validate`); a signed Award opinion is never the "working" opinion (`state.working_opinion`). Not found defective: no command path rewrites frozen content (AUD-EVL-015 candidate dropped). Residual System Manager/DB write exposure is owned by the xc-authz part.
3. Scoring arithmetic. No weights or scores exist by design. Money is `Decimal` in checks, comparison and funding (`rules.py:229-264`, `comparison.py:40-93`, `funding.py:27-57`) and exact strings in Award (decision amounts are Data fields, `award/services/decision.py:57-61`). Defects: rounding mode ignored (AUD-EVL-018); a single member finding resolves a price discrepancy (AUD-EVL-003); a qualified outcome cannot be frozen (AUD-EVL-002); `float(rec['evaluated_total'])` only formats report text (`report.py:162,180`, display-only, owned by the float-money cluster of xc-core). Multi-bid ranking, ties and funding shortfall have no test (not a finding).
4. Bid Opening → Evaluation consumption. Present and verified field by field: consumer `intake.py:81,95-106` against producer `P/bid_opening/services/completion.py:37-45`; completion digest recomputed (`P/bid_opening/services/evaluation_seam.py:53-55`, `intake.py:77-78`); once-only key `intake:{tender}:{handoff_id}` (`intake.py:65`) with unique `operation_key`; no assessment intake from an incomplete or cancelled opening (`intake.py:51-58`). Gaps: opening exceptions and `render_digest` unused (AUD-EVL-008); supplements consumed once by key but with no recheck before freezing (AUD-EVL-005).
5. Evaluation → Award payload. Present: `award_seam.py:70-119` supplies exactly the fields Award reads (`award/services/intake.py:60-65`, `checks.py:31-39,60-80`, `eligibility.py:15-32`); the outcome literal "Recommendation" and the tie text (`comparison.py:36` vs `award/services/checks.py:23`) match. Mismatches: `annexes[*].available` hard-coded (AUD-AWD-006); funding block absent when Budget unreadable (AUD-EVL-014 / AUD-AWD-002); delivery can bypass rechecks via `retry_delivery` (AUD-EVL-004).
6. Award-status service for Tenders cancellation. Present: Award publishes `kt_tender_cancellation_guards` → `authority.cancellation_guard(*, tender)` (`hooks.py:172`, `authority.py:76-90`), Tenders calls it through `award_seam.cancellation_refusals` (`P/tenders/services/award_seam.py:42-48`, `cancellation.py:128-132`); the contract matches (kwarg, string return, Not issued ⇒ ""), locks the case row (`authority.py:83`) and refuses on Issued, Issue in progress and Unknown. Gaps: no durable tender-level record and `status()` not exposed (AUD-AWD-014); interrupted issue not recoverable (AUD-AWD-013); the post-lock read is a plain read (REPEATABLE READ stale-read class, owned by xc-core item 1 / trace-award F7).
7. Replay idempotency. Present: one intake per opening completion (`intake.py:65`); Evaluation report delivery keyed `{case}:{version}` (`signing.py:192-196`); Award intake keyed `receive:{kind}:{delivery}` with unique `source_delivery` (`award/services/intake.py:27-37`); one `AwardDecisionRecorded` per decision (`award/services/events.py:50-51`); tender events keyed by source event (`award/services/tender_events.py`). Residual concurrent-duplicate and journal-before-lock weaknesses are owned by xc-core item 11 (trace-award F16 not written here).
