# Handoff: Departmental Needs and Procurement Planning changes, 16 October 2026

**For:** whoever revises NDS-CHG-001 and PLN-CHG-001 and implements the result.
**Baseline:** NDS-CHG-001 v1.17 (approved 9 October 2026). PLN-CHG-001 at its current approved version; it was not read for this handoff, so PLN section numbers below must be checked against the file.
**Follow:** the `kentender-document-change` protocol. Every v1.17 rule is retained unless a change below replaces it. Replaced wording is kept beside its correction.

## Project Owner decisions, 16 October 2026

| ID | Decision | Owner's words |
|---|---|---|
| D1 | A Head of User Department can create a Need for their department without holding the Departmental Author responsibility. | "the HOD can create a need for the department unfettered. He is the HOD!" |
| D2 | Heads may also enter their own requirements directly in the departmental plan, as Planning already allows (NDS-BR-021). Needs remain optional. | "Heads directly plan their requirements" |
| D3 | When an accepted Need's withdrawal is blocked by the annual plan, the Procurement Planner gets a Planning work item. | "Add" |
| D4 | An Author cannot recall a submitted Need. No change. | "Leave it for now" |

**Reading applied to D1 ("unfettered").** A head's own Need does not go to another head for review: it is accepted for planning when the head submits it. The head acts as both maker and decider for their own department. The derived rules R4 to R6 below apply the same principle to updates and withdrawals. The owner should confirm R4 to R6 when approving v1.18.

## Part A: NDS-CHG-001 v1.18

### A1. Rules

| ID | Rule | Replaces or changes |
|---|---|---|
| R1 | A user with an active Head of User Department assignment (substantive or acting) may create, edit, submit and withdraw a Need for any Organisation Unit in that assignment's subtree. A Departmental Author assignment is not required. | §6 ("HoD responsibility by itself grants no Author creation/edit rights"), §6.1, NDS-BR-005 |
| R2 | **Head's own Need is accepted on submission.** A revision submitted by a user who, at the moment of submission, holds an active Head of User Department assignment covering the Need's OU is accepted in the same transaction. The transaction freezes the revision and its hash and runs every acceptance check: current unit, estimate precision, hash, intake for an initial submission, and concurrency. It records two decisions, Submitted and Accepted for planning, both by the head under that HoD assignment ID. It publishes `DepartmentalNeedAccepted.v3`. It creates no review task. | §5.1 (new row), NDS-BR-006, NDS-BR-010 |
| R3 | **Maker-checker for Authors is unchanged.** A revision submitted by a user without HoD authority over the Need's OU is reviewed by a head, never by its submitter. | NDS-BR-006 restated |
| R4 | **Updates by a head.** An update to an accepted Need that is submitted by a head of that department is accepted on submission under R2. It supersedes the earlier revision atomically and publishes the supersession event. | §5.2 (new row) |
| R5 | **Withdrawals by a head.** A withdrawal request raised by a head of that department is decided on raising. It is approved immediately if Planning confirms no Active dependency across all revisions (§8.3). Otherwise it goes to Awaiting planning clearance, and the same head may approve it later once it is cleared. Unknown or stale dependency evidence still blocks approval. | §5.3 (new rows) |
| R6 | **Dual role in the same department.** A user who is both a Departmental Author and a head of the same OU is treated as a head for that OU, so R2, R4 and R5 apply. | §6.1 "Dual-role user" |
| R7 | **Unchanged for heads' Needs:** the intake window (NDS-BR-002/003), the seven required facts including the estimated cost (NDS-BR-007, BR-022 to BR-025), immutability, one open update or withdrawal at a time, and the Planning payload. | — |
| R8 | **Acting heads** follow R1 to R6 only within their dated assignment's OU subtree and period. | §6 acting-HoD paragraph |

### A2. Lifecycle table additions (§5.1 to §5.3)

| Current state | Command | Result | Actor |
|---|---|---|---|
| No record | Save Draft | Draft Revision 1 | Departmental Author **or Head of User Department** |
| Draft | Submit | **Accepted for planning** (no Submitted state persists; both decisions recorded) | Head of User Department for the Need's OU |
| Accepted, Draft update | Submit update | **Successor accepted; earlier revision Superseded** | Head of User Department |
| Accepted | Request withdrawal | **Approved, or Awaiting planning clearance** | Head of User Department |

### A3. Commands (§8.2)

- `submit_need_revision`: after authorisation, if the actor holds HoD authority over the Need's OU, call the existing acceptance path in the same transaction. Do not create a review task. Use one idempotency key for the whole action; a replay returns the accepted result.
- `request_accepted_need_withdrawal`: if the actor is a head of the Need's OU, run the §8.3 decision validation in the same transaction and approve, or set Awaiting planning clearance.
- No new command names. `NDS_MAKER_CHECKER` stays for Authors only.

### A4. Next step, journey and hand-offs (§5.5, §7.6)

- **Journey for a head's own Need:** Preparation goes straight to Accepted for planning. The Head of Department review stage shows as completed by the same head at the same instant; do not show it as skipped or pending.
- **Next step after submission:** Done, using the existing line "Accepted for planning by {actor} on {instant}".
- Delete the §5.5 maker row "Waiting for another Head of User Department to review this requirement" and its sentence. Keep the row as historical wording beside the correction.
- §7.6: no review item and no "waiting for review" item for a head's own submission.

### A5. Screens (§11) — new wording for owner review

- **HoD workspace (NDS-DES-02):** add **Create need** in the header when the head has an eligible create target, and a **My needs** region for the head's own Needs. This is the same composition as the dual-role variant NDS-DES-02-DUAL-ROLE.
- **Editor (NDS-DES-03, 04, 08, 15) for a head:** the primary action is **Submit and accept for planning**, with this consequence beside it: **As head of this department, submitting accepts this requirement for departmental procurement planning. It does not approve spending or start procurement.** Save draft is unchanged. The department selector lists the head's OU subtree.
- **Update editor for a head:** **Submit and accept changes**, consequence: **This replaces the accepted requirement for new planning. Existing plans do not change automatically.**
- **Withdrawal dialog for a head (NDS-DES-11):** primary **Withdraw need**, consequence: **This withdraws the accepted requirement unless it is still in the current annual plan.**
- **Accepted detail:** no change. The Done line shows the head as the acceptor.

### A6. Errors (§9)

No new codes. The `NDS_MAKER_CHECKER` explanation applies to Authors only. When a head's submission fails an acceptance check, nothing is saved as Submitted: the Draft stays editable and the actual failure is shown.

### A7. Seeds (§14)

Add an isolated profile **NDS-SC-HOD-OWN**: Dr Peter Kimani, as Head of User Department for HRMD, creates and submits an HRMD Need, which is accepted on submission. The title, facts, estimate and instant are **Awaiting fixture** and are supplied by the owner; do not invent them. The canonical four Needs and their chronology do not change.

### A8. Acceptance criteria (§15.7, new)

| ID | Required result |
|---|---|
| NDS18-AC-001 | A head with no Author assignment can create, save and submit a Need for an OU in their subtree, and is refused for a sibling OU. |
| NDS18-AC-002 | A head's submission produces one accepted revision, two decision records under the HoD assignment, one `.v3` event and no review task or review notification, atomically and idempotently. |
| NDS18-AC-003 | A head's submission that fails any acceptance or intake check leaves an editable Draft, with no Submitted or Accepted state and no event. |
| NDS18-AC-004 | An Author's submission still creates a review task, and the Author cannot decide it, including an Author who is head of a different OU. |
| NDS18-AC-005 | A head's update is accepted on submission and supersedes the earlier revision with lineage. A head's withdrawal approves only after an all-revision clear Planning result, and otherwise waits for clearance. |
| NDS18-AC-006 | An acting head has these rights only inside their dated assignment period and OU. |
| NDS18-AC-007 | The dead-end matrix covers the head's own Need: there is no state where anyone waits for themselves, and no "waiting for another head" answer. |

### A9. Documents and records to update with v1.18

- **Withdrawn from v1.17:** the §5.5 maker row and the §6 "HoD grants no creation rights" sentence. Keep both as v1.17 wording beside the correction.
- **Change register:** add six rows, NDS18-CHG-001 to 006.
- **Dependencies:** NDS18-XD-001 (PLN, Part B); NDS18-XD-002 (AUTH-ADR-001: the HoD create right is a business-role change, so check the registry entry and its `sod_tags`); NDS18-XD-003 (artboards: regenerate NDS-DES-02, 03, 04, 08, 11 and 15 for the head variants).

## Part B: PLN-CHG-001 and the NDS producer side

### B1. Planner work item for a blocked withdrawal (D3)

| Field | Requirement |
|---|---|
| Trigger | An accepted Need's withdrawal request enters **Awaiting planning clearance**, whether through a head's decision or R5. |
| Holder | Procurement Planner (site-wide). |
| My Work item | **Withdrawal requested for {need title} — decide whether the annual plan keeps it.** Show the department, the withdrawal reason and the annual plan item. Action: **View annual plan item**. |
| Clears when | The withdrawal request is approved or declined, or Planning's governed plan change removes every Active inclusion of the Need. |
| Does not | Create a Planning approval, change the plan, or approve the withdrawal. |

### B2. Contract

Planning must not read NDS tables (NDS §3), so NDS publishes the trigger.

- **Producer (NDS):** a new outbox event `NeedWithdrawalClearanceRequested.v1`, sent when a request enters Awaiting planning clearance. Fields: event ID, Need ID and reference, title, OU, pinned accepted revision ID, withdrawal request ID, reason, requested-by, instant.
- **Producer (NDS):** a new outbox event `NeedWithdrawalRequestClosed.v1`, sent on approve or decline. Fields: event ID, withdrawal request ID, outcome, actor, instant.
- **Consumer (Planning):** projects both events into the item above through `kt_my_work_providers`. It is idempotent, ordered per Need and clears on close. The event names are proposals until both documents approve them.

### B3. Updates needed in each document

- **NDS-CHG-001 v1.18:**
  - §7.6, row "`decide_accepted_need_withdrawal`, blocked for clearance": change "None in Departmental Needs" to "Planning item per PLN-CHG-001 (B1)", and keep the old wording beside it.
  - §5.5: the Planner's existing "Your turn" stays.
  - §7.1A: add the two events.
- **PLN-CHG-001 (next version):**
  - add the hand-off row to its hand-off register (cited by NDS as PLN v1.28 §7.7);
  - add the consumer contract and the My Work provider;
  - add acceptance criteria for the item appearing, its content, clearing on approve, decline or plan removal, and no item for an unblocked withdrawal.
- **No Planning change for D1:** a head's accepted Need reaches Planning as an ordinary `DepartmentalNeedAccepted.v3`.

## Part C: Code

1. **Authorisation.** Grant Need create, edit, submit and withdraw to an active Head of User Department assignment over the OU, through the AUTH resolver. Use no Frappe User Permission and no new role.
2. **`submit_need_revision`.** Add the head branch from A3, with one transaction, one idempotency identity and no review task. Reuse the acceptance service; do not duplicate its checks.
3. **`request_accepted_need_withdrawal`.** Add the head branch from R5, using the existing §8.3 Planning validator.
4. **Next step and journey service.** Implement A4, and remove the "another head" answer for the head's own Need.
5. **Vue screens.** Implement A5: the HoD workspace Create need and My needs, and the head labels and consequence text on the editor, update and withdrawal screens.
6. **Outbox.** Add the two B2 events, and publish them only after commit.
7. **Planning.** Add the B2 consumer and the B1 My Work provider; clear the item on close or plan removal.
8. **Tests.**
   - NDS18-AC-001 to 007.
   - Extend `departmental_needs/tests/test_departmental_needs_dead_end_matrix.py` for the head's own Need.
   - Regression that an Author's submission still routes to a head.
   - Planning item appear and clear tests.
   - Replay and duplicate-event tests for B2.
9. **Seed.** Add the NDS-SC-HOD-OWN profile once the owner supplies its values.

## Already done

- **Departmental Needs module guide:** updated for D1 to D3.
- **Overview note:** corrected for estimated cost, optional Needs and D1/D2.