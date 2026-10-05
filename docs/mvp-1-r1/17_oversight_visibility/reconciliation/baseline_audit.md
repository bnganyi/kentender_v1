# OVS-CHG-001 v0.6: baseline audit (Phase 0, OVS6-0006 and OVS6-0009)

Two read-only audits run on 4 October 2026. Neither wrote anything, ran a test, a seed or a migration. Findings are observations of the code and the dev site `kentender.midas.com`, not requirements.

## 1. Absorbed versions in code (OVS6-0006)

The approved package absorbed three versions that were never separately approved (OVS v0.6 control paragraph) and two earlier approved ones. Each was checked in the source. Paths are relative to `kentender_procurement/kentender_procurement/` (`P`) or `kentender_core/kentender_core/` (`C`).

| Item | Status | Evidence | Gap |
|---|---|---|---|
| **REQ v1.13 (OD5):** an IT-equipment requisition needs the template release installed, intact, Available and switched On; checked at Prepare and again at Authorise; failure is `REQ_PRODUCT_UNSUPPORTED` | Built; no acceptance tests | `P/procurement_requisitions/services/compatibility.py:45-62` `template_support()` calls `binding.available_release()` then `binding.require(…, "new_binding")`; failure sets `available: False`, which fails the "Planned designation" row (`:83`) with the code at `:28`. `P/std_templates/services/binding.py:52-65` filters on lifecycle Available, `site_switch` On and integrity Verified; `:82-90` also needs a live `verify_integrity`. Prepare at `procurement_requisitions/services/draft_commands.py:95`; Authorise at `services/authorise.py:44`; lock on submit at `services/lifecycle.py:81`. | Nothing in the code mentions REQ113. `tests/test_compatibility.py:79` only passes a stubbed `{"available": False}`; `tests/test_draft_commands.py:75` patches `template_support`. No test uses a real release switched Off, not installed or not intact, and none covers a release switched off after submission. The docstrings at `compatibility.py:4` and `:46` still say v1.11/v1.12. |
| **CFG v0.17:** Open Tender bid-opening interval has a separate minimum of 7 days and default of 21 | Built; no dedicated tests | Seed `C/seeds/site_setup.py:385` (default 21), `:396` `LEGAL_PREPARATION_MINIMUMS`, written at `:1397-1401`; patch `C/patches/v1_28/open_tender_preparation_minimum.py:23-37` (registered last in `C/patches.txt`) writes the minimum only when it is 0 (`:30`); separate fields and a default-below-minimum check at `C/services/procurement_settings.py:654-659`; consumer `P/tenders/services/configuration_gateway.py:131-146`. `P/tenders/tests/test_publication.py:176` asserts `{"minimum_days": 7, "default_days": 21, …}`. | No CFG17 test and no test of the patch (idempotence, not overwriting an administrator's value). The seed skips an existing profile (`site_setup.py:1383`), so only the patch reaches earlier sites. Not verified on a live site. The patch overwrites the reference and basis on rows it fills. |
| **PLN v1.28:** position derivation per accepted Need, published to NDS; §5.7 row; §7.7 hand-off; U01 and U02 variants | Built, with tests | `P/procurement_planning/services/needs_intake.py:274-316` `need_positions()`, `:319-343` `publish_need_positions()`; call sites in `dpp_lifecycle.py`, `dpp_validation.py`, `dpp_autostart.py`; NDS side `P/departmental_needs/services/usage.py:436`, `departmental_needs/api.py:103`; next-step `P/procurement_planning/services/next_step.py:638-675`; My Work `my_work_provider.py:217-240`; tests `P/procurement_planning/tests/test_late_accepted_need.py` (lines 91, 142, 156, 167) and dead-end matrix profiles | No test is labelled PLN28-AC-xxx. The tests were not run in this audit. |
| **TPR v0.16** | Present | `ReturnApprovedTender` `P/tenders/services/publication.py:233,259,264`, API `P/tenders/api.py:178`; `TND_PUBLICATION_PERIOD_INVALID` `publication.py:82,159`, `errors.py:41`; work-summary cards `P/tenders/services/read.py:34`, tested in `P/tenders/tests/test_read.py` | Not exercised |
| **NDS v1.15** | Present | `P/departmental_needs/services/guidance.py:4`, `services/workspace.py:446,735-765`, `services/usage.py:396,436`, `services/my_work_provider.py:16` | Not exercised |

**Consequence for this plan.** None of the five blocks an OVS phase. Two gaps are acceptance-test debts that belong to the REQ and CFG owners, not to OVS: logged as FU-OVS-31 (REQ113 tests) and FU-OVS-32 (CFG17 tests and patch test).

## 2. Canonical data on the dev site (OVS6-0009)

Read-only queries by `frappe.get_all` / `frappe.db.get_value` on 4 October 2026. The probe script is in the scratchpad, not in the repository. The process check before querying matched only idle `@playwright/mcp` tool servers and the dev-mail loop (which flushes the mail queue and runs `dispatch_pending`); no test, seed or migration was running.

### 2.1 What exists

| Fact | Observed |
|---|---|
| Tenders | Exactly one: `TDR-306772`, reference **TND-MOH-2027-002**, "Clinical training and deployment laptops for digital health rollout"; status Submission period ended; namespace `KENTENDER_MVP_1_R1_TND` |
| Departments on that Tender | lead `OU-MOH-02498` (Digital Health); contributors `OU-MOH-02498` and `OU-MOH-02499` (Human Resources Management and Development) |
| Opening | `BOC-MOH-2027-002`, state Opening complete, outcome Bids opened; its Proceeding `PRC-BOC-MOH-2027-002` is Finalized and has **0 Proceeding Sessions** |
| Evaluation | `EVL-MOH-2027-002`, state **Report sent**; Proceeding `PRC-EVL-MOH-2027-002` state Open with **2 sessions, both Ended** |
| Bids | **4** Evaluation Bids, all KES: Afya Digital Supplies Limited 46,400,000; Jirani Office Supplies Limited 48,720,000; Pwani Tech Distributors Limited 43,500,000; Mlima Computer Solutions Limited 46,980,000. Recommended: BID-01 at 46,400,000 |
| Report | `EVL-MOH-2027-002-RPT-01`, version 1, state Delivered, outcome Recommendation; `content_json` is non-empty with keys `bid_findings`, `clarifications_and_record`, `financial_comparison`, `narrative`, `recommendation`, `sections`, `summary`, `tender_and_committee` |
| Delivery | `EVL-MOH-2027-002-RPT-01-DLV` to charles.mutiso@moh.example.test; status Delivered; review_state **With Award**; delivered 2027-06-16 14:07 |
| Award | `AWD-MOH-2027-002`, stage **Opinion**, outcome empty, decision_status "No decision recorded", notification_status "Not issued" |
| Proceedings overall | 2 (one Bid Opening Finalized, one Bid Evaluation Open); none Not held or Aborted after start |
| Organisation Units | `PE-MOH` Ministry of Health; `OU-MOH-02497` Directorate of Digital Health and Policy (child of PE-MOH); `OU-MOH-02498` Digital Health (child of 02497); `OU-MOH-02499` Human Resources Management and Development (child of PE-MOH). All Active |

### 2.2 Personas and assignments

| Persona | Role | Scope | Effective |
|---|---|---|---|
| Amina Hassan | Accounting Officer | Site-wide | permanent |
| Charles Mutiso | Head of Procurement Function | Site-wide | permanent |
| Naomi Chebet | Auditor | Site-wide | permanent |
| Dr Peter Kimani | Head of User Department | `OU-MOH-02499` (HRMD) | permanent |
| Dr Peter Kimani | Head of User Department | `OU-MOH-02498` (Digital Health) | from 2026-12-01, no end |
| Dr Peter Kimani | Head of User Department | `OU-MOH-02497` (Directorate) | from 2026-09-01, no end |
| Julia Njeri | Head of User Department | `OU-MOH-02498` (Digital Health) | Acting, 2026-10-01 to 2026-11-30 23:59:59 |
| Grace Wanjiku | Head of User Department | `OU-MOH-02499`; also Departmental Author for 02498 and 02499 | — |
| Samuel Otieno | Head of User Department | `OU-MOH-02497` | 2026-01-01 to 2026-08-31 (lapsed) |

All 22 responsibility assignments carry namespace `KT_STD_001_S8` and status Enabled.

### 2.3 What this means for the plan

1. **The canonical Tender already is "Tender A".** It has lead Digital Health and contributor Human Resources Management and Development, one started Opening that has no session row, and two started Evaluation sessions. The counting test of OVS v0.6 §14 can run on it without a new Tender; only Tender B (lead HRMD, one Not held opening) is a new isolated branch. Confirmed by observation, not by running the register (it does not exist yet).
2. **The Opening really has no session row (plan D6).** The Proceeding row is the only source for an opening meeting.
3. **The Award has already begun.** The review state is With Award and the Award stage is Opinion. This is exactly the state in the Project Owner's screenshot, so the Phase 2 oversight view can be checked against real data without a branch.
4. **Peter Kimani's positive persona depends on the clock.** On the real date (4 October 2026) he is Head of User Department for HRMD (permanent, a contributor to the canonical Tender) and for the Directorate (from 1 September 2026), but his Digital Health assignment starts on 1 December 2026, and Julia Njeri holds Digital Health until 30 November 2026. His Digital Health view of the lead department is therefore positive only when the test clock is set to a June 2027 date (the fixture dates), and Julia becomes the expired negative persona only then. Phase 5 must state which clock each persona case runs under. Logged as FU-OVS-33.
5. **Directorate descendants.** `OU-MOH-02498` is a child of `OU-MOH-02497`. A Directorate-scoped Head of User Department therefore reads Digital Health records by the descendant rule (AUTH-ADR-001 v1.11 §4.3: "An OU-scoped assignment covers the selected Organisation Unit and all of its descendants."). Dr Peter Kimani holds the Directorate assignment from 1 September 2026, so he already reaches Digital Health records through it. The department-scope tests must include this path, not only the direct assignment.
6. **Residue to know about.** The Evaluation Proceeding `PRC-EVL-MOH-2027-002` has a **blank `fixture_namespace`**, while every other seeded row has a namespace. A purge keyed on namespace would not reach it. Logged as FU-OVS-34.
7. **Two Procuring Entities exist** (`PE-MOH` and `PE-MOE`), and the Organisation Units' `procuring_entity` field is empty. The AUTH baseline says one site is one Procuring Entity. Not an OVS matter; recorded because Phase 2–4 department joins must not depend on that field. Logged as FU-OVS-35.
8. **Single canonical Tender reference.** There is no TND-MOH-2027-033 on the site; the design fixture's Tender number is a design value, not a database record.

## 3. D3: does the frozen delivered report carry its supporting records? (OVS6-0007)

**Verdict: partly present, mostly missing.** Read-only trace of `bid_evaluation/services/signing.py`, `report.py`, `reads.py`, `sources.py` and the Evaluation Report Version doctype, with a check of the canonical report on the dev site. Paths are relative to `kentender_procurement/kentender_procurement/`.

### 3.1 What a freeze writes

`signing.py:82-115` `send_for_signing` stores, on the Evaluation Report Version: `content_json` (the output of `report.build()` plus the secretary's narrative, `signing.py:95`), `content_digest`, `outcome`, `recommended_bid`, `recommended_total`, `qualifications_json`, `source_versions_json` (only the run name, the definition digest and the intake name) and the freeze fields. It also copies the content and digest into a Proceeding Minutes Version with one signature target per roster member (`proceedings/services/record_versions.py:66-91`). The doctype has no child table and no annex field. The module docstring says "with its annexes", but no annex is implemented: `sections` is a list of five section names (`report.py:33,173`).

### 3.2 Against OVS v0.6 §7

The requirement: the delivered report exposes "its exact report version, evaluated bid versions, findings, reasons, clarifications and dispositions, due diligence, committee record and signatures", and "all submitted documents belonging to those evaluated bid versions … even if not individually cited", through "immutable associations between the delivered version and its supporting records. A time filter alone is not sufficient."

| Part of the requirement | In the frozen version? | Evidence |
|---|---|---|
| Evaluated bid **versions** (submission version, receipt, package digest) | **No.** `content_json` carries the Evaluation Bid name only | Live values sit on the Evaluation Bid rows (written at `bid_evaluation/services/intake.py:100-104`); `award_seam.delivered_report` (`award/services/award_seam.py:84-100`) re-reads `submission_version` live |
| All submitted **documents**, cited or not | **No.** Evaluation keeps no package bytes (`sources.py` docstring); `reads.evidence` and `reads.bid` fetch the released package live from the tender box by the opening hand-off. `reads.bid` (264-268) lists file names and digests live | The only commitment is indirect: `Evaluation Bid.package_digest` is a hash over the whole package, files included |
| Findings, financial comparison, clarifications (Sent replies), sessions, disagreements, recommendation | **Yes**, in `content_json` keys `bid_findings`, `financial_comparison`, `clarifications_and_record`, `recommendation`, `summary`, `tender_and_committee`, `sections`, `narrative` | `report.build`, `report.py:156-174` |
| Committee record items | **Partly.** Frozen: roster, appointment history, secretary, sessions with start, end and Arrival attendance, disagreements. **Not frozen:** discussion items and conclusions as records, attendance departures, clarification attachments and non-Sent or superseded replies, member declarations and conflicts (shown live by `committee_record`, `reads.py:350-356`) | `report.py:91-116` |
| Signatures | **Yes, by association.** They sit on the Minutes Version targets and Attestations linked by `record_version_reference`; `target_digest` equals the content digest | `signing.signatures()` (280-288); `record_versions.py:118-121` keeps superseded proofs |
| A returned or superseded version keeps its content | **Yes.** Only state and supersession fields change | `lifecycle.withdraw_signing` (43-47); `correction._apply_return` |

### 3.3 Access today

- The only evidence route is the whitelisted GET `bid_evaluation/api.py:89-98` `get_evidence` → `reads.evidence`, which applies `require()`, `a["bids"]` and a check that the bid belongs to the case. A refusal is masked as not found. No direct file-URL bypass exists inside Evaluation. Whether Frappe's `/private/files/` route for the underlying Bid Evidence files is closed to Evaluation users was **not verified**.
- `evidence()` takes no report-version argument, so it is bound to the case and not to a delivery. An eligible member can read any digest of any bid in the case at any time.
- The delivered recipient (the Head of Procurement Function) has `report` access but not `bids`, so they cannot reach any bid document, cited or not.
- `evidence()` does not apply the declaration check that `bid()` applies (`reads.py:255-258`). A successful evidence read is not audited; `_audit` runs only on refused or not-found outcomes (`api.py:35-43,57-70`).

### 3.4 Consequences for the plan

1. **The report text, findings, comparison, recommendation and signatures can be shown to the AO and HOPF from the frozen version today, with no stored addition.** That is Phase 2 part A.
2. **The "all submitted documents, cited or not" requirement cannot be met from the frozen version.** Nothing immutable lists the bid versions or their documents. This needs a stored addition, which OVS v0.6 §3 allows only as "the smallest owner-owned addition" and plan rule 6 requires the owner to sign off first. That is Phase 2 part B, **Blocked — owner** (row OVS6-0213, FU-OVS-11).
3. **Smallest addition (proposed, for the owner):** an evidence manifest written at freeze **beside** `content_json`, not inside it.
   - Inside would change `report.build()` output and so the digest every member signs; existing delivered reports such as `EVL-MOH-2027-002-RPT-01` could not carry it without breaking their signatures. (The same trap is on record: a new Tenders control changes every existing package digest.)
   - Per bid: bid reference, entry and envelope references, receipt, submission version and package digest.
   - Per document of the released package, cited or not: response id, file digest, original file name, media type, size.
   - The Source Intake digests (`handoff_digest`, `register_digest`, `opening_record_digest`, definition digest).
   - Its own digest, recorded on the Report Version.
   - A backfill for versions already delivered, built from the insert-only Evaluation Bid rows and the released package, labelled as reconstructed.
   - The committee-record items not frozen today (discussion conclusions, departures, reply attachments) need the same treatment, or are read live with an explicit "as recorded at delivery" boundary. This is the owner's call.
4. **`reads.evidence` gains a version argument.** With a delivered version it permits a (bid, digest) pair only if the pair is in that version's manifest, and it extends to the delivered recipient and the AO. A successful read is audited. Whether to audit reads is OVS-OD-7 of the retired draft, now an open question for the owner (FU-OVS-37).

## 4. D5: the Tender's department (OVS6-0008)

Verdicts: **reassignment possible: no. Null possible: yes. Join path: confirmed.** One correctness defect found.

| Question | Answer | Evidence |
|---|---|---|
| Where is the lead set, and can it change? | Written once, at creation, in `tenders/services/draft_commands.py:110-118`; no other writer in non-test code. Both fields are `read_only` in `tender.json:106-117` (UI only); `tender.py` has no guard, and `tender_management/immutability_guards.py` is not applied to them. A script could change them; nothing does | grep of non-test Python |
| Can the requisition's lead change and reach the Tender? | HOPF can change a requisition's lead only while it is "Submitted to Procurement" (`procurement_requisitions/services/lifecycle.py:325-357`, `change_requisition_lead_department`, API `api.py:237`). A Tender starts only from an Authorised handoff (`tenders/services/handoff_gateway.py`), after that window, so a later change never reaches an existing Tender | |
| Can the lead be null? | Yes: empty when the snapshot has no contributing units; set to None when the unit does not exist (`draft_commands.py:118`); `tenders/tests/sample.py:125` inserts None. Consumers tolerate it (`tender_authorization.py:193-203`). The one Tender on the dev site is not null | |
| Do Organisation Units change over time? | Yes. A NestedSet with `track_changes`; `unit_name`, `parent_organisation_unit` and `status` are editable; `effective_from`/`effective_to` are deprecated and unused; the unit code is not renamable. The only history is the Frappe Version log. A Tender stores only the code | `kentender_core/kentender_core/kentender_core/doctype/organisation_unit/` |
| Join path | `Proceeding.owner_id` → case name → `case.tender` → `Tender.lead_org_unit` and `contributing_org_unit_ids`; reverse lookup by `Proceeding.owner_key = "<type>:<case.name>"`. `Evaluation Case.proceeding` is a Data field, `Bid Opening Case.proceeding` is a Link | `proceedings/services/records.py:80-81`; `bid_evaluation/services/prc_owner.py:21-22`; `bid_opening/services/prc_owner.py:22-23` |

**Defect: the Tender's lead department is not the certified lead.**

- `lead = requisition_summary(handoff).get("lead_org_unit") or snap.lead_unit(snapshot)` (`draft_commands.py:111`). `snap.lead_unit` returns `contributing_org_unit_ids[0]` (`tenders/services/snapshot.py:116-118`), and the handoff builds that list with `sorted(...)` (`procurement_requisitions/services/handoff.py:61`), so the "lead" is the **alphabetically first** contributing unit.
- The first branch reads `Procurement Requisition.lead_org_unit` (`handoff_gateway.py:55`), but the doctype field is `lead_org_unit_id` (`procurement_requisition.json:123`). A legacy `lead_org_unit` column exists in the dev database and is NULL, so the fallback always wins. On a site without that column the read would probably fail (not verified).
- The authoritative certified lead is `payload.departmental_certification.lead_org_unit_id` (`handoff.py:84`) and is ignored. `tenders/services/correction.py:82,97` has the same stale read.
- **Effect on OVS:** OVS-DEC-3 attributes a meeting to "the Tender's owning department", and OVS v0.6 §4.1 and the TPR v0.17 preamble require the "certified lead and contributing OU identifiers from the exact consumed REQ Version". Reading `Tender.lead_org_unit` as it stands would attribute meetings to the wrong department whenever the certified lead is not first alphabetically.
- **The canonical Tender is not a counter-example.** Its lead (`OU-MOH-02498`, Digital Health) is also first alphabetically among `["OU-MOH-02498","OU-MOH-02499"]`, so it cannot show whether the defect bites. Phase 3 begins by reading that requisition's certified lead (OVS6-0310).
- **Proposed fix (plan D15):** read the lead from the handoff's certified lead at Tender creation and expose it through the Tender read; patch existing Tenders from their consumed handoff; fix `correction.py`. This changes Tenders data and code, so it is stated to the owner (FU-OVS-36) and not done silently.

**D5 settled:** attribute a meeting by the Organisation Unit **code** held on the Tender (stable, never reassigned), grouped under the corrected lead, with the **current** unit name shown. Moving or renaming a unit does not change grouped totals. OVS v0.6 §11 asks to "use owner history for attribution at the meeting date" only "if reassignment is supported"; reassignment is not supported.

## 5. Document checks on the filed package (OVS6-0010)

Run 4 October 2026 with the skill's scripts. Nothing was edited.

**Preservation, each predecessor against its successor** (`--allow-control-table`, 17 pairs; CTX v1.1 is a rewrite and OVS v0.6 has no predecessor):

- **No pair deleted a line.** Deleted-not-allowed = 0 everywhere.
- **7 pairs pass:** SEED-001, TRUST-ADR-001, STR, BUD, PLN, REQ, EVL.
- **10 pairs fail** only because "changed" lines sit outside the control table: AUTH 1, KT-STD 4, SEED-OPS 4, NDS 1, CFG 2, TPR 3, BDS 1, PRC 3, BOP 1, AWD 1 (21 lines in all).
- What changed: the "Current approval record" or "Status — proposed" preamble line at the top of eight documents (superseded by the 3 October approval record; OVS v0.6 says "Earlier proposed/pending wording is drafting history superseded by this record"); KT-STD-001 §12 approval-effect labels at lines 710–714; and the clause replacements the impact schedule names: BOP line 225, PRC lines 154 and 160, and the TPR tracker sentence at line 1379. NDS v1.16 line 497 changed from "Finance, AO, statutory…" to "Finance, statutory…"; the impact schedule lists NDS §6 as a target but does not name that removal (FU-OVS-38).
- No line is deleted. Each of the 21 is a change to an approved document's wording; the full line text is available by running the check on the pair. They are recorded here so the owner can see them; this audit does not judge whether any is acceptable.

**Consistency** (`consistency_check.py`, errors and warnings, predecessor then successor): no successor adds an error except two preambles that cite section 18.1 of OVS without naming the document (BOP v0.11 line 5, EVL v0.5 line 5), and OVS v0.6 line 329 (its section 16.1) cites sections 9.1, 9.2 and 13.12 of STD-TPL without naming it. EVL's other three errors (no Version row; `EVL_REPLY_OVERDUE` and `EVL_EVALUATION_OVERDUE` undefined) are in v0.4 too. SEED-OPS (21), CFG (6) and PLN (3) carry the same errors as their predecessors. CTX v1.1: 0 errors, 2 warnings. OVS v0.6: 3 errors (the line 329 references), 4 warnings. Logged as FU-OVS-39.

**Register:** 13 `register_check` errors, all status values outside `workflow_states` (FU-OVS-24).

## 6. Method notes

- The first probe attempt failed with "App ro_seed_probe is not installed" and a NameError naming the scratch module. That is `bench execute` resolving a dotted path through the app list, not queue overload. The working form wraps the import: `PYTHONPATH=<scratchpad> bench --site kentender.midas.com execute "__import__('ro_seed_probe').run"`. Use it for later read probes.
- Nothing was cleaned up after the probes because nothing was written.
