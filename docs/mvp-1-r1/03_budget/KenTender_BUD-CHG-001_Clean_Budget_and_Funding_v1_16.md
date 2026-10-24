# BUD-CHG-001 — Clean Budget & Funding

**Controlling approval — 16 October 2026 (BUD-CHG-001 v1.16).** The Project Owner instructed, verbatim: **“Mark them as approved”**, following delivery of the coordinated package containing BUD v1.16, AWD v0.7, CM v0.10 and AUTH v1.16 with the two adopted product decisions incorporated. This approves **BUD-CHG-001 v1.16 in full**, including its current requirements, design specification, fixtures, interfaces and acceptance criteria. It supersedes the approved v1.12 baseline and the intervening proposal chain as incorporated and corrected in this successor; it does not create separate retrospective approvals of intermediate versions. Requisition v1.19 and KT-STD v1.30 are unchanged and receive no new approval through this record.

**Approval effect and reading rule.** The current control table and this approval govern. Earlier Proposed/pending wording, predecessor-baseline statements and draft-update records retained below are drafting history superseded for this version. Approval changes no requirement and does not establish code completion, migration, tests, legal clearance, owner-adapter verification or production readiness. Existing follow-up and evidence conditions remain open until satisfied. External guides, seed-owner files and live control registers were not supplied and are not claimed updated.

**Implementation entry point.** Read §§4.12, 8.6–8.8, 11.22, 16.8 and 19.4. Map each changed requirement to the existing follow-up ID, code location and required evidence; retain implementation-open items until their actual closure conditions pass. Review the complete changed sections and their affected dependencies; do not infer completion from this index.

**Approved product decisions — 16 October 2026.** The Project Owner replied **“Adopt”** to the recommendations that (1) the Budget Approver must be a different person from both the entry preparer and the person who confirmed that contract’s funding basis; and (2) independently onboarded contracts within the supported CM product/profile may obtain funding through one annual request per contract and target year, reusing the entry/evidence/review workflow without reopening the contract. Tender-derived purchases remain single-year. These two decisions are approved and incorporated below. The complete successor is now Approved under the controlling approval above; implementation, tests and release are not certified.

**Approved successor v1.16 — 16 October 2026.** Reconciles the supplied BUD v1.15 against REQ v1.19, AWD v0.6, CM v0.9, AUTH v1.15 and KT-STD v1.30. Adds the complete funding-operation model (§8.7), usable funding/correction screens (§11.22), precise request and entry lifecycle, and matching acceptance. Preserves single-year tender-derived procurement, one target year per funding entry, single-currency funding and Budget’s separation from accounting; adopted annual entries support independently onboarded contracts. AWD v0.7, CM v0.10 and AUTH v1.16 are the coordinated proposals. v1.12 remains approved; v1.13–1.15 proposals are carried forward only as corrected here.

**Reading rule.** The control table and the explicitly identified current successor provisions govern this proposal. Earlier version introductions, approval effects, source-status observations and change records are history for their stated versions; they neither approve this successor nor establish current implementation. No test, deployment, legal clearance or register update is claimed. The user’s “Proceed” authorises preparation for review, not automatic requirements approval.

**v1.15 proposal — 16 October 2026.** The Project Owner replied to the three open questions of v1.14 with advice and the instruction “Proceed with drafting CM v0.9 and the matching Budget amendment together.” The owner then supplied recommendations on seven open points, with the instruction “These recommendations should go into both [CM-CHG-001 v0.9] §20.7 and BUD24-XD-005, with matching workflow, controls and acceptance criteria. They remain proposed decisions until you approve them.” The owner then settled the point those recommendations left open, the Finance allocation by Budget year, with the requirement quoted in §4.12 (proposed decision 8). The owner later replaced the earlier wording, which depended on “the entity’s established Budget treatment”, with a concrete evidence requirement and no new Finance policy register or approval. The advice and the recommendations are adopted here as a proposal for the owner to confirm by approving this version. v1.15 carries v1.14 in full and makes two changes. **First**, the lineage of a conversion is verified at the first conversion as well as every later one, by the owning modules and not by whatever the caller supplies; the verified Tender, lot, Award and version and funding allocation are retained on the immutable commitment and conversion evidence, and the reservation is not changed (BUD-BR-036). Before adding any field to a reservation, the existing records were checked, and the reservation already proves its Requisition and source-allocation identity (§4.5). **Second**, it adds an explicit **existing-contract commitment entry** beside reservation conversion, for a contract that is controlled by KenTender Budget and has no reservation: Contract Management raises one request, Finance confirms the opening obligation and its allocation by Budget year, the system calculates the amount requiring funding from those confirmed figures (identifying what is already represented), a Budget Officer maps the confirmed amounts to Budget Lines and records the reconciliation to Budget, a different Budget Approver approves all rows together, and it is not a general manual commitment editor (BUD-BR-037–040). For funding controlled outside KenTender Budget, Budget creates and holds nothing. This needs the matching Contract Management version, CM-CHG-001 v0.9, proposed with it. Nothing here is approved until the Project Owner approves v1.15, and approving v1.15 approves v1.14 and v1.13 with it. v1.12 remains the approved baseline.

**v1.14 proposal — 16 October 2026 (carried in full).** Owner decisions 2 and 3, supplied to the working session on 16 October 2026 as “Decision 2: funding lineage on conversion” and “Decision 3: contracts with no tender in KenTender”, and the earlier answer “1. Yes” to the recommendation that Budget enforce by itself, refusing by default, that a contract may convert only reservations its own award names. v1.14 carries v1.13 in full. It makes decision 2 a requirement (BUD-BR-035): a conversion is valid only when the whole chain matches, and Budget checks it against references the owning modules supply in the conversion event. It records decision 3 as a **missing path** (§19.3, BUD23-XD-004): the approved text and the code that exists are cited there, and no onboarding rule is invented before the owner settles its controls. The conversion event does not carry the full chain today, so this is an interface change in Budget and in Contract Management, which needs the matching Contract Management version (named in §19.3). Nothing here is approved until the Project Owner approves v1.14, and approving v1.14 approves v1.13's content with it. v1.12 remains the approved baseline.

**v1.13 proposal — 16 October 2026 (carried in full).** Owner decision 1, supplied to the working session on 16 October 2026 as “Decision 1: closed commitments”, with the owner's answers to four open points: “Officer records, Approver approves (Recommended)”, “Yes, for a KenTender contract (Recommended)”, “Yes, decrease only (Recommended)” and “Own record, amount lowered (Recommended)”. v1.13 applies it. **Committed** counts Active and Closed commitments at their retained amounts, and closing a commitment releases no money. A Closed commitment accepts no increase and no ordinary adjustment. Its amount can be lowered only by an evidenced **correction** that a Budget Officer records and a different Budget Approver approves; the correction is its own record, the corrected amount returns to Available and never to the original reservation, and reopening the contract record in Contract Management does not reopen or change its funding. `close_commitment` (built in `kentender_budget` at commit `678fb20a`, follow-up FU-CM-59) becomes a requirement. Nothing here is approved until the Project Owner approves v1.13. v1.12 remains the approved baseline.

**Controlling approval of v1.12 — 3 October 2026 (retained).** The Project Owner instructed: “Mark the documents as approved”. This approves this version in the coordinated OVS v0.6 package, including its incorporated amendments. OVS-P01–P05 are approved. The incorporated REQ v1.13, CFG v0.17 and TPR v0.16 changes are accepted within their approved successors; this does not create separate retrospective approvals of those intermediate versions. Earlier proposed/pending wording is drafting history superseded by this record. Static design work and conformance matrices remain open; CM and the separate template walkthrough remain deferred. Approval does not establish implementation, seed execution, testing, legal clearance or production readiness.

**OVS reference and owner-specific amendment (§§7–7.1, 9.1, 11.1, 12.1).** Add OVS v0.6 §4.1 approved-allocation and funding-position reads. Department attribution must use existing owner-authorised source relationships; a shared Budget Line alone does not establish departmental ownership. Preserve BUD calculations, funding contracts, historical versus current amounts and Finance authority. No Budget Viewer role or second ledger is introduced.

Shared usability rules are owned once by **OVS-CHG-001 v0.6**, especially §§3–8 and 12–15. This module retains its domain lifecycle, facts, commands and existing authority except the explicit proposed read additions above. Implement the named changes in the cited owner surfaces; do not copy shared usability chapters into this document. This amendment takes effect under the controlling approval above.

| Control | Value |
|---|---|
| Document ID | BUD-CHG-001 |
| Version | 1.16 |
| Date | 16 October 2026 (v1.12: 3 October 2026) |
| Status | Approved — 16 October 2026; requirements and design specification. Implementation, verification and release tracked separately. |
| Approved on | 16 October 2026 |
| Approval record | Project Owner, 16 October 2026: “Mark them as approved”. Approves BUD-CHG-001 v1.16 in full with the coordinated funding package. See controlling approval above. |
| Approval basis | Retains approved BUD v1.9 and removes the obsolete service and evidence that made the approved Budget ceiling the 30% Planning denominator. Coordinated with approved PLN v1.25, CFG v0.13 and LAW v1.2. |
| v1.13 approval basis | None yet. Proposed on the owner decision quoted above. Three points the owner left to the specification are settled here as proposals for the owner to confirm: who records and who approves a correction, whether it must cite a Contract Management reference, and whether it is allowed after the Budget is Closed. |
| v1.14 approval basis | None yet. Proposed on owner decisions 2 and 3 and the answer “1. Yes”, quoted above. The build that exists for decision 2 is an interim check (BUD23-XD-002), not the requirement. |
| v1.15 approval basis | None yet. Proposed on the owner's instruction to draft quoted above. The recommendations in the owner-supplied advice (who records and who approves, the evidence, the effect on availability) are adopted as the proposal and need the owner's confirmation. The eight points the owner's recommendations settled are recorded as proposed decisions in §19.3 (BUD24-XD-005). |
| Supersedes | Approved v1.12 baseline and intervening proposals as incorporated/corrected; current v1.16 is the requirements baseline. Prior approvals and drafting history remain retained. |
| v1.14 supersession | v1.14 carries v1.13 in full, so approving v1.14 approves v1.13's content with it. v1.13 may also be approved on its own, which leaves v1.14 proposed. |
| v1.15 supersession | v1.15 carries v1.14 and v1.13 in full, so approving v1.15 approves their content with it. v1.14 or v1.13 may be approved without v1.15, which leaves v1.15 proposed. |
| Change type | Current v1.16: complete funding operations in §8.7, precise single-year/currency opening basis and Budget-only coverage, complete entry/request lifecycle, native-integration ownership, usable correction/funding screens in §11.22, current dependency disposition and BUD25-AC-001–013. Independent annual funding under §8.8 is adopted; no FX funding extension. Earlier version-specific change rows remain history. |
| v1.14 change type (retained) | Targeted successor: carries v1.13 in full and makes owner decision 2 a requirement. A conversion is valid only when the whole chain matches, plan source allocation → exact Requisition Version and drawdown → Tender, and lot where the source carries one → Award → contract, checked against references the owning modules supply in the conversion event; a matching supplier, Tender or Requisition is not enough (BUD-BR-035, §§1.1, 3, 4.6, 5, 7, 8.4, 9.1, 13, 15.8). Records owner decision 3 as a missing path and lists what must be decided (BUD23-XD-004). New BUD-BR-035, `BUDGET_RESERVATION_NOT_AUTHORISED`, BUD23-AC-001–011 and BUD23-CHG-001–002. No role, approval stage or manual financial control. All v1.13 and v1.12 content is retained. |
| v1.13 change type (retained) | Targeted successor: Committed counts Active and Closed commitments at their retained amounts, reconciled across availability, the successor floor, the omission test and the labels (§§4.6, 4.9, 5, 6, 9.4, 11); `close_commitment`, its audit event and its errors (§§7, 8.4, 9.1, 13, 14); a Closed commitment accepts no increase and no ordinary adjustment; and the **Commitment Correction** — Budget's own two-person process for lowering a Closed commitment (§§2, 4.11, 5, 7, 8.4, 9.2, 9.3, 12.8, 13, 14). New BUD-BR-031–034, a carve-out of BUD-BR-015, BUD22-AC-001–009 and BUD22-CHG-001–004. One departure from v1.12: a person now records a money movement, which v1.12 §§2, 7 and 12.8 and BUD-BR-015 excluded. It is the correction and nothing else, it can only lower an amount, and it needs two people. No new role. All v1.12 content is retained. |
| v1.12 change type (retained) | Targeted successor required by approved PLN-CHG-001 v1.27 (§§7.3, 7.7, 15.2) and approved KT-STD-001 v1.8 §12.1: adds the Budget-owned **receiving side of a Planning budget revision request** (§§1.1, 3, 4.10, 5, 6, 7, 8.5, 9, 11.1B, 11.21, 12.1, 13, 14, 15.8, 16.4, 18, 19, 20). The request is not a Budget revision: an increase still requires external approval and is registered as an ordinary successor Version. No role, approval stage, reservation behaviour or change to an existing financial rule. All v1.10 content is retained. |
| v1.10 change type (retained) | Complete narrow successor: Budget continues to own funding ceilings, affordability, financial reservations and commitments; Planning owns the eligible-current-APP reservation calculation. No business task or approval stage changes. |
| Module | Budget & Funding |
| Standards | KT-STD-001 v1.30, Approved; AUTH v1.15, Approved, with AUTH v1.16 Proposed for the CM bindings; existing CFG ownership remains unchanged. |
| Implementation posture | Requirements Proposed; no current implementation/deployment/test result asserted. The retired annual-denominator mechanism remains retired. Implement only after coordinated requirements review and verified owner-interface mapping. |

**Controlling decision:** Budget & Funding is a **record of externally allocated funds**, not a budgeting function. Appropriation, enactment, exchequer release and accounting happen in IFMIS and are outside this system. KenTender registers the externally approved procurement allocation, exposes eligible Procurement Budget Lines, and protects those amounts through reservations and commitments so that procurement cannot commit money it does not have.

**v1.11 addition.** When a Procurement Planning Draft exceeds a Budget Line's approved amount, Planning may send the Budget Officer a **budget revision request**. Budget records it and shows it as the Budget Officer's pending work. The Budget Officer answers it by seeking the external revision and registering it through the existing **Update registered allocation** successor, or by declining it with a reason. Budget reports the outcome to Planning. A request changes no amount, creates no reservation and is not itself a revision or an approval.

**v1.13 addition.** Closing a contract does not give its money back. From v1.13 **Committed** counts the retained amount of every Active **and Closed** commitment (BUD-BR-031), so a closed contract's final amount stays out of Available. `close_commitment` (§9.1) closes a commitment by status only (BUD-BR-032). A Closed commitment accepts no increase and no ordinary adjustment from the contract service (BUD-BR-033). Its amount is lowered only by a **correction**: a Budget Officer records it with a reason, evidence and a Contract Management reference, a different Budget Approver approves it, and the decrease returns to Available, never to the original reservation (BUD-BR-034, §4.11). Follow-up FU-CM-59 closes only when v1.13 is approved and the evidence in §19.3 exists, not because the commit exists.

**v1.14 addition.** A contract may consume only what its own award funds. A conversion is valid only when the whole chain matches (BUD-BR-035): the plan source allocation, the exact Requisition Version and drawdown, the Tender and, where the source carries one, the lot, the Award and the contract. A matching supplier, Tender or Requisition alone is not enough. Budget checks the chain against references the owning modules supply in the conversion event, never reads their records, and refuses when the chain does not match or is not supplied.

**v1.15 addition.** The chain is verified, not supplied. At the first conversion and every later one Budget consumes the owning module's verified answer for the Tender, the lot where the source carries one, the Award and its version and the funding allocation, compares it with what it holds on the reservation, and retains it immutably on the commitment and on the conversion event (BUD-BR-036). A contract that has no tender in KenTender is funded in one of two ways. When KenTender Budget controls the funding, an **existing-contract commitment entry** creates its commitments once, one for each allocation row, from an amount the system calculates from Finance's confirmed figures, with two different people and an atomic check of every row together (BUD-BR-037–040). When funding is controlled outside KenTender Budget, Budget creates and holds nothing; Contract Management keeps the evidence. No Tender, Requisition or reservation is ever invented for an existing contract.

It is **fully separate from ERPNext accounting**. ERPNext's own `Budget`, `Cost Center` and accounting records govern the finance function on the same site and are never read, mirrored or reconciled by this module.

---

## 1. Governing decision

This document is the single implementation authority for Budget & Funding. The existing application is corrected in place. Removed concepts are deleted rather than renamed, aliased, dual-read or retained behind feature flags.

### 1.1 Conflict and disposition register

Items disposed of in v1.2 and not reopened: the separate Allocation object; Budget Value Treatment, the treatment questionnaire and Public Value Objectives; Budget-side Strategy references; reservation at Departmental Need acceptance; the Budget-owned Finance confirmation screen; one-reservation-per-Plan-Item; the separate Budget Revision object; the Budget Reviewer / Budget Activation Authority split and the `In Review` and `Awaiting Activation` statuses; the Funding Exception object; Expenditure Snapshot and actual-expenditure data; the advanced Funding Performance dashboard; budget classification and separate purpose fields; generic source, authority, notes and evidence fields.

New in v1.15:

| Earlier item | Disposition in v1.15 |
|---|---|
| v1.14 had Budget check the chain against “references the owning modules supply in the conversion event”, and proposed that the first conversion record whatever it received so that later ones could be compared | **Refined by the owner's advice: validate the first conversion too, against authoritative source references, not whatever the first caller supplies (BUD-BR-036).** Budget consumes the owner's verified answer through a published owner contract and imports no Tender controller. |
| v1.14 said a reservation stores no requisition version and that the owners must supply one | **Corrected after checking the existing records (§4.5).** The reservation's `source_set_hash` already binds the exact Requisition Version and its drawdown lines, and its source allocation, drawdown line, Requisition reference and Budget Line are held. No new reservation field is needed. The Tender, lot, Award and version and per-conversion allocation are not held and are retained on the commitment and the conversion event. |
| A contract with no tender in KenTender had no funding path (v1.14, BUD23-XD-004, “missing”) | **Specified as a proposal:** the existing-contract commitment entry for KenTender Budget-controlled funding, and nothing in Budget for funding controlled outside it (BUD-BR-037–040, §4.12). Eight points are settled as proposed decisions in BUD24-XD-005. |
| A commitment is always created by converting a reservation and reaches its Budget Line only through it | **A commitment can also be an existing-contract entry and carries its Budget Line directly (§4.6).** Every reader of Committed must read it that way (BUD24-XD-001). |

New in v1.14:

| Earlier item | Disposition in v1.14 |
|---|---|
| `convert_reservation` checked that the caller named its own contract, that the reservation was open and that the amount fitted the remainder, but not that the contract's award was funded from the reservation (a review of 16 October 2026 found this; the safeguard lived only upstream, in how Award names the reservations and how Contract Management passes them on) | **A conversion is valid only when the whole chain matches (BUD-BR-035, owner decision 2).** Release was already scoped to the reservation the contract converted; conversion now is too. |
| The conversion event carried only the reservation, the contract, the amount, a key and the contract event | **It must carry the chain (§9.1).** This changes the interface of Budget and of Contract Management; the matching Contract Management version is named in §19.3. |
| A contract registered with no tender in KenTender had no stated relationship to Budget | **Recorded as a missing path, not specified here (BUD23-XD-004, owner decision 3).** Approval of Contract Management's independent entry does not approve any funding path. |

New in v1.13:

| Earlier item | Disposition in v1.13 |
|---|---|
| Committed counted commitments in `Active` only (§5, v1.12 read), so closing a contract could be read as freeing its money | **Count Active and Closed commitments at their retained amounts (BUD-BR-031).** Closing changes status and attribution only, and Available is unchanged. The successor floor (BUD-BR-017), the omission test (BUD-BR-020) and every reader of a line's position use the same figure. |
| `close_commitment` existed as a proposal in CM-CHG-001 v0.8 §5.14.1 and as built code | **Adopt it as a Budget requirement (§9.1, BUD-BR-032).** The built behaviour at commit `678fb20a` was an observation; this version makes it a rule. |
| A Closed commitment could be lowered by the contract service: with no evidence in the build at commit `678fb20a`, and with evidence in the first draft of this version | **Superseded by owner decision 1.** The contract service can neither raise nor lower a Closed commitment (BUD-BR-033). Only a Budget correction lowers it (BUD-BR-034). An earlier recommendation that a Closed commitment be frozen, with corrections coming only from Contract Management, is overridden by the same decision. |
| No person keys a money movement into Budget (BUD-BR-015, §2, §7, §12.8) | **One exception, the correction of a Closed commitment (BUD-BR-034).** A person records it, a different person approves it, it can only lower an amount, and it never touches a reservation. Nothing else a person does in Budget moves money. |
| Decreases after a Budget is Closed remained in the contract owner's contract, not a Budget adjustment (§12.8) | **A decrease of a Closed commitment after the Budget is Closed is a Budget correction (BUD-BR-034).** Proposed on the owner's choice “Yes, decrease only”. A Closed Budget still refuses every increase. |

New in v1.11:

| Earlier item | Disposition in v1.11 |
|---|---|
| No way for Planning to ask Budget for a line revision; the Planner had to contact the Budget Officer outside the product (KT-STD-001 v1.8 §3B.4; PLN-CHG-001 v1.27 §7.7) | **Add a Budget Revision Request record and its receive, decline and withdraw commands (§§4.10, 8.5, 9.2).** This does **not** revive the separate Budget Revision object disposed of in v1.2: the revision itself remains an ordinary externally approved successor Version under §6, with no separate revision workflow. The request only records Planning's ask, the Budget Officer's answer and the outcome. |

New in v1.4:

| Earlier item | Disposition in v1.4 |
|---|---|
| Reservations created at Procurement Planning, one per Plan source allocation, before the Annual Plan could be submitted | **Move to Procurement Requisition.** A ministry plan runs to hundreds of items; creating a reservation for each at planning locked the whole budget from the start of the planning cycle and made every plan revision a release-and-re-reserve exercise. The statutory budget-alignment basis is tracked in LAW-REG-001 v1.1; placing the operational hold at Requisition authorisation is the agreed product control, not a claim that the statute prescribes this software event. |
| No aggregate affordability contract | **Add `check_plan_affordability`.** Non-mutating; returns per-line approved amount, planned total, current positions and two verdicts. Within-approved blocks plan submission; within-currently-available is advisory. |
| `check_funding` and `reserve_funding` called by Procurement Planning | **Called by Procurement Requisition.** The contracts, their all-or-none semantics, idempotency and ledger effects are unchanged; only the caller and the moment change. |
| Finance Confirmation Officer confirming per Plan Item | **Reviews the whole Plan financial basis**, with at most one open Finance review per Plan Version, retained completed reviews and Active reassessment under PLN-CHG-001 v1.18 §5.3. The role, its scope and its registry entry are unchanged. |

New in v1.3:

| Earlier item | Disposition in v1.3 |
|---|---|
| DocType named `Budget` | **Rename to `Procurement Budget`.** ERPNext ships its own `Budget` DocType in the Accounts module, set against a Cost Center or Project for a Fiscal Year with Stop, Warn and Ignore control actions. Frappe DocType names are globally unique per site, so with ERPNext installed the existing name will fail at install or migrate. `BudgetVersion`, `BudgetLine` and `BudgetLineVersion` are renamed to match. |
| Any relationship between a Procurement Budget Line and an ERPNext Cost Center | **None.** Fully separate. No `cost_center` field, no reconciliation link, no derived value. The two systems control the same money for different purposes and are not integrated in MVP 1. |
| `procuring_entity_id` on `Budget` | **Remove.** One site is one Procuring Entity. BUD-BR-002 becomes one Procurement Budget per Fiscal Year. |
| `financial_year_id` referencing a KenTender `FinancialYear` | Replace with `fiscal_year`, referencing the ERPNext `Fiscal Year` governed by CFG-CHG-002 v0.10 §4.2. |
| Assignments scoped by PE, FY, organisation unit, capability and effective dates | **Remove PE, FY and capability.** Business authority is a role-bound `User Responsibility Assignment` under AUTH-ADR-001 v1.7, and Fiscal Year is never a user-permission dimension. One Budget Officer assignment works across every year; eligibility comes from the record's own fiscal year and version status. |
| "Capability" as the permission primitive throughout §7, §8.2, §12.5, §12.6 and §14 | **Remove.** Registered business roles replace every capability string. |
| `Budget Viewer` workflow role | **Remove.** Read access is produced by the registered permission hooks acting on the actor's assignments, exactly as Strategy Viewer was removed in STR-CHG-001 v1.7. |
| `owner_org_unit_id` on the line version | **Retain unchanged.** It governs which lines a Need may draw on — record eligibility, not user scope. These Budget roles are site-wide; AUTH may use Organisation Unit scope for other modules. Budget line ownership never grants or narrows a user's Budget responsibility. The label "PE-wide" becomes **Entity-wide**. |
| County Government of Kisumu (`PE-CGK`) isolation baseline, its three actors and every cross-PE isolation test | **Remove entirely.** Creating a second Procuring Entity is structurally impossible under CFG-AC-003, so the seed would fail unconditionally. |
| Bespoke fixture cast (`moh.budget.officer@…`, `bud.viewer.moh@…`, and the rest) | Replace with the KT-STD-001 §8.3 shared register, extended by the Budget actors in §15.1. |
| PE row in every artboard context strip and identity card | **Remove.** The **Financial Year** row is retained where it is the record's own attribute and replaced by a changeable year filter on the workspace. |
| "the existing KenTender PE/FY selector" in §11.1, §11.18 and §12.1 | **Remove.** The component no longer exists. |
| Restated closed-input rules, common page states, TDD protocol, release evidence and product-wide prohibitions | **Remove.** Cite KT-STD-001. |
| Citations of CFG-CHG-002 v0.3 and STR-CHG-001 v1.5 | Update to CFG-CHG-002 v0.6 and STR-CHG-001 v1.6. |

**Identifiers are deliberately unchanged.** `MOH-BUD-2027-001`, `MOH-BL-DHI-2027` and the rest keep their existing prefixes. They are opaque stable strings referenced by approved Procurement Planning contracts and seed data; the embedded `MOH` is not a permission dimension, a source of truth or a scope check. Renaming them would break downstream approved documents for no functional gain. Do not "tidy" them.

---

## 2. Purpose and exclusions

Budget & Funding records the externally approved procurement allocation for each fiscal year, preserves immutable approved Versions and line identities, supplies Budget-ceiling and affordability evidence, and protects availability through Requisition-authorisation reservations and downstream commitments. It provides controlled successor versions and read-only funding lineage. It does not calculate the statutory 30% planned-allocation denominator.

It does not enact or appropriate a budget, release cash, maintain accounting ledgers, process invoices or payments, or integrate with ERPNext accounting. Its own append-only **funding-control ledger** records reservations and commitments; it is not an accounting ledger or evidence of payment. Shared native Company currency and Fiscal Year metadata are permitted through owner contracts; ERPNext `Budget`, `Cost Center`, accounts and journals are never read, mirrored or reconciled.

No separate Allocation object, Strategy field, procurement method/schedule/lot authoring, actual expenditure, forecasts, utilisation dashboard, manual reservation/commitment entry, Budget-owned Finance task or duplicate shell is introduced. From v1.13 there is one exception to the exclusion of manual entry: the evidenced correction that lowers a Closed commitment (§4.11, BUD-BR-034). It is recorded by a Budget Officer, approved by a different Budget Approver, and can only lower an amount. From v1.15 there is a second exception: the existing-contract commitment entry (§4.12, BUD-BR-037), a reconciled record that a Budget Officer records and a different Budget Approver approves, for a contract that has no reservation. It is not a general manual commitment editor. There are no generic notes, descriptions, justification, contacts, miscellaneous attachments or editable technical identifiers. The external approval reference, date and one document pass KT-STD-001 §7's purpose gate because they substantiate the registered allocation.

## 3. Fixed external constraints and ownership

KenTender records the allocation approved through the external public-budget process. Budget approval verifies and activates that record for KenTender control; it does not replace external approval. No new assertion about current law is established by this amendment; LAW-REG-001 v1.1 governs legal verification and its remaining prerequisites.

| Information or decision | Owner | Budget relationship |
|---|---|---|
| Site entity, native Company association, Fiscal Year, Organisation Units, funding-source catalogue and UOM adapter | CFG-CHG-002 v0.10 | Resolve authoritative IDs and eligibility; no guessed Company mapping, fallback record or parallel catalogue. |
| Business authority | AUTH-ADR-001 v1.7 | Registered hooks and live responsibility assignments; no parallel permission mechanism. |
| Budget currency/precision contract | Budget, using verified native metadata mapping | Exact versioned currency-unit representation in §4.8; no accounting amounts or ledger import. |
| ERPNext accounting | ERPNext | No integration or modification by Budget. |
| Strategic Objective and snapshots | Strategy / Planning | No Budget field or write. |
| Accepted departmental requirement | Departmental Needs v1.12 | Six source facts; no Budget Line selection or Money field. Acceptance never reserves. |
| Budget Line selected for a Need-backed or direct departmental source | Procurement Planning | The Planning source entry selects the line; Budget validates exact source-department/funding eligibility. No selection is added to the Need. |
| Plan, items, source allocations, financial basis, Finance review and decision | Planning v1.18 | Read affordability; validate at a decision boundary; store returned evidence. No Planning reservation. |
| Requisition, exact submitted Version, drawdown and authorisation | Requisitions | Calls check/reserve at authorisation; stores one returned reservation per drawdown line in the same transaction. |
| Budget roots, Versions, lines, reservations, commitments and funding-control ledger | Budget | Own their persistence, rules and service contracts. |
| Budget revision request from Planning (v1.11) | Budget, on Planning's request | Planning decides to ask (PLN-CHG-001 v1.27 `RequestBudgetRevision`); Budget records the request, the Budget Officer's answer and the outcome. The external revision and its approval evidence stay outside KenTender until registered as a successor Version. |
| Contract, variation and cancellation | Contract Management | Authenticated conversion/adjustment/release events through Budget. |
| The chain behind a conversion (v1.14) | Each owner supplies its own link: Requisitions the Requisition Version and drawdown, the Tender owner the Tender and any lot, Award the Award, Contract Management the contract. Budget decides | Budget checks the references in the conversion event against what it holds and reads no other module's records (BUD-BR-035). |
| Statutory target applicability, planning denominator, qualifying category and overlap rules | LAW / CFG / Planning | Budget supplies exact Money and Budget-ceiling facts only. Planning calculates eligible current APP value from exact Plan Items and the verified rule; downstream reporting owns actual achievement. |

Owners exchange services and immutable event references. Budget never imports a downstream controller or queries its tables; callers never query or lock Budget tables themselves. The REQ authorisation boundary coordinates Planning drawdown and Budget reservation without moving either owner's persistence into the other module.

---

## 4. Canonical domain model

All identifiers are server-generated. Framework audit fields remain framework-managed.

### 4.1 Procurement Budget

The stable identity of one fiscal year's procurement allocation record.

| Field | Operational purpose and system effect |
|---|---|
| `budget_id` | Immutable generated reference used by routes, services, audit and downstream lineage. Not editable. |
| `fiscal_year` | The ERPNext `Fiscal Year` whose funding period this record governs. Required and immutable after creation. |
| `currency` | Fixes one currency for every line and calculation. Copied from the explicitly configured native Company default at creation and immutable. |
| `currency_basis_reference` | Retains the creation currency/precision evidence in §4.8; system generated, never editable. |

There is no `procuring_entity_id`. Every record belongs to the site entity by construction. There is at most one Procurement Budget per Fiscal Year. The display title is derived as `{entity name} procurement budget {FY label}` and is not stored.

### 4.2 Procurement Budget Version

The immutable approval boundary for one registered baseline or successor revision.

| Field | Operational purpose and system effect |
|---|---|
| `budget_version_id` | Immutable generated reference used by line versions, review tasks and audit. |
| `budget_id` | Links the version to its stable Procurement Budget. |
| `version_number` | Ordered version history; generated per Budget. |
| `based_on_budget_version_id` | Identifies the Active version copied to create a successor. Empty only for Version 1. |
| `revision_type` | Classifies an externally approved successor as `Supplementary allocation`, `Reduction`, `Transfer` or `Correction`. Required only when `based_on_budget_version_id` is present. |
| `status` | `Draft`, `Submitted for approval`, `Active`, `Superseded` or `Closed`. |
| `approval_reference` | Identifies the external approval instrument reviewed before activation. Required. |
| `approval_date` | Confirms that external approval preceded KenTender activation. Required. |
| `approval_document_file_id` | Links exactly one uploaded approval document used by the Budget Approver. Required. |
| `authorised_total` | The total approved by the external instrument. Version lines must sum to it before submission or activation. Required and positive. |

Submitted, approved, superseded and closed actors and timestamps are audit events. A Return reason is stored on the decision event, not as a version field.

### 4.3 Procurement Budget Line

| Field | Operational purpose and system effect |
|---|---|
| `budget_line_id` | Immutable generated reference used by Planning source allocations, reservations, commitments and routes; Need identity may remain upstream lineage, never a selected Budget field on the Need. |
| `budget_id` | Prevents the line identity from moving to another fiscal year's Budget. |

### 4.4 Procurement Budget Line Version

| Field | Operational purpose and system effect |
|---|---|
| `budget_line_version_id` | Immutable generated reference for review comparison and audit. |
| `budget_version_id` | Binds the values to one immutable version. |
| `budget_line_id` | Preserves downstream funding lineage across approved amount changes. |
| `title` | The funded purpose displayed in selectors, tables and snapshots. Required. No separate purpose or description field. |
| `owner_org_unit_id` | Limits **line eligibility** to one configured Organisation Unit. Empty means Entity-wide. This is a domain rule about which source departments may draw on the line; it is never a user-scope or permission check. |
| `funding_source` | From the governed funding-source catalogue; copied into downstream funding snapshots. Required. |
| `approved_amount` | The allocation ceiling for the line in this version. Required and positive. |

After first activation, `title`, `owner_org_unit_id` and `funding_source` define the stable line identity and cannot change in a successor. A genuinely different purpose, owner scope or funding source requires a new line. A successor may change only the approved amount. Submitted/approved snapshots retain the funding-source ID and its display label as reviewed; a catalogue rename may appear as a separately labelled current catalogue value but cannot rewrite that historical label.

There is no `cost_center` field and no ERPNext accounting reference of any kind.

### 4.5 FundingReservation

| Field | Operational purpose and system effect |
|---|---|
| `reservation_id` | Immutable generated reference returned to Procurement Requisitions and used by downstream lineage. |
| `budget_id` | Fixes the fiscal year funding root. |
| `budget_version_id_at_creation` | Preserves the version under which the reservation was confirmed. |
| `budget_line_id` | Identifies the funded purpose and balance affected. |
| `plan_item_id` | Links the reservation to the governed Plan Item. |
| `plan_source_allocation_id` | Retains the exact Planning allocation drawn; it is not a lifetime-unique reservation key. |
| `requisition_id`, `requisition_version_id` | Stable Requisition and exact immutable submitted Version authorising the draw. |
| `drawdown_id`, `drawdown_line_id` | Exact owning drawdown and line; database uniqueness on the owning authorisation event and drawdown line prevents duplicate creation. |
| `authorisation_event_id` | Immutable owner event coordinated in the authorisation transaction; retained after revocation. |
| `source_organisation_unit_id` | Exact source department validated through Planning/REQ facts; never inferred from the actor. |
| `original_amount` | The exact amount authorised on this REQ drawdown line, which may be less than the original Plan allocation. Required and positive. |
| `remaining_amount` | The unconverted and unreleased hold. Changed only by Budget services. |
| `status` | `Active`, `Partially Converted`, `Converted`, `Released` or `Needs Attention`. |
| `correlation_id` | Binds all reservations in one REQ authorisation; idempotency includes the immutable payload digest, not this string alone. |

There is no `Requested` reservation. **v1.15 — what the reservation already proves.** A reservation holds its plan item, plan source allocation, drawdown line, source organisation unit, Budget Line, the Requisition that authorised it (the caller reference), the correlation identity, the payload digest and the `source_set_hash`. The Requisitions owner computes `source_set_hash` over the exact Requisition Version and its drawdown lines (quantity and value), so the digest is supporting version evidence. The normative reservation model above retains the explicit `requisition_version_id`; an implementation that stores only a hash must resolve and verify the exact Version through REQ and include it in the verified conversion evidence. A hash alone is not a self-describing Version reference. No existing reservation is relabelled or silently rewritten. These are enough to prove the Requisition and source-allocation identity, and they stay as authorised. They do not hold the Tender, the lot, the Award and its version or the amount allocated at each conversion; those are retained on the commitment and the conversion event (BUD-BR-036). A failed check creates no reservation. There is no expiry date, manual authority field, note or attachment.

### 4.6 ProcurementCommitment

| Field | Operational purpose and system effect |
|---|---|
| `commitment_id` | Immutable generated reference used by Contract Management and funding lineage. |
| `reservation_id` | Prevents a commitment from bypassing the confirmed funding lineage. From v1.15 it is required when the commitment was made by converting a reservation and is empty for an existing-contract entry (§4.12). |
| `contract_id` | Identifies the owning downstream contract. Required and unique within the reservation lineage. |
| `current_amount` | Retained funding charge, including performed/paid work and supported surviving obligations; never merely unpaid balance. Active commitments change through the authorised adjustment service; Closed commitments decrease only through an approved correction. |
| `status` | `Active`, `Cancelled` or `Closed`. From v1.13, `Closed` means the contract owner has reported the final supported obligation: the amount is retained in Committed (BUD-BR-031) and changes only through an approved correction (BUD-BR-034). |
| `origin` (v1.15) | `Reservation conversion` or `Existing-contract entry`. Set once at creation. |
| `budget_line_id` (v1.15) | The Budget Line the commitment is charged to. Required. For a conversion it equals its reservation's line; for an existing-contract entry it is the line the entry names. Every reader of Committed reads it from here. |
| `entry_row_id` (v1.15) | For an existing-contract entry, the allocation row of the entry that created this commitment (§4.12). Empty for a conversion. |
| `lineage` (v1.15) | For a conversion, the verified lineage retained at creation (BUD-BR-036): Tender, lot where the source carries one, Award and version, funding allocation, package digest, contract and agreement version. Immutable; a legitimate correction is a new versioned entry beside it. |

One reservation may convert into more than one commitment. Each conversion is bounded by the locked remaining amount. Original amount = remaining hold + cumulative conversion debits + cumulative reservation-release debits. Commitment decreases/cancellations do not replenish the reservation or erase conversion history. A separately authorised commitment increase consumes additional available funds through `adjust_commitment`; it does not rewrite original reservation amount. A fully consumed hold is `Released` when only released, otherwise `Converted`; the event history distinguishes mixed conversion/release outcomes. `Needs Attention` applies while a positive remaining hold is retained; its typed reason blocks further progression until successful owner revalidation. Contract details, supplier, dates, variations and payments remain in Contract Management.

**v1.13 — Closed commitments.** A Closed commitment keeps its `current_amount`. It stays in Committed, in the line position, in the successor floor and in the omission test. It accepts no increase and no ordinary adjustment from the contract service. It is never counted as released, it never replenishes its reservation, and its conversion history is untouched. Closing a Budget does not extinguish it either (§6). Reopening the contract record in Contract Management neither reopens it nor changes its funding.

**v1.14 — Lineage.** `contract_id` names the contract, but it does not by itself prove that the contract may draw on the reservation. The proof is the chain in the conversion event under BUD-BR-035.

### 4.7 FundingLedgerEvent

Append-only: event ID and type; Budget, line, reservation and commitment IDs as applicable; Plan allocation, exact REQ Version/drawdown/authorisation event, contract or variation reference; exact Money amount; before and after approved, reserved, committed and available positions; actor or calling service, timestamp and correlation ID; and a typed revalidation failure code where applicable. Users do not create or edit ledger events.

---

### 4.10 Budget Revision Request — v1.11

The Budget-owned record of one Planning request to revise one Budget Line. It is a request and its outcome, not a revision: approved amounts change only through a successor Version under §6.

| Field | Operational purpose and system effect |
|---|---|
| `budget_revision_request_id` | Immutable generated reference returned to Planning and used in routes, audit and the outcome event. |
| `planning_request_id` | Planning's BudgetRevisionRequest identity (PLN-CHG-001 v1.27 §4.7); unique, so one Planning request creates one Budget request. |
| `idempotency_key`, `payload_digest` | Replay the original result for the same key and payload; conflict for the same key with a different payload. |
| `budget_id`, `budget_line_id`, `budget_line_version_id_at_receipt` | The Budget, line and exact line Version current when the request was received. |
| `approved_amount_at_receipt` | Budget's own approved amount at receipt, read under §8.5, not Planning's figure. |
| `planned_amount`, `over_amount` | Planning's planned total for the line and the excess, as sent. Displayed as Planning's facts; never Budget allocation. |
| `plan_version_reference` | Planning's exact Plan Version reference, for display and routing only. |
| `requested_by`, `requested_at` | The Planner and AUTH assignment evidence validated by Planning's registered service call, and the receipt instant. |
| `status` | `Open`, `Revised`, `Declined` or `Withdrawn`. |
| `linked_budget_version_id` | The successor Version started or continued from this request, when one is. |
| `outcome_by`, `outcome_at`, `decline_reason` | Who closed the request, when, and the 10–500 character reason when Declined. |

At most one `Open` request exists per `planning_request_id`. Several Open requests may name the same line (for example from successive Plan updates); each resolves on its own. Closed requests are immutable history. The record creates no reservation, commitment, financial record or funding ledger event.

### 4.11 Commitment Correction — v1.13

The Budget-owned record of one correction that lowers a Closed commitment. It is its own record: the original conversion event, the closure event and every earlier event are never edited, and Budget never overwrites a past ledger entry. The commitment's `current_amount` is the running figure the position reads, and an approved correction is what lowers it.

| Field | Operational purpose and system effect |
|---|---|
| `correction_id` | Immutable generated reference, used in routes, audit and the ledger event. |
| `commitment_id`, `budget_id`, `budget_line_id` | The Closed commitment corrected and its Budget and line. |
| `status` | `Awaiting approval`, `Approved` or `Returned`. At most one correction awaits approval per commitment. |
| `before_amount`, `after_amount` | The commitment's amount when the correction was recorded and the lower amount proposed. `after_amount` is below `before_amount`; zero is allowed. |
| `reason` | Why the amount was wrong, 10–500 characters. |
| `evidence` | One or more evidence references. Budget keeps them as references and never reads the documents they point to. |
| `contract_reference` | The Contract Management reference the correction relates to. Required. Budget keeps it as an opaque string and never reads Contract Management's records. |
| `recorded_by`, `recorded_at`, `recorded_event` | The Budget Officer who recorded it, when, and the ledger event that records it. |
| `decided_by`, `decided_at`, `decision_reason` | The Budget Approver who approved or returned it, when, and the reason (required to return). |

An approved correction lowers the commitment's amount and appends one funding ledger event, *Commitment corrected*, carrying the amounts before and after, the position before and after, the reason, the evidence and the Contract Management reference. A returned or awaiting correction moves no money. The record is written only by the Budget commands in §9.2.

### 4.12 Existing-Contract Commitment Entry — current v1.16

One coordinated entry recognises an independently registered contract’s confirmed funding charge in one eligible Active Budget year and its currency. Several rows may use different eligible Budget Lines in that same year. Do not fund several years by adding rows here. Independently onboarded contracts may use a separate Annual request/entry for each later eligible year under §8.8. Annual funding does not increase the contract or require reopening. Cross-currency funding remains excluded.

| Field | Operational purpose, validation and consumer |
|---|---|
| `entry_id`, `version_no`, `kind` | Generated identity and revision; Initial, Annual or Additional. Initial and Annual recognise that independently onboarded contract’s supported target-year charge; they share the contract/year uniqueness guard. Additional names an exact effective increment, never the original whole contract again. |
| `status` | Draft / Awaiting approval / Returned / Approved / Superseded. Draft and Returned are editable; submission freezes the reviewed payload. Approved is immutable. Superseded applies only to an unapproved preparation version; it never hides an effective commitment. |
| `request_id`, `contract_reference`, `contract_evidence` | One CM funding request, external contract identity, agreement version/digest and source evidence. Reused from CM; no retyping or fictional procurement records. |
| `finance_confirmation` | CM-owned `ContractFundingBasis.v1` (§8.7): exact intake/agreement revision, target year/currency, confirmed gross funding charge and explanation/evidence, confirmed by an authorised CM Finance approver. CM obtains native accounting evidence. Budget receives validated funding facts and opaque evidence references, not accounts or a ledger import. |
| `year_allocation_status` | Year allocation required / Confirmed. Missing confirmation permits saving the request and Draft; it prevents submission, approval and posting. A future-year share is Future funding not yet confirmed until its own eligible annual basis and funding exist; it does not block unrelated covered current-year actions. Unsupported currency/product remains Scope review required. No invented allocation. |
| `already_represented` | Exact Budget commitment IDs, current amounts/revisions and non-overlapping contract/scope coverage. Budget verifies these from its own records. Native invoices/payments alone do not count. |
| `amount_requiring_funding` | System calculation: confirmed gross funding charge for the target year and scope minus verified existing Budget commitment coverage of exactly that charge. Neither this total nor verified coverage is editable. Negative/overlapping/mismatched coverage is refused; zero is a no-entry outcome (§8.7). |
| `reconciliation_to_budget` | Officer’s explanation and references resolving current-year funding coverage, 10–500 characters; not a replacement for Finance’s evidence or an editable total. |
| Allocation rows | Generated row ID; exact Budget Line, year, funding source, source OU, amount and resulting commitment ID. Positive exact Money, eligible source under BUD-BR-007/008, target year/currency only. Group by line for affordability; row total equals amount requiring funding. |
| Actors and evidence | Recorder/submitter and exercised assignment, server times, submitted payload digest and expected source/entry revisions; deciding Budget Approver/assignment distinct from both the entry preparer and all Finance confirmers relied on by that submitted basis, decision/reason and original operation key. |
| Additional lineage | For Additional: original Closed commitment and CM’s exact effective increment event/version. Uniqueness is by obligation event and row, not merely contract + kind. Several legitimate later increments remain possible without duplicate funding. |

`record_existing_contract_commitment_entry` saves a Draft or updates a Returned preparation without money effects. `submit_existing_contract_commitment_entry` validates the complete payload and freezes it Awaiting approval. Approval atomically creates one Active commitment per row; Return changes no money. A later correction of an approved entry does not recreate or supersede its funded amounts: use authorised Active adjustment or Closed correction, with immutable source evidence. No generic entry editor changes an existing commitment.

Draft creation needs the real contract/request identity but permits incomplete rows, reconciliation and year confirmation. Submission requires them. A changed Finance basis or coverage revision invalidates the pending entry: the approver returns it for refreshed preparation; there is no silent recalculation of a submitted amount.

### 4.8 Shared types and financial evidence

| Type / representation | Required contract |
|---|---|
| Identifier | Opaque stable string; exact Version IDs are separate from roots and display references. All snapshots preserve both where needed. |
| Money | Exact decimal **currency units**, never binary float or implicit minor units. JSON strings use plain digits and an optional decimal point; no commas, exponent, NaN or Infinity. Non-negative except explicitly signed change projections. Positive where a field requires it. Inputs with more fractional digits than supported are rejected, even if trailing zeroes; valid inputs are canonically emitted at the supported scale. |
| Storage/calculation | At least 18 integral digits plus supported fractional digits. Exact decimal addition/subtraction/comparison throughout persistence, services, fixtures and owner boundaries; no `flt()`, epsilon equality or silent rounding. Overflow fails before mutation. |
| CurrencyBasis | `currency`, `fraction_digits`, `precision_version`, `source_metadata_reference`; immutable retained evidence of the verified owner/native mapping. KES fixture uses 2. No user-editable precision setting is added to Budget. Missing or unsupported precision blocks monetary writes and positive decisions; it is not defaulted. |
| Quantity | Exact positive decimal string and UOM identity/precision from the owning adapter. Budget validates the incoming drawn-value lineage; REQ/Planning own quantity allowance checks. No float conversion or reconstructed value from rounded display prices. |
| Instant / Date | ISO-8601 UTC instant / ISO date; EAT formatting in UI. Server decision time and CFG applicability basis are authoritative. |
| FinancialBasis | Schema `BudgetFinancialBasis.v1`: FY, Budget root/Active Version, CurrencyBasis, sorted unique lines of exact line/version IDs, approved amount, planned total, source funding identity and normalized eligibility facts; read `as_at`. Positions are separately timestamped advisory observations. |

Budget root retains its creation CurrencyBasis reference. Approved Version and decision snapshots retain the exact precision identity used; catalogue edits never reinterpret saved Money. A changed native default currency does not change an existing Budget. A precision-policy change that would affect existing records requires a separately controlled migration and cross-module reconciliation; do not round or silently adopt it on read.

Canonical basis fingerprint: SHA-256 over UTF-8 JSON with lexicographically ordered object keys, no insignificant whitespace, Money at CurrencyBasis scale, nulls explicit, and line/eligibility arrays sorted by their opaque identities. Include schema, FY, currency/precision, authoritative financial values and eligibility identities/revisions. Exclude read timestamps, available/reserved/committed observations, actor and UI labels. Return exact Budget/line revisions separately even where a semantically unchanged amount can reuse Finance evidence. Planning owns the explicit link between reused evidence and its current basis; Budget never asserts that Finance reviewed different Plan content.

Version IDs and basis digests returned by reads are evidence references, not a reservation token or guarantee that a later decision will pass.

---

### 4.9 User labels and exact financial meaning

| Stored concept | Visible label | Meaning / retained control |
|---|---|---|
| authorised_total on evidence form | Approved allocation | Externally approved total, not an appropriation made by KenTender. |
| approved_amount / sum of approved lines on live view | Registered allocation | Current recorded allocation ceiling in the displayed Budget Version. |
| Reserved | Reserved for requisitions | Remaining unconverted/unreleased holds, including Needs Attention. |
| Committed | Committed to contracts | Current active contractual obligations from owner events; not payments. |
| Committed (v1.13 reading) | Committed to contracts | The retained amount of Active and Closed commitments from owner events (v1.12 read: current active contractual obligations). Closing a contract frees nothing. Not payments. |
| Available | Available to reserve | Approved minus Reserved minus Committed; not a cash/bank balance. |
| owner_org_unit_id | Available to | Exact source-department eligibility; null means All departments. Not user authority or inferred descendant scope. |
| revision_type | Type of change | Same Supplementary allocation, Reduction, Transfer and Correction enum. |
| Active / Superseded Budget Version | Current / Previous version | Same immutable lifecycle states; exact Version remains visible in supporting detail. |
| Draft with latest Return evidence | Changes requested | Same editable Draft, exact immutable earlier submission attempt retained. |
| Submitted for approval | Awaiting Budget Approver review | Same submitted state; no additional queue/state. |
| Needs Attention reservation | Requires review — funds remain reserved | Same remaining hold and blocked downstream progression until owner revalidation. |
| Reserved + Committed during successor review | Reserved + committed | This amount must remain covered; current live check, not frozen proposed content. |
| proposed approved amount minus protected amount | Available after update / Shortfall | Non-negative projected availability if the guard passes; display exact positive Shortfall when it fails, never negative spendable money. |
| Budget Revision Request, Open (v1.11) | Budget revision requested | Planning has asked for this line to be revised; nothing has changed yet. |
| Budget Revision Request, Revised / Declined / Withdrawn (v1.11) | Revised / Declined / Withdrawn by Procurement Planning | The outcome reported to Planning; the Budget amount is whatever the Active Version says. |

These labels do not change source fields, enums, references, event keys, Money scale or historical evidence. Derived display title remains unstored. No separate Allocation object is created by using the word allocation in a user label. Raw correlation IDs, hashes and calculation internals are secondary technical evidence, not business tasks.

## 5. Canonical calculations and invariants

For one line at an `as_at` point:

**Reserved** = sum of `remaining_amount` for reservations in `Active`, `Partially Converted` or `Needs Attention`.
**Committed** = sum of `current_amount` for commitments in `Active` or `Closed` (v1.12 read: commitments in `Active` only; superseded by v1.13, BUD-BR-031).
**Available** = `approved_amount − Reserved − Committed`.

Budget totals are the sums of the Active Version's line positions. Users never enter calculated totals. Closed/historical projections use the explicit retained Version and funding ledger at the requested instant; they never combine an old approved amount with today's position without labeling the two contexts separately.

| ID | Rule and enforcement |
|---|---|
| BUD-BR-001 | Every user business write requires an Active site-wide `User Responsibility Assignment` for the required role. Registered service writes additionally validate the owner command/event and the initiating actor’s live authority at its decision boundary; a service identity alone grants no financial discretion. No Procuring Entity, Fiscal Year or capability scope check participates. |
| BUD-BR-002 | One Fiscal Year has at most one Procurement Budget and one Active Version. Enforced by a database-level partial unique index or equivalent guard **and** in the activation transaction. Serialization alone is insufficient. |
| BUD-BR-003 | Every line amount and funding event uses the Budget currency. Cross-currency funding is outside MVP 1. |
| BUD-BR-004 | Approval reference, approval date, one approval document and a positive authorised total are required before submission. The approval date cannot be in the future or after activation, and the version line sum shall equal `authorised_total`. |
| BUD-BR-005 | Only Draft versions are editable; Submitted for approval, Active, Superseded and Closed versions are read-only. |
| BUD-BR-006 | Only an Active Version may support a new reservation. |
| BUD-BR-007 | A line is eligible for an allocation only when it is in the resolved Active Version and its owner scope is Entity-wide or exactly matches the explicit `source_organisation_unit_id` of that allocation. Need-backed and direct Planning sources obey the same rule; no descendant expansion is inferred. This is record eligibility, evaluated after the actor's responsibility check, never instead of it. |
| BUD-BR-008 | The allocation's funding source shall equal the line's funding source. Procurement type does not restrict eligibility. |
| BUD-BR-009 | No Procurement Planning event creates a reservation. Need acceptance, DPP submission, DPP validation, Plan Item formation, plan funding confirmation, Annual Plan adoption, statutory approval and publication all leave Budget balances unchanged. Reservation begins only at successful Procurement Requisition authorisation. |
| BUD-BR-010 | A reservation request covers the complete current source-allocation set for the drawing record. All required reservations succeed in one transaction or none is created. |
| BUD-BR-011 | Each authorised REQ drawdown line receives exactly one reservation. A later separately eligible drawdown may reference the same original Planning allocation without reusing its earlier reservation. Planning enforces remaining allowance, stable-item scope lock and one-open-REQ rules. Same idempotency key plus same payload returns the original result; a different payload conflicts. |
| BUD-BR-012 | `check_funding` and `check_plan_affordability` are both non-mutating. A check token is short-lived and cannot bypass locked revalidation during reservation. Plan affordability issues no token. |
| BUD-BR-013 | Reserved, committed and available positions shall never be negative. Concurrent commands cannot oversubscribe a line. |
| BUD-BR-014 | A reservation may be partially converted into one or more commitments; only the unconverted remainder stays reserved. |
| BUD-BR-015 | Release, conversion and commitment adjustment require an authenticated downstream event and are idempotent by correlation ID. No user keys amounts directly in Budget UI. From v1.13 the one exception is the correction of a Closed commitment (BUD-BR-034). From v1.15 there is a second, the existing-contract commitment entry (BUD-BR-037). |
| BUD-BR-016 | `Needs Attention` keeps the remaining amount reserved while downstream progression is blocked. It does not silently release funds. |
| BUD-BR-017 | A successor cannot reduce a line below its current Reserved plus Committed position. From v1.13 that Committed includes Closed commitments (BUD-BR-031). |
| BUD-BR-018 | A Transfer successor shall have equal total increases and decreases and shall preserve `authorised_total`. |
| BUD-BR-019 | An existing line identity may change approved amount only. A new purpose, owner scope or funding source requires a new line. |
| BUD-BR-020 | A line may be omitted from a successor only when it has no remaining reservation or active commitment (v1.13: and no Closed commitment amount, BUD-BR-031). |
| BUD-BR-021 | Approval rechecks approval evidence, line total, floors, transfer balance, responsibility and concurrency under one transaction lock before activating. |
| BUD-BR-022 | Approving a successor atomically makes it Active and the previous Active Version Superseded, preserving all line, reservation and commitment identities. |
| BUD-BR-023 | A Closed Budget admits no new reservations but retains all read, audit and downstream lineage. |
| BUD-BR-024 | Downstream modules use Budget service contracts and cannot query or mutate Budget tables directly. |
| BUD-BR-025 | Generated identifiers, calculated positions, statuses and audit authority are never client-editable. |
| BUD-BR-026 | No Budget path reads, writes or reconciles an ERPNext `Budget`, `Cost Center`, account or journal record. |
| BUD-BR-027 (v1.11) | A Budget Revision Request is received only from the registered Planning service principal, only for a line on the current Active Version whose Planning planned amount exceeds Budget's own approved amount at receipt. It changes no amount and creates no reservation, commitment or ledger event. |
| BUD-BR-028 (v1.11) | Only a successor Version approved under BUD-BR-021 and BUD-BR-022 changes an approved amount. A request never substitutes for external approval evidence, the four approval details or the Budget Approver's decision. |
| BUD-BR-029 (v1.11) | When `approve_budget_version` activates a successor that changes or omits a line's approved amount, every Open request on that line becomes `Revised` in the same transaction. A successor that leaves the line unchanged leaves the request Open. |
| BUD-BR-030 (v1.11) | Decline requires the Budget Officer and a 10–500 character reason. Withdrawal is received only from the Planning service principal. `close_budget` resolves every remaining Open request on that Budget as `Declined` with the system reason **The budget for this financial year is closed.** Each close of a request publishes one outcome. |
| BUD-BR-031 (v1.13) | Committed includes active commitments and closed commitments at their retained final amounts. Closing a commitment does not release funds. Any permitted reduction requires an evidenced correction under Budget’s controls (BUD-BR-034). Availability, the successor floor (BUD-BR-017), the omission test (BUD-BR-020) and every read of a line's position use this one figure. |
| BUD-BR-032 (v1.13) | `close_commitment` is called only by the Contract Management service principal, for its own contract's commitment, on an owner outcome event of type `ContractClosed` or `TerminationSettlementCompleted` that names the final supported obligation, with reconciliation evidence and the commitment revision the caller read. It changes the commitment's status and records one zero-value Commitment closed event whose before and after positions are identical. It never accepts a release amount, never changes an amount, never replenishes a reservation and is idempotent. A stale revision, an amount that differs from the owner event, or a different outcome for an already Closed commitment fails with no effect. |
| BUD-BR-033 (v1.13) | A Closed commitment accepts no increase and no ordinary adjustment: `adjust_commitment` refuses it, up or down, and a Closed Budget refuses any increase and any new conversion. Reopening the contract record in Contract Management neither reopens the commitment nor changes its funding, and Contract Management makes no funding call when it reopens. |
| BUD-BR-034 (v1.13) | The amount of a Closed commitment is lowered only by an approved correction (§4.11). A Budget Officer records it with the new lower amount, a reason, at least one evidence reference and a Contract Management reference. A different person holding Budget Approver approves or returns it; the person who recorded it can never approve it, even holding both responsibilities, and the check fails closed when the recorder cannot be shown. Approval lowers the commitment's amount, returns exactly the decrease to Available, leaves the reservation, its remainder and its conversion history unchanged, never edits an earlier ledger event, and appends one Commitment corrected event with the amounts and positions before and after, the reason, the evidence and both people. A correction can only lower an amount, can be recorded after the Budget is Closed, and is refused if the commitment changed after it was recorded. |
| BUD-BR-035 (v1.14) | A conversion is valid only if the whole chain matches: plan source allocation, exact Requisition Version and drawdown, Tender (and lot where the source already carries one), Award, contract. A matching supplier, Tender or Requisition alone is not enough. Budget checks the chain against references the owning modules supply in the conversion event and never reads their records. A mismatch, and a chain that is not supplied, are refusals with no effect. The amount converted from each reservation cannot exceed what is still unconverted (BUD-BR-014). A reservation that is Needs Attention, Released or revoked, and a Closed Budget, cannot be converted. A repeated conversion event creates nothing twice (BUD-BR-015), and two contracts competing for one reservation cannot oversubscribe it. When one award names several reservations, every one is checked before any is converted. No new lot feature is added: a lot is enforced only where the source already carries one. |
| BUD-BR-036 (v1.15) | The lineage of a conversion is verified at the first conversion as well as every later one, against authoritative source references. Budget consumes the owning modules' verified answer for the Tender, the lot where the source carries one, the Award and its version and the funding allocation, through a published owner contract. It never imports a Tender controller, never reads another module's records, and never trusts an identifier a browser supplied. It compares that answer with the conversion event and with what it holds on the reservation, and refuses on any difference or when the owner's verification is unavailable. The verified lineage is retained immutably on the commitment and on the conversion ledger event. The reservation is not changed: its Requisition and source-allocation identity stays as authorised. A later conversion, an amendment or a legitimate correction is checked against what was retained; a correction is a new versioned owner event beside the earlier evidence, never an overwrite. |
| BUD-BR-037 (current v1.16) | Existing-contract entries follow §§4.12/8.7: real independent contract, exact CM-confirmed funding basis, one target eligible year/currency, system-calculated uncovered charge, Officer preparation and separate Approver decision. Draft saving and request creation allow missing year confirmation; submission/approval/posting do not. No Budget-owned Finance task or accounting access. |
| BUD-BR-038 (current v1.16) | Approval validates all rows together, adds requirements by Budget Line under lock, verifies the exact submitted Finance/coverage revisions and creates one commitment per positive row atomically. Zero uncovered charge uses the verified no-entry outcome. §§4.12/8.7 govern. |
| BUD-BR-039 (current v1.16) | Approved entries are immutable. Subsequent Active adjustments or Closed corrections retain the original evidence; an entry version never re-creates funded money. Returned preparation can be edited and resubmitted. §§4.12/8.7 govern. |
| BUD-BR-040 (current v1.16) | Reopening alone changes no funding. A separately evidenced increment beside a Closed commitment uses eligible verified conversion or a bounded Additional entry under §8.7. The original amount is neither raised nor duplicated; event-and-row uniqueness permits successive real increments without replay duplicates. |

---

## 6. Lifecycle and governance

| Current status | Command | Next status | Authorised actor |
|---|---|---|---|
| Draft | Submit for review | Submitted for approval | Budget Officer |
| Submitted for approval | Return | Draft | Budget Approver; reason required |
| Submitted for approval | Approve | Active | Budget Approver |
| Active | Activate successor | Superseded | System, inside the successor activation transaction |
| Active | Close after FY | Closed | Budget Approver |

Version 1 is the initial baseline; Version 2 and later are successor revisions. There is no separate revision workflow and no recommend-then-activate two-step — Approve both decides and activates in one atomic transaction.

- A Budget Officer may create and edit only Draft versions.
- The submitting Budget Officer cannot approve the same version, even when that user also holds Budget Approver. Enforced from the version's own submission audit event.
- Return requires 10–500 characters and preserves an immutable submission-attempt snapshot, exact evidence attachment and decision. Re-editing the same Draft Version creates a new submission attempt; no prior submitted content or decision is overwritten. Decision authority is checked against the submission being decided.
- Approval means "available for KenTender procurement control". It does not approve the public budget, which happens in IFMIS.
- At most one open Draft or Submitted-for-approval successor may exist per Budget.
- A successor is always copied server-side from the current Active Version.
- Closing requires the fiscal year to have ended and no reservation with a remaining amount. Existing commitments remain in the funding-control history and calculation; authorised decreases/cancellations may still reconcile them. From v1.13 an existing commitment, Active or Closed, counts in Committed until it is lowered, and a Closed commitment is lowered only by an approved Budget correction (BUD-BR-031, BUD-BR-034), also after the Budget is Closed. Closed budgets cannot support new holds, conversions or obligation increases. Closure never means payment or extinguishment of an obligation.
- Records and ledger events are never deleted after submission.
- **v1.11 — Budget revision request.** Request status is independent of Version status: `Open` → `Revised` (BUD-BR-029), `Declined` (BUD-BR-030) or `Withdrawn` (Planning). Answering a request uses the existing successor route: **Update registered allocation** creates or reuses the one open successor (the at-most-one rule above is unchanged) and links it to the request. The successor needs the same external approval details and the same Budget Approver decision as any other; the request adds no step, queue or state to the Version lifecycle.

---

## 7. Roles and permissions

Three Budget business responsibilities exist. All are registered in the AUTH-ADR-001 v1.7 §4.4 registry with `scope_type = Site-wide`.

| Business role | Scope type | Permitted actions |
|---|---|---|
| Budget Officer | Site-wide | Register the initial Draft, create a successor, edit Draft approval details and lines, and submit. From v1.13 also records a correction that lowers a Closed commitment (BUD-BR-034). From v1.15 also records an existing-contract commitment entry, with its allocation rows and reconciliation, and answers a contract funding request (BUD-BR-037, §8.6). |
| Budget Approver | Site-wide | Inspect a submitted version; return it with a reason, or approve and activate it; close a Budget after the fiscal year. From v1.13 also approves or returns a correction of a Closed commitment, never one the same person recorded (BUD-BR-034). From current v1.16 also approves or returns an Initial/Annual/Additional entry, never one they prepared or whose funding basis they personally confirmed; check actual relied-on funding-basis participants (BUD-BR-037; §8.8). |
| Finance Confirmation Officer | Site-wide | Open the current whole-Plan Finance review, confirm or return against its basis, and reassess exact Active Plan content through Planning. At most one review is open per Plan Version; completed reviews remain history. Confirmation creates no reservation and grants no Budget authoring, approval or activation authority. |

Registry properties: none is an `exclusive_office`; all are granted by Administrator or System Manager; Budget Officer and Budget Approver carry `sod_tags` sufficient for the no-self-approval rule.

There is no Budget Viewer role. Read access is produced by the registered permission hooks acting on the actor's assignments. **Auditor** is a registered business role under AUTH-ADR-001 v1.7 §4.4 and confers no Budget mutation. **Procurement Planner** reads eligible lines through contracts and holds no Budget responsibility.

The **REQ service principal** is a registered authenticated caller for `check_funding`, `reserve_funding` and exact pre-consumption revocation release. It supplies the owner-authorised command context; Budget validates it with the immutable REQ/drawdown facts, live initiating authority and the full atomic transaction. It cannot read Draft Budgets or author a Budget Version.

The **Planning service principal** (v1.11) is a registered authenticated caller for `receive_budget_revision_request` and `withdraw_budget_revision_request`, in addition to its existing read and decision-validation calls (§9.1). It supplies Planning's owner-authorised command context and the initiating Planner's live Procurement Planner assignment; Budget validates both at receipt. It cannot change an amount, read a Draft Budget, author a Version or create a reservation.

The **contract service principal** is an authenticated service account, not a business role and not a registry entry. It calls `revalidate_reservations`, `release_reservation`, `convert_reservation` and `adjust_commitment` with a downstream event reference and an idempotency key. From v1.13 it also calls `close_commitment` on the same terms (v1.12 read: the four calls named above only). It cannot change a Closed commitment (BUD-BR-033). From v1.14 `convert_reservation` additionally needs the chain in the conversion event (BUD-BR-035); the principal alone does not grant a conversion. From v1.15 the contract service principal may also call `revalidate_reservations`, but only for a reservation that the funding-lineage owner confirms for that contract (`contract_reservation_authority.authorises(contract, reservation)`), which means the exact reservations in the contract's approved funding package. A call for any other reservation is refused with `BUDGET_DOWNSTREAM_FORBIDDEN`. This grants no general Budget access and no power to change funds: the principal gains no `check_funding` or `reserve_funding`, cannot create or edit a Version and cannot read a Draft, and nothing else in the 6 October 2026 list changes (owner decision of 16 October 2026, recorded as FU-CM-81, a narrowly scoped amendment to the 6 October decision; v1.12 read: the sentence above lists the call for the contract principal without that limit, while the build followed the 6 October decision and refused it). It cannot create a reservation, edit a version or read a Draft.

Administrator and System Manager receive full technical read under AUTH-ADR-001 v1.7 §8 and no Budget business action. No capability profile, capability string, operational scope assignment, Fiscal Year grant, Frappe User Permission or parallel permission store participates in a Budget authorization path.

---

### 7.1 All-actor journey and read boundary

| Actor | Normal work | Boundary |
|---|---|---|
| Budget Officer | Record approved allocation; continue initial Draft; correct return; update current allocation; from v1.11, answer a Planning budget revision request by updating the allocation or declining with a reason | Site-wide current assignment; register/edit/submit only. Same submission's submitter cannot approve it even with both roles. |
| Budget Approver | Review initial allocation or changes, inspect exact evidence, approve/activate or return; close after year-end | One decision activates; closure is the existing guarded action, not a new queue or appropriation stage. |
| Finance Confirmation Officer | Whole-Plan Finance review and reassessment in Planning; permitted live Budget Line reading | No Budget Finance screen, authoring/approval power or reservation from confirmation. |
| Procurement Planner | Owner selection of eligible lines for exact departmental sources; permitted positions; from v1.11, request a line revision through Planning | Record eligibility does not derive from the Planner's assignments; no Budget mutation. A request is Planning's service call, not a Budget write by the Planner, and it waits in Planning, not on a Budget screen. |
| Requisition actors / registered service | Work in REQ; authorisation coordinates exact drawdown reservations | Draft, submission and department approval reserve nothing. Service requires owner-authorised live context. |
| Contract actors / registered service | Owner conversion, adjustment or release; permitted lineage | No manual Budget financial controls; unavailable owner facility is not replaced locally. |
| Auditor | Authorised exact Budget, Version, submission attempt, file and funding history | Read only; historical Version/instant never replaced with current ledger. |
| Administrator / System Manager | All-record technical read/search, including Draft, Submitted and exact approval-shaped routes | No business assignment required for technical read; all mutation needs the actual business authority and checks. |
| Multiple roles / AO or other titles | Actual assigned work together without a role switch | No Budget authority from title alone. External appropriation/approval remains outside this system. |

A technical-reader detail exception under AUTH v1.7 §8 applies equally to BUD-UI-02 and BUD-UI-04. Ordinary neutral/consumer read does not itself grant workflow-task access. Denied pages resolve inline before protected content paints; navigation stays on the selected route. Reader access is enforced by the registered hooks, not by a new Budget Viewer role.

## 8. Procurement Planning and downstream integration

### 8.1 Distinct financial moments

| Moment | Caller / contract | Effect |
|---|---|---|
| Planning preparation and review display | PLN / `check_plan_affordability` | Read-only comparison; no lock, token, financial write or ledger event. |
| Positive Finance or other governed Planning decision needing a current basis | PLN / `validate_plan_affordability_for_decision` | Serialize the Budget basis inside the caller's transaction; no Budget financial record, hold or ledger event. PLN writes its decision only if the same transaction commits. |
| Planned reservation-target calculation | PLN / its eligible-current-APP calculation | No Budget denominator call. Planning uses current Plan Items plus the exact verified CFG rule; Budget participates only in ordinary affordability/ceiling checks. |
| REQ authorisation | REQ / `check_funding` then `reserve_funding` | Exact reservation per drawdown line; full authorisation commits or nothing does. |
| Contract conversion/adjustment | Registered Contract service | Changes owned reservation/commitment positions through authenticated events. |
| Planning budget revision request (v1.11) | PLN / `receive_budget_revision_request`, `withdraw_budget_revision_request`; Budget outcome event to Planning | Records the request and its outcome only; no lock beyond the line read, token, financial write, reservation or ledger event (§8.5). |

Finance review covers the **whole Plan financial basis**, never one item or one lifetime-only review. Draft basis changes cancel/stale the affected review under PLN v1.18 §5.3. Active reassessment appends current evidence without editing the approved Plan or original Finance statement. Source changes that leave all financial amounts and eligibility facts unchanged can reuse evidence only through PLN's explicit basis-reuse record. Available-funds changes alone do not invalidate affordability evidence.

An Active Plan with stale funding evidence cannot support a new REQ authorisation until Planning's recovery gate passes. Its earlier authorised Requisitions and Budget reservations remain intact. A Budget amendment does not enlarge an already procured Plan Item; new scope follows the separately governed Planning route and cannot be absorbed into a locked proceeding.

### 8.2 Plan affordability

Per-line planned total is compared with that line's approved amount on the applicable Active Budget Version. Excess over approved amount is blocking for positive Finance and formal Planning submission. Excess over currently available amount, while within approved, is **advisory** for Planning; REQ reservation still requires sufficient actual availability.

`check_plan_affordability` reads a coherent committed snapshot, locks nothing, writes nothing, issues no check token and emits no funding ledger event. It returns the FinancialBasis and each line's approved/planned/reserved/committed/available amounts, exact excess/shortfall, both verdicts and observation time. It checks explicit source-OU/funding eligibility; an aggregate alone cannot prove every contributing source eligible. Caller-supplied amounts describe the Plan; they do not replace Budget-owned approved amounts.

### 8.2A Decision-time validation

`validate_plan_affordability_for_decision` is distinct from the display call. It requires the trusted caller transaction context, exact decision/Plan financial-basis context, FY/currency/precision, complete per-line totals and financial eligibility facts, and expected Budget and line revisions. Reservation-rule inputs and the eligible-current-APP calculation remain Planning/CFG evidence and are not part of this Budget validation contract.

1. Authorize the registered caller and its owner-validated live actor/decision context. Resolve current CFG facts through the owner contract; no raw cross-module table access.
2. Lock or equivalently serialize the applicable Budget root/Active-Version guard and affected authoritative lines in stable ID order. All Budget activation, closure and decision-validation paths use compatible locks. Retain protection until the caller commits or rolls back; a lock released before PLN saves is insufficient.
3. Re-read current Active Version, currency/precision, line identities, amounts and eligibility revisions. Check expected revisions; stale/missing/ineligible basis fails atomically. A changed revision is returned for explicit refresh/reuse evaluation, never silently substituted in the pending positive command.
4. Return the immutable affordability comparison snapshot. A change in unused Budget headroom can change funding evidence but cannot change the 30% Planning denominator. Planning separately validates its exact Plan/rule calculation in the same positive decision.
5. Commit the Planning decision only in that same valid transaction. Budget creates no reservation, commitment, financial record or funding ledger event. Out-of-process implementations require equivalent proven atomicity; a remote success response plus a later unguarded PLN commit is not sufficient.

A failure returns typed stale, configuration, eligibility, precision or affordability details to the authorized caller; no partial positive decision survives. Ordinary reserved/committed movements remain advisory for Finance but are represented consistently in the returned observation.

### 8.2B Budget ceiling versus Planning denominator

The Active Procurement Budget Version and its approved line amounts remain authoritative for affordability. They are **not** a statutory planned-allocation denominator. The Budget total may exceed the complete APP value; unused headroom does not compel procurement and does not create a qualifying-allocation target.

Planning freezes its exact Plan Version, rule Version and per-item applicability evidence for the 30% calculation. Budget freezes the exact funding basis used for affordability. These snapshots may share currency and Plan-decision context, but neither owner substitutes its measure for the other. Historical Budget reads continue through the ordinary exact-Version financial contracts; no separate `AnnualProcurementBudgetBasis.v1` schema or `get_annual_procurement_budget_basis` service is retained.

### 8.3 Atomic REQ reservation

REQ supplies its root/exact immutable submitted Version, proposed authorisation-event identity, exact Planning root/Version/item/allocation facts, every drawn line/quantity/value/source OU/funding source, source-set digest and one command idempotency key. Drafting, submission, department approval and return create no reservation.

`check_funding` validates the complete array and aggregates requirements **by Budget Line** before testing availability: two individually affordable rows can together exceed one line. It returns per-drawdown rows, per-line totals/shortfalls and one token binding the full input digest, actor/caller, REQ/Plan/source/line revisions and server expiry. It writes nothing. A token is not authorisation, cannot cover a subset, and cannot bypass revalidation. The implementation must publish and test its bounded token lifetime; expiry returns `BUDGET_CHECK_STALE` without mutation.

`reserve_funding` validates that same token and exact payload in the REQ owner transaction, locks Budget root/affected lines in stable order, rechecks aggregate availability and creates **one reservation per drawdown line**, even when two lines share a Budget Line. It returns a complete drawdown-to-reservation mapping. REQ authorisation, Planning drawdown/scope guard, reservation set, decision, immutable handoff and outbox event commit together or all roll back. Owner APIs implement the shared lock order; no downstream table locks by callers. All callers use the same ordered transaction protocol, documented and concurrency-tested during implementation.

Same key plus identical payload returns the original committed mapping, even if later released; it never recreates a released hold. Same key plus changed payload fails. A unique authorisation-event/drawdown-line constraint prevents a new key duplicating that authorised line. Later draws against remaining original allowance require their own eligible REQ authorisation and lineage. No partial source confirmation, silent line substitution, silent reduction or release-and-reserve retry workaround is permitted.

### 8.4 Later events and boundary protection

| Event | Required effect |
|---|---|
| Material change before REQ authorisation | Recheck submitted owner facts; no reservation yet. |
| Correction of an authorised unconsumed REQ | REQ's governed revocation reverses exact Planning drawdown and releases the exact reservation set atomically; retain prior evidence, then use the owner's corrected successor route. No in-place mutation of authorised facts. |
| Handoff already consumed | No Budget release shortcut for scope change; follow the owning downstream procedure. Planning scope lock does not disappear merely because funding is later released. |
| Contract conversion | Convert at most the remaining hold; preserve exact REQ/source lineage. |
| Contract conversion lineage (v1.14) | Convert only when the chain in the event matches the reservation's own lineage (BUD-BR-035). A reservation another award funds, an unrelated reservation with the same supplier or Tender, a wrong Requisition Version, a wrong line and a missing chain are all refused, and nothing is partly converted. |
| Existing-contract commitment entry (v1.15) | A Budget Officer records the allocation rows and a different Budget Approver approves the amount the system calculated from Finance's confirmed figures for an existing contract that KenTender Budget controls; one commitment is created for each row, with no reservation, and Available falls by exactly the rows charged to each line (BUD-BR-037, BUD-BR-038). Insufficient availability on any row refuses the whole approval with the exact shortfall per row. |
| Contract increase | Revalidate current Active line availability and authorised variation; consume only the increase atomically. |
| Contract decrease/cancellation | Reduce commitment through an idempotent owner event. Release a reservation remainder only when the authenticated event explicitly authorises that release; never automatically recreate a hold. |
| Contract closure (v1.13) | Close the commitment through `close_commitment` on the owner's Closed or termination-settlement outcome. Status and attribution change. The amount, Available, the reservation remainder and the conversion history do not (BUD-BR-031, BUD-BR-032). |
| Correction of a Closed commitment (v1.13) | Lower it only through a Budget correction recorded by a Budget Officer and approved by a different Budget Approver (BUD-BR-034). The contract service cannot, and reopening the contract in Contract Management changes nothing. A correction never recreates a hold. |
| Budget successor activation | Enforce Reserved + Committed floors, retain lineage and expose exact new revision evidence through owner contracts for consumer staleness checks. A monetary floor breach blocks activation; it is not cured by marking reservations Needs Attention. |
| Eligibility revalidation failure | Retain the remaining hold with typed Needs Attention reason and block affected downstream progression; restore status only after successful owner revalidation. |

### 8.5 Planning budget revision request — v1.11

1. **Receipt.** Planning calls `receive_budget_revision_request` inside its `RequestBudgetRevision` transaction (PLN-CHG-001 v1.27 §7.2) with: Planning request ID, idempotency key, Fiscal Year, Budget Line and expected line revision, Planning's planned amount, the over amount, the Plan Version reference and the requesting Planner. Budget authorises the service principal and the Planner's live assignment, reads the current Active line and its approved amount, and checks the expected revision (`BUDGET_DECISION_BASIS_STALE` when changed). It rejects the request when the planned amount does not exceed Budget's approved amount (`BUDGET_REVISION_NOT_REQUIRED`). It records one Open request and returns `budget_revision_request_id`. The call commits with Planning's transaction or not at all; Budget holds no lock after it.
2. **Answer.** The request appears in the Budget Officer's pending work (§11.1B, BUD-DES-18). **Update registered allocation** runs the existing `create_budget_successor_version` and links the created or reused successor. The Budget Officer obtains the external approval outside KenTender and completes the successor as today. **Decline request** runs `decline_budget_revision_request`.
3. **Outcome.** Revised (BUD-BR-029), Declined or Withdrawn (BUD-BR-030) each publish one `BudgetRevisionRequestOutcome.v1` event through a transactional outbox committed with the state change: Planning request ID, Budget request ID, outcome, resulting line Version and approved amount when Revised, decision actor or service, instant and a per-request ordering number. Delivery is idempotent and retried from the outbox; Budget draws no Planning conclusion. Planning recomputes its own readiness (PLN-CHG-001 v1.27 §7.3).
4. **Withdrawal.** Planning calls `withdraw_budget_revision_request` when its Planner withdraws. A successor already started from the request is not changed or cancelled by withdrawal; it remains ordinary Budget Officer work.

### 8.6 Contract funding request — current v1.16

CM raises `receive_contract_funding_request` for Initial entry, Annual entry, Additional entry or Closed correction with contract/agreement/evidence/operation identities. An incomplete Finance basis does not prevent receipt. Budget creates/reuses the one request under §8.7, with Officer pending work and the linked CM waiting item. Finance confirmation is owned and completed in CM.

The Officer prepares the entry or correction, or declines with reason. Entry save is distinct from submit; correction recording submits the complete correction directly for its existing separate decision. Budget’s ordered outbox returns each actual outcome and its attempt identity, exact created commitments or shortfall grouped by line. Return and insufficient availability keep the request open for correction; decline and withdrawal close it without money changes. A successful identical replay returns its original receipt/outcome.

Source evidence arriving later updates the same request through `update_contract_funding_basis`; changed submitted evidence requires return and resubmission. CM alone calls `withdraw_contract_funding_request`. No request creates a reservation, commitment or appropriation by itself. A correction initiated directly from Budget may link the same CM subject without forcing a redundant HOP request.

### 8.7 Funding operations, ownership and balances — current v1.16

This section controls conflicting v1.13–1.15 proposal wording. For each affected line let A = registered allocation, R = remaining reservation holds, C = retained Active + Closed commitments and V = A − R − C. None is cash or accounting expenditure. Source evidence establishes authority; an authenticated caller alone does not. All monetary operations recheck their sources, live initiating authority where applicable, expected revisions and aggregate balances inside their compatible owner transaction. Identical accepted retries return the original result; conflicting payloads fail.

| Operation / trigger | Owner and authority / evidence | Approval and balance effect |
|---|---|---|
| Register/update external allocation | Officer records externally approved instrument; separate Budget Approver verifies exact Version | Approval changes A only; new A cannot be below R+C. Transfer preserves total A. No new appropriation. |
| Reserve on REQ authorisation | REQ owner authorisation, exact Version/drawdown/source set and live initiating authority | Existing authorisation only; Budget atomically adds drawn amounts to R and subtracts them from V, one reservation per drawdown line. |
| Release unused hold | Owning REQ revocation or downstream authorised disposition names exact unconverted remainder | No new Budget approval; R decreases and V increases by that amount. Never releases a commitment or restores Planning scope automatically. |
| Convert to effective contract | CM owner event + AWD verified allocation; all source rows validated | R decreases, C increases equally; V unchanged. No part exceeds remaining hold. Whole allocation set succeeds or none does. |
| Revalidate | Exact authorised source reservations; owner service, not a browser check | No value change. Failed eligibility retains the hold and Needs Attention; successful revalidation restores only the appropriate state. |
| Adjust Active obligation | CM effective variation/cancellation with exact supported amount and source evidence | C changes by the signed delta; V changes oppositely. Increase needs open Active funding and sufficient V. No paid-work reduction merely because an invoice settled. |
| Close commitment | CM closed/termination-settlement event with matching final supported amount | Status only; A,R,C,V unchanged. No new approval beyond owner outcome. |
| Correct Closed commitment | Officer’s evidenced error record + different Budget Approver | Approved downward difference decreases C and increases V; R and original conversion unchanged. After year closure this is a historical correction, not spendable current-year funding or reopened authority. |
| Existing-contract entry | CM confirmed basis; Officer’s mapped rows and separate Budget Approver | Approval adds only new uncovered charge to C and reduces V; R unchanged. No fabricated reservation. |
| Additional obligation after reopening | Effective incremental owner event; original commitment remains Closed | New approved funding for the increment only. Use available eligible reservation conversion or, if no such hold exists, a bounded Additional entry with a verified original commitment and owner increment. Both origins can use that bounded Additional path; it is not a new Initial-entry shortcut for an award. |
| Annual funding for an independently onboarded contract | CM confirms the exact target-year basis; Officer prepares and independent Approver decides under §8.8 | One eligible year’s confirmed uncovered charge increases C and reduces V; no reservation, reopening, contract-value increase or automatic cross-year transfer. Future portions remain visible as not yet funded. |
| Foreign currency / unsupported product | CM retains actual terms and flags unsupported funding | No exchange conversion, invented product/profile or implied signing authority. Existing currency/product exclusions remain. |

**Tender scope and independent annual funding.** REQ v1.19 §§5.1/5.12 still excludes multi-year tender-derived purchases; AWD remains one lot/KES/fixed price. Independently onboarded, already executed contracts within CM’s supported goods/minor-related-service profile may span years and use §8.8 annually. The current-year fraction is not evidence that the entire contract is funded. Show each year’s confirmed coverage separately; future portions stay visible without blocking covered current-year actions. BUD-BR-003 still excludes cross-currency funding. No prior-year unpaid amount is automatically moved into a new year, and no earlier-year closed Budget is reopened.

**Opening funding basis.** `ContractFundingBasis.v1` is a CM-owned verified response for an exact intake/agreement revision and funding scope: contract and confirmation identity/revision; target Budget year; currency/precision; confirmed gross funding-control charge; its contractual/accounting basis and evidence references; effective confirmer/assignment and confirmation time; source digest; any unsupported residual scope. It reuses the existing opening review, with CM Finance approval authority (§20 of CM v0.10), not the Planning-only Finance Confirmation Officer. The gross charge includes attributable performed/paid work plus supported remaining obligation on that confirmed basis. Accounting evidence establishes facts; posting a native invoice or payment alone never reduces C or supplies Budget coverage.

Budget verifies coverage by commitment ID, year, currency, contract, exact scope and revision. Count coverage once, whether Active or Closed. For an Additional request calculate coverage for that exact increment; never subtract the original commitment from an unrelated increment. CM provides an independently supported increment, not total-minus-old-amount guessed by Budget. Coverage above the charge or duplicate coverage creates an error; do not clamp to zero. If new charge is exactly zero, Budget returns Already covered or No charge to this year after its validation and closes the request with no entry, zero commitment or funding ledger event. That outcome authorises no new expenditure or future-year payment.

**Transaction and source freshness.** Read external owner evidence through published interfaces, then pin the verified source revision/digest to a durable authorised operation. Within Budget locks recheck the pinned authority remains current or is valid for that exact operation, plus reservation/commitment revisions and grouped line balances. A pre-lock check alone is insufficient. Multi-reservation conversion uses one owner command transaction; no partly converted contract is returned as complete. Signature evidence survives a later funding failure; CM retains the original durable intent and shows the funding issue without requesting repeat signatures.

**Request lifecycle and recovery.** For Initial/Annual funding, one request per contract and target Budget year, with one linked entry lineage and no parallel Initial/Annual request for the same year. Additional requests are unique by exact increment event and target year; correction requests by exact correction subject. Identical replays reuse the original request and entry. Request states are Open / Completed / Declined / Withdrawn. Draft/Returned/Awaiting approval are entry states, not duplicate request states. A Return or insufficient-funds result leaves the request Open and publishes one ordered outcome for that decision attempt. Approved entry, verified Already covered or verified No charge to this year completes it. Decline requires reason. CM may withdraw an Open request before funding; withdrawal abandons unapproved preparation but changes no commitment. Finance confirmation arriving later refreshes the same request by versioned owner event; Budget stores no Finance task.

**Handoffs and next work.** CM owns the Finance opening-confirmation task and retains the original supplier/contract context. Receipt creates the Officer’s request item and CM’s linked waiting item. Missing Finance basis shows Waiting for Finance with the CM task link; it is not a blocked request-creation command. Submission creates the Approver item and Officer waiting item. Return clears the Approver item and restores Officer preparation. Approval/decline/withdrawal clears the corresponding items and updates CM by ordered outbox event. Changed-holder resolution uses existing AUTH/task services. The shortfall belongs to the open request; Officer can seek an externally approved Budget revision through the existing successor process or return the funding mapping to CM for supported correction. No new escalation approval is added.

**Corrections and closure.** There is no reconstructed historical approval of post-close correction. BUD-BR-034 is explicitly Proposed here for review. The original events and closed-year context remain inspectable. The Budget Approver reviews attached evidence through its authorised source projection; Budget does not inspect an ERPNext ledger. Only an evidenced overstatement may decrease; performed work and supported surviving liabilities must remain covered.

### 8.8 Annual funding of independently onboarded contracts — approved direction

Applies only to an already executed independently onboarded contract within CM’s supported product/profile and currency. It does not authorise a new multi-year procurement or enlarge a signed obligation. Keep full contract value and year-by-year obligation/coverage visible in CM; Budget records only the approved charge against each annual allocation.

1. When a later target year becomes eligible and its Budget is Active, CM surfaces **Request annual funding** in the existing contract work. The action reuses `RequestExistingContractFunding` with Annual kind, target year and exact contract/basis reference. No arbitrary reminder interval, new module or contract reopening is introduced. A request may be saved before all funding facts exist, but positive entry approval requires an eligible Active Budget for that target year, complete evidence and availability. Simply reaching a calendar date grants no funding.
2. Reuse signed terms, schedule, source/terms review and immutable historical facts. Finance confirms the target-year funding basis using the existing CM funding-evidence review and actual Finance approval responsibility; Finance preparation may prepare its reconciliation but cannot confirm its own subject. This appends a versioned annual funding confirmation; it does not revise the original cutover stock/accounting opening position. Refresh only changed or unresolved facts. An earlier basis may be referenced only where it explicitly covers this exact target-year charge and is still valid; an old approval is not automatically carried forward.
3. Budget verifies that year’s non-overlapping existing commitment coverage and calculates the uncovered charge under §8.7. Previous-year commitments stay in their original years and are neither subtracted from the new year’s charge nor released to fund it. Prior-year unpaid liabilities need an explicit supported treatment; calendar rollover alone never reallocates them.
4. Budget Officer prepares eligible same-year rows. Budget Approver must be a different person from that preparer and every Finance confirmer relied on by the submitted basis. Same request/entry/decision workflow, no new approval stage. Record the actual participant identities and reject self-review through `AUTH_SEGREGATION_BLOCKED`.
5. Approval creates only that year’s new commitments atomically. CM marks only those covered actions as funded. A future year’s unconfirmed allocation cannot block a payment fully supported by a confirmed earlier/current-year allocation, subject to its actual liability/year treatment and the existing native payment controls. A payment spanning several funding scopes needs coverage of every applicable portion.
6. One contract/year has one Initial-or-Annual request identity and entry lineage. Returned, declined or withdrawn attempts are retained; deliberate resubmission reuses that same year’s lineage and creates no second request or duplicate charge. A completed year later needing a genuine increase uses the existing supported adjustment/increment path, not another Annual entry for the same obligation. Decreases use the relevant Active adjustment or Closed correction. A year-2 entry is not an increase to year 1 and never requires reopening a Closed contract merely to process surviving payment work.

**Annual acceptance.** For an isolated existing KES 900,000 contract with supported year shares 300,000/400,000/200,000, year 1’s approved entry covers 300,000 only. In year 2, an Active eligible Budget and confirmed 400,000 basis allow one Annual request/entry without reopening; its approval funds 400,000 only, leaves year-1 charge/history unchanged and makes that scope’s eligible payments available. Year 3 remains Future funding not yet confirmed. Duplicate year-2 requests, same confirmer/Approver, insufficient year-2 funds and attempts to spend year-3 coverage are refused without partial posting. Exact prior-year debt treatment and native payment guards remain independently enforced. The scenario uses three existing relative seed years from the current configured anchor, not future native postings or fabricated FY dates.

## 9. Service and command contracts

### 9.1 Read and funding contracts

All amounts use §4.8 Money. Authorized responses provide human `reference` separately from stable IDs, exact version/revision references and typed errors. No service accepts a Procuring Entity or user-FY scope argument. Source OU is a **record-eligibility argument**, not user authority.

| Contract | Required input | Output / effect |
|---|---|---|
| `get_budget_currency_contract` | FY/Budget context, optional exact historical Budget Version | CurrencyBasis and supported Money format; no inferred default or ledger access. Logical provider name to be mapped to the repository in implementation. |
| `resolve_budget_context` | FY | One Active Budget/Version summary and CurrencyBasis, or typed absent/ineligible result. |
| `list_eligible_budget_lines` | FY, **source_organisation_unit_id**, optional funding source, search/paging | Eligible Active rows: ID, human `reference`, title, owner scope, funding source, exact revisions and positions. Entity-wide or exact source OU only; no Draft rows. |
| `get_budget_line_position` | Line ID; current mode or explicit historical Version/instant | Exact authorized identity, approved/reserved/committed/available amounts and `as_at`; historic replay fails typed if not reproducible. Never silently label today's position as historical. |
| `check_plan_affordability` | FY, CurrencyBasis, unique per-line planned totals and complete source-OU/funding eligibility facts | FinancialBasis, both verdicts and observations; §8.2. No lock, token, financial write or ledger event. |
| `validate_plan_affordability_for_decision` | Trusted caller transaction/decision context, same complete financial inputs and expected Budget/line revisions | Serialized immutable comparison or atomic typed failure; §8.2A. No Budget financial record or ledger event and no reservation-denominator result. |
| `check_funding` | Exact REQ/Plan/drawdown/authorisation context, complete drawn source array and digest, correlation | Non-mutating per-row and per-line results, aggregate shortfalls, one bound expiring token; §8.3. No Finance-task parameter. |
| `reserve_funding` | Owner transaction, check token, exact unchanged payload/expected revisions, idempotency key | Complete drawdown-line/reservation mapping and positions or rollback. |
| `revalidate_reservations` | Exact set, authenticated owner event/type and idempotency key | Current or Needs Attention result and effective state-change ledger evidence; no new reservation. |
| `release_reservation` | Reservation, exact amount, authenticated owner cancellation/revocation event, key | Reduced hold and position; excess/duplicate payload conflicts fail. REQ revocation coordinates the complete set atomically. |
| `convert_reservation` | Reservation, contract, exact amount, authenticated contract event, key | Commitment, updated remainder/position; no amount beyond locked remainder. |
| `adjust_commitment` | Commitment, exact new total, authenticated variation/cancellation event, key | Locked adjustment and effective ledger event; no unfunded increase. |
| `close_commitment` (v1.13) | Commitment, expected revision, contract outcome event naming the final supported obligation, reconciliation evidence, key | The Closed commitment with its new revision, identical before and after positions and an acknowledgement (BUD-BR-032). An in-process service for the contract service principal only, never a web endpoint. |
| `get_funding_lineage` | Authorized Plan allocation, REQ/drawdown, reservation, contract or commitment reference | Stable and exact-version lineage, owner events and authorized routes; no guessed links or Draft Budget disclosure. |

**v1.13 — `adjust_commitment` and a Closed commitment.** `adjust_commitment` changes an Active commitment only. For a Closed commitment it fails with `BUDGET_INVALID_STATE` whether the new total is higher, lower or equal, and nothing changes (BUD-BR-033). A Closed commitment's amount is lowered by a Budget correction (§9.2, BUD-BR-034), never by this call.

**Historical v1.14 conversion proposal — superseded by current §8.7 and verified lineage.** `convert_reservation` carries, beside the reservation, the contract, the amount, the contract event and the key, one `lineage` the owning modules supplied. Budget compares each link with what it holds. Where it holds nothing yet, the first conversion of a reservation records the link and every later conversion of that reservation must match it (record-and-compare, proposed; BUD23-XD-001).

| Link | Supplied by | Budget checks it against |
|---|---|---|
| Plan source allocation | Planning, through the Award package | The reservation's own plan source allocation. Held today. |
| Requisition and exact Version | Requisitions | The reservation's Requisition. Held today as the caller reference. Normative explicit Version reference is in §4.5; predecessor implementation reportedly omitted that field but retained the source-set hash. Verify the exact Version through REQ and retain the owner-confirmed reference; a hash is not a display identity. |
| Drawdown line | Requisitions | The reservation's own drawdown line. Held today. |
| Budget line | Budget's own lineage read, through the Award package | The reservation's own Budget Line. Held today. |
| Tender, and lot where the source carries one | The Tender owner, through the Award package | Not held today. Recorded and compared as above. |
| Award | Award | Not held today. Recorded and compared as above. |
| Contract | Contract Management | The caller's own contract. Already required today. |

Budget refuses with `BUDGET_RESERVATION_NOT_AUTHORISED` when any link differs, when the chain is not supplied, or when the reservation is not convertible. It validates the complete source set and pins the verified operation, then revalidates its current authority and local revisions under the compatible locking protocol in §8.7 before converting any row.

**v1.15 — verified lineage on the conversion.** `convert_reservation` consumes a verified answer, not a caller's claim. Contract Management supplies the award reference, the agreement version and the package digest it received from Award. Budget asks the Award owner’s published lineage verification through a registered interface in `kentender_core`, pins its exact revision under §8.7, and to confirm for that award and that reservation the Tender, the lot where the source carries one, the Award and its version and the funding allocation. Budget compares the answer with the event, and the Budget-held links with its own reservation (source allocation, drawdown line, Budget Line, Requisition and the exact Version through the source-set digest), refuses with `BUDGET_RESERVATION_NOT_AUTHORISED` on any difference, and on success retains the verified lineage on the commitment and the conversion event. The interim check built under v1.14, which asks Contract Management whether the agreement names the reservation, is replaced by this verification when the Award contract exists (BUD24-XD-002).

Eligible-line listing verifies source OU after caller authorization. Missing/unknown source OU fails even for Entity-wide candidates because source lineage still requires a real source department. Optional funding-source filter affects selection; a decision validates the exact source identity of every allocation. Disabling a catalogue entry removes new-selection eligibility and triggers current-use validation; historical read-by-ID and frozen labels remain available. No catalogue rename rewrites an approved Budget line or a downstream snapshot. A genuinely changed line owner/source requires a new line under §5.

Draft Budget save/submit/approve validate active selectable configuration through CFG's owner contract; decisions revalidate owner facts under `ValidateProcurementConfigurationForDecision` where applicable. Generic open/read actions perform no check-and-reserve side effects.

### 9.2 Governance commands

| Command | Purpose |
|---|---|
| `save_budget_version_draft` | Create or update Draft approval details with optimistic concurrency. |
| `save_budget_lines_draft` | Create, update or remove Draft lines as one validated change set. |
| `submit_budget_version` | Validate approval details, line total and version rules; move Draft to Submitted for approval. |
| `return_budget_version` | Require a correction reason and return a submitted version to Draft. |
| `approve_budget_version` | Revalidate responsibility, evidence, line total, floors, transfer balance and concurrency; atomically activate and supersede where applicable. |
| `create_budget_successor_version` | Copy the current Active Version and line identities into one Draft successor. |
| `close_budget` | Close an Active Budget after the fiscal-year and remaining-reservation guards pass. From v1.11 it also resolves remaining Open budget revision requests under BUD-BR-030. |
| `receive_budget_revision_request` (v1.11) | Planning service principal only. Record one Open request under §8.5 and BUD-BR-027; idempotent. |
| `decline_budget_revision_request` (v1.11) | Budget Officer. Open request only; reason 10–500 characters; publish the outcome. A closed request returns `BUDGET_REVISION_REQUEST_CLOSED`. |
| `withdraw_budget_revision_request` (v1.11) | Planning service principal only. Open request only; publish the outcome; no effect on a linked successor. |
| `record_commitment_correction` (v1.13) | Budget Officer. Record a correction that lowers a Closed commitment: the commitment, the new lower amount, a 10–500 character reason, at least one evidence reference, the Contract Management reference, the commitment revision read, a key. Missing evidence, reference or reason fails with `BUDGET_EVIDENCE_REQUIRED`; an amount that does not lower, or a commitment that is not Closed, with `BUDGET_INVALID_STATE`; a changed commitment with `BUDGET_STALE_REVISION`. Moves no money. |
| `decide_commitment_correction` (v1.13) | Budget Approver, never the person who recorded it. Approve or return a correction awaiting approval; a return needs a 10–500 character reason. Approval applies BUD-BR-034 under the Budget's lock. A correction already decided fails with `BUDGET_INVALID_STATE`; a commitment that changed since it was recorded with `BUDGET_STALE_REVISION`; the recorder with `AUTH_SEGREGATION_BLOCKED`. |
| `receive_contract_funding_request` (v1.15) | Contract service principal only. Record one Open request under §8.6; idempotent; changes no amount. |
| `decline_contract_funding_request` (v1.15) | Budget Officer. Open request only; reason 10–500 characters; publishes the outcome. |
| `record_existing_contract_commitment_entry` (v1.15) | Budget Officer saves Draft/Returned preparation from an exact open request. Contract/owner facts are reused. Incomplete rows/reconciliation/target-year confirmation may be saved; only submission requires completeness. No money changes. A completed duplicate/replay resolves its original result; conflicting payload or record revision fails. |
| `decide_existing_contract_commitment_entry` (v1.15) | Budget Approver independent of both its preparer and every relied-on funding-basis confirmer approves or returns the exact Awaiting approval entry. Return needs reason. Recheck unchanged submitted basis and Budget coverage, grouped line availability, currency/year, authority and row sum under one transaction. Approval creates all commitments or none. Source change requires returned preparation; no silent refreshed amount. |

From v1.11, `create_budget_successor_version` accepts an optional `budget_revision_request_id`: it creates or reuses the one open successor exactly as before and records the link on the request. `approve_budget_version` applies BUD-BR-029 in its activation transaction.

Every write requires the expected record version. Concurrency and idempotency rules are in KT-STD-001 §11.

---

**Current v1.16 command completion.** `record_existing_contract_commitment_entry` saves Draft/Returned preparation (§4.12), including incomplete preparation; `submit_existing_contract_commitment_entry` validates and freezes the exact entry Awaiting approval. `update_contract_funding_basis` and `withdraw_contract_funding_request` are authenticated CM-only operations under §8.7. `decide_existing_contract_commitment_entry` cannot silently refresh a changed source. All commands use expected revision, actor/owner authority, immutable payload digest and the original retry identity. The existing correction record/decision commands retain their separate-author controls. The existing `convert_reservation` is a logical per-row operation; a whole Award conversion set commits in one Budget transaction through the existing owner integration, never sequential independent successful row calls.

### 9.3 User-action mapping and save/submission contract

| User action | Existing command / scope |
|---|---|
| Save and add budget lines | save_budget_version_draft creates one Budget and initial Draft, then opens its lines. |
| Save changes — Approval details | save_budget_version_draft saves only the permitted Draft evidence/details. |
| Save changes — Budget lines | save_budget_lines_draft saves one validated line change set. |
| Submit for review | Save changed valid scopes as below, then submit_budget_version on the exact confirmed Version. |
| Update registered allocation | create_budget_successor_version copies the exact Active Version; at most one open successor. |
| Update registered allocation, from a revision request (v1.11) | create_budget_successor_version with the request ID; reuses an open successor; links it to the request. |
| Decline request (v1.11) | decline_budget_revision_request with the reason from BUD-DES-19. |
| Return for correction | return_budget_version, preserving the submitted attempt/document and 10–500 character reason. |
| Approve registered allocation / Approve allocation update | approve_budget_version; atomic decision/activation and predecessor supersession. |
| Close budget | close_budget; existing year-end, remaining-hold and authority guards. |
| Record a correction to a closed commitment (v1.13) | record_commitment_correction. Use BUD-DES-20 (§11.22); browser entry is required for workflow acceptance. |
| Approve or return a correction (v1.13) | decide_commitment_correction. Use BUD-DES-20 review variant (§11.22). |
| Answer or decline a contract funding request (v1.15) | record_existing_contract_commitment_entry or record_commitment_correction from the request; decline_contract_funding_request with the reason. Use BUD-DES-21/22 (§11.22). |
| Record or decide an existing-contract commitment entry (v1.15) | record_existing_contract_commitment_entry; decide_existing_contract_commitment_entry. Use BUD-DES-21/22 (§11.22). |

First creation resolves an explicit native Fiscal Year with no existing Budget and a verified CurrencyBasis. The registration form requires its four existing approval details (valid reference, non-future approval date, positive approved allocation and exactly one successfully uploaded/linked approval document) before Save and add budget lines. It does not yet require completed lines or a reconciled line sum. Generated Budget/Version IDs and immutable year/currency are returned only on confirmed save. No unsupported partial field schema is inferred from the word Draft; an incomplete form stays unsaved with its actual errors. Submission additionally requires all valid lines, exact total equality and applicable Version rules. Subsequent saves revalidate their affected scope; Save never claims full submission readiness.

Capture a stable attempt payload, expected token and idempotency identity for each command. Pending details and line edits remain distinct validated scopes. Submit validates visible completeness, saves changed approval details first, reconciles/refetches the authoritative token as needed, saves changed lines using the confirmed current token, then submits that exact resulting Version with a separate submission key. Unchanged scopes need no repeated save. A stale result cannot silently overwrite newer changes or use the prior token. Client previews never submit calculated balances or generated identities.

| Result | Required recovery |
|---|---|
| Upload or evidence-link failure | Do not submit or claim the file is attached. Preserve authorised input; no Budget record if first save has not succeeded. An uploaded file alone is not a registered allocation. |
| Known first-save failure | No alleged Budget identity or submitted status. Explain the actual error; duplicate-year response opens the authorised existing record instead of another create. |
| Save confirmed, navigation failed | Offer Open saved draft for that exact returned Budget/Version. Do not register again. |
| One save confirmed, later scope save rejected | Retain the confirmed saved scope; state which changes were saved and which were not, and preserve permitted unsaved edits. No submit. |
| All required saves confirmed, Submit rejected | Your changes were saved, but the allocation was not submitted. Show cause and permitted retry on the same Draft. |
| Save/submit/approve/close outcome unknown | We could not confirm the result. Checking the existing request… Resolve/replay the original command identity and immutable payload. No duplicate root, submission attempt, decision or financial effect; no failure inferred from a timeout. |
| Stale record or permission changes | Re-read authoritative state and allow deliberate reconciliation. Preserve only still-authorised input; remove protected content on access revocation. Never auto-submit content the user has not reviewed. |

Every underlying save/submit/decision is its own transaction unless an inspected implementation proves otherwise. This document does not claim multiple saves plus submit are atomic. Actual RPC/token/idempotency/file-link mappings require implementation evidence. Retries after browser refresh recover the original unresolved request before creating another identity. Do not add autosave, a new workflow record or manual financial adjustment.

Replacing a Draft's current document affects only that Draft link. Every earlier submitted attempt retains the exact immutable attachment and reviewed values. Failed replacement cannot orphan submitted evidence; any temporary-upload cleanup follows the existing file owner's mechanism, never bulk deletion of historical files.

The current entry action labels are **Save draft**, **Submit for review**, **Approve funding entry** and **Return for correction**, mapped respectively to record, submit and the two decision outcomes. **Decline request** acts on the request and requires a reason. Finance confirmation is reached through **Open contract review**, not a new Budget Finance screen.

### 9.4 Review and closure observation contract

Review composes exact immutable submitted values and fixed predecessor comparison separately from live Reserved/Committed positions at a stated as_at. Compare material amount/line membership and changed external evidence, not only the total; include the complete proposed line set and exact source eligibility. Refresh cannot modify a submission, release holds or create a ledger event. Missing live positions/critical evidence produce unavailable, not zero or Ready. Approval repeats all guards under the existing lock.

Closure reads actual year-end status, Active Version and all remaining reservations including Needs Attention. After year-end, show either exact blockers, unavailable or ready. The close command revalidates current actor, state and every hold at commit using compatible existing Budget locks. Concurrent reservation/conversion/closure produces one valid ordering or an atomic typed failure; the displayed ready result is not clearance. Active commitments alone do not prohibit closure (v1.13: nor do Closed commitments). Existing owner decreases/cancellations remain governed; closure permits no new hold, conversion or commitment increase.

## 10. UI architecture and routes

Budget & Funding remains a top-level module. Its menu contains only **Budget & Funding** and **Approval tasks**, the latter resolving access through the server; business decisions require Budget Approver authority, while AUTH v1.7 technical readers may inspect the exact review read-only. Other denied callers reach its inline Forbidden state rather than hidden navigation. Finance tasks remain in Procurement Planning; no Budget-side Finance queue or screen is added.

| Screen | Canonical route | Purpose |
|---|---|---|
| BUD-UI-01 Budget & Funding workspace | `/app/budget` | Selected fiscal year's existing Draft/submission, current Budget and operational position. |
| BUD-UI-02 Budget Version editor | `/app/budget/{budget_id}/version/{version_number}/edit` | Baseline or successor Draft approval details and lines. |
| BUD-UI-03 Budget workspace | `/app/budget/{budget_id}` | Read-only Overview, Budget Lines, Funding Activity and History. |
| BUD-UI-04 Approval task | `/app/budget/review/{budget_version_id}` | Approver inspection and return-or-approve decision. |
| BUD-UI-05 Budget Line detail | `/app/budget/line/{budget_line_id}` | Read-only line position and funding lineage; target of Planning's **Open Budget & Funding**. |

Current v1.16 adds two deep links, reached from existing pending work and line detail: `/app/budget/correction/{correction_id}` for the correction and `/app/budget/contract-funding/{request_id}` for the request/entry. These are task/detail routes inside Budget, not new menu modules or a Finance queue. Existing read hooks apply; business mutation requires the actual responsible Officer/Approver.

The Budget workspace uses URL-backed **Overview**, **Budget Lines**, **Funding Activity** and **History** tabs. The approval task uses **Overview**, **Budget Lines**, **Changes** and **History**. This document authorises no second dashboard, application shell or Frappe header.

---

## 11. Static Claude Design contract

Supply **KT-STD-001 §2 plus this section** to Claude Design. Nothing else. The closed-input rules, product-wide prohibitions, approved desktop shell, page-header pattern and division of supply are in KT-STD-001 §2.2–2.5 and are not repeated. Fixture actors, organisation units and fiscal years come from KT-STD-001 §8, extended by §15.1 below.

**Additional prohibitions for this document:** do not show a Procuring Entity row or selector, a Cost Center, an accounting reference, Strategy data, procurement classification, a separate purpose field, Value Commitment, treatment, actual expenditure, outstanding commitment, forecast, utilisation percentage, chart, contact, note, justification or generic attachment. Show the one named **Approval document** only on artboards that explicitly include it.

The Financial Year appears as a **record attribute** on Budget and version pages, and as a **changeable filter** on the workspace. It is never a gate and never a context selector.

### 11.1 BUD-DES-01 — Budget & Funding workspace

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding**

**Page content header**

- Eyebrow: **BUDGET & FUNDING**
- Title: **Budget & Funding**
- Description: **View the registered procurement budget and the funding position used by Procurement Planning.**
- No header action button

**Filter row**

- select showing **FY 2027/28**

**Current budget card**

- Heading: **Ministry of Health procurement budget 2027/28**
- Status: **Current**

| Label | Value |
|---|---|
| Budget reference | MOH-BUD-2027-001 |
| Current version | Version 1 |
| Currency | KES |
| Approval reference | MOH-FIN-BUD-2027-01 (Demo) |
| Approval date | 30 Sep 2026 |

Right-aligned secondary button: **View budget**

**Funding position row — four equal cards**

| Card label | Value |
|---|---:|
| Registered allocation | KES 160,000,000 |
| Reserved for requisitions | KES 0 |
| Committed to contracts | KES 0 |
| Available to reserve | KES 160,000,000 |

**Budget Lines preview**

| Budget Line | Available to | Registered allocation | Reserved for requisitions | Committed to contracts | Available to reserve | Action |
|---|---|---:|---:|---:|---:|---|
| Digital health infrastructure programme · MOH-BL-DHI-2027 | Digital Health | KES 100,000,000 | KES 0 | KES 0 | KES 100,000,000 | View |
| Digital health workforce development · MOH-BL-HWD-2027 | All departments | KES 60,000,000 | KES 0 | KES 0 | KES 60,000,000 | View |

Do not show Finance tasks, a register button on this Active-state artboard, or a Procuring Entity row.

### 11.1A BUD-DES-01A — Budget & Funding workspace, technical reader with an open Draft or Submitted version

**Retained v1.7 correction.** Before v1.7, no artboard showed a technical reader anything for a Draft or Submitted version — the workspace and BUD-UI-03 both scoped to Active, Superseded and Closed only, and AUTH-ADR-001 §8's technical-read right had no artboard exercising it. This is that artboard.

**Fixture context — outside the artboard:** Administrator · System Manager · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding**

Use isolated `BUD-SC-REVISION` (§15.6), including its KES 80m DHI hold and aggregate KES 80m available. Same page content header, filter row and Current budget card as BUD-DES-01 — an Active version, if one exists for the year, still renders identically; this variant adds to it, never replaces it.

**Additional card**, shown only when a Draft or Submitted-for-approval version exists for the selected year:

- Heading: **Allocation update awaiting Budget Approver review**; secondary Version 2 (fixture submitted by Josphat).
- Status badge: **Submitted for approval**

| Label | Value |
|---|---|
| Version | Version 2 |
| Submitted by | Josphat Mwangi, Budget Officer |
| Submitted | 15 Mar 2027, 16:20 EAT |

Right-aligned secondary button: **View version (read-only)**.

Selecting it opens BUD-UI-02's route for that version. Every field renders as a plain read-only value, per §12.2's correction below — no edit control, no Save draft, no Submit for review.

### 11.1B BUD-DES-01B — Officer and Approver pending-work variants

Use the same selected-year workspace and existing tasks. No second register or work queue. These variants supply the missing initial Draft/submission journeys alongside the technical-reader variant below.

| Actual state | Main message | Server-authorised action |
|---|---|---|
| No Budget record | No procurement allocation has been recorded for FY [year]. | Officer: Record approved allocation. Reader: none. |
| Initial Draft | Allocation draft. Continue recording the approved allocation. | Officer: Continue draft; authorised reader: View draft. No Register again. |
| Initial Submitted | Awaiting Budget Approver review. No allocation is current in KenTender yet. | Approver: Review; Officer: View submission. No current position or duplicate create. |
| Current plus Draft successor | Keep current allocation and its position; show Update in progress separately. | Officer: Continue update. Reuse the existing successor. |
| Current plus Submitted successor | Update awaiting Budget Approver review. The current allocation stays in use. | Approver: Review; Officer: View submission. |
| Returned Draft | Changes requested, full exact return comment and prior-attempt context. | Officer: Correct and resubmit, directly opening the same Draft. |
| Closed | Closed; year, exact closure actor/time and retained financial context. | Read permitted history; no new financial controls. |
| Current plus one or more Open budget revision requests (v1.11) | One task row per request, BUD-DES-18. The current allocation and position stay as they are. | Officer: Update registered allocation (or Continue update when a successor is already open) and Decline request. Approver, Auditor, technical reader: none; the request is not their work. |

Initial Draft/submission examples use the existing October V1 chronology; successor uses the isolated March profile. Never show a current zero allocation merely because approval is pending. Queue columns are Budget/year, Review (Initial allocation/Allocation changes), Submitted by, Submitted, Status, Review. Opening Review writes no decision. Multiple responsibilities display permitted work together without a role switch. Finance stays in Planning.

### 11.2 BUD-DES-02 — Record approved allocation

Fixture: Josphat, Budget Officer, 1 Oct 2026 09:20 EAT. Heading **Record approved allocation**. Introduction **Enter the allocation approved outside KenTender and attach its approval document.** Financial year FY 2027/28 and Currency KES are visible record context; the explicit target year comes from the selected, revalidated native-year context. It grants no authority. If the Officer needs another year before creation, return to/change the existing year choice without creating a record; after first save the year is immutable. No Budget title input, duplicate PE or generated reference field before save.

| Label | Exact fixture |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-01 (Demo) |
| Approval date | 30 Sep 2026 |
| Approved allocation | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget 2027-28 (Demo).pdf |

Use the existing input/date/fixed-currency/single-file controls. One document only; file upload/link state is explicit. Footer Cancel / **Save and add budget lines**. Save requires these four values under §9.3 and creates the Budget/Version once before opening the line editor. No Submit before lines exist; no competing second Save button, extra evidence, author-name field, justification, effective date or generic attachment. Cancel before first successful save creates no Budget record; temporary upload ownership remains governed separately.

### 11.3 BUD-DES-03 — Draft Budget Lines editor

Fixture: Josphat, 1 Oct 2026 10:10 EAT, exact saved MOH-BUD-2027-001-V1. Heading **Record approved allocation**, Draft. Tabs **Approval details**, **Budget lines** selected (same existing Overview/lines route state). Secondary reference/version. Page actions **Save changes** / **Submit for review**; adjacent save-scope label **Budget lines**. No competing row-save command.

| Total | Value |
|---|---:|
| Approved allocation | KES 160,000,000 |
| Total entered | KES 160,000,000 |

Message **Budget lines match the approved allocation.** Unequal variants show the exact positive **Amount still to assign** or **Amount over allocation** instead of an unexplained signed Difference. Totals preview locally but server responses and decimal rules control; never automatically adjust a line to balance.

| Budget line | Available to | Funding source | Amount | Action |
|---|---|---|---:|---|
| Digital health infrastructure programme; secondary MOH-BL-DHI-2027 | Digital Health | Government of Kenya | KES 100,000,000 | Remove |
| Digital health workforce development; secondary MOH-BL-HWD-2027 | All departments | Government of Kenya | KES 60,000,000 | Remove |

Title, exact department/null eligibility, governed funding source and amount are the only editable line facts. Guidance **Which department may use this budget line?** No descendant expansion, inferred source OU or permission grant. Add budget line adds a pending editable row; generated ID is server-owned and shown only after persistence. Remove affects an eligible unsubmitted new line; it cannot delete historical approved identity or submitted-attempt evidence. A saved/returned Draft remains governed by first-submission rules.

Submit includes pending valid details and lines through §9.3; it is not a requirement to manually visit and Save each tab. Unsaved navigation offers Save changes / Discard unsaved changes / Stay here for the named scope, preserving the other scope's pending work. Discard never deletes previously saved or submitted evidence. No money-control action, accounting reference, purpose duplicate or notes.

### 11.4 BUD-DES-04 — Active Budget overview

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001**

**Page content header**

- Eyebrow: **MOH-BUD-2027-001 · VERSION 1**
- Title: **Ministry of Health procurement budget 2027/28**
- Status: **Current**
- No header action button

**Tabs:** **Overview** selected, **Budget Lines**, **Funding Activity**, **History**

**Funding position row — four equal cards**

| Card label | Value |
|---|---:|
| Registered allocation | KES 160,000,000 |
| Reserved for requisitions | KES 0 |
| Committed to contracts | KES 0 |
| Available to reserve | KES 160,000,000 |

**Budget context card**

| Label | Value |
|---|---|
| Financial Year | FY 2027/28 |
| Currency | KES |
| Current version | Version 1 |

**External approval card**

| Label | Value |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-01 (Demo) |
| Approval date | 30 Sep 2026 |
| Approved allocation | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget 2027-28 (Demo).pdf |

The Approval document value uses the approved quiet file-link style.

**Activation card**

| Label | Value |
|---|---|
| Submitted by | Josphat Mwangi |
| Approved and activated by | Beatrice Kamau |
| Activated | 3 Oct 2026, 11:15 EAT |

Do not show edit controls, Update registered allocation, an approval stepper or a Procuring Entity row on this artboard.

Each live funding position explicitly displays **Funding position as at [owner observation time]**. Registered allocation is the recorded ceiling; Reserved for requisitions is remaining holds; Committed to contracts is active obligations (v1.13: and the retained amount of closed contracts); Available to reserve is the unreserved/uncommitted balance. It is not cash received or money paid. Approved evidence and exact version/actor/time belong in structured supporting detail, not a repeated technical identity strip. A historical route uses its exact Version and declared instant; unavailable replay is not today's ledger.

### 11.4A BUD-DES-04A — Active Budget overview for Budget Officer

Duplicate BUD-DES-04.

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001**

Keep all BUD-DES-04 content unchanged and add one right-aligned primary page-header button: **Update registered allocation**.

Do not add Edit budget, Add line or Finance controls to this Officer-only variant. Budget Approver closure belongs to §11.18 under its existing authority; the Officer gains no close power.

### 11.5 BUD-DES-05 — Active Budget Lines

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Budget Lines**

Reuse the BUD-DES-04 page content header without changing its content or placement.

**Tabs:** **Overview**, **Budget Lines** selected, **Funding Activity**, **History**

**Budget Lines table**

| Budget Line | Available to | Funding source | Registered allocation | Reserved for requisitions | Committed to contracts | Available to reserve | Action |
|---|---|---|---:|---:|---:|---:|---|
| Digital health infrastructure programme · MOH-BL-DHI-2027 | Digital Health | Government of Kenya | KES 100,000,000 | KES 0 | KES 0 | KES 100,000,000 | View |
| Digital health workforce development · MOH-BL-HWD-2027 | All departments | Government of Kenya | KES 60,000,000 | KES 0 | KES 0 | KES 60,000,000 | View |
| Total | — | — | KES 160,000,000 | KES 0 | KES 0 | KES 160,000,000 | — |

Do not show an Allocation column, utilisation, cost centre, purpose, row menu or edit action.

**Implementation note:** reuse the existing components, updated consistently to this successor’s labels and actor rules, from the BUD-DES-04 header and tabs component and the Budget Lines table component as it renders in the BUD-DES-13 family's Budget Lines duplicate. Do not design new table chrome.

### 11.6 BUD-DES-06 — Budget Line detail

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 4 Dec 2026, 09:58 EAT · opened from the Active Budget Lines table · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BL-DHI-2027**

**Page content header**

- Eyebrow: **MOH-BL-DHI-2027**
- Title: **Digital health infrastructure programme**
- Status: **Current**
- No header action button

**Context strip**

| Label | Value |
|---|---|
| Budget | MOH-BUD-2027-001 · Version 1 |
| Financial Year | FY 2027/28 |

**Funding position row — four equal cards**

| Card label | Value |
|---|---:|
| Registered allocation | KES 100,000,000 |
| Reserved for requisitions | KES 0 |
| Committed to contracts | KES 0 |
| Available to reserve | KES 100,000,000 |

**Line identity card**

| Label | Value |
|---|---|
| Available to | Digital Health |
| Funding source | Government of Kenya |
| Current version | Version 1 |

**Active reservations section**

- Heading: **Active reservations**
- Empty-state title: **No active reservations**
- Empty-state body: **This Budget Line has no confirmed funding reservations.**
- No empty-state button

Do not show Confirm funding, Return, Release, Convert, Adjust, Edit, approval evidence or contract fields.

**v1.11:** when the line has an Open budget revision request, show one quiet line beneath the Line identity card: **Budget revision requested by Procurement Planning on {date}.** It carries no action on this page. The base fixture above has no request, so the line is absent.

### 11.6A BUD-DES-06A — Budget Line detail with two REQ reservations

Use conditional `BUD-SC-REQ-AUTH` in §15.4A at **16 Mar 2027, 10:15 EAT**, Naomi Chebet, Auditor. Reuse BUD-DES-06 shell; eyebrow `MOH-BL-HWD-2027`, title **Digital health workforce development**, owner **All departments**, Government of Kenya, Budget Version 1, FY 2027/28. This fixture is separate from the December pre-REQ screen.

| Card | Value |
|---|---:|
| Registered allocation | KES 60,000,000 |
| Reserved for requisitions | KES 50,000,000 |
| Committed to contracts | KES 0 |
| Available to reserve | KES 10,000,000 |

| Requisition / source | Reservation (secondary) | Plan Item | Originally reserved | Still reserved | Status | Action |
|---|---|---|---:|---:|---|---|
| REQ-MOH-2027-033-001 · HRMD source | RSV-MOH-2027-033-001 | PPI-MOH-2027-033 | KES 20,000,000 | KES 20,000,000 | Active | View Requisition |
| REQ-MOH-2027-033-001 · Digital Health source | RSV-MOH-2027-033-002 | PPI-MOH-2027-033 | KES 30,000,000 | KES 30,000,000 | Active | View Requisition |

Authorized secondary **View Plan Item** links preserve allocation context. No release, convert, adjust or Finance controls. Routes come from owner-authorized response data.

### 11.7 BUD-DES-07 — Funding Activity

Default: Naomi Chebet, Auditor, **10 Dec 2026, 15:05 EAT**, Budget Version 1. Reuse BUD-DES-04 header/tabs with **Funding Activity** selected. Filters **All Budget Lines** and **All funding events**. Show **No funding activity has been recorded for this budget.** No zero-value event, chart or Add action.

Conditional authorized-REQ variant: `BUD-SC-REQ-AUTH`, **16 Mar 2027, 10:15 EAT**. Header positions are approved KES 160m, reserved KES 50m, committed zero, available KES 110m. Show the following separate source rows. The exact recorded authorization time comes from the owning REQ event; the shared fixture defines 15 March but does not invent a more precise instant here.

| Date | Event | Budget Line | Requisition / reservation | Amount | Initiating actor |
|---|---|---|---|---:|---|
| 15 Mar 2027 | Requisition funding reserved | MOH-BL-HWD-2027 | REQ-MOH-2027-033-001 · RSV-MOH-2027-033-001 | KES 20,000,000 | Charles Mutiso, HOPF |
| 15 Mar 2027 | Requisition funding reserved | MOH-BL-HWD-2027 | REQ-MOH-2027-033-001 · RSV-MOH-2027-033-002 | KES 30,000,000 | Charles Mutiso, HOPF |

Footer **Showing 2 funding events**. Both are effects of one atomic authorization; audit also retains the calling service. Show business summaries and permitted owner links, not correlation IDs, before/after JSON, editable event rows or a Finance officer as the reserving actor.

### 11.7A BUD-DES-07A — Active Budget History

**Fixture context — outside the artboard:** Naomi Chebet · `naomi.chebet@moh.example.test` · Auditor · 10 Dec 2026, 15:05 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > History**

Reuse the BUD-DES-04 page content header without changing its content or placement.

**Tabs:** **Overview**, **Budget Lines**, **Funding Activity**, **History** selected

**Version history card**

| Date and time | Event | Actor |
|---|---|---|
| 3 Oct 2026, 11:15 EAT | Version 1 approved and activated | Beatrice Kamau |
| 1 Oct 2026, 16:20 EAT | Submitted for review | Josphat Mwangi |
| 1 Oct 2026, 15:55 EAT | Draft saved | Josphat Mwangi |
| 1 Oct 2026, 09:20 EAT | Budget Version 1 created | Josphat Mwangi |

Do not show funding ledger events, technical logs, comments, attachments or history from another Budget.

**Implementation note:** reuse the existing components, updated consistently to this successor’s labels and actor rules, from the BUD-DES-04 header and tabs component and the version-history table component as it renders in BUD-DES-07's Funding Activity event table — same row and column chrome, different event set.

### 11.8 BUD-DES-08 — Review allocation changes

Fixture: Beatrice, Budget Approver, 16 Mar 2027 10:15 EAT; exact submitted MOH-BUD-2027-001-V2, based on V1, isolated BUD-SC-REVISION with DHI 80m reserved and no HWD hold. Title **Review allocation changes**, budget/year name prominent; Transfer; Awaiting review; secondary reference/version. Submitted by Josphat, 15 Mar 16:20 EAT. Tabs Overview selected, Budget lines, Changes, History; decision footer stays on all tabs.

**What changed** leads the opening page:

| Budget line | Current allocation / V1 | Proposed allocation / V2 | Change |
|---|---:|---:|---:|
| Digital health infrastructure programme | KES 100,000,000 | KES 90,000,000 | − KES 10,000,000 |
| Digital health workforce development | KES 60,000,000 | KES 70,000,000 | + KES 10,000,000 |
| Total | KES 160,000,000 | KES 160,000,000 | KES 0 |

Summary **KES 10,000,000 moves from infrastructure to workforce development. The total allocation stays the same.**

**Amounts already reserved or committed**:

| Budget line | Reserved + committed | Available after update |
|---|---:|---:|
| Digital health infrastructure programme | KES 80,000,000 | KES 10,000,000 |
| Digital health workforce development | KES 0 | KES 70,000,000 |

Explanation **This amount must remain covered.** Label **Live funding position · 16 Mar 2027 10:15 EAT. KenTender checks these amounts again when you approve.** Submitted amounts stay fixed; refresh updates only the separately identified live observation. Full proposed line eligibility and funding source remain inspectable on this page in Budget line details: DHI/Digital Health/GoK and HWD/All departments/GoK.

**External approval** labelled facts: reference MOH-FIN-BUD-2027-02 (Demo); date 14 Mar 2027; Approved allocation KES 160,000,000; one exact **MOH Approved Procurement Budget Transfer 2027-28 (Demo).pdf**. Show **Open approval document** and an in-page preview where supported. Keep the actual submitted file identity; unsupported preview uses the exact file link, unavailable file shows an error. No invented PDF contents, forced download, opened-document checkbox or later Draft file substitution.

Supporting **Submission and history** retains exact submitter and events from §11.11. Material evidence changes from V1 to V2 are visible: external reference -01 → -02, approval date 30 Sep 2026 → 14 Mar 2027, and the baseline approval document → transfer document. The comparison must not imply only line amounts changed. No extra evidence attachment is added to the submission.

Footer **Return for correction** / **Approve allocation update**. Consequence **Approval makes these registered amounts current in KenTender. Existing reservations and commitments remain in place. This does not release cash.** No green readiness checklist, arbitrary tab tour, per-line acceptance, repeat generic confirmation or new Reject/Activate step.

Blocked variant, isolated from the 80m profile: proposed DHI 90m, live Reserved+Committed 95m. Banner **Infrastructure cannot be reduced to KES 90,000,000 because KES 95,000,000 is already reserved or committed. Shortfall: KES 5,000,000.** Approval unavailable; permitted Return stays. Do not show negative spendable availability, release holds or mark them Needs Attention to bypass the monetary floor. Missing live basis, stale Version, invalid evidence or unbalanced transfer uses the exact failure and prevents a positive decision.

### 11.9 BUD-DES-09 — Approval task · Budget Lines

**Fixture context — outside the artboard:** Beatrice Kamau · `beatrice.kamau@moh.example.test` · Budget Approver · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Approval tasks > MOH-BUD-2027-001-V2**

Reuse the BUD-DES-08 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Budget Lines** selected, **Changes**, **History**

**Submitted Budget Lines table**

| Budget Line | Available to | Funding source | Proposed amount | Reserved + committed | Available after update |
|---|---|---|---:|---:|---:|
| Digital health infrastructure programme · MOH-BL-DHI-2027 | Digital Health | Government of Kenya | KES 90,000,000 | KES 80,000,000 | KES 10,000,000 |
| Digital health workforce development · MOH-BL-HWD-2027 | All departments | Government of Kenya | KES 70,000,000 | KES 0 | KES 70,000,000 |
| Total | — | — | KES 160,000,000 | KES 80,000,000 | KES 80,000,000 |

Do not show inputs, Remove, Add Budget Line, classification, purpose or row actions.

### 11.10 BUD-DES-10 — Approval task · Changes

**Fixture context — outside the artboard:** Beatrice Kamau · `beatrice.kamau@moh.example.test` · Budget Approver · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Approval tasks > MOH-BUD-2027-001-V2**

Reuse the BUD-DES-08 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Budget Lines**, **Changes** selected, **History**

**Budget Line comparison card**

- Heading: **Changes from Active Version 1**

| Budget Line | Active Version 1 | Submitted Version 2 | Change |
|---|---:|---:|---:|
| Digital health infrastructure programme · MOH-BL-DHI-2027 | KES 100,000,000 | KES 90,000,000 | − KES 10,000,000 |
| Digital health workforce development · MOH-BL-HWD-2027 | KES 60,000,000 | KES 70,000,000 | + KES 10,000,000 |
| Total | KES 160,000,000 | KES 160,000,000 | KES 0 |

**Funding impact** uses the protected amounts and after-update positions in §11.8, with current observation time. If useful, secondary detail may show one affected reservation and no commitments. Keep an actual shortfall or failed evidence check prominent; do not make internal floor-breach counts the decision summary. Include the changed external approval reference/date/document alongside line changes; preserve exact baseline identity even if a later version becomes current.

Do not show unchanged identity fields, inline editing, per-row accept or reject controls, comments or a side-by-side document viewer.

### 11.11 BUD-DES-11 — Approval task · History

**Fixture context — outside the artboard:** Beatrice Kamau · `beatrice.kamau@moh.example.test` · Budget Approver · 16 Mar 2027, 10:15 EAT · Frappe header breadcrumb: **Home > Budget & Funding > Approval tasks > MOH-BUD-2027-001-V2**

Reuse the BUD-DES-08 page content header and fixed footer without changing their content or placement.

**Tabs:** **Overview**, **Budget Lines**, **Changes**, **History** selected

**Version history card**

| Date and time | Event | Actor |
|---|---|---|
| 15 Mar 2027, 16:20 EAT | Submitted for review | Josphat Mwangi |
| 15 Mar 2027, 15:55 EAT | Draft saved | Josphat Mwangi |
| 15 Mar 2027, 13:10 EAT | Successor Version 2 created | Josphat Mwangi |

Do not show comments, attachments, technical request logs, funding ledger events or history from another version.

### 11.12 BUD-DES-12 — Retired

BUD-DES-12 modelled the removed `Awaiting Activation` status as a second task screen for the Budget Activation Authority. That status and role no longer exist. BUD-DES-08 through BUD-DES-11 cover the single decision point, and **Approve** both decides and activates. Do not build a second task screen.

### 11.13 BUD-DES-13 — Review registered allocation, four tab variants

Fixture: Beatrice, 2 Oct 2026 10:00 EAT; exact submitted V1, inspection before the recorded 3 Oct activation. Heading **Review registered allocation**, FY 2027/28, Awaiting review; reference/version secondary. Submitter Josphat, 1 Oct16:20 EAT. Footer on all tabs **Return for correction** / **Approve registered allocation**. Consequence **Approval makes this recorded allocation current for KenTender procurement control. It does not approve the public budget or release cash.**

Overview puts the approved allocation KES 160m, complete two-line set and external evidence together:

| Budget line | Available to | Funding source | Submitted amount |
|---|---|---|---:|
| Digital health infrastructure programme · MOH-BL-DHI-2027 | Digital Health | Government of Kenya | KES 100,000,000 |
| Digital health workforce development · MOH-BL-HWD-2027 | All departments | Government of Kenya | KES 60,000,000 |
| Total | — | — | KES 160,000,000 |

Evidence: MOH-FIN-BUD-2027-01 (Demo); 30 Sep 2026; Approved allocation KES 160m; exact one MOH Approved Procurement Budget 2027-28 (Demo).pdf. Open approval document / supported preview; no required download or acknowledgement checkbox. Show actual missing/equality/configuration failures, not a green checklist. No Based on, Type of change, current floor, transfer balance or invented predecessor.

Budget lines tab repeats the same complete submitted set, not an unrelated Active table. Changes shows **Initial allocation. Review the complete submitted budget lines.** No empty previous-version column or comparison against zero. History retains V1 creation 1 Oct09:20, Draft saved15:55, submission16:20, all by Josphat; no successor or funding events. A returned/resubmitted variant must identify the exact submission attempt and full return reason, not overwrite this evidence. All tab reads bind to the exact submitted V1 attempt.

### 11.13A BUD-DES-13A — Retired

BUD-DES-13A modelled the same removed `Awaiting Activation` stage for Version 1. BUD-DES-13 covers the single decision point. Do not build a second task screen.

### 11.14 BUD-DES-14 — Successor revision draft · Overview

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 15 Mar 2027, 15:55 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Version 2 > Overview**

**Page content header**

- Eyebrow: **MOH-BUD-2027-001 · VERSION 2**
- Title: **Update registered allocation**
- Status: **Draft**
- Right-aligned secondary button: **Save changes**
- Right-aligned primary button: **Submit for review**

**Tabs:** **Approval details** selected, **Budget Lines**

**Version context card**

| Field label | Displayed value |
|---|---|
| Financial Year | FY 2027/28 |
| Currency | KES |
| Based on | Active Version 1 |
| Type of change | Transfer |

The first three rows use approved read-only components. Type of change uses the approved select component.

**External approval card**

| Field label | Displayed value |
|---|---|
| Approval reference | MOH-FIN-BUD-2027-02 (Demo) |
| Approval date | 14 Mar 2027 |
| Approved allocation | KES 160,000,000 |
| Approval document | MOH Approved Procurement Budget Transfer 2027-28 (Demo).pdf |

Approval reference uses an input; Approval date a date component; Approved allocation a KES currency input; Approval document one file component showing the exact filename.

Show **The current allocation stays in use until this update is approved.** Save scope is Approval details; Type of change retains the four existing enum options. The immutable year/currency and fixed baseline remain secondary read-only facts. No extra change reason, justification, source type, effective date, notes or PE row.

### 11.15 BUD-DES-15 — Successor revision draft · Budget Lines

**Fixture context — outside the artboard:** Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 15 Mar 2027, 15:55 EAT · Frappe header breadcrumb: **Home > Budget & Funding > MOH-BUD-2027-001 > Version 2 > Budget Lines**

Reuse the BUD-DES-14 page content header without changing its content or placement.

**Tabs:** **Approval details**, **Budget Lines** selected

**Line total strip**

| Label | Value |
|---|---:|
| Approved allocation | KES 160,000,000 |
| Total entered | KES 160,000,000 |
| Match | Budget lines match the approved allocation. |

**Editable successor lines table**

| Budget line | Reference (secondary) | Available to | Funding source | Current allocation | Proposed amount | Change |
|---|---|---|---|---:|---:|---:|
| Digital health infrastructure programme | MOH-BL-DHI-2027 | Digital Health | Government of Kenya | KES 100,000,000 | KES 90,000,000 | − KES 10,000,000 |
| Digital health workforce development | MOH-BL-HWD-2027 | All departments | Government of Kenya | KES 60,000,000 | KES 70,000,000 | + KES 10,000,000 |

Budget line name/reference, Available to, Funding source, Current allocation and Change use approved read-only components. Proposed amount uses a KES currency input.

Below the table, left-aligned secondary button: **Add Budget Line**.

Do not show a destructive Remove action on protected historical lines. A permitted **Omit from this update** action is separate: only when current remaining reservation and active commitment are zero (v1.13: and no Closed commitment amount is retained, BUD-BR-031), under BUD-BR-020, and with the same guard rechecked at activation. Retain all historical line/Version/event identities. DHI with the 80m hold cannot be omitted; an eligible HWD omission would also require a valid revised total/type and approval instrument, not silent rebalancing of this Transfer. New Draft-only lines use the existing removal rule. No classification, duplicate purpose, financial-control buttons or notes.

Keep **Total moved out: KES 10m** / **Total moved in: KES 10m** for this Transfer. Existing title, Available to and funding source remain read-only; a different identity requires Add budget line. Exact original references remain secondary; the name and proposed amount lead. Save scope is Budget lines; Submit follows §9.3, including pending valid details on the other tab.

### 11.16 BUD-DES-16 — Workspace state variants

Four static variants. Resolve authorization first. Authorized Loading, No baseline and Server error may use the BUD-DES-01 header/filter; Forbidden renders only its inline panel, with no Budget page header, filters or protected content. Do not show position cards or Budget Line rows unless stated. State treatments follow KT-STD-001 §3.

Fixture context for Loading, No baseline and Server error — outside the artboard: **Josphat Mwangi · `josphat.mwangi@moh.example.test` · Budget Officer · 1 Oct 2026, 09:00 EAT**. Fixture context for Forbidden — outside the artboard: **Samuel Otieno · `samuel.otieno@moh.example.test` · No Budget responsibility · 1 Oct 2026, 09:00 EAT**. Frappe header breadcrumb for all variants: **Home > Budget & Funding**.

| Variant | Main content | Buttons |
|---|---|---|
| Loading | One full-width skeleton Current budget card followed by four skeleton position cards and two skeleton table rows | None |
| No baseline | Heading **No procurement allocation has been recorded for FY 2027/28.** Body **Record the externally approved allocation for this financial year.** | **Record approved allocation** |
| Server error | Heading **Budget & Funding could not be loaded.** Body **Try again. If the problem continues, contact KenTender support.** | **Try again** |
| Forbidden | Heading **You do not have access to Budget & Funding.** Body **This area needs one of these responsibilities: Budget Officer, Budget Approver, Finance Confirmation Officer or Auditor. Ask your KenTender administrator to assign one in System setup.** | None |

**Correction.** Forbidden is a business-role check; it is not the same check AUTH-ADR-001 §8 grants Administrator and System Manager. A technical reader holding neither a Budget business role nor a Budget business action never reaches this state — the workspace resolves for them per BUD-DES-01A instead. Samuel Otieno, this variant's fixture, has no Budget responsibility *and* is not Administrator or System Manager; Forbidden is what an ordinary user with no assignment sees, never what a technical reader sees.

### 11.17 Existing Frappe, KenTender and Planning controls

No artboard is authorised for the Frappe header, breadcrumb, module menu, global page chrome, notifications or user menu. Reuse those without visual modification, per KT-STD-001 §2.5.

The Finance task, sufficient and insufficient states, return dialog and planner-waiting state are defined by Procurement Planning. Do not reproduce or redesign them here.

---

### 11.18 BUD-DES-17 — Close budget, existing Approver command

This adds a missing state composition on existing BUD-UI-03; no new route, task, role or lifecycle. An Active Budget's authorised Approver can inspect year-end closure eligibility. Before the year ends, display **This budget can be closed only after [actual FY end date].** No override. After year-end, the relevant ready/blocked/unavailable state is visible.

| Condition | Content / action |
|---|---|
| Remaining hold | This budget cannot be closed yet. [Exact amount] remains reserved for requisitions. Show affected Budget lines and permitted reservation/owner links; Check again / Back to budget. Approval is not an alternative release action. |
| Unknown hold check | The funding position could not be checked. Try again before closing this budget. Never treat unavailable as zero. |
| Year ended, no remaining reservations | Closing stops new reservations, conversions and commitment increases. Existing commitments and history remain. Offer Close budget. Active commitments alone do not block. |
| Confirm requested closure | Close budget for FY [year]? Display exact Budget/year, above consequence, Cancel / Close budget. Focused confirmation, no extra approval stage or reason field. |
| Closed | Closed; exact actor/time/year; retained commitments, ledger and historic evidence. No new holds/conversions/increases. Owner-authorised existing commitment decreases/cancellations remain possible. (v1.13: for a Closed commitment, only an approved Budget correction.) |

Proposed isolated blocked fixture: 1 Jul 2028 after FY 2027/28 ends; DHI KES 20m remaining reservation, actual owner event/authority/time declared in executable profile. Show **KES 20,000,000 remains reserved for requisitions. Resolve the remaining reservations through their owning Requisition or Contract process, then check again.** Needs Attention counts as reserved. No Release button or manufactured owner task. Ready fixture starts separately with no remaining hold and optionally KES 60m active commitments; it must not erase the blocked profile's hold to force success.

### 11.19 BUD-DES-06B — Partial conversion and a reservation requiring review

Separate BUD-SC-CONVERT-PARTIAL profile, exact current owner observation time supplied at runtime. DHI line: registered allocation100m, originally reserved80m, converted60m, remaining reserved20m, active committed60m, available to reserve20m. Explain **KES 60,000,000 of the reservation is now committed to a contract. The remaining reservation is KES 20,000,000. No payment is recorded here.** Supporting reservation evidence: original80m = remaining20m + converted60m + released0. Commitment decrease does not replenish the hold or change its conversion history.

Rows lead with Requisition and source department, then exact original/still-reserved amounts; reservation IDs secondary. For Needs Attention use **Requires review — funds remain reserved**, full actual translated reason, responsible owner and authorised next-record link. No expiry promise, automatic release or local repair task. Where the approved owner facility is not implemented, state the supported limit and retain the financial restriction.

The two HWD reservations in BUD-DES-06A remain separate20m/30m with exact source lineage; do not merge their IDs into one generic hold. Funding activity shows business effects; Budget history shows version/submission/decision events. No manual release, conversion, adjustment, financial event entry or invoice/payment field.

### 11.20 Common readable supporting detail and error treatment

Use labelled amounts, source/department facts and short explanations; right-align comparable Money with visible currency. Material blockers remain outside collapsed History. Complete reasons, references and document facts wrap, with keyboard-accessible full reading. Narrow-screen composition preserves line name, relevant amount and decision result; no forced download or carousel of mandatory tabs.

Known failure, partial success, pending/unknown result and historical unavailable are distinct. Error summaries identify the actual field/line and exact amount still to assign, amount over allocation or shortfall. Use supported CurrencyBasis scale in messages, never guessed cents. Maintain focus/error announcements and preserve only still-authorised unsaved data. Access denial resolves before headers/filters/protected placeholders; technical read is a separate authorised outcome, not an ordinary no-assignment denial.

### 11.21 BUD-DES-18 and BUD-DES-19 — Budget revision request (v1.11)

**BUD-DES-18 — Budget revision request row.** A variant of the BUD-DES-01 workspace for the Budget Officer, per the §11.1B row added in v1.11.

**Fixture context — outside the artboard:** Josphat Mwangi · Budget Officer · 15 Dec 2026, 10:30 EAT · Budget `MOH-BUD-2027-001` Version 1 Active since 3 Oct 2026 · profile BUD21-SC-REVISION-REQUEST (§15.8) · Frappe header breadcrumb: **Home > Budget & Funding**.

Same page content header, filter row, Current budget card, funding position and Budget Lines preview as BUD-DES-01. Between the Current budget card and the funding position, one task row:

- Title: **Budget revision requested for Digital health workforce development**
- Narrative: **Procurement Planning's plan update needs KES 62,000,000 on this line. The registered allocation is KES 60,000,000, so it is over by KES 2,000,000. An increase needs external approval before you record it as an allocation update.**
- Muted facts on one line each: Requested by **Mercy Kilonzo, Procurement Planner**; Requested **15 Dec 2026, 10:00 EAT**; Plan **PLN-MOH-2027-001, Version 2**.
- Primary action: **Update registered allocation**. Secondary action: **Decline request**.

No count badge, card per fact or second task list. The row states the request once; the Budget Lines preview is unchanged.

**BUD-DES-19 — Decline request dialog.** 520 px dialog over BUD-DES-18. Heading **Decline this budget revision request?** Facts: line **Digital health workforce development**; over by **KES 2,000,000**; requested by **Mercy Kilonzo**. Required multiline **Reason for declining**, 10–500 characters, blank at open. Text beneath: **The plan update stays over budget. Procurement Planning will see your reason.** Footer **Cancel** / primary **Decline request**, disabled until the reason is valid.

**Funding fixture segregation.** In all new D21/D22 entry branches, Ruth Achieng confirms the opening/funding basis under a separate CM Finance approval assignment and required native rights, Josphat prepares the Budget entry, and Beatrice approves it. Existing Evaluation membership grants Ruth no CM rights. The same-confirmer variant attempts approval by Ruth and is refused even if she separately holds Budget Approver; display **Another Budget Approver must review this funding entry.** The recorder/Approver correction variants retain their separate two-person rule; they do not invent a Finance confirmation where no funding basis is used.

### 11.22 Closed correction and contract funding — current v1.16

These briefs are complete closed visual input for the new surfaces. Inherit KT-STD v1.30 §2 and the existing Budget shell; no ledger/account fields or new global navigation. Source links are authorised disclosures, not editable identifiers. Technical readers get the same permitted values without editor/decision actions. Pending work is added to BUD-DES-01B’s existing work list, not another queue: title, contract reference, current holder/status and Open; no KPI cards.

**Shared isolated fixture.** Use existing people Josphat Mwangi (Budget Officer), Beatrice Kamau (Budget Approver), Ruth Achieng (separately assigned CM Finance approver for the opening basis) and Charles Mutiso (HOP), each in the stated capacity. The contract is CM’s existing isolated `CM-MOH-2027-EXT-001`, Afya Digital Supplies Limited. For entry examples, original contract KES 1,000,000; prior-year supported work KES 400,000; confirmed target-year funding charge KES 600,000; existing target-year Budget coverage KES 100,000; uncovered charge KES 500,000. The evidence explicitly reconciles 400,000 + 600,000 to the contract total. The 100,000 coverage is a real isolated Budget commitment linked to this scope, never inferred from a paid invoice. Funding rows are HWD KES 300,000 and its second same-year, same-source, Entity-wide line titled **IT support equipment** KES 200,000. Both use the already configured Government funding source; source OU Digital Health. In the isolated entry branch A=1,000,000 on each line, R=0; before entry C=100,000 on HWD and 0 on the second line, hence V=900,000/1,000,000; after entry C=400,000/200,000 and V=600,000/800,000. This is a proposed isolated fixture, not a change to canonical allocations. All other lines remain outside this example.

**BUD-DES-20 — Correct commitment; Form/editor then decision variant.** Existing line detail offers Correct commitment only to the Officer for a Closed commitment. Isolated correction uses CM-MOH-2027-CLOSE-001: retained amount KES 1,000,000, supported correction KES 800,000, reason **Unperformed amount included in final obligation**, evidence **Final obligation review 1** and **Closure 1**. Officer sees title Correct commitment, next step Your turn — Record the supported correction; read-only contract, Closed status, original amount; editable corrected amount, reason and evidence selection; calculated reduction KES 200,000; primary **Submit correction**, secondary Cancel. Approver variant shows the exact saved comparison and Josphat as recorder; primary **Approve correction**, secondary **Return for correction** (reason required). Approved variant shows KES 800,000, reduction KES 200,000, recorder and Beatrice as approver; View history and Open contract only. Closed-year variant adds **This financial year is closed. The correction does not authorise spending.** A same-person variant omits approval and explains **Another Budget Approver must decide this correction.** Stale variant preserves input and explains **The commitment has changed. Review the current amount.** No journey tracker is needed for this short correction record.

**BUD-DES-21 — Contract funding; Form/editor.** Josphat’s pending-work row has Task **Fund existing contract**, Reference **CM-MOH-2027-EXT-001**, and Status **Ready to prepare**. The reference may sit beneath the task title; status is distinctly labelled. Page title Contract funding; next step Your turn — Allocate KES 500,000 to budget lines. First region: contract/supplier, confirmed target-year charge 600,000, already covered 100,000 and amount requiring funding 500,000. Named disclosures **Opening review and source evidence** and **Existing budget coverage** expose the evidence and commitment referenced above. Allocation table has Budget line, Available, Amount and Remove; source/year are read-only supporting detail. Exact two rows use the figures above; calculated Total 500,000 and Remaining to allocate 0. Required reconciliation text: **Existing funding checked against the confirmed current-year charge.** Primary Submit for review; secondary Save draft and Decline request. Add budget line selects eligible lines; it adds a row, not a separate request. Entry state label Draft. No currency picker or total override.

**BUD-DES-22 — Review contract funding; Review/decision.** Beatrice sees the same source and rows frozen, Josphat as submitter and the before/after positions above. Next step Your turn — Review the funding entry. Primary Approve funding entry; secondary Return for correction and Open contract. Confirmation dialog repeats total KES 500,000 and two lines; Confirm approval/Cancel. Approved variant shows Funding entry approved and commitment references per row, with View history/Open contract. No new confirmation action after approval. Same-person variant explains another Approver is needed and offers no approval.

**Required variants of D21/22.** Missing year basis: Status **Year allocation required**; Next work **Waiting for Finance**, holder Ruth Achieng under her separately provisioned CM Finance approval assignment, action Open contract review; retain Draft values and Save draft, no Submit/Approve. Shortfall: second line available 150,000 against request 200,000, shortfall 50,000; show Status **Funding shortfall** and Shortfall **KES 50,000**, Officer holder; no successful commitments; actions Edit allocation / Update registered allocation / Open contract (as permitted), no arbitrary override. Returned: exact return reason **Confirm the source allocation**, Officer holder, editable Draft and resubmit. Changed basis: **The opening review has changed. Return this entry for an updated allocation.** No approve. Zero charge after coverage: **Already covered — no new entry required**, exact verified coverage disclosure, View history/Open contract; no zero-row submission. Unsupported year/currency: **This funding is outside the supported scope**, named issue and Open contract; factual Draft remains. Service failure has its actual unavailable message and retry owner, never an empty success.

**Fixture execution.** Obtain generated IDs from the real owner builders; labels above are display references, not guessed database IDs. Reuse the actor identities but provision only the separate assignments actually needed. Use runtime seed anchor T and instants T−30 minutes (opening confirmation), T−20 (request), T−10 (submit), T−5 (decision), never future instants. Bind the isolated target Budget year to the anchor’s configured active financial year; its contract display reference is not a date rule. Do not alter native Fiscal Year dates or silently shift existing canonical fixtures. Existing SEED-002 governs production/demo reset chronology; this relative isolated branch does not claim that its latest source was supplied or executed.

## 12. Functional interaction requirements — excluded from design prompts

Common page behaviour and accessibility follow KT-STD-001 §3.

### 12.1 BUD-UI-01 — Workspace

- The workspace resolves the existing Budget root, initial pending Version, current Version and open successor for the selected fiscal year; apply the complete §11.1B state matrix. It never chooses the first Budget or the first year.
- The Financial Year select is a local view filter. It grants nothing, is remembered only with a visible reset, and is ignored when stale or invalid.
- One Active Budget returns its exact version and derived positions. A Draft successor does not replace or alter the Active projection.
- Counts and rows use the same server-side predicate as direct routes and services.
- **Record approved allocation** appears only when the selected year has no Budget and the actor holds an Active Budget Officer assignment.
- **View budget** opens the exact server-returned `budget_id`.
- **Update registered allocation** comes only from the server's `available_actions`.
- **Correction.** Where a Draft or Submitted-for-approval version exists for the selected year and the caller holds AUTH-ADR-001 §8 technical read with no matching Budget business assignment, the server returns a fourth outcome for that version — **View version (read-only)** — instead of nothing. It opens BUD-UI-02's route with every mutation control removed or disabled, never a 404. See BUD-DES-01A.
- Loading never shows zero balances. Forbidden and failure states disclose no out-of-scope Budget IDs, titles, lines or amounts.
- **v1.11:** the workspace read returns each Open budget revision request for a Budget Officer, with its available actions. **Update registered allocation** on a request invokes `create_budget_successor_version` with the request ID and opens the created or reused successor in BUD-UI-02. **Decline request** opens BUD-DES-19 and invokes `decline_budget_revision_request`; on success the row disappears and the outcome is published. The row clears only on the request's outcome, never on view. A closed request answered in another session returns `BUDGET_REVISION_REQUEST_CLOSED` and the row refreshes.

### 12.2 BUD-UI-02 — Version editor

- **Correction.** For Administrator and System Manager, this route resolves for any version status — including Draft and Submitted for approval — and returns the same content and lines a Budget Officer would see while drafting, with every field read-only (`can_edit: false`) and no business assignment required, per AUTH-ADR-001 §8. This is the route BUD-DES-01A's **View version (read-only)** opens. It is not a new route; it is this same one, already correctly authorising a technical reader before this correction — only never reachable from anywhere in the specified UI, and never documented as doing so.
- Saving the initial Draft creates the Procurement Budget and Version and returns generated references. The fiscal year and currency become immutable.
- Initial Overview edits only `approval_reference`, `approval_date`, `authorised_total` and one `approval_document_file_id`; a successor also has its existing `revision_type`. First-save and submit prerequisites, file outcomes and named save scopes are explicit in §9.3.
- The document component permits one current file. Replacing it in Draft removes the old Draft link; submitted evidence is retained in the version snapshot.
- Line create and update accept only title, owner scope, funding source and approved amount. Generated line IDs are not editable.
- Available-to choices are Active Organisation Units. Funding-source choices come from the governed catalogue.
- Draft line total and difference are server-calculated after every save response. The client may preview them but cannot submit calculated totals.
- Remove only a permitted unsubmitted new line. Do not delete previously Active or submitted history or change its identity. Omit from this update means exclusion from the proposed Version only under BUD-BR-020: no remaining reservation or active commitment (v1.13: and no Closed commitment amount), rechecked at approval, preserved history/line IDs and all total/type/evidence guards.
- **Submit for review** first saves pending valid scopes through §9.3, then submits the confirmed exact Version. The submit command alone locks/reloads the Draft and applies all readiness rules atomically. Saved scopes survive a later failure; no false atomic multi-save assertion.
- Failed readiness returns structured failing rules, keeps the Draft editable and focuses the first failing field or line.

### 12.3 BUD-UI-03 — Budget workspace

- Current Overview and Budget Lines use the Active Version and coherent ledger snapshot at response `as_at`. Explicit historical selection uses the exact retained Version and declared instant; show **Historical funding position** and its time. Never combine old approved amounts and live holds as a single historical position.
- The selected tab is represented in the URL. Back and forward change the tab without changing the Budget or mounting another page application.
- Active, Superseded and Closed versions are read-only.
- Budget Lines returns only stored identity values and derived positions. It infers no classification or expenditure data.
- Funding Activity is reverse chronological and server-filtered. Filtering grants no additional access, and the table shows business event summaries only.
- History contains version lifecycle events only; it does not duplicate the funding ledger.
- **Update registered allocation** creates one server-side copy of the Active Version, preserving line IDs and values, and opens its Draft Overview. A second open successor is rejected and the existing Draft route is returned.

### 12.4 BUD-UI-05 — Budget Line detail

- The route authorises the actor's responsibility and the exact line before returning its title, owner, funding source, positions or reservations.
- A Planning Finance task passes a line ID only. Budget independently authorises the actor and never trusts Planning route visibility as Budget authority.
- The default line page labels the current live position and observation time; it does not freeze to the Finance snapshot. Explicit historical mode follows §9.1 and labels the historical Version/instant.
- Before REQ authorisation, the page shows no hold from that draw even if a Planning Finance review shows planned amounts.
- After REQ authorisation, active reservations show each drawdown-line reservation, REQ/source and Plan Item references, original/remaining amounts and status, read-only, as in BUD-DES-06A.
- **View Plan Item** uses a server-returned authorised Planning URL. The Budget client does not build a route from a guessed naming rule.
- Opening or closing the page creates no check, reservation, decision or ledger event.

### 12.5 BUD-UI-04 — Approval task

- Business task review/decisions require an Active Budget Approver assignment. AUTH v1.7 §8 permits Administrator/System Manager to inspect the exact task and all submitted evidence read-only without that assignment; no mutation controls. Ordinary neutral/consumer read alone grants no workflow-task access.
- All four tabs always read the submitted `budget_version_id`; no tab substitutes the current Active Version.
- Overview leads with the complete initial allocation or successor changes, exact approval evidence and separately observed live protection results. Submitted identity/amounts never change when live balances refresh; actual failed checks are prominent and full evidence remains accessible.
- Budget Lines returns the complete submitted line set and current floors calculated at task-read time.
- Changes is calculated server-side against `based_on_budget_version_id`. Version 1 returns the explicit initial-baseline state and never invents a predecessor.
- History returns only events for the submitted version, in reverse chronological order.
- The decision footer remains available on every tab; every command carries version ID, expected status and expected record version.
- Return or Approve are available only while status is Submitted for approval. Return opens **What needs to change?** with **Correction required**, Cancel and Return for correction, validated at 10–500 characters. Preserve the exact immutable submission-attempt snapshot and document before editing the same Draft.
- Approve reruns evidence, totals, line identity, floor, transfer, responsibility and concurrency checks under transaction locks and activates in the same transaction. There is no separate later activation step.
- A failed live guard leaves the version Submitted for approval and returns the exact failed rule. No line, status, reservation or ledger position changes.
- The Budget Officer who submitted a version cannot approve it, enforced from the version's own submission audit event.

### 12.6 Procurement Planning Finance boundary

Planning owns Finance task discovery, whole-Plan comparison, insufficient-approved and available-funds-advisory states, Return, repeat review, current funding reassessment and original-versus-current evidence. Use PLN v1.18's compositions; Budget adds no Finance screen or decision.

Budget independently checks authorized caller/decision context before returning protected positions. **Check affordability** uses the nonlocking display contract. An affirmative Finance command uses §8.2A within the Planning transaction and creates **no reservation**. Above-approved or stale basis prevents a positive decision; exceeding current availability is advisory when the Plan remains within approved amounts. Finance Return records its reason in Planning only. Repeated Finance decisions use Planning's idempotency and evidence history, never Budget reservation IDs.

A Finance user may open the exact Budget Line through the authorized returned route. The line shows **current funding position — as at [time]**; it does not replace the frozen comparison in the Finance review. Navigation creates no decision or ledger event. `reserve_funding` rejects a Planning caller even when the user also holds Finance Confirmation Officer.

### 12.7 Additional page states

- A fiscal year with no Budget shows the no-baseline state and no zero-value funding position.
- An Active Budget with no funding events shows **No funding activity has been recorded for this budget.** and no Add action.
- A filter with no matching events provides **Clear filters**.
- Forbidden responses disclose no record names, counts, amounts or task details.

---

### 12.8 Year-end closure and current observations

Close budget is available only through the existing Budget Approver authority and close_budget command. Inspect and show server-derived year-end/current-status/remaining-reservation facts. Before year-end or with any positive remaining hold, including Needs Attention, no positive close may commit. Unavailable evidence is not clearance. After year-end and zero remaining holds, focused confirmation leads to commit-time revalidation under compatible locks. Existing active commitments alone do not bar closure; decreases/cancellations after closure remain in the Contract owner contract, not a Budget UI adjustment. (v1.12 read as stated. v1.13: a decrease of a Closed commitment after closure is a Budget correction under BUD-BR-034, recorded and approved by two different people. The contract owner's call cannot change a Closed commitment, BUD-BR-033.) Closed means no new holds, conversions or obligation increases, never payment or release.

Current and historical observations are timestamped separately. Data refresh or Check again creates no business/ledger effect. Unknown close/approval outcomes resolve the original idempotency identity before another attempt. After success show exact closure evidence and retain the authorised history; after a stale or failed guard show the actual still-current result.

## 13. Error contract

| Code | Required service result | User-facing explanation / recovery |
|---|---|---|
| `BUDGET_RESPONSIBILITY_REQUIRED` | You are not assigned the responsibility required for this action. No protected data is returned. | You are not assigned the responsibility required for this action. Ask your KenTender administrator to check your assignment. |
| `BUDGET_CONFIG_MISSING` | A referenced organisation unit, financial year, currency or funding source is unavailable. The operation fails closed. | The required setup is unavailable. Name the actual missing year, department, funding source or currency setting and direct the user to the KenTender administrator. |
| `BUDGET_ALREADY_EXISTS` | This financial year already has a procurement budget. Return its authorised route; create nothing. | An allocation record already exists for this financial year. Open it to continue where authorised. |
| `BUDGET_INVALID_STATE` | The command is not valid for the current server status. Current status is returned. | This budget has changed. Refresh to see the available actions. |
| `BUDGET_NOT_READY` | Submission or approval readiness failed. Structured failing rule IDs are returned. | Complete the highlighted details before submitting or approving. Focus the actual field or line. |
| `BUDGET_APPROVAL_EVIDENCE_REQUIRED` | Approval reference, date, document or authorised total is absent or invalid. | Complete the approval reference, date, allocation amount and approval document. Identify the missing or invalid value. |
| `BUDGET_TOTAL_MISMATCH` | Budget Line total does not equal the authorised total. No status changes. | Budget lines do not match the approved allocation. Show Amount still to assign or Amount over allocation with the exact difference. |
| `BUDGET_LINE_NOT_ELIGIBLE` | The line is missing, inactive or incompatible with the allocation's owner scope or funding source. | This budget line is not available for the selected source department or funding source. Show only authorised eligibility detail. |
| `BUDGET_LINE_IDENTITY_IMMUTABLE` | A successor attempted to change title, owner scope or funding source on an existing Active line. | Add a new budget line for the changed purpose, department or funding source. The existing approved line cannot be changed in this way. |
| `BUDGET_CONTEXT_NOT_FOUND` | No applicable Active procurement budget exists for that financial year. No line is selected. | No current procurement allocation is available for this financial year. Show existing pending work where authorised, not a zero balance. |
| `BUDGET_FINANCE_TASK_DENIED` | The caller does not hold the live Finance task responsibility. No protected position is returned. | You cannot act on this Finance review. Open the authorised review in Procurement Planning or ask your administrator to check your assignment. |
| `BUDGET_CHECK_STALE` | The REQ/Plan source set, owner revisions, token expiry or funding basis changed after Check Funding. Refresh; no reservation is created. | The funding check is no longer current. Refresh and check again before authorisation; no funds were reserved by this failed attempt. |
| `BUDGET_INSUFFICIENT_FUNDS` | One or more allocations lack full availability. Per-line shortfalls are returned; no reservation is created. | There is not enough available funding for this authorisation. Show the exact shortfall for each affected line; nothing is partially reserved. |
| `BUDGET_RESERVATION_CONFLICT` | This authorisation/drawdown line is already reserved, or an idempotency key is reused with a different payload. No duplicate or replacement is created. | This authorisation already has funding reserved, or the repeated request differs from the original. Show the actual result and preserve original reservations. |
| `BUDGET_REVISION_FLOOR_BREACH` | A proposed line amount is below current Reserved plus Committed. Approval is blocked. | This budget line must cover the amount already reserved or committed. Show proposed amount, protected amount and exact Shortfall. |
| `BUDGET_TRANSFER_UNBALANCED` | Transfer increases and decreases do not balance. Submission or approval is blocked. | The amounts moved out and moved in must match. Show both totals and the exact difference. |
| `BUDGET_CONVERSION_EXCEEDS_REMAINDER` | Contract conversion exceeds the reservation remainder. No commitment changes. | The proposed contract amount exceeds the remaining reservation. Review it in the owning Contract process; no commitment was changed. |
| `BUDGET_COMMITMENT_INCREASE_UNFUNDED` | A proposed commitment increase lacks available funds. No adjustment occurs. | There is not enough available funding for this commitment increase. Return the exact shortfall to the owning Contract action. |
| `BUDGET_CLOSED` | The budget is closed and cannot accept a new reservation. | This budget is closed. New reservations, conversions and commitment increases are not permitted. |
| `BUDGET_STALE_WRITE` | The expected record version is stale. No newer data is overwritten. | This budget has changed since you opened it. Refresh to see the current details; do not overwrite newer saved work. |
| `BUDGET_DOWNSTREAM_FORBIDDEN` | A downstream caller attempted an unsupported Draft read or direct mutation. | This information or action is not available through this request. Do not expose protected data or provide a manual bypass. |
| `BUDGET_DECISION_BASIS_STALE` | Expected Budget/line/eligibility evidence changed. Positive caller decision rolls back; refresh the affordability comparison. | The allocation or its eligibility details have changed. Refresh the Planning comparison before confirming; no positive decision was saved by this failed command. |
| `BUDGET_PLAN_EXCEEDS_APPROVED` | Planned totals exceed approved amounts; authorized caller receives exact per-line excess. No positive decision. | The Plan exceeds the approved allocation. Show the exact approved-versus-planned excess in the Planning review. |
| `BUDGET_MONEY_PRECISION_INVALID` | Amount is malformed, over scale/range or has missing/unsupported currency precision. Reject without rounding. | Enter an amount within the supported size and decimal-place limit. Show the verified currency scale; unavailable precision requires setup recovery, not a guessed default. |
| `BUDGET_SOURCE_OU_REQUIRED` | A real explicit source department is absent or unresolved. Do not infer it from the user. | The source department is missing or unavailable. Complete the source in its owning Planning or Requisition record; do not infer it from the user. |
| `BUDGET_HISTORICAL_BASIS_UNAVAILABLE` | Exact requested historical Version/position cannot be reproduced. No current-data substitution. | The funding position for this version and time is unavailable. Do not substitute the current position. |
| `BUDGET_IDEMPOTENCY_CONFLICT` | Same command key has a different immutable payload. Return no new effect. | This request differs from the original attempt. Check the original result before retrying; no new effect was created. |
| `BUDGET_REVISION_NOT_REQUIRED` (v1.11) | Planning's planned amount does not exceed the line's current approved amount. No request is recorded. | This budget line already covers the planned amount. No budget revision is needed. |
| `BUDGET_REVISION_REQUEST_CLOSED` (v1.11) | The request is no longer Open. No change. | This budget revision request has already been resolved. Refresh to see its outcome. |
| `BUDGET_STALE_REVISION` (v1.13) | The commitment changed after the caller read it, or after a correction was recorded. Nothing changes. | The commitment changed after it was read. Review its latest amount before continuing. |
| `BUDGET_COMMITMENT_AMOUNT_MISMATCH` (v1.13) | The owner outcome's final obligation differs from the commitment's current amount. Nothing is adjusted implicitly. | The owner outcome's final obligation does not equal the commitment's current amount. Review the contract's final position before closing. No amount was changed. |
| `BUDGET_POSITION_CHANGED` (v1.13) | Closing or correcting would have changed a line's position in a way the rule forbids, so the change is rolled back. An internal safeguard, not an expected outcome. | The Budget position would have changed unexpectedly. Nothing was saved. |
| `BUDGET_INVALID_STATE` (v1.13) | The record is not in a state that allows the call, for example a closure of a commitment that is not Active or is already Closed by a different outcome, any adjustment of a Closed commitment, a correction that does not lower the amount or targets a commitment that is not Closed, a second correction awaiting approval, or a correction already decided. Already returned by the build for the first group and first listed here. No change. | This action is not available in the record's current state. Nothing was changed. |
| `BUDGET_EVIDENCE_REQUIRED` (v1.13) | A correction came without evidence, a Contract Management reference or a reason of the required length, or a return came without a reason. Nothing is recorded. | Add the missing evidence, Contract Management reference or reason before continuing. Show which one is missing. |
| `BUDGET_RESERVATION_NOT_AUTHORISED` (v1.14) | The chain in the conversion event does not match the reservation's own lineage, no chain was supplied, or no funding owner confirms the contract may draw on the reservation. Nothing is converted. | This reservation is not one of the reservations awarded to this contract, or no funding owner confirms which reservations the contract may draw on. Nothing was committed. |
| `BUDGET_ENTRY_DUPLICATE` (v1.15) | A new entry would duplicate the exact request/obligation event or existing scope coverage. | Open the existing funding record. Do not create the same funding twice. |
| `BUDGET_ENTRY_ROWS_MISMATCH` (v1.15) | The allocation rows do not add up to the amount the system calculated as requiring funding. Nothing is recorded. | The allocation rows must add up to the amount requiring funding. Show the calculated amount, the rows' total and the difference. |
| `BUDGET_YEAR_ALLOCATION_REQUIRED` (v1.15) | The supported target-year funding basis is unconfirmed. The request/Draft persists; submit/approve/post fail with no funding movement. | Finance must confirm the funding year and amount. Show the existing CM review and holder. |

`BUDGET_SCOPE_REQUIRED`, `BUDGET_PERMISSION_DENIED` and `BUDGET_CONTEXT_AMBIGUOUS` are removed: the first two named a scope and a capability that no longer exist, and the third is unreachable now that one fiscal year has at most one Budget. Message conventions are in KT-STD-001 §11. Display plain text and support references, not raw payloads or stack traces. Known rejection and unknown outcome differ: use §9.3 recovery before claiming failure or retrying. Translated wording never overrides a code, guarded action or owner boundary.

---


## 14. Audit and historical integrity

Append-only events: Budget and successor-version creation; Draft approval-detail and line change sets; submit, return, approve, activate, supersede and close; owner decision evidence referencing a funding check; reservation creation; revalidation, release, conversion and commitment adjustment; from v1.13 also commitment closure (a zero-value event with identical before and after positions) and, for a Closed commitment, correction recorded, correction returned and commitment corrected (the funding event, with the amounts and positions before and after, the reason, the evidence and the Contract Management reference); from v1.15 also the verified lineage on a conversion event, contract funding request received, declined and outcome published, existing-contract entry recorded and returned, and existing contract commitment recorded (the funding event that creates the commitment, with the positions before and after); responsibility, segregation, floor and concurrency denial; and protected-access security audit where supported. From v1.11 also: budget revision request receipt, link to a successor, Revised on activation, decline with reason, withdrawal, closure resolution and each outcome publication. Read/check calls do not create business or funding-ledger events. A transport/security log is not a new financial record. Successful idempotent replay returns prior financial events; it does not append a second effective funding event.

Each event records actor or calling service, business role, the exercised responsibility assignment ID, fiscal year, relevant IDs, action, timestamp, before and after status or line position, required decision reason, correlation ID and calling module. No event records a Procuring Entity or a capability string.

Active, Superseded and Closed versions are immutable. Funding Ledger events cannot be edited or deleted. Downstream reservation and commitment identities remain resolvable after a successor activates or the fiscal year closes.

---

## 15. Deterministic seed contract

SEED-001 v1.3 governs shared identities and the BASE/READY separation; CFG v0.10 governs actual authority/configuration at the frozen command instant. A documentation amendment is not proof that the executable seed or its end-to-end validator passes.

### 15.1 Actors and baseline chronology

Josphat Mwangi (`josphat.mwangi@moh.example.test`) has separate site-wide Budget Officer and Finance Confirmation Officer assignments. Beatrice Kamau (`beatrice.kamau@moh.example.test`) is Budget Approver. Naomi Chebet is Auditor. Charles Mutiso is HOPF and initiates the REQ authorisation; Budget records the registered service too. All are resolved by live assignments; no Administrator business action. Samuel Otieno has neither a Budget assignment nor technical-read grant and supplies Forbidden.

Baseline creation: Josphat, 1 Oct 2026 09:20 EAT; Draft save 15:55; submission 16:20; Beatrice approval/activation 3 Oct 2026 11:15. The prior 2 Oct approval-review artboard is an inspection before the 3 Oct decision. Technical-reader successor artboard uses the isolated March revision, not an impossible future submission shown in December.

### 15.2 Required configuration and boundaries

Resolve native Fiscal Year `2027-2028` (1 Jul 2027–30 Jun 2028), explicit Company/currency association, KES precision 2, `OU-MOH-DHI`, `OU-MOH-HRMD`, and enabled Government of Kenya funding-source identity. No fallback records or guessed mapping. Exact native metadata fields and precision mapping require repository inspection.

**Shared date dependency remains open:** CFG-XD-001 identifies the May 2027 procurement schedule against FY/profile starting July 2027. This Budget amendment neither shifts invitation to 2028 nor waives date guards. The conditional positive downstream fixture remains gated on coherent approved FY/applicability evidence. Budget registration dates represent externally approved future-year allocations, not evidence that a pre-FY tender is eligible.

### 15.3 Active Budget baseline

| Field | Exact value |
|---|---|
| Budget / Version | `MOH-BUD-2027-001` / `MOH-BUD-2027-001-V1` |
| FY / currency / scale | `2027-2028` / KES / 2 |
| Status | Active Budget Version; this does **not** imply an Active Plan. |
| External approval reference | `MOH-FIN-BUD-2027-01 (Demo)` |
| External approval date | 30 Sep 2026 |
| Approval document | `MOH Approved Procurement Budget 2027-28 (Demo).pdf` |
| Authorised total | `"160000000.00"` |

| Line | Title | Owner scope | Funding source | Approved |
|---|---|---|---|---:|
| MOH-BL-DHI-2027 | Digital health infrastructure programme | Digital Health (`OU-MOH-DHI`) | Government of Kenya | KES 100,000,000 |
| MOH-BL-HWD-2027 | Digital health workforce development | **Entity-wide** (null owner) | Government of Kenya | KES 60,000,000 |

**Explicit fixture correction:** v1.7's HWD owner HRMD excluded the DHI laptop source under its own BUD-BR-007. Entity-wide is required for the shared two-department fixture and applies consistently to baseline creation and every artboard. It does not make actors site-wide in other modules. A fresh/reset fixture creates this correct baseline through governance. Do not update an already Active real line's immutable scope in place: inspect existing data and use a new eligible line plus governed source/Budget successors; preserve real history and downstream scope restrictions. Release evidence must distinguish a fixture rebuild from a production data correction.

### 15.4 BASE: Planning with no REQ authorisation

| Line | Approved | Planned | Reserved | Committed | Available |
|---|---:|---:|---:|---:|---:|
| DHI | KES 100m | KES 80m | KES 0 | KES 0 | KES 100m |
| HWD | KES 60m | KES 50m | KES 0 | KES 0 | KES 60m |
| Total | KES 160m | KES 130m | KES 0 | KES 0 | KES 160m |

BASE has two Plan Items and three exact sources under SEED v1.3, including HRMD 100 Each/KES 20m and DHI 150 Each/KES 30m against HWD. BASE's None/None planned designations fail the mandatory illustrative reservation target; its Plan remains blocked Draft even though Budget is Active. Planning's eligible current APP value is KES 130m, so the illustrative 30% target is KES 39m. READY's separately declared planned Youth designation on the KES 50m laptop item gives 38.46% and zero remaining allocation; production law/configuration/date prerequisites still apply. The KES 160m Budget total remains the funding ceiling only. Budget does not seed eligibility entitlements or force the Plan Active.

December BUD-DES-01/04/05/06/07 show no reservations. Finance confirmation and the entire Planning lifecycle leave all Budget financial balances unchanged. A Draft or submitted REQ likewise reserves nothing.

### 15.4A BUD-SC-REQ-AUTH: conditional harmonized authorisation

Only run after the eligible Active positive Plan scenario and owner configuration/date gates pass. REQ `REQ-MOH-2027-033-001`, Version 1: Grace drafts 1 Mar 2027; Peter submits 8 Mar; Charles authorises 15 Mar. Retain exact owner-generated Version and event identities/timestamps; do not invent a more precise shared instant.

| REQ source / drawdown line reference | Plan allocation | Source OU | Reservation | Line | Amount |
|---|---|---|---|---|---:|
| SRC-MOH-033-001 / PIL-MOH-033-001 | PSA-MOH-2027-033-001 | OU-MOH-HRMD | RSV-MOH-2027-033-001 | MOH-BL-HWD-2027 | KES 20m |
| SRC-MOH-033-002 / PIL-MOH-033-002 | PSA-MOH-2027-033-002 | OU-MOH-DHI | RSV-MOH-2027-033-002 | MOH-BL-HWD-2027 | KES 30m |

Both retain stable Plan Item `PPI-MOH-2027-033` and the exact approved Plan/item/source revisions supplied by Planning. The owner API maps source/drawdown references to physical IDs; they are not interchangeable.

| Line | Approved | Reserved | Committed | Available |
|---|---:|---:|---:|---:|
| DHI | KES 100m | KES 0 | KES 0 | KES 100m |
| HWD | KES 60m | KES 50m | KES 0 | KES 10m |
| Total | KES 160m | KES 50m | KES 0 | KES 110m |

Two reservation-creation ledger effects belong to one authorisation transaction. Repeating it returns the same two IDs. Pre-consumption revocation releases both and reverses the exact Planning drawdown together; restored Budget availability is 160m, historical authorisation remains, and Planning's permanent first-authorisation scope lock remains under its own rules.

### 15.5 Isolated service profiles

These profiles reset independently; none supplies extra activity to BASE or the harmonized laptop chain. Legacy `BUD-SC-FIN-*` identifiers are renamed to `BUD-SC-REQ-*` because their effect belongs to REQ authorisation, not Finance. Fixture builders must supply actual owner-valid authorisation events/authority or explicitly scoped provider-test stubs; a stub is not end-to-end evidence.

| Profile | Exact precondition / expected result |
|---|---|
| BUD-SC-REQ-SINGLE | DHI available 100m; authorised draw 80m → reserved 80m, available 20m. |
| BUD-SC-REQ-COMBINED | DHI 100m and HWD 60m available; draws 72m and 48m → availability 28m and 12m; two reservations or none. |
| BUD-SC-REQ-SHORT | Isolated prior valid DHI hold 30m; available 70m; new requirement 80m → shortfall 10m, no new effect. |
| BUD-SC-REQ-SAME-LINE | HWD available 40m; rows 20m + 30m → aggregate shortfall 10m; neither reserves. Do not test rows independently. |
| BUD-SC-CONVERT-PARTIAL | DHI hold 80m; convert 60m → remaining hold 20m, commitment 60m, available 20m. |
| BUD-SC-DUPLICATE-CORRELATION | Replay exact successful SINGLE key/payload → original reservation/effect. Changed payload with same key fails. |
| BUD-SC-AFFORDABILITY | DHI approved 100m, reserved 30m, planned 80m → within approved passes; available advisory shortfall 10m; Finance creates no hold. |
| BUD-SC-CEILING-SEPARATION | Budget ceiling 100m, eligible current APP value 40m and qualifying planned allocation 12m: affordability passes and Planning reports 30%. Budget returns no reservation denominator; unused 60m headroom does not change the Planning result. |
| BUD-SC-BASIS-RACE | Budget successor races Finance decision; one serialized ordering succeeds or stale failure occurs, never a positive decision on an already replaced basis. |
| BUD-SC-PRECISION | Exact 18-integral-digit Money round-trip with supported decimals; excess scale and overflow rejected; decimal arithmetic has no epsilon path. |

### 15.6 BUD-SC-REVISION: isolated successor artboards

Start from baseline V1 plus **isolated REQ DHI hold 80m**, HWD no hold. This is not the harmonized laptop reservation and never coexists with it in a single fixture. Create the hold through BUD-SC-REQ-SINGLE before 15 Mar 2027 13:10; freeze an explicit owner-valid event instant in the executable profile before claiming the scenario passes.

Version `MOH-BUD-2027-001-V2`, based on V1; Transfer; external reference `MOH-FIN-BUD-2027-02 (Demo)`, approval date 14 Mar 2027, document `MOH Approved Procurement Budget Transfer 2027-28 (Demo).pdf`; total 160m; DHI proposed 90m, HWD 70m. Josphat creates 15 Mar 13:10, saves 15:55, submits 16:20. Review/read-only fixture is 16 Mar 10:15, EAT.

DHI floor 80m/headroom 10m; HWD floor zero/headroom 70m; transfer difference zero. One affected reservation, no commitment. On approval, total remains 160m; DHI available 10m, HWD available 70m. Separate reset copies exercise Return and Approve. BUD-DES-01A and 08–15 consume this exact profile; initial-baseline BUD-DES-13 variants still use their own October V1 fixture.

### 15.7 Seed and historical controls

Upsert stable IDs deterministically; second run makes no change. Validate through domain services, with frozen authority dates and exact CurrencyBasis. No second entity, fallback catalogue, administrative workflow bypass, float amounts or patched Active histories. Keep future fixtures conditional where owning contracts/date evidence are absent. Record each artboard's scenario and observation time; historical December screens must not display March reservation effects.

---

### 15.8 Additional isolated usability profiles

These extend the retained §15 scenarios; they do not silently modify BASE, REQ-AUTH or REVISION. Each executable fixture must declare a valid owner event/actor/instant and reset independently. A provider stub is not integrated evidence.

| Profile | Exact scenario / expected result |
|---|---|
| BUD19-SC-PENDING | Existing October V1 Draft/submission and returned-attempt branches at actual chronological instants. Officer finds Continue draft/Correct and resubmit; Approver finds Review; no current allocation or duplicate registration. Return has an exact stored10–500 character comment and retained file snapshot. |
| BUD19-SC-LIVE-BREACH | Independent successor test: DHI proposed90m; current reserved+committed95m; exact5m shortfall. Approval blocked; no partial activation, release or negative spendable balance. Do not attach this balance to the80m review fixture. |
| BUD19-SC-CLOSE-BLOCKED | 1 Jul2028 after FY2027/28 end, DHI20m remaining hold. Closure blocked, including Needs Attention variant. Verify Budget Approver's assignment at the frozen actual command instant. |
| BUD19-SC-CLOSE-READY | Separate year-ended profile with zero remaining holds, optionally60m active commitments. Closure allowed if all current guards pass; obligations/history retained; new holds/conversions/increases rejected. No manual release of another scenario's hold to construct this result. |
| BUD19-SC-CLOSE-UNKNOWN | Live year-end/hold verification unavailable; no close. Also lose response after a valid close to prove original-result recovery without another effective event. |
| BUD19-SC-PARTIAL-CONVERSION-UI | Reuse BUD-SC-CONVERT-PARTIAL exact100m allocation,20m remaining reservation,60m commitment,20m available. Runtime observation and authorised owner links supplied from that profile, not invented shared events. |
| BUD19-SC-OMISSION | Independent valid successor: line with zero remaining reservations and active commitments can be omitted while prior Version/identity/history stay readable; nonzero protected amount blocks. Revised total/type/evidence must be valid. |
| BUD19-SC-RECOVERY | Unknown creation, upload/link failure, details-save success then line failure, saved-but-submit-failed, stale tree/token, duplicate click and revoked access. No duplicate root/attempt/event or protected-data retention. |
| BUD24-SC-EXISTING-ENTRY (v1.15) | Current reconciled isolated scenario: DHI approved KES 100m and HWD KES 60m, Reserved 0, existing HWD commitment KES 2m covering this contract/year. Contract KES 12m; supported historical charge KES 3m and target-year gross charge KES 9m reconcile to 12m. Finance confirmer Ruth independently confirms the exact year/basis; accounting settlement alone supplies no Budget coverage. Existing same-year Budget coverage 2m yields new charge 7m, allocated DHI 4m and HWD 3m. Josphat prepares, Beatrice independently approves. Final Committed DHI 4m / HWD 5m; Available DHI 96m / HWD 55m, combined 151m. Before funding the combined Available was 158m, so the decrease is exactly 7m. Incomplete basis permits request/Draft but no submission. A shortfall on either line creates no partial commitment. Replay returns the same result; same confirmer/Approver is refused. A supported later Active decrease follows CM’s authorised adjustment; a Closed decrease uses Budget correction, never a replacement Initial entry. A distinct effective increment after closure uses the bounded Additional path, while an unchanged contract’s next annual charge follows §8.8 without reopening. |
| BUD23-SC-LINEAGE (v1.14) | New content for owner review, from the test world of `test_budget_contract_reservation_authority` for the checks that are built (the contract named in the award, an unrelated reservation on the same line, another contract's award, an unknown contract, no owner, several reservations all-or-none, a replay) and as required results for those not yet built (a wrong Requisition Version, a wrong awarded lot or scope, a wrong budget line, a reservation that Needs Attention, is released or revoked, a Closed Budget, two contracts racing for one reservation). One DHI line holds two reservations, A and B, from different requisitions, each KES 10m. A contract awarded A converts KES 4m of A, leaving KES 6m; the same contract converting B is refused and B stays KES 10m. |
| BUD22-SC-CLOSED-RETAINED (v1.13) | New content for owner review, taken from the test world of `test_budget_retained_commitments`. Isolated Active allocation: DHI KES 100m, HWD KES 60m. DHI hold KES 80m, KES 60m converted, the unused KES 20m released, the commitment Closed at KES 60m. Position: reserved 0, committed KES 60m, available KES 40m, not KES 100m. A successor moving DHI to KES 50m (HWD to KES 110m) is blocked with a Shortfall of KES 10m, DHI KES 60m (HWD KES 100m) passes, omitting DHI is blocked and omitting HWD is allowed. The contract service cannot raise it to KES 61m or lower it to KES 45m: both fail with `BUDGET_INVALID_STATE`. A Budget Officer records a correction to KES 45m with evidence RECON-DECREASE and MINUTE-17; nothing moves. A different Budget Approver approves it: committed KES 45m, available KES 55m, reserved 0, the reservation unchanged, and one Commitment corrected event showing available KES 40m before and KES 55m after. The same person cannot approve their own correction even holding both responsibilities. A correction with no evidence, no Contract Management reference or no reason is refused, and a correction is still possible after the Budget is Closed but never an increase. |
| BUD21-SC-REVISION-REQUEST (v1.11) | Default Active V1 (§15.3), no REQ authorisation: HWD approved KES 60m, available KES 60m. Mercy's Planning plan update PLN-MOH-2027-001 Version 2 (PLN-CHG-001 v1.27 §10.2 UPDATE-OVER-BUDGET) plans KES 62m on HWD; `RequestBudgetRevision` at 15 Dec 2026, 10:00 EAT records one Open request. Branches, each reset independently: Decline by Josphat with a stored reason; Withdraw from Planning; Update registered allocation creating a Supplementary allocation successor that Beatrice approves, resolving Revised; a successor leaving HWD unchanged, leaving the request Open; `close_budget` after year end resolving Declined. No REQ reservation or ledger event in any branch. |

Josphat/Beatrice/Naomi retain their existing roles; technical readers never receive a Budget role to pass tests. The full source approval PDFs are real controlled fixture artifacts when supplied by the owner; an HTML/MD filename alone is not proof that an uploaded document exists. Preserve all existing BUD18-XD gates and exact source event identities.

## 16. Acceptance contract

All 70 v1.8 criteria remain mapped below, including their earlier v1.7 sources, with operative contradictions corrected. Section 16.2 adds 28 usability criteria, giving **98 acceptance criteria** total. Old IDs are traceability references, not a parallel implementation contract. Every new criterion is required unless its named downstream facility remains explicitly gated. These are requirements, not claims of tests executed in this document review.

| ID | Prior criterion / source | Required result |
|---|---|---|
| BUD18-AC-001 | BUD-AC-001 | The module installs and migrates cleanly on a site with ERPNext installed; no DocType name collides with an ERPNext DocType. |
| BUD18-AC-002 | BUD-AC-002 | No executable metadata, route, service, field, seed or active test contains Allocation as a separate object, Budget Value Treatment, PVO or Value Commitment. |
| BUD18-AC-003 | BUD-AC-003 | Budget Officer records one Draft for the explicit year through Save and add budget lines, gets generated references, and resumes the existing record on navigation failure; no duplicate create for pending initial work. |
| BUD18-AC-004 | BUD-AC-004 | Without the applicable live business responsibility, including technical Administrator/System Manager alone, user mutations are denied. Registered service effects require authenticated owner command/event context and initiating authority; Finance decisions remain PLN-owned. |
| BUD18-AC-005 | BUD-AC-005 | Initial registration edits only the four approval-detail fields, with explicit year/currency context and §9.3 save/submit validation; successor adds only its existing revision_type. No extra appropriation, justification or Allocation object. |
| BUD18-AC-006 | BUD-AC-006 | A line accepts only title, owner scope, funding source and approved amount. |
| BUD18-AC-007 | BUD-AC-007 | Submission is blocked unless approval evidence is complete and the line total equals the authorised total. |
| BUD18-AC-008 | BUD-AC-008 | Only one Procurement Budget and one Active Version exist per fiscal year, and the guard holds when the command layer is bypassed. |
| BUD18-AC-009 | BUD-AC-009 | Explicit real source OU yields Entity-wide or exactly matching Active lines for Need-backed and direct sources; missing OU fails; owner scope never grants or narrows user Budget authority. |
| BUD18-AC-010 | BUD-AC-010 | An allocation whose funding source differs from the line's is rejected. |
| BUD18-AC-011 | BUD-AC-011 | Every Planning event, including repeated Finance review and Active reassessment, leaves Budget financial balances unchanged; no reservation, commitment or funding-ledger effect is created. |
| BUD18-AC-012 | BUD-AC-011a | check_plan_affordability returns coherent per-line exact amounts, eligibility, revisions, as_at and both verdicts; no lock, check token, financial write or ledger event. |
| BUD18-AC-013 | BUD-AC-011b | A planned total exceeding a line's approved amount returns the within-approved verdict as failed with the exact excess; a planned total exceeding currently available but within approved returns within-approved as passed. |
| BUD18-AC-014 | BUD-AC-011c | Only successful REQ authorisation creates reservations. Drafting, submission, return and Planning callers create none; a Planning reserve_funding call is rejected. |
| BUD18-AC-015 | BUD-AC-012 | check_funding writes nothing and returns exact per-allocation positions. |
| BUD18-AC-016 | BUD-AC-013 | A REQ authorisation reserves one row per complete drawdown line, including two rows sharing one Budget Line; drawdown, reservations, decision, handoff and outbox commit together or all roll back. |
| BUD18-AC-017 | BUD-AC-014 | An insufficient allocation returns the exact shortfall and creates no reservation. |
| BUD18-AC-018 | BUD-AC-015 | Same authorisation key/payload returns the original full reservation mapping and no duplicate effective events; changed payload conflicts and replay after release does not recreate a hold. |
| BUD18-AC-019 | BUD-AC-016 | Concurrent authorisations cannot oversubscribe a line, and no position becomes negative. |
| BUD18-AC-020 | BUD-AC-017 | Partial conversion leaves the correct remainder reserved and the correct amount committed. |
| BUD18-AC-021 | BUD-AC-018 | Commitment adjustment, release and cancellation are idempotent by correlation ID. |
| BUD18-AC-022 | BUD-AC-019 | `Needs Attention` retains the reserved amount and blocks downstream progression without releasing funds. |
| BUD18-AC-023 | BUD-AC-020 | BASE, conditional two-row REQ-AUTH and isolated REVISION positions match §15 exactly, with the correct scenario/time on every affected artboard. |
| BUD18-AC-024 | BUD-AC-021 | A successor cannot reduce a line below Reserved plus Committed. |
| BUD18-AC-025 | BUD-AC-022 | A Transfer successor with unbalanced increases and decreases is blocked at submission and approval. |
| BUD18-AC-026 | BUD-AC-023 | Approving a successor atomically activates it and supersedes the prior Active version, preserving all identities. |
| BUD18-AC-027 | BUD-AC-024 | Existing line title/source-department eligibility/funding source cannot change. Governed omission from a successor is distinct from deletion and requires zero remaining reservation/active commitment; historical line identities remain. |
| BUD18-AC-028 | BUD-AC-025 | The submitting Budget Officer cannot approve the same version, enforced from the submission audit event. |
| BUD18-AC-029 | BUD-AC-026 | The seed is deterministic and a second run produces no change. |
| BUD18-AC-030 | BUD-AC-027 | A missing ERPNext Fiscal Year, organisation unit, currency or funding source fails seed execution without creating a fallback record. |
| BUD18-AC-031 | BUD-AC-028 | PLN/REQ/Contract callers use only owner contracts; neither side imports downstream controllers or reads/locks another owner’s tables. |
| BUD18-AC-032 | BUD-AC-029 | Downstream direct-table mutation and Draft reads are rejected. |
| BUD18-AC-033 | BUD-AC-030 | All five canonical routes and revised BUD-DES families, including pending work, decision-first review, both historical/live positions and year-end closure variants, render correctly with owner-authorised links. |
| BUD18-AC-034 | BUD-AC-031 | Loading, no-baseline, forbidden and server-error states disclose no false or unauthorised funding data. |
| BUD18-AC-035 | BUD-AC-032 | The Frappe header and breadcrumb are reused and not duplicated inside the Vue page; no Procuring Entity or context selector appears on any Budget screen. |
| BUD18-AC-036 | BUD-AC-033 | Approver can inspect and close after FY only with zero remaining holds including Needs Attention. Active commitments alone do not bar closure; no new holds/conversions/increases afterward, while permitted commitment decreases/cancellations and historical lineage remain. |
| BUD18-AC-037 | BUD-AC-034 | No executable metadata, permission, route, service, seed or active test refers to Budget Reviewer, Budget Activation Authority, Budget Viewer as a workflow role, or the removed `In Review` and `Awaiting Activation` statuses. |
| BUD18-AC-038 | BUD-AC-035 | User business writes use live registered AUTH responsibility hooks; registered downstream services validate owner event/command and actor context. No User Permission, capability string, FY grant or parallel lookup participates. |
| BUD18-AC-039 | BUD-AC-036 | No `procuring_entity_id`, KenTender `FinancialYear`, `cost_center` or accounting-transaction reference exists in Budget schema, services, seeds, fixtures or tests. Explicit owner/native Company currency metadata and Fiscal Year references remain permitted. |
| BUD18-AC-040 | BUD-AC-037 | Budget Officer, Budget Approver and Finance Confirmation Officer appear in the business-role registry with `scope_type = Site-wide`, and no Budget command performs a user-scope organisation-unit or fiscal-year check. |
| BUD18-AC-041 | BUD-AC-038 | ERPNext accounting and its own `Budget` and `Cost Center` records remain fully functional and untouched after this module installs. |
| BUD18-AC-042 | BUD-AC-039 | Every page resolves its authorisation verdict before rendering; a denied actor sees the inline Forbidden panel with no header, filter, content or empty state painted, and no permission modal appears on page load. |
| BUD18-AC-043 | BUD-AC-040 | The Forbidden panel names the responsibilities that open the surface and directs the user to a KenTender administrator; it names no line manager or supervisor. |
| BUD18-AC-044 | BUD-AC-041 | Selecting this module without access pushes its own route, highlights it in navigation, and lands on its Forbidden state; the module is never hidden and route and view never diverge. |
| BUD18-AC-045 | BUD-AC-042 | Administrator/System Manager can discover and read every Budget/Version/task in all statuses, including edit and exact approval routes, without business assignment or mutation. Ordinary unauthorised callers receive non-disclosing denial. |
| BUD18-AC-046 | FU-23; decision validation | validate_plan_affordability_for_decision retains serialization until the caller decision commits, validates expected Budget/line revisions and returns immutable evidence without any Budget financial record or ledger write. |
| BUD18-AC-047 | FU-23; concurrency | A racing Budget activation/closure and positive Finance decision cannot commit a stale basis; test both orderings and caller rollback after successful provider validation. |
| BUD18-AC-048 | Corrected in v1.10; owner boundary | Budget exposes exact ceiling and affordability evidence but no statutory planned-allocation denominator. Eligible current APP value is calculated by Planning under the exact verified rule. |
| BUD18-AC-049 | Corrected in v1.10; concurrency | A Budget change stales affordability evidence where applicable. An unused-line change cannot by itself alter Planning's 30% denominator; Plan/rule changes control that calculation. |
| BUD18-AC-050 | FU-23; historical evidence | Historical Budget/line reads return exact retained Version/instant/precision; unsupported replay fails typed and never substitutes current values. Missing funding evidence never becomes zero. |
| BUD18-AC-051 | FU-23/FU-30; precision | All Budget API Money values are plain decimal strings in currency units; exact 18-integral-digit plus supported-scale round-trip succeeds. Excess scale, float JSON, malformed and overflow values fail before effects. |
| BUD18-AC-052 | FU-30; arithmetic | Shared precision tests across BUD/NDS/REQ/PLN prove exact aggregation, comparison, token digests and persistence without flt(), binary float, epsilon or silent rounding. Contract suite evidence is required before release. |
| BUD18-AC-053 | FU-23; currency | get_budget_currency_contract returns verified metadata/precision identity; missing native Company mapping or unsupported precision blocks affected writes/decisions. Changing native default never rewrites Budget currency/history. |
| BUD18-AC-054 | FU-23; human reference | Eligible-line responses return human reference plus stable/exact IDs; labels can display a reference without guessing one from a technical ID. |
| BUD18-AC-055 | FU-23; source eligibility | HWD Entity-wide accepts both HRMD and DHI; an isolated HRMD-owned line rejects DHI even when the initiating user has broad authority. OU descendant membership is not inferred. |
| BUD18-AC-056 | CFG v0.10 integration | Disabled source/OU is excluded from new selection and rechecked at decisions while historical read-by-ID/frozen labels remain available. No catalogue rename rewrites approved line identity. |
| BUD18-AC-057 | REQ duplicate-line risk | Two REQ rows of 20m and 30m against one line with 40m available return aggregate 10m shortfall and create nothing; both individually passing is insufficient. |
| BUD18-AC-058 | REQ identity correction | Two eligible sequential draws against the same original Planning allocation have distinct REQ/drawdown reservations; same authorised drawdown with a different key cannot duplicate. Owner remaining allowance and scope gates apply. |
| BUD18-AC-059 | REQ token contract | The complete-array check token binds expiry, actor/caller, exact source/revision/amount payload and cannot authorize a subset, changed amount or expired request. |
| BUD18-AC-060 | REQ revocation | Unconsumed REQ revocation reverses exact drawdown and both 20m / 30m reservations atomically. Consumed handoff blocks that route; a funding release cannot reset Planning’s permanent scope lock. |
| BUD18-AC-061 | Reservation conservation | Partial conversion/release preserves original=remaining+cumulative conversion+cumulative release; commitment decrease never recreates a reservation and repeated events have one effect. |
| BUD18-AC-062 | Governance snapshots | Return/re-edit/resubmit preserves each immutable submitted attempt, attachment and decision; approval checks the current attempt’s submitter for segregation. |
| BUD18-AC-063 | Finance repeat/reuse | At most one open whole-Plan review per Version; changed financial/eligibility basis stales old evidence, unchanged financial facts permit only explicit reuse, and Active reassessment retains original approval evidence. |
| BUD18-AC-064 | Availability advisory | A 100m approved line with 30m held and 80m planned can pass Finance with 10m availability advisory; a new 80m REQ fails availability. Neither Finance read nor confirmation adds a hold. |
| BUD18-AC-065 | UI fixture correction | December workspace/overview/lines show 160m available and no holds; March conditional REQ shows two HWD reservations 20m / 30m and 110m total available, attributed to Charles/owner service, not Finance. |
| BUD18-AC-066 | UI technical read | Technical-reader March successor uses the actual submitted March timestamp and isolated 80m DHI hold; it neither displays future submission in December nor replaces the Active card with a Draft. |
| BUD18-AC-067 | UI page states | Forbidden renders no Budget header/filter/protected data; server-error remains a valid documented state; module/approval navigation resolves access without hidden-route or modal-on-load behavior. |
| BUD18-AC-068 | Seed ownership correction | A fresh fixture activates HWD as Entity-wide consistently. A populated Active HRMD line is never silently patched; affected real histories use an explicit reviewed migration/governance route. |
| BUD18-AC-069 | Scope and legal boundary | Annual target numerator/category/overlap remain LAW/CFG/PLN-owned; Budget does not infer candidate entitlement, waive statutory prerequisites or force BASE Active. CFG-XD-001 and other positive fixture gates remain visible. |
| BUD18-AC-070 | Adoption evidence | All 70 baseline criteria and 30 prior changes remain traceable;28 usability criteria and 14 changes are added. Release evidence separates approved requirements, implemented contracts, precision/transaction/browser/user results and remaining dependencies. |

### 16.1 Minimum verification coverage

Run owner-contract and database tests for precision, authorization, unique guards, rollback/idempotency, same-line aggregation, concurrent activation/reservation/Finance decisions, historical replay, eligibility and Budget-ceiling versus APP-denominator separation. Browser evidence must exercise all five routes, technical readers, forbidden/loading/failure states, version creation/return/approval, current-versus-historical positions and the three isolated fixture contexts. Shared precision and REQ orchestration suites are release gates; unit stubs cannot stand in for integration evidence.

---


### 16.2 Approved usability coverage

| ID | Approved source | Required result |
|---|---|---|
| BUD19-AC-001 | BUD-UX-001 | No record, initial Draft, initial Submitted, current-with-update, returned and Closed states give each authorised actor the correct next action without duplicate registration or fake current balances. |
| BUD19-AC-002 | BUD-UX-001 | FY is a changeable view choice, not authority; queue Review is navigation only; current allocation remains while updates wait; multiple roles need no switch. |
| BUD19-AC-003 | BUD-UX-002 | The four external approval fields, explicit native FY and verified currency are complete before first Save and add budget lines; no line-total prerequisite yet, extra evidence or unassigned-ID input. |
| BUD19-AC-004 | BUD-UX-002 | One current document link and every immutable earlier submission attachment remain distinct; upload/link failure and unknown save never imply successful registration/submission. |
| BUD19-AC-005 | BUD-UX-003 | Budget line names lead references; Available to means null/all-departments or exact source OU, never user scope, descendant expansion or missing-OU default. |
| BUD19-AC-006 | BUD-UX-003 | Entered total and positive unassigned/excess messages use exact currency-scale arithmetic; no auto-balancing, rounding or new fields. |
| BUD19-AC-007 | BUD-UX-004 | Save scopes and token sequence are explicit; one Submit saves changed valid details/lines and submits the exact confirmed Version, without mandatory manual Save steps. |
| BUD19-AC-008 | BUD-UX-004 | Lost response, partial saved scopes, submit rejection, stale token, duplicate clicks and revoked permission resolve original identities, preserve only permitted work and create no duplicate Budget/submission/decision. |
| BUD19-AC-009 | BUD-UX-005 | Update registered allocation reuses one pending successor and keeps current amounts; type/line identity/transfer/evidence rules remain enforced. |
| BUD19-AC-010 | BUD-UX-005 | Old line identity cannot change; valid zero-protection omission retains prior history; remaining hold/commitment or invalid totals/type block. No destructive historical deletion. |
| BUD19-AC-011 | BUD-UX-006 | Review opens with complete initial allocation or successor amount/evidence changes; fixed proposed Version/baseline and live protected amounts/time are clearly distinct. |
| BUD19-AC-012 | BUD-UX-006 | 90m proposed against95m reserved+committed shows5m Shortfall and blocks approval; positive10m projected availability against80m fixture is exact. Missing live/evidence data never produces Ready. |
| BUD19-AC-013 | BUD-UX-007 | One labelled approval activates registered amounts with explicit external-approval/cash distinction; no Reject, extra activation step, score, checklist or mandatory tab tour. |
| BUD19-AC-014 | BUD-UX-007 | Return preserves exact attempt/document/reason before same-Draft editing;10–500 character guard and submitting-actor no-self-approval revalidate against the current attempt. |
| BUD19-AC-015 | BUD-UX-008 | Registered100m−Reserved20m−Committed60m=Available20m is displayed without double-counting conversion; Available to reserve is not cash or payment. |
| BUD19-AC-016 | BUD-UX-008 | Exact current as_at and historical Version/instant cannot be blended; missing historical position is unavailable, never substituted with current ledger. |
| BUD19-AC-017 | BUD-UX-009 | Each source drawdown reservation remains separately visible with original/still-reserved amounts and exact owner links; two HWD20m/30m holds are not merged. |
| BUD19-AC-018 | BUD-UX-009 | Requires review keeps funds reserved; owner-only recovery cannot create a local release/convert/adjust action or replenish reservations after commitment decreases. Funding activity and Budget history stay separate. |
| BUD19-AC-019 | BUD-UX-010 | Finance whole-plan review remains in Planning;100m approved/80m planned/70m available passes approved comparison with10m advisory while an80m actual reserve fails. Confirmation adds no hold. |
| BUD19-AC-020 | BUD-UX-010; corrected in v1.10 | Budget ceiling remains KES 160m despite APP KES 130m/current availability KES 110m or filters, but only Planning's eligible APP value drives its 30% calculation. Current line read does not replace frozen Finance evidence, cancel earlier authorisations or enlarge procured scope. |
| BUD19-AC-021 | BUD-UX-011 | Closure variants cover before FY end, remaining/flagged hold, unavailable, ready and Closed; only Budget Approver may act through the existing command and focused confirmation. |
| BUD19-AC-022 | BUD-UX-011 | After FY ends, zero remaining holds permits closure even with active commitments; commit-time race/stale/failure cannot bypass guards. Closed blocks new holds/conversions/increases and does not imply payment. |
| BUD19-AC-023 | BUD-UX-012 | Errors name exact shortfall/field/owner action, distinguish known/partial/unknown outcomes and preserve still-authorised input without overwriting newer values. |
| BUD19-AC-024 | BUD-UX-012 | Keyboard/focus/contrast/narrow-screen and full document/reason reading are verified with representative users; no forced download, clipped blocker or protected-data flash. |
| BUD19-AC-025 | BUD-UX-013 | Actor matrix covers Officer, Approver, Finance, Planner, REQ/Contract consumers, Auditor and technical readers; no extra title-based authority or financial controls from technical read. |
| BUD19-AC-026 | BUD-UX-013 | All-state technical read includes exact approval-shaped routes while ordinary neutral readers remain correctly restricted; counts/search/routes use the same authorisation policy. |
| BUD19-AC-027 | BUD-UX-014 | Needs remains six-field source with no Budget Line or Money; Planning source entry owns selection and Budget owns eligibility; sibling approval/implementation statuses stay explicit. |
| BUD19-AC-028 | BUD-UX-014 | All 70 baseline AC/30 changes and existing seed facts remain; new breach/closure profiles are isolated, actual owner dates/events/assignments are required and no positive end-to-end gate is silently waived. |

### 16.3 v1.10 denominator-boundary acceptance

| ID | Required result |
|---|---|
| BUD20-AC-001 | Budget exposes exact approved amounts, Money metadata and affordability evidence but no statutory planned-allocation denominator. |
| BUD20-AC-002 | `AnnualProcurementBudgetBasis.v1` and `get_annual_procurement_budget_basis` are absent from the new schema/service inventory and implementation; no compatibility alias remains. |
| BUD20-AC-003 | An unused Budget-line change can affect Budget evidence but cannot change or stale Planning's 30% calculation unless a relevant Plan/rule/funding fact used by its own controls changes. |
| BUD20-AC-004 | The integrated fixture preserves Budget ceiling KES 160m and APP value KES 130m as separate facts; Planning calculates KES 39m required and 38.46% for KES 50m qualifying. |
| BUD20-AC-005 | Historical BUD18/BUD19 denominator wording is non-operative; reimplementation follows BUD20-CHG-001–004 and the matching approved PLN/CFG/LAW successors. |

### 16.4 v1.11 budget revision request acceptance

| ID | Required result |
|---|---|
| BUD21-AC-001 | `receive_budget_revision_request` from the Planning service principal records one Open request in Planning's transaction, checks the expected line revision and Budget's own approved amount, and replays idempotently. It changes no amount and creates no reservation, commitment or ledger event. |
| BUD21-AC-002 | A request whose planned amount does not exceed the current approved amount fails with `BUDGET_REVISION_NOT_REQUIRED`; a stale line revision fails with `BUDGET_DECISION_BASIS_STALE`. |
| BUD21-AC-003 | **Update registered allocation** from a request creates or reuses the one open successor and links it. The successor needs the same approval details and Budget Approver decision as any other. |
| BUD21-AC-004 | Activating a successor that changes or omits the line resolves every Open request on it as Revised in the same transaction; a successor leaving the line unchanged leaves the request Open. |
| BUD21-AC-005 | Decline requires a Budget Officer and a 10–500 character reason; Withdraw comes only from Planning and leaves a linked successor untouched; `close_budget` resolves remaining Open requests as Declined. A second answer returns `BUDGET_REVISION_REQUEST_CLOSED`. |
| BUD21-AC-006 | Every outcome publishes one `BudgetRevisionRequestOutcome.v1` through the transactional outbox, delivered idempotently and in order. |
| BUD21-AC-007 | The Budget Officer's request row appears only while the request is Open and never clears on view; Budget Approver, Auditor, Administrator and System Manager never see it as their work or see Decline. |
| BUD21-AC-008 | No Budget screen shows a Planner-waiting state, Finance decision or Plan editing control for the request. |

### 16.5 v1.13 closed-commitment acceptance

| ID | Required result |
|---|---|
| BUD22-AC-001 | A line's Committed is the sum of the `current_amount` of its Active and Closed commitments. Closing a commitment leaves the line's Committed and Available unchanged, and every reader of the position (the line position, the Procurement budget-line use read and the analytics totals) agrees. |
| BUD22-AC-002 | A successor cannot reduce a line below Reserved plus Committed when the Committed is a Closed commitment's retained amount. The blocker shows the exact protected amount and Shortfall. |
| BUD22-AC-003 | A line whose only protection is a Closed commitment cannot be omitted from a successor. A line with no reservation and no commitment can. |
| BUD22-AC-004 | `close_commitment` accepts only the Contract Management service principal for its own contract, an owner outcome of type `ContractClosed` or `TerminationSettlementCompleted` naming the final supported obligation, reconciliation evidence and the revision the caller read. It changes status only, records one zero-value Commitment closed event with identical before and after positions, never accepts a release amount, and returns the first result on an identical repeat. A stale revision fails with `BUDGET_STALE_REVISION`, a differing amount with `BUDGET_COMMITMENT_AMOUNT_MISMATCH`, and a different outcome for an already Closed commitment or a closure of a Cancelled commitment with `BUDGET_INVALID_STATE`. |
| BUD22-AC-005 | The contract service can neither raise nor lower a Closed commitment: `adjust_commitment` fails with `BUDGET_INVALID_STATE` for a higher, lower or equal total and nothing changes. A Closed Budget refuses a new conversion and any increase. |
| BUD22-AC-006 | A Budget Officer's correction without evidence, without a Contract Management reference or without a reason of 10–500 characters is refused with `BUDGET_EVIDENCE_REQUIRED` and records nothing. A correction that does not lower the amount, a correction of a commitment that is not Closed, and a second correction awaiting approval are refused with `BUDGET_INVALID_STATE`. |
| BUD22-AC-007 | Only a Budget Officer records and only a Budget Approver decides a correction. A person who recorded one cannot approve it, even holding both responsibilities, and the correction stays awaiting approval. A decided correction cannot be decided again, and a return needs a reason and changes nothing. |
| BUD22-AC-008 | An approved correction raises Available by exactly the decrease, leaves Reserved, the Approved amount, the reservation, its remainder and its conversion history unchanged, leaves every earlier ledger event as written, and appends one Commitment corrected event with the amounts and positions before and after, the reason, the evidence, the Contract Management reference and the recorder and approver. A correction to zero is allowed. A correction is refused when the commitment changed after it was recorded, and is possible after the Budget is Closed but never raises an amount. |
| BUD22-AC-009 | Reopening a contract record in Contract Management makes no funding call and changes no funding record or balance, and the contract still shows its commitment as closed by the funding owner. Repeating a decision with the same key creates no second event. |

### 16.6 v1.14 conversion-lineage acceptance

| ID | Required result |
|---|---|
| BUD23-AC-001 | A valid conversion succeeds, including one contract that draws on several reservations: each converts, the unconverted remainder of each stays reserved, and a repeat of the whole conversion converts nothing more. |
| BUD23-AC-002 | An unrelated reservation is refused even when the supplier, the Tender or the Requisition is the same. The refusal is `BUDGET_RESERVATION_NOT_AUTHORISED` and nothing changes. Another contract's award does not carry over. |
| BUD23-AC-003 | A wrong awarded lot or scope is refused, where the source already carries a lot. No lot feature is added where it does not. |
| BUD23-AC-004 | A wrong Requisition Version is refused. |
| BUD23-AC-005 | A wrong Budget Line is refused. |
| BUD23-AC-006 | A conversion larger than the unconverted amount is refused with `BUDGET_CONVERSION_EXCEEDS_REMAINDER` and changes nothing. |
| BUD23-AC-007 | A repeated conversion event, with the same key or the same contract and reservation, creates nothing twice. |
| BUD23-AC-008 | Two contracts competing for one reservation cannot oversubscribe it: one valid ordering or a typed refusal. |
| BUD23-AC-009 | A reservation that Requires review (Needs Attention), is Released or has been revoked cannot be converted. |
| BUD23-AC-010 | A Closed Budget refuses a conversion with `BUDGET_CLOSED`. |
| BUD23-AC-011 | A contract no owner knows, a missing chain and a site with no owner installed are refusals, never a yes. A repository scan proves that only the seam module, seeds and tests can install a fixed answer. |

### 16.7 v1.15 verified-lineage and existing-contract entry acceptance

| ID | Required result |
|---|---|
| BUD24-AC-001 | The first conversion of a reservation is validated against the owning module's verified lineage, not what the caller supplied. A conversion whose Tender, lot, Award version or funding allocation differs from the verified answer, or whose verification is unavailable, is refused with `BUDGET_RESERVATION_NOT_AUTHORISED` and changes nothing. A valid one retains the verified Tender, lot, Award and version, funding allocation and package digest immutably on the commitment and the conversion event, and leaves the reservation unchanged. |
| BUD24-AC-002 | A later conversion of the same reservation, or an amendment, is checked against the retained lineage. A legitimate correction is a new versioned owner event beside the earlier evidence, and the earlier evidence is never overwritten. |
| BUD24-AC-003 | Budget imports no Tender controller, reads no other module's records and accepts no identifier from a browser in a conversion. A scan proves the first, and the conversion is a service-principal call only. |
| BUD24-AC-004 | An entry is prepared only by Budget Officer and decided only by Budget Approver. The Approver must differ from both its preparer and every Finance confirmer whose basis supports the submitted entry, even holding all responsibilities; unattributed confirmation fails closed. No extra approval stage; approver capacity and actual participation are retained. |
| BUD24-AC-005 | An entry without the contract references, the exact line and year of each row, the source allocation or the reconciliation to Budget is refused with `BUDGET_EVIDENCE_REQUIRED`. The amount requiring funding is calculated by the system from Finance's confirmed allocation by Budget year, identifies the amounts already represented, cannot be typed or overtyped, and is never taken from the contract value or the unpaid balance on its own. |
| BUD24-AC-006 | Approval creates exactly one Active commitment for each allocation row, each with origin Existing-contract entry and no reservation. For each line, Committed rises and Available falls by exactly the rows charged to it, Reserved and the Approved amount are unchanged, and one funding event per commitment records the positions before and after. |
| BUD24-AC-007 | Approval rechecks availability for every row atomically under the Budget's lock, with rows on one line added together. Two entries that together exceed availability cannot both be approved. If any row cannot be funded the whole entry is refused with `BUDGET_INSUFFICIENT_FUNDS` and the exact shortfall per row, nothing is created for any row, and there is no negative position, reservation or revision. Recording an existing obligation authorises no further expenditure. |
| BUD24-AC-008 | An Initial entry cannot duplicate existing coverage; only the verified uncovered amount for exact scope may be added. A concurrent pending entry for the same request/event is refused or returned as that same preparation. Additional events use exact event-and-row uniqueness, so subsequent real increments remain possible. No entry invents a reservation; replay creates nothing twice. |
| BUD24-AC-009 | A Closed Budget takes no positive new entry or obligation increase. Supported saved request facts may persist; only the evidenced downward Closed correction is permitted. |
| BUD24-AC-010 | Approved entries remain immutable; later Active adjustment or Closed correction changes the commitment through its owner operation without creating another commitment. A returned preparation may be revised and resubmitted; stale confirmation is not silently substituted. |
| BUD24-AC-011 | For funding controlled outside KenTender Budget, Budget creates and holds no commitment, entry or record of the funding, and no Tender, Requisition or reservation exists for the contract. |
| BUD24-AC-012 | Initial entry is confined to an independently registered contract; Additional is bounded to an exact new obligation under §8.7. Neither edits an existing commitment or invents a reservation. Both origins count identically in every line/analytics/floor/omission reader. |
| BUD24-AC-013 | One request may hold several allocation rows. The row amounts must add up to the calculated amount, or the entry is refused with `BUDGET_ENTRY_ROWS_MISMATCH`. The rows are submitted, approved and checked together: all rows are funded or none is. |
| BUD24-AC-014 | A contract funding request has one identity. Opening it from Contract Management's contract screen or from the Budget Officer's pending work reaches the same request. It carries the contract details, the evidence and whatever Finance has confirmed automatically, with nothing retyped, and there is one open request per contract and kind. It can be raised while the allocation is incomplete. |
| BUD24-AC-015 | Reopening changes no funding. Each exact new increment can be funded once by eligible verified conversion or bounded Additional entry under §8.7, including a reservation-origin contract whose hold is exhausted. Closed commitments and original reservations are unchanged; a later legitimate increment is not blocked by contract-and-kind uniqueness. |
| BUD24-AC-017 | An incomplete request and Draft entry exist while the supported target-year basis is outstanding; CM owns the Finance task. Submission/approval/posting fail with BUDGET_YEAR_ALLOCATION_REQUIRED until that basis is confirmed. No unsupported future-year charge is silently included. |
| BUD24-AC-018 | The current §8.7 opening funding basis is confirmed through CM’s existing Finance approval review, with explanation and evidence. Accounting facts and Budget coverage are distinct; only non-overlapping Budget commitments count as coverage. Target-year charge is not an equal split or automatically the unpaid balance; unsupported scope remains visible and blocked. |
| BUD24-AC-019 | The contract service principal may call `revalidate_reservations` only for the reservations that the funding-lineage owner confirms for that contract, that is the exact reservations in its approved funding package. A call for any other reservation is refused with `BUDGET_DOWNSTREAM_FORBIDDEN` and changes nothing. The principal still has no `check_funding`, `reserve_funding`, Version edit or Draft read, and the rest of the 6 October 2026 list is unchanged. |
| BUD24-AC-016 | Existing confirmations are reused. An entry needs no routine approval beyond the Budget Approver's decision: Finance's confirmation of the opening accounting position and HOP's confirmation of source and terms are consumed as already given. |

### 16.8 Coordinated funding acceptance — current v1.16

| ID | Required result |
|---|---|
| BUD25-AC-001 | Execute every §8.7 operation against real owner services; positions reconcile A−R−C before/after and include both commitment origins. No payment reduces the retained funding charge. |
| BUD25-AC-002 | Multi-reservation conversion validates the entire verified allocation, locks/rechecks source validity and grouped local balances, commits all rows or none, and handles replay/concurrency without duplicates or overspend. A mutation test proves source validation matters. |
| BUD25-AC-003 | Tender-derived input remains single-year/KES. Independent supported contracts can obtain one annual entry per eligible year under §8.8; no future allocation is treated as funded, no automatic rollover or cross-currency conversion occurs, and covered current-year work is not globally held. |
| BUD25-AC-004 | The opening fixture in §11.22 produces a new 500,000 entry, not 100,000, 600,000 or unpaid balance; accounting-only records supply no Budget coverage. Duplicate/overlapping/wrong-year coverage is refused rather than clamped. |
| BUD25-AC-005 | Request may exist and Draft save may be incomplete. Submit freezes complete content; Return preserves the attempt and permits corrected resubmission; changed Finance/coverage revisions cannot be silently approved. |
| BUD25-AC-006 | A real later increment after a Closed commitment is funded once by eligible conversion or bounded Additional entry even when the original hold is exhausted. A different legitimate increment is allowed; replays and unsupported whole-value entries are refused. |
| BUD25-AC-007 | Correction screens work under normal Officer/Approver roles, including no self-approval, stale revision, post-year-close correction and retained evidence. Correction creates no current-year funding or restored reservation. |
| BUD25-AC-008 | D21/D22 two-row request is one submission/decision; insufficient funds on one line produces grouped shortfall and no partial commitments. Zero uncovered charge completes a validated no-entry request and no ledger movement. |
| BUD25-AC-009 | Missing Finance basis creates/retains CM’s actual Finance work, Officer waiting context and CM waiting item. Submission/Return/approval/decline/withdrawal and holder changes create and clear only their stated work items; completed decisions/evidence remain discoverable. |
| BUD25-AC-010 | Budget makes no native ledger/account/Cost Center read; CM passes validated funding facts and opaque evidence links. The correction Approver can access the authorised source evidence without Budget becoming an accounting integration. |
| BUD25-AC-011 | Migrate existing commitment line/origin and correction/audit metadata through normal migrations, then exercise the multi-reservation Award→CM→Budget closure/reopening/correction path on the intended integration site. Component tests alone do not close this case. |
| BUD25-AC-012 | Render and exercise D20–22 and their variants under KT-STD v1.30, including denied/read-only/error access, browser refresh recovery and persistent history. Record actual evidence; this document is not a test result. |

| ID | Required result |
|---|---|
| BUD25-AC-013 | Annual funding executes the §8.8 three-year example with real Budget boundaries, one request/entry lineage per contract/year, explicit basis, independent confirmer/Approver and no reopening. Duplicate/replayed year-2 attempts create no second charge; insufficient funds and unfunded future payment scope remain held. |

These criteria qualify conflicting BUD24 wording about several years, generic approved-entry replacement and unscoped already-represented deductions. Earlier acceptance IDs remain stable and are interpreted through the current §§4.12/8.7.

## 17. Implementation and test constraints

The implementation baseline is KT-STD-001 §4; the verification protocol is KT-STD-001 §5; release evidence is KT-STD-001 §6.

### 17.1 Additional implementation rules

- Rename the DocTypes to `Procurement Budget`, `Procurement Budget Version`, `Procurement Budget Line` and `Procurement Budget Line Version`, with every route, service, fixture, label, index and test. Verify on a site with ERPNext installed that no name collides.
- Drop `procuring_entity_id` with every dependent parameter, filter, index, fixture and test. Rename `financial_year_id` to `fiscal_year` and repoint it at the ERPNext `Fiscal Year`.
- Add the database-level partial unique index or equivalent guard for BUD-BR-002.
- Register Budget Officer, Budget Approver and Finance Confirmation Officer with `scope_type = Site-wide`. Remove every capability string, custom assignment lookup and Frappe User Permission read from Budget code. The no-self-approval check reads the version's submission audit event.
- Register Budget DocTypes in `kentender_scope_map` per AUTH-ADR-001 v1.7 §5.3, through both hooks, so direct-route access is covered.
- Keep `owner_org_unit_id` on the line version and its BUD-BR-007 eligibility logic. Do not move it into a permission path and do not register it as a scope field.
- Add no ERPNext accounting import, `Cost Center` link or reconciliation job. A static scan shall prove no Budget module imports from `erpnext.accounts`.
- Delete the separate Allocation, treatment, Funding Exception and expenditure artifacts. Preserve no aliases or compatibility response fields.
- Remove the `review_budget_version` and `activate_budget_version` pair; `approve_budget_version` performs the full recheck-and-activate transaction in one call.
- Existing Budget Activation Authority holders may receive a Budget Approver assignment during migration. Budget Reviewer holders are not promoted automatically.
- Where an artboard is marked retired (BUD-DES-12, BUD-DES-13A), do not port it.
- Integrate Planning through §§8–9 only. Align Finance UI with PLN v1.18; Budget owns the line route and read surfaces, not a competing Finance composition. Publish actual code/schema/transaction mapping before release.

### 17.2 Additional minimum coverage

1. Install and migrate on a bench with ERPNext and HRMS present; assert no DocType name collision and that ERPNext `Budget` and `Cost Center` still function.
2. Budget write attempted with no assignment, with an expired assignment and with a Scheduled assignment.
3. Administrator and System Manager technical read succeeds; business mutation is denied.
4. Direct-route access to a Budget, line or task excluded from the actor's register.
5. One-Budget-per-fiscal-year guard under a direct-SQL insert bypassing the command layer.
6. Concurrent reserve and concurrent activation against isolated fixtures.
7. All §15.5 profiles, each reset independently.
8. Successor floor breach, transfer imbalance and line identity immutability.
9. No-self-approval enforced from the submission audit event when one user holds both roles.
10. Owner-scope eligibility proving BUD-BR-007 filters lines without acting as a permission check.
11. Repository scan proving `procuring_entity_id`, `FinancialYear`, `cost_center`, `erpnext.accounts`, `BUDGET_SCOPE_REQUIRED` and `BUDGET_PERMISSION_DENIED` are absent.
12. Browser journeys: Budget Officer registers a baseline and submits; Budget Approver inspects four tabs and returns in one run, approves in another; a read-only actor opens an Active Budget, its lines, a line detail and Funding Activity; a Finance Confirmation Officer uses the Planning task, opens the line, returns and confirms in separate reset profiles; an actor with no Budget assignment sees the Forbidden state with no disclosure.
13. (v1.11) Budget revision request: every BUD21-SC-REVISION-REQUEST branch, Planning/Budget transaction rollback when either side fails, outbox replay and ordering, and the Budget Officer's workspace row and decline dialog in the browser.
14. (v1.13) Closed commitments and corrections: the position, the successor floor and the omission test with a Closed commitment as the only protection; the contract service refused for every change of a Closed commitment; a correction without evidence, reference or reason; a correction that does not lower; a self-approved correction; a returned correction; a stale correction; a correction after the Budget is Closed; a replay of each call; a Contract Management reopen that makes no funding call; and a scan proving no reader counts only Active commitments.
15. (v1.14) Conversion lineage: every result of BUD23-AC-001–011, each against isolated fixtures, with two contracts racing in separate connections.
16. (v1.15) Verified lineage and the existing-contract entry: every result of BUD24-AC-001–019, including two entries racing for the same availability in separate connections, a two-row entry with one unfunded row, a reader-parity test over commitments of both origins, and a scan that Budget imports no Tender controller.

### 17.3 Additional release evidence

- Static scan showing no removed concept, expenditure artifact, or leftover Budget Reviewer, Budget Activation Authority, Budget Viewer or `Awaiting Activation` reference.
- Migration succeeds on a copy of real data, including the DocType rename.
- Planning read/decision and Budget-ceiling-separation tests pass; obsolete annual-denominator schema/service/error identifiers are absent. REQ single, combined, same-line shortfall, rollback and duplicate-correlation contract tests pass separately.
- Contract Management conversion and adjustment contract tests pass before those actions are enabled.
- AUTH contract suite passes, proving no Budget path reintroduces a User Permission read.

---

## 18. Prohibited shortcuts

The universal list is KT-STD-001 §2.3 and §10. Additionally, for this document:

- Do not define a DocType whose name collides with an ERPNext DocType.
- Do not read, write, mirror or reconcile an ERPNext `Budget`, `Cost Center`, account or journal record, and do not import from `erpnext.accounts`.
- Do not add a `cost_center` field or any accounting reference to a Procurement Budget Line.
- Do not reintroduce `procuring_entity_id`, a Fiscal Year permission grant or a capability string.
- Do not use `owner_org_unit_id` as a user-scope or permission check.
- Do not create a Budget Viewer, Budget Reviewer or Budget Activation Authority role, or revive the `In Review` and `Awaiting Activation` statuses under another label.
- Do not add a separate Allocation, Budget Value Treatment, PVO, Value Commitment, Funding Exception or expenditure object under another label.
- Do not add a Strategy field on a Budget or line.
- Do not create a Budget-owned Finance task, decision, queue, sufficient or insufficient form, or planner-waiting screen.
- (v1.11) Do not let a budget revision request change an approved amount, create a reservation, stand in for external approval evidence, add a Version state, or become a separate revision object or workflow.
- Do not create a reservation at any Procurement Planning event. Reservation begins only at successful Procurement Requisition authorisation.
- Do not let `check_plan_affordability` write, lock, issue a token or produce a ledger event.
- Do not make the within-currently-available verdict blocking.
- Do not permit partial REQ all-source reservation or silent line substitution. Do not collapse distinct drawdown rows into one reservation.
- Do not add an accounting-derived outstanding-commitment or actual-expenditure measure, forecast, utilisation score or an `Unavailable` placeholder. Retain Budget-owned Committed as defined in §5.
- Do not add an editable Budget title, classification, separate purpose, generic description, source type, effective date, authority name, contact, note, justification or miscellaneous attachment.
- Do not allow downstream raw SQL or ORM reads of Budget tables.
- Do not allow client-only permission, total, floor, availability or lifecycle enforcement.
- Do not permit direct edits of Active, Superseded or Closed data.
- Do not rename the existing Budget or line identifiers.

---

## 19. Traceability, full changes and remaining dependencies

### 19.1 Governing inputs and adoption scope

This approved successor retains approved BUD v1.9 and corrects only the denominator ownership and its dependent fixtures/contracts. Approved NDS v1.12 owns the six-field requirement; Strategy v1.8 has separately consolidated its approved usability direction. Approved Planning v1.25, CFG v0.13 and LAW v1.2 carry the matching correction. None is deployed merely by this Budget document. Use current operative sections here and the v1.10 rows over historical BUD18/BUD19 register wording.

| Input | Use / limit |
|---|---|
| BUD-CHG-001 v1.7 | Full inherited Budget domain, governance, routes, artboards and 45 acceptance criteria, corrected here. |
| PLN-CHG-001 v1.25 §§4.1, 5.3, 5.4, 5.5.3, 7–8, 15, 17, approved | Financial-basis validation/reuse, eligible-current-APP calculation, precision, source OU and downstream scope boundaries. |
| PLN-CHG-001_FOLLOW_UPS.md FU-23, FU-30 and retired FU-02 | Provider amendments and precision; human reference is reported implemented, but current repository was not supplied for verification. |
| CFG-CHG-002 v0.13, approved | Configuration owner contracts, funding sources, explicit native mapping, immutable rules, separate planning/actual reservation measures and CFG-XD-001 date dependency. |
| SEED-001 v1.3, approved | Two-department/two-reservation lineage, BASE/READY separation, named authority and shared chronology. HWD owner inconsistency is explicitly corrected in this Budget successor. |
| LAW-REG-001 v1.2, approved | Controlled eligible-current-APP Planning interpretation and remaining primary/category/county verification; document approval does not verify production law. |
| AUTH-ADR-001 v1.7 / KT-STD-001 v1.4 supplied baseline | Responsibility hooks, technical read and common UX/implementation rules. FU-27's later shared technical-read citation cleanup remains separately owned. |
| PLN-CHG-001 v1.27, approved (v1.11) | §§4.7, 7.2, 7.3, 7.7, 10.2, 15.2: `RequestBudgetRevision`, the request record, the receive and outcome contracts, the hand-off register row and the UPDATE-OVER-BUDGET fixture. Other Planning references in this document remain to v1.25 until a separate reconciliation. |
| KT-STD-001 v1.8, approved (v1.11) | §3B.4 hand-off register format and §12.1 required correction for Budget. Other citations of KT-STD-001 remain as in v1.10. |
| REQ-CHG-001 v1.7, supplied | Authorisation owns reservations; one per drawdown line; complete authorisation atomicity and pre-consumption reversal. Matching v1.8 caller amendment remains to be consolidated. |
| CM-CHG-001 v0.8 §5.14.1, approved within CM v0.8 on 14 October 2026 (v1.13) | The specified `close_commitment` contract and Closed-amount position semantics that this version applies to Budget. §5.14.1 describes itself as a proposed amendment to be applied in Budget's owner sections, and says an exact, separately authorised decrease may later reconcile a Closed commitment under Budget's adjustment service; owner decision 1 replaces that last point with Budget's own correction (BUD-BR-034). |
| CM-CHG-001_v0_8_FOLLOW_UPS.md FU-CM-04, FU-CM-23, FU-CM-59 and FU-CM-118 (v1.13) | Tracking records that this version, with the evidence in §19.3, closes or advances. They are not requirements. |
| CM-ADVICE-001 v0.1, Proposed advice (v1.13) | Advice, not an owner decision. Its direction to adopt the built Budget semantics is followed here only as far as owner decision 1 of 16 October 2026 allows. |
| Commit `678fb20a` and the BUD-CHG-001 implementation tracker addendum of 15 October 2026 (v1.13) | An observation of what the build does. This version adopts the counting and the closure as requirements; the observation alone was not one. Its allowance for the contract service to lower a Closed commitment is replaced. |
| Owner decision 1 of 16 October 2026 and the owner's four answers (v1.13) | The source of BUD-BR-033, BUD-BR-034 and §4.11. Quoted at the head of this document. |
| Owner decisions 2 and 3 of 16 October 2026 and the answer “1. Yes” (v1.14) | The source of BUD-BR-035 and of BUD23-XD-004. Quoted at the head of this document. |
| Review of 16 October 2026 and the interim build made on the owner direction (v1.14) | The finding that Budget did not itself check a contract's award, and the interim check that now does (`require_authorised_reservation` in `kentender_budget`, `reservation_authority` in `kentender_contracts`). Observations; the requirement is BUD-BR-035. |
| CM-CHG-001 v0.8 §5.14, approved 14 October 2026 (v1.14) | The only approved text on a contract registered independently of a Tender: “An external registered contract does not automatically draw from KenTender Budget. Retain its funding-authority evidence and show Not linked to KenTender Budget. Adding a link later requires Budget’s verified opening/reconciliation contract, not conversion of already recognised liabilities a second time.” |
| Owner advice and instruction of 16 October 2026 (v1.15) | “Proceed with drafting CM v0.9 and the matching Budget amendment together.” The advice on verified lineage, on the record of the Tender, lot, Award and funding allocation, and on the existing-contract entry (who records, who approves, the evidence, the effect on availability, the shortfall rule) is adopted as the proposal. Advice, not an approved source. |
| Owner recommendations on seven open points, 16 October 2026 (v1.15) | “These recommendations should go into both [CM-CHG-001 v0.9] §20.7 and BUD24-XD-005, with matching workflow, controls and acceptance criteria. They remain proposed decisions until you approve them.” Applied in §§4.12, 5, 8.6 and 19.3. Recommendations, not an approved source. |
| Owner requirement on the allocation by Budget year, 16 October 2026 (v1.15) | “Finance confirms the opening obligation and the amounts allocated to each Budget year. The confirmation records the basis for the allocation and links the supporting contract and accounting evidence, including any applicable policy or instruction. The system checks that the amounts reconcile and identifies amounts already represented in Budget. Unresolved allocations prevent funding approval and commitment posting, while the request remains available for completion.” Applied in §4.12 and BUD-BR-037. A requirement the owner supplied, proposed until approved. |
| Owner decision of 16 October 2026 on revalidation, FU-CM-81 (v1.15) | “Approve a narrowly scoped amendment to Budget's 6 October decision. Allow the authorised CM integration to request Budget-owned revalidation of the exact reservations in the contract's approved funding package. This grants no general Budget access or power to change funds.” Recorded in CM-CHG-001_v0_8_FOLLOW_UPS.md (commit `aee6e9b2`), which itself says it is read as his decision, to be corrected if it was only a recommendation. Applied in §7 and BUD24-AC-019. |
| Record check of 16 October 2026 (v1.15) | Reservation: plan source allocation, drawdown line, Requisition reference, `source_set_hash` over the exact Requisition Version and its drawdown lines, payload digest. Commitment and conversion event: reservation, contract, amount, key, contract event. Tender, lot, Award, Award version and per-conversion allocation: not held anywhere. Observation of the build and of `procurement_requisitions/services/authorise.py`. |
| CM-CHG-001 v0.9, proposed 16 October 2026 (v1.15) | The matching Contract Management version: conversion event contents, corrections, independent-contract funding. Proposed, not approved; reviewed together with this version. |

The body is the to-be-implemented Budget contract. Historical references in §1 are disposition history, not permission to retain deleted executable concepts. Original files remain historical baselines. No current application behavior, code mapping or test result is asserted from these documents alone.

### 19.2 Full change register for re-implementation

The 30 BUD18 rows and 14 BUD19 rows remain the prior approved baseline change set. The four BUD20 rows below correct the denominator boundary. Total: **48 change rows**. **v1.11 adds BUD21-CHG-001, giving 49.** **v1.13 adds BUD22-CHG-001–004, giving 53.** **v1.14 adds BUD23-CHG-001–002, giving 55.** **v1.15 adds BUD24-CHG-001–006, giving 61.** Original counts, obsolete denominator instructions and old screen terminology in historical rows are traceability, not an alternative operative contract.

| ID | Prior issue / gap | Complete required change | Document locations | Verification references |
|---|---|---|---|---|
| BUD18-CHG-001 | Residual Planning reservation language | Purpose, ownership, Finance interaction and service arguments place holds only at successful REQ authorisation; no Budget Finance task. | §§2–3, 7–9, 12.6 | BUD18-AC-011, 014, 058, 063 |
| BUD18-CHG-002 | No transactional Finance provider | Add validate_plan_affordability_for_decision with owner-held serialization through caller commit and exact expected revision checks, without financial writes. | §§4.8, 8.2A, 9.1 | BUD18-AC-046–047 |
| BUD18-CHG-003 | Annual denominator contract missing | **Superseded by BUD20-CHG-001.** Do not implement the annual Budget denominator schema/service. Budget supplies ceiling and affordability evidence only. | §§4.8, 8.2B, 9.1 | BUD18-AC-048 as corrected; BUD20-AC-001–002 |
| BUD18-CHG-004 | Annual denominator could change in an unused line | **Superseded by BUD20-CHG-002.** Unused Budget headroom cannot change the Planning denominator; serialize Budget only for its funding decision. | §8.2A | BUD18-AC-049 as corrected; BUD20-AC-003 |
| BUD18-CHG-005 | Current and historical bases conflated | Explicit current versus exact historical Version/instant; preserve authoritative snapshot/precision and fail unreproducible replay. | §§4.8, 5, 8.2B, 9.1, 12.3 | BUD18-AC-050 |
| BUD18-CHG-006 | Float/minor-unit/precision boundary unspecified | Exact decimal-string currency units; at least 18 integral digits; supported scale, no rounding/epsilon, malformed/overflow rejection. | §4.8; all monetary services | BUD18-AC-051–052 |
| BUD18-CHG-007 | No Budget currency provider contract | Expose retained CurrencyBasis using verified native Company/precision mapping; no editable precision or inferred Company/accounting integration. | §§3, 4.1, 4.8, 9.1 | BUD18-AC-053 |
| BUD18-CHG-008 | Source-OU input ambiguous or treated as user scope | Require explicit source department for Need and direct sources; exact owner or Entity-wide eligibility after actor authorization; no tree inference. | §§4.4–4.5, 5 BR-007, 9.1 | BUD18-AC-009, 055 |
| BUD18-CHG-009 | Budget line human reference absent from specification | Return reference separately from root and exact Version IDs; preserve implemented reference behavior reported in FU-02. | §9.1 | BUD18-AC-054 |
| BUD18-CHG-010 | Catalogue changes could rewrite history or evade validation | Use CFG owner eligibility/decision contracts; disabling affects current use, historical IDs/labels remain; immutable line identity requires new line. | §§4.8, 9.1 | BUD18-AC-056 |
| BUD18-CHG-011 | Lifetime one-review-per-Version wording | At most one open whole-Plan review; immutable completed reviews, explicit reuse, basis staleness and Active reassessment through PLN. | §§1.1, 7, 8.1–8.2A, 12.6 | BUD18-AC-063 |
| BUD18-CHG-012 | Available funds confused with Planning affordability | Within-approved blocking; within-available advisory for Planning, availability blocking for REQ; preserve original/current evidence separation. | §§8.1–8.3, 12.6 | BUD18-AC-012–013, 064 |
| BUD18-CHG-013 | Reservation lacks owning REQ/drawdown identity | Persist exact REQ Version, drawdown/line, authorisation event and source OU; amount is authorised draw, not necessarily original Plan total. | §§4.5, 5 BR-011, 8.3 | BUD18-AC-058 |
| BUD18-CHG-014 | One-reservation-per-allocation lifetime rule | Uniqueness belongs to authorisation/drawdown line; later eligible draw against remaining original allowance has its own lineage. | §§4.5, 5 BR-011, 8.3 | BUD18-AC-058 |
| BUD18-CHG-015 | Each row could pass availability while their sum fails | Aggregate full request by Budget Line under locks; retain distinct drawdown reservations and exact shared-line shortfall. | §§8.3, 9.1, 15.5 | BUD18-AC-057 |
| BUD18-CHG-016 | Finance-task funding inputs and weak check/retry semantics | Replace with trusted REQ owner context; full-array bound expiring token, payload-aware idempotency and unique effect guard. | §§8.3, 9.1, 13 | BUD18-AC-018, 058–059 |
| BUD18-CHG-017 | All-or-none did not name complete owner boundary | REQ decision, Planning drawdown/scope guard, reservation set, handoff and outbox commit together; no partial orchestration. | §§8.3–8.4 | BUD18-AC-016, 047, 060 |
| BUD18-CHG-018 | Authorised correction/release could bypass immutable scope | Exact pre-consumption revocation, retained old evidence and governed successor; consumed handoff bars shortcut; release never resets scope lock. | §§8.1, 8.4 | BUD18-AC-060 |
| BUD18-CHG-019 | Conversion bound and release semantics ambiguous | Remaining-hold bound plus event-debit conservation; commitment decrease does not re-reserve; additional increase uses current available funds. | §§4.6, 8.4 | BUD18-AC-020–022, 061 |
| BUD18-CHG-020 | User-role wording omitted legitimate service effects | Separate live business-role writes from authenticated REQ/Contract owner-command effects; no service financial discretion or Draft reads. | §§3, 5 BR-001, 7, 9 | BUD18-AC-004, 038 |
| BUD18-CHG-021 | Return could obscure earlier submitted content | Retain each submission-attempt snapshot/document/decision; no-self-approval uses current submission authority. | §§6, 12.5, 14 | BUD18-AC-028, 062 |
| BUD18-CHG-022 | Closed Budget and audit semantics incomplete | Closed budget blocks new obligations but retains existing commitments and authorized decreases; reads/replays create no effective financial events. | §§5–6, 14 | BUD18-AC-018, 036, 050 |
| BUD18-CHG-023 | HWD seed owner excludes DHI laptop source | Make fresh canonical HWD line Entity-wide; never patch an Active real line’s owner in place; record data reconciliation gate. | §§11, 15.3, 19.3 | BUD18-AC-055, 068 |
| BUD18-CHG-024 | December artboards show Planning-created 80m hold | Default workspace/overview/lines/activity use 160m available and zero holds; conditional March screen shows two 20m / 30m HWD reservations. | §§11.1, 11.4–11.7, 15.4–15.4A | BUD18-AC-023, 065 |
| BUD18-CHG-025 | Funding event attributed to Finance; collapsed laptop reservation | REQ authorisation/Charles/service provenance; distinct HRMD and DHI rows with owner links; no manual Budget funding action. | §§11.6A–11.7, 12.4, 15.4A | BUD18-AC-016, 065 |
| BUD18-CHG-026 | Technical-read successor dated in future; revision floor borrowed from default | Use declared isolated March DHI 80m hold/Transfer scenario; retain v1.7 read-only route for technical actors. | §§11.1A, 11.8–11.15, 15.6 | BUD18-AC-045, 066 |
| BUD18-CHG-027 | Forbidden artboard painted header/filters; Server error row detached | Authorization-first inline Forbidden, valid four-state table and accessible navigation with server-denied approval surface. | §§10, 11.16, 12.1 | BUD18-AC-042–044, 067 |
| BUD18-CHG-028 | Seed allowed positive claims without prerequisite distinction | Separate BASE/conditional REQ/isolated revision; preserve SEED v1.3 and CFG-XD-001/legal/precision gates; never force BASE Active. | §15; §19.3 | BUD18-AC-023, 029–030, 069–070 |
| BUD18-CHG-029 | Follow-up ownership stale; funding catalogue called ownerless | Use approved CFG v0.10/LAW v1.1/SEED v1.3 and PLN v1.18; REQ/TPR/NDS/Contract/cross-module precision remain explicit dependencies. | §§3, 19.1–19.3 | BUD18-AC-070 |
| BUD18-CHG-030 | Acceptance IDs scattered; no complete reimplementation table | Map all 45 v1.7 criteria, add 25, and provide this full 30-row change register with locations and verification references. | §§16, 19.2, 20 | BUD18-AC-001–070 |
| BUD19-CHG-001 | BUD-UX-001: Workspace and pending work (§§10–12.1) | Cover no record, initial Draft, initial submission, current-with-update, returned and Closed states for Officer, Approver and readers. Keep one existing queue, Review navigation and changeable FY filter. | §§7.1, 10, 11.1B, 12.1 | BUD19-AC-001–002; Every actor finds the next step; no duplicate registration, invisible initial work, false current allocation or role switch. |
| BUD19-CHG-002 | BUD-UX-002: Registration and external evidence (§§4.1–4.2, 11.2, 12.2) | Record approved allocation; Approved allocation total; explicit year/currency; remove unassigned-ID input. Retain one exact approval document and make submit-time completeness explicit. | §§9.3, 11.2, 12.2 | BUD19-AC-003–004; No extra fields or appropriation workflow; valid partial save versus complete submit unambiguous; submitted evidence survives Draft replacement. |
| BUD19-CHG-003 | BUD-UX-003: Budget Line language and eligibility (§§4.3–4.4, 5, 11.3, 11.5–11.6) | Names before IDs; Available to / All departments; Amount; exact running total and mismatch labels. Source department remains exact domain eligibility, not user scope. | §§4.9, 11.3, 11.5–11.6A | BUD19-AC-005–006; No descendant expansion or missing-source fallback; all line facts remain; totals use exact Money and no silent rounding. |
| BUD19-CHG-004 | BUD-UX-004: Save, submission and correction (§§9.2, 11.3, 11.14–11.15, 12.2) | One user Submit for review includes pending valid edits via explicit existing command sequencing. Define scope, upload/link handling and original-result recovery; returned work opens the same Draft. | §§9.3, 11.3, 11.14–11.15, 12.2 | BUD19-AC-007–008; Save failure, partial success, unknown result, stale token and retry produce no duplicate record/attempt or overwritten history; no invented cross-command atomicity. |
| BUD19-CHG-005 | BUD-UX-005: Successor update and line identity (§§4.4, 5–6, 11.14–11.15, 12.2–12.3) | Update registered allocation; Type of change; reuse one pending successor; current record remains. Existing identity immutable. Distinguish permitted successor omission under BR-020 from deleting history. | §§5–6, 11.14–11.15, 12.2–12.3 | BUD19-AC-009–010; Amount-only edits on old lines; new purpose/scope/source uses new line. Transfer balances; omission allowed only without remaining reservation or active commitment and retains lineage. |
| BUD19-CHG-006 | BUD-UX-006: Changes-first review and live impact (§§11.8–11.11, 11.13, 12.5) | Show changes, external evidence and protected-amount comparison on opening review. Reserved + committed replaces Current floor; Available after update replaces Headroom; real blockers replace green checklist. | §§9.4, 11.8–11.13, 12.5 | BUD19-AC-011–012; Exact submitted Version and baseline; current protection as-at separate; all changed amounts/evidence and complete lines inspectable; guards recheck at approval. |
| BUD19-CHG-007 | BUD-UX-007: Approval and Return meaning (§6, §§11.8, 11.13, 12.5) | Approve registered allocation / Approve allocation update; visible activation consequence. Return for correction with existing reason and immutable attempt history. No repeated generic approval confirmation. | §§6, 9.3, 11.8, 11.13, 12.5 | BUD19-AC-013–014; One decision activates; no public-budget appropriation, cash release, Reject or extra stage; submitter cannot approve own submission. |
| BUD19-CHG-008 | BUD-UX-008: Understandable funding position (§§4.5–4.8, 5, 11.1, 11.4–11.6A) | Registered allocation; Reserved for requisitions; Committed to contracts; Available to reserve. Explain partial conversion and show coherent current/historical context. | §§4.9–5, 11.4, 11.19 | BUD19-AC-015–016; 100m−20m−60m=20m; no double counting, cash/payment implication or old-approved/live-ledger blend. |
| BUD19-CHG-009 | BUD-UX-009: Reservations, issues and event reading (§§4.5–4.7, 8.4, 11.6A–11.7A, 12.4) | Requisition/source names first; original/still-reserved amounts; Requires review—funds remain reserved. Read-only owner links; separate funding activity and Budget history. | §§11.6A–11.7A, 11.19, 12.4 | BUD19-AC-017–018; One reservation per drawdown line preserved; no automatic release, manual amount input, guessed route or recreated hold after commitment decrease. |
| BUD19-CHG-010 | BUD-UX-010: Finance/Planning and annual-basis boundary (§§7–9, 11.17, 12.6) | Keep whole-plan Finance work in Planning; live line view is separate from frozen review evidence. Explain approved-versus-planned blocking and available-funds advisory. **The former full-annual-denominator clause is superseded by BUD20-CHG-001–003.** | §§8–9, 11.17, 12.6 | BUD19-AC-019–020 plus BUD20-AC-001–004 |
| BUD19-CHG-011 | BUD-UX-011: Year-end closure completeness (§§6, 9.2, 10–12) | Provide Approver closure entry, pre-year-end, ready, held, unavailable and Closed states on existing surfaces. Focused closure confirmation and actual guard failure. | §§9.4, 11.18, 12.8 | BUD19-AC-021–022; No new role/workflow. Remaining reservations including Needs Attention block; active commitments alone do not. No payment claim; close revalidates at commit. |
| BUD19-CHG-012 | BUD-UX-012: Errors and shared readability (§§11.16, 12.7, 13) | Plain exact recovery, meaningful waiting/unknown states, structured evidence and readable responsive tables; preserve permitted input, focus and access protection. | §§9.3, 11.20, 12.7, 13 | BUD19-AC-023–024; No false zero/success, lost Draft or forced download. Keyboard/contrast/narrow-screen checks and user comprehension recorded. |
| BUD19-CHG-013 | BUD-UX-013: Complete actor and technical read coverage (§§7, 10, 11.1A, 12.2, 12.5) | Implement full actor matrix; reconcile blanket approval-route denial with AUTH v1.7 all-record technical read; no decision controls from technical access. | §§7.1, 10, 11.1A–11.1B, 12.2, 12.5 | BUD19-AC-025–026; Ordinary users, Approvers and technical readers get distinct correct outcomes across all statuses; no protected-data flash or title-based AO authority. |
| BUD19-CHG-014 | BUD-UX-014: Owner and fixture reconciliation (§§3, 15, 19.3) | Correct selected-line ownership to Planning source entry under approved NDS v1.12; retain approved source facts and isolated scenario chronology. Declare new breach/closure variants without merging March/December cases. Update completed sibling-document references without asserting implementation closure. | §§3, 15.8, 19.1–19.3 | BUD19-AC-027–028; No Need funding field, invented REQ authorisation/contract event, altered HWD scope in live history or forced positive end-to-end date evidence. All 70 prior AC and 30 change rows remain traceable. |
| BUD20-CHG-001 | Budget was incorrectly made owner of the 30% Planning denominator. | Remove `AnnualProcurementBudgetBasis.v1` and `get_annual_procurement_budget_basis`; BUD returns ceiling/affordability evidence only. | §§2–4, 8–9 | BUD20-AC-001–002 |
| BUD20-CHG-002 | Unused Budget-line changes were made capable of staling the statutory Planning calculation. | Scope Budget concurrency to affordability; Plan/rule Versions control the 30% calculation. | §§8.2A–8.2B | BUD20-AC-003 |
| BUD20-CHG-003 | BASE/READY and annual-basis fixtures asserted KES 48m / 31.25%. | Use Planning's KES 130m eligible APP value, KES 39m target and 38.46% qualifying share; retain KES 160m only as ceiling. | §§15.4–15.5 | BUD20-AC-004 |
| BUD20-CHG-004 | Historical criteria and dependencies could reintroduce the obsolete service. | Mark affected BUD18/BUD19 rows superseded/corrected and require removal with no compatibility alias. | §§16, 19–20 | BUD20-AC-005 |
| BUD21-CHG-001 | Planning had no in-product way to ask Budget for a line revision (PLN-CHG-001 v1.27 §§7.7, 15.2). | Add the Budget Revision Request record, Planning service principal, receive/decline/withdraw commands, Revised-on-activation and closure rules, outcome event, Budget Officer workspace row and decline dialog, errors, audit, fixture and acceptance. No revision object, role, Version state or financial effect. | §§1.1, 3, 4.9–4.10, 5, 6, 7, 8.1, 8.5, 9.2–9.3, 11.1B, 11.6, 11.21, 12.1, 13, 14, 15.8, 16.4, 17.2, 18 | BUD21-AC-001–008 |
| BUD22-CHG-001 | Committed counted `Active` commitments only, so a contract's closure could be read as freeing its money. | Count Active and Closed commitments at their retained amounts. Reconcile availability, the successor floor, the omission test, the labels and the closure wording. | §§1.1, 4.6, 4.9, 5, 6, 9.4, 11, 15.8 | BUD22-AC-001–003 |
| BUD22-CHG-002 | `close_commitment` had no requirement home: it was a Contract Management proposal and built code. | Add the service, BUD-BR-032, the audit event, the contract principal's call list and the error codes. | §§1.1, 7, 8.4, 9.1, 13, 14 | BUD22-AC-004 |
| BUD22-CHG-003 | A Closed commitment could be lowered by the contract service, with no evidence in the build and with evidence in this version's first draft. | A Closed commitment accepts no increase and no ordinary adjustment; reopening in Contract Management changes no funding. Supersedes the allowance, and an earlier recommendation that corrections come only from Contract Management. | §§1.1, 4.6, 5, 8.4, 9.1 | BUD22-AC-005, BUD22-AC-009 |
| BUD22-CHG-004 | No way to correct a Closed commitment's amount at all except through the contract service. | Add the Commitment Correction record, the two commands, BUD-BR-034, the carve-out of BUD-BR-015 and §§2, 7, 12.8 for the one money movement a person records, the ledger events and errors. | §§1.1, 2, 4.11, 5, 7, 8.4, 9.2, 9.3, 12.8, 13, 14, 15.8 | BUD22-AC-006–008 |
| BUD23-CHG-001 | Budget trusted the contract caller: any open reservation with enough remainder could be converted for any contract, and the conversion event carried no chain. | A conversion is valid only when the whole chain matches, checked against references the owning modules supply in the event; no chain and a mismatch are refusals; every allocation of an award is checked before any converts. | §§1.1, 3, 4.6, 5, 7, 8.4, 9.1, 13, 15.8 | BUD23-AC-001–011 |
| BUD23-CHG-002 | A contract registered with no tender in KenTender had no stated funding path, and the approval of independent entry did not approve one. | Record the path as missing, cite the approved text and the code, and list the decisions and the controls an onboarding route needs. No rule is specified. | §§1.1, 19.1, 19.3 | BUD23-XD-004 |
| BUD24-CHG-001 | v1.14 trusted the references the first caller supplied and proposed recording them. | Verify the lineage at the first conversion through the owning modules' published contract; retain the verified Tender, lot, Award and version and allocation on the commitment and the conversion event; leave the reservation unchanged. | §§1.1, 4.5, 4.6, 5, 9.1, 13, 14 | BUD24-AC-001–003 |
| BUD24-CHG-002 | A contract with no tender in KenTender had no funding path (v1.14, “missing”). | Add the existing-contract commitment entry for KenTender Budget-controlled funding, with allocation rows and an amount the system calculates from Finance's confirmed figures; the contract funding request, one identity reachable from both modules; the two commands and BUD-BR-037–039; nothing in Budget for externally controlled funding. | §§1.1, 2, 4.12, 5, 7, 8.4, 8.6, 9.2, 9.3, 13, 14, 15.8 | BUD24-AC-004–011, BUD24-AC-013, BUD24-AC-014, BUD24-AC-016 |
| BUD24-CHG-006 | The contract service principal could not request revalidation of its own reservations, so a reservation lost between award and signing was found only when the conversion was refused, after both signatures (FU-CM-81). | Allow `revalidate_reservations` for the contract principal, only for the reservations the funding-lineage owner confirms for that contract; nothing else in the 6 October 2026 list changes. | §7 | BUD24-AC-019 |
| BUD24-CHG-005 | The calculation of the amount requiring funding had no stated basis for allocating a confirmed obligation to Budget years. | Finance confirms the allocation by Budget year inside the existing opening-position confirmation, with its basis and the supporting contract and accounting evidence, citing any applicable policy or instruction; the system proposes and reconciles; an incomplete allocation shows Year allocation required and blocks approval and posting, not the request. | §§4.12, 5, 8.6, 13, 15.8 | BUD24-AC-017, BUD24-AC-018 |
| BUD24-CHG-004 | After a reopening there was no stated way to fund an additional obligation, and a Closed commitment accepts no increase. | Reopening restores nothing; only the additional amount is funded, by an Additional entry or a new conversion, beside the original commitment (BUD-BR-040). | §§4.12, 5, 19.3 | BUD24-AC-015 |
| BUD24-CHG-003 | A commitment always reached its Budget Line only through its reservation. | A commitment carries its Budget Line and origin directly; the reservation link is required only for a conversion; every reader of Committed reads the line from the commitment. | §§4.6, 5, 19.3 | BUD24-AC-012 |

All shortened `BUD18-AC` ranges in the final column refer to §16. Approval applies to this complete successor, including the reconciled fixture and UI rules; individual rows are not a second specification.

### 19.3 Remaining implementation and sibling-document register

| ID | Outstanding item | Owner / required evidence | Status and effect |
|---|---|---|---|
| BUD18-XD-001 | FU-23 provider adoption | BUD/PLN: inspect actual service/schema, publish mappings, remove obsolete annual-denominator artifacts, add display/decision/ceiling-separation tests, prove compatible locking and caller rollback. | Documented here; implementation and integration unverified. Attach evidence to the implementation tracker; do not mark code Done from this MD. |
| BUD18-XD-002 | FU-30 cross-module precision | BUD/NDS/REQ/PLN: shared exact-decimal suite and storage/arithmetic scan; replace float/epsilon paths; reconcile existing persisted values with authoritative evidence. | Release prerequisite. No automatic rounding migration or assertion that binary-float history can be recovered exactly. |
| BUD18-XD-003 | Explicit Company/currency/UOM metadata mapping | CFG/BUD/REQ: inspect repository/native owner fields; declare supported scales and token lifetime; demonstrate no accounting-ledger dependency. | Implementation prerequisite; no inferred defaults/native fields. |
| BUD18-XD-004 | REQ v1.8 / TPR v0.8 matching caller amendment (FU-25) | Adopt owner drawdown naming, scope/hold errors, correction outcome and requester follow-up, exact reservation mappings and one complete-array token semantics. Coordinate old REQ prose saying per-line returned tokens; no dual response contract. | REQ v1.8 has been produced as a proposed sibling successor; its approval and TPR/caller implementation remain separate. This Budget successor does not approve or deploy them. |
| BUD18-XD-005 | NDS source/eligibility integration | Approved NDS v1.12 now documents its source/disposition/readable Planning rules. Budget Line selection belongs to Planning, never the Need. Verify exact quantity/source handoff and eligibility without a Need Money field. | Sibling specification completed; implementation evidence remains outstanding. |
| BUD18-XD-006 | HWD owner mismatch in already populated data | BUD/SEED/REQ/PLN: compare actual line history and references; rebuild only authorized disposable fixtures or prepare a reviewed new-line/governed-successor correction for retained data. | No silent Active-line edit. Document affected IDs, evidence and migration outcome before declaring seed/data alignment. |
| BUD18-XD-007 | Canonical date/production-rule prerequisites | CFG/LAW/SEED: resolve CFG-XD-001 and LAW v1.2 verification items; preserve verified applicability evidence. | Conditional positive end-to-end claim remains blocked where these prerequisites fail. Budget does not decide the statutory denominator. |
| BUD18-XD-008 | Exact isolated revision hold event | SEED/REQ: freeze a valid authorisation event before 15 Mar 13:10 for the independent DHI 80m scenario, with live authority and lawful/applicable prerequisites. | Artboard/provider-test scenario specified; integrated execution requires owner evidence. Do not borrow laptop events or invent a Finance hold. |
| BUD18-XD-009 | Contract conversion/adjustment integration | Contract owner: authenticated event schemas, exact lineage, conservation, cancellation and closed-budget restrictions, idempotency and tests. | Keep actions unavailable until the approved caller and evidence exist; no manual Budget substitute. |
| BUD18-XD-010 | Shared standard/citation and fixture adoption | KT-STD/SEED owner: retain Budget actors and scenario index; perform FU-27 technical-read citation cleanup with the actual controlling standard. | Editorial/shared-fixture follow-up; no new technical-read right and no claim that an unseen later standard was reviewed. |
| BUD18-XD-011 | Full UI/artboard implementation and review | Budget UI owner: implement the approved §§11–12 usability compositions, including pending work, changes-first review, closure and all-state task reading; verify keyboard/focus, narrow-screen amounts, full evidence and representative-user understanding. | Required implementation evidence. This document corrects completeness; it does not claim user-tested experience or completed artboards. |
| BUD19-XD-001 | Save/submit/upload recovery | BUD UI/service/file owner: inspect actual token granularity, reply IDs, file-link transaction and authorised idempotent outcome replay; prove §9.3 including partial scope saves and browser reload. | Implementation gate; no claim of atomic multi-save or fabricated current endpoint. |
| BUD19-XD-002 | Closure composition and concurrent guards | BUD/Contract/REQ owners: implement existing command UI; prove before-year-end/held/unavailable/ready/Closed, concurrent financial mutation and original-result replay; declare valid future test assignments/events. | Documentation complete; executable closure and owner reconciliation evidence required. |
| BUD21-XD-001 (v1.11) | Planning/Budget request transaction and outbox | BUD/PLN: prove `receive_budget_revision_request` commits or rolls back with Planning's `RequestBudgetRevision`, the outbox delivers `BudgetRevisionRequestOutcome.v1` idempotently and in order, and Planning consumes it. | Implementation gate; documented here, not implemented. |
| BUD21-XD-002 (v1.11) | Segregation open question | Project Owner: should a Finance Confirmation Officer be barred from confirming funding for a plan whose Budget Line they revised as Budget Officer? The shared fixture gives Josphat both roles. | Open. v1.11 adds no such rule; the existing no-self-approval rule is unchanged. |
| BUD19-XD-003 | Historical versus proposed omission and evidence | BUD migration/read owner: map omitted successor membership without deleting prior line identities, attempt snapshots or attachments; test live zero-protection revalidation and exact historical replay. | No blanket delete or silent unlock of approved line identity. |
| BUD22-XD-001 (v1.13) | Metadata reload and migration test | Budget owner: the Commitment Correction record type and four Budget Audit Event types (Commitment closed, Commitment correction recorded, Commitment correction returned, Commitment corrected) are metadata the site must load. Reload them by migration on any site that will close or correct a commitment, and test that migration on the test site. Do not migrate the dev site without the owner's go-ahead. | Open. Loaded on the test site by reloading the two record types; the dev site has not been migrated. |
| BUD22-XD-002 (v1.13) | Closure and correction against the real Budget on the canonical award | BUD/CM: form the canonical award through the real owner hooks, convert, close, reopen, correct, and repeat each call at the same revisions (FU-CM-118). Blocked by the Contract Management source gaps FU-CM-70, FU-CM-71 and FU-CM-72. | Open. Budget's own tests and the simulated funding owner do not substitute. |
| BUD22-XD-003 (v1.13) | Contract Management's closure-correction path | CM owner: a contract record reopened or corrected after closure must not call `adjust_commitment` on a Closed commitment; the funding change goes through a Budget correction that cites a Contract Management reference. No Contract Management caller adjusts a Closed commitment today. CM-CHG-001 v0.8 §5.14.1 needs the matching version. | Open; a Contract Management document change is required. |
| BUD22-XD-004 (v1.13) | The correction screens | Current §11.22 specifies D20. Render, implement and verify normal-role interaction, stale/self-approval/closed-year variants and line-detail history. | Requirements specified in this proposal; rendering/build/evidence remain open. |
| BUD22-XD-005 (v1.13) | Partner guide alignment | Apply the current correction, independent/annual funding and truthful capability wording. Remove the internal build-status table; retain implementation evidence in the internal tracker. | Current guide was not supplied; update/verification remains open. No claim about its present text or completed change. |
| BUD23-XD-001 (v1.14) | The chain is not held or supplied today | BUD/REQ/Tender owner/Award/CM: the conversion event carries only the reservation, contract, amount, key and contract event. A reservation stores no Requisition Version, authorisation event, Tender, lot or Award (v1.12 §4.5 names `requisition_version_id` and `authorisation_event_id`; the build has neither). Each owner must supply its link, and Budget must record what it first receives so later conversions can be compared. The owner decides whether record-and-compare is the right rule. | Open. An interface change in Budget, Requisitions and Contract Management at least; the Contract Management version is named below. **v1.15 correction:** the exact Requisition Version is already bound through the reservation's `source_set_hash`, so Budget needs no new reservation field for it (§4.5). What Budget lacks, and must retain on the commitment and the conversion event, is the Tender, lot, Award and version and the per-conversion allocation; BUD-BR-036 specifies it. |
| BUD23-XD-002 (v1.14) | The interim check | Until the chain exists, Budget asks Contract Management, through `kentender_core.services.contract_reservation_authority`, whether the contract's effective agreement names the reservation, and refuses on no or no answer. It is fail-closed and tested, and it is an interim substitute: it uses Contract Management's own record of the award, not a chain Budget can check. Reconcile or retire it when the chain is built. | Built and tested on the test site; not the requirement. |
| BUD23-XD-003 (v1.14) | Awards that name more than one reservation | Allocation/verification requirements are now specified in AWD v0.7 §7.1. Build the actual provider and verify full-set lookup/replay/rollback against expected total; a partial lookup cannot claim complete funding. | Requirements specified, Proposed; implementation/integrated evidence open. No allocation-policy question remains on this row. |
| BUD23-XD-004 (v1.14) | Independently onboarded contract funding | BUD §§4.12/8.6–8.8 and CM v0.10 §20 now specify the two routes, request/entry states, annual funding, evidence, holds and separate participants. No synthetic procurement records. | Requirements specified, Proposed; the two approved product decisions are recorded at the head. Build/migration/native/integration evidence remains open; the path is not “missing”. |
| BUD24-XD-001 (v1.15) | The commitment record and every reader | Budget owner: a commitment gains `budget_line_id`, `origin` and `lineage`, and `reservation_id` becomes optional. Today the Procurement Commitment record has the reservation link only, and Committed is read by joining commitments to reservations to lines. Readers found: the line position, the Procurement budget-line use read, the analytics queries, the funding lineage read, and the commitment services (adjust, close, correct). All must read the line from the commitment, with a parity test over both origins and a migration that sets the line on existing commitments from their reservations. | Open. A schema and reader change; not built. |
| BUD24-XD-002 (v1.15) | The Award lineage verification contract | AWD owner: publish a read contract that, for an award reference and a reservation, returns the verified Tender, lot where the source carries one, Award and version, funding allocation and package digest, or says it cannot verify. Add a `kentender_core` seam and have Budget consume it. The interim check built under v1.14 (BUD23-XD-002) is retired when it exists. Needs an Award version. | Open. Not built; Award document change required. |
| BUD24-XD-003 (v1.15) | The Budget screens | Current §11.22 specifies pending work, D21 preparation and D22 review/history. | Requirements specified in this proposal; rendering/build/evidence remain open. |
| BUD24-XD-004 (v1.15) | Contract Management coordination | CM owner: CM-CHG-001 v0.9 (proposed with this version) defines the conversion event's contents, the funding request and its outcome, the funding route of an existing contract, the holds and the Not linked label. Both documents are reviewed together; neither is approved alone for the behaviour they share. | Open; reviewed together. |
| BUD24-XD-005 (v1.15) | Coordinated funding decisions | Current §§4.12/8.7 and CM v0.10 §20 replace the earlier eight-point advice table. Use actual CM Finance approval, one supported target year/currency, verified Budget-only coverage and complete request/entry states. | Proposed for review; no “nothing left open” claim. Exact current adapter/role/deployment evidence remains required. |

Future facilities remain owned by their approved change units: accounting/expenditure integration, automated financial-system reconciliation, expanded tender/scope-amendment handling and new multi-year tender procurement are not enabled by this document; annual funding of supported independently onboarded contracts follows §8.8. Missing owner functionality must produce an explicit supported-state limit, not a manual bypass.

### 19.4 Current coordinated disposition — v1.16

| Item | Current requirement and evidence boundary |
|---|---|
| BUD22-XD-004 / BUD24-XD-003 | Browser requirements now specified by §11.22; implementation, rendering and role-based verification remain open. API-only correction does not satisfy acceptance. |
| BUD24-XD-002 | AWD v0.7 §7.1 supplies the proposed source verification/allocation interface; actual TPR/issued-price adapter mapping and verification remain release evidence, not assumed installed. |
| BUD24-XD-004/005 | CM v0.10 §20 and current §§4.12/8.7 replace the earlier “nothing left open” claim. Current requirements are Proposed; their review does not certify implementation. |
| Earlier approval conflict | Source v1.13 narrative and its control row disagree about post-close correction authority. Preserve their history; current BUD-BR-034 is Proposed, not a reconstruction of the owner’s earlier answer. |
| Scope | REQ v1.19 and KT-STD v1.30 are unchanged. Tender-derived procurement remains single-year. Annual funding of already executed independent contracts is adopted under §8.8; no FX, NGO or World Bank profile is added. |
| Partner guide | Remove the internal build-status table and repeated proposed-exception wording. Keep implementation defects/evidence in the existing internal tracker. Describe intended capabilities without representing unfinished controls as deployed. Current guide/register files were not supplied and are not claimed changed. |
| Integration metadata | Normal migration and actual site verification remain required. Retained source statements saying a site was or was not migrated are dated observations, not current verification. |

Source basis: supplied BUD v1.15, REQ v1.19 §§5.1/5.3/5.6/5.12, AWD v0.6, CM v0.9 §§5.12/5.13/6/20, AUTH v1.15 and KT-STD v1.30. No current law, repository or database was independently inspected for this revision. No schema/API names outside these logical contracts are asserted installed.

## 20. Approval effect

**Current approved effect — BUD-CHG-001 v1.16, 16 October 2026.** The Project Owner’s “Mark them as approved” adopts this complete successor, including the independent funding-basis confirmer/Budget-Approver separation and annual funding for supported independently onboarded contracts where applicable to this owner. The current source allocation, money model, task/screen/role/interface provisions and their stated acceptance criteria are controlling. Tender-derived procurement remains single-year and cross-currency funding remains excluded. Approval grants no new exception to existing legal, financial, native accounting or release controls. The following proposal-era effects are retained history and are superseded for this version by this record.


### 20.0N Current v1.16 approval effect — Proposed

Approval would adopt the current §§4.12/8.7, request lifecycle, usable screens and BUD25-AC-001–013 alongside the retained rules as explicitly corrected. BUD v1.12 remains the approved baseline until then. Shared behaviour requires coordinated review with AWD v0.7, CM v0.10 and AUTH v1.16. The two adopted decisions include independent annual funding and confirmer/Approver separation; this successor as a whole remains Proposed. It does not approve a foreign-currency extension or new multi-year tender procurement, a migration, test success, current-law clearance or release. Historical acceptance/change-row totals below describe their versions only; this successor makes no unverified total-count claim.

### 20.0 v1.15 approval effect (proposed, not yet approved)

**BUD-CHG-001 v1.15 is proposed.** It carries v1.14 and v1.13 in full. If the Project Owner approves it, it supersedes v1.12 and makes binding everything in §20.0A and §20.0B plus: the verification of lineage at the first conversion and its retention on the commitment and the conversion event, with the reservation unchanged (BUD-BR-036); the existing-contract commitment entry, its two-person authority, its evidence, its effect on availability and its duplicate and correction rules (BUD-BR-037–040, §4.12); the contract funding request (§8.6); the commitment's line, origin and lineage (§4.6); `BUDGET_ENTRY_DUPLICATE`, `BUDGET_ENTRY_ROWS_MISMATCH` and `BUDGET_YEAR_ALLOCATION_REQUIRED`; BUD24-SC-EXISTING-ENTRY; and BUD24-AC-001–019. The operative register would become **150 acceptance criteria** and **61 change-register rows**.

Approval would add no role, Version state or approval stage. It would add a second way a person records a money movement, which creates a commitment only from a reconciled existing contract and needs two different people, and a commitment with no reservation, and a calculated amount that can be funded across several rows. BUD24-XD-001–005 remain open: the schema and reader change, the Award lineage contract, the screens, Contract Management v0.9, and the eight proposed decisions in BUD24-XD-005. Approval is a requirements decision, not implementation or test evidence.

### 20.0A v1.14 approval effect (proposed, not yet approved; carried in full by v1.15)

**BUD-CHG-001 v1.14 is proposed.** It carries v1.13 in full. If the Project Owner approves it, it supersedes v1.12 and makes binding everything in §20.0A below (v1.15 read: §20.0B) plus: the rule that a conversion is valid only when the whole chain matches, with a missing chain as a refusal (BUD-BR-035); `BUDGET_RESERVATION_NOT_AUTHORISED`; BUD23-SC-LINEAGE; and BUD23-AC-001–011. The operative register would become **131 acceptance criteria** and **55 change-register rows**.

Approval would add no role, Version state, approval stage or manual financial control. It would add one refusal condition to an existing call, and an interface change that Contract Management and the owners of the chain must meet before a conversion can pass. It would not approve any funding path for a contract with no tender in KenTender: BUD23-XD-004 records that path as missing. BUD23-XD-001–004 remain open. Approval is a requirements decision, not implementation or test evidence.

### 20.0B v1.13 approval effect (proposed, not yet approved; carried in full by v1.14 and v1.15)

**BUD-CHG-001 v1.13 is proposed.** If the Project Owner approves it, it supersedes v1.12 and makes binding: Committed counting Active and Closed commitments at their retained amounts, reconciled across availability, the successor floor and the omission test (BUD-BR-031); `close_commitment` and its audit event (BUD-BR-032); the refusal of any change to a Closed commitment by the contract service (BUD-BR-033); the Commitment Correction and its two-person process (BUD-BR-034, §4.11); the carve-out of BUD-BR-015; the error codes; BUD22-SC-CLOSED-RETAINED; and BUD22-AC-001–009. The operative register would become **120 acceptance criteria** and **53 change-register rows**. That is the count for v1.13 alone. v1.14 carries v1.13 and adds to it, and its own count is in §20.0. (v1.15 read: §20.0A; v1.15's own count is in §20.0.)

Approval would add no role, Version state or approval stage. It would add one money movement that a person records, the correction, which only lowers an amount and needs two different people. BUD22-XD-001–005 remain open. Approval is a requirements decision, not implementation or test evidence.

### 20.1 v1.11 approval effect (retained)

**BUD-CHG-001 v1.11 is approved by the Project Owner** as a targeted successor. It supersedes v1.10. Approval makes the following binding: the Budget Revision Request record (§4.10); BUD-BR-027–030; the Planning service principal and the receive, decline and withdraw commands (§§7, 8.5, 9.2); Revised on successor activation and Declined on closure; the outcome event; the Budget Officer's workspace row and decline dialog (BUD-DES-18, BUD-DES-19); two error codes; the BUD21-SC-REVISION-REQUEST fixture; and BUD21-AC-001–008. The operative register becomes **111 acceptance criteria** and **49 change-register rows**.

Approval adds no role, Version state, approval stage, reservation behaviour, Finance surface or planner-waiting screen, and changes no v1.10 financial rule. An increase still requires external approval registered through an ordinary successor Version. BUD21-XD-001 and BUD21-XD-002 remain open. Approval is a requirements decision, not implementation or test evidence.

### 20.2 v1.10 approval effect (retained)

**BUD v1.10 is approved by the Project Owner.** It supersedes BUD v1.9 and all earlier Budget & Funding implementation specifications in full.

This approval retains v1.9's usability, Budget lifecycle, exact Money, affordability, Requisition reservation, commitment, audit and actor contracts while removing the obsolete annual-denominator schema/service and correcting all dependent fixtures, criteria and change rows. The resulting operative register has **103 acceptance criteria** and **48 change-register rows**. BUD20-CHG-001–004 and BUD20-AC-001–005 prevail over the named historical conflicts.

Approval records requirements/design decisions, not deployed code, completed migration, passed consumer/transaction/browser tests, representative-user acceptance, current-law verification or closure of §19.3. Keep conditional downstream fixture and Contract integration gates visible. Financial service effects remain governed; there is no manual workaround, new appropriation step or accounting integration. Approved PLN v1.25, CFG v0.13 and LAW v1.2 provide the coordinated owner contracts.


## Current revision record — 16 October 2026

Source: `KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1_15.md`, SHA-256 `bdc5b2c374e06ef328f88d9d729622cfdb83e70d18787a1d83078c834886594d`. The supplied source file is unchanged. This successor preserves unaffected sections, stable acceptance IDs and historical approval records. Replaced operational wording is superseded by the explicitly current provisions; older factual build observations are not fresh verification. Status: Proposed. Code, database, guide, seed owner and live control registers were not modified.


**Draft update — 16 October 2026, after “Adopt”.** Incorporated the two approved product decisions and review cleanup without marking the complete successor approved. Full-document approval, implementation, guide/control-register updates and verification remain separately outstanding. Original supplied source files are unchanged.


**Approval record addition — 16 October 2026.** Full-version approval above supersedes the earlier record that only two product decisions had been adopted. No code or other owner content was changed by recording approval.
