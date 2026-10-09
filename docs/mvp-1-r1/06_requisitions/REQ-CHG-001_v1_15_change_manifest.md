# REQ-CHG-001 v1.15 — change manifest (draft for owner agreement)

Status: non-normative implementation support (the requirements live only in the REQ specification). v1.15 has been written from this manifest as `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_15.md` (now Approved, 9 October 2026; see §11). The change report is at the end of this file. Owner directions of 9 October 2026 are recorded below. Baseline: `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_14.md` (Approved 3 October 2026; register KT-DOC-CTRL-001 entry REQ-CHG-001 agrees on version 1.14 and approval date 2026-10-03).
Output (when agreed): `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_15.md`, produced by `apply_edits.py` from v1.14; v1.14 stays unchanged.

## Version impact
Domain change. Version 1.15; Status **Proposed — v1.14 was Approved; re-approval required**; Approved on **Not yet approved**; Approval record **None for v1.15**, with the v1.14 record retained. v1.14 remains the controlling approved version until the owner approves.

## Scope (one concern)
"Enter items once, derive the rest" for the Goods requisition, as scoped by the Project Owner on 9 October 2026 (quoted in §22.1 of v1.15). Two v1.14 rules are proposed for reversal. One v1.14 rule the handover proposed to reverse is **retained**. Automatic estimation is a documented **deferral**.

| # | v1.14 rule | v1.15 treatment |
|---|---|---|
| PD-1 | Requested quantity and value default to the full remaining balance (§13.4 lines 1123-1128, §14.1 line 1408, §14.3 line 1468, REQ19-AC-051) | **Proposed reversal.** Items entered by the requester determine coverage. No full-amount default. |
| PD-2 | Item quantities must equal each line's requested quantity (§5.6 lines 275-276, §10.2 line 797, §13.5, REQ19-AC-008/048) | **Proposed reversal.** Item rows are the only quantity entry; each line's requested quantity is derived as the sum of its item quantities and is bounded by the line's remaining quantity. |
| Retained | No automatic proportional repricing (§5.14 line 406); no rounding or epsilon (§5.14 line 397) | **Retained verbatim.** Estimated total is entered once per approved source allocation and validated on the server against remaining value. |
| Deferral | — | Automatic cost prefill (rate source, applicable costs, rounding rule) is deferred for MVP 1 and not specified. |

## Change manifest

| Section (v1.14 lines) | Operation | What changes | Source basis | New content? |
|---|---|---|---|---|
| Header, control table (1-26) | Insert/replace | Version 1.15; Date 9 October 2026; Status/Approved on/Approval record per above; new "Change type (v1.15)" row; v1.14 change type becomes "(retained)"; Supersession row extended; header paragraph added stating v1.15 is proposed and the v1.14 controlling-approval paragraph is retained | Protocol Step 3 | Date only |
| §1.1 (36-47) | Insert rows | Two rows: full-amount default → items determine coverage; typed requested quantity → derived | Owner scoping; handover | Wording |
| §2 (55), §2.1 (82-93) | Replace/insert | "state the exact quantity and value" → "enter items; state an estimated total per source"; add deferral of automatic estimation to the not-supported list | Owner scoping | Wording |
| §3 (115-116) | Replace | Ownership rows for requested drawdown and equipment items | Owner scoping | Wording |
| §5.1 (175-177) | Insert | Clarification only: the open slot stays held after authorisation until handoff consumption or revoke; remainder is requisitionable afterwards. No rule change. | v1.14 line 175 | Clarification |
| §5.3 (214-215) | Replace | `requested_quantity` derived (sum of item quantities for the line, 0 at start); `requested_value` is the entered estimated total per source allocation, blank at start; both bounded by remaining | PD-1, PD-2 | Wording |
| §5.6 (264, 275-276) | Replace | Quantity entered only on the item; bounded check replaces equality; shared-details capture unchanged | PD-2 | Wording |
| §5.14 (397-406) | Insert after 406 | Statement that line 406 and the no-rounding rule are retained and automatic estimation is deferred | Owner scoping | Wording |
| New §5B (after §5A) | Insert | Template boundary: common frame is category-neutral; the Goods item-quantity rule belongs to the Goods template; Works/Services scope structures are not specified here; unsupported category explained before a Draft exists (existing §5A test 1) | Handover | **New section number** |
| §6.1 (442), §6.5 (516-517, 526) | Replace | Completion rules: item quantities within limit; every line with items has a valid estimate; blocking finding wording | PD-1, PD-2 | Wording |
| §7.2 (566-582) | Insert | Frozen evidence: at submission the exact item rows, derived line quantities and entered estimates are frozen under the existing content digest; authorisation, Planning drawdown and Budget reservation use that frozen content, never a recalculation | v1.14 §5.2 `content_digest`, §9.1A | Clarification |
| §7.3A (595-597) | Insert | Deriving totals never widens edit rights; an author edits only own department's item rows and estimate; lead Head certifies all | v1.14 header line 5 | Clarification |
| §7.5 (644-645) | Replace | Invariants 4 and 5 reworded to bounded-by-remaining and derived-from-items | PD-1, PD-2 | Wording |
| §9.1A (702) | Insert | Reservation amount per line equals that line's frozen `requested_value` | Code and spec agree (authorise path) | Clarification |
| §10.2 (796-799) | Replace | `SaveRequisitionSummary` saves header fields and per-source estimated total only; item commands recompute the line's derived quantity; `AddSameSpecificationItems` takes an item quantity per source | PD-2 | Wording |
| §11 (834) | Insert rows | Retain `REQ_QUANTITY_MISMATCH` as v1.14 history; add two codes for item quantity above the line limit and for estimate outside the allowance | Reuse rule: no existing code fits | **Two new error codes (names to be agreed)** |
| §12.1 (880-884) | Replace/insert | "Amounts requested from the approved plan" replaced by **Request summary**; new **Items** section label; rule that wording names a product only inside the chosen category | Handover | Wording |
| §13.1 (947-983) | Insert | Isolated example "20 Each, category Printer" for acceptance test 1; existing fixture rows unchanged | Handover | **New fixture values (20 printers; amount to be agreed)** |
| §13.4 REQ-DES-03 (1106-1135) | Replace | Request details → **Items** (Add item) → **Request summary** (available quantity, requested quantity, estimated total, allowance remaining) → Continue saves and validates the whole draft; footer hint reworded; contributor variant keeps own-department-only | PD-1, PD-2 | Wording |
| §13.5 REQ-DES-04 (1137-1157) | Replace | "Add laptop request" becomes neutral **Add item**; quantity per item per source; default category not Laptop; opens from the current on-screen draft | PD-2 | Wording |
| §13.7 (1207-1208), §13.13 (1367), §13.14 (1381-1382) | Replace | Review summaries, save-validation message naming the real limit, design inventory | PD-2 | Wording |
| §14.1 (1408-1412), §14.3 (1459-1468) | Replace | Remove "Use full available amount"; control map for Add item; item editor opens from current on-screen draft; unsaved changes kept | PD-1, PD-2 | Wording |
| §15 (1506-1526) | Insert bullet | Audit of entered estimate and derived quantity recomputation | Existing "old and new values" rule | Wording |
| §16.4A (1634-1648) | Insert rows | Two isolated profiles (items-entered-once; item over limit) | Acceptance tests 1, 4 | **Two profile IDs** |
| §17 (1668-1785) | Mark + insert | REQ19-AC-008, AC-048 (equality part) and AC-051 marked "superseded by REQ115-AC-…, retained as history"; new §17.5 `REQ115-AC-001..009` mapped to handover tests 1-9; test 5 recorded as deferred | Handover tests | **New criteria IDs** |
| §18 (1839, 1851-1909) | Insert | Pure-test layer wording; new smoke REQ-SMK-16 | Handover | **New smoke ID** |
| §19 (1942-1952) | Insert bullet | Goods rule located in Goods template only | Handover | Wording |
| §20 (1954-1960) | Insert bullets | Submitted and authorised Versions read unchanged; in-flight Drafts keep stored values until edited (owner decision D3) | Handover; D3 | Wording |
| §22.1 (1970-1984) | Insert rows | Handover document and the Project Owner direction of 9 October 2026, quoted | Owner answers | Quotation |
| §22.2 (1992-2057) | Insert rows | `REQ115-CHG-001..` one per change above | Protocol | **New change IDs** |
| §22.3 (2061-2078) | Insert rows | `REQ115-XD-…`: Tender Preparation/Budget/Planning consumers unchanged-handoff check; seeds; artboards | Code survey | **New dependency IDs** |
| §23 (2082-2098) | Insert and renumber | New §23.1 v1.15 approval effect (proposed, conditional); existing subsections renumbered, text kept | Protocol | Wording |

Not changed: §4, §5.2, §5.4-5.5, §5.7-5.13, §5A, §6.2-6.4, §7.1, §7.3, §7.4-7.4B, §8, §9.1, §9.1B-9.3, §10.1, §12 routes, §13.2, §13.3, §13.6, §13.8-13.12, §14.2, §14.4-14.6, §16.1-16.3, §16.5, §18.3-18.4, §21.

## Owner directions received (Project Owner, 9 October 2026, in this session)
These are the owner's directions for the proposed text. They shape the proposal; they are not an approval of v1.15.
- **D1 — source with no items and no estimate:** omit a wholly unused source from the submitted snapshot; require at least one valid source; a source with items but no estimate, or an estimate but no items, is incomplete and blocks submission with a clear correction message; draft history is preserved.
- **D2 — lead department before estimates exist:** keep the existing start-time lead and the established selection rule. Where the rule depends on estimates, apply it once valid estimates exist and freeze the result at submission. No new routing rule.
- **D3 — Drafts created under the full-amount default:** preserve entered data, do not erase it, and do not treat the old defaults as confirmed intent. The requester must review quantities and estimated amounts under the corrected workflow before submission. (Implementation needs a marker or derivation that says "not yet reviewed under v1.15"; the spec will state the behaviour, and the field-purpose rule §2.2 applies to any field added. New content, to be justified when drafted.)
- **D4 — error codes:** add distinct codes for quantity exceeding availability and for estimated value exceeding allowance; existing code meanings stay stable (`REQ_QUANTITY_MISMATCH` unchanged, kept as history). Messages name the affected source, the requested amount and the actual limit. Code names are new content for the owner to review.
- **D5 — amendment record:** change rows inside the canonical specification (§22.2) and updates to the existing registers. This manifest and the change report support implementation only; they are non-normative and not a document users must consult.

Further owner directions:
- **Remainder rule:** Tender Preparation consuming the handoff may release the one-open slot; it must not restore quantity or money already authorised. The next requisition uses only the remaining allowance. Revocation follows the existing reversal rules. To be verified by test: partial requisition → authorisation → Tender handoff → second requisition for the remainder.
- **Downstream contracts:** KT-STD, PLN, BUD and TPR must be read before the change is finalised; "v1.15 does not change them" is a conclusion to establish (read in progress; results go in the change report).
- **Approval metadata:** report the contradictory v1.14 approval metadata separately; correct it only against an actual approval record; never infer approval.
- **Deferred:** automatic estimation and any new rounding rule.

## Downstream contract review (read this session; quotes verified against the files)
Versions used: PLN-CHG-001 v1.29 (Approved 3 Oct 2026; v1.30 and v1.31 are Proposed and carry identical requisition-contract rows), BUD-CHG-001 v1.12 (Approved 3 Oct 2026, newest), TPR-CHG-001 v0.17 (Approved 3 Oct 2026, newest), KT-STD-001 v1.27 (Approved 8 Oct 2026).

Confirmed compatible (no change to PLN, BUD or TPR text needed):
- Partial and sequential draws are allowed: PLN v1.29 line 608 "This rule does not cancel the existing allowance or prohibit otherwise eligible sequential drawdowns within its original scope"; BUD v1.12 line 184 `original_amount` "may be less than the original Plan allocation".
- Planning and Budget take the exact figures REQ supplies and prefill nothing: PLN line 977 "positive per-source quantity/value"; BUD line 184 "Required and positive"; BUD-BR-011 one reservation per drawn line.
- Excess decimals are rejected, never rounded (PLN lines 141, 1115; BUD lines 234-236, 1227), which matches the owner's deferral of any rounding rule.
- Consumption does not restore allowance or funds: PLN line 612 and BUD line 437 ("No Budget release shortcut … Planning scope lock does not disappear merely because funding is later released"). PLN and TPR are silent on slot release at consumption; REQ v1.14 lines 175, 177 and 746 already own it.
- TPR reads only the inherited snapshot (items with quantity, unit, delivery; reservation and source identities as lineage); it never names `drawdown_lines`, `requested_quantity` or `requested_value`, and reports only the actual invitation date to Planning.

Needs explicit wording in v1.15 (coordinated notes; the other documents are not edited here):
1. **Omitted sources vs "complete" array.** BUD-BR-010 (line 292) "A reservation request covers the complete current source-allocation set for the drawing record" and BUD line 1566 "Do not permit partial REQ all-source reservation". v1.15 states that the complete array is the frozen snapshot's retained sources, and that omitting an unused source is a snapshot rule, not a partial reservation. Coordinated note to BUD.
2. **Positive-only amounts.** PLN lines 282 and 977 and BUD line 184 allow only positive quantity and value per listed source. v1.15 therefore blocks a source with items but no estimate, or an estimate but no items (owner D1).
3. **Contributing departments in the snapshot.** TPR line 7 exposes "certified lead and contributing OU identifiers from the exact consumed REQ Version". v1.15 states that a Version's contributing departments are those of its retained sources, while the root's immutable eligibility list is unchanged. Coordinated note to TPR.
4. **Slot release at consumption** calls neither `ReverseRequisitionDrawdown` nor `release_reservation`. Stated in REQ; compatible with PLN and BUD.
5. **Quantity precision.** PLN line 142 and BUD line 237 make quantity a decimal string at governed unit precision; the derived sum and the limit use the same precision rule. Whole numbers remain a REQ product rule for Each (REQ v1.14 §5.14).
6. **Handoff version drift (pre-existing).** Approved REQ v1.14 (§5.12, line 754) and approved TPR v0.17 (lines 32, 1823, 2024, 2143) name handoff v1.3; the build emits v1.4 (`handoff.py:33`, REQ implementation plan D4, 24 Sep 2026). v1.15 does not change the handoff shape; it states that and reports the drift separately. Reconciling the spec text is a separate change.
7. **KT-STD-001 v1.27 has no rule** on autosave or unsaved changes, dialogs opening from on-screen state, messages naming entered value and limit, or product names in wording. These are REQ domain rules in v1.15. Rules that do apply: a blocked action's reason and recovery are shown once, in the blocked next-step block (§2.6.5, §2.9.1); field errors bind to the exact control and focus moves to the first invalid control (§3); omit blank or default facts (§2.6); no internal terms such as "handoff" or "digest" in primary labels (§2.1). REQ v1.14 cites KT-STD-001 v1.7; reconciling REQ's UI sections to v1.27 is outside this change and is reported.

Not read: STD-TPL-001 v0.10 §13.6 (goods-schedule grouping and its reconciliation of item and source quantities); the KT-STD table-pagination amendment proposal. Item rows keep their shape, so the risk is low, but this is not verified.

## Required corrections elsewhere (named, not made)
Register entry (version, filename, status, `approval_history`, which still lists v1.13 as pending predecessor); `IMPLEMENTATION_TRACKER.md`, `03_REQ_Implementation_Plan.md`, `FOLLOW_UPS.md` (still cite v1.11); design board v2 (header still says v1.11); stale Makefile `ui-req-*-gate` targets pointing at specs that do not exist.

## Pre-existing findings in v1.14 (reported, not fixed silently)
- Header says Approved but §23.1 (line 2086) still says "v1.13 is proposed"; there is no v1.14 approval-effect subsection. Per owner direction this is **reported, not corrected**: the only written sources for the 3 October 2026 approval are the document's own header, the register entry, and the OVS v0.6 version-set table and decision log (OVS tracker line 42, "Owner instruction, verbatim: 'Mark the documents as approved'"). There is no standalone approval-record file for 3 October (`KenTender_Approval_Record_2026-10-01.md` covers 1 October and does not list REQ). Whether those suffice as an actual approval record is the owner's judgement. In v1.15 the old §23.1 text is renumbered and kept as retained history; no v1.14 approval effect is written.
- Register `approval_history` for REQ still shows `proposal_status: "Project Owner review"` and a pending v1.13 predecessor.
- Handoff version drift: see downstream review item 6.
- Line 599: "and20–500 character reason" (missing space).
- No currency rounding rule exists in v1.14 (§5.14 says no rounding); the handover's "established currency rounding rule" has no source in this document.

## Read list
Read in full: REQ v1.14 (2098 lines); handover `99_other/requisitions-enhancements.md`; the document-change protocol.
Read in part (by delegated readers; key quotes re-verified by me): PLN-CHG-001 v1.29 (requisition contracts, allowance, scope lock, coverage, one-open rows; v1.30 and v1.31 compared by row), BUD-CHG-001 v1.12 (§8.3 check/reserve, idempotency, release, precision), TPR-CHG-001 v0.17 (handoff consumption, invitation event, cancellation), KT-STD-001 v1.27 (§§2.1, 2.6, 2.9.1, 3, 7, 10, 11); Baseline Register (REQ-CHG-001 entry and approval blocks); OVS v0.6 version set and tracker.
Not read: STD-TPL-001 v0.10 §13.6; KT-STD table-pagination amendment proposal; registry entries for other documents.

---

# Change report — REQ-CHG-001 v1.15 (protocol Step 5)

## 1. Files
- Input: `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_14.md` (2099 lines, unchanged).
- Output: `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_15.md` (2223 lines). Version 1.15; Status **Proposed — v1.14 was Approved; re-approval required**; not approved.
- Method: 82 anchored edits applied by `apply_edits.py`; each replaced wording is kept beside the new in a "v1.14 read:" parenthesis. Register: `successor_proposal` key added inside the REQ-CHG-001 `approval_history` block of `KenTender_Baseline_Register.yaml` (additive; no existing value changed).

## 2. Read list
See "Read list" above. Everything stated about PLN v1.29, BUD v1.12, TPR v0.17 and KT-STD-001 v1.27 comes from quotes re-verified against those files this session.

## 3. Changes by section, as made
As the manifest table, with these differences from it:
- **§23:** the v1.15 approval effect is added as **§23.1A**. The retained subsections (§23.1 to §23.3) are not renumbered, so the protocol's preservation check passes.
- **§5.12:** a short note that the handoff shape is unchanged was added (not a separate row in the manifest).
- **§11:** three rows were added: the two new codes and a note that `REQ_QUANTITY_MISMATCH` keeps its v1.14 meaning.
- **§12.1:** one wording rule and two label rows; the v1.14 label "Amounts requested from the approved plan" is kept as "v1.14 read".
- **§22.1A** (new subsection) quotes the owner's direction verbatim. **§22.1** gains one row for the downstream versions read.

## 4. Preservation result
`preservation_check.py ... --allow-control-table`: **PASS**. 2099 original lines, 2223 revised; extended in place 52; changed 1 (allowed); deleted 0.
Changed original line, verbatim, allowed as a control-table row (reason: version of the document): `| Version | 1.14 |` → `| Version | 1.15 |`.
Other control-table rows whose values changed. The checker lists them as "extended" because the revised control-table block still contains their old words in order; the Date row's own value did change from 3 October 2026 to 9 October 2026, and the checker only passes it because neighbouring rows keep the old wording. Verbatim originals:
- `| Date | 3 October 2026 |`
- `| Status | Approved — 3 October 2026 |`
- `| Approved on | 3 October 2026 |`
- `| Approval record | Project Owner: “Mark the documents as approved” — 3 October 2026 |` (retained inside the new Approval record cell)
- `| Supersession | On approval, supersedes v1.12, …` (retained inside the new cell)
- `| Change type | Targeted change required by Project Owner decision OD5 …` (kept as `| v1.14 change type (retained) | …`).

## 5. Consistency result
`consistency_check.py` (actors from KT-STD-001 v1.27, registry from the register): **0 errors**, 6 warnings, 9 info.
- Introduced by this change (2, deliberate): PLN-CHG-001 now cited at v1.29 as well as v1.25 and v1.27; BUD-CHG-001 now cited at v1.12 as well as v1.10. The new v1.15 text names the versions actually read; the older citations are v1.14 text, retained.
- Pre-existing, unchanged (4): `§15.2` unqualified in the v1.12 change-type row; KT-STD-001 cited at v1.7 and v1.8; `§3A` unqualified; `§8.3` unqualified.
- Cleared (1): v1.14's warning that the approval-effect section did not mention the current version; §23.1A now does.
- Info: other documents cited at older versions than the register's current ones (pre-existing; v1.15 does not reconcile them).
`register_check.py` on the register with v1.15: the two **R5** errors on REQ-CHG-001 (register says v1.14; file is v1.15, Proposed) are expected until the owner approves v1.15. The other 13 errors and all warnings are in other entries and were there before this change.

## 6. New content for owner review (not from a source)
- Error code names `REQ_QUANTITY_EXCEEDS_AVAILABLE`, `REQ_ESTIMATE_EXCEEDS_ALLOWANCE`.
- Identifiers: PD-1, PD-2, §5B, §22.1A, §23.1A, `REQ115-AC-001..013`, `REQ115-CHG-001..012`, `REQ115-XD-001..004`, `REQ-SMK-16`, `REQ-SC-ITEMS-ENTERED-ONCE`, `REQ-SC-OVER-LIMIT`, `REQ-SC-OMITTED-SOURCE`, `REQ-SC-CARRIED-OVER-DRAFT`, `REQ-DES-03-PARTIAL`.
- Fixture values: Office printers, Printer, 20 Each, estimate KES 3,000,000.00, 100 Each and KES 20,000,000.00 available, leaving 80 Each and KES 17,000,000.00 (arithmetic checked).
- Wording: labels **Items**, **Add item**, **Request summary**, **Estimated total cost**, **Still available after this request**; hint **Add at least one item and enter its estimated total cost.**; message **Digital Health can request at most 150 Each for this requirement; you entered 160.** (Digital Health, 150 and 160 are illustrative values from the existing fixture).
- Rules written to make the owner's direction testable: the screen never shows as saved a value the saved Draft does not hold; the item dialog opens from the current on-screen draft; slot release on consumption calls neither the Planning reversal nor the Budget release; a Version's contributing departments are its retained sources' departments.
- The review-required indicator for carried-over Drafts (§20) and its justification under §2.2.
- The delivery-location rule in §13.5: the dialog starts from the request's values, and a location chosen in the dialog when the request has none also sets the request's location (see "Delivery-location finding" below).

## 7. Decisions needed (all answered on 9 October 2026: “Approved with all recommendations”; see §11)
1. **Approval of v1.15,** including the two proposed reversals PD-1 and PD-2. Nothing in the code reverses them until you approve.
2. **Lead department at start (D2).** I wrote that, with no estimate yet, the established rule is applied to the lines' remaining values, because that is what the v1.14 default produced (and what the start preview computes today). Please confirm that is the "existing start-time lead" you meant. If a lead department's own source is omitted at submission, the lead is re-derived from the retained lines.
3. **Error code names** (new content above).
4. **§23 numbering.** I used 23.1A to avoid renumbering retained subsections; say if you prefer a renumbered §23 and I will allow it explicitly in the preservation check.
5. **One delivery location.** The rule added to §13.5 (a location chosen in the dialog also sets the request's location when it has none) is a proposal that makes "enter each fact once" true for the delivery location. Confirm it, or tell me the dialog should not offer a location at all.

## 8. Required corrections elsewhere (named, not made)
- Register: `approval_history` values for REQ still read as a v1.14 proposal with a pending v1.13 predecessor; correct only against an actual approval record. The companion workbook `KenTender_Documentation_Control_Register.xlsx` is not updated (the register file says it is generated from the YAML; no spreadsheet library is installed here).
- REQ trackers and plan (`IMPLEMENTATION_TRACKER.md`, `03_REQ_Implementation_Plan.md`, `FOLLOW_UPS.md`) cite v1.11; the design board v2 header cites v1.11.
- BUD-CHG-001 v1.12: confirm that "complete current source-allocation set for the drawing record" and "partial REQ all-source reservation" mean the retained sources of the frozen Version.
- TPR-CHG-001 v0.17: confirm contributing departments are read from the consumed Version's retained sources; handoff version label (v1.3 in approved REQ and TPR text; v1.4 in the build).
- REQ cites KT-STD-001 v1.7; reconciling REQ's UI sections to v1.27 is separate work.

## 9. Not verified
- STD-TPL-001 v0.10 §13.6 (goods-schedule grouping) and the KT-STD table-pagination amendment proposal were not read.
- No code, test, seed or UI was run for this document change; every statement about code behaviour comes from the explorers' reading of the current repository and has not been exercised.
- Whether the three written sources for the 3 October approval (document header, register entry, OVS version-set table and decision log) are an adequate approval record is the owner's judgement; no approval was inferred.
- The companion `.xlsx` register and the other registry entries were not read.

## 10. Verification run alongside the document (Stage 1C; test site `kentender-test.local` only)

**Remainder rule, with a real Tender start.** New test `kentender_procurement/tenders/tests/test_partial_requisition_remainder.py` (one test). It authorises a Requisition for 40% of a 250 Each, KES 50,000,000.00 item through the real commands, starts a real Tender from the handoff, then proves: the open slot is held until the Tender starts; a second Prepare before that returns the existing Requisition; after the Tender starts the slot is released while the Planning drawdown, the Budget reservations (one per line, equal to the authorised amounts) and the scope lock are unchanged; revocation is refused with `REQ_HANDOFF_CONSUMED`; the second Draft is offered exactly the remainder (first draw plus remainder equals the original quantity and value); and a quantity above the remainder is refused with `REQ_BALANCE_CHANGED`. **Result: 1 test, passed.** It describes behaviour that already holds under v1.14; it is not a red test, and it needed no code change. It also leaves no rows behind (all remaining reservations and requisitions on the test site are the seeded world, dated 2027).
- Fixture change: `confirmed_item` and `active_item` in `procurement_requisitions/tests/fixtures.py` take an optional `quantity` (default 1, so no existing caller changes).
- Regression run of `procurement_requisitions.tests.test_draft_commands`: 17 passed, 1 failed. The failure is `test_creates_one_draft_with_exact_default_amounts_and_no_budget_or_planning_effect` (`14 != 0` on its count of Budget reservations from Requisitions). Those 14 are the seeded demo world copied from dev onto the test site (namespace `KENTENDER_MVP_1_R1_REQ`), so the assertion fails on any seeded site. It predates this work; I did not fix it.
- Not run: the wider Requisitions, Budget, Planning and Tenders modules; vitest; the structure and fidelity gates; browser walks. No application behaviour was changed, so none of those is affected by what was done.

**Delivery-location finding (handover item 5).** Diagnosed from the code, not yet reproduced in a browser. The delivery location has two entry points: the page's request field and a separate select inside the item dialog. The dialog starts from the saved request value (`AddLaptopDialog.vue:86`), so when the request has none it starts empty. A location chosen in the dialog is stored on the items only (`draft_commands.py:298-306, 415-417`), the equipment table shows the item's location (`presenters.py:173-184`), and the footer checks only the request's saved location (`validation.py:161-162`). So the table shows a location while the footer says "Select the delivery location." A second route to the same symptom is a location picked on the page but not yet saved, because the footer hint always refers to the saved Draft (`RequestDetailsTask.vue:263-274, 307-308`). v1.15 §13.5 and §14.3 now address both; the fix itself is Stage 2 work, and no code was changed for it.

## 11. Approval step (9 October 2026)

**Instruction (verbatim, Project Owner):** “Approved with all recommendations”, given in answer to the five decisions put with v1.15: approval of v1.15 including PD-1 and PD-2; the start-time lead basis; the two error code names; the §23.1A numbering; the delivery-location rule.

**Changed in v1.15 by the approval (everything else is unchanged from the proposed text, shown by diff):**
- Control table: Status (`Approved — 9 October 2026`), Approved on, Approval record (the instruction quoted above, with the v1.14 record retained), and Supersession (v1.14 is now retained as historical evidence).
- Approval-state wording that would otherwise have contradicted the control table: the v1.15 header paragraph; the two §1.1 rows (“Decision PD-1/PD-2, approved by the Project Owner on 9 October 2026”, replacing “Proposed decision … not approved”); the §17.5 heading and its introduction; one word in the §22.2 count sentence (“Proposed v1.15” became “v1.15”); the §22.1A introduction; and the §23.1A heading and first sentence (now declarative).
- Not changed: any requirement, rule, identifier, error code or acceptance criterion.

**Checks after approval:** preservation against v1.14 PASS (one allowed control-table line changed, 52 extended, none lost); consistency 0 errors, the same 6 warnings as before; register check — the two REQ-CHG-001 errors are gone (register now says v1.15, Approved, 2026-10-09, matching the file); the 13 remaining errors and the warnings belong to other entries and were there before.

**Register:** `KenTender_Baseline_Register.yaml` REQ-CHG-001 entry now reads version 1.15, `Approved requirement`, approval date 2026-10-09, filename v1_15, `source_sha256` of the file, `prior_approved_baseline` v1.14 (2026-10-03), approval record quoted, `library_file_id` blank (no library upload exists for v1.15). `implementation_status`, `verification_status` and `release_status` are unchanged: approval is not evidence of any of them. The stale v1.14/v1.13 values in `approval_history` are left as they were.

**Not updated:** the companion workbook `KenTender_Documentation_Control_Register.xlsx` was already behind the register for seven documents (REQ-CHG-001, CFG-CHG-002, KT-STD-001, AUTH-ADR-001, SEED-OPS-001, PRC-CHG-001, EVL-CHG-001); it needs one bulk sync, not a one-row edit. Other register entries (PLN-CHG-001, STD-TPL-001 and several decisions and delivery items) still cite REQ v1.12; they were stale before and are not edited here.

## 12. Build evidence (9 October 2026; test site `kentender-test.local` only; dev not touched)

**What was built.** Backend: `services/goods_template.py` (the Goods item-quantity rule, §5B); `draft_commands.py` (nothing defaulted at Prepare; estimates saved per source and bounded; item add/edit/remove bounded and deriving the line quantity; a location chosen in the dialog also sets the request's); `validation.py` (incomplete-source and review-required findings; no mismatch check; neutral hint); `lifecycle.py` (omit unused sources at lock and restore them in a copied Draft; lead re-derived from the retained lines); `records.py` (lead falls back to remaining values until estimates exist); `handoff.py` (contributing departments are the retained sources'); `read.py`/`presenters.py` (derived quantities, estimate, still-available, summary block, neutral labels); `errors.py` (two codes); Requisition Version doctype (two header fields, not in the digest) and patch `req_chg_001_v115_review_carried_over_drafts`. Seeds and Playwright fixtures build through the new commands. UI: `RequestDetailsTask.vue`, `AddItemDialog.vue` (renamed from `AddLaptopDialog.vue`), `EditItemDialog.vue`, `ReviewSections.vue`, `RequirementsTask.vue`, `requisitionsApi.js`; design board v2 and the fidelity registries.

**Interpretation to confirm (lead department).** The spec says the established rule applies "once valid estimated total costs exist". Implemented: while Drafting, the lead is re-derived only when every source line has an estimate (otherwise a department that typed first would take the lead and the original lead would lose its routing rights); submission always re-derives it from the retained lines and freezes it. At start it uses the lines' remaining values.

**Results (all observed this session).**
- New Python tests: `procurement_requisitions/tests/test_items_entered_once.py` 16 of 16 pass; `tenders/tests/test_partial_requisition_remainder.py` 1 of 1 passes (partial requisition → authorised → real Tender start → second requisition takes only the remainder). These were written after the code, not strictly red-first; the older tests that encoded the retired behaviour were rewritten (draft commands, validation, schema allow-list, lifecycle, maker-checker, API journey, authorisation and My Work sequences).
- Full Requisitions Python suite: 29 modules, 319 tests, 316 pass, 3 fail. The three are `test_draft_commands` and `test_read` (both count Budget reservations from Requisitions and expect 0; the 14 seeded demo reservations make them fail on this site) and `test_ovs_requisition_reads` (the Accounting Officer's list pages past the 2027-dated seed rows). All three predate this change; no baseline run was possible, so this is by reading the assertions.
- Downstream (25 Tenders modules and 2 Evaluation modules): all pass except `tenders.tests.test_read` (3 failures: workspace counts of 2 where 1 is expected) and `bid_evaluation.tests.test_home_provider` (2: an outsider has an oversight region). Both fail when run alone; they concern Tenders and Evaluation counts and regions, not requisitions, and are probably the seeded world, but this is **not baseline-verified**.
- Vitest: Requisitions project 128 of 128; design-fidelity project 49 of 50 (the failure is in `departures/procurement-planning.js`, a file with no uncommitted change).
- Browser (test site): request-details spec 6 of 6 (including a new phone-width test); decisions and requirements-review 11 of 11; workspace-start 6 of 6 with its one forbidden-wording check excluded; design-fidelity gate `ui-req-fidelity-gate` 5 of 5, run twice. Failing in specs this change did not touch: `requisitions-evidence-pack` (calls `reset_editor_review_fixture`, which does not exist at HEAD), `requisitions-release-evidence` (expects the legacy seeded MOH world; 1 failed, 3 not run) and the "no responsibility" wording check in `requisitions-workspace-start` (identical at HEAD).
- Canonical seed: `make seed-canonical SITE=kentender-test.local REBUILD=True` finished with `validate: ok, failures: []` and no tracebacks; the demo requisitions were created through the new commands.
- Assets rebuilt with `./scripts/bench-with-node.sh build --app kentender_procurement`; the bundle hash changed and carries the v1.15 strings.

**Not done / not verified.** Not run on the dev site: migration (two new Version columns), the review patch, any reseed. The dev site already runs the new Python and the rebuilt JavaScript, so Requisitions on dev will error on save until `bench --site kentender.midas.com migrate` is run. No Playwright spec exists for a carried-over Draft (a vitest case and a Python test cover it). The Tenders handoff version label (v1.3 in approved REQ/TPR text, v1.4 emitted) is unchanged. The companion workbook and the other register entries are as reported in §11. STD-TPL-001 v0.10 §13.6 was not read.

## 13. v1.16 (proposed 9 October 2026) and an open finding

**v1.16 — dialog action wording.** On the Project Owner's direction ("Do it", 9 October 2026, §22.1B of v1.16) the item dialog's action reads "Add item" and "Add N items" instead of "Add equipment row" and "Add 2 equipment rows", because that wording sits in the common frame and a Services template could not keep it. New file `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_16.md`, built from v1.15 by 13 anchored edits (§§13.5, 14.1, 22.1B, 22.2 row REQ116-CHG-001, 23.1B and the control table). **Status: Approved by the Project Owner on 9 October 2026 ("v1.16 is approved"); the register now carries v1.16 as the approved version with v1.15 as the prior baseline. Preservation PASS; consistency 0 errors; the register check has no REQ errors.** Preservation PASS (1 allowed control-table line); consistency 0 errors. The code, design board v2, component test and browser spec already use the new wording (vitest 139/139; request-details browser spec 7/7; fidelity gate 5/5), so the product and the approved text now agree.

**Open finding — requests that mix categories (not fixed).** A request with laptops and monitors gets the generic starting proposal (`IT-EQUIPMENT-CATALOGUE-V1`) with every row scoped to "All items". Applying it is refused with `REQ_CONTROL_INVALID: Storage type does not apply to Monitor equipment.` (observed with a probe test). A row scoped to a single item is accepted, so the requester can work around it by hand, but the proposal does not do it. The proposal logic (`catalogue.proposal_for`, `draft_commands._generate_proposal`) is unchanged by v1.15; the spec (§6.3, §6.4) describes one category per proposal. Needs a spec decision (suggested: propose each category's rows scoped to that category's items; keep the acceptance checks on all items; give the requirements screen one group per category) and should be its own version.

## 14. The segmented control, fixed once for every module (9 October 2026)

**Cause (a shared stylesheet defect, found after it had been fixed in one module).** The Yes/No control had four definitions. The design pack's `.seg` / `.seg-opt` was correct. A legacy `.kt-seg.kt-seg-inline` variant sat on top of the old colour-swatch bar's `height: 12px; overflow: hidden`, so every screen using it had clipped labels: Requisitions, Bid Evaluation and the System Setup "Assign" dialog. `kt_admin_configuration.css` overrode `.seg-opt` for the whole site (every app stylesheet is loaded globally). Tenders and Planning each kept their own copy (`tnd-seg`, `pln-seg`). The System Setup board itself draws `class="seg"`, so the board, the pack and the generator agreed and the code did not.

**Fix.** One definition, the pack's. The generator source `scripts/industry_old_stylesheet.css` lost the legacy block; `scripts/industry_design_css.py` gained the three things screens needed beyond the pack (a track that does not stretch, no label margin, a readable disabled option); `kt_industry_tokens.css` was regenerated (`--check` passes; 74 changed lines, all the legacy block and the additions). The admin-configuration override and the Tenders and Planning copies were deleted. EvlBoard, AssignDialog, SegYesNo, Tenders (3 files) and Planning (1 file) now use `seg` / `seg-opt`.

**Guards.** New `kentender_core/tests/test_one_segmented_control.py` (3 tests) fails if the shared stylesheet loses the control or regains a legacy variant, if any other stylesheet defines a segmented control, or if any screen uses a legacy or module-named copy. While running the existing design guards, three more existing defects surfaced and were fixed: a `kt-btn kt-btn-secondary` link in `templates/kt_portal/base.html` (now `btn btn-secondary`); `test_industry_design_gate` expected `<body class=` on one line, which the portal template splits (pattern now allows it); and the gate did not know that Bid Evaluation and Bid Opening mount inside the Tenders page (they are now registered as nested mounts, and the test checks the Tenders host carries `kt-industry`).

**Results.** Design guard tests (6 modules) pass. Browser: Requisitions request-details 7/7; Tenders editor (meeting toggle) 2/2; System Setup responsibilities (Assign dialog) 6/6; Planning fidelity U08 (plan-items dialog) 5/5; Bid Evaluation ordinary path 1/1 (first attempt failed in its fixture, passed on rerun). Not run: the Tenders clarification browser spec, because its fixture sends mail and no mail server exists on this machine. Component tests: 9 failures in Analytics and Planning's COVERED registry; the committed code passes those tests in a clean checkout, and the failing files carried other sessions' uncommitted changes when this work began; not isolated further.
