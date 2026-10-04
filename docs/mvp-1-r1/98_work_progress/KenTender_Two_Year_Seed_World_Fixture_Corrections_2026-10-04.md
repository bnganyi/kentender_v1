# Two-year seed world: required corrections to KT-STD-001 §8 and SEED-001

| Control | Value |
|---|---|
| Date | 4 October 2026 |
| Status | Phase 1 deliverable of `KenTender_Two_Year_Seed_World_Proposal_2026-10-04.md`, for the Project Owner to apply in their own copies of KT-STD-001 and SEED-001 (decision D7). Neither document is changed here. |
| Basis | Proposal §9 D1–D7, accepted by the Project Owner on 4 October 2026, verbatim: "Decisions for the owner: recommendations accepted". |
| Targets | KT-STD-001 v1.22 §8.4 and §8.4A (approved 4 October 2026); SEED-001 v1.4 (approved 3 October 2026). The next versions would be KT-STD-001 v1.23 and SEED-001 v1.5, unless the owner's library already holds later ones. |
| Read in full | KT-STD-001 v1.22 §8; SEED-001 v1.4; the proposal. |
| Code read for the finding in §1 | `departmental_needs/services/lifecycle.py:474`; `procurement_planning/services/dpp_lifecycle.py:519–522`; `procurement_planning/services/readiness.py:437–438`; `procurement_planning/services/schedule.py:76–89`; `procurement_planning/seeds/kentender_mvp_v1.py` CLOCK and baseline dates. |

## 1. Finding that shapes the dates: each year's dates must fit that year

The proposal said the existing chain "keeps its dates". That holds for what actually happened: the requisition, tender, bids, opening, evaluation and award. It does **not** hold for the planned dates, because three owner checks tie a year's planned dates to that year:

1. Needs refuse a Required by outside the Need's financial year (`departmental_needs/services/lifecycle.py:474`).
2. Departmental-plan direct requirements refuse it too, with the message "Required by must fall inside the selected Financial Year." (`dpp_lifecycle.py:521–522`).
3. Planning blocks a Plan item whose baseline signing plus estimated delivery period ends after its completion boundary, the earliest Required by (`PLN_DELIVERY_BOUNDARY_INSUFFICIENT`, `readiness.py:437–438`).

SEED-001 v1.4 gives the laptops Required by 31 December 2027 and the infrastructure 31 August 2027. Both are outside FY 2026/27 (1 Jul 2026 – 30 Jun 2027). So in Year 1:

- Each Year 1 Required by moves inside FY 2026/27.
- Each Year 1 Plan item's baseline invitation date moves early enough that baseline signing plus delivery fits that boundary.
- The actual publication (15 May 2027) and everything after it keep their dates. The laptop Tender is therefore published **103 days after its approved invitation date**. That is a real, readable fact (Analytics measure ANL-M-05 "Days after approved date"), not a defect.

Recommendation: accept this. The alternative is moving the actual chain about three months earlier, which would break the Bid Opening, Evaluation and Award fixtures pinned to 10–17 June 2027 and their demo profiles. If the owner prefers that alternative, say so before Phase 2.

## 2. How Year 1's history is dated: 52 weeks earlier

Year 1's needs, departmental plans, Annual Plan and budget are today's journeys moved back **364 days (52 weeks)**, not one calendar year. Each event keeps its weekday and its spacing from its neighbours. One calendar year back would move every date a weekday earlier, putting the Plan's 7 December signature on a Sunday.

| Today (Year 2 keeps these) | Year 1 (minus 364 days) |
|---|---|
| Tue 24 Nov 2026 needs | Tue 25 Nov 2025 |
| Wed 25 Nov 2026 acceptances and certifications | Wed 26 Nov 2025 |
| Fri 27 Nov 2026 DPP acceptances | Fri 28 Nov 2025 |
| Mon 30 Nov 2026, 23:59 DPP intake closes | Mon 1 Dec 2025, 23:59 |
| Fri 4 Dec 2026 Finance confirmation | Fri 5 Dec 2025 |
| Mon 7 Dec 2026 sign and submit | Mon 8 Dec 2025 |
| Tue 8 Dec 2026 AO adoption | Tue 9 Dec 2025 |
| Wed 9 Dec 2026 statutory approval | Wed 10 Dec 2025 |
| Thu 10 Dec 2026 Treasury evidence and publication | Thu 11 Dec 2025 |
| Thu 1 Oct 2026 budget journeys begin | Thu 2 Oct 2025 |

Everything Year 1 relies on moves back by the same 364 days:
- **Site configuration history**: Mon 29 Jun 2026 becomes Mon 30 Jun 2025.
- **Responsibility administration**: Tue 1 Sep 2026 becomes Tue 2 Sep 2025.
- **Julia Njeri's acting window and Dr Peter Kimani's Digital Health start** move the same way, so Julia still accepts the Digital Health laptop Need inside her acting term and Peter takes over afterwards.

A Year 2 action dated after Julia's term ends finds her expired. That matches the existing SEED-001 v1.4 note: "At June 2027 instants Julia's 2026 acting term is expired".

## 3. KT-STD-001 §8.4 — replacement table

Proposed text. The v1.22 table is kept beneath it as history, following the standard's own correct-by-addition rule.

| Year | Period | Role in the shared fixture | Needs submission |
|---|---|---|---|
| FY 2025/26 | 1 Jul 2025 – 30 Jun 2026 | Configured, closed. No business records. It exists only if a command needs a configured year around Year 1's late-2025 history (decision D3; the build confirms). | Closed |
| FY 2026/27 | 1 Jul 2026 – 30 Jun 2027 | **Year 1, the year being carried out.** Its Annual Plan is Active and locked; requisitions, Tenders and later stages run against it. | Closed (closed on Wed 26 Nov 2025, 23:59 EAT) |
| FY 2027/28 | 1 Jul 2027 – 30 Jun 2028 | **Year 2, the year being prepared.** Never goes past an approved Annual Plan. | Closed (closed on 25 Nov 2026, 23:59 EAT) |

Proposed sentence under the table: "The shared fixture is read **as at 18 June 2027, 10:00 EAT** (the as-at instant). Every recorded fixture event is at or before it; every live deadline is after it. Test sites run with the site test clock at that instant."

> (v1.22 read: FY 2026/27, 1 Jul 2026 – 30 Jun 2027, Needs submission Closed; FY 2027/28, 1 Jul 2027 – 30 Jun 2028, Needs submission Open, closing 25 Nov 2026, 23:59 EAT.)

Year 2's Needs intake reads "Closed" because at the as-at instant it closed seven months earlier. The Year 2 journey itself opens and closes it at its own instants, as today.

## 4. KT-STD-001 §8.4A — replacement table

Proposed replacement of the opening sentence: "Each module works in a distinct window so the fixtures compose into two coherent years, one carried out and one prepared, read as at 18 June 2027, 10:00 EAT, without colliding." (v1.22 read: "…compose into one coherent year without colliding.")

| Purpose | Instants |
|---|---|
| Site configuration history | 30 Jun 2025, 10:10 EAT (v1.22 read: 29 Jun 2026, 10:10 EAT) |
| Responsibility administration | 2 Sep 2025, between 09:00 and 10:30 EAT (v1.22 read: 1 Sep 2026) |
| Strategy journeys | 24–25 Nov 2026, between 11:00 and 17:00 EAT. Unchanged: these are the Version 2 artboard profiles. The base Strategic Plan, approved 1 Jul 2023 for 1 Jul 2023 – 30 Jun 2028 (`kentender_mvp_v1_strategy.py` V1_APPROVED_AT and PERIOD), is in force before both years' planning. |
| Year 1 Budget journeys | 2 Oct 2025 through 17 Mar 2026, EAT. Registration precedes the Plan's Finance confirmation. Requisition reservations against the FY 2026/27 Budget follow at the Requisition instants below. |
| Year 1 Departmental Needs journeys | 25 Nov 2025, between 09:00 and 15:30 EAT |
| Year 1 Procurement Planning journeys | 25 Nov 2025 through 11 Dec 2025, EAT. The FY 2026/27 Annual Plan is Active from 11 Dec 2025. |
| Year 1 execution: Requisitions and Tender preparation | 1 Mar 2027 through 15 May 2027, EAT (unchanged dates; now inside FY 2026/27, against the FY 2026/27 Plan) |
| Year 1 execution: Bid submission through Award | 15 May 2027 through 18 Jun 2027, 10:00 EAT for the canonical state. Award demo profiles keep their later moments, up to 2 Jul 2027, as isolated profiles. |
| Year 2 Budget journeys | 1 Oct 2026 through 16 Mar 2027, EAT (the v1.22 Budget window, now for FY 2027/28 only, with no Requisition reservations) |
| Year 2 Departmental Needs journeys | 24 Nov 2026, between 09:00 and 15:30 EAT (unchanged) |
| Year 2 Procurement Planning journeys | 24 Nov 2026 through 20 Dec 2026, EAT (unchanged). The FY 2027/28 Annual Plan is Active from 10 Dec 2026 when `NEXT=annual_plan`. |
| Asset Disposal journeys | 4 May 2027 through 14 Jan 2028, EAT (unchanged and out of scope of this change; this window extends past the as-at instant, which the owner may want reconciled separately) |

> v1.22 rows read: "Budget journeys | 1 Oct 2026 through 16 Mar 2027, EAT — registration precedes reservation, which precedes revision"; "Departmental Needs journeys | 24 Nov 2026, between 09:00 and 15:30 EAT"; "Procurement Planning journeys | 24 Nov 2026 through 20 Dec 2026, EAT"; "Requisition and Tender Preparation journeys | 1 Mar 2027 through 15 May 2027, EAT — Requisition authorisation (15 Mar 2027) precedes Tender preparation, which precedes the baseline invitation date (SEED-001 §7)".

The v1.22 Requisition row says Tender preparation "precedes the baseline invitation date". In Year 1 the baseline invitation date (§5.2 below) is earlier than the actual Tender preparation, so that clause no longer holds. It is replaced by: "actual publication may fall after the baseline invitation date; the difference is Planning's Baseline lateness".

## 5. SEED-001 — corrections, section by section

SEED-001 v1.4 describes one chain. The corrections move that chain into Year 1, add Year 2 and the Year 1 portfolio, and keep every identity rule. References stay generated (SEED-OPS v1.21 decision D3, "Keep generated codes"), so `NDS-MOH-2027-0003`-style references in the text remain examples of form.

| Section | Change |
|---|---|
| Control / approval effect | New version; basis is the two-year proposal and decisions D1–D7. |
| §1.3, last paragraph | Replace the open issue ("The source pack labels the period FY 2027/28 while using the dates below… An incompatible configured period is an open CFG/SEED reconciliation issue before execution.") with its resolution: the laptop chain is Year 1, FY 2026/27, and every Year 1 date fits FY 2026/27 bounds as configured (§1 of this brief). Keep the old paragraph as history. |
| §2 lineage | The lineage is unchanged in shape: three accepted Needs, two Plan items, two allocations, one Requisition and one Tender. It is stated as FY 2026/27. |
| §3.1 actors | Julia Njeri's acting window moves 364 days earlier: Thu 2 Oct – Tue 1 Dec 2025, replacing 1 Oct – 30 Nov 2026. Dr Peter Kimani's Digital Health assignment starts Tue 2 Dec 2025, replacing 1 Dec 2026. Grace Wanjiku's two assignments must be in force from Year 1's needs. |
| §3.2 Needs | Required by: infrastructure **30 Jun 2027** (was 31 Aug 2027); HRMD and DHI laptops **30 Jun 2027** (were 31 Dec 2027). Acceptance instants move 364 days earlier: Julia **26 Nov 2025, 09:30**; Peter **26 Nov 2025, 10:00**. The infrastructure acceptance instant is still to be fixed; §10's open item remains, and its bound becomes "before 26 Nov 2025, 10:30 EAT". |
| §3.3 chronology | Every instant moves 364 days earlier: certifications 26 Nov 2025, 10:30 and 11:00; DPP acceptances 28 Nov 2025, 14:00 and 14:05; handover 2 Dec 2025. DPP intake open through **Mon 1 Dec 2025, 23:59 EAT**, belonging to FY 2026/27's intake configuration. |
| §3.5 Budget | The Budget is FY 2026/27's: Version 1 Active before the Plan's Finance confirmation (5 Dec 2025). Lines, amounts and the KES 160,000,000 denominator are unchanged. Line references stay generated. |
| §3.6 Plan | Title **Ministry of Health Annual Procurement Plan 2026/27** (was 2027/28). Completion boundaries become 30 Jun 2027 for both items. Estimated completion from signing becomes 13 Jun 2027 for laptops and 11 Jun 2027 for infrastructure (§5.2). The paragraph on three distinct dates becomes: Plan boundary **30 Jun 2027**, Requisition operational required-by **20 Jun 2027**, estimated completion **13 Jun 2027**. Each is still a distinct fact. |
| §3.7 governance | Instants move 364 days earlier: 5, 8, 9, 10 and 11 Dec 2025. The Treasury dispatch reference becomes **MOH/APP/2026/001** (was MOH/APP/2027/001), so Year 2 can keep MOH/APP/2027/001. |
| §4.2–4.3 Requisition | Draft 1 Mar, submitted 8 Mar and authorised 15 Mar 2027 are unchanged. Operational required by becomes **20 Jun 2027** (was 30 Sep 2027). The two reservations are against the FY 2026/27 Budget. |
| §5.2 baselines | Laptop baseline: invitation **1 Feb 2027**, opening 22 Feb, evaluation completion 24 Mar, award approval 29 Mar, notification 31 Mar, signing 14 Apr, estimated completion 13 Jun 2027 (60 days). Infrastructure baseline: invitation **1 Mar 2027**, opening 22 Mar, evaluation completion 21 Apr, award approval 26 Apr, notification 28 Apr, signing 12 May, estimated completion 11 Jun 2027 (30 days). Both use the same 21/30/5/2/14-day profile arithmetic; recomputed for this brief. |
| §5.3 Tender | Dates unchanged (prepare 20 Mar, approve 20 Apr, authorise and publish 15 May 2027). Add: "Actual publication is 103 days after the approved invitation date; Planning records this as Baseline lateness." |
| New §5A Year 1 portfolio | The ten further Tenders, extra Requisitions and Plan items of proposal §5. Each has a target state at the as-at instant, an owner chain and named actors. The titles reuse the Home and Analytics fixture titles (§6 of this brief). |
| New §5B Year 2 preparation | Year 2's Needs, departmental plans, Budget and Annual Plan for FY 2027/28, at today's instants (24 Nov – 10 Dec 2026), with their own titles (§6). `NDS-MOH-2027-0002`-style "Digital health workforce certification programme" stays Submitted for Dr Peter Kimani's review, serving HOME H11. Year 2 holds no Requisition, Tender or reservation. |
| §8 acceptance | Amend SEED-AC-005, 011, 013 and 015 for the new instants and dates. Add rows for: the two years' independence; Year 2 never past an Active Plan; every Year 1 Required by and boundary inside FY 2026/27; each portfolio state present at the as-at instant; the as-at instant. |
| §10 dispositions | Close "FY bounds and mandatory owner inputs" for the FY label mismatch once the build validates. Add the build's open items. |

## 6. New content for owner review

None of these comes from an approved source unless stated.

**Year 1 Required by and baseline dates** (§5 table, rows §3.2, §3.6, §4.2–4.3 and §5.2): chosen to satisfy the owner checks in §1, with arithmetic recomputed here.

**Treasury reference MOH/APP/2026/001.**

**Year 1 portfolio Tender titles.** Taken from the illustrative fixtures of HOME-CHG-001 v0.6 §10B.2 and ANL-CHG-001 v0.8 §10A.2, paired with the same states those fixtures give them:

| Portfolio | Title | State at the as-at instant | Design source |
|---|---|---|---|
| T1 | Supply and delivery of business laptops (canonical, unchanged) | Award decided; a required notice not yet confirmed | the canonical chain |
| T2 | Supply of printers | Report delivered; professional opinion pending (Charles Mutiso) | HOME, ANL |
| T3 | Supply of hospital laboratory analysers | Award decision pending (Amina Hassan) | HOME H12 |
| T4 | Supply of office desks | Committee review outstanding; evaluation deadline after the as-at instant | HOME, ANL |
| T5 | Supply of network switches | Opening complete; evaluation committee not yet appointed | HOME H12 |
| T6 | **New title needed**: the design has no titled open Tender with clarifications | Open for bids; clarifications; opening Upcoming | — |
| T7 | Supply of UPS units | Approved by Charles; publication decision pending (Amina) | HOME H1, H10, H12 |
| T8 | Supply of IT peripherals | Returned to Brian for the warranty correction | HOME, ANL |
| T9 | Supply of field laptops | Cancellation under the Accounting Officer's consideration | HOME H1, H12 |
| T10 | Supply of hospital beds | Cancelled; compliance evidence due after the as-at instant | HOME H1, H12 |
| T11 | Supply of servers | Cancelled; compliance evidence complete | ANL |
| Requisition awaiting authorisation | Clinic equipment | Submitted to Procurement (Charles) | ANL R-A, HOME H10 |

Suggested title for T6: **Supply of medical-grade tablets**. New; owner to confirm or replace.

**Year 2 Need titles.** New, needed so the two years don't repeat the same requirements. Suggested:
- Digital Health: "Health information exchange platform upgrade" (1 Programme).
- HRMD: "Training centre audio-visual equipment" (Each).
- Digital Health: "Clinical decision-support software licences" (Each).

They also keep "Digital health workforce certification programme" pending. Owner to confirm or replace.

**FY 2025/26 as a configured closed year**: only if the build shows it is needed (D3).

## 7. Not verified

- Whether Requisitions check their operational required-by against the Plan boundary or the financial year. The 20 Jun 2027 value satisfies both if they do.
- Whether any command refuses Year 1's late-2025 instants for a reason not read here, such as a rule effective date or an intake window. Phase 2 runs the commands and reports.
- Whether the Asset Disposal window (to 14 Jan 2028) collides with the as-at model. It is out of scope and is flagged in §4.
- The owner's library may hold KT-STD-001 or SEED-001 versions later than v1.22 and v1.4. The repository's latest are those.
