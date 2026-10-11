# Follow-up 2 — methods and release 1.5, correction and addendum, draft update, incident-read auditing, PR-001 procedure, workbook (11 October 2026)

Follows `KenTender_Tender_Security_Followup_Reconciliation_2026-10-10.md`. The Project Owner’s decisions of 10 October 2026 on the four open points are quoted in part in each document’s control table. The eight documents below were **approved by the Project Owner on 11 October 2026** (“Mark the documents as approved”); nothing is committed.

## 1. What was done

| Decision | Result |
|---|---|
| 1. Use the existing addendum process | The two tender-security statements are two **non-material addendum rows** with option lists (choice list in the Addendum editor); the existing stale, open-period, late-amendment/deadline and channel-confirmation rules apply; a closed Tender cannot be amended. Missing system data for a requirement the published Tender already makes explicit is an **auditable correction** (`CorrectSecurityStatement`: Head of Procurement Function; where the published Tender states it, and the basis; append-only; one per Tender; changes nothing published). Bid Submission reads the correction only where the published definition states neither. |
| 2. Conditional proof upload in the next release | **Template release 1.5** built, validated (22 checks) and installed on the test site: upload → attachment required; issuer-supplied → its own group with **no attachment**; paper → prescribed electronic copy plus delivery instructions (the Tender Data Sheet row gains the sentence); no security → neither group. The Tender’s method is now one of three (bidder uploads / issuer supplies / paper). **Explicit update:** `UpdateDraftTemplateRelease` moves only an unpublished Draft, only for a Procurement Officer, and the Draft’s release notice offers **Update to the current release**; published Tenders keep their release. A pending issuer response blocks nothing (tested). |
| 3. Incident-detail read auditing | `GetIncidentDetails` names a **purpose** and writes one sealed **Opening Incident Access Event** (actor, capacity, time, incident, action, purpose, outcome; refusals too; no content, no free text); exports write one event per incident; a page refresh writes nothing; the trail is read only by the Auditor and the Accounting Officer; the incident panel asks for the purpose before showing details; the support holder alone sees the envelope. Bid Submission incident notices no longer link to the sealed record either. |
| 4. PR-001 procedure and closure work | **TRUST-OPS-001 v0.1** drafted (declaration, authorised support access, permitted diagnostics, recovery without exposing sealed contents, evidence preservation, escalation, closure review, test plan, exceptional access out of scope). The **Documentation Control workbook** now matches the register cell by cell; `scripts/sync_control_workbook.py` does it and verifies it. |

## 2. A conflict the Owner must resolve

The Owner’s table has a fourth row, **No security required**. Release 1.5 supports it at response level, but the Tender details control does **not** offer it: this product’s issued documents say a Tender Security is required (ITT 18.2) and the template’s insertion-point register fixes the treatment to ‘Tender Security’, excluding the Tender-Securing Declaration path. A Tender that stated no security would publish documents that contradict it. Offering it needs an Owner-approved document variant (register item FW-013). Until then it stays unavailable.

## 3. Documents (approved 11 October 2026)

BDS v0.16, TPR v0.20, STD-TPL v0.17, BOP v0.15, TRUST-ADR v0.6, AUTH-ADR v1.15, SEED-002 v0.7 and the new TRUST-OPS-001 v0.1; the register has decisions DEC-053 to DEC-056, interface IF-028, delivery item TSI-003, PR-001 updated, and the future-work item above. Each new version passes the preservation check and introduces no consistency error (the remaining errors are in the earlier versions). New wording in the Tender Data Sheet row, the issuer mapping’s result rule and the procedure’s severity classes, time targets, review period and retention are the drafter’s proposals, marked as new content.

## 4. Tests

Run on `kentender-test.local`, one run at a time. Python: bid_submission 25 modules (all passing after fixes), security duty, intake and verification, sealed surfaces, `test_security_and_price` (27, including the three methods, the pending-issuer rule and the correction), bid_opening `test_bop_incident_sealing` (15, ten of them new for the audited reads), `test_bop_pre_session` (22), tenders `test_security_statement_review` (11: correction, addendum, closed Tender, draft update and its notice), `test_documents`, `test_lifecycle`, `test_open_period`, `test_read`, `test_published_release`, `test_bds_seams`, `test_bid_definition`, `test_serializer`, bid_evaluation `test_evl_rules` and `test_evl_seams`, std_templates `test_release_1_5_security` (all four rows of the Owner’s table at definition level) and `test_security_statements`; the frozen releases 1.2 to 1.4 compile byte for byte. Vitest: tenders (106) and bid_opening (55, including the new details panel) pass.

Failures found and fixed on the way: stale expectations (release 1.4 → 1.5, endpoint counts, the old notice link), `test_handoffs`, `test_start_bid`, `test_template_binding` (an Available Draft release that another release has replaced is now offered the update) and `test_bop_api`.

## 5. Not run, and open

- **Playwright** passed for the Tender details editor, the Tender release-evidence walk, the Addendum screen (including the new security choice list), the supplier Company task and the security intake. The incident-details panel has vitest and server tests but **no browser test** (it needs the Bid Opening demo profile), and the Draft’s “Update to the current release” action has server and notice tests but no browser test; `bop-release-evidence.spec.ts` was edited in the earlier round and still has not been run.
- **A screen for `CorrectSecurityStatement`**: the command and endpoint exist; the screen is owed.
- **Dev site**: migrated (the new tables were missing and would have broken published-Tender reads); release 1.5 is **not** installed on dev, so dev still binds release 1.4 until the owner switches it (a dev Tender that chose the issuer-supplied method would still show the attachment).
- **PR-001** stays open: the procedure is a draft, untested and unapproved; its tests (§11) are not run.
- Boards owed for the changed screens; nothing committed.

## 6. Approval of 11 October 2026

Approved: BDS-CHG-001 v0.16, TPR-CHG-001 v0.20, STD-TPL-001 v0.17, BOP-CHG-001 v0.15, TRUST-ADR-001 v0.6, AUTH-ADR-001 v1.15, SEED-002 v0.7 and TRUST-OPS-001 v0.1, each with the proposals it carries in full (including the v0.18 content carried by TPR v0.20). Only the control tables and each document’s approval-effect paragraph changed (plus two STD-TPL section headings and one TRUST-OPS opening line); the preservation check passes with those lines listed explicitly, and the register and the workbook were updated to match. EVL-CHG-001 v0.9, PRC-CHG-001 v0.13 and AWD-CHG-001 v0.6 were not in this set and remain proposed. Approval is not evidence of implementation or release; **PR-001 stays open** until the recovery procedure is tested and its results accepted.
