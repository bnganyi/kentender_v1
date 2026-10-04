# SEED-001 — Harmonized End-to-End Fixture

| Control | Value |
|---|---|
| Document ID | SEED-001 |
| Version | 1.3 |
| Date | 12 September 2026 |
| Status | **Approved** |
| Approved on | 12 September 2026 |
| Approval record | Project Owner approval in this review: “Approved”. |
| Predecessor | SEED-001 v1.2, approved 11 September 2026; retained as historical evidence |
| Approval effect | Replaces v1.2 as the approved shared fixture contract. This document does not claim that sibling documents, code or tests have already been updated. |
| Purpose | Reconcile the shared Ministry of Health fixture with PLN-CHG-001 v1.18, preserving exact cross-module lineage, lawful-governance prerequisites, scenario separation and testable implementation requirements. |
| Standards baseline inspected | KT-STD-001 v1.4 and AUTH-ADR-001 v1.7. KT-STD v1.5 and SEED-OPS-001 mentioned in Claude Code's follow-ups were not supplied and are not treated as inspected authorities. |
| Primary change basis | PLN-CHG-001 v1.18 §§4, 7–8, 10.1, 10.9, 13, 15 and 17.2; FU-20 in PLN-CHG-001_FOLLOW_UPS.md, qualified by the follow-up review |
| Change register | §9 contains every substantive correction in this successor and its acceptance mapping. |

One site represents one Procuring Entity: Ministry of Health, fixture reference `PE-MOH`. This reference identifies the fixture entity; it does not introduce a Procuring Entity selector or a new per-record PE authority field. Historical KEBS tender examples retained as external template-curation evidence are distinct from executable MOH seed records.

## 1. Authority, source precedence and scenario boundaries

### 1.1 Source documents

| Source inspected | Authority used here | Remaining coordination |
|---|---|---|
| PLN-CHG-001 v1.18 | Current Planning identities, chronology, governance, source boundaries, reservation readiness, publication and scenario separation | Real implementation and affected integrations still require evidence. |
| NDS-CHG-001 v1.10 | Need references, accepted revisions, immutable source facts and departmental lifecycle | Harmonize chronology/scopes and add the separate disposition contract in its next amendment. Do not infer approval from this seed. |
| STR-CHG-001 v1.7 | Objective selection, lineage and deterministic approval-time snapshot | Verify the consumer contract against the exact reviewed Strategy Version/path. |
| BUD-CHG-001 v1.7 | Budget references, amounts and Requisition-stage reservations | Decision-basis, annual denominator and precision amendments remain prerequisites. |
| REQ-CHG-001 v1.7 | Requisition identifiers, source drawdowns, operational required-by date and reservation references | Reconcile permanent scope locks, correction outcomes and exact monetary/quantity contracts. |
| TPR-CHG-001 v0.7 | Tender identity, specification, template binding and preparation segregation | Reconcile invitation-event contract and remove stale claims that the Planning correction receiver is undesigned. |
| TPUB-CHG-001, internal version 0.3 | Tender publication actor/caller boundary | Uploaded filename says v0.1; use its internal control version. Actual event integration remains subject to the coordinated amendment. |
| CFG-CHG-002 v0.9 | Shared entity, authority route, intake and configuration ownership | Required fields, resolvers, profiles, surfaces and historical evidence need the coordinated amendment. |
| LAW-REG-001 v1.0 | Supplied legal-correction register and identified verification dependencies | This document performs no new primary-source legal verification. Rule values below are not certified production law. |
| SEED-001 v1.2 | Existing MOH references, specification and two-reservation fixture | Superseded by this approved successor; conflicts are corrected explicitly in §9. |

This document supplies the shared fixture facts; each module continues to own its domain, commands, authorization and evidence. It does not assert blanket approval of REQ or TPR. The predecessor's control text and §1.2 contradicted one another about those approvals; actual approval records govern.

### 1.2 Three distinct uses of the fixture

| Scenario | Exact meaning | Permitted outcome |
|---|---|---|
| **BASE** | Original 2 Plan Items, 3 accepted Need sources and KES 130,000,000 Plan. Both planned designations are None. With the illustrative 30% rule and KES 160,000,000 annual denominator, qualifying allocation is zero. | Draft consolidation and negative readiness verification. Mandatory reservation shortfall prevents positive submission/approval. No Active Plan or authorized downstream procurement is derived from BASE. |
| **READY — visual** | PLN v1.18's UI-only variant changes the laptop planned designation to Youth. KES 50,000,000 qualifies under the illustrative scenario assumptions. | Demonstrates calculation and screen states. It is not an executed business history, approved integrated seed or legal eligibility determination. |
| **READY — integrated test candidate** | Approved integrated test scenario design, isolated from BASE and from production configuration. Same identities/amounts in a separate reset/replay world; explicitly declared test rules and evidence. | This seed amendment is approved. Execution requires its exact test configuration to be approved and applicable provider contracts to exist. It produces test evidence only. Production-equivalent readiness requires verified applicable rules; a fixture label cannot satisfy that gate. |

Approval of this successor explicitly approves the integrated READY test scenario design; the earlier UI proof-of-concept approval alone did not do so. BASE remains the canonical executable blocked case. Integrated READY execution remains subject to the exact test-configuration and provider prerequisites stated above. Do not silently change BASE's designation, reduce its denominator, relax required validations or hard-code approval states to preserve the predecessor's happy path.

PLN's UPDATE, PUBLICATION, EXECUTION and CONFIG artboards remain separately declared presentation scenarios unless an approved command-driven test builds their history. References and screenshots alone do not prove execution. A production site must not obtain legal readiness merely from test configuration labelled `Fixture-verified — not production law`.

### 1.3 Rule status and execution manifest

`Production verification pending` is the required presentation for unresolved production rules. `Fixture-verified — not production law` is the approved test-fixture provenance label, not a newly authorized CFG enum or a substitute for `verification_status = Verified`. CFG owns the final stored vocabulary and resolver behavior.

Every executable run records the scenario, document versions, seed/build revision, site timezone, configured FY identity and actual date bounds, rule/profile IDs and versions, provenance, actor assignments, clock instants, command results and artifact hashes. An isolated test configuration must be explicit in that manifest; production selection must not accept it as legally verified configuration. If no supported test mechanism exists, leave the positive scenario unexecuted rather than bypassing the business service.

The source pack labels the period **FY 2027/28** while using the dates below. Preserve those stated values, but obtain the actual FY bounds from the authoritative fixture/configuration contract. Do not infer dates from the label, disable within-FY validation or silently redefine a fiscal period to make the fixture pass. An incompatible configured period is an open CFG/SEED reconciliation issue before execution.

## 2. Complete lineage and invariants

| Stage | Stable fixture reference | Relationship |
|---|---|---|
| HRMD laptop Need | `NDS-MOH-2027-0003`, accepted Revision 2 | 100 Each; DPP entry `DPPE-MOH-HRMD-2027-001` |
| DHI laptop Need | `NDS-MOH-2027-0004`, accepted Revision 1 | 150 Each; DPP entry `DPPE-MOH-DHI-2027-002` |
| Laptop Plan Item | `PPI-MOH-2027-033` | Both sources; 250 Each; KES 50,000,000; line `MOH-BL-HWD-2027` |
| HRMD allocation | `PSA-MOH-2027-033-001` | Exact HRMD DPP entry/Need revision; 100 Each; KES 20,000,000 |
| DHI allocation | `PSA-MOH-2027-033-002` | Exact DHI DPP entry/Need revision; 150 Each; KES 30,000,000 |
| Requisition | `REQ-MOH-2027-033-001`, Version 1 | Draws the exact eligible Active Plan/item/allocation versions in the positive scenario |
| Tender | `TND-MOH-2027-033`, Version 1 | Consumes the authorized Requisition handoff and binds `IT-EQUIPMENT-OPEN-V1`, template version 1.1 |

Plan inclusion, authorized proceeding coverage, tender publication and fulfilment are separate facts. The source Needs remain traceable throughout; neither Plan activation nor Tender publication proves delivery. Exact root/version IDs returned by services accompany business references in seed evidence. A copied Plan Version cannot reset consumed capacity or permanent scope-lock history.

`NDS-MOH-2027-0001` and its infrastructure item are part of the same Annual Plan, not an optional disconnected example. The isolated security-assessment direct requirement in PLN's UI pack is excluded from BASE and READY totals. Separate cases may exercise direct-origin requirements without creating a Need or changing this fixture's three-source count.

## 3. Upstream fixture — Need through Annual Plan

### 3.1 Site, actors and authority

| Actor | Responsibility in this fixture | Required authority |
|---|---|---|
| Grace Wanjiku | Departmental Author; prepares the HRMD and DHI sources and the later Requisition | Actual assignments for both `OU-MOH-HRMD` and `OU-MOH-DHI`, effective at each command; a DHI-only assignment cannot authorize HRMD authorship. |
| Julia Njeri | Acting Head of User Department, Digital Health | `OU-MOH-DHI`, 1 October through 30 November 2026 inclusive. |
| Dr Peter Kimani | Head of User Department | Substantive HRMD assignment throughout; separate DHI assignment from 1 December 2026. No earlier DHI assignment added to repair the old chronology. |
| Mercy Kilonzo | Procurement Planner | Site-wide consolidation and DPP validation; no HOPF preparation signature. |
| Josphat Mwangi | Budget Officer and Finance Confirmation Officer | Site-wide, exercised in the applicable capacity. |
| Charles Mutiso | Head of Procurement Function | Site-wide; signs/submits the Annual Plan, authorizes the Requisition, and reviews Tender preparation in their respective lifecycles. |
| Amina Hassan | Accounting Officer | Site-wide; adopts the Annual Plan, records Treasury evidence and authorizes Tender publication through the relevant owning modules. |
| Daniel Rotich | Statutory approver | Cabinet Secretary in this ministry fixture's configured route; no discretionary route selection at decision time. |
| Brian Wafula | Procurement Officer | Site-wide Tender preparation; distinct from Charles's approval actor. |
| Naomi Chebet | Auditor | Site-wide read within the shared AUTH rules; no business decision. |

Use the shared AUTH registry and command-time checks. Actor names, a selected department or a displayed task do not confer authority. The approval route is a fixture configuration subject to applicability verification, not a rule that every entity uses Cabinet Secretary approval.

### 3.2 Accepted Needs and their immutable source facts

| Field | Infrastructure | HRMD laptops | DHI laptops |
|---|---|---|---|
| Need | `NDS-MOH-2027-0001` | `NDS-MOH-2027-0003` | `NDS-MOH-2027-0004` |
| Accepted Revision | 1 | 2 | 1 |
| Title | National digital health infrastructure upgrade | Clinical training laptops for digital health rollout | Clinical deployment laptops for digital health rollout |
| Department | Digital Health | Human Resources Management and Development | Digital Health |
| Quantity | 1 Programme | 100 Each | 150 Each |
| Required by | 31 August 2027 | 31 December 2027 | 31 December 2027 |
| Departmental Author | Grace Wanjiku | Grace Wanjiku | Grace Wanjiku |
| Acceptance evidence | Must precede DHI certification; see chronology rule below | Peter, 25 November 2026, 10:00 EAT | Julia, 25 November 2026, 09:30 EAT |
| DPP entry | `DPPE-MOH-DHI-2027-001` | `DPPE-MOH-HRMD-2027-001` | `DPPE-MOH-DHI-2027-002` |
| Indicative amount | KES 80,000,000 | KES 20,000,000 | KES 30,000,000 |
| Budget Line | `MOH-BL-DHI-2027` | `MOH-BL-HWD-2027` | `MOH-BL-HWD-2027` |

Copy all six accepted source facts exactly: title, description, expected operational result, quantity, unit and required-by date. Read the accepted revision through NDS; do not reconstruct its text from a screen. The complete-detail laptop narratives and market-survey examples in PLN §10.1 are UI-only additions until reconciled with the authoritative source fixture. This seed does not silently rewrite accepted NDS revisions.

The supplied correction fixes the two laptop acceptance instants but does not supply a replacement exact acceptance instant for the infrastructure Need. The executable manifest must name its valid NDS acceptance command, actor and instant before 25 November 2026, 10:30 EAT. If the available NDS fixture accepts it later, reconcile that fixture before running this chain; do not import a later acceptance as earlier historical evidence. This is a specific remaining seed fact, tracked in §10.

### 3.3 Departmental certification and acceptance chronology

All instants below are EAT; service/audit instants use the equivalent UTC value. Run commands under a controlled test clock at these instants. Do not backdate production evidence or grant retroactive authority.

| Event | Actor | Instant | Required result |
|---|---|---|---|
| DHI laptop Need accepted | Julia | 25 November 2026, 09:30 | Revision 1 available before DPP certification. |
| HRMD laptop Need accepted | Peter in HRMD capacity | 25 November 2026, 10:00 | Revision 2 available before DPP certification. |
| DHI DPP certified | Julia | 25 November 2026, 10:30 | `DPP-MOH-DHI-2027-001`, Submission 1; two proceeding entries; KES 110,000,000. |
| HRMD DPP certified | Peter in HRMD capacity | 25 November 2026, 11:00 | `DPP-MOH-HRMD-2027-001`, Submission 1; one proceeding entry; KES 20,000,000. |
| DHI DPP accepted | Mercy | 27 November 2026, 14:00 | Atomically creates the first Draft APP; no wait for every department. |
| HRMD DPP accepted | Mercy | 27 November 2026, 14:05 | Adds accepted source coverage to the same Draft APP. |
| DHI handover effective | AUTH assignment boundary | 1 December 2026 | Peter may now exercise DHI authority; Julia's earlier evidence remains hers. |

The DPP initial-intake fixture is Open through **30 November 2026, 23:59 EAT**, subject to CFG's exact instant interpretation. The close instant belongs to the intake configuration for FY 2027/28; it need not occur inside that FY. Both the open flag and current command-time close check apply. Needs intake is independently configured and must permit the preceding NDS commands.

Test Julia acting from an old open page after her assignment expires: the command must fail. A HoD may prepare and certify their own departmental submission but cannot validate that same submission as Planner. Preserve exact certified snapshots and their accepted classifications.

All three sources proceed. Any other accepted Need in the same departmental/FY cohort must be explicitly accounted for under the coverage/disposition contract; the runner cannot omit it to force certification. `NDS-MOH-2027-0002` is not an additional accepted source in this scenario.

### 3.4 Strategy

| Field | Value |
|---|---|
| Objective | `OBJ-MOH-2023-001` — Strengthen interoperable national digital health services |
| Reviewed Strategy Version | `STR-MOH-2023-001-V1` |
| Ancestor path | Digital health systems › Health policy, standards and regulation › Digital health governance |

Select the eligible Objective from STR. Retain the exact reviewed version/path and create the deterministic Strategy snapshot at final statutory approval, not at item formation, Finance confirmation or AO adoption. A mismatch or loss of eligibility fails the positive approval atomically. Retrying the same approval correlation must not duplicate snapshot evidence. BASE has no approval-time snapshot merely because the Objective has been selected.

### 3.5 Budget and reservation arithmetic

Budget `MOH-BUD-2027-001`, Version 1, is Active before its first dependent command. Its prior Budget approval history must exist through its own service; this document does not authorize direct state insertion.

| Budget Line | Name | Funding source | Approved | Planned | Reserved before REQ | Committed before REQ | Available before REQ |
|---|---|---|---:|---:|---:|---:|---:|
| `MOH-BL-DHI-2027` | Digital health infrastructure programme | Government of Kenya | KES 100,000,000 | KES 80,000,000 | KES 0 | KES 0 | KES 100,000,000 |
| `MOH-BL-HWD-2027` | Digital health workforce development | Government of Kenya | KES 60,000,000 | KES 50,000,000 | KES 0 | KES 0 | KES 60,000,000 |
| Total | Complete annual procurement budget basis | — | KES 160,000,000 | KES 130,000,000 | KES 0 | KES 0 | KES 160,000,000 |

The two laptop allocations share `MOH-BL-HWD-2027`. BUD must return its eligibility for each source OU; a plausible line title or sufficient headroom is not proof of eligibility. Planning creates no financial reservation, commitment or balance deduction. Finance evaluates the whole Plan by line using the authoritative Budget decision-basis contract, distinct from a display read.

| Calculation | BASE | READY candidate |
|---|---:|---:|
| Illustrative target | 30% | 30% |
| Complete annual denominator | KES 160,000,000 | KES 160,000,000 |
| Required qualifying allocation | KES 48,000,000 | KES 48,000,000 |
| Infrastructure planned designation | None | None |
| Laptop planned designation | None | Youth |
| Qualifying allocation under test assumptions | KES 0 | KES 50,000,000 |
| Shortfall | KES 48,000,000 | KES 0 |
| Qualifying share of annual budget | 0% | 31.25% |
| County obligation | Not applicable to this ministry fixture | Not applicable to this ministry fixture |
| Reservation arithmetic result | Required allocation not met | Required allocation met under the declared test assumptions |

Passing this arithmetic is only one readiness check. Eligibility, method compatibility, applicable rule version and all other submission predicates still apply. Do not calculate the target against the KES 130,000,000 Plan total. A planned designation is not candidate entitlement or actual procurement achievement.

Money crosses APIs as exact decimal currency-unit strings, for example `"50000000.00"` for KES 50 million; KES precision is two decimals in this fixture. Quantity uses exact decimal strings with the owner's UOM precision. Reject excess precision, missing precision and unsupported units. No binary-float epsilon or hidden rounding may make an invalid allocation pass. Coordinated BUD/NDS/REQ precision remains a release dependency.

### 3.6 Annual Plan and item boundaries

| Field | Infrastructure item | Laptop item |
|---|---|---|
| Reference | `PPI-MOH-2027-021` | `PPI-MOH-2027-033` |
| Title | National digital health infrastructure upgrade | Clinical training and deployment laptops for digital health rollout |
| Requirement type | Non-consulting services | Goods |
| Procurement category | Services | Goods |
| Quantity | 1 Programme | 250 Each |
| Planned value | KES 80,000,000 | KES 50,000,000 |
| Method | Open Tender, subject to the applicable verified or expressly isolated test profile | Open Tender, subject to the applicable verified or expressly isolated test profile |
| Horizon | Single year | Single year |
| Aggregation | Not aggregated | Aggregated; common specification and delivery programme across two departments |
| Lotting | Single lot | Single lot |
| Source-derived Plan completion boundary | 31 August 2027 | 31 December 2027 |
| Estimated delivery/implementation period | 30 calendar days, illustrative profile assumption | 60 calendar days, illustrative profile assumption |
| Estimated completion from signing | 11 August 2027 | 24 September 2027 |

The Plan is `PLN-MOH-2027-001`, title **Ministry of Health Annual Procurement Plan 2027/28**, candidate `PLN-MOH-2027-001-V1`. Project name is absent; render **Not applicable** without storing that phrase as a project name. Across the Plan: two items, three sources, two departments and KES 130,000,000. Do not total unlike UOM quantities.

The laptop Plan boundary remains **31 December 2027**. The downstream Requisition operational required-by date remains **30 September 2027**. The estimated 24 September completion fits both; none of these three distinct dates overwrites another. The predecessor's hard-coded KES 3,000,000 RFQ justification is removed: applicable admissibility/thresholds belong to verified configuration, not this seed's narrative.

Populate each mandatory package description, aggregation reason and estimate basis through its owner contract before positive readiness. A UI-only market-survey reference is not an actual downloadable attachment. If an executable test uses synthetic evidence, create real test bytes, retain hashes and identify the evidence as synthetic; do not claim an actual survey was performed.

### 3.7 Governance and Annual Plan publication — conditional positive scenario

These are the approved Planning scenario dates, preserved as targets for the integrated READY candidate. They are not a history generated by BASE. Progress only when §1.2's positive-scenario conditions and each command's current guards pass.

| Stage/action | Actor | Fixture instant, EAT | Evidence and state effect |
|---|---|---|---|
| Confirm affordability | Josphat | 4 December 2026, 10:00 | Exact financial-basis decision across both lines; no Budget reservation. |
| Sign and submit Annual Plan | Charles, HOPF | 7 December 2026, 10:00 | Preparation signature on exact complete content; Draft becomes Awaiting Accounting Officer. No separate HOPF approval state. |
| Adopt and submit | Amina, AO | 8 December 2026, 10:00 | Immutable adoption decision; Awaiting statutory approval. |
| Approve Annual Procurement Plan | Daniel, configured Cabinet Secretary | 9 December 2026, 11:00 | Exact approval and matching Strategy snapshot; Approved with durable publication intent. No synchronous external transmission inside the approval transaction. |
| Record Treasury submission | Amina, AO | 10 December 2026, 14:00 | Exact approved document and external-dispatch evidence; permits dispatch when other holds clear. This is not Treasury approval. |
| Website acknowledgement | Authenticated publication adapter | 10 December 2026, 15:00 | Exact approved package/hash and destination acknowledgement; activate once only if all current activation predicates pass. |

Required Treasury fixture values: channel **Official correspondence**; destination **National Treasury**; dispatch reference **MOH/APP/2027/001**; exact approved Version/document hash; supporting attachment; submitting instant; recording actor/instant; and confirmation of the exact document submitted. The visual filename **Treasury-dispatch-evidence-example.pdf** is only a placeholder in the artboard. An executable test must supply actual synthetic evidence bytes and their identity/hash, not a dead link. These are test records, not a claim of actual dispatch to Treasury.

Freeze one approved web/PDF/KenTender JSON package. Dispatch uses the configured destination and exact manifest; the authoritative acknowledgement correlates that identity. An isolated adapter test may simulate external acknowledgement, explicitly recorded as simulation; it must not be presented as real website publication. An unknown result remains unknown pending reconciliation; no blind retry, manual success flag or premature activation. Treasury evidence, entity website acknowledgement and State Portal publication remain distinct facts. Real production publication and any applicable State Portal evidence are separate prerequisites, not completed by this test.

In BASE, preserve Draft and failed-readiness evidence: no signature, adoption, approval, publication success, Active pointer or downstream eligibility may be fabricated. In a valid positive run, Need Active-usage projection changes only when activation actually succeeds. Accepted DPP disposition, when its coordinated event exists, is distinct from this usage projection.

## 4. Downstream Requisition fixture

The following chain is conditional on an eligible Active positive scenario under §3.7. It is not executable against BASE.

### 4.1 Identity and lineage

| Field | Value |
|---|---|
| Requisition | `REQ-MOH-2027-033-001`, Version 1 |
| Consumed stable Plan Item | `PPI-MOH-2027-033` |
| Exact approved content | Active Plan Version, item-version ID and exact source-allocation identities returned by Planning |
| Entity | Ministry of Health, `PE-MOH` fixture context |
| Delivery and inspection location | Ministry of Health Headquarters, Afya House, Nairobi |
| Owner | REQ-defined organizational responsibility; one open Requisition per stable Plan Item, with both source departments retained in lineage |

### 4.2 Drawdown lines and requirement

| Field | HRMD line | DHI line |
|---|---|---|
| Line | `PIL-MOH-033-001` | `PIL-MOH-033-002` |
| REQ source reference | `SRC-MOH-033-001` | `SRC-MOH-033-002` |
| Exact allocation | `PSA-MOH-2027-033-001` | `PSA-MOH-2027-033-002` |
| Requirement | Business laptops | Business laptops |
| Quantity | 100 Each | 150 Each |
| Amount | KES 20,000,000 | KES 30,000,000 |
| Purpose | Secure clinical training equipment | Secure field deployment equipment |
| Operational required by | 30 September 2027 | 30 September 2027 |
| Budget Line | `MOH-BL-HWD-2027` | `MOH-BL-HWD-2027` |

Both lines use technical requirement `TRQ-MOH-033-001`: standard business laptop, mid-range processor, 16 GB memory, 512 GB solid-state storage, pre-loaded security configuration, three-year warranty and on-site support. Preserve the owning REQ fixture's structured specification and validation detail rather than substituting this index description for the specification. The originating department/allocation differs; both lines have the same Budget Line and Government of Kenya funding source.

### 4.3 Lifecycle and financial effects

| Step | Actor | Date, EAT |
|---|---|---|
| Draft opened | Grace | 1 March 2027 |
| Submitted | Peter, with valid REQ-owner authority | 8 March 2027 |
| Authorized | Charles, HOPF | 15 March 2027 |

Exact within-day instants are not fixed in the supplied downstream fixture. The executable manifest records deterministic instants on these dates and each exercised assignment; ordering must be explicit. The Requisition-owned authorization invokes Planning's canonical `AuthoriseRequisitionDrawdown` and BUD's reservation services in the coordinated transaction. It creates:

| Reservation | Source allocation | Amount | Budget Line |
|---|---|---:|---|
| `RSV-MOH-2027-033-001` | HRMD `PSA-MOH-2027-033-001` | KES 20,000,000 | `MOH-BL-HWD-2027` |
| `RSV-MOH-2027-033-002` | DHI `PSA-MOH-2027-033-002` | KES 30,000,000 | `MOH-BL-HWD-2027` |

Before authorization, this Planning/REQ chain has created no reservation or commitment. In the isolated no-other-activity run, after authorization HWD reserved is KES 50,000,000, committed is zero and available is KES 10,000,000; DHI available remains KES 100,000,000. Planning's indicative KES 130 million does not reduce these balances.

The first authorized drawdown permanently fixes the item's source scope. An authorization reversal releases only the corresponding reversible consumption/reservation; it cannot erase that scope lock. An open Planning correction request temporarily holds new authorizations. Stopped Requisition Versions remain stopped after correction; a fresh permitted Draft is explicit, never automatically resurrected. Test the later-Need case against an authorized and then published original item: reject absorption into that item or its copied successor and route the new Need through a separate item with its own governance.

## 5. Tender preparation, publication and operational dates

### 5.1 Identity and rendered requirement

| Field | Value |
|---|---|
| Tender | `TND-MOH-2027-033`, Version 1 |
| Handoff consumed | Exact authorized `REQ-MOH-2027-033-001` handoff |
| Template | `IT-EQUIPMENT-OPEN-V1`, version 1.1 |
| Entity | Ministry of Health |
| Schedule of Requirements | One consolidated business-laptop line, 250 Each, against `TRQ-MOH-033-001` |

The Tender retains exact internal lineage to both allocations. Consolidation in the bidder-facing schedule does not collapse internal financial or source identities. The external historical KEBS tender retained by STD-TPL-001 is source evidence for template curation, not a second live entity or a new executable fixture.

### 5.2 Baseline dates and explicit assumptions

These are Planning baseline dates, not pre-existing actuals. The first six dates reproduce PLN v1.18's illustrative 21/30/5/2/14-day profile arithmetic. Internal approval/notification buffers are planning assumptions; legal period/counting applicability still needs verification. A method in a catalogue is not proof that its downstream procedure is implemented.

| Milestone | Infrastructure Plan baseline | Laptop Plan baseline | Operational distinction |
|---|---|---|---|
| Invitation/advertisement | 1 May 2027 | 15 May 2027 | Actual populated only by the corresponding authentic publication event. |
| Bid opening | 22 May 2027 | 5 June 2027 | No opening actual generated by this seed. |
| Evaluation completion | 21 June 2027 | 5 July 2027 | No evaluation actual generated by this seed. |
| Tender award approval | 26 June 2027 | 10 July 2027 | No award actual generated by this seed. |
| Notification of award | 28 June 2027 | 12 July 2027 | No notification actual generated by this seed. |
| Contract signing | 12 July 2027 | 26 July 2027 | No signing actual generated by this seed. |
| Delivery/implementation boundary | 31 August 2027 | 31 December 2027 | Laptop REQ operational deadline remains 30 September; estimated completion is 24 September. No delivery actual or fulfilment inference. |

Infrastructure estimated completion is 12 July + 30 calendar days = 11 August 2027, before its 31 August boundary. Laptop estimated completion is 26 July + 60 calendar days = 24 September 2027, before both its 30 September REQ date and 31 December Plan boundary. Required-by boundaries are not calculated by blindly adding the delivery period.

### 5.3 Tender lifecycle and invitation actual

| Step | Actor/owner | Fixture date, EAT | Result |
|---|---|---|---|
| Prepare Tender | Brian, Procurement Officer | 20 March 2027 | Governed TPR Draft from the authorized handoff. |
| Approve for publication | Charles, HOPF | 20 April 2027 | Exact approved Tender Version and publication handoff. |
| Authorize publication | Amina, AO, through TPUB | 15 May 2027; before distribution/acknowledgement | Required publication authority and channel/readiness checks. This does not replace the earlier TPR approval. |
| Distribute and acknowledge publication | TPUB and configured adapter; operational channel confirmations by the authorized owner where required | 15 May 2027; exact ordered instants recorded in the run | Exact published Tender evidence and supported invitation event. A test adapter is identified as simulation. |

Brian cannot approve the Version he prepared; Charles is the distinct TPR approver. TPUB owns publication authorization and distribution; TPR approval alone is not supplier publication. The baseline 15 May invitation date becomes an actual only after an authoritative event establishes publication, with actual publication date distinguished from a delayed acknowledgement/recording date.

The coordinated TPR §9.5/TPUB contract must supply producer/event identity, schema version, exact proceeding/REQ/Plan/item/allocation lineage, actual date, ordering and evidence, as required by PLN §§4.8 and 7.3. Duplicate delivery is idempotent. A correction appends a linked correcting event and preserves the old event; it does not overwrite history. Plan baselines and independent forecast revisions remain unchanged. A second proceeding on the same stable item must retain its own actual rather than overwrite the first.

All seven actuals start absent. Only the laptop proceeding's invitation actual is produced by the supported Tender-publication path here. No infrastructure invitation actual is fabricated merely because an infrastructure baseline is shown. The remaining six milestone integrations and fulfilment derivation remain deferred to their actual owning modules. A delayed-date scenario may be separately declared for forecast/error testing without converting its simulated dates into downstream evidence.

## 6. Shared naming and model ownership

| Concern | Required treatment |
|---|---|
| Procurement office name | **Head of Procurement Function** is the shared responsibility label. Charles's Planning preparation signature is explicitly included. No second office or extra approval stage. |
| DSP naming | KT-STD v1.4 contains the shared label. DSP was not supplied; verify its own text/registry use before closing the previously reported omission. |
| Annual Plan publication record | PLN v1.18's logical record is `PlanPublication`. The follow-up reports the Frappe rename **Annual Plan Publication → Plan Publication**. Use the approved implementation mapping and inspect callers/migrations before declaring the rename complete. |
| Departmental counter | User-facing **Submission**; preserve exact root/version/snapshot identity underneath it. |
| Annual Plan counter | **Version**; stable item identity is separate from exact item-version identity. |
| Retired source names | Live MOH seed records must not use `PE-KEBS`, `PPI-KEBS-2026-ICT-001` or `TND-KEBS-2026-0001`. Preserve intentionally historical external references. |
| Canonical validator | `make seed-canonical-validate` and `validate_planning_seed` are names reported by Claude Code, not evidence inspected here. Confirm their current implementation and scope before using their results for closure. |

## 7. Execution, shared-document reconciliation and evidence

### 7.1 Deterministic execution

Execute via the same authorized domain commands used by the application, with supported test clocks, immutable evidence, expected version tokens and idempotency keys. Capture generated IDs rather than parsing business references. Reset/replay is isolated and repeatable, fails on conflicting authoritative data and cannot create another PE, FY permission grants, compatibility roles or direct governed-state writes.

Use separate test worlds for BASE and an approved READY integrated candidate. A fixture switch must not mutate an already approved baseline in place. A separate county-configured world may test county applicability without placing a second PE in this ministry site. It is outside this fixture's acceptance claim until implemented under FU-26.

Before execution, complete and validate mandatory source narrative, estimate basis/evidence, source acceptance, Budget activation, Strategy eligibility and configuration inputs through their owners. Missing provider services or unresolved mandatory configuration must yield explicit failed/unexecuted evidence; do not mark the scenario passed because the screen can be rendered.

### 7.2 Coordinated owner updates

| Owner | Matching amendment/evidence required |
|---|---|
| KT-STD / AUTH fixture registry | Grace's actual two-OU assignments, Julia/Peter chronology, HOPF Planning signature responsibility, and complete fixture instants. Do not claim KT-STD v1.5/v1.6 was inspected or updated by this file. |
| NDS | Matching accepted revisions, infrastructure acceptance evidence and all six facts; earlier independent Draft/Returned screenshots remain separately labelled scenarios, not snapshots of this later accepted chain. |
| CFG / LAW | Applicable FY bounds and intake clocks; method/schedule/reservation/route rules and their versions/statuses; complete annual-denominator applicability; explicit separation of test assumptions from verified production rules. |
| BUD | Atomic affordability decision contract, authoritative annual-budget basis and source-OU eligibility; exact decimal amount behavior. |
| REQ | Exact Active lineage, 30 September operational date, two reservations, scope locks/holds and correction-outcome handling. |
| TPR / TPUB | Baseline versus actual date distinction, publication authority, exact invitation-event/correction envelope and preservation of internal source lineage. |
| Planning publication owner | Exact schema/field mappings, synthetic test files where appropriate, adapter evidence and separate production destination readiness. |

KT-STD v1.4 §8.4A already provides a Requisition/Tender fixture window spanning 1 March–15 May 2027. That window remains useful; it does not replace the exact upstream chronology in §3.3 or the governance instants in §3.7. Approval of this seed does not amend sibling documents automatically.

### 7.3 Completion claims

Use distinct dispositions: **specified**, **approved**, **implemented**, **verified**, **blocked**, or **deferred**. A test result records the commit/build, suite/test identity, scenario, time, expected/actual result and relevant evidence. Merely adding this document cannot close FU-20 as implemented or verified. Green legacy tests cannot override the corrected assertions below.

Production legal verification, actual external publication and full release/browser evidence are not claimed by this document. Neither a synthetic Treasury PDF nor a fixture-verified profile proves those facts.

## 8. Acceptance and smoke contract

The seven existing IDs are retained with corrected assertions, so their replacement is explicit. Additional IDs extend the coverage. Each row requires recorded results; no row is marked passed by publication of this specification.

| ID | Required result |
|---|---|
| SEED-AC-001 | Exactly one configured entity, Ministry of Health, participates in each executable world. Historical external KEBS source documents do not become seed entities. |
| SEED-AC-002 | Laptop allocations retain their exact accepted Need revisions/DPP entries, 100/150 Each and KES 20m/30m; both use eligible line MOH-BL-HWD-2027. |
| SEED-AC-003 | This chain creates no financial reservation/commitment before REQ authorization; authorization creates exactly the two specified reservations and no Planning-stage balance deduction. |
| SEED-AC-004 | The bidder-facing Tender requirement is one 250 Each laptop line against the shared specification, with immutable internal lineage to both allocations. |
| SEED-AC-005 | Recorded chronology satisfies source acceptance, certification, validation, Finance, signature, adoption, statutory approval, Treasury evidence, APP acknowledgement, REQ authorization, TPR approval and Tender publication ordering in the conditional positive scenario; baseline dates are not asserted as later actuals. |
| SEED-AC-006 | No retired KEBS identity remains in the executable MOH chain; explicitly historical external template evidence is preserved. |
| SEED-AC-007 | Shared responsibility name is Head of Procurement Function; Planning signature and downstream capacities are explicit. DSP coverage remains unverified until its own source/registry is inspected. |
| SEED-AC-008 | BASE has exactly 2 items, 3 sources, 2 departments and KES 130m, with None/None designations and KES 48m shortfall under the illustrative full-budget calculation. |
| SEED-AC-009 | BASE cannot sign/submit for positive governance or become Active; no fabricated approval, publication or downstream authorization evidence is produced. |
| SEED-AC-010 | READY changes only explicitly declared scenario inputs, retains the KES 160m denominator and yields KES 50m qualifying allocation/31.25%/zero shortfall under isolated test assumptions. No implicit promotion of UI-only data to production configuration. |
| SEED-AC-011 | Julia certifies DHI at 25 Nov 10:30; Peter certifies HRMD at 11:00; every accepted source precedes its certification. A missing/incompatible infrastructure acceptance blocks execution. |
| SEED-AC-012 | Mercy's DHI acceptance at 27 Nov 14:00 creates the Draft APP once; HRMD acceptance at 14:05 updates that Draft. Duplicate command delivery creates no duplicate source capacity. |
| SEED-AC-013 | Grace has both required OU assignments; Julia's October–November and Peter's December DHI windows are enforced at command time. Julia's expired-page command is denied without retroactive reassignment. |
| SEED-AC-014 | All accepted Needs in the applicable cohort are accounted for; DPP initial intake checks both the flag and configured close instant, independently of the Needs intake flag. |
| SEED-AC-015 | Laptop Plan boundary is 31 Dec, REQ operational deadline 30 Sep and estimated completion 24 Sep 2027; changing one projection cannot silently rewrite the other owners' facts. |
| SEED-AC-016 | Both schedule columns reproduce the specified date arithmetic; infrastructure/laptop estimates fit their boundaries. Rule verification remains distinct from arithmetic correctness. |
| SEED-AC-017 | Finance validates the exact authoritative basis across both Budget Lines without reservations; incomplete/stale basis cannot be accepted using a prior display read. |
| SEED-AC-018 | Positive governance uses Charles's preparation signature, Amina's adoption and Daniel's configured statutory approval on exact immutable content, with all authorization/segregation checks and no added HOPF approval stage. |
| SEED-AC-019 | Strategy snapshot is created/reused deterministically at statutory approval, matches the reviewed version/path and fails atomically on mismatch or ineligibility. |
| SEED-AC-020 | APP dispatch waits for valid exact-Version Treasury evidence; synthetic attachment bytes exist in a test run. Reference MOH/APP/2027/001 alone is insufficient evidence. |
| SEED-AC-021 | Exact-package acknowledgement at the conditional 10 Dec 15:00 target activates once only when eligible; duplicate acknowledgement is idempotent and unknown publication cannot be manually marked successful. |
| SEED-AC-022 | First authorized REQ locks stable item scope permanently. Reversal or a copied Plan Version cannot permit a later Need to be absorbed into the original authorized/published item. |
| SEED-AC-023 | The later-Need case follows a separate item and governed route; open correction holds block new authorization, terminal outcomes never resurrect stopped REQ Versions automatically. |
| SEED-AC-024 | Brian prepares, Charles approves Tender preparation, and Amina authorizes publication through TPUB. A preparation approval alone produces no invitation actual. |
| SEED-AC-025 | Actuals start absent; only the correct proceeding's invitation event writes an actual. Duplicate delivery is harmless; linked correcting events preserve history; other six actuals and fulfilment remain unavailable. |
| SEED-AC-026 | Exact Money/Quantity values survive owner boundaries and calculations; excess precision is rejected and two reservations reconcile exactly with drawdowns/reversals. |
| SEED-AC-027 | Reset/replay with identical inputs is deterministic and idempotent; conflicting authoritative data fails visibly. No direct governed-state writes, permission bypass or synthetic production-law verification. |
| SEED-AC-028 | All required real/synthetic evidence references resolve to the correct bytes/version/hash; UI-only labels are never presented as existing downloads or actual external dispatch. |
| SEED-AC-029 | Executable manifest records exact FY bounds, mandatory owner inputs, clock instants, actor assignments and rule/profile provenance; incompatible FY/source/configuration facts block the affected run. |
| SEED-AC-030 | Closure evidence distinguishes document specification/approval from implementation/tests. Reported canonical validator results are inspected against these assertions and the actual build. |

Focused smoke order: validate manifest and authority; build BASE to the blocked Draft; verify denied positive action; separately execute an approved READY candidate through Finance/governance and test publication; authorize its Requisition and reconcile both reservations; prepare/approve/publish the Tender; verify invitation event only; attempt forbidden later-Need absorption and correction/reversal cases. Do not broaden this fixture into the six deferred operational modules.

## 9. Full change register for re-implementation

| ID | v1.2 defect or omission | v1.3 replacement | Sections / owner impact | Acceptance |
|---|---|---|---|---|
| SEED13-CHG-001 | Control claimed a live approved chain and repeated contradictory sibling approval claims. | Approved successor, explicit source versions and separate approval/implementation/evidence status. | Control, §§1.1, 7.3; document owners | AC-030 |
| SEED13-CHG-002 | None/None Plan stated Active unconditionally despite mandatory reservation shortfall. | Preserve BASE as blocked; distinguish visual READY and the approved integrated test scenario design. | §§1.2, 3.5–3.7; PLN/CFG/SEED | AC-008–010 |
| SEED13-CHG-003 | No explicit control against promoting fixture assumptions into verified law. | Manifest provenance and isolated test configuration; production rules still need verification. | §§1.3, 3.5, 7; CFG/LAW | AC-010, 029 |
| SEED13-CHG-004 | Grace listed DHI-only while authoring HRMD and DHI Needs. | Require actual effective assignments for both OUs. | §3.1; KT-STD/AUTH/NDS | AC-013 |
| SEED13-CHG-005 | Peter certifies both DPPs at 10:00 before valid DHI authority. | Julia DHI 25 Nov 10:30; Peter HRMD 11:00; valid separate assignments. | §§3.1–3.3; NDS/PLN/KT-STD | AC-011, 013 |
| SEED13-CHG-006 | Both DPP acceptances at the same instant obscured APP creation order. | Mercy accepts DHI 27 Nov 14:00, creates APP, then HRMD 14:05. | §3.3; PLN/SEED | AC-012 |
| SEED13-CHG-007 | Infrastructure source and complete Plan totals not fully indexed. | Three accepted source rows, two items, exact revisions, lines and KES 130m totals. | §§2, 3.2, 3.5–3.6 | AC-002, 008 |
| SEED13-CHG-008 | Source acceptance/coverage/intake prerequisites implicit. | Require prior infrastructure acceptance, full accepted cohort, independent intake flags and valid command-time checks. | §§3.2–3.3, 10; NDS/CFG | AC-011, 014, 029 |
| SEED13-CHG-009 | Only KES 60m laptop line stated, missing full annual denominator. | KES 100m + KES 60m authoritative basis; KES 160m denominator; 30% illustrative arithmetic. | §3.5; BUD/CFG | AC-008, 010, 017 |
| SEED13-CHG-010 | Line title/headroom used as eligibility justification; monetary exactness unstated. | BUD source-OU eligibility and decision contract; exact decimal Money/Quantity. | §§3.5, 4.3; BUD/NDS/REQ | AC-002, 017, 026 |
| SEED13-CHG-011 | Hard-coded KES 3m RFQ threshold asserted as method justification. | Remove number; use applicable governed and verified or expressly isolated test profile. | §§3.6, 5.2; LAW/CFG | AC-016, 029 |
| SEED13-CHG-012 | Laptop Plan baseline incorrectly became REQ's 30 Sep deadline. | Plan boundary 31 Dec; REQ date 30 Sep; estimated completion 24 Sep retained separately. | §§3.6, 4.2, 5.2; PLN/REQ/TPR | AC-015–016 |
| SEED13-CHG-013 | Finance, preparation signature, AO adoption and statutory approval absent from indexed chain. | Exact separate actors, capacities, instants and immutable state effects. | §3.7; PLN/KT-STD | AC-018 |
| SEED13-CHG-014 | Strategy snapshot point and reviewed-path matching omitted. | Final statutory-approval deterministic snapshot with atomic eligibility/match failure. | §§3.4, 3.7; STR/PLN | AC-019 |
| SEED13-CHG-015 | Active timestamp asserted without Treasury evidence or acknowledgement contract. | Exact Treasury dispatch evidence, durable intent, authenticated package acknowledgement and guarded activation. | §3.7; PLN publication owner | AC-020–021, 028 |
| SEED13-CHG-016 | Two-reservation correction present but lifecycle protections omitted. | Retain both amounts/IDs; exact transaction, stable identity, permanent scope lock, holds and no resurrection. | §§2, 4.3; REQ/BUD/PLN | AC-003, 022–023, 026 |
| SEED13-CHG-017 | Shared technical requirement described different funding sources despite same source/line. | Preserve departmental/allocation distinction with the same GoK funding source and HWD line. | §4.2; REQ/TPR | AC-002, 004 |
| SEED13-CHG-018 | Milestone table described every actual as equal to baseline. | Label baseline/estimate/operational dates; only supported proceeding invitation event can produce an actual. | §§5.2–5.3; PLN/TPR/TPUB | AC-005, 016, 025 |
| SEED13-CHG-019 | Published/System row was detached from lifecycle table; AO publication authority omitted. | Complete lifecycle table with TPR segregation, AO authorization and authentic or labelled simulated distribution evidence. | §5.3; TPR/TPUB | AC-024–025 |
| SEED13-CHG-020 | Actual event identity, retries and correction history unspecified. | Exact proceeding/allocation envelope, idempotency, linked correction and no baseline overwrite. | §5.3; TPR/TPUB/PLN | AC-025 |
| SEED13-CHG-021 | Naming follow-up covered only HOPF; reported publication rename absent. | Preserve shared office; map logical PlanPublication and verify reported DocType rename/callers. | §6; KT-STD/DSP/PLN | AC-007, 030 |
| SEED13-CHG-022 | Static artifacts and inherited date windows treated as sufficient execution evidence. | Real synthetic test bytes where needed, deterministic manifests/clocks, explicit FY/authority/owner-input checks and actual test results. | §§1.3, 3.2, 3.7, 7; all seed owners | AC-027–030 |
| SEED13-CHG-023 | Seven acceptance rows assumed unconditional end-to-end success. | Retain/correct AC-001–007; add AC-008–030 for negative BASE, conditional positive flow and boundaries. | §8; tests/trackers | AC-001–030 |

Acceptance references in this table abbreviate `SEED-AC-`. The table specifies required changes, not completed code migrations. No external controlled document is marked amended by this seed alone.

## 10. Remaining dispositions and approval effect

| Item | Current disposition | Concrete closure evidence |
|---|---|---|
| FU-20 document amendment | Document amendment approved on 12 September 2026; revised fixture, change table and acceptance contract adopted. Implementation and verification remain open. | Actual aligned seed/test results against this approved successor. |
| Infrastructure acceptance instant | Exact replacement instant/actor not fixed by the supplied Planning correction; must precede DHI certification. | Reconciled NDS fixture and executable manifest with valid acceptance evidence. No backdating real evidence. |
| Integrated READY promotion | Integrated test scenario design approved with this successor on 12 September 2026. Exact executable test configuration and provider readiness remain prerequisites. | Approved exact test configuration and provider evidence; legally verified rules still required for production-equivalent claims. |
| FY bounds and mandatory owner inputs | Authoritative bounds, complete source narratives/estimate evidence and any missing parent-command instants must be supplied before execution. | Valid manifest and successful owner-contract checks; no guessed fiscal calendar or accepted-revision rewrite. |
| Legal/configuration/provider dependencies | FU-21–FU-25 and FU-30 remain coordinated work; their detailed applicability is unchanged by this seed. | Applicable verified rules, matching provider contracts and affected integration evidence. |
| TPUB and publication adapter alignment | Named explicitly; neither TPR-only editing nor a static publication screenshot closes it. | Exact caller/event/adapter tests, real destination evidence for production claims. |
| Shared KT-STD/NDS/REQ/TPR fixture amendments | Required owner changes in §7.2; not authored in this file. | Matching controlled revisions and traced test/fixture assertions. |
| DSP label and reported validator/rename state | Unverified against current source/repository. | Inspection of the actual owner documents/callers and scoped verification results. |

Approved on 12 September 2026, this v1.3 replaces v1.2's unconditional Active-plan assumption and the other corrected assertions listed in §9. It preserves the original MOH identities, both laptop allocations and the two Requisition-stage reservations. It authorizes no invented legal verification, modification of real historical evidence, direct lifecycle-state insertion or claim that deferred operational facilities are implemented.
