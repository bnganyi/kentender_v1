# Follow-up reconciliation — supplier security status, Tender-stated submission method, incident records, emergency access (10 October 2026)

Follows `KenTender_Tender_Security_Intake_Reconciliation_2026-10-10.md`. The Project Owner's answers of 10 October 2026 to five open decisions are quoted in part in each document's control table. Nothing here is approved or committed. Items 2 to 4 are implemented; item 5 is recorded as a production-readiness item.

## 1. What was done

| Item | Result |
|---|---|
| 2. Replace “Not yet matched” | A supplier reads its own actual status: **Original received** (receipt reference and time), **Original receipt not yet recorded**, **Issuer verification pending** (also confirmed / does not match / not requested), with “Security will be checked against your bid after opening.” It is worked out when the supplier reads its bid and stored nowhere. A guard test fails if supplier-facing source says “not matched”. |
| 3. Template and published Tender data | The Tender has two required controls with no default — how its security may be submitted (Electronic / Physical / Electronic or physical) and delivery of the original (Required / Not required). They travel through the projection and the tender-security selector into the published facts, and drive the supplier statement, advisory, the electronic block and the intake lookup. A Tender published before them reads **Original delivery not stated**, gets no advisory, no original is assumed and nothing it published changes; `get_security_statement_review` lists those Tenders. Released template vectors 1.2 to 1.4 compile byte for byte. |
| 4. Incident-record exposure | Opening Access Incident, Opening Exception, Opening Decision Item, Opening Entry and Opening Register Request are sealed (no DocPerm, controller refusal that also stops Administrator, deny hooks). The technical-search resolver for incidents is removed; the notice to support links to the opening page; the opening page shows a technical reader who is not the Opening access support holder no incident, no decision item and no count (“Held by Opening access support”). |
| 5. Break-glass | None added. Recorded as production-readiness item PR-001 (register, TRUST-ADR-001 §2B, BDS runbook §7) with operational recovery kept apart from access to sealed contents. |

## 2. A tension resolved, for the owner to confirm

Earlier the rule was “no intake is matched to a bid before the opening”. The owner now wants the supplier to see its actual status before opening. Reconciliation made in the documents (BDS v0.15 §4.8, BOP v0.14 §5): the **stored** match still waits for the opening boundary and nothing shows procuring-entity or intake staff which bid presented which security; the supplier's own read is computed in memory from its own instrument facts and counts an intake only when exactly one active bid and exactly one intake carry that instrument. Residual risk, stated plainly: a supplier who knew another bidder's exact guarantee reference, issuer and amount could type them into its own bid and, if that bidder's own bid does not yet carry them, learn that an intake exists for that instrument. Once the other bidder's bid carries the same instrument both read “not yet recorded”. Knowing another bidder's guarantee reference is itself a leak outside this system; I judge the residual small and ask the owner to confirm it is acceptable.

## 3. Decisions needed

1. How does a published Tender state its method and original delivery — by a new addendum kind (recommended) or by republication? Until decided nothing changes a published requirement.
2. When may the successor template release make the proof and electronic submission conditional on the published method (STD-TPL-001 v0.16 TPL16-CHG-003)? Until then a Physical-only Tender still shows the proof upload; BDS hides the electronic submission and verification for it.
3. Is an audit event for each Opening access support read of an incident's details wanted before production? It is not built (BOP v0.14 §6, TRUST v0.5 §2B item 6).
4. PR-001: the incident-recovery procedure (authorisation, scope, duration, audit evidence, recovery steps).

## 4. Tests run (kentender-test.local, one run at a time)

Python, all passing after fixes: bid_submission 28 modules including `test_security_and_price` (25), `test_security_duty` (14), `test_security_verification` (9), `test_company_task` (7), `test_review_task` (7), `test_sealed_surfaces` (6), `test_sealed_bid_desk_read` (5), `test_submission` (11), `test_security_wording_guard`; bid_opening `test_bop_incident_sealing` (5, new), `test_bop_api`, `test_bop_pre_session` (22), `test_bop_ceremony`, `test_bop_record`, `test_bop_public`, `test_bop_leakage`, `test_bop_dead_end`, `test_bop_intake_duty`; bid_evaluation 6 modules; kentender_core authorization, registry, administration, technical operator; tenders `test_serializer`, `test_lifecycle`, `test_read`, `test_publication`, `test_open_period`, `test_bid_definition`, `test_bds_seams`, `test_published_release`, `test_template_binding`, `test_documents`, `test_dead_end_matrix`, `test_security_statement_review` (new); std_templates frozen releases 1.2 to 1.4, `test_compiler`, `test_binding`, `test_security_statements` (new). Vitest: bid_portal 391, tenders, bid_opening and tender_security_receipts specs pass. Playwright: `tnd-editor-details`, `tnd-release-evidence`, `bds-security-intake`, `bds-security-duty`, `bds-sealed-access`, `bds-company-task`, `bds-review`, `bds-release-evidence` pass.

Failures met and fixed in this pass: stale expectations (the old advisory text, the incident resolver, the endpoint count, “Confirmed” now “Issuer verification confirmed”); `physical_receipt_status` fixtures; and a weakness in `test_sealed_surfaces` whose System Manager address named a user that did not exist, so its System Manager checks had passed vacuously — corrected and passing.

`test_acceptance_gaps` still fails on stepper labels from earlier uncommitted portal work (not caused by these changes).

## 5. Not run, and open

- `bop-release-evidence.spec.ts` was edited (the technical-status expectation) but not run: it needs the Bid Opening demo profile.
- Dev site not migrated and not reseeded. Hooks take effect there now (sealing, Tender details controls); the Opening DocPerm rows are removed only by migration; published dev Tenders have no statements and will appear in the review list. Reseeding dev is still blocked by stray older Afya supplier organisations.
- Documentation Control workbook (.xlsx) not updated; the register is.
- Boards owed: BDS-DES-15 redraw, duty page, Company/Review/Submit status facts, Tender details task.
- The workspace sidebar JSON was reverted by `bench migrate`'s reverse sync during this work; the intake and duty links were reapplied and survive a migrate.
- All seven documents are Proposed (BDS v0.15, BOP v0.14, TRUST v0.5, AUTH v1.14, STD-TPL v0.16, TPR v0.19, SEED-002 v0.6); the document-change scripts pass preservation and introduce no consistency error.
