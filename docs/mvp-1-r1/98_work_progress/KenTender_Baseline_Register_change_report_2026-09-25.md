# Change report — KenTender Baseline Register (KT-DOC-CTRL-001)

| Item | Value |
|---|---|
| Input | `KenTender_Baseline_Register.yaml` as supplied, `as_of` 2026-09-25 (retained unchanged as the predecessor) |
| Output | `KenTender_Baseline_Register.yaml`, corrected; same `register_id`, `schema_version` and `as_of` |
| Basis | Project Owner confirmation, 25 September 2026: TPUB-CHG-001 was absorbed into TPR-CHG-001 v0.10; corrections to match approved document text, each cited below |
| Method | 20 anchored whole-entry replacements, each asserting the old value before changing it (`apply_edits.py`); no entry removed |

## Read list

- **Read in full:** the register; PLN-CHG-001 v1.27; BUD-CHG-001 v1.11; REQ-CHG-001 v1.12; KT-STD-001 v1.8; STD-TPL-001 v0.9.
- **Read in part** (every section on templates, roles, publication, the bid definition and STD handling): TPR-CHG-001 v0.10; BDS-CHG-001 v0.7; CFG-CHG-002 v0.16.
- **Not read (not supplied):** STR-CHG-001, NDS-CHG-001, AUTH-ADR-001, LAW-REG-001, SEED-001, G1-REG-001, RES-IMP-001, KT-RCA-001, the Workflow Guidance Standard file, the roadmap, the candidate bundle ZIP, and the companion workbook.

## Changes to existing entries

| Entry | Field | Was | Now | Reason and source |
|---|---|---|---|---|
| PLN-CHG-001 | implementation_status | Not implemented | Not evidenced | Not in workflow_states.implementation. PLN-CHG-001 v1.27 control table: 'Not implemented by this document' — the document makes no implementation claim, which the register records as Not evidenced, as for BUD and REQ. |
| REQ-CHG-001 | scope | Structured requisition preparation, Planning-created Purchase ready for requisition hand-off, Budget reservation at authorisation and authorised handoff to Tenders. | Structured requisition preparation, the REQ-owned Purchase ready for requisition item derived from Planning eligibility after plan activation, Budget reservation at authorisation and authorised handoff to Tenders. | REQ-CHG-001 v1.12 §9.1C: the item is REQ-owned and derived at read time; 'No Planning event, REQ command or stored record is added.' |
| CFG-CHG-002 | scope | Site, responsibilities, procurement rules, schedules, STD Templates inspection and supplier portal operating settings. | Site entity, financial years and submission periods, funding sources, source-backed procurement rules, schedules, reminders and supplier portal support/legal settings. Responsibility surfaces belong to AUTH-ADR-001; STD Templates inspection belongs to STD-TPL-001. | CFG-CHG-002 v0.16 control table (Purpose) and §2: 'Excluded: installed-template inspection or administration'; AUTH owns responsibility surfaces; §10.11 gives STD Templates to STD-TPL-001. |
| CFG-CHG-002 | action | Project Owner approval, then implement public-portal and STD Templates settings. | Project Owner approval, then implement the supplier-portal settings. STD Templates inspection is implemented under STD-TPL-001, not CFG. | CFG-CHG-002 v0.16 §10.11. |
| TPR-CHG-001 | supersedes | v0.9 on approval | v0.9 on approval; absorbs TPUB-CHG-001 (Tender Publication) | Project Owner, 25 September 2026: TPUB-CHG-001 was absorbed into TPR-CHG-001 v0.10. |
| IF-006 | contract | Effective procurement rules, schedule profiles, responsibilities, public portal settings and release availability | Effective procurement rules, schedule profiles and public portal settings (responsibilities come from AUTH-ADR-001; template release availability from STD-TPL-001 through IF-007) | CFG-CHG-002 v0.16 §2 (AUTH owns responsibility surfaces; installed-template inspection excluded). |
| IF-012 | contract | Planning budget revision request with affected plan item, requested outcome, reason, requester, timestamps and immutable request identity | Planning budget revision request for one over-budget Budget Line of a Draft Plan Version: Planning request identity and idempotency key, Plan Version reference, Budget Line and expected revision, Planning's planned and over amounts (server-derived), requesting Planner and timestamps; Budget returns its request reference | PLN-CHG-001 v1.27 §§4.7, 7.2, 7.3 and BUD-CHG-001 v1.11 §§4.10, 8.5: the request is per Plan Version and Budget Line, with no plan-item, requested-outcome or reason field. |
| DEC-019 | decision | Plan activation creates a REQ-owned Purchase ready for requisition item in the existing Ready to start surface. | Plan activation makes a REQ-owned Purchase ready for requisition item appear in the existing Ready to start surface; the item is derived at read time, not stored. | REQ-CHG-001 v1.12 §9.1C. |
| DEC-019 | implementation_effect | Use the existing requisition aggregate and lifecycle; add no parallel task record, state, role, command or approval stage. | Derive the item in the requisition workspace read from Planning eligibility and the stable-item open slot; add no stored task record, state, role, command, notification or approval stage. | REQ-CHG-001 v1.12 §9.1C (derived item; no notification). |
| G1-002 | owner_doc | CFG-CHG-002 v0.16 / STD-TPL-001 v0.9 | STD-TPL-001 v0.9 | CFG-CHG-002 v0.16 §10.11: STD-TPL-001 §11 is the complete design and implementation authority for STD Templates. |
| G1-006 | requirement_status | Mixed approved/proposed | Project Owner review | Not in workflow_states.requirement. Gated by its least-approved owner document (TPR-CHG-001 v0.10, Project Owner review); owner_doc still shows the mix. |
| G1-013 | requirement_status | Mixed proposed/approved | Project Owner review | Not in workflow_states.requirement. Gated by BDS-CHG-001 v0.7 (Project Owner review); owner_doc still shows the mix. |
| G1-015 | design | Goods, Works and Services differ through metadata, not bespoke page forks. | Goods, Works and Services differ through code-owned product profiles and renderer compositions selected by the release metadata, not bespoke page forks or a generic metadata form. | BDS-CHG-001 v0.7 §4.4.3 and §4.4.7: a product 'cannot be admitted merely because its metadata fits the primitive field allowlist'. |
| G1-023 | requirement_status | Blocked by unresolved standard | Referenced—unresolved | Not in workflow_states.requirement. The blocking cause, the unresolved STD-ST-001 v0.5 file, is what 'Referenced—unresolved' records. |
| RES-003 | requirement_status | Mixed approved/proposed | Project Owner review | Not in workflow_states.requirement. Gated by CFG-CHG-002 v0.16 (Project Owner review). |
| RES-004 | requirement_status | Mixed approved/proposed | Project Owner review | Not in workflow_states.requirement. Gated by TPR-CHG-001 v0.10 and BDS-CHG-001 v0.7 (Project Owner review). |
| RES-005 | requirement_status | Needs reconciliation | Cross-document review | Not in workflow_states.requirement. 'Cross-document review' is the vocabulary state for reconciliation work (see AUD-008). |
| WF-003 | change | Create the complete hand-off register and consume it in My Work, waiting views and notifications. | Create the complete hand-off register and consume it in My Work and waiting views; send notifications only where a module's register row specifies one. | PLN-CHG-001 v1.27 §7.7: 'Notification: none from Planning in any row' (PLN23-AC-001); BUD-CHG-001 v1.11 and REQ-CHG-001 v1.12 add none; KT-STD-001 v1.8 §3B.4 requires each row to state whether one is sent. |
| PLN-027-002 | design | Show requested outcome, reason, Budget owner and returned outcome in plain language. | Show the over-budget line and amount, the Budget Officer who now holds the request, and the returned outcome in plain language. | PLN-CHG-001 v1.27 §§7.2, 10.6 (U07-WAITING-BUDGET-REVISION): the request carries no requested-outcome or reason field. |
| REQ-012-001 | change | Create the REQ-owned Purchase ready for requisition item when a plan is activated. | Show the REQ-owned Purchase ready for requisition item, derived at read time, once a plan is activated. | REQ-CHG-001 v1.12 §9.1C. |
| REQ-012-001 | functional | Use the existing requisition aggregate and Ready to start lifecycle with no new role, state, command or approval stage. | Derive the item in the workspace read from Planning eligibility and the stable-item open slot; no stored record, role, state, command, notification or approval stage. | REQ-CHG-001 v1.12 §9.1C and REQ112-AC-001–005. |

## New entries

| Entry | Kind | Status or severity | Basis |
|---|---|---|---|
| TPUB-CHG-001 | new document entry | Historical provenance | Do not use as implementation authority. Replace remaining current references with TPR-CHG-001 at each document's next revision (see AUD-017). |
| DSP-CHG-001 | new document entry | Referenced—unresolved | Locate or admit the exact controlled file and version. Outside the Gate 1 slice. |
| STD-TPL-IMP-001 | new document entry | Historical provenance | Do not implement from it. STD-TPL-001 §13.11 requires a complete successor before release 1.1 is coded (G1-025). |
| E2E-REQ-001 | new document entry | Referenced—unresolved | Obtain the exact controlled file and check it against REQ-CHG-001 §2.1 and the Budget reservation addition before claiming conformance. |
| G1-025 | new delivery item | Draft | STD-TPL-001 v0.9 §13 authorises no DocType, route, migration, permission or production deployment; §13.11 requires a complete successor before coding release 1.1. |
| AUD-015 | new audit finding | High / Reconciliation | BUD-CHG-001 v1.11 BUD-DES-19 tells the Budget Officer 'Procurement Planning will see your reason', but the BudgetRevisionRequestOutcome.v1 payload in BUD-CHG-001 §8.5 and PLN-CHG-001 v1.27 §7.3 carries no decline reason, and the PLN §7.7 row passes only 'the outcome'. IF-013 expects the reason. |
| AUD-016 | new audit finding | High / Implementation handoff | No implementation authority exists for the STD Templates runtime: STD-TPL-001 v0.9 §13 authorises no DocType, route, migration, permission or production deployment, and §13.11 requires a complete successor to the obsolete STD-TPL-IMP-001 v0.2 before release 1.1 is coded. |
| AUD-017 | new audit finding | Medium / Stale reference | KT-STD-001 v1.8 §12.1 lists TPUB-CHG-001 among documents needing the workflow-guidance correction, but TPUB-CHG-001 was absorbed into TPR-CHG-001 v0.10. |
| AUD-018 | new audit finding | Medium / Document defect | PLN-CHG-001 v1.27 has two editorial defects: the U10-CHANGED row in §10.9 merges the Kind and Headline cells (6 cells under a 7-column header), and §13.4 and PLN27-AC-005 cite a bare '§8.3' that means KT-STD-001 §8.3. |
| AUD-019 | new audit finding | Medium / Document defect | BUD-CHG-001 v1.11 names 'Charles Kariuki' where the KT-STD-001 §8.3 register has Charles Mutiso, and §16's introduction states 98 acceptance criteria where 111 are defined. |
| AUD-020 | new audit finding | Medium / Reconciliation | TPR-CHG-001 v0.10 and BDS-CHG-001 v0.7 use a 'Daniel Otieno' fixture actor, and BDS also uses 'Peter Mwangi'. Neither is in the KT-STD-001 §8.3 register, and both resemble registered actors. |
| AUD-021 | new audit finding | Medium / Document defect | CFG-CHG-002 v0.16 cites KT-STD-001 sections as bare references (for example §3A.6, §2.3, §8.5 in its exceptions table) without naming the document. |
| AUD-022 | new audit finding | Medium / Evidence | KT-STD-001 and LAW-REG-001 are recorded with verification 'Passed', and the IT-EQUIPMENT-OPEN-V1 bundle with implementation 'Implemented', without an evidence reference. The register's status_rule forbids treating document approval as evidence. |
| AUD-023 | new audit finding | Medium / Missing controlled file | E2E-REQ-001 v0.2 is cited by REQ-CHG-001 but the exact controlled file was not in the admitted set. |
| AUD-024 | new audit finding | Info / Missing controlled file | DSP-CHG-001 is referenced by REQ-CHG-001 and KT-STD-001 but no controlled file or version was in the admitted set. |

## Verification

| Check | Result |
|---|---|
| JSON validity | Valid: 27 documents, 14 interfaces, 20 decisions, 39 delivery items, 10 future-work items, 24 audit findings |
| Field-level diff | Only the fields listed above differ; no entry removed; no top-level field changed |
| `preservation_check.py` | 16 entry lines changed and 4 extended, all by the edits above; 0 deleted |
| `register_check.py` | Before: 7 errors (status vocabulary). After: 0 errors. The three remaining warnings are the unevidenced statuses tracked as AUD-022 |
| Register versus documents | Version, status and approval date agree for all eight supplied documents |

## Judgements for your review

1. **Mixed statuses.** Delivery items whose owner documents have different statuses (for example REQ v1.12 approved with TPR v0.10 in review) now carry the status of their least-approved owner document, because the vocabulary has no mixed value. `owner_doc` still shows every owner. The alternative is to add a value such as "Mixed" to `workflow_states.requirement`.
2. **G1-023** now reads "Referenced—unresolved", naming its blocking cause (the unresolved STD-ST-001 file). **RES-005** reads "Cross-document review".
3. **Titles of three new document entries** are descriptive, because the supplied documents give an ID but no title: DSP-CHG-001, STD-TPL-IMP-001 and E2E-REQ-001. TPUB-CHG-001's title comes from PLN-CHG-001's source table.
4. **DSP-CHG-001** has no version, because none of the supplied documents states one.
5. **New finding types** "Document defect" and "Evidence" are introduced; the register does not enumerate finding types.
6. **AUD-022** leaves the three unevidenced statuses unchanged. Only you can confirm the evidence or reset them.

## Required follow-up outside the register

- **Companion workbook:** regenerate it from this register, per the register's governance rule.
- **KT-STD-001:** replace TPUB-CHG-001 with TPR-CHG-001 in §12.1 (AUD-017).
- **PLN-CHG-001 and BUD-CHG-001:** carry the decline reason in `BudgetRevisionRequestOutcome.v1`, or change the dialog text (AUD-015); correct the editorial defects (AUD-018, AUD-019).
- **TPR-CHG-001 and BDS-CHG-001:** register or replace the unregistered fixture actors (AUD-020).
- **CFG-CHG-002:** qualify its bare KT-STD-001 references (AUD-021).
- **STD Templates:** write the successor implementation pack (G1-025, AUD-016).

## Not verified

- The register's entries for documents not supplied (see the read list) were not checked against those documents.
- DSP-CHG-001's version and status, and E2E-REQ-001's current status, are unknown.
- The evidence, if any, behind the three statuses in AUD-022.
