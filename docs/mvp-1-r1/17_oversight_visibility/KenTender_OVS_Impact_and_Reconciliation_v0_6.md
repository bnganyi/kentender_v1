# OVS v0.6 — Impact and reconciliation schedule

**Controlling approval — 3 October 2026.** The Project Owner instructed: “Mark the documents as approved”. This approves this version in the coordinated OVS v0.6 package, including its incorporated amendments. OVS-P01–P05 are approved. The incorporated REQ v1.13, CFG v0.17 and TPR v0.16 changes are accepted within their approved successors; this does not create separate retrospective approvals of those intermediate versions. Earlier proposed/pending wording is drafting history superseded by this record. Static design work and conformance matrices remain open; CM and the separate template walkthrough remain deferred. Approval does not establish implementation, seed execution, testing, legal clearance or production readiness.

**Status: Approved requirements package.** Earlier reconciliation findings below are retained as dated review history. Current approval supersedes proposal-status wording, but not recorded outstanding design work or deferred scope.


Date: 3 October 2026. Status: proposed package, no new approval.

## Baseline findings

- 20 files supplied. AUTH v1.10 controls over historical v1.3. Uploaded OVS v0.1 does not replace the expanded v0.3 prepared in this conversation. This package advances OVS to v0.5.
- NDS v1.15 and PLN v1.28 have explicit 28 September approvals. Both registers are corrected to those baselines.
- REQ v1.13, CFG v0.17 and TPR v0.16 remain proposed in their source controls. Their changes are preserved in the OVS successors and are not implicitly approved.
- KT-STD v1.14 and SEED-OPS v1.21 are approved. The four-bid seed decision is preserved. Older proposed-status text in SEED-OPS is retained history under its explicit latest approval.
- Inspection covered supplied controls and relevant role/read, history/navigation, workflow, fixture and affected interface sections. This is not a claim that every unrelated requirement or repository implementation was revalidated.

## Single-source ownership

OVS owns common usability and the proposed read matrix. KT-STD retains archetypes, shared next_step, Home/My Work and technical-read policy. Module changes are limited to one reference, explicit owner read extensions and named conflicting-text replacements. Existing approved versions are preserved; all supplied successor files in this package are proposed.

## Owner amendments

| Owner | Uploaded source | Proposed successor | Classification | Target sections |
|---|---|---|---|---|
| KT-STD-001 | 1.14 | 1.15 | reference + shared standard | §§3, 3A, 3B |
| AUTH-ADR-001 | 1.10 | 1.11 | reference + permission mapping | §§4.4, 5.3–5.4, 8 |
| STR-CHG-001 | 1.8 | 1.9 | reference + reader addition | §§6–6.1, 11.3, 12.1–12.2 |
| BUD-CHG-001 | 1.11 | 1.12 | reference + reader addition | §§7–7.1, 9.1, 11.1, 12.1 |
| NDS-CHG-001 | 1.15 | 1.16 | reference + reader addition | §§6–6.1, 8.1, 11.17 |
| PLN-CHG-001 | 1.28 | 1.29 | reference + scoped progress | §§6, 7.1, 7.7, 9.3, 11.1 |
| REQ-CHG-001 | 1.13 | 1.14 | reference + reader addition | §§7.3A, 8, 10.1, 13.12 |
| CFG-CHG-002 | 0.17 | 0.18 | reference only | §§6, 8.1, 10 |
| TPR-CHG-001 | 0.16 | 0.17 | reference + summary interface | §§4.1, 6, 7.1, 10.10, 10.17 |
| BDS-CHG-001 | 0.10 | 0.11 | reference only | §§6, 7.1, 11.8, 14.7 |
| BOP-CHG-001 | 0.10 | 0.11 | conflict replacement + read addition | §§6, 7, 9 |
| EVL-CHG-001 | 0.4 | 0.5 | read/evidence and screen extension | §§3, 5.5–5.6, 7, 9.8–9.10, 9.12 |
| AWD-CHG-001 | 0.4 | 0.5 | summary + departmental read | §§6–7, 9 |
| PRC-CHG-001 | 0.10 | 0.11 | register exclusion replacement | §§2, 6–7, 9–10, 20 |
| SEED-OPS-001 | 1.21 | 1.22 | fixture reference + isolated branches | §§9A, 11 |
| KT-RCA-001 | 1.2 | 1.3 | roadmap coordination | §§5–6 |

## Exact owner changes

### KT-STD-001

OVS-CHG-001 v0.6 owns persistent decision visibility and finding completed records. Apply its shared usability requirements alongside this standard. This standard remains the single owner of archetypes, technical read, next_step, Home and My Work. OVS adds no parallel task engine. Resolve the technical-reader discrepancy recorded in the impact schedule before releasing affected views.

Source: `KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_14.md`. Proposed: `KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_15.md`.

### AUTH-ADR-001

Implement the owner-defined OVS v0.6 §4.1 read additions through existing responsibility registry and registered query/direct-read predicates. Match each valid role-scope pair without Cartesian privilege expansion. Resolve Tender lead/contributor scope through its immutable source handoff, not a new Frappe User Permission or permission store. Apply identical scope to rows, totals, evidence and search suggestions. Existing technical-read policy is not changed by this amendment; its cross-owner conflict is recorded separately.

Source: `KenTender_AUTH-ADR-001_Role-Bound_Business_Responsibility_and_Organisational_Scope_v1_10.md`. Proposed: `KenTender_AUTH-ADR-001_Role-Bound_Business_Responsibility_and_Organisational_Scope_v1_11.md`.

### STR-CHG-001

Add the approved-version reader projection in OVS v0.6 §4.1 for AO, HOPF and scoped HoD responsibilities. Implement it in Strategy registered reads and expose current/historical approved versions, actor/date and recorded reasons; no Draft/task or Strategy command is granted. Preserve all existing author/approver and consumer boundaries.

Source: `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_8.md`. Proposed: `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_9.md`.

### BUD-CHG-001

Add OVS v0.6 §4.1 approved-allocation and funding-position reads. Department attribution must use existing owner-authorised source relationships; a shared Budget Line alone does not establish departmental ownership. Preserve BUD calculations, funding contracts, historical versus current amounts and Finance authority. No Budget Viewer role or second ledger is introduced.

Source: `KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1_11.md`. Proposed: `KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1_12.md`.

### NDS-CHG-001

Add AO/HOPF neutral read of submitted/decided Needs and recorded disposition/lineage under OVS v0.6 §4.1. Unsent author Draft access remains unchanged. Preserve Author/HoD scope, the v1.15 Planning intake position and the rule that Needs are optional. Keep accepted, declined, withdrawn and superseded records discoverable under current permission.

Source: `KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_15.md`. Proposed: `KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_16.md`.

### PLN-CHG-001

Apply OVS v0.6 §4.1 to submitted/approved Plan reading and scoped downstream source progress. Preserve the accepted v1.28 departmental-plan position rules, Finance/governance actions, existing snapshots and historical evidence. Do not expose another department’s protected evidence or add a second work queue. Existing owner exports remain governed by their original permission.

Source: `KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_28.md`. Proposed: `KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_29.md`.

### REQ-CHG-001

Add AO read-only access to authorised Requisitions and their decisions/history under OVS v0.6 §4.1. Preserve the v1.13 pending change intact. Retain the certified lead/contributor version through onward links and scope resolution; read progress from the consumed handoff. Existing author/contributor edit and HoD certification rules do not widen.

Source: `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_13.md`. Proposed: `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_14.md`.

### CFG-CHG-002

Apply OVS v0.6 finding/history/recovery requirements to the existing setup surfaces and owner-authorised business configuration context. No new setup read or mutation audience is added. Preserve all pending v0.17 schedule changes; this usability reference does not approve or independently verify them.

Source: `KenTender_CFG-CHG-002_Site_Configuration_and_System_Setup_v0_17.md`. Proposed: `KenTender_CFG-CHG-002_Site_Configuration_and_System_Setup_v0_18.md`.

### TPR-CHG-001

Add owner-composed Decisions and progress under OVS v0.6 §§8, 13. Expose certified lead and contributing OU identifiers from the exact consumed REQ Version through the read model; do not invent independent editable copies. Apply OVS §4.1 departmental summary scope. Preserve pending v0.16 work-summary counts over the whole permitted queue, AO return and schedule changes. Filtered result count is separate from those summary controls.

Source: `KenTender_TPR-CHG-001_Tenders_v0_16.md`. Proposed: `KenTender_TPR-CHG-001_Tenders_v0_17.md`.

Direct conflicting text replaced: “No upstream/downstream link is supplied for these artboards; draw none.”.

### BDS-CHG-001

Apply OVS v0.6 own-organisation history, navigation and recovery requirements to existing permitted supplier surfaces. Preserve sealed-bid boundaries, signatory/representative separation, receipt evidence and all production gates. No supplier access to internal decision records or competitors is added. Existing submitted-version and receipt sources remain canonical.

Source: `KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_10.md`. Proposed: `KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_11.md`.

### BOP-CHG-001

Add explicit AO contextual read after reveal, preserving the independent opening/attestation authority boundary. Add the HoD revealed summary defined in OVS v0.6 §4.1, scoped through the Tender’s consumed source. Expose an owner-controlled Tender summary and meeting-row verdict. The Procurement meetings register is read-only and creates no general proceedings workspace.

Source: `KenTender_BOP-CHG-001_Electronic_Bid_Opening_v0_10.md`. Proposed: `KenTender_BOP-CHG-001_Electronic_Bid_Opening_v0_11.md`.

Direct conflicting text replaced: “There is no generic Proceedings menu.”.

### EVL-CHG-001

Implement OVS v0.6 §§4, 4.1, 7 and 13: AO/HOPF full delivered-version projection and HoD scoped administrative/outcome summary. Freeze evidence associations with the signed report and material annexes already required by §5.5; verify uncited evaluated submissions are included. Preserve previous delivered versions during correction. D07-SENT remains accessible after Award takes the review. Existing committee working views and independently authorised review actions remain unchanged. Technical-reader conflict is explicitly outstanding.

Source: `KenTender_EVL-CHG-001_Bid_Evaluation_v0_4.md`. Proposed: `KenTender_EVL-CHG-001_Bid_Evaluation_v0_5.md`.

### AWD-CHG-001

Expose the OVS v0.6 §4.1 HoD scoped final-decision summary and §13 Tender summary. Retain separate recommendation, professional opinion and AO decision labels and their versions. Keep AO/HOPF authority unchanged; no unfinished opinion, unissued notice or supplier correspondence is added to HoD read. Point to the exact Evaluation source; never erase it after hand-off.

Source: `KenTender_AWD-CHG-001_Award_v0_4.md`. Proposed: `KenTender_AWD-CHG-001_Award_v0_5.md`.

### PRC-CHG-001

Add ListProcurementMeetings, a read-only register at /app/procurement-meetings under Tender Management, using OVS v0.6 §11 and owner row/record verdicts. It supports AO/HOPF, scoped HoD and authorised auditor; technical-read treatment follows the explicit policy resolution in the impact schedule. No create, edit, meeting administration or new owner lifecycle is added. Owner-specific ceremonies, discussions, minutes and proofs remain in existing screens.

Source: `KenTender_PRC-CHG-001_Minimal_Procurement_Proceedings_v0_10.md`. Proposed: `KenTender_PRC-CHG-001_Minimal_Procurement_Proceedings_v0_11.md`.

Direct conflicting text replaced: “PRC defines **no menu entry, Home tile, independent register, generic form or supplier portal route**.”; “This document intentionally supplies **no incomplete Claude Design prompt**. PRC has no standalone page to draw.”; “PRC still has no standalone artboards.”.

### SEED-OPS-001

Retain the approved four-bid canonical story and all v1.21 seed decisions. Add isolated OVS v0.6 §14 branches using existing Amina, Charles, Naomi, Julia, Dr Peter Kimani and approved supplier personas. Include delivered/returned report, department-contributor, Not held, pagination and stale-authority cases. CM fixtures remain pending its current sources. Do not change the canonical tender to a single-bid story for convenience.

Source: `KenTender_SEED-OPS-001_Canonical_Site_Seed_Runbook_v1_21.md`. Proposed: `KenTender_SEED-OPS-001_Canonical_Site_Seed_Runbook_v1_22.md`.

### KT-RCA-001

Track OVS v0.6 as a cross-cutting usability change. Release verified Evaluation visibility first, then shared/departmental views and meeting register, then CM coverage with its module delivery. All stages stay in scope; completion requires module-level evidence. CM all-stage documentation remains next substantive module work, with independent operation and ERPNext Accounts direction retained; its latest source was not in this upload.

Source: `KenTender_Roadmap_Coverage_Assessment_v1_2.md`. Proposed: `KenTender_Roadmap_Coverage_Assessment_v1_3.md`.

## Reconciliation decisions and open items

| Item | Disposition |
|---|---|
| TPR work-summary counts versus meeting totals | Preserve TPR v0.16 full permitted-queue counts. Meeting totals follow filters. Filtered result counts are separately labelled. |
| Broad technical read versus procurement restrictions | TRUST supplied. OVS v0.6 §4.2 now states a proposed resolution; approval remains pending. |
| Department attribution | REQ v1.13 §7.3A freezes certified lead by version; TPR must expose the exact consumed source relationship. No editable duplicate department or inferred join. |
| Evaluation version binding | EVL §5.5 already freezes report/material annexes. Verify uncited evaluated documents and committee-record associations; extend owner relationships only if missing. No competing copy store. |
| Departmental views | Proposed OVS §4.1 gives exact minimum read boundaries, including summary-only HoD access to Evaluation/Award. No full bid/committee evidence for HoD solely through this change. |
| Existing Home/My Work | KT-STD §3B is sufficient owner contract for supplied modules; CTX supplied; proposed v1.1 aligns its obsolete context rules. |
| Successor numbers | Allocated from versions in this supplied bundle only. If another external successor already occupies one, rebase/renumber before approval. |

## Second-bundle reconciliation

Four files were supplied. CTX and TRUST were read in full; SEED controls/affected chronology and template control/availability/navigation sections were inspected. No code was inspected.

| Source | Result | Proposed amendment |
|---|---|---|
| CTX v1.0 | Obsolete multi-PE selector, permission sources and registry gate conflict with later AUTH/CFG | Clean CTX v1.1 retains reversible module filters and retires old requirements |
| TRUST v0.1 | Confirms sealed custody, no technical business authority and test/production separation | Limited TRUST v0.2 reference; OVS §4.2 supplies an explicit proposed technical-reader resolution |
| SEED v1.3 | Supplied; chronology and generated-code assumptions need current runbook decisions | Limited SEED v1.4 OVS scenario binding; wider seed harmonisation remains recorded |
| STD-TPL v0.15, supplied separately after v0.13 | Approved 3 October 2026; release 1.4 and renderer 1.2.0; baseline confirmed | Preserve approved source unchanged. The separate walkthrough change requires rebase; do not allocate a competing template successor here. |

OVS fixture correction: Julia’s 2026 acting term is expired at June 2027; use her as a negative case. Positive departmental reads use in-force assignments from the approved runbook. OU mnemonics are aliases, not forced installed identities. No existing assignment is silently extended.

## Remaining sources and decision

The Project Owner deferred the current CM sources and separate template walkthrough on 3 October 2026. Do not request them again until that work resumes. CTX, TRUST and SEED need not be uploaded again. The technical-reader policy now has a concrete proposed resolution in OVS §4.2 for approval; it is not marked approved. Both registers distinguish this from source absence.

## Review and implementation sequence

1. Review the proposed consolidated usability/read policy and limited owner amendments.
2. Review the proposed OVS §4.2 technical-reader resolution and resolve remaining CM/template interfaces; bind CM fixtures.
3. Approve one coordinated version set, including an explicit disposition for the three previously pending source changes.
4. Implement and verify Evaluation visibility first, then common/departmental views and the meeting register, and CM coverage alongside CM delivery.
5. Keep module implementation evidence separate from requirements approval. No build tests have been run by this reconciliation.

## Package contents

OVS v0.6, 19 limited proposed owner/reference successors, this impact schedule, reconciled YAML and XLSX registers, source SHA-256 inventory, both unmodified source ZIPs and the unmodified standalone template v0.15. Original approval history remains available in those sources.

## Supplement precedence

The second-bundle reconciliation above replaces the earlier missing-source findings and open-ended technical-reader disposition. Supplied owner successors remain proposed at their existing candidate versions; only OVS advances to v0.5. Both unmodified source ZIPs are preserved in this package.

## STD-TPL v0.15 reconciliation

The standalone upload confirms approval on 3 October 2026. Preserve v0.15 unchanged; v0.13 is historical. The separate walkthrough change request is recorded as approved on 2 October in v0.15, but is not incorporated into this specification. Its full text is still needed to reconcile the interface and allocate the next template version. Approval of that separate change is reported from v0.15, not independently verified from the missing change request.

The proposed usability amendment for the next coordinated template successor is: apply OVS v0.6 to existing authorised template inspection and related-record navigation; retain the owner-controlled read surface and concern action in §11. Display evaluation evidence using the exact bid snapshot, published release, question wording, answer reading and rule reason in §§9.1 and 13.12. Do not substitute current Account facts for the business profile captured in the bid. Contract views use the explicit destinations in §9.2; an administrative fact marked Not carried forward is not a contract obligation. Preserve available historical outputs and the existing On/Off, integrity and withdrawal rules. No template editing or activation action, new approval gate, or access to another supplier's information is added.

The existing evaluation-display follow-up remains open. Structured discounts remain a separate future release. This reconciliation does not close the source's open questions, certify the renderer or infer runtime implementation. IF-020 and AUD-024/AUD-028 remain open specifically for walkthrough rebase and integration, not for absence of v0.15.

## v0.5 design-readiness review disposition — v0.6

Reviewed input: OVS-CHG-001_v0_5_Design_Readiness_Review.md. This supersedes the earlier v0.1 review as the current review input.

| Findings | Disposition |
|---|---|
| D1–D5, D7 | Accepted and open: complete static owner design sections under OVS §14.1. Requirements text is not a design prompt. |
| D6 | CM and supplier contract designs deferred at the owner's instruction; submission/receipt/clarification scope remains. |
| C1 | Corrected §11: Administrator/System Manager site-wide safe metadata read; limited operators distinguished; §4.2 policy still proposed. |
| C2 | Source clarification: SEED-OPS v1.21 §11 D4 plus SEED v1.3 §3.1 support Peter's positive Digital Health case. No new persona. Runtime seed not verified. |
| C3 | Corrected grouping: three held under lead A; one Not held under lead B, zero held for B. |
| C4 | HoD grants individually marked pending OVS-P01–P03 in OVS and matching owners. |
| C5 | TPR v0.16 counts expressly pending OVS-P04; approval not inferred. |
| C6 | Consistent: dates and prior actors remain in the working section, not the journey tracker. TPR link conflict already corrected. |
| C7 | Added control fields, error contract, seed/shortcut/traceability coverage; numbered and relocated template reconciliation. Retained numbering with skeleton mapping. Static design remains openly incomplete. |
| C8 | Preserved; no new business requirements inferred from a conforming finding. |
| KT-STD editorial findings | Corrected stale conditional approval sentence, historical label, v1.13 effect and malformed duplicate heading; explained unused §9 without renumbering established sections. |

CM sources and the separate template walkthrough are deferred, not approval blockers for independently completed supplied-module work. All new requirements remain proposed. The first design slice is EVL/TPR/PRC, followed by other supplied-module changes; no closed-input design or runtime completion is claimed.

## Approved version set — 3 October 2026

| Document | Approved version |
|---|---|
| STR-CHG-001 | 1.9 |
| BUD-CHG-001 | 1.12 |
| NDS-CHG-001 | 1.16 |
| PLN-CHG-001 | 1.29 |
| REQ-CHG-001 | 1.14 |
| CFG-CHG-002 | 0.18 |
| TPR-CHG-001 | 0.17 |
| BDS-CHG-001 | 0.11 |
| KT-STD-001 | 1.15 |
| AUTH-ADR-001 | 1.11 |
| SEED-001 | 1.4 |
| SEED-OPS-001 | 1.22 |
| KT-RCA-001 | 1.3 |
| TRUST-ADR-001 | 0.2 |
| BOP-CHG-001 | 0.11 |
| PRC-CHG-001 | 0.11 |
| EVL-CHG-001 | 0.5 |
| AWD-CHG-001 | 0.5 |
| OVS-CHG-001 | 0.6 |
| CTX-CHG-001 | 1.1 |
