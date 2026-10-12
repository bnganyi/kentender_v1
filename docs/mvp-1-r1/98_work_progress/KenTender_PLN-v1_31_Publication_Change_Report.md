# Change report — PLN-CHG-001 v1.31 and SEED-002 v0.4 (MVP 1 publication confirmed by the Planner)

Written 9 October 2026 under the KenTender document-change protocol. This report accompanies two new proposed versions. It is not an approval.

## 1. Files

| | Input | Output | Version and status |
|---|---|---|---|
| Planning | `04_planning/KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_30.md` (itself Proposed and uncommitted, written 9 October 2026 with NDS-CHG-001 v1.17) | `04_planning/KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_31.md` | v1.31, **Proposed — v1.29 was Approved; re-approval required** (builds on proposed v1.30) |
| Seed world | `20_seed_data/KenTender_SEED-002_Canonical_Seed_World_v0_3.md` (Approved 8 October 2026) | `20_seed_data/KenTender_SEED-002_Canonical_Seed_World_v0_4.md` | v0.4, **Proposed — v0.3 was Approved; re-approval required** |

Neither input was modified. Both outputs were produced by anchored edits (`apply_edits.py`; 106 edits to PLN, 13 to SEED-002). The base choice (v1.31 on top of v1.30; SEED-002 v0.4) was the owner's, answered on 9 October 2026.

**Decision recorded (owner instruction, 9 October 2026, quoted in v1.31's change scope row):** "For MVP 1, the Planner should record external submission and publication on behalf of the entity. The AO and CS retain their decision responsibilities; routine evidence capture should sit with the operational role." Flow: CS approval, Planner confirms publication, system activates if the existing checks pass.

## 2. Read list

- **Read in part, by section:** PLN-CHG-001 v1.30 (3,242 lines): control table and status paragraphs; §§1.1, 4.9, 5.2, 5.3.4, 5.5.2, 5.7, 6 to 6.5, 7.1 to 7.3, 7.7, 8, 9.2, 9.5, 9.6, 10.1A.1, 10.2, 10.12, 10.17, 10.18, 11.4, 11.7, 11.9, 12, 13.3, 14 (the acceptance rows that mention publication), 15, 16, 17, 18. **Not read in full**, contrary to protocol step 1: §§2 to 4.8, 5.1, 5.4, 5.5.1, 5.5.3, 5.6, 9.1, 9.3, 9.4, 10.3 to 10.11, 10.13 to 10.16, 13.1, 13.2, 13.4 and the §17.3 and §17.4 mapping tables were reached only by search for publication, Treasury, acknowledgement, adapter and retry.
- SEED-002 v0.3 (481 lines): control table, A1, A3, A4, the validation list and Appendix ledger rows 351 to 370, found by search; not read in full.
- Other sources read: `audit/DOC_CHANGE_REQUESTS.md` (DCR-01); `audit/REMEDIATION_TRACKER.md` decisions D4 and D5 and rows RG-01 and XC-106; LAW-REG-001 v1.2 rows LAW-OB-002 and LAW-OB-003; the baseline register entry for PLN-CHG-001; KT-STD-001 v1.27 (as the actor register for the consistency check).
- **Searched, no publication contract found:** AUTH-ADR-001 v1.12, SEED-001 v1.4, KT-STD-001 v1.27, HOME, OVS, ANL and CFG documents.
- **Not read:** PLN-CHG-001_Next-step_and_journey.md, the Planning implementation tracker and follow-ups beyond search hits, Artboards-U12-U13.dc.html.

## 3. Changes by section (manifest as made)

| Section | Operation | What changed | Source basis | New content |
|---|---|---|---|---|
| Header, control table | Replace and add | v1.31 status paragraph; Version, Date, Status, Approval record, Supersession rows with v1.30 rows retained; change scope | Owner instruction | Wording |
| §1.1 | Replace sentence | Publication is manual: the Planner confirms, the system activates | Owner instruction | Wording |
| §3, §4.9 | Add and mark | New record PlanPublicationConfirmation; PublicationIntent, Attempt, Acknowledgement and TreasurySubmissionEvidence marked historical | Owner instruction; code reading | Field list |
| §5.2.1, §5.2.3, §5.3.4 | Replace rows | New pending reason **Approved — publication confirmation needed**; transitions for Save draft, Confirm, Correct; retired transmit, retry and reconcile rows | Owner instruction | Wording |
| §5.5.2 | Rewrite | New §5.5.2.0 (reconciliation of v1.29, v1.30 and the 7 October build), §5.5.2.2 (confirmation), §5.5.2.4 (activation); §5.5.2.1 and §5.5.2.3 amended | Owner instruction; DCR-01; audit D4, D5 | Date rules, field limits |
| §5.7, §6, §6.4, §6.5 | Replace and add rows | Planner holds the turn; AO and Head lose publication actions; no segregation rule for recording publication; Planner journey row; technical recovery row removed | Owner instruction | Segregation default |
| §7.1 to 7.3, §7.7, §8 | Replace rows | Commands SavePublicationDraft, ConfirmPlanPublication, CorrectPublicationDetails; four commands retired; adapter row deferred; hand-offs; error messages | Owner instruction | Command names |
| §9, §10.1A.1, §10.2, §10.12, §10.17, §10.18 | Rewrite and replace | U13 screen and variants; stage 6 holder; fixture instants; headline-as-link rule | Owner instruction and message of 9 October | Variant names, wording, URL fixture |
| §11, §12, §13.3, §14, §15, §16, §17, §18 | Replace, add | Interaction map; audit; profiles; new §14.15 (PLN31-AC-001 to 019); older acceptance rows reworded; §15.3 deferrals; prohibited shortcut; ledger; PLN31-CHG-001 to 008; §18.0B | Owner instruction | IDs and wording |
| SEED-002 | Replace | Chronology rows, ledger row, control table; new fixture values paragraph | PLN v1.31 | URLs |

## 4. Preservation result

- **PLN v1.31 against v1.30:** `preservation_check.py ... --allow-control-table --allow <the lines below>`: original lines 3,243; revised 3,331; **Changed 100 (100 allowed), Deleted 0**, extended in place 30. Without the allowance the check fails on exactly these lines; each is an operational statement the owner's instruction supersedes, replaced rather than left beside its replacement, as the owner asked ("replace superseded operational wording rather than leaving conflicting instructions beside it"). Where the replaced wording carries a rule, the new text keeps a short "(v1.30 read: …)" note.
- **SEED-002 v0.4 against v0.3:** original 482; revised 486; **Changed 7 (7 allowed), Deleted 0**.

### 4.1 Every changed original line, verbatim — PLN-CHG-001 v1.30

## v1.30 status paragraph relabelled

```
**Status of this version — proposed.** Version 1.30 is **Proposed**. PLN-CHG-001 v1.29, approved on 3 October 2026, remains the approved document until the Project Owner approves this version. The controlling-approval paragraphs below record the approval of v1.29 and are retained as history. This version adds the receiving side of NDS-CHG-001 v1.17 (proposed): a Need-origin departmental plan entry starts from the accepted Need's estimated total cost, and Planning shows any change from it. Every other rule of v1.29 is retained.
```

## control: version

```
| Version | 1.30 |
```

## control: date

```
| Date | 9 October 2026 |
```

## control: status

```
| Status | Proposed — v1.29 was Approved; re-approval required |
```

## control: approval record

```
| Approval record | None for v1.30 |
```

## control: supersession

```
| Supersession | On approval only: supersedes v1.29, approved 3 October 2026, which is retained as historical evidence. |
```

## control: change scope

```
| Change scope | Domain change on the Project Owner decisions of 9 October 2026 (NDS-CHG-001 v1.17 §1.2): a Need-origin departmental plan entry starts from the accepted Need's estimated total cost, and Planning shows the change from it. Adds the entry reference and the prefill and change rules (§4.3), the `DepartmentalNeedAccepted.v3` consumer (§7.3), the funding-panel, certification and Procurement-review presentation (§§10.4, 10.5), the action-map row (§11.9), the isolated profile (§13.3), acceptance (§14.14), the owner dependency (§15.2), ledger and change rows (§§17.1, 17.4) and the proposed approval effect (§18.0A). The Need's estimate is never summed into any total. All v1.29 content is retained. |
```

## §1.1 publication sentence

```
Finance confirms the consolidated Plan's per-Budget-Line affordability. This confirmation creates no reservation and is separate from Plan approval. The Plan is formally submitted with preparation accountability, countersigned through Accounting Officer adoption, and approved through exactly one configured statutory route. Publication transmits the exact approved content after the Treasury-submission evidence gate. Authoritative acknowledgement plus successful activation checks activates the Version; a published Version that fails those checks is explicitly held under §5.5.2.
```

## §4.9 PlanPublication

```
| PlanPublication | Stable publication ID; snapshot/Version ID; configured destination reference; schema version; manifest of filename/media type/hash/size; frozen file references | One logical publication per approved snapshot/destination; repeated attempts do not invent a new package |
```

## §4.9 PublicationIntent

```
| PublicationIntent | ID; publication ID; durable dispatch state; created instant; hold/recovery correlation | Commit with approval; external send only after commit and valid Treasury evidence/no hold |
```

## §4.9 PublicationAttempt

```
| PublicationAttempt | ID; publication ID; attempt sequence; Pending/Acknowledged/Failed/Indeterminate; attempted instant; external reference; response evidence | Append-only attempts; indeterminate is not confirmed unpublished |
```

## §4.9 PublicationAcknowledgement

```
| PublicationAcknowledgement | Adapter event ID; publication/snapshot IDs; manifest/package hash; destination; public location; external reference; acknowledged instant | Authenticated exact-package correlation; duplicate event idempotent; mismatch cannot activate |
```

## §4.9 TreasurySubmissionEvidence + new record

```
| TreasurySubmissionEvidence | ID; approved Version/document hash; submission instant; channel; destination; dispatch reference; supporting attachment; exact-document confirmation; recorded actor/AUTH/instant; superseded record ID and correction reason where applicable | AO only; immutable append/supersede; current invalid evidence holds transmission; own evidence per successor |
```

## §5.2.1 pending row

```
| Approved — publication pending | Locked | Statutory approval recorded; activation not yet complete |
```

## §5.2.1 failed row

```
| Publication failed | Locked | Approval retained; retry/reconciliation required |
```

## §5.2.1 paragraph

```
`Indeterminate` belongs to publication-attempt state. The screen must distinguish an uncertain external result from a confirmed failed attempt even if both are held outside Active status. **Approved — awaiting Treasury submission evidence** is a pending reason within Approved — publication pending. A publication hold is a recorded control over transmission, not an unrecorded withdrawal of approval. A Published — activation held Version retains its historical evidence when a correcting successor becomes Active and records the explicit replacement link; it must never be described as having been Active.
```

## §5.2.3 approve row

```
| Awaiting statutory approval | Approve Annual Procurement Plan | Configured statutory authority | Record approval and Strategy snapshot; enqueue publication of exact approved content |
```

## §5.2.3 treasury row

```
| Approved — publication pending; Treasury evidence missing | Record Treasury submission | Accounting Officer | Append evidence for the exact approved Version; release this prerequisite only if valid |
```

## §5.2.3 transmit row

```
| Approved — publication pending; prerequisites met and no hold | Transmit and reconcile acknowledgement | System | Record authoritative publication evidence; activate only if activation checks also pass |
```

## §5.2.3 retry row

```
| Publication failed or indeterminate | Retry exact approved payload / reconcile | System; System Manager technical retry | No payload edit and no new procurement decision |
```

## §5.2.3 hold row

```
| Material defect found before publication completes | Hold publication | System on detected invalidity; authorised AO correction request | Hold new transmission, preserve outstanding-attempt state and reconcile any in-flight attempt |
```

## §5.2.3 request row

```
| Confirmed unpublished; no outstanding transmission | Request withdrawal for correction | Accounting Officer | Record reason and request to the configured statutory approving authority; content stays locked |
```

## §5.2.3 withdraw row

```
| Confirmed unpublished; valid AO request | Withdraw for correction | Configured statutory approving authority | Preserve approved evidence as Withdrawn for correction and create one copied Draft; repeat full governance |
```

## §5.2.3 activate successor row

```
| Successor publication acknowledged; all activation checks pass | Activate successor | System | Atomically change Active pointer, preserve balances and history, apply approved removals and publish eligibility/usage changes |
```

## §5.3.4 row

```
| Approved but publication incomplete, or Published — activation held | Hold/reconcile and use the explicit §5.5.2 recovery route; never edit approved content or assume a timed-out attempt was unpublished |
```

## §5.5.2 intro + 5.5.2.0

```
Approval commits the exact immutable content identity and a durable publication intent. External transmission occurs afterwards. A remote website call cannot be made part of the local database rollback by placing it inside ApproveAnnualPlan.
```

## §5.5.2.1 freeze paragraph

```
Freeze publication files and their hashes. Retries resend the exact approved files under the same publication identity. Preserve Annual Plan ID, exact Plan Version ID and stable Plan Item IDs. Disposal content is excluded. Owner-supplied operational dates appear separately; they never rewrite the approved publication. Approved successors create new publications and retain predecessors.
```

## §5.5.2.1 acknowledgement paragraph

```
The adapter acknowledgement identifies the exact package, its hash, public location and acknowledgement timestamp. A generic success response is insufficient. Distinguish confirmed failure, authoritative success and indeterminate result. Record external success even if activation checks fail. Activate once only when authoritative acknowledgement and all current activation checks pass.
```

## §5.5.2.2 rewrite

```
##### 5.5.2.2 Treasury submission evidence

Transmission to Treasury remains external in the MVP. The Accounting Officer uses **Record Treasury submission** against the exact approved Plan Version; this records an external action, not another approval.

| Field or control | Required contract |
|---|---|
| Submission evidence | Submission date/time, transmission channel, destination, dispatch/reference number and supporting attachment |
| Content identity | Link to the immutable approved document and system-generated hash; require confirmation that this was the document submitted |
| Audit | Record officer and recording timestamp automatically; distinguish submission time from recording time |
| Gate | Approved — awaiting Treasury submission evidence is the pending reason until valid evidence exists |
| Required proof | Submission/dispatch evidence; no extra Treasury approval or receipt-acknowledgement gate |
| Correction | Append a superseding evidence record with a reason; never overwrite the earlier record |
| Invalidated evidence | Hold transmission before publication; reconcile any outstanding attempt under §5.5.2.3 |
| Successor | Its own newly approved document requires its own evidence; predecessor evidence cannot satisfy the gate |

Treasury submission recorded, entity website publication acknowledged and State Portal publication are distinct facts. None proves the others. Automated Treasury transmission and acknowledgement handling are explicitly future facilities. This design follows the supplied LAW register; independent legal applicability verification remains a prerequisite.
```

## §5.5.2.3 row 1

```
| Confirmed unpublished; no outstanding transmission | Hold transmission. AO requests withdrawal with a mandatory reason; the configured statutory approving authority performs Withdraw for correction. Preserve the approved Version as Withdrawn for correction and create one copied Draft |
```

## §5.5.2.3 row 2

```
| Outcome unknown or transmission in flight | Hold further transmission and reconcile the existing attempt. No withdrawal or replacement candidate while publication remains uncertain |
```

## §5.5.2.3 row 3

```
| Confirmed published and valid for activation | Preserve publication and activate through the existing guarded process; subsequent correction uses a governed successor |
```

## §5.5.2.3 row 4

```
| Confirmed published but activation checks fail | Published — activation held. Preserve the external fact; the Version provides no new Requisition authority. Permit one linked correction successor without forcing defective content Active |
```

## §5.5.2.3 hold paragraph

```
A system-detected material defect or authorised correction request places transmission on hold immediately. A hold is not a withdrawal of statutory approval. Coordinate hold, worker dispatch and reconciliation so an in-flight attempt can never be classified as confirmed unpublished merely because the local worker stopped.
```

## §5.5.2.3 last sentence and new §5.5.2.4

```
A correcting candidate linked to a Published — activation held Version records both that correction origin and the actual current Active predecessor, if one exists. Activate against the current authoritative baseline and cumulative consumption, not against a fictional Active state for the held Version. On success, retain the held Version's true history and explicit replacement relationship. Technical retry authority cannot withdraw approval, edit the approved content or fabricate publication.
```

## §5.7 row 1

```
| Approved — publication pending; Treasury evidence missing | Publication | Accounting Officer: Your turn — Record the Treasury submission | `PLN_TREASURY_EVIDENCE_REQUIRED` | Waiting |
```

## §5.7 row 2

```
| Approved — publication pending; prerequisites met, no hold | Publication | System | — | Waiting for website publication |
```

## §5.7 row 3

```
| Publication failed or indeterminate | Publication (Blocked) | Authorised technical operator: Your turn — Retry publication or Check publication result | `PLN_PUBLICATION_FAILED` / `PLN_PUBLICATION_UNKNOWN` | Waiting on an authorised technical operator |
```

## §5.7 row 4

```
| Material defect held; confirmed unpublished | Publication (Blocked) | Accounting Officer: Your turn — Request withdrawal for correction | `PLN_PUBLICATION_HELD` | Waiting |
```

## §6 Planner row

```
| Procurement Planner | DPP validation, classification correction, consolidation, pending requirements and Plan corrections | Classify/reclassify under §5.1.6; package work, Finance request and successor/correction management | No source-fact editing, accepted-decision mutation or final HOPF signature unless separately assigned; no procurement creation or MVP forecast maintenance |
```

## §6 AO row

```
| Accounting Officer | Adoption, Treasury evidence, late explanation and withdrawal requests | Existing governed actions | Does not impersonate the statutory authority |
```

## §6 technical row

```
| Administrator/System Manager | Technical read under KT-STD-001 v1.7 §3A.6 | Read all Planning records site-wide through registered routes; no business command. Separately granted setup/publication-recovery authority uses the owning contract. | Technical read supplies no Planning decision or publication retry authority |
```

## §6.5 AO row

```
| Accounting Officer — Record external evidence and request withdrawal | U13 and §11. **Record Treasury submission**, **Correct submission details**, **Explain late start of the annual plan** when applicable; **Request withdrawal for correction** only for confirmed-unpublished eligible content. | Evidence recording is not Treasury approval. A withdrawal request goes to the existing statutory authority. AO cannot declare publication successful, change activation dates or withdraw a published plan through this route. |
```

## §6.5 technical row

```
| System Manager / authorised technical operator — Recover publication | Same publication record as U13, with the permitted recovery action for its actual state: **Retry publication** or **Check publication result**. | Technical commands retry the same approved content or read/reconcile an existing attempt. They do not edit the plan, bypass checks or supply business approval. Technical read access alone does not grant retry authority. |
```

## §7.1 GetPublicationTask

```
| GetPublicationTask | Publication/Version ID | Approved package, Treasury history, attempts, confirmed/unknown result, hold/withdrawal/activation outcome and allowed recovery actions |
```

## §7.2 RecordTreasurySubmission

```
| RecordTreasurySubmission — AO | Exact approved Version; §4.9 evidence and document confirmation | Append evidence; validate own Version/document; release transmission prerequisite only if current/valid |
```

## §7.2 CorrectTreasury

```
| CorrectTreasurySubmissionEvidence — AO | Prior evidence ID; corrected evidence; reason | Append superseding record; preserve old; hold/reconcile any affected in-flight publication |
```

## §7.2 Hold

```
| HoldPlanPublication — system on invalidity / AO correction request | Exact publication, reason/evidence | Hold new dispatch; preserve in-flight uncertainty; no withdrawal of approval |
```

## §7.2 RequestPlanWithdrawal

```
| RequestPlanWithdrawal — AO | Confirmed-unpublished approved Version; reason | Record request to exact statutory authority; no outstanding transmission; content locked |
```

## §7.2 Withdraw

```
| WithdrawApprovedPlanForCorrection — statutory authority | Valid AO request; resolution reference when collective | Confirm still unpublished/no outstanding attempt; retain approval/withdrawal and create one copied correction Draft |
```

## §7.2 PublishAnnualPlan

```
| PublishAnnualPlan — system worker | Durable publication ID | Post-commit only; Treasury/hold checks; send exact immutable manifest under stable deduplication identity; record attempt |
```

## §7.2 Reconcile

```
| ReconcilePublication — system / technical System Manager | Existing attempt/publication ID | Read authoritative destination result; never set success manually; unknown remains held |
```

## §7.2 Retry

```
| RetryPublication — system / technical System Manager | Confirmed safely retryable publication ID | Same frozen files/identity; indeterminate must reconcile first; no business approval or payload edit |
```

## §7.2 Activate

```
| ReceivePublicationAcknowledgement / ActivatePlanVersion — system | Exact signed/validated acknowledgement and current aggregate tokens | Preserve publication even on invalid activation; activation checks all sources/basis/locks/allowances/predecessor; switch once or Published—activation held |
```

## §7.3 adapter row

```
| Publication adapter | Stable publication identity, exact approved snapshot/manifest, destination; reconciliation by same identity | Exact manifest/hash-bound authoritative acknowledgement, confirmed failure or unknown; no guessed success |
```

## §7.7 approve row

```
| ApproveAnnualPlan with Treasury evidence missing | Accounting Officer | Record the Treasury submission | None | Valid evidence recorded |
```

## §7.7 failed row

```
| Publication failed or indeterminate | Authorised technical operator | Retry publication / Check publication result | Accounting Officer: Waiting on publication recovery | Acknowledgement or confirmed result reconciled |
```

## §8 TREASURY row

```
| PLN_TREASURY_EVIDENCE_REQUIRED | Record evidence that this approved plan was sent to Treasury before website publication. |
```

## §8 FAILED row

```
| PLN_PUBLICATION_FAILED | The plan was not published. The approved document is unchanged. |
```

## §8 UNKNOWN row

```
| PLN_PUBLICATION_UNKNOWN | We could not confirm whether publication succeeded. Check the existing attempt before trying again. |
```

## §8 ACK row

```
| PLN_PUBLICATION_ACK_MISMATCH | The publication confirmation does not match this approved plan. |
```

## §9.2 U13 row

```
| U13 publication | /app/procurement-planning/publication/{publication_id} | AO submission evidence and eligible withdrawal request; authorised technical recovery |
```

## §9.5 row

```
| Publication | Exact approved package, submission evidence, external result and activation separately | U13 |
```

## §9.6 U13 row

```
| U13 | Treasury evidence missing/recorded/corrected; sending; confirmed failure; unknown; published and Active; published but held; eligible withdrawal request/decision |
```

## §9.7 publish-button sentence and acknowledgements

```
There is no new Author handover approval, HoD return stage, HOPF approval or business Publish button. Actions that commit a decision have the consequence immediately beside them. Do not layer an unnecessary checkbox, confirmation modal and final click over the same statement. Retain the specifically required HoD certification and Treasury document-match acknowledgements.
```

## §10.1A.1 stage 6

```
| 6 | **Publication** | Record Treasury submission; transmit and reconcile acknowledgement | As stated per U13 variant |
```

## §10.2 publication rows

```
| Publication acknowledgement, PUBLICATION scenario | 10 Dec 2026, 15:00 EAT |
```

## §10.12 U13 rewrite

```
### 10.12 U13 — Publication evidence and recovery

**Archetype and primary question:** Detail/evidence with a focused next action. **What has happened to this approved Plan, and what—if anything—must I do now?** Level 1 is the four-step status and the one lawful next action; Level 2 is the evidence for the current step; Level 3 is transmission and recovery history. Do not present all recovery mechanics as parallel controls.

**Purpose:** Record external submission evidence, observe publication/activation separately and use only state-appropriate recovery.

**Fixture — outside the artboard:** Approved Plan Version 1. Primary AO fixture: Amina Hassan; 10 Dec 2026, 13:45 EAT before Treasury evidence. PUBLICATION variants supply later states.

**Header.** Title **Complete publication of the annual plan**; description **Record when the approved plan was sent to the National Treasury and attach the submission evidence.** Plan title, reference **PLN-MOH-2027-001**, Version **1**, state **Approved — Treasury submission details needed** on separate rows. Upper-right links **View approved plan**, **Download approved plan**, **Download Plan data** in that order; enabled.

**Publication status.** Four rows in this order: Plan approval **Approved**; Treasury submission **Details not yet recorded**; Website publication **Not started**; Use for procurement **This plan is not yet active**. Each row has its own label and state. Immediately below, enabled primary **Record Treasury submission** for Amina.

**U13-TREASURY-FORM.** Standard form over/after header. Read-only Plan/reference/version. Fields: Date and time sent **10 Dec 2026, 14:00 EAT**; Submission channel **Official correspondence**; Destination **National Treasury**; Dispatch/reference number **MOH/APP/2027/001**; Submission evidence file **Treasury-dispatch-evidence-example.pdf** labelled **Illustrative fixture file**. Checkbox **I confirm that this approved plan is the document submitted** starts unchecked. Footer Cancel / Record submission disabled; helper **Confirm the document match to record this submission.** Checked variant enables Record submission.

**U13-EVIDENCE-RECORDED.** Status rows: Plan approval Approved; Treasury submission Recorded; Website publication Not started/next actual state; Use for procurement Not active. Beneath Treasury row show separate Date/time sent **10 Dec 2026, 14:00 EAT**; Recorded by **Amina Hassan**; Channel **Official correspondence**; Destination **National Treasury**; Dispatch reference **MOH/APP/2027/001**. Enabled **View submission evidence**; no Record button.

**U13-SENDING.** Website publication **Publication is in progress**; Use for procurement Not active. Show attempt started at and responsible system from exact attempt fixture. No retry/check/manual-success button.

**U13-FAILED.** Website publication **The plan was not published**; Use for procurement Not active. Show confirmed failure time/code/message from owner fixture. For a separately authorised technical operator show primary **Retry publication**; for AO/reader show Responsible role **Authorised technical operator** and no button. Technical read alone does not create retry authority.

**U13-UNKNOWN.** Website publication **We could not confirm whether publication succeeded.** Below: **Check the existing attempt before trying again.** Authorised technical operator gets **Check publication result** only. No Retry or manual success.

**U13-ACTIVE.** Website publication **Published**; Use for procurement **Current plan**. Separately labelled Publication acknowledged at **10 Dec 2026, 15:00 EAT**; Activated at from exact owner fixture. Enabled **View published plan** / **View current plan**. No preparation action.

**U13-PUBLISHED-HELD.** Website publication Published; Use for procurement **Published, but not available for new procurement**. Show exact failed mandatory check above actions. Planner gets **Prepare a corrected plan** if current guards allow; Current predecessor and action **View current plan** are separate.

**U13-UNPUBLISHED-DEFECT.** State **Publication is on hold**. Show exact confirmed defect/reason and evidence that no publication occurred. AO gets **Request withdrawal for correction**. No action for unknown/published content.

**U13-WITHDRAWAL-REQUEST.** State **Withdrawal requested — awaiting Cabinet Secretary**. Show request reason, Requested by **Amina Hassan** and request time from the exact withdrawal fixture. Daniel’s authority variant shows one enabled primary action: **Withdraw for correction**. No second business action appears.

**U13-WITHDRAWN.** State **Withdrawn for correction**; Plan approval **Historical approval retained**; Website publication Not published; Use for procurement Not active. Planner gets **Continue correction**; readers get **View withdrawn plan** only.

**U13-CORRECT-EVIDENCE.** Form heading **Correct submission details**. First block **Previous submission evidence** read-only with every recorded field. Second block repeats editable fields. Required **Reason for correction** blank. Footer Cancel / Save corrected details, disabled until a reason/change is entered. No overwrite language.

**U13-WITHDRAWAL-REQUEST-DIALOG.** AO dialog over U13-UNPUBLISHED-DEFECT. Header **Request withdrawal for correction**. Show exact approved Plan name, reference and Version **1**; Publication status **Confirmed not published**. Required **Reason for withdrawal** starts blank. Text **The approved plan will remain in history. If the request is approved, a correction draft will repeat the required review and approval.** Footer left **Cancel**; right primary **Request withdrawal for correction**, disabled until a valid reason is entered.

**U13-WITHDRAWAL-DECISION-DIALOG.** Cabinet Secretary dialog over U13-WITHDRAWAL-REQUEST. Header **Withdraw this plan for correction?** Show the exact Plan name, reference, Version **1**, request reason, Requested by **Amina Hassan**, request time and Publication status **Confirmed not published**. Text **The approved plan will remain in history. A correction draft will be prepared and will repeat the required review and approval.** Footer left **Cancel**; right primary **Withdraw for correction**, enabled. No editable reason and no return action.

**Visual check.** Approval, external submission, publication and activation are four distinct rows. Each state exposes exactly one valid recovery path and never treats unknown as failure.

**Next step and journey — added in v1.26.** Tracker always in **reduced** form: **Stage 6 of 7: Publication — {holder}**. The four publication status rows stay as the Level 2 working region, because they are the working detail of stage 6, not a second tracker. The header state row (for example "Approved — Treasury submission details needed") is replaced by the next-step line.

| Variant | Kind | Headline | Holder / since |
|---|---|---|---|
| U13 | Your turn | **Record the Treasury submission** | — |
| U13-TREASURY-FORM, unchecked and checked | Neither component; a form state of U13 | — | — |
| U13-EVIDENCE-RECORDED | Waiting on someone | **Waiting for website publication** | System; since **Awaiting fixture** |
| U13-SENDING | Waiting on someone | **Publication is in progress** | Responsible system and start time from the existing attempt fixture |
| U13-FAILED, authorised technical operator | Your turn | **Retry publication** | — |
| U13-FAILED, AO or reader | Waiting on someone | **Waiting for an authorised technical operator to retry publication** | Since: failure time from the existing fixture |
| U13-UNKNOWN, authorised technical operator | Your turn | **Check the publication result** | — |
| U13-UNKNOWN, AO or reader | Waiting on someone | **Waiting for an authorised technical operator to check the publication result** | Since: attempt time from the fixture |
| U13-ACTIVE | Done | **In force since {Activated at}**; the tracker reads **Stage 7 of 7: In force** | Activated at from the existing owner fixture |
| U13-PUBLISHED-HELD, Planner | Your turn | **Prepare a corrected plan** | — |
| U13-UNPUBLISHED-DEFECT, AO | Your turn | **Request withdrawal for correction** | — |
| U13-WITHDRAWAL-REQUEST, AO | Waiting on someone | **Waiting for Daniel Rotich (Cabinet Secretary) to decide the withdrawal** | Since: request time from the existing fixture |
| U13-WITHDRAWAL-REQUEST, Daniel | Your turn | **Withdraw the plan for correction** | — |
| U13-WITHDRAWN, Planner | Your turn | **Continue the correction**; the tracker restarts at Preparation on the correction Draft | — |
| U13-CORRECT-EVIDENCE and both U13 dialogs | Neither component | — | — |
```

## §10.17 technical sentence

```
Technical readers follow KT-STD §3A.6 for Planning data. Setup maintenance follows CFG/AUTH. Publication retry appears in U13 only to a separately authorised technical operator; it is not acquired from technical read.
```

## §10.17 late activation wording

```
**U21-LATE-ACTIVATION.** Dialog over the initial plan activation context. Heading **Explain late start of the annual plan**. Separate read-only facts Financial year started **1 Jul 2027**; Plan became active **2 Jul 2027, 09:00 EAT**. Required multiline Explanation **Publication acknowledgement was received after the financial year began.** Footer Cancel / primary Record explanation. No editable date or update-plan variant.
```

## §10.17 technical detail

```
**U21-TECHNICAL-DETAIL.** Administrator/System Manager on any U02/U06/U07/U09/U10/U11/U13/U16 route. Render the same full facts for the exact status; all business mutation/decision controls absent. Read/navigation disclosures and exact evidence links remain. The U13-FAILED and U13-UNKNOWN authorised-operator variants show the separately granted publication-recovery command stated in those variants. Every other technical-reader variant omits it.
```

## §10.18 U13 row

```
| U13 | Missing/recorded Treasury evidence; form unchecked/checked; sending; failed AO/technical; unknown AO/technical; Active; published-held; unpublished defect; withdrawal request/decision/withdrawn; correction form/dialog. |
```

## §11.4 rewrite

```
### 11.4 Publication and recovery

The Treasury form records external dispatch, not Treasury approval. Each successor has its own evidence. Invalidating that evidence holds new transmission and reconciles outstanding attempts. A technical Check publication result may only invoke the authoritative adapter's read/reconciliation; it cannot set success manually. Its exact adapter contract is a prerequisite.

Only confirmed-unpublished content may follow AO request/statutory withdrawal. Unknown publication state cannot offer withdrawal or a competing replacement candidate. Acknowledged but invalid content remains Published — activation held and exposes a correction successor without obtaining procurement eligibility. Preserve an existing Active predecessor separately.

The UI never hides external publication merely because activation failed. Public-view/PDF/JSON identity is exact and operational updates remain separate. The review pack is not confused with the approved publication or Treasury attachment.
```

## §11.9 treasury row

```
| Record/Correct Treasury submission | Open U13 form and append/correct exact external evidence. | §5.5.2; acknowledgement required; prior evidence preserved. |
```

## §11.9 retry row

```
| Retry publication / Check publication result | Retry same approved content after confirmed failure, or reconcile existing unknown attempt. | §5.5.2; separately authorised technical command; unknown is not failure. |
```

## §11.7 acknowledgements

```
Approval/signature/adoption text sits beside its specific action and identifies the actual consequence. Preserve HoD and Treasury acknowledgements; do not add a generic checklist of opened screens, a forced download or duplicate confirmation dialog. An explicit decline/return still records its required reason. Do not invent a HoD return task, HOPF approval, per-member collective vote, assignee picker or Planner-to-HOPF approval stage.
```

## §12 publication row

```
| Publication | Approved document, Treasury evidence history, actual adapter outcomes, acknowledgement and activation outcome |
```

## §12 audit sentence

```
Every command records its exact input/output identities, expected/resulting token, actor or authenticated producer, exercised authority, prior/resulting states, idempotency correlation, decision reason/evidence where required and instant. Audit derives actor/time server-side. Financial-basis reuse, source substitution/exclusion, scope protection, every correction request disposition, Treasury corrections, publication reconciliation/withdrawal and activation failure are distinguishable. Preserve immutable earlier versions, decisions and files. Reversal is a linked record, never erasure. A failed transaction cannot leave a signature, allocation, drawdown or pointer partially committed.
```

## §13.3 profile

```
| Publication recovery | Separate missing-evidence, confirmed-failure, unknown and published-held profiles; no injected success or reuse of one live publication identity across incompatible histories |
```

## AC-030

```
| PLN18-AC-030 | Approval commits durable intent; external transmission follows valid exact-Version Treasury evidence and hold checks. Authoritative acknowledgement is recorded; activation occurs once only when every current activation predicate passes. |
```

## AC-043

```
| PLN18-AC-043 | Publication is an idempotent system action; any technical retry reuses the exact approved payload. |
```

## UX-16

```
| PLN18-UX-16 | Treasury evidence gate, append-only correction, exact document match and successor-specific evidence work without an extra Treasury approval stage |
```

## UX-17

```
| PLN18-UX-17 | Confirmed failure, unknown outcome and published-held are distinct; no unsafe withdrawal/blind retry; hold/dispatch concurrency preserves the external truth |
```

## UX-18

```
| PLN18-UX-18 | Web/PDF/JSON publication derives from one immutable snapshot; no disposal or OCDS-compliance claim; activation does not occur on generic success |
```

## §14.3 item 5

```
5. Publication intent commits separately from external transmission. Treasury evidence gates exact-Version dispatch; crash/unknown/duplicate callbacks, hold races, confirmed-unpublished withdrawal and published-held corrections preserve external fact and activate at most once.
```

## UX-033

```
| PLN19-UX-033 | AO Treasury evidence matches the exact approved document and records dispatch only; correction appends history. Late initial adoption/activation explanations occur in their correct contexts without backdating or ordinary-update duplication. |
```

## UX-034

```
| PLN19-UX-034 | Publication failure, unknown outcome and published-held remain distinct; only safe retry/reconciliation/eligible withdrawal actions appear for authorised actors. No blind retry, manual success or forced activation exists. |
```

## §14.5 AO row

```
| AO external evidence | Record that the exact approved plan was sent to Treasury | Dispatch, receipt and approval distinguished |
```

## §14.5 technical row

```
| Technical recovery | Investigate an uncertain publication result | Checks existing attempt before retrying |
```

## §15.2 row 7

```
| 7 | Implement the agreed schedule, publication and reporting boundaries after their prerequisites | Method profiles, deterministic calculations, exact publication package/acknowledgement, Treasury evidence, recovery paths and report data ownership contracts |
```

## §15.2 publication row

```
| Publication package and adapter | PLN publication owner | Exact KenTender JSON schema and human-readable mappings; immutable approved files; hash-bound acknowledgement; Treasury evidence; failure/indeterminate reconciliation; withdrawal and activation-held correction contracts |
```

## §15.3 transmission row

```
| Automated Treasury transmission and acknowledgement | AO records external submission evidence | Transmission adapter, exact document correlation, receipt/reconciliation and exception handling |
```

## §17.2 adapter row

```
| Planning publication adapter | Frozen web/PDF/JSON package and exact acknowledgement under §5.5.2 | Final schemas, protected package/export mapping, Treasury evidence, read reconciliation, unknown/failure recovery and activation race tests |
```


### 4.2 Every changed original line, verbatim — SEED-002 v0.3

## control: version

```
| Version | 0.3 (v0.2: proposed 8 October 2026 and superseded before approval; v0.1: proposed 5 October 2026) |
```

## control: date

```
| Date | 8 October 2026 (v0.1: 5 October 2026) |
```

## control: status

```
| Status | **Approved — 8 October 2026** (proposed read: Proposed — Project Owner approval required. Not approved.) |
```

## control: approved on

```
| Approved on | 8 October 2026 |
```

## A1 dates sentence

```
| How the dates are made | Every seeded command runs **at** its fixture instant under the frozen seed clock (`kentender_core.seeds.clock`); nothing is back-stamped, except the two publication-attempt instants one inline worker run cannot both hold. Year 2 keeps the module seeds' instants; Year 1's planning history is the same journey **364 days (52 weeks) earlier**, so each event keeps its weekday and spacing. Year 1's execution keeps its own March–July 2027 instants. |
```

## Year 1 plan row

```
| Year 1 Annual Plan | items formed 2 Dec 2025; funding requested 4 Dec, confirmed 5 Dec 10:00; signed 8 Dec 10:00; adopted 9 Dec 10:00; approved 10 Dec 11:00; Treasury evidence 11 Dec 14:00; published and Active 11 Dec 2025 15:00 |
```

## Year 2 plan row

```
| Year 2 Annual Plan | confirmed 4 Dec, signed 7 Dec, adopted 8 Dec, approved 9 Dec; published and Active 10 Dec 2026 15:00 |
```

## A4 same commands

```
- **The same commands as the screens, as the named people**, never Administrator for a business decision, each at its fixture instant. No direct write to a governed record, except the namespace stamps that let `reset` recognise canonical rows and the publication attempt's two instants.
```

## validation planning bullet

```
- **Planning:** each year's departmental certifications and acceptances; for an Active plan its signature, item count, each item's approved invitation, estimate basis and completion inside the year, activation instant, Treasury evidence and reference, and each funded Need Fully included; at `NEXT=departmental_plans`, a Draft Annual Plan; below it, no FY 2027/28 plan past Draft. At `CURRENT=annual_plan` also the plan's full read (items, value, eligibility, Finance, governance, publication).
```

## ledger row 364

```
| §3.7 synthetic Treasury evidence bytes, labelled; publication by the sandbox adapter, labelled simulation | Carried | `Treasury-dispatch-evidence-example.pdf` per plan version |
```

## ledger row 363

```
| §3.7 governance chronology and Treasury dispatch `MOH/APP/2027/001` | Carried, moved 364 days for Year 1 | §A3; Year 1 Treasury reference `MOH/APP/2026/001`, Year 2 keeps `MOH/APP/2027/001` |
```


## 5. Consistency result

- **PLN v1.31:** ERROR 3, WARN 9, INFO 6. **v1.30 baseline:** ERROR 3, WARN 8, INFO 7. The three errors are the same rows, shifted: a 6-cell row under a 7-cell header in the U10 next-step table, and two `§8.3` references that name KT-STD-001 §8.3 without the document name. All pre-existing. **One warning introduced:** LAW-REG-001 is now cited at v1.1 (existing, §6.2) and v1.2 (new, §5.5.2.2 and the change scope), because I read LAW-REG-001 v1.2 this session.
- **SEED-002 v0.4:** ERROR 82 (v0.3: 83). All cross-document `§` references of the kind the v0.3 baseline already has; the v0.3 error that flagged Approved-on beside a Proposed status is gone.
- **register_check:** the register lags the library. It records PLN-CHG-001 at v1.29 and does not know proposed v1.30, v1.31 or SEED-002 v0.4; it also carries 15 errors that predate this change. **The register needs updating by the documentation owner; I did not edit it.**

## 6. New content for owner review

Every item below is mine, not taken from a source.

- **Names and IDs:** PlanPublicationConfirmation; SavePublicationDraft, ConfirmPlanPublication, CorrectPublicationDetails; U13 variant names U13-CONFIRM-FORM, U13-DRAFT-SAVED, U13-WAITING, U13-CORRECT-DETAILS; §§5.5.2.0 and 5.5.2.4; PLN31-AC-001 to 019; PLN31-CHG-001 to 008; §14.15; §18.0B.
- **Rules:** the Treasury date may not be before the date of statutory approval nor in the future; the website date may not be before the Treasury date nor in the future; the URL must be http or https; the reference is at most 140 characters; a correction reason is 10 to 500 characters (the existing evidence-correction length); a Planner who prepared, requested Finance for or signed the plan may confirm its publication; a Version already in the historical **Publication failed** status can be confirmed.
- **Wording in bold:** the U13 title, description, status values (**Not yet confirmed**, **Confirmed**), **Complete every field and tick the confirmation to confirm.**, **Draft saved. Nothing has been confirmed yet.**, **Correcting these details does not change the approved plan, deactivate an active plan or repeat an approval.**, **Earlier publication attempts**, **Waiting for Mercy Kilonzo (Procurement Planner) to confirm publication**, and the re-worded message for `PLN_TREASURY_EVIDENCE_REQUIRED`. The confirmation statement and the labels you named are verbatim from your instruction.
- **Fixture values:** the public plan URLs `https://www.moh.example.test/procurement/annual-procurement-plan-2026-27` and `…-2027-28`, labelled illustrative. Instants are unchanged (activation 15:00 on 11 December 2025 and 10 December 2026, now Mercy's recording instant).
- **Headline as the link:** every Your turn headline that names an action held on another page carries a link to it (PLN31-AC-016).

## 7. Decisions needed from the Project Owner

1. **Approve v1.31 (and with it v1.30) and SEED-002 v0.4.** Recommendation: approve together; v1.31 retains every v1.30 rule.
2. **The three date rules and the URL rule** (§6 above). Recommendation: keep; they stop an impossible record, and the Planner can still save a Draft.
3. **PDF.** The frozen package holds one file, the JSON. **Download approved plan** and **Download Plan data** both serve it. The spec names a PDF and an accessible web view that have never been built. Recommendation: say which is needed for MVP 1.
4. **Reseeding the dev site.** Its canonical world was built under the v1.30 flow, so `make seed-canonical-validate` fails there until it is rebuilt. I did not reseed it because you are mid-test. Recommendation: rebuild when you finish.
5. **DCR-01 items 9 to 11** (quantity precision wording, read and write scope, the AUD-PLN-021 withdrawal question) remain open and are not made here. Items 1 to 8 are superseded by this change.

## 8. Required corrections elsewhere (not made)

- **LAW-REG-001 v1.2**, row LAW-OB-002: its owner column still names adapter acknowledgement, reconciliation and publication evidence. Legal wording needs a verified source, so I did not edit it.
- **PLN-CHG-001_Next-step_and_journey.md** (U13 rows and the stage 6 holder); the **Planning implementation tracker and follow-ups** (record the 9 October decision and that it supersedes the 7 October decision); **audit/DOC_CHANGE_REQUESTS.md** DCR-01 items 1 to 8 and **audit/REMEDIATION_TRACKER.md** decisions D4 and D5 (mark superseded).
- **Artboards-U12-U13.dc.html**: the new U13 variants need artboards before design sign-off. The fidelity gate no longer compares U13 to a board.
- **KenTender_Baseline_Register.yaml**: PLN-CHG-001, SEED-002 and the approval status of v1.30.
- **Workspace and My Work** still read **Open decision** and **Open Finance task** for the Accounting Officer, the statutory authority and Finance (the plan page's own button was renamed on 9 October).

## 9. Not verified

- The v1.31 text is not checked against the 3,242-line v1.30 outside the sections listed in §2, so a sentence elsewhere may still describe the retired flow. A search for publication, Treasury, acknowledgement, adapter, retry and reconcile found the lines edited here and the §17.3 and §17.4 historical mapping rows, which §17 says are history.
- Whether the Treasury and website dates are the right legal facts to record: no legal source was consulted beyond LAW-REG-001 v1.2 rows LAW-OB-002 and LAW-OB-003.
- Any statement in the new text about a document I did not read (§2 lists them).

## 10. Follow-up the same day: naming the wrong field

First Planner test of the form (9 October 2026): an address typed as `www.xyz.com` enabled Confirm and was refused with a generic sentence that named no field. Cause: the server's field detail never left the server, and the form checked only that boxes were non-empty. Fixed by carrying the refusal's code and fields on the message log (as Requisitions does), naming the field in the message, applying the same rules in the form as the Planner types, and marking the server-refused field. Documented as PLN31-AC-018 and PLN31-CHG-007 (three further anchored edits, no original line changed).

Second report from the same test: **Save draft** with an address that did not yet start with https:// saved nothing and said nothing, because a Draft was refused under the confirmation's rules (and my browser test had only checked that nothing else changed, never that the values came back). A Draft now keeps what was typed and the rules apply at confirmation; it says when it was saved; a refused save says nothing was saved. PLN31-AC-019 and PLN31-CHG-008; the browser test now reloads the page and checks every value and the attached file.

## 11. Build and test evidence (the code that implements these documents)

Behaviour built: `publication_confirmation.py` (three commands), the new record `Plan Publication Confirmation`, the activation hand-off, the removal of the worker, adapter, acknowledgement, retry, reconcile and the Head's Publish, the Planner's work rows, the Your-turn link, the confirmation screen and the approved-package download, and the canonical seed.

| Check | Result |
|---|---|
| `test_plan_publication_confirmation` (28 new tests: authorised and unauthorised, wrong and stale Version, incomplete evidence, duplicate presses, held activation, correction, successor, hold, withdrawal, read model, download) | 28 passed |
| `test_plan_publication`, `test_plan_governance`, `test_planning_api_requests`, `test_plan_v127_guidance`, `test_dead_end_matrix`, `test_plan_requisition`, `test_planning_workspace`, Requisitions `test_lifecycle`, `test_authorise`, `test_correction` | all passed |
| `planning-seed-gate` (after rebuilding the canonical world on the test site with the new seed) | planning seed tests 7 passed |
| Component tests, whole Planning front end (including the field-error and transport tests) | 421 passed |
| Playwright `planning-publication.spec.ts` (Planner confirms and the plan becomes current; Your-turn link; held state and correction; withdrawal), `planning-governance`, `planning-guidance`, `pln-finance` | 24 passed |
| **Failing, unrelated to publication** | `test_home_provider` (one departmental-plan row timestamp); `test_planning_v123_schema` allow-list (the `need_estimated_total_cost` field from today's Needs v1.17 work); two Needs architecture tests (a `get_all("Departmental Need")` already in HEAD's seed file); Playwright `pln-annual-plan` (expects "Finance is reviewing the funding", the page says "Awaiting confirmation"). None touches the publication code; I did not run them against a clean checkout. |
