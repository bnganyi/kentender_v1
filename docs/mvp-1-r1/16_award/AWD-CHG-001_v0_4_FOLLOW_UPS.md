# AWD-CHG-001 v0.4: outstanding follow-ups

| Control | Value |
|---|---|
| Version | 0.4-follow-ups.2 |
| Date | 30 September 2026 |
| Status | Open register |

This register holds items found while planning and building AWD-CHG-001 v0.4: corrections owed to other documents, gaps in sibling contracts, capabilities with no provider on this bench, and production-gate items. Under owner decision OD-A ("Build now, amend later"), none blocks this module's own build unless its row says so.

**Inherited:** FU-EVL-15 (the delivered report has no Award consumer) closes when tracker rows AWD4-204 and AWD4-301 are Done.

## 1. Owner-document amendments owed (OD-A)

| ID | Item | Severity | Owner | Status |
|---|---|---|---|---|
| FU-AWD-01 | **EVL-CHG-001 amendment (AWD-IF-01).** Record the `kt_evaluation_report_consumers` hook called after delivery; `award_seam.py` (`delivered_report`, `take_up`, `return_report`, `corrections_after`); the new delivery `review_state` value "With Award" that ends EVL's "Review evaluation report" row; and that EVL's decision status now comes from Award's authority status. | High — spec | EVL owner | Open |
| FU-AWD-02 | **TPR-CHG-001 amendment (AWD-IF-02).** Durable tender-level decision and notification status; the serialised issue/cancel transition (`kt_tender_cancellation_guards`); post-close cancellation, suspension and validity-extension events (§5.5, §5.7), which today exist only as simulated owner events; acceptance/reply terms as published facts. | High — spec | Tenders owner | Open |
| FU-AWD-03 | **BDS-CHG-001 amendment (AWD-IF-03).** Authoritative award audience (submitted, withdrawn, replaced); the signatory-only award response; contact-correction receipts; the supplier route `/supplier/awards/{notice_id}` and its link from the bid overview. | High — spec | BDS owner | Open |
| FU-AWD-04 | **PRC-CHG-001 amendment (AWD-IF-04).** Indexing of the opinion, decision, notices and giving proof, responses, correspondence, restrictions and consumer receipts. Not built: no PRC change was made (plan D6). | Medium — spec | PRC owner | Open |
| FU-AWD-05 | **Contracting counterpart document (AWD-IF-05).** `ReceiveAwardPublicationEvent`, `RecordContractAwardPublication`, package receipt and **Prepare contract** task, later-restriction updates. Only a synthetic receiver exists (plan D10). | High — spec | Project Owner | Open |
| FU-AWD-06 | **KT-STD-001 v1.13 actors.** Mary Wanjiku (Afya Authorised Signatory) and Daniel Otieno (Technical operator) as used by AWD §10.1; Daniel is a technical user whom My Work skips (C9); Jirani Office Supplies Limited is a synthetic recipient only (C8); Charles's separately authorised Contracting capacity. | Medium — spec | KT-STD owner | Open |
| FU-AWD-07 | **AWD next revision.** Record: timestamps stored in site time with UTC in serialized messages (C13, AGENTS.md §4.4) vs §15 "Persist timestamps in UTC"; the simulation stand-ins (synthetic sources, test profile, test receiver) as an accepted dev-site departure. | Low — spec | Project Owner | Open |
| FU-AWD-08 | **SEED-OPS-001 and register.** The `award` canonical stage and demo profiles; interface rows IF-017/018/019 implementation status. The owner's own uncommitted register and `.xlsx` edits of 30 Sep 2026 are not touched by this build. | Low — runbook | Seed owner / documentation owner | Partly done 1 Oct 2026 — SEED-OPS-001 v1.16 adds the `award` stage and its five demo profiles (§9B), and the register now lists SEED-OPS-001; interface rows IF-017/018/019 implementation status still open (was: Open) |

## 2. Production gates and deferred capabilities

| ID | Item | Severity | Owner | Status |
|---|---|---|---|---|
| FU-AWD-09 | **Legal operating profile (§15).** Current law, the official Goods STD version, LAW-V-001, notice forms, audience treatment, lawful channels and giving evidence, date counting, debrief effects, review/resumption treatment, required signatures, security and publication ownership, with reviewer and date. Only a simulation test profile exists; production answers `AWD_RULE_UNVERIFIED`. | High — production gate | Project Owner / Legal | Open |
| FU-AWD-10 | **Real signing (TRUST-ADR-001).** The opinion is signed through the test attestation double under the simulation flag. | High — production gate | Project Owner | Open |
| FU-AWD-11 | **Real notice channels.** Email goes to the test mailbox; giving evidence follows the test profile's channel rule. | High — production gate | Project Owner | Open |
| FU-AWD-12 | **Contracting module and receiver.** Without one, an eligible award stays Waiting to proceed with a Support Issue. | High — production gate | Project Owner | Open |

## 3. Found during the build (1 October 2026)

| ID | Item | Severity | Owner | Status |
|---|---|---|---|---|
| FU-AWD-13 | **Notice-contact correction after close.** BDS `update_tender_notice_contact` accepts only an Active bidder arrangement, and every arrangement is Closed after the submission deadline, so a supplier cannot correct a rejected award-notice address today. Award's **Correct contact** reads the contact owner's current address and retries the same notice; on the real provider it can only succeed once BDS allows a post-close notice-contact correction (the synthetic provider proves Award's side). | High — cross-module | BDS owner | Open |
| FU-AWD-14 | **Pre-existing technical-read conformance failures** (not Award): `kentender_core.tests.test_technical_read_conformance` fails because Bid Opening's resolvers return text routes where the check calls a function (3 errors), and `tenders.get_tender_publication` returns `can_configure = True` to a technical reader (1 failure). Award's own resolver and probes were checked with the same rule and conform. | Medium — platform | Bid Opening and Tenders owners | Open |
| FU-AWD-15 | **Evaluation's post-decision correction route.** `correction.return_for_authorised_correction` (built here) lets the AO's recorded correction instruction send the delivered report back to the same committee after a committed decision; EVL-CHG-001 §5.6 names this "controlled correction route" but does not specify it. Record it in the EVL amendment (FU-AWD-01). | Medium — spec | EVL owner | Open |
| FU-AWD-16 | **Board V23p has no decision-reason field.** The combined **Record corrected award and notify bidders** needs the AO's reasons (§4 Decision), so the build shows D03's **Decision reason** field there; registered departure in `tests/ui/fidelity/departures/award.js`. Add the field to the board or state where the reasons come from. | Low — design | Designer / Project Owner | Open |
| FU-AWD-17 | **Durable tender-level decision/notification status before an Award case exists** (§7 last paragraph). Until Tenders keeps it (FU-AWD-02), "No award decision recorded" for a tender without a case comes from the Tender status, as before. | Medium — cross-module | Tenders owner | Open |
| FU-AWD-18 | **Live funding read.** Award reads funding from the signed report (Evaluation's Budget confirmation) and opens a Funding issue from its qualification; there is no live Budget read at decision time (inherits FU-EVL-06). | Medium — cross-module | Budget owner | Open |
| FU-AWD-19 | **Notice document format.** Letters are generated deterministically as HTML (digest-bound, kept verbatim, shown read-only); no PDF is produced. The verified notice forms (§15) decide the production format. | Low — production gate | Project Owner / Legal | Open |
| FU-AWD-20 | **"Open Contracting".** With only the test receiver there is no Contracting page; the action opens a read-only view of the receipt that says no contract exists. | Low — cross-module | Contracting owner | Open |
| FU-AWD-21 | **Evaluation browser specs changed with the take-up** (§3 one work item): `evl-ordinary-path` and `evl-demo-walk` now expect the Head's Evaluation record to read "The committee report was sent to …" and the task to be Award's. EVL's own fidelity fixtures (captured before Award existed) still show D07-HOP "Review the committee's report."; recapture when EVL next changes. | Low — test | EVL owner | Open |
| FU-AWD-22 | **Pre-existing Industry design-gate failure** (not Award): `kentender_core.tests.test_industry_design_gate` fails because Bid Evaluation's `BidEvaluation.vue` root is `kt-evl`, not `kt-industry` (it mounts inside the Tenders page's Industry root). Award's two page roots (`Award.vue`, `portal/AwardPortal.vue`) carry `kt-industry`. | Low — platform | EVL owner | Open |
