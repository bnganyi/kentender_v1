# TPR-CHG-001 v0.12 — Tenders implementation plan

| Control | Value |
|---|---|
| Authority | `KenTender_TPR-CHG-001_Tenders_v0_12.md`. Its control table reads "**Approved** — Project Owner, 26 September 2026; supersedes unapproved v0.11". The baseline register (`98_work_progress/KenTender_Baseline_Register.yaml`) still records `requirement_status: "Project Owner review"` for v0.12 with an empty `approval_date` — a register/document disagreement reported here, not resolved (FU-21). |
| Sibling authorities consumed | KT-STD-001 v1.8 (§2.9 journey tracker and next-step block, §3A technical read, §3B next-step runtime contract and dead-end test); AUTH-ADR-001 v1.10; REQ-CHG-001 (`AuthorisedRequisitionHandoff` as built: v1.4 payload, 26 Sep seam fix); PLN-CHG-001 v1.27 (guidance precedent; `RecordTenderMilestoneActual`); CFG-CHG-002 v0.16; STD-TPL-001 v0.10 and STD-TPL-IMP-001 v1.1 (installed release, shared `CompilePublishedBidDefinition`); BDS-CHG-001 v0.7 (candidate registration and clarification producer — not built). |
| Design | `design/` — the Project Owner's 26 Sep 2026 board set: fifteen `.dc.html` boards (TPR-DES-01..14; DES-11 is now **Respond to Supplier Clarification**), `TenderGuidance.dc.html` (props-driven guidance component embedded on DES-03..13), `Index.dc.html`, and `Handoff - Journey Tracker and Next-Step Block.md` (approved by the Project Owner for formalisation in the Industry design system, 26 Sep 2026). The v0.8 boards are in `retired/design/`. Same `_ds/kentender-industry-82d82607…` bundle (md5-identical). |
| Predecessor cycle | TPR-CHG-001 v0.8 (Phases 0–9 closed 19 Sep 2026; plan, tracker and follow-ups now `retired/TPR-CHG-001_v0_8_*`) plus the STD-TPL-IMP-001 cutover (commits `8e5ca5c9`, `765f0675`). **This cycle extends that build; it is not a rebuild.** |
| Companions | `TPR-CHG-001_IMPLEMENTATION_TRACKER.md`, `TPR-CHG-001_FOLLOW_UPS.md`, `RUNBOOKS.md`, `evidence/v0_12/`. |
| Prepared | 26 September 2026 |
| Status | Approved for implementation by the Project Owner, 26 September 2026 (session instruction: "Complete the implementation without waiting for further prompting"). |

## 1. Governing approach

v0.12 adds three versions of change the v0.8 build never received:

- **v0.10 supplier side** — general supplier clarifications from registered bid candidates (replacing the addendum-only inquiry), candidate notices with delivery evidence, the Published Bid Definition frozen at publication authorisation with a successor per addendum, and subject-scoped channel confirmations.
- **v0.11 release lifecycle** — largely delivered by the STD cutover; addendum issue must re-verify the bound release, and Tenders needs its own switched-Off boundary tests.
- **v0.12 workflow guidance** — server-derived `next_step`, the five-stage journey, guard reasons with fixes, the §5.11 hand-off register, the material-addendum cancellation-review route and draft discard; every screen re-ported to the new boards.

The v0.8 transactional mechanics are kept: envelope/journal idempotency, closed error set, digest-addressed documents, the generic channel-confirmation engine, the event outbox and the Planning actual. Phases 0–2 are horizontal; Phases 3–12 are vertical per board (server read/command → Vue port → vitest → one Playwright spec → live browser check); Phase 13 is release evidence.

## 2. Owner decisions (26 September 2026)

| # | Decision | Recorded instruction |
|---|---|---|
| OD-1 | **Update the shared guidance component** to the approved handoff design. | "Update the shared one (Recommended)" — change the shared component to match the approved design so every module looks the same. |
| OD-2 | **Build everything**, including supplier clarifications and candidate notices, against a Tenders-side stand-in for the Bid Submission candidate registry. | "Everything, with a stand-in (Recommended)". |
| OD-3 | Implement to the end without intermediate check-ins. | "Complete the implementation without waiting for further prompting". |

OD-1 note (found during planning): PLN-CHG-001 v1.27 line 1271 fixes Planning's reduced tracker text — "One line: **Stage {n} of 7: {label} — {holder}**" — and line 1917 places Planning's next-step line in the header ("The header state row … is replaced by the next-step line"). Six Planning/core tests pin these. The shared **visual design** (bars, stage numbers, state lines, the 3px Your-turn rule, the "Waiting on someone" label that KT-STD-001 v1.8 §2.9.1 already uses, the narrow-width switch) changes for every module; the **reduced wording and placement** become per-module settings so Planning's approved wording survives. Budget does not mount the shared guidance.

## 3. Decision register

v0.8 decisions D1–D24 (`retired/TPR-CHG-001_v0_8_Implementation_Plan.md` §4) remain in force except where amended below.

| # | Decision | Why |
|---|---|---|
| D2′ | **Doctype set amended.** New: `Tender Clarification` (§4.9), `Tender Candidate Notice` + child `Tender Candidate Notice Attempt` (§4.9A), `Tender Bid Definition` (W4), `Tender Candidate Registration` (stand-in, W2). Changed: `Tender Publication` (definition id/version/digest + component digests), `Tender Addendum` (`issue_decided_by/at`, `issued_at` = effective instant, successor-definition fields, `predecessor_addendum`, `cancellation_review_status`, `Discarded` status), `Tender Channel Confirmation` (`subject_type` "Tender package"; DB unique index), `Tender Cancellation` (status fields), `Tender Task` (`holder`, `sender`, §5.11 types). Removed: `Tender Addendum Inquiry`. | §4; v0.10/v0.12 model. |
| D6′ | Unchanged publication-rule source (CFG Publication obligations). The **candidate-notice** cancellation obligation is now derived from the candidate registry and dispatch evidence (§4.10 `candidate_notice_status`), not recorded by hand. | §4.9A, §4.10. |
| D8′ | Candidate boundary: `services/candidate_gateway.py` resolves hook `kt_tender_candidate_registry`; with no registered provider it uses the Tenders **stand-in** (W2). Clarifications arrive through a service-identity producer (`Tender Inquiry Producer` role kept, renamed in copy only) with `(producer, inbound_event_id)` deduplication. | OD-2; §3, §4.9. |
| D13′ | `errors.py` = exactly the thirty-five v0.12 §8 codes (adds the six clarification/notice/reservation codes; removes `TND_INQUIRY_LATE`). | §8. |
| D16′ | Compatibility = the **nine** §5.3 checks (adds County-residents and reservation-rule availability). | §5.3. |
| D25 | **Published Bid Definition** is compiled only by the shared STD compiler (`std_templates/services/runtime.py::compile_published_bid_definition_for`) from a Tenders-built `TenderVersionProjection v1`; frozen in the `AuthoriseTenderPublication` transaction and, per addendum, in `IssueAddendum`; activated on the final addendum channel confirmation. Tender-local response/evaluation/contract builders are retired. | §4.5.4, §5.6, §16(28), TPR11-AC-007. |
| D26 | **Guidance** = `tenders/services/guidance.py` (§5.9 states × actors → `ns.answer`), `tenders/services/guards.py` (§5.10 rows → `ns.guard`), `tenders/services/handoffs.py` (§5.11 items opened/cleared inside command transactions; notifications via `kentender_core.services.notification_service.emit_notification_log`); `allowed_actions` is derived from the guards. Reads return `next_step` + `journey`. Dead-end conformance in `tests/test_dead_end_matrix.py` (`make tenders-dead-end-gate`). | KT-STD-001 v1.8 §3B; §5.9–5.11. |
| W1 | Boards govern structure; spec §10/§10.17 governs content. Content the board regeneration dropped is restored and registered as a departure (DES-14 publication-not-configured split; DES-10 recorded AO reason; DES-12 Tender fact; DES-13 Requisition fact; DES-05 mappings/digests). Where §§10.7, 10.8, 10.14 narratives contradict §10.17, §10.17 wins. | Spec controls content; boards are the build source for structure. |
| W2 | Candidate **stand-in**: minimal `Tender Candidate Registration` doctype + service-identity register command standing in for **Start bid**; field names from BDS v0.7; retired when BDS registers the real provider. | OD-2. |
| W3 | Notice delivery through hook `kt_candidate_notice_transports`; default transport records only **Sent**; seed/test transports supply Delivered/Failed provider evidence. | §4.9A "Sent is never displayed as Delivered". |
| W4 | `Tender Bid Definition` rows (Frozen / Effective / Superseded); Publication and Addendum carry id/version/digest; the Approved Version is never written. | §4.5.4, §4.6, TPR09-AC-096. |
| W5 | Addendum return keeps the submitted row (`Returned`) and creates a copied Draft linked by `predecessor_addendum`; discard sets `Discarded`. Neither status is in §4.8's list → FU. | §7.4 `ReturnAddendumForCorrection`, `DiscardAddendumDraft`. |
| W6 | Cancellation review = a `Tender Task` of type "AO cancellation review" + `Tender Decision` rows; `cancellation_review_status` on the addendum blocks a repeat request. | §7.4, TPR12-AC-012. |
| W7 | Dev-site data: addendum fields renamed by patch; `Tender Addendum Inquiry` dropped (free-text identity cannot map to a registration); canonical reseed. | Owner allows dev-site teardown. |
| W8 | DES-14 Superseded **Continue** is offered by the server and remembered for the browser session only. | §10.15. |

## 4. Conflict register

| # | Conflict | Disposition |
|---|---|---|
| C17 | Register says v0.12 "Project Owner review"; the document says Approved 26 Sep 2026. | Build to the document; FU-21 for the register owner. |
| C18 | PLN v1.27 pins Planning's reduced wording and header placement; the Tenders handoff specifies a different region. | OD-1 note: per-module settings. |
| C19 | Handoff §5 accent rule vs KT-STD-001 v1.8 §2.9.3 rule 6. | Build the handoff (owner-approved); FU-22 to KT-STD. |
| C20 | §4.8 status list lacks `Returned`/`Discarded`. | W5; FU-23. |
| C21 | Board regeneration dropped spec content (W1 list). | W1; FU-24. |
| C22 | §13.2 still names Alice Njeri / Daniel Otieno. | D20 stands (carried FU-03). |
| C23 | No BDS candidate registry or clarification producer exists. | W2/D8′; FU-25 (retire stand-in when BDS lands). |
| C24 | Header cites `AuthorisedRequisitionHandoff v1.3`; REQ builds v1.4. | Consume v1.4 through `handoff_gateway` (26 Sep seam fix); FU-26. |

## 5. Site-safety protocol

1. Tenders and Requisitions Python tests historically wiped **every** Requisition and Tender on the site. Phase 0 scopes those wipes; until proven, take `bench --site kentender.midas.com backup --with-files` before any such run and record it in the tracker.
2. Never run Python tests while Playwright runs; never kill a run part-way; check `pgrep -af "playwright test|run-tests"` first (another session may share the site and git index).
3. After a run that touched Requisitions: `recover_orphaned_drawdowns(commit=True)`, `make seed-canonical SITE=kentender.midas.com THROUGH=tenders REBUILD=True`, `make seed-canonical-validate`.
4. UI runs: `make ui-queue-check` first; `restore_site` after each gate.
5. Git: stage explicit paths only; check `git diff --cached` before each commit; commit at the end of each phase.

## 6. Phase sequence

| Phase | Name | Exit (= tracker gate) |
|---|---|---|
| 0 | Docs, safety, housekeeping | New plan/tracker/follow-ups; design set committed; scoped fixture wipes proven by a counts test. **TND12-G00** |
| 1 | Schema, errors, contracts, Published Bid Definition | Doctypes/patches migrate clean ×2; 35 error codes; nine compatibility checks; STD digests bound; definition compiled from the shared compiler; schema/services gates green. **TND12-G01** |
| 2 | Shared guidance, Tenders guidance/guards/hand-offs, harness | Core restyle + per-module settings; Planning re-verified; Tenders reads return `next_step`/`journey`; guards; hand-offs; dead-end matrix; fidelity harness. **TND12-G02 (CP1)** |
| 3 | Slice A: DES-03/04/05 preparation | **TND12-G03** |
| 4 | Slice B: DES-06/07 decisions (+ definition freeze) | **TND12-G04** |
| 5 | Slice C: DES-08 publication confirmation | **TND12-G05 (CP2)** |
| 6 | Slice D: DES-09 published + clarification intake + notice engine | **TND12-G06** |
| 7 | Slice E: DES-10 addendum (seven variants) | **TND12-G07** |
| 8 | Slice F: DES-11 supplier clarification | **TND12-G08** |
| 9 | Slice G: DES-12 cancel (five variants) | **TND12-G09 (CP3)** |
| 10 | Slice H: DES-13 correction states | **TND12-G10** |
| 11 | Slice I: DES-14 common states | **TND12-G11** |
| 12 | Slice J: DES-01 workspace, DES-02 start | **TND12-G12** |
| 13 | Seeds and release evidence | **TND12-G13 (CP4)** |

Phase detail is the approved session plan, transcribed into the tracker's work register.

## 7. Verification commands

```bash
# Focused Python — from /home/midasuser/frappe-bench
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tenders.tests.<module>
# Component / browser — from apps/kentender_v1
npx vitest run --project tenders
npx playwright test --workers=1 tests/ui/smoke/tenders/<spec>.spec.ts -g "<test>"
# Assets
cd /home/midasuser/frappe-bench && ./scripts/bench-with-node.sh build --app kentender_procurement
# Gates
make tenders-schema-gate tenders-services-gate tenders-dead-end-gate
make ui-tenders-<slice>-gate ui-tenders-fidelity-gate ui-tenders-release-evidence-gate
make seed-canonical SITE=kentender.midas.com THROUGH=tenders REBUILD=True && make seed-canonical-validate SITE=kentender.midas.com
```

## 8. Non-goals

Bid submission itself, tender box, opening, evaluation, award, contract; a real publication adapter (§5.5.1 stays closed); a real bidder portal (BDS); template/rule configuration screens; retiring the legacy `publications`/`tender_management` surfaces (carried FU-08).
