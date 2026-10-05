# ANL-CHG-001 — Procurement Analytics

| Control | Value |
|---|---|
| Document ID | ANL-CHG-001 |
| Version | 0.8 |
| Status | Approved — 4 October 2026 |
| v0.8 proposed status (retained) | Proposed — 4 October 2026; v0.6 is the approved version |
| v0.7 status (retained) | Proposed — 4 October 2026; v0.6 is the approved version |
| v0.6 status (retained) | Approved — 4 October 2026 |
| v0.6 proposed status (retained) | Proposed — 4 October 2026; v0.5, v0.4 and v0.3 were Proposed and never approved; approval of v0.6 required |
| v0.5 status (retained) | Proposed — 4 October 2026; v0.4 and v0.3 were Proposed and never approved; approval of v0.5 required |
| v0.4 status (retained) | Proposed — 4 October 2026; v0.3 was Proposed and never approved; approval of v0.4 required |
| Approved on | 4 October 2026 |
| Approval record | v0.8: Project Owner, 4 October 2026, verbatim: “Yes”, answering “Shall I apply this pass, and then approve KT-STD v1.22, HOME v0.6 and ANL v0.8 together?”. Approves v0.8 including the v0.7 content it incorporates; no separate approval of v0.7. (Proposed record read: None for v0.8. None for v0.7. v0.6: Project Owner, 4 October 2026, verbatim: “Mark the three documents as approved and give them to me to download”. Approves v0.6 in full, including the v0.4 and v0.5 content it incorporates; this creates no separate approval of v0.4 or v0.5. None recorded for v0.3. (Proposed record read: None for v0.6. None for v0.5. None for v0.4. None recorded for v0.3.)) |
| v0.3 status (retained) | Proposed; requirements and static design contract in this document |
| Date | 4 October 2026 |
| Owner | kentender_core |
| Supersedes | ANL-CHG-001 v0.7 and v0.6 on approval only. v0.7 read: ANL-CHG-001 v0.6 on approval only. v0.6 read: ANL-CHG-001 v0.5 on approval only. v0.5 superseded ANL-CHG-001 v0.4 on approval only. v0.4 superseded ANL-CHG-001 v0.3 on approval only. v0.3 superseded ANL-CHG-001 v0.2 and its separate design-prompt extract   |
| Sources | KT-STD-001 v1.22 (v0.6 read: KT-STD-001 v1.18; v0.5 read: KT-STD-001 v1.17; v0.4 read: KT-STD-001 v1.16; v0.3 read: KT-STD-001 v1.15); OVS-CHG-001 v0.6; AUTH-ADR-001 v1.11; CTX-CHG-001 v1.1; CFG-CHG-002 v0.18; STR v1.9; BUD v1.12; NDS v1.16; PLN v1.29; REQ v1.14; TPR v0.17; BOP v0.11; EVL v0.5; AWD v0.5 |
| v0.4 change type | Domain and presentation change on the Project Owner decisions of 4 October 2026 (§1, D-ANL-01 to D-ANL-05): Analytics becomes an analytics surface with time-based measures, value measures and lineage-based Plan coverage, and areas become tabs with pushed routes and URL-encoded filter state. Adds §4A, §§5.4–5.5, §7.1, §9.1, §10A, §13.1, §16, §17.1 and §18.1; adds rows to §§1, 8, 11 and 14. All v0.3 content is retained; superseded v0.3 rules are marked in place and kept as history. No owner business command, lifecycle, stored record or permission is added. |
| v0.5 change type | Applies the Project Owner decisions of 4 October 2026 on the v0.4 review (§1, D-ANL-06 to D-ANL-10): the Analytics archetype and chart forms move to KT-STD-001 v1.17; the funding-position audience is set, with a department view for Heads of User Department; the HoD award-amount treatment, the twelve-month window and the waiting bands are confirmed; the Technical Operator has site-wide read-only Analytics access. Adds a Budget Line fixture, ANL-DES-29F, ANL-DES-31J, ANL-AC-25 to ANL-AC-27 and §18.0. All v0.4 content is retained; changed wording keeps its v0.4 reading beside it. |
| v0.6 change type | Visual-language change applying KT-STD-001 v1.18 §2.6.11 (D-ANL-11): colour roles per chart, area icons, tinted region surfaces, display-size result figures, lighter captions and permitted empty-state illustration in §10A.1; two captions shortened with their meaning kept in the definitions; ANL-AC-28; §17.1 and §18 rows. No measure, value, label of a fact, action, state or permission changes. |
| v0.7 change type | Surface correction only, following KT-STD-001 v1.22 §2.4 and D-ANL-12: chart regions and the summary strip sit on the white sheet without a fill. Colour roles, icons, measures, values and states are unchanged. |
| v0.8 change type | Presentation alignment with HOME-CHG-001 v0.6 (D-ANL-13): each summary-strip column takes the Home summary-column treatment, and result figures use the design system's figure colour; the render pass (D-ANL-14) records the rendered treatment, removes repeated waiting times and counts and the register links, adds a narrow rule, updates the first-view rule and moves ANL-DES-28 to the Accounting Officer. No measure, value, label or state changes. |

**Controlling decision:** Analytics gives a read-only view of authorised Needs, departmental plans, annual Plan items, Requisitions and Tender proceedings. It distinguishes current work, recorded outcomes and unfinished obligations. Each count has its own unit and accessible source records. Strategy and funding are supporting owner context. The complete requirement and design input are in this document; there is no companion specification or prompt file.

**Controlling decision added in v0.4:** Procurement Analytics is an analytics surface, not a status register. Within the same read-only, owner-sourced and permission-scoped boundary it also shows how work is distributed, how long recorded key steps took, how long current matters have waited, how much planned value is covered by authorised requisitions, and the Budget funding position. Each figure keeps its own unit and owner source; different units and different kinds of amount are never added together. Areas are peer tabs on one page, and the selected tab and filters are carried in the route so that refresh, Back and shared links reopen the same view. The static design input is §10A.

## 1. Governing decision and disposition register

| Earlier item / review finding | Disposition in v0.3 |
|---|---|
| Tender-only v0.1 | Retain v0.2 cross-module scope. No Tender-only product boundary. |
| Saved prompt extract and hierarchy companion | Retired as inputs; use this document’s §10 with KT-STD §2. No separate clarification is required. |
| Incomplete structure and screen briefs | Use applicable KT-STD §7 sections and twelve-part base brief with separately identified variants. |
| Register archetype containing several competing dashboard regions | Overview is one comparative area register. Selected area is one record register with a subordinate summary; no multi-area task queue or peer chart/dashboard. (v0.4: superseded by D-ANL-01 and §10A; the prohibition on a multi-area task queue is retained.) |
| Root creation dates exclude older outstanding work | Remove Created from/to. Default All years; optional Financial year filters owner-attributed records, including earlier-created records for that year. No mandatory current-year/configuration gate. |
| Annual Plan root count switches to Plan-item count for HoD | Count stable Plan items for both site-wide and departmental views, from the operative Active Version of each selected Annual Plan root. Candidate Version is disclosed separately. |
| Award decision called Concluded | Remove In progress/Concluded measures. Stage and recorded decision are separate; notices, response, restrictions and handoff can remain after Award/No award. |
| Opening complete; Evaluation not started | Replace with verified EVL intake/current work. Approved Evaluation receives and checks nonempty Opening automatically. |
| Generic “No decision recorded” hides earlier decisions | Name the decision type, e.g. No AO award decision recorded. |
| Generic Strategy/funding buttons imply an unspecified applicable record | Link explicitly to owner registers; show record-specific context only from an exact owner relationship. |
| Six Tender roots supported by only two consumed Requisitions | Correct to seven Requisition roots: six authorised and consumed, one still submitted. Seven Active Plan items and explicit owner lineage support the dataset. |
| Static input refers to fixture tables outside the design section | All pictured rows and expanded detail are repeated exactly within §10; no missing source section for the designer. |
| D-ANL-01 — v0.4 review finding: the dry-run design was table- and text-heavy because v0.3 specified a status register. Project Owner, 4 October 2026, asked “Is this Analytics, or a status/oversight register?”, answered verbatim: “Analytics” | Analytics shows distributions, waiting time, elapsed time, value and coverage as charts and summary figures (§4A, §10A). Record registers remain as the drill-down layer in each area tab. The v0.3 Overview register (§10 ANL-DES-01) is retained as history. |
| D-ANL-02 — Project Owner, 4 October 2026, asked “May time-based measures be in scope?”, answered verbatim: “In scope.” | Monthly recorded events, elapsed calendar days between recorded key steps, waiting time of current matters and Planning's own invitation timing measure (§4A ANL-M-02 to ANL-M-05, §5.4). No forecast, overdue judgement or statutory-period calculation is introduced. The §5.1 current-position rule is retained for counts and states. |
| D-ANL-03 — Project Owner, 4 October 2026, asked “May value measures be in scope?”, answered verbatim: “In scope” | Planned value, Requisition value, authorised requisition value by Tender stage, recorded award amount and the Budget funding position, each from its owner and labelled by kind (§4A ANL-M-06 to ANL-M-11, §5.5). The v0.3 §4 statement that no allocation or availability total is defined is superseded for the funding position only. |
| D-ANL-04 — Project Owner, 4 October 2026, asked “Is lineage-based plan execution coverage acceptable under the conversion-percentage ban?”, answered verbatim: “Acceptable” | Plan coverage uses PLN-CHG-001 v1.29 §5.4.6 **Procurement coverage** and PLN-CHG-001 v1.29 §4.8 `ProceedingCoverage` projection (§4A ANL-M-07). It is the only percentage Analytics shows. The §2 ban on a cross-module conversion percentage between unrelated counts is retained. |
| D-ANL-05 — Project Owner, 4 October 2026, on tabs and URL-encoded state with search text and paging excluded from the URL, answered verbatim: “Recommendation accepted.” | Areas are tabs; each tab and filter selection is a pushed route under §9.1, applying KT-STD-001 v1.16 §3A.3 (“Route and view shall never diverge”). Search text and page cursor stay out of the URL. |
| v0.4 review correction — menu visibility | The v0.4 review suggested showing the Analytics menu item only to roles with a permitted area. That contradicts KT-STD-001 v1.16 §3A.3 (“Gate navigation, do not hide it”) and is withdrawn. The menu item stays visible; access is resolved on the page. |
| D-ANL-06 — Project Owner, 4 October 2026, on the Analytics page type, answered verbatim: “Revise KT-STD” | KT-STD-001 v1.17 adds the **Analytics** archetype to KT-STD-001 v1.17 §2.6.3 and chart forms in KT-STD-001 v1.17 §2.6.10. §10A.1 cites them; the stated departure in v0.4 is withdrawn. |
| D-ANL-07 — Project Owner, 4 October 2026, on who sees the funding position, answered verbatim: “All budget / finance roles and Head of User Department, limited by departmental visibility;  Head of Procurement, Accounting Officer, Auditor,” | Audience and department view in §5.5 rule 5. Budget Officer, Budget Approver, Finance Confirmation Officer, Head of Procurement Function, Accounting Officer and Auditor; Head of User Department through the department view only. The read verdict remains BUD's; §17.1 names the BUD correction. |
| D-ANL-08 — Project Owner, 4 October 2026, on the award amount for department heads, answered verbatim: “Peter's views currently show no award amount until the Award module confirms what its department-head summary contains.” | v0.4 treatment confirmed: no award amount in HoD views until AWD confirms its HoD summary content (§17.1). |
| D-ANL-09 — Project Owner, 4 October 2026, on the trend period and waiting bands, answered verbatim: “Accepted.” | §5.4 rule 1 window and the ANL-M-02 bands are confirmed. |
| D-ANL-10 — Project Owner, 4 October 2026, on the Daniel Otieno conflict, answered verbatim: “Technical Operator has site-wide read-only access” | The Technical Operator reads every Analytics tab, figure, chart and row site-wide, including the funding position, with no action beyond navigation, filters and Refresh (§6). The v0.3 §6 sentence on technical operators and ANL-DES-11B's use of Daniel Otieno are superseded; ANL-DES-31J pictures his view. |
| D-ANL-11 — Project Owner, 4 October 2026: “The standards are there to serve and not straight-jacket! We created the standards and WE CAN most definitely change them.”, on the design review asking to “Check the iconography, restrained color, and also suggest any changes that will make for an attractive system” | KT-STD-001 v1.18 adds §2.6.11. §10A.1 replaces the neutral-only chart colour and flat-region rules with colour by meaning, area icons, tinted surfaces and display figures. |
| D-ANL-12 — the tinted-region direction was rejected on the rendered Home artboard. Project Owner, 4 October 2026, choosing between rendered Option A (Frappe workspace cards) and Option B (light grey ground with one bordered white sheet), answered verbatim: “Option B” | §10A.1 rule 6 follows KT-STD-001 v1.22 §2.4: no tinted regions or summary band. |
| D-ANL-13 — Project Owner, 4 October 2026, on the five adjustments to the Claude Design review (main column for oversight-only users; figures in heading colour; module name kept visible on the quiet line; relative times with the exact time always visible; Coming up kept in the main column), answered verbatim: “Yes”; on the Option C brief and render: “Approved” | The Home summary column and figure colour apply to the Analytics summary strip and result figures (§10A.1 rules 6 and 8). The chart and register layout is unchanged. |
| D-ANL-14 — render review of ANL-DES-21, 22 and 25 found repeated waiting times and counts, navigation links that duplicate Frappe, a first-view rule the accepted render does not meet, and the Accounting Officer absent from the funding view. Project Owner, 4 October 2026, on the rendered Analytics artboards: “See the sample analytics designs. They a much better fit”; on the resulting ANL v0.8 pass and joint approval, answered verbatim: “Yes” | §10A.1 rules 11 and 12, the outstanding-row, waiting-chart, link, first-view and ANL-DES-28 changes below. Rendering defects are listed for Claude Design and need no requirement change. |

## 2. Purpose, outcomes and scope

The reader can compare position across areas, inspect outstanding matters, distinguish a decision from completed obligations, and open evidence. Analytics makes no business decision and assigns no work. Its questions are: Where does each area stand? What is outstanding and who holds it? What outcome is recorded? Which records support the figure?

Needs are optional and direct Planning entry is valid. Combined/split sources and downstream versions are not a linear funnel. There is no combined Total procurements, cross-module conversion percentage, health score or inferred absence of problems.

**v0.4 scope addition (D-ANL-01 to D-ANL-04).** Analytics also answers: How long have current matters been waiting? How long did recorded key steps take in the last twelve months? How much planned value is covered by authorised requisitions? What is the Budget funding position? These measures are defined once in §4A. Plan coverage is a lineage measure owned by Planning, not a conversion percentage between unrelated counts. There is still no combined total, health or risk score, forecast, savings figure or budget-utilisation percentage.

Contract Management, delivery, inspection, performance and Accounts measures remain deferred pending current owner requirements. Their later inclusion must count independent signed contracts without requiring Tender/Award predecessors. ERPNext Accounts remains the first-deployment accounting source. This document does not introduce financial ledgers, payment measures or a generic inventory module.

## 3. Ownership and dependency boundary

| Owner | Authoritative input / boundary |
|---|---|
| NDS | Need root, current accepted/submitted disposition and separately disclosed successor; accepted does not mean included in an Active Plan. |
| PLN | DPP root/accepted submission and candidate; stable Plan item in exact Active Annual Plan Version; candidate changes do not replace operative allowance. |
| REQ | Root/current Version, authorisation, return reason and confirmed consumption; authorisation is not consumption. |
| TPR/BOP/EVL/AWD | Certified Tender identity/scope, released progress, delivered report, current Award cycle, decision and outstanding obligations. No classification from browser badges or child existence alone. |
| STR/BUD | Approved direction/funding records and permitted exact relationships. Owner calculations remain authoritative. |
| AUTH/CTX/CFG | Current responsibility predicates; local filters; native Fiscal Year identities and site timezone. Filters do not grant authority. |
| Core | Composition, labelled counts, area/state selection, pagination and safe navigation. No business state or recommendation. |

Use canonical owner reads listed in §7. Proposed additions are safe Analytics projections in those interfaces, not a second permission service or direct SQL over owner tables.

## 4. Canonical read model and measures

Response values below are transient; no new stored business records are introduced.

| Area / unit | Count and current position |
|---|---|
| Needs / Needs | Distinct readable root; current owner disposition. Accepted baseline and pending successor count once, with separately labelled pending work. |
| Departmental planning / departmental plans | Distinct readable DPP root; accepted submission remains effective while an update exists. |
| Annual planning / Plan items | Distinct stable item identities in the exact operative Active Version of each selected Annual Plan root. No candidate-only item added to this total. Return separately any permitted pending candidate and its material outstanding matters; those facts are not hidden by counting only operative items. If no Active Plan exists, report No Active Plan, not zero items in an invented plan. |
| Requisitions / Requisitions | Distinct readable root; current Version/decision state, plus separately recorded consumption status. |
| Tender proceedings / Tenders | Distinct readable Tender root; one §5 stage and separately its current recorded AO outcome, restrictions and outstanding obligations. |

Per area return: unit; selected fiscal year/department; safe identities; count completeness; state-distribution completeness; source revision/event and owner read time; exact row facts; owner destinations; paging cursor. Outstanding matter facts are the owner’s required action/issue, reason, responsible role/person, since and actual due date if supplied. Do not sum matters into a count of procurement processes. Totals are not page lengths; contributors/versions do not duplicate an identity.

Strategy/Budget context uses labelled register destinations and exact related records within the owner view. No Analytics-wide allocation/availability total is defined in this release: a shared funding line cannot be multiplied across source records, and availability is not cash or expenditure. (v0.4: superseded for the funding position by §4A ANL-M-11, which shows Budget's own totals for one Fiscal Year and never multiplies a line across source records; the remainder of this paragraph is retained.)

## 4A. Analytics measures — v0.4

Every measure below is computed from owner reads under the same scope as its area's records (§§3, 6, 7). Each has one unit and one owner. A measure is never added to another measure. The browser never calculates a measure from rows; the server returns each value with its owner read time and completeness (§7.1).

### 4A.1 Measure catalogue

| ID | Visible name | Unit | Definition | Owner source | Shown in |
|---|---|---|---|---|---|
| ANL-M-01 | Area count and state distribution | Each area's own §4 unit | The §4 count for the area, split by current state. Needs by current owner disposition; departmental plans by accepted state; Plan items by coverage state (ANL-M-07); Requisitions by current state; Tenders by §5.2 bucket. Segments add up to the area count because each record is classified once. | NDS, PLN, REQ, TPR/BOP/EVL/AWD as in §3 | Overview summary strip; each area tab |
| ANL-M-02 | Outstanding matters by waiting time | Outstanding matters | Current owner outstanding matters (§4) for permitted records, grouped by waiting time from the owner's recorded `since` instant to the read time. Bands: **0–7 days**, **8–30 days**, **31–90 days**, **Over 90 days**. A matter counts once, in the area of the record that holds it. | Owner `next_step.since` under KT-STD-001 v1.16 §3B.2, through each owner's outstanding-matter projection | Overview; each area tab's outstanding work lines |
| ANL-M-03 | Recorded each month | Recorded events of one named kind | For each calendar month of the §5.4 window, the number of recorded owner events of each kind in §4A.2, for permitted records within the selected filters. Each kind is its own series. | §4A.2 | Needs, Departmental planning, Requisitions and Tender proceedings tabs |
| ANL-M-04 | Time between key steps | Calendar days | For each transition in §4A.3 completed inside the §5.4 window: the number completed, median, shortest and longest calendar days between its start and end events (§5.4). | §4A.3 | Overview (all five transitions); Requisitions tab (T1, T2); Tender proceedings tab (T2 to T5) |
| ANL-M-05 | Tender invitation timing | Days after approved date | For each published Tender proceeding, Planning's **Baseline lateness** for the invitation milestone: actual invitation date minus the approved baseline invitation date of the exact Plan Version that proceeding covers. Positive is later, negative is earlier. | PLN-CHG-001 v1.29 §5.5.1A and PLN-CHG-001 v1.29 §4.8 `MilestoneActualEvent`; PLN label **Days after approved date** from PLN-CHG-001 v1.29 §10.13 | Annual planning tab |
| ANL-M-06 | Planned value | KES | Sum of PLN `planned_value` for the distinct stable Plan items counted in the Annual planning area (§4). In a department selection: sum of the `PlanSourceAllocation` Money amounts whose source department is the selected Organisation Unit. | PLN-CHG-001 v1.29 §4.6 | Overview (Plan coverage); Annual planning tab |
| ANL-M-07 | Plan coverage | KES, Plan items and one whole percentage | **Covered by authorised requisitions** = sum of covered value in PLN `ProceedingCoverage` for the counted items' allocations. **Not yet covered** = Planned value minus Covered. Item coverage state: **Fully covered** when covered equals planned, **Partly covered** when covered is above zero and below planned, **Not covered** when covered is zero. In a department selection only that department's allocations are used, for both value and item state. Percentage = Covered ÷ Planned × 100 under §5.5. | PLN-CHG-001 v1.29 §5.4.6 **Procurement coverage** and PLN-CHG-001 v1.29 §4.8 `ProceedingCoverage`; the same facts PLN shows in U14 (PLN-CHG-001 v1.29 §10.13) | Overview; Annual planning tab; Annual planning column of the summary strip |
| ANL-M-08 | Requisition value | KES | For each Requisition: the sum of `requested_value` on the drawdown lines of its current Version. Shown as **requested** for Awaiting Department Approval and Submitted to Procurement, and as **authorised** for Authorised. Draft, Withdrawn, Revoked, Upstream correction required and Returned Versions contribute no value total. In a department selection only drawdown lines whose `contributing_org_unit_id` is that department are used. | REQ-CHG-001 v1.14 §§5.2–5.3, 7.1 | Requisitions tab |
| ANL-M-09 | Authorised requisition value by Tender stage | KES | For each Tender: the authorised value of the exact Requisition Version whose handoff it consumed, summed by §5.2 bucket. Labelled **Authorised requisition value**; never called a Tender value, estimate or price. Department selection as ANL-M-08. | REQ-CHG-001 v1.14 §§5.3, 5.12; TPR-CHG-001 v0.17 §4.1 `requisition_handoff_id` | Tender proceedings tab |
| ANL-M-10 | Recorded award amount | KES | The amount of the current committed **Award** decision for a Tender's current decision cycle. Labelled **Award amount**. A superseded decision is history, not a second amount. No award, Return for correction and pending decisions have no amount. No department total is formed, because one award amount is not divided between contributing departments by any owner rule. | AWD-CHG-001 v0.5 §4 Decision; AWD-CHG-001 v0.5 §5.3 | Tender proceedings tab, per row and as one site-wide total |
| ANL-M-11 | Funding position | KES | For one selected Fiscal Year: Budget's own totals for its Active Version — **Registered allocation**, **Reserved for requisitions**, **Committed to contracts** and **Available to reserve** — with Budget's meanings. Reserved, Committed and Available together equal Registered allocation. | BUD-CHG-001 v1.12 §§4.9, 5, 9.1 | Overview, only under §5.5 rule 5 (v0.5: or, under §5.5 rule 5, the department view of Budget Lines available to the department and that department's own reservations and commitments on Budget Lines available to all departments.) |

### 4A.2 Recorded event kinds for ANL-M-03

| Area | Series label | Event counted | Owner fact |
|---|---|---|---|
| Needs | **Accepted for planning** | First acceptance of a Need root | NDS-CHG-001 v1.16 §4.5 decision timestamp |
| Departmental planning | **Departmental plans accepted** | Each Accept decision on a departmental plan submission | PLN-CHG-001 v1.29 §4.4 `DPPValidationDecision` decision instant |
| Requisitions | **Submitted to Procurement** | Each Version entering Submitted to Procurement | REQ-CHG-001 v1.14 §7.1 transition, recorded under REQ-CHG-001 v1.14 §15 |
| Requisitions | **Authorised** | Each Authorise requisition decision | REQ-CHG-001 v1.14 §5.11 `RequisitionDecision` timestamp |
| Tender proceedings | **Published** | First establishment of `published_at` | TPR-CHG-001 v0.17 §4.1 |
| Tender proceedings | **Cancelled** | Each Tender cancellation decision | TPR-CHG-001 v0.17 §4.10 `decided_at` |
| Tender proceedings | **AO award decisions** | Each committed Award or No award decision version | AWD-CHG-001 v0.5 §4 Decision AO time; a Return for correction is not counted |

The Annual planning tab has no monthly series in this release.

### 4A.3 Transitions for ANL-M-04

| ID | Visible label | Start event | End event | Rule |
|---|---|---|---|---|
| T1 | **Requisition submitted to authorised** | The authorised Version entering Submitted to Procurement | Its Authorise requisition decision | Uses the Version that was authorised; earlier returned Versions are not added. |
| T2 | **Requisition authorised to Tender started** | Authorise requisition decision | REQ `handoff_consumed_at` (REQ-CHG-001 v1.14 §5.13) | One per consumed handoff. |
| T3 | **Tender started to published** | REQ `handoff_consumed_at` for the Tender's handoff | TPR `published_at` | Unpublished Tenders are not completed transitions. |
| T4 | **Bid opening complete to evaluation report sent** | BOP Opening complete for a nonempty opening (BOP-CHG-001 v0.11 §5) | First **Report sent** for that Evaluation case (EVL-CHG-001 v0.5 §5.5) | Empty openings have no transition. Later report versions are not added. |
| T5 | **Evaluation report sent to AO decision recorded** | AWD Award case received time (AWD-CHG-001 v0.5 §4) | First committed Award or No award decision of decision cycle 1 | Return for correction is not an end event. |

A transition is completed when both events are recorded and the end event falls inside the §5.4 window. A transition whose start event is unavailable is excluded and the read's completeness is marked incomplete (§8).

## 5. Selection and stage rules

### 5.1 Filters and temporal meaning

Default **Financial year: All years**, **Department: All departments** within current permitted scope. The year is an optional local record-data filter, not a permission dimension. Native configured years provide options; absence of a single current year does not block access. A selected year matches the owner’s fiscal-year identity: NDS/DPP/Plan directly; REQ/Tender through their exact immutable Planning/Requisition source. Do not infer a year from creation date or display reference. Historical years remain selectable for authorised history, including disabled years with records.

Department matches owner-certified owning/contributing OUs. Site-wide All departments means site-wide permission; a HoD’s All departments means their permitted set only. Count a contributor record once and identify its lead. Plan-item department attribution comes from exact Active-Version source allocations. A department filter narrows existing authority; it does not limit an independently valid second responsibility.

The view is **current position when loaded**, not a reconstructed historical snapshot or decisions recorded in a date range. Each area carries its actual read time. Do not promise a common transaction/as-of instant across independent owner calls. The page marks the last completed refresh; if area read times differ, show them in supporting definitions. Explicit Refresh rereads; no silent background replacement. Record routes always show current authority and retain exact historical versions where requested. (v0.4: counts and states keep this current-position rule; the time-based measures of §4A count recorded events inside the window defined in §5.4 and do not reconstruct earlier positions.)

### 5.2 Tender proceeding presentation mapping

These are presentation buckets, not new owner lifecycle states. Every Tender is classified once from confirmed owner transitions; unknown progress has its own Status unavailable category.

| Bucket | Confirmed basis / important distinctions |
|---|---|
| Tender preparation and publication | TPR Draft, review/approval/authorisation or channel confirmation before published-open completion. Returns/holds remain here with exact reason. |
| Open for bids | TPR confirms published-open state and operative deadline not yet closed. |
| Opening | Submission closed and BOP opening still pending/active, or its confirmed completed package awaits EVL receipt. Display the exact pending-delivery fact; do not invent a manual Start evaluation step. Never reveal sealed content. |
| Evaluation | EVL confirms nonempty Opening receipt and current pre-delivery work. Automatic checks, review/signing and approved correction work are shown by owner, not a Start evaluation action. |
| Award | AWD confirms report receipt/current cycle, including a committed award with notices/response/wait/handoff work. Correction/restriction status is separate. |
| Sent to Contract Management | AWD confirms durable delivery to Contract Management Stage 1. This says nothing about contract signature, delivery or payment. |
| Closed | Authoritative cancellation, final empty Opening/no evaluation required, or current closed No award cycle. Show the exact outcome and any outstanding follow-up/compliance work. Closed is not “all obligations complete”. |
| Status unavailable | Tender identity is permitted but a required known stage read/receipt cannot be established. Do not guess; classify safely and name the unavailable area only if its existence is authorised. |

Terminal cancellation takes precedence; retained earlier report/decision remains historical. Empty Opening closes evaluation preparation without inventing a report or Award case. Successful EVL delivery awaiting AWD receipt is displayed **Evaluation report delivered — Award receipt pending**, not assumed successful Award intake. A closed decision under governed reconsideration keeps its recorded outcome and shows owner-provided current correction work; never make the original decision disappear. Stage counts are separate from counts of Award/No award decisions, and this release shows decisions on rows rather than adding a competing decision metric.

### 5.3 Information priority

Overview leads with each area’s current result and material outstanding matters. Selected-area view leads with its actual outstanding facts and record rows; the stage summary is subordinate. A blocked/returned reason remains visible, even after an outcome was recorded. Routine facts are concise; history/calculation detail is a named disclosure or exact owner link. Tables serve real cross-area or record comparison. No five-level hierarchy, arbitrary table-size rule, unsupported No exceptions, urgency score or claim that assignment proves activity.

### 5.4 Window and time rules — v0.4

1. **Window.** Monthly events (ANL-M-03) and completed transitions (ANL-M-04) use the twelve calendar months ending with the month that contains the read time, in the site timezone. The current month is labelled **to date**. The Financial year and Department filters select which records are included; they do not change the window.
2. **Calendar days.** Elapsed and waiting days are the difference between the local calendar dates of the two instants, in the site timezone. The result is a whole number of days, zero or more. It is not a statutory period, business-day count or Planning duration variance (PLN-CHG-001 v1.29 §5.5.1A).
3. **Statistics.** For ANL-M-04 show the number completed, the median, the shortest and the longest. With an even number of values the median is the mean of the two middle values, shown with one decimal place only when it ends in .5. With no completed transitions show **No completed steps in these 12 months.**
4. **Waiting time.** ANL-M-02 bands use the owner's recorded `since`. Waiting time is never called late, overdue or at risk. An owner's own overdue fact, such as an Evaluation past its statutory deadline under EVL-CHG-001 v0.5 §5.7, may appear on that matter's line in the owner's words; Analytics adds no overdue count of its own.
5. **No forecast.** No expected date, projected completion, trend line or extrapolation is shown.

### 5.5 Value rules — v0.4

1. **Money.** Amounts are exact decimals from the owner in KES (BUD-CHG-001 v1.12 §4.8). Display uses thousands separators; the two decimal places are shown only when the cents are not zero, for example **KES 55,500,000** and **KES 7,185,000.50**. Chart axis tick labels may abbreviate millions as **KES 20 m**; data labels never abbreviate.
2. **Kinds of amount.** Planned value, requested value, authorised value, award amount and Budget positions are different kinds of amount. They are never added together, subtracted from one another or shown as a ratio, except the ANL-M-07 coverage percentage and Budget's own identity in ANL-M-11.
3. **Percentage.** The ANL-M-07 percentage is Covered ÷ Planned × 100, rounded half up to a whole number, shown as **81%**. When Planned value is zero or unavailable, no percentage is shown.
4. **Department attribution.** Department totals use only owner records that carry the department: Planning allocations (ANL-M-06, ANL-M-07) and Requisition drawdown lines (ANL-M-08, ANL-M-09). A row value in a department selection is the department's share and shows the whole value as secondary text, for example **KES 2,500,000** with **HRMD share of KES 6,500,000**. (v0.5: for the funding position, Budget Lines by Available to and Budget reservations by `source_organisation_unit_id`, under rule 5.)
5. **Funding position.** ANL-M-11 is shown only when a single Fiscal Year is selected, the actor holds a responsibility in the D-ANL-07 audience or is a technical reader, and the BUD read returns a permitted verdict. **Whole-Budget view:** Budget Officer, Budget Approver, Finance Confirmation Officer, Head of Procurement Function, Accounting Officer, Auditor and technical readers (KT-STD-001 v1.17 §3A.6), with Department All departments. **Department view:** any of those actors with a department selected, and every Head of User Department view, limited to the departments in the actor's permitted scope. It shows (a) Budget's Registered allocation, Reserved, Committed and Available for the Budget Lines whose Available to is that department; and (b) for Budget Lines available to all departments, only the Reserved amount of reservations whose `source_organisation_unit_id` is that department and the Committed amount converted from those reservations. The allocation and available amount of a line available to all departments are never divided: BUD-CHG-001 v1.12 states that “a shared Budget Line alone does not establish departmental ownership”. An actor outside the audience sees no funding region. Otherwise the region shows the §8 message. (v0.4 read: **Funding position.** ANL-M-11 is shown only when a single Fiscal Year is selected, Department is All departments, the actor's Analytics scope is site-wide and the BUD read returns a permitted verdict. BUD-CHG-001 v1.12 states that “a shared Budget Line alone does not establish departmental ownership”, so the position is never divided by department. Otherwise the region shows one of the §10A.2 messages.)
6. **No derived money measure.** No savings, variance between award amount and authorised value, utilisation percentage, spend, payment or cash figure is shown.

## 6. Roles and permissions

Apply each owner’s AUTH/OVS verdict before count, stage, title, search suggestion and row. AO/HOPF/HoD/auditor/technical access follows their actual owner grants; no new Analytics business role. HoD gets scoped downstream summaries, not committee working findings or full bid/report access. Unfinished Evaluation corrections do not replace delivered oversight evidence. Technical operators do not receive business aggregates from a support assignment alone. (v0.5: superseded by D-ANL-10 — the Technical Operator has site-wide read-only Analytics access, including every aggregate and the funding position, and no business action.)

Keep navigation under KT-STD §3A; an unauthorised reader receives an explanatory Analytics access state. Protected record existence remains masked. Permitted aggregate cannot include identities whose existence is undisclosable. Role expiry invalidates affected rows/counts on the next read; destination reads recheck independently.

**v0.4 addition.** Value, time and coverage measures obey the same owner verdicts as counts. A measure includes only records whose identity the actor may know; a masked record contributes to no figure. Where an owner returns a summary without an amount for a responsibility, such as the HoD scoped Award summary under AWD-CHG-001 v0.5's OVS amendment, Analytics shows no amount for that record and forms no total from it. The funding position follows §5.5 rule 5.

## 7. Service contract

**Proposed `GetProcurementAnalytics` read:** input is selected area, optional fiscal-year ID, permitted department ID, area state filter, search term and page cursor. Actor/scope comes from server context. Overview returns the five separately labelled units and permitted context links. Area read returns the §4 projection; state/search filters affect record results, not overview or whole-area state counts. Count search matches separately. A new selection clears incompatible state filters. Pages contain ten rows.

| Owner binding | Existing read family / proposed adapter duty |
|---|---|
| Needs | NDS register/detail/accepted-revision contracts; return scoped roots and current disposition, not only the actor’s task queue. |
| Planning | GetPlanningWorkspace, GetDepartmentalPlan, GetAnnualPlan, GetPlanItem; distinguish current accepted/Active pointer from candidate. |
| Requisitions | GetRequisitionWorkspace, GetProcurementAuthorisationTask, GetAuthorisedRequisitionHandoff, GetRequisitionHistory; use neutral read scope, not personal-task count. |
| Tenders | GetTendersWorkspace/GetTender plus OVS Decisions and progress projections; return distinct Tender roots. |
| Opening/Evaluation/Award | Approved owner stage/disclosure reads and authoritative receipt/correction/decision evidence; AWD GetAwardRecord/GetAwardAuthorityStatus distinguish decision, notice and delivery. |
| Context | STR approved-register read and BUD approved funding-register/line reads under current permission. No guessed exact record. |

Owner adapters return identities, read time, completeness and safe destinations. Count and row queries use the same scope. If stable full-set paging is unavailable, the adapter must obtain a bounded consistent owner revision set; do not produce complete-looking counts from changing pages. Core emits no business event, task or decision. Exact report/stage links must come from owner routing; missing bindings block implementation acceptance, not closed-fixture design generation.

### 7.1 Measure reads — v0.4

`GetProcurementAnalytics` additionally returns, for the selected tab, each §4A measure that tab shows: its value or series, unit, owner read time, completeness (complete, incomplete or unavailable) and the window bounds of §5.4. Inputs are unchanged except that the tab replaces the v0.3 selected area. State and search filters change record rows only; every measure describes the whole filtered area, as the v0.3 summary did.

| Owner | Proposed safe aggregate or projection read | Facts returned |
|---|---|---|
| NDS | Needs acceptance events in the window, by permitted Need | Decision timestamp of first acceptance |
| PLN | Departmental plan acceptance events; Active Version item value and allocation amounts by source department; `ProceedingCoverage` covered values; invitation Baseline lateness per proceeding | Instants, Money amounts, department attribution, covered values, baseline and actual invitation dates; the same predicate as GetPlanningWorkspace counts |
| REQ | Drawdown values by current Version state and contributing department; submission, authorisation and handoff-consumption instants | Money amounts and instants under the neutral read scope, not a personal task queue |
| TPR | `published_at` and cancellation `decided_at` per permitted Tender | Instants |
| BOP | Opening complete instant for nonempty openings | Instant only; no sealed content or bid count |
| EVL | First Report sent instant per Evaluation case | Instant only |
| AWD | Award case received time; first committed decision instant and outcome of cycle 1; current Award decision amount where the actor's owner read includes it | Instants, outcome and amount |
| BUD | Active Version totals for one Fiscal Year from `resolve_budget_context` and line positions (BUD-CHG-001 v1.12 §9.1) | Registered allocation, Reserved, Committed, Available, Version number and `as_at` (v0.5: for the department view, line positions with their Available to, and reserved and committed amounts by reservation `source_organisation_unit_id`.) |
| Owners with outstanding matters | Current outstanding-matter projections with `since` | Matter, holder and `since` |

Each read is a proposed Analytics projection inside the owner's canonical interface (§3), using the owner's own permission verdict. Core computes medians, bands, month buckets and the coverage percentage from returned facts on the server under §§5.4–5.5; it never queries owner tables. If any read needed by a measure is unavailable, that measure is unavailable and no partial figure is shown as complete.


## 8. Error contract

| Result | User language / treatment |
|---|---|
| Initial loading | **Loading Analytics…**; no counts or empty claim. |
| One area unavailable | **[Area] could not be loaded.** / **Try again**; other complete areas remain visible. |
| State read incomplete, identities complete | Total may remain known; unknown rows use **Status unavailable** and distribution includes that bucket. Never assign a guessed stage. |
| Identity/scope count incomplete | **[Area] totals are unavailable.** Safe partial rows labelled **Partial list**; no complete total. |
| All reads fail | **Analytics could not be loaded.** / **Try again**. |
| Filter invalid / stale selection | **Choose an available financial year.** or **Choose a department in your permitted area.** Preserve other valid filters; no broader silent fallback. |
| No permitted Analytics area | **No Analytics records are available to your responsibilities.** No protected titles/counts. |
| Successful filtered-empty | **No records match these filters.** / **Clear filters**. |
| v0.4: one measure unavailable | **[Measure name] could not be loaded.** / **Try again** in that region; other regions remain. No zero, empty chart or partial total. |
| v0.4: measure read incomplete | The region shows the complete figures it has and the sentence **Some records could not be included, so these figures may be incomplete.** No percentage is shown when either coverage figure is incomplete. |
| v0.4: no completed transitions or events | **No completed steps in these 12 months.** for ANL-M-04; a monthly chart with all months at zero shows its zero bars and the sentence **Nothing was recorded in these 12 months.** |
| v0.4: funding position not applicable | **Choose a financial year to see its funding position.** when All years is selected and the actor is in the §5.5 rule 5 audience. An actor outside the audience sees no funding region and no message. Neither is an error. (v0.4 read: **Choose a financial year to see its funding position.** when All years is selected; **Funding position is shown only for a site-wide view with All departments selected.** otherwise. Neither is an error.) |
| v0.4: tab route with an invalid filter value | Same as Filter invalid / stale selection; the route keeps the valid parts and the page states which choice is unavailable. |

These are composition response categories; owner errors remain authoritative. Denied owners are not described as service failures. A missing optional module is not zero records in an installed module.

## 9. UI architecture and routes

Proposed core route **`/app/analytics`**, menu **Analytics**. One page with **Overview** and local area selector. No separate module dashboard routes or stored context gate. (v0.4: the local area selector is replaced by tabs with pushed routes under §9.1; still one page and no stored context gate.)

| Row/link | Owner destination |
|---|---|
| Need | `/app/departmental-needs/{need_reference}`, exact accepted revision link if selected. |
| DPP / Plan item | Owner-generated exact DPP Submission / Active-Version item route from GetDepartmentalPlan / GetPlanItem. No guessed route or candidate substitution. |
| Requisition | Current authorised detail `/app/procurement-requisitions/{requisition_id}/authorised`; other permitted current detail `/app/procurement-requisitions/{requisition_id}`. Home/action tasks are not substituted here. |
| Tender | `/app/tenders/{tender_id}`; TPR Decisions and progress exposes permitted downstream links. |
| Strategy / Budget & Funding | `/app/strategy`, `/app/budget`, explicitly registers; not a claim of one applicable exact record. |

### 9.1 Tabs, routes and URL state — v0.4

One Analytics page has six peer tabs, used under KT-STD-001 v1.16 §2.6.4 (“Use tabs only for peer views of the same context”):

| Tab | Route |
|---|---|
| **Overview** | `/app/analytics` |
| **Needs** | `/app/analytics/needs` |
| **Departmental planning** | `/app/analytics/departmental-planning` |
| **Annual planning** | `/app/analytics/annual-planning` |
| **Requisitions** | `/app/analytics/requisitions` |
| **Tender proceedings** | `/app/analytics/tender-proceedings` |

Query parameters carry applied filters only: `fy` (native Fiscal Year ID; absent means All years), `dept` (Organisation Unit ID; absent means All departments) and `state` (the tab's state or stage key; absent means all). Search text and the paging cursor are never written to the URL, because search text can contain names that would enter browser history and server logs, and a cursor goes stale.

Selecting a tab, applying filters, clearing filters or choosing a state pushes a new route, so refresh, Back and a shared link reopen the same view, applying KT-STD-001 v1.16 §3A.3. Opening a route resolves the actor's verdict and re-reads every value; a link grants nothing. An invalid or unpermitted `fy`, `dept` or `state` value shows the §8 filter message and never widens silently. Changing tab keeps `fy` and `dept`, and drops `state` because states differ by area. The Analytics menu item stays visible to every desk user under KT-STD-001 v1.16 §3A.3; access is resolved on the page.

These are routes of one page, not separate module dashboards; the v0.3 prohibition on separate module dashboard routes is retained in that sense.

## 10. Static design contract

**v0.4: retained history, not design input.** This section is the v0.3 design contract and is kept unchanged as evidence. It is superseded by §10A on approval of v0.4. Do not supply this section to Claude Design.

Supply KT-STD v1.15 §2 and **this section only** for design generation. All pictured facts are here; no extracted prompt or external fixture section is required. Use approved **Register** archetype. Overview compares work areas; an area view compares records. No journey/next-step components on either.

### ANL-DES-01 — Charles’s Overview

1. **Identity/archetype/purpose:** Procurement Analytics; Register; Charles compares current position and chooses an area to inspect.
2. **Fixture outside artboard:** Charles Mutiso, HOPF, site-wide, 18 June 2027, 10:00 EAT; isolated illustrative A1 dataset, all owner reads completed at 10:00. All years/All departments. Records are presentation fixtures, not runtime seed facts. Exact outside-artboard identities: Need N-A (Clinic equipment) and N-B (Office furniture), accepted Revision 1 each; DPP D-A (Digital Health) and D-B (HRMD), accepted Submission 1 each; Annual Plan P-A, Active Version 1, item identities I-A through I-G in DES-07 order; Requisitions R-A through R-G in DES-04 order, current Version 1 each. Tenders 041–046 are distinct roots: 041 Draft Version 2 after return of Version 1; 042 Published Version 1; 043 Published Version 1 with confirmed Opening package and current Evaluation revision 1; 044 Published Version 1, delivered Evaluation report Version 1 and Award cycle 1; 045 Published Version 1, Award cycle 1 and AO decision Version 1; 046 cancelled Published Version 1, cancellation event 1. Keys N-/D-/P-/I-/R- are fixture identities, not rendered business references. The generated visible Tender references are design-only examples.
3. **Question/action:** Where does work stand, and which area needs investigation? Read-only. **View records** is navigation, not a decision.
4. **Priority:** Level 1 current results and material outstanding matters in area rows; Level 2 area/filter controls; Level 3 definitions and context links.
5. **Header:** **Procurement Analytics**; **See where procurement work stands and what is outstanding.** Quiet text action **Refresh**. Scope **All departments**; quiet **Updated 18 June 2027, 10:00 EAT**.
6. **Composition:** header; compact local controls; area comparison register; quiet context links; collapsed counting disclosure. One main register, no KPI grid, separate cross-module task queue or stage chart on Overview.
7. **Controls/content:** select **View** = **Overview**, options Overview / Needs / Departmental planning / Annual planning / Requisitions / Tender proceedings; select **Financial year** = **All years**, options All years / FY 2026/27 / FY 2027/28; select **Department** = **All departments**, options All departments / Digital Health / Human Resources Management and Development; standard **Apply filters**, text **Clear filters**. Table columns **Area**, **Current position**, **Outstanding work**, **Action**. Five exact rows:
   - **Needs** / **2 Needs accepted for planning** / **No outstanding matters recorded** / **View records**.
   - **Departmental planning** / **2 departmental plans accepted** / **No outstanding matters recorded** / **View records**.
   - **Annual planning** / **7 Plan items in the Active Plan** / **No outstanding matters recorded** / **View records**.
   - **Requisitions** / **7 Requisitions: 1 submitted to Procurement, 6 authorised** / **Clinic equipment requisition: awaiting authorisation by Charles Mutiso since 16 June 2027, 11:00 EAT** / **View records**.
   - **Tender proceedings** / **6 Tenders: 1 in preparation, 1 open for bids, 1 in Evaluation, 2 in Award, 1 cancelled** / **IT peripherals: warranty requirement needs correction by Brian Wafula. Office desks: committee review is outstanding. Printers: professional opinion awaited from Charles Mutiso. Monitors: award notices awaiting delivery.** / **View records**.
   The table is required to compare the same questions across five areas. Counts are labelled by unit. Beneath it **These counts describe different records and are not added together.** No grand total or Concluded measure.
8. **Actions/state:** Refresh quiet header text action; Apply filters standard button; Clear filters text; all five View records text links in Action column. No mutation, Download, Export, Assign or Approve. No search/paging on the fixed five-row Overview.
9. **Supporting detail:** quiet links **View Strategy register**, **View Budget & Funding register**. Collapsed **How these figures are counted** expands to: **Each area counts its own permitted records once. Financial year follows the record’s Planning source, not its creation date. Annual planning counts items in the Active Plan. Versions and contributing departments do not add records. An award decision does not mean notices or contract work are complete. These values describe current position when loaded. All area reads completed at 10:00 EAT.**
10. **Variants:** ANL-DES-02–11 below inherit this brief with stated replacements; each has a distinct ID. No conditional layout or action choice.
11. **Comprehension:** different units, upstream coverage and actual outstanding work are obvious without opening definitions. The award decision is not procurement completion. Context remains subordinate.
12. **Next step/journey:** neither record component appears on this Register; no personal task or tracker.

### ANL-DES-02 — Charles’s Tender proceedings

Inherit DES-01 header/controls, twelve-part brief and context/definitions. View selected **Tender proceedings**. Replace Overview register with: short result **6 Tenders**; visible **Outstanding work** compact paragraphs **Supply of IT peripherals — State the warranty period required from suppliers. Awaiting correction by Brian Wafula since 16 June 2027, 09:00 EAT.**; **Supply of printers — Awaiting professional opinion by Charles Mutiso since 16 June 2027, 14:07 EAT.**; **Supply of monitors — Award decision recorded. Required bidder notices are awaiting delivery.** These are current facts, not action buttons. **Supply of office desks — Automatic checks complete; committee review outstanding. Grace Wambui chairs the appointed committee.** Then subordinate horizontal stage chart labels **Tender preparation and publication 1**, **Open for bids 1**, **Evaluation 1**, **Award 2**, **Closed 1**. Values are visible; no colour-only state. No zero-category sentence is needed. Then expanded record register with columns **Tender**, **Current position**, **Recorded AO outcome**, **Action**; exact six rows:

| Tender / secondary reference | Current position | Recorded AO outcome | Action |
|---|---|---|---|
| Supply of IT peripherals / TND-MOH-2027-041 | Tender preparation — warranty requirement returned for correction | No AO award decision recorded | View record |
| Supply of network switches / TND-MOH-2027-042 | Open for bids | No AO award decision recorded | View record |
| Supply of office desks / TND-MOH-2027-043 | Evaluation — automatic checks complete; committee review outstanding | No AO award decision recorded | View record |
| Supply of printers / TND-MOH-2027-044 | Award — professional opinion outstanding | No AO award decision recorded | View record |
| Supply of monitors / TND-MOH-2027-045 | Award — required bidder notices awaiting delivery | Award decision recorded 17 June 2027, 11:00 EAT | View record |
| Supply of servers / TND-MOH-2027-046 | Closed — cancelled; cancellation compliance evidence complete | Cancellation recorded 16 June 2027, 12:00 EAT | View record |

Above register search input **Search Tender or reference**, blank; local state select **All stages**, options All stages / Tender preparation and publication / Open for bids / Evaluation / Award / Closed. Footer **Showing 6 of 6 Tenders**. No paging buttons for six results. All row links are enabled text links. Level 1 material reasons/current work; Level 2 comparable rows and state summary; Level 3 definitions/context. Outstanding paragraphs order: IT peripherals, Office desks, Printers, Monitors. First view reveals the real pending work; 045 remains in Award despite its decision. Neither chart nor table is collapsed. No next-step/tracker.

### ANL-DES-03 — Award filter

DES-02 fixture A1 unchanged; local state selected **Award** and Award chart bar selected. Outstanding facts and whole-area chart/6-Tender summary remain unchanged, labelled **All 6 Tenders in this area**. Table has only the exact 044 and 045 rows from DES-02. A table is justified by comparison of current work and recorded decisions across these two records. Footer **Showing 2 of 2 matching Tenders**; enabled text **Clear stage filter** beside local state. No duplicate chart or new total. Level priorities unchanged. No tracker.

### ANL-DES-04 — Requisitions

DES-01 View selected **Requisitions**, same A1 actor/time/filters. Replace Overview register with **7 Requisitions** and visible paragraph **Clinic equipment requisition — Awaiting authorisation by Charles Mutiso since 16 June 2027, 11:00 EAT.** Then seven-row register columns **Requisition**, **Current position**, **Tender relationship**, **Action**:

| Requisition | Current position | Tender relationship | Action |
|---|---|---|---|
| Clinic equipment requisition | Submitted to Procurement | No Tender created | View record |
| IT peripherals requisition | Authorised | TND-MOH-2027-041 created | View record |
| Network switches requisition | Authorised | TND-MOH-2027-042 created | View record |
| Office desks requisition | Authorised | TND-MOH-2027-043 created | View record |
| Printers requisition | Authorised | TND-MOH-2027-044 created | View record |
| Monitors requisition | Authorised | TND-MOH-2027-045 created | View record |
| Servers requisition | Authorised | TND-MOH-2027-046 created | View record |

Search label **Search Requisition**, blank. State select **All states**, options All states / Submitted to Procurement / Authorised. Footer **Showing 7 of 7 Requisitions**. All View record actions enabled text links. A table supports comparison of authorisation and actual Tender creation across seven records. No chart. Level 1 outstanding authorisation; Level 2 record states and relationships; Level 3 context/definitions. No personal approve action or tracker.

### ANL-DES-05 — Needs

DES-01 View selected **Needs**, A1 context/filters. Replace overview with **2 Needs accepted for planning**, **No outstanding matters recorded in this selection.** Two compact rows **Clinic equipment — Accepted for planning — View record**, **Office furniture — Accepted for planning — View record**. Search **Search Need**, blank; state **All states**, options All states / Accepted for planning; footer **Showing 2 of 2 Needs**. Text links enabled. No claim that acceptance puts either Need in the Active Plan. No chart/table/tracker. Level 1 disposition; Level 2 two records; Level 3 context/definitions.

### ANL-DES-06 — Departmental planning

DES-01 View **Departmental planning**, A1 context/filters. **2 departmental plans accepted**, **No outstanding matters recorded in this selection.** Compact rows **Digital Health departmental plan — Accepted — View record**, **Human Resources Management and Development departmental plan — Accepted — View record**. Search **Search departmental plan**, blank; state **All states**, options All states / Accepted; footer **Showing 2 of 2 departmental plans**. No chart/table/tracker. Level 1 accepted result; Level 2 records; Level 3 context/definitions. Acceptance is departmental submission acceptance, not Annual Plan approval.

### ANL-DES-07 — Annual planning

DES-01 View **Annual planning**, A1 context/filters. **7 Plan items in the Active Plan**, **No outstanding matters recorded in this selection.** Quiet source **Ministry of Health Annual Procurement Plan · Active Version 1**. Seven-row register, columns **Plan item**, **Department**, **Current position**, **Action**:

| Plan item | Department | Current position | Action |
|---|---|---|---|
| Clinic equipment | Digital Health | In the Active Plan | View record |
| IT peripherals | Digital Health; HRMD contributes | In the Active Plan | View record |
| Network switches | Human Resources Management and Development | In the Active Plan | View record |
| Office desks | Human Resources Management and Development | In the Active Plan | View record |
| Printers | Digital Health | In the Active Plan | View record |
| Monitors | Human Resources Management and Development | In the Active Plan | View record |
| Servers | Digital Health | In the Active Plan | View record |

Search **Search Plan item**, blank; no state filter because these records share the operative Active baseline; footer **Showing 7 of 7 Plan items**. All View record actions text/enabled. Table supports finding and comparing seven items with differing lead/contributor attribution. No chart/tracker. Level 1 operative baseline; Level 2 items/departments; Level 3 context/definitions. No candidate or Plan-root count substituted.

### ANL-DES-08 — Peter’s departmental Overview

Inherit DES-01; fixture A2, Dr Peter Kimani, current Directorate of Digital Health and Policy and HRMD HoD responsibilities; HRMD selected locally at 18 June 2027, 10:00 EAT. Scope **Human Resources Management and Development**; Financial year All years; View Overview. Department choices All departments / Digital Health / Human Resources Management and Development. Replace five rows:
- **Needs** / **1 Need accepted for planning** / **No outstanding matters recorded** / View records.
- **Departmental planning** / **1 departmental plan accepted** / **No outstanding matters recorded** / View records.
- **Annual planning** / **4 Plan items in the Active Plan** / **No outstanding matters recorded** / View records.
- **Requisitions** / **4 Requisitions authorised** / **No outstanding matters recorded** / View records.
- **Tender proceedings** / **4 Tenders: 1 in preparation, 1 open for bids, 1 in Evaluation, 1 in Award** / **IT peripherals: warranty requirement needs correction by Brian Wafula. Office desks: committee review is outstanding. Monitors: award notices awaiting delivery.** / View records.
Unit explanation/definitions retained. Context links to Strategy/Budget registers retained as navigation, not unrelated record access. Level 1 scoped position and pending matters. No site-wide total or 044/046. No tracker.

ANL-DES-08B, same A2 with View Tender proceedings: use DES-02 area layout with **4 Tenders**, only outstanding paragraphs for IT peripherals, Office desks and Monitors. Chart **Tender preparation and publication 1**, **Open for bids 1**, **Evaluation 1**, **Award 1**. Four rows 041/042/043/045 with exact DES-02 values; 041 additionally **HRMD contributes · Lead: Digital Health**. Footer Showing 4 of 4 Tenders. Local stage options All stages / Tender preparation and publication / Open for bids / Evaluation / Award. Annual planning A2 variant ANL-DES-08C: DES-07 with **4 Plan items**, only IT peripherals, Network switches, Office desks and Monitors, exact DES-07 row values; source/controls otherwise unchanged; footer **Showing 4 of 4 Plan items**. The count unit never changes from Plan items to Plan roots.

### ANL-DES-09 — no matches / no records

ANL-DES-09A, Charles A1, View Tender proceedings, DES-02 global filters, search **laboratory**, state All stages. Retain whole-area six-Tender summary/chart/outstanding facts; add label **All 6 Tenders in this area** above the summary; replace record rows with **No records match these filters.**, enabled text **Clear search**, footer **0 matching Tenders**. This is a search result, not an empty owner feed. ANL-DES-09B, separate A3 complete successful dataset with no records in any included area: DES-01 header/filters, show **No records are available in this selection.**, enabled Clear filters, context register links retained; omit counts, chart, table and No outstanding claim. No tracker.

### ANL-DES-10 — failures

ANL-DES-10A, Charles A1 with Needs read unavailable: DES-01 overview retains four exact complete rows; Needs row position **Needs could not be loaded.**, Outstanding work **Unavailable**, Action standard button **Try again**. No Needs total or zero. Definitions replace time statement with **The Needs read is unavailable. Other area reads completed at 10:00 EAT.** ANL-DES-10B, all area reads fail: header/filters retained; no update time or context/definitions; **Analytics could not be loaded.**, primary **Try again**. ANL-DES-10C, Tender044 permitted but confirmed Award stage read unavailable: DES-02 six-Tender total retained; chart Award count 1 and **Status unavailable 1**; 044 row position **Status unavailable**, outcome **Could not be loaded**, enabled View record. Replace its outstanding paragraph with **Supply of printers — We could not load the current Award position.** Other rows/paragraphs unchanged. No inferred professional-opinion holder in that row. Each failure is explicit; no tracker.

### ANL-DES-11 — initial loading / no permitted area

ANL-DES-11A, Charles initial read pending: header title/description, **Loading Analytics…**, no counts, filters/options, update time or record actions yet. ANL-DES-11B, Daniel Otieno, limited technical support only, direct Analytics entry: title **Procurement Analytics**, **No Analytics records are available to your responsibilities.**, no protected area list, totals, rows or action. Level 1 read/access explanation only. No next-step/tracker.

## 10A. Static design contract — v0.4

### 10A.1 Prompt assembly, archetype and shared chart rules

Supply KT-STD-001 v1.16 §2 and **this section only** for design generation. All pictured facts, rows, chart values and expanded disclosures are here. §10 is retained history and is not supplied. (v0.5: supply KT-STD-001 v1.17 §2, which contains the Analytics archetype and chart forms. Text in the form “(v0.4 read: …)” or “(v0.5: …)” is retained revision history; do not render it.) (v0.6: supply KT-STD-001 v1.18 §2, which adds KT-STD-001 v1.18 §2.6.11 Visual language and warmth.)

**Archetype: Analytics.** Dominant job: understand how many records are in each position, how long recorded steps and current waits are, and how much value is planned, covered, requested, authorised, awarded or funded, then open an area or record to inspect. Composition, top to bottom: page header; tab row; filter row; area result and summary figures; charts; record register (area tabs only); quiet context links; collapsed definitions. This is a module-specific composition stated as a deliberate departure from the KT-STD-001 v1.16 §2.6.3 archetype list under KT-STD-001 v1.16 §1 item 3; §17.1 names the required standard correction. (v0.5: the departure is withdrawn; Analytics is the KT-STD-001 v1.17 §2.6.3 archetype.) Every page is read-only. No next-step block or journey tracker appears on any Analytics artboard.

**Shared chart rules.** (v0.5: KT-STD-001 v1.17 §2.6.10 now states the shared chart forms and rules and prevails; the rules below remain this module's statement of them.)

1. Use only the chart forms named in each brief: horizontal bar, horizontal segmented bar, vertical grouped bar by month and range strip. No pie, donut, gauge, area chart, trend line, trend arrow, sparkline card or 3D effect.
2. Every bar or segment shows its value as text. A segmented bar has a legend giving each segment's label and value in the stated order. A zero-value segment and its legend entry are omitted unless a brief states otherwise. Colour is never the only carrier of meaning (KT-STD-001 v1.16 §3).
3. Colour by meaning under KT-STD-001 v1.18 §2.6.11 item 1, with values chosen by Claude Design. **Sequential ramp** in one hue, light to dark: waiting bands. **Paired tones**, a strong product hue and its pale tint: Covered and Not yet covered. **One colour family in three tones**, darkest to lightest: Reserved for requisitions, Committed to contracts, Available to reserve. **Categorical set**: Tender stages, Requisition states, Needs and departmental-plan states, and monthly series. **Accent**: the median marker in the time strip, result figures and the selected tab or bar. Status red, amber and green are not used for any category or band. (v0.5 read: Use the existing `--kt-*` neutral and data tokens for categories. Do not use status red, amber or green for categories, because a category is not good or bad. The product accent appears only on the selected tab, a selected stage bar and focused controls.)
4. Monthly charts show twelve month slots labelled `Jul 2026` to `Jun 2027 (to date)` on the horizontal axis. A month with zero shows no bar and no value label.
5. Charts have a light baseline and no heavy gridlines. Axis tick labels may abbreviate millions as `KES 20 m`; value labels never abbreviate.
6. Each chart region sits on its own lightly tinted surface with soft radius and no hard border; the summary strip is one tinted band. Region titles use the ordinary section heading style, preceded by the area icon where the region belongs to one area. (v0.5 read: Chart regions sit on the page sheet without their own bordered card unless the brief says otherwise; a region title in the ordinary section heading style names each chart.) (v0.7: superseded. Chart regions sit on the white sheet without a fill or their own border, each starting with its icon and section heading and separated by spacing and a 1px `--border-color` rule. The summary strip is a row of columns divided by 1px rules, with no fill. Colour appears only in chart data, icon chips and the selected tab or bar.) (v0.8: each summary-strip column follows the HOME-CHG-001 v0.6 §10B.1 summary column: no box, a neutral 3–4 px left rule, the area icon and name as a small heading; five equal columns in one row. Its headline, segmented bar, outstanding line and link stay as stated.)
7. **Area icons** (v0.6), one per area from one outline set chosen by Claude Design, used on the tab, the summary strip column and that area's region titles: Needs — a request or lightbulb concept; Departmental planning — a department list concept; Annual planning — a calendar concept; Requisitions — a document-with-check concept; Tender proceedings — a published-notice concept. No icons in table rows.
8. **Result figures** (v0.6): area counts in the strip, the coverage percentage and the funding registered allocation use a display size with tabular digits; their sentence sits beneath in body size. (v0.8: figures use `--color-figure` `#1b2c68` (KT-STD-001 v1.22 §2.4), as rendered on HOME-DES-21; links stay underlined so figures and links never differ by colour alone.)
9. **Empty, error and access states** (v0.6): ANL-DES-31B, ANL-DES-31D and ANL-DES-31H may carry a small spot illustration above their stated text; the text is unchanged.
10. Subtle transitions of 200 ms or less on tab change and disclosure are permitted; none on charts.
11. **Rendered treatment (v0.8, D-ANL-14).** The waiting-band ramp uses its own hue, never one used by a category in the summary strip. Outstanding-count lines use a neutral icon, not the warning colour, because waiting is not lateness. A waiting time is a small tinted badge (**Waiting 2 days**) followed by **since [day month, hh:mm]** in quiet text; the matter sentence never repeats the instant. Amounts that are not links, such as **not covered** values, use muted text, never the link colour. A segmented bar labels each segment separately, never two values joined by a delimiter. Result-figure blocks such as **Planned value** and **Covered by authorised requisitions** use the summary-column treatment.
12. **Narrow sheet (v0.8).** When the sheet's content width is below 960 px, summary columns wrap to three then two per row, side-by-side chart regions stack in their stated order, and the range strip keeps its value columns, with the chart track shrinking first.

**Shared header, tab row and filter row (all ANL-DES-21 to ANL-DES-30B artboards unless replaced).**

- Header: title **Procurement Analytics**; description **See where procurement work stands, how long key steps take and how much planned value is covered.**; quiet text action **Refresh** at the right; beneath the description, quiet text **Updated 18 June 2027, 10:00 EAT** and scope text **All departments** (or the stated department).
- Tab row, left to right: **Overview**, **Needs**, **Departmental planning**, **Annual planning**, **Requisitions**, **Tender proceedings**. The selected tab is stated per artboard.
- Filter row below the tabs, applying to the whole page: select **Financial year**, options **All years** / **FY 2026/27** / **FY 2027/28**; select **Department**, options **All departments** / **Digital Health** / **Human Resources Management and Development**; standard button **Apply filters**; text action **Clear filters**.
- Bottom of every artboard: quiet links **View Strategy register** and **View Budget & Funding register**; then the collapsed disclosure **How these figures are counted**. (v0.8: superseded. The two register links are removed; Frappe's sidebar provides navigation. The collapsed disclosure remains at the bottom of every artboard.)

**Expanded content of How these figures are counted** (shown expanded only in ANL-DES-21X): **Each area counts its own permitted records once. Financial year follows the record's Planning source, not its creation date. Annual planning counts items in the Active Plan. Versions and contributing departments do not add records. An award decision does not mean notices or contract work are complete. Waiting time runs from when a matter reached its current holder; it is not a judgement that work is late. Time between key steps counts calendar days between recorded events completed in the 12 months to 18 June 2027; these are not statutory periods. Plan coverage uses the Annual Plan's own record of value covered by authorised requisitions. Amounts are in Kenya shillings, and different kinds of amount are never added together. Counts and positions describe current position when loaded. All area reads completed at 10:00 EAT.**

### 10A.2 Shared fixture — outside the artboard

Dataset **A1** is the v0.3 illustrative dataset of §13 with the v0.4 facts below. Actor Charles Mutiso, Head of Procurement Function, site-wide; read instant 18 June 2027, 10:00 EAT; all owner reads complete at 10:00 EAT; window July 2026 to June 2027 (to date). All A1 records are attributed to **FY 2027/28**. Amounts are KES. These are presentation fixtures, not seed facts.

Plan items in Annual Plan P-A, Active Version 1:

| Item | Plan item | Lead department | Planned value | Digital Health allocation | HRMD allocation | Covered value | Approved invitation date |
|---|---|---|---|---|---|---|---|
| I-A | Clinic equipment | Digital Health | 12,000,000 | 12,000,000 | 0 | 0 | No proceeding |
| I-B | IT peripherals | Digital Health | 6,500,000 | 4,000,000 | 2,500,000 | 6,500,000 | 9 Apr 2027 |
| I-C | Network switches | HRMD | 9,000,000 | 0 | 9,000,000 | 8,000,000 | 19 Apr 2027 |
| I-D | Office desks | HRMD | 3,500,000 | 0 | 3,500,000 | 3,500,000 | 9 Apr 2027 |
| I-E | Printers | Digital Health | 5,000,000 | 5,000,000 | 0 | 5,000,000 | 12 Apr 2027 |
| I-F | Monitors | HRMD | 7,500,000 | 0 | 7,500,000 | 7,500,000 | 6 Apr 2027 |
| I-G | Servers | Digital Health | 25,000,000 | 25,000,000 | 0 | 25,000,000 | 5 Apr 2027 |

Totals: planned 68,500,000 (Digital Health 46,000,000; HRMD 22,500,000); covered 55,500,000 (Digital Health 34,000,000; HRMD 21,500,000); not yet covered 13,000,000 (Digital Health 12,000,000; HRMD 1,000,000). I-B's covered value is 4,000,000 on its Digital Health allocation and 2,500,000 on its HRMD allocation.

Requisitions (current Version 1 each):

| Requisition | State | Value | Submitted to Procurement | Authorised | Handoff consumed | Tender |
|---|---|---|---|---|---|---|
| R-A Clinic equipment | Submitted to Procurement | 12,000,000 requested | 16 Jun 2027, 11:00 | Not authorised | Not consumed | None |
| R-B IT peripherals | Authorised | 6,500,000 authorised | 9 Mar 2027, 10:00 | 15 Mar 2027, 11:00 | 16 Mar 2027, 09:00 | 041 |
| R-C Network switches | Authorised | 8,000,000 authorised | 8 Mar 2027, 10:00 | 15 Mar 2027, 11:30 | 19 Mar 2027, 09:00 | 042 |
| R-D Office desks | Authorised | 3,500,000 authorised | 3 Mar 2027, 10:00 | 15 Mar 2027, 12:00 | 18 Mar 2027, 09:00 | 043 |
| R-E Printers | Authorised | 5,000,000 authorised | 2 Mar 2027, 10:00 | 12 Mar 2027, 11:00 | 16 Mar 2027, 10:00 | 044 |
| R-F Monitors | Authorised | 7,500,000 authorised | 4 Mar 2027, 10:00 | 11 Mar 2027, 11:00 | 16 Mar 2027, 11:00 | 045 |
| R-G Servers | Authorised | 25,000,000 authorised | 1 Mar 2027, 10:00 | 15 Mar 2027, 14:00 | 17 Mar 2027, 09:00 | 046 |

R-B has two drawdown lines: Digital Health 4,000,000 and HRMD 2,500,000. Every other Requisition has one drawdown line in its lead department. R-C draws 8,000,000 of its 9,000,000 allocation.

Tenders:

| Tender | Published | Opening complete | Report sent and Award case received | AO decision | Award amount | Cancellation |
|---|---|---|---|---|---|---|
| 041 | Not published | None | None | None | None | None |
| 042 | 14 May 2027, 10:00 | None | None | None | None | None |
| 043 | 16 Apr 2027, 10:00 | 3 Jun 2027, 10:00 | None | None | None | None |
| 044 | 9 Apr 2027, 10:00 | 10 May 2027, 12:00 | 16 Jun 2027, 14:07 | None | None | None |
| 045 | 6 Apr 2027, 10:00 | 7 May 2027, 12:00 | 4 Jun 2027, 15:00 | Award, 17 Jun 2027, 11:00 | 7,185,000 | None |
| 046 | 12 Apr 2027, 10:00 | None | None | None | None | 16 Jun 2027, 12:00 |

Needs N-A and N-B were accepted for planning on 24 Nov 2026 at 11:00 and 14:00. DPP D-A and D-B were accepted on 2 Dec 2026 at 10:00 and 3 Dec 2026 at 10:00.

Outstanding matters:

| Record | Matter | Holder | Since | Waiting days at read |
|---|---|---|---|---|
| R-A | Awaiting authorisation | Charles Mutiso | 16 Jun 2027, 11:00 | 2 |
| 041 | Warranty requirement awaiting correction | Brian Wafula | 16 Jun 2027, 09:00 | 2 |
| 043 | Committee review outstanding | Appointed committee chaired by Grace Wambui | 3 Jun 2027, 10:00 | 15 |
| 044 | Awaiting professional opinion | Charles Mutiso | 16 Jun 2027, 14:07 | 2 |
| 045 | Required bidder notices awaiting delivery | No named holder supplied | 17 Jun 2027, 11:00 | 1 |

No owner overdue fact is recorded.

Budget FY 2027/28, Active Version 1: Registered allocation 150,000,000; Reserved for requisitions 55,500,000; Committed to contracts 0; Available to reserve 94,500,000. No reservation release or conversion event is recorded in A1.

Budget Lines and reservations for FY 2027/28 (v0.5):

| Budget Line | Available to | Registered allocation | Reserved for requisitions | Committed to contracts | Available to reserve |
|---|---|---|---|---|---|
| ICT equipment for Digital Health | Digital Health | 60,000,000 | 9,000,000 | 0 | 51,000,000 |
| Office equipment for Human Resources Management and Development | Human Resources Management and Development | 30,000,000 | 13,500,000 | 0 | 16,500,000 |
| Ministry-wide ICT infrastructure | All departments | 60,000,000 | 33,000,000 | 0 | 27,000,000 |

| Reservation for | Budget Line | Source department | Reserved |
|---|---|---|---|
| R-B Digital Health line | ICT equipment for Digital Health | Digital Health | 4,000,000 |
| R-B HRMD line | Office equipment for Human Resources Management and Development | Human Resources Management and Development | 2,500,000 |
| R-C | Ministry-wide ICT infrastructure | Human Resources Management and Development | 8,000,000 |
| R-D | Office equipment for Human Resources Management and Development | Human Resources Management and Development | 3,500,000 |
| R-E | ICT equipment for Digital Health | Digital Health | 5,000,000 |
| R-F | Office equipment for Human Resources Management and Development | Human Resources Management and Development | 7,500,000 |
| R-G | Ministry-wide ICT infrastructure | Digital Health | 25,000,000 |

Department views for FY 2027/28: Human Resources Management and Development has Registered allocation 30,000,000, Reserved 13,500,000, Committed 0 and Available 16,500,000 on its own line, and Reserved 8,000,000 and Committed 0 on the line available to all departments. R-A has no reservation because it is not authorised.

Derived figures used below, computed under §§5.4–5.5. Days are calendar days.

| Transition | A1 completed | A1 median | A1 shortest | A1 longest | A2 completed | A2 median | A2 shortest | A2 longest |
|---|---|---|---|---|---|---|---|---|
| T1 Requisition submitted to authorised | 6 | 8.5 | 6 | 14 | 4 | 7 | 6 | 12 |
| T2 Requisition authorised to Tender started | 6 | 3.5 | 1 | 5 | 4 | 3.5 | 1 | 5 |
| T3 Tender started to published | 5 | 26 | 21 | 56 | 3 | 29 | 21 | 56 |
| T4 Bid opening complete to evaluation report sent | 2 | 32.5 | 28 | 37 | 1 | 28 | 28 | 28 |
| T5 Evaluation report sent to AO decision recorded | 1 | 13 | 13 | 13 | 1 | 13 | 13 | 13 |

| Plan coverage | Planned | Covered | Not yet covered | Percentage |
|---|---|---|---|---|
| A1, All departments | 68,500,000 | 55,500,000 | 13,000,000 | 81% |
| A1, Digital Health | 46,000,000 | 34,000,000 | 12,000,000 | 74% |
| A2, HRMD | 22,500,000 | 21,500,000 | 1,000,000 | 96% |

| Tender | Days after approved invitation date |
|---|---|
| 042 | 25 |
| 043 | 7 |
| 046 | 7 |
| 045 | 0 |
| 044 | −3 |
| 041 | No date recorded |

**Dataset A2** is v0.3's: Dr Peter Kimani, Head of User Department, with the Directorate and HRMD responsibilities stated in §13, Department filter **Human Resources Management and Development**, same instant and window. A2 contains the HRMD-attributed part of A1. The AWD read for Peter returns the scoped final-decision summary without an award amount, so A2 pictures no award amount. Peter's Analytics scope is not site-wide, so no funding position appears. (v0.5: Peter sees the department view of the funding position when one Financial year is selected, under §5.5 rule 5; ANL-DES-29F pictures it.)

### 10A.3 ANL-DES-21 — Charles's Overview

1. **Identity, archetype and purpose:** ANL-DES-21, Procurement Analytics Overview; Analytics; Charles compares counts, current waits, timing of key steps and Plan coverage across areas and chooses an area to inspect.
2. **Fixture outside the artboard:** A1 (§10A.2); route `/app/analytics`; All years; All departments.
3. **Question and action:** Where does procurement work stand, what is waiting and for how long, how long are key steps taking, and how much planned value is covered? Read-only; tabs and links navigate only.
4. **Priority:** Level 1: area summary strip and Outstanding matters by waiting time. Level 2: Plan coverage and Time between key steps. Level 3: funding message, context links and definitions.
5. **Header:** shared header (§10A.1); scope **All departments**.
6. **Composition, top to bottom:** header; tab row with **Overview** selected; filter row; area summary strip, full width; a two-column row with **Outstanding matters by waiting time** on the left at 60% of the content width and **Plan coverage** on the right; **Time between key steps**, full width; one quiet line for the funding position; context links; collapsed definitions. No record register on Overview. (v0.8: no context links; the funding line is followed directly by the collapsed definitions.)
7. **Controls and content:**
   - **Area summary strip.** One strip with five columns separated by thin dividers, left to right. Each column: unit headline; one horizontal segmented bar with its legend; one outstanding line; one text link.
     - **Needs:** headline **2 Needs**; bar one segment **Accepted for planning 2**; line **No outstanding matters recorded**; link **View Needs**.
     - **Departmental planning:** headline **2 departmental plans**; bar one segment **Accepted 2**; line **No outstanding matters recorded**; link **View departmental planning**.
     - **Annual planning:** headline **7 Plan items in the Active Plan**; bar segments in order **Fully covered 5**, **Partly covered 1**, **Not covered 1**; line **No outstanding matters recorded**; link **View annual planning**.
     - **Requisitions:** headline **7 Requisitions**; bar segments **Submitted to Procurement 1**, **Authorised 6**; line **1 outstanding matter**; link **View Requisitions**.
     - **Tender proceedings:** headline **6 Tenders**; bar segments **Preparation 1**, **Open 1**, **Evaluation 1**, **Award 2**, **Closed 1**; line **4 outstanding matters**; link **View Tender proceedings**. These short legend labels stand for the §5.2 buckets Tender preparation and publication, Open for bids, Evaluation, Award and Closed.
     - Beneath the strip, quiet text: **These counts describe different records and are not added together.**
   - **Outstanding matters by waiting time.** Horizontal segmented bars, one row per area that has outstanding matters, segments in band order **0–7 days**, **8–30 days**, **31–90 days**, **Over 90 days**, with a shared legend above the rows. Rows: **Requisitions** with **0–7 days 1**; **Tender proceedings** with **0–7 days 3** and **8–30 days 1**. No total at the bar end; the summary strip carries the counts. (v0.7 read: Rows: **Requisitions** with **0–7 days 1** and total **1** at the bar end; **Tender proceedings** with **0–7 days 3**, **8–30 days 1** and total **4**.) Below the rows: **Needs, departmental planning and annual planning: no outstanding matters recorded.** Caption: **Days since each matter reached its current holder.** (v0.5 read: Caption: **Waiting time is measured from when each matter reached its current holder. It is not a judgement that work is late.** The second sentence remains in How these figures are counted.)
   - **Plan coverage.** Result line **81% of planned value is covered by authorised requisitions**; secondary line **Planned value KES 68,500,000 in the Active Plan**. One horizontal segmented bar: **Covered by authorised requisitions KES 55,500,000**, then **Not yet covered KES 13,000,000**. Beneath: **5 Plan items fully covered, 1 partly covered, 1 not covered.** Text link **View annual planning**.
   - **Time between key steps.** A range strip with value columns. Columns left to right: **Step**; chart; **Completed**; **Median**; **Shortest**; **Longest**. The chart draws a line from shortest to longest with a marker at the median on a shared axis 0 to 60 days, ticks every 10 days. Rows, top to bottom:
     - **Requisition submitted to authorised** / **6** / **8.5 days** / **6 days** / **14 days**
     - **Requisition authorised to Tender started** / **6** / **3.5 days** / **1 day** / **5 days**
     - **Tender started to published** / **5** / **26 days** / **21 days** / **56 days**
     - **Bid opening complete to evaluation report sent** / **2** / **32.5 days** / **28 days** / **37 days**
     - **Evaluation report sent to AO decision recorded** / **1** / **13 days** / **13 days** / **13 days**
     - Caption: **Calendar days, last 12 months.** (v0.5 read: Caption: **Calendar days between recorded events completed in the 12 months to 18 June 2027. These are not statutory periods.** Both sentences remain in How these figures are counted.)
   - **Funding line:** quiet text **Choose a financial year to see its funding position.**
8. **Actions and visible state:** **Refresh** quiet text action; six tabs, Overview selected; **Apply filters** standard button; **Clear filters** text action; five strip links and **View annual planning** as enabled text links; two context links; disclosure toggle. No search, paging, export, download, assign, approve or chart interaction. (v0.8: the two context links are removed.)
9. **Supporting detail:** **How these figures are counted**, collapsed, with the §10A.1 content.
10. **Variants:** ANL-DES-21X is ANL-DES-21 with the disclosure expanded. ANL-DES-22 to ANL-DES-31H inherit this brief with the stated replacements.
11. **Comprehension:** the first view shows each area's count and state split, that five matters are waiting and one of them for 8–30 days, that 81% of planned value is covered, and how long each key step took. Different units are not added. Waiting is not lateness. The page is read-only.
12. **Next step and journey:** neither component appears.

### 10A.4 ANL-DES-22 — Charles's Tender proceedings tab

Inherit ANL-DES-21 header, filters, context links and definitions. Tab **Tender proceedings** selected; route `/app/analytics/tender-proceedings`. Priority: Level 1 area result and outstanding work; Level 2 stage chart, monthly chart, time between key steps and register; Level 3 context and definitions. Composition top to bottom:

1. **Area result:** **6 Tenders**.
2. **Outstanding work.** Compact rows, two columns: matter text, then waiting time right-aligned. Order: (v0.8: each row is the record title in bold, the matter sentence without its instant, then the badge **Waiting n days** and quiet **since [day month, hh:mm]**, under §10A.1 rule 11.)
   - **Supply of IT peripherals** — **State the warranty period required from suppliers. Awaiting correction by Brian Wafula.** — badge **Waiting 2 days** — quiet **since 16 June, 09:00** (v0.7 read: **Supply of IT peripherals — State the warranty period required from suppliers. Awaiting correction by Brian Wafula since 16 June 2027, 09:00 EAT.** / **Waiting 2 days**)
   - **Supply of office desks** — **Automatic checks complete; committee review outstanding. Grace Wambui chairs the appointed committee.** — badge **Waiting 15 days** — quiet **since 3 June, 10:00** (v0.7 read: **Supply of office desks — Automatic checks complete; committee review outstanding. Grace Wambui chairs the appointed committee. Waiting since 3 June 2027, 10:00 EAT.** / **Waiting 15 days**)
   - **Supply of printers** — **Awaiting professional opinion by Charles Mutiso.** — badge **Waiting 2 days** — quiet **since 16 June, 14:07** (v0.7 read: **Supply of printers — Awaiting professional opinion by Charles Mutiso since 16 June 2027, 14:07 EAT.** / **Waiting 2 days**)
   - **Supply of monitors** — **Award decision recorded. Required bidder notices are awaiting delivery.** — badge **Waiting 1 day** — quiet **since 17 June, 11:00** (v0.7 read: **Supply of monitors — Award decision recorded. Required bidder notices are awaiting delivery. Waiting since 17 June 2027, 11:00 EAT.** / **Waiting 1 day**)
3. **Two charts side by side.** Left, **Tenders by stage**: horizontal bars sized by count, with a value column at the right headed **Authorised requisition value**. Rows: **Tender preparation and publication** / **1** / **KES 6,500,000**; **Open for bids** / **1** / **KES 8,000,000**; **Evaluation** / **1** / **KES 3,500,000**; **Award** / **2** / **KES 12,500,000**; **Closed** / **1** / **KES 25,000,000**. Beneath: **1 AO award decision recorded. Award amount KES 7,185,000.** Right, **Recorded each month**: vertical grouped bars with legend **Published**, **Cancelled**, **AO award decisions**. Values: Apr 2027 **Published 4**; May 2027 **Published 1**; Jun 2027 (to date) **Cancelled 1** and **AO award decisions 1**. All other months zero.
4. **Time between key steps:** the ANL-DES-21 range strip with rows **Requisition authorised to Tender started**, **Tender started to published**, **Bid opening complete to evaluation report sent** and **Evaluation report sent to AO decision recorded**, values as ANL-DES-21, same caption.
5. **Record register.** Above it: search input **Search Tender or reference**, blank; select **All stages**, options All stages / Tender preparation and publication / Open for bids / Evaluation / Award / Closed. Columns **Tender**, **Current position**, **Authorised requisition value**, **Recorded AO outcome**, **Action**. Rows:

| Tender / secondary reference | Current position | Authorised requisition value | Recorded AO outcome | Action |
|---|---|---|---|---|
| Supply of IT peripherals / TND-MOH-2027-041 | Tender preparation — warranty requirement returned for correction | KES 6,500,000 | No AO award decision recorded | View record |
| Supply of network switches / TND-MOH-2027-042 | Open for bids | KES 8,000,000 | No AO award decision recorded | View record |
| Supply of office desks / TND-MOH-2027-043 | Evaluation — automatic checks complete; committee review outstanding | KES 3,500,000 | No AO award decision recorded | View record |
| Supply of printers / TND-MOH-2027-044 | Award — professional opinion outstanding | KES 5,000,000 | No AO award decision recorded | View record |
| Supply of monitors / TND-MOH-2027-045 | Award — required bidder notices awaiting delivery | KES 7,500,000 | Award decision recorded 17 June 2027, 11:00 EAT; secondary line Award amount KES 7,185,000 | View record |
| Supply of servers / TND-MOH-2027-046 | Closed — cancelled; cancellation compliance evidence complete | KES 25,000,000 | Cancellation recorded 16 June 2027, 12:00 EAT | View record |

Footer **Showing 6 of 6 Tenders**; no paging buttons. All **View record** actions are enabled text links. No chart is collapsed. 045 remains in Award despite its decision. No next-step block or tracker.

### 10A.5 ANL-DES-23 — Award stage selected

ANL-DES-22 with the stage select at **Award** and the **Award** bar selected with the accent; route `/app/analytics/tender-proceedings?state=award`. Outstanding work, both charts and the time strip are unchanged and labelled **All 6 Tenders in this area** above the stage chart. The register shows only the 044 and 045 rows exactly as in ANL-DES-22. Footer **Showing 2 of 2 matching Tenders**; enabled text **Clear stage filter** beside the select. No duplicate chart or new total.

### 10A.6 ANL-DES-24 — Requisitions tab

ANL-DES-21 shared parts; tab **Requisitions**; route `/app/analytics/requisitions`. Priority: Level 1 area result and outstanding authorisation; Level 2 charts, time strip and register; Level 3 context and definitions. Top to bottom:

1. **Area result:** **7 Requisitions**.
2. **Outstanding work:** one compact row **Clinic equipment requisition** — **Awaiting authorisation by Charles Mutiso.** — badge **Waiting 2 days** — quiet **since 16 June, 11:00**. (v0.7 read: **Outstanding work:** one compact row **Clinic equipment requisition — Awaiting authorisation by Charles Mutiso since 16 June 2027, 11:00 EAT.** / **Waiting 2 days**.)
3. **Two charts side by side.** Left, **Requisitions by current state**: horizontal bars sized by count with value column **Requisition value**. Rows **Submitted to Procurement** / **1** / **KES 12,000,000 requested**; **Authorised** / **6** / **KES 55,500,000 authorised**. Right, **Recorded each month**: grouped bars, legend **Submitted to Procurement**, **Authorised**. Values Mar 2027 **Submitted to Procurement 6** and **Authorised 6**; Jun 2027 (to date) **Submitted to Procurement 1**. Other months zero.
4. **Time between key steps:** rows **Requisition submitted to authorised** and **Requisition authorised to Tender started**, values as ANL-DES-21, same caption.
5. **Record register.** Search **Search Requisition**, blank; select **All states**, options All states / Submitted to Procurement / Authorised. Columns **Requisition**, **Current position**, **Requisition value**, **Tender relationship**, **Action**:

| Requisition | Current position | Requisition value | Tender relationship | Action |
|---|---|---|---|---|
| Clinic equipment requisition | Submitted to Procurement | KES 12,000,000 requested | No Tender created | View record |
| IT peripherals requisition | Authorised | KES 6,500,000 authorised | TND-MOH-2027-041 created | View record |
| Network switches requisition | Authorised | KES 8,000,000 authorised | TND-MOH-2027-042 created | View record |
| Office desks requisition | Authorised | KES 3,500,000 authorised | TND-MOH-2027-043 created | View record |
| Printers requisition | Authorised | KES 5,000,000 authorised | TND-MOH-2027-044 created | View record |
| Monitors requisition | Authorised | KES 7,500,000 authorised | TND-MOH-2027-045 created | View record |
| Servers requisition | Authorised | KES 25,000,000 authorised | TND-MOH-2027-046 created | View record |

Footer **Showing 7 of 7 Requisitions**. All **View record** links enabled. No approve action, next-step block or tracker.

### 10A.7 ANL-DES-25 — Annual planning tab

ANL-DES-21 shared parts; tab **Annual planning**; route `/app/analytics/annual-planning`. Priority: Level 1 area result, planned value and coverage; Level 2 coverage charts, invitation timing and register; Level 3 source line, context and definitions. Top to bottom:

1. **Area result:** **7 Plan items in the Active Plan**; secondary **No outstanding matters recorded in this selection.**; quiet source **Ministry of Health Annual Procurement Plan, Active Version 1**.
2. **Result figures**, one line of two labelled figures: **Planned value** **KES 68,500,000**; **Covered by authorised requisitions** **KES 55,500,000 (81%)**.
3. **Coverage by Plan item:** horizontal segmented bars, one per Plan item, ordered by planned value from largest; segments **Covered** then **Not yet covered**; value text at each segment. Rows: **Servers** Covered **KES 25,000,000**; **Clinic equipment** Not yet covered **KES 12,000,000**; **Network switches** Covered **KES 8,000,000**, Not yet covered **KES 1,000,000**; **Monitors** Covered **KES 7,500,000**; **IT peripherals** Covered **KES 6,500,000**; **Printers** Covered **KES 5,000,000**; **Office desks** Covered **KES 3,500,000**.
4. **Two regions side by side.** Left, **Coverage by department**: segmented bars **Digital Health** Covered **KES 34,000,000**, Not yet covered **KES 12,000,000**, end label **74%**; **Human Resources Management and Development** Covered **KES 21,500,000**, Not yet covered **KES 1,000,000**, end label **96%**. Caption: **IT peripherals is shared: KES 4,000,000 is attributed to Digital Health and KES 2,500,000 to Human Resources Management and Development.** Right, **Tender invitation timing**: horizontal bars from a zero line, later to the right and earlier to the left, value label on each bar. Rows: **Network switches** **25 days after approved date**; **Office desks** **7 days after approved date**; **Servers** **7 days after approved date**; **Monitors** **On the approved date**; **Printers** **3 days before approved date**; **IT peripherals** **No date recorded**, with no bar. Caption: **Actual invitation date compared with the date approved in the Active Plan.**
5. **Record register.** Search **Search Plan item**, blank; no state filter. Columns **Plan item**, **Department**, **Planned value**, **Covered by authorised requisitions**, **Action**:

| Plan item | Department | Planned value | Covered by authorised requisitions | Action |
|---|---|---|---|---|
| Clinic equipment | Digital Health | KES 12,000,000 | KES 0 | View record |
| IT peripherals | Digital Health; HRMD contributes | KES 6,500,000 | KES 6,500,000 | View record |
| Network switches | Human Resources Management and Development | KES 9,000,000 | KES 8,000,000 | View record |
| Office desks | Human Resources Management and Development | KES 3,500,000 | KES 3,500,000 | View record |
| Printers | Digital Health | KES 5,000,000 | KES 5,000,000 | View record |
| Monitors | Human Resources Management and Development | KES 7,500,000 | KES 7,500,000 | View record |
| Servers | Digital Health | KES 25,000,000 | KES 25,000,000 | View record |

Footer **Showing 7 of 7 Plan items**. All **View record** links enabled. No candidate or Plan-root count is substituted. No next-step block or tracker.

### 10A.8 ANL-DES-26 — Needs tab and ANL-DES-27 — Departmental planning tab

**ANL-DES-26.** ANL-DES-21 shared parts; tab **Needs**; route `/app/analytics/needs`. Area result **2 Needs accepted for planning**; secondary **No outstanding matters recorded in this selection.** Chart **Accepted for planning each month**: vertical bars, one series, Nov 2026 **2**, other months zero. Compact rows, no table: **Clinic equipment — Accepted for planning — View record**; **Office furniture — Accepted for planning — View record**. Search **Search Need**, blank; select **All states**, options All states / Accepted for planning; footer **Showing 2 of 2 Needs**. Links enabled. No claim that acceptance puts either Need in the Active Plan. Level 1 disposition; Level 2 chart and records; Level 3 context and definitions.

**ANL-DES-27.** Tab **Departmental planning**; route `/app/analytics/departmental-planning`. Area result **2 departmental plans accepted**; secondary **No outstanding matters recorded in this selection.** Chart **Departmental plans accepted each month**: Dec 2026 **2**, other months zero. Compact rows: **Digital Health departmental plan — Accepted — View record**; **Human Resources Management and Development departmental plan — Accepted — View record**. Search **Search departmental plan**, blank; select **All states**, options All states / Accepted; footer **Showing 2 of 2 departmental plans**. Acceptance is departmental submission acceptance, not Annual Plan approval.

### 10A.9 ANL-DES-28 — Overview with FY 2027/28 selected

ANL-DES-21 with Financial year **FY 2027/28** applied; route `/app/analytics?fy={FY 2027/28 ID}`. Every count, chart and figure is unchanged because every A1 record is attributed to FY 2027/28. The funding line is replaced by the region **Funding position**, placed after Time between key steps: (v0.8: ANL-DES-28 pictures Amina Hassan, Accounting Officer, site-wide, at the same instant, instead of Charles Mutiso. Every figure is identical, because both have site-wide Analytics scope, and the funding position appears under §5.5 rule 5 for the Accounting Officer.)

- Secondary line **Ministry of Health procurement budget FY 2027/28**; quiet text **Current version 1**.
- Result line **Registered allocation KES 150,000,000**.
- One horizontal segmented bar, segments in order **Reserved for requisitions KES 55,500,000**, **Committed to contracts KES 0**, **Available to reserve KES 94,500,000**. The zero segment has no width; its legend entry remains.
- Caption: **Available to reserve is not a cash balance. Committed to contracts is Budget's record of contract commitments; none is recorded.**

The fixture pictures a permitted BUD funding-position read for Charles; §17.1 records that this must be confirmed before design approval. (v0.5: confirmed by D-ANL-07; Head of Procurement Function is in the whole-Budget audience.)

### 10A.10 ANL-DES-29, ANL-DES-30 and ANL-DES-30B — Peter's department views

**ANL-DES-29 — Peter's Overview.** ANL-DES-21 with fixture A2; Department **Human Resources Management and Development** applied; scope text **Human Resources Management and Development**; route `/app/analytics?dept={HRMD ID}`. Replacements:
- Strip: **1 Need** / **Accepted for planning 1** / **No outstanding matters recorded**; **1 departmental plan** / **Accepted 1** / **No outstanding matters recorded**; **4 Plan items in the Active Plan** / **Fully covered 3**, **Partly covered 1** / **No outstanding matters recorded**; **4 Requisitions** / **Authorised 4** / **No outstanding matters recorded**; **4 Tenders** / **Preparation 1**, **Open 1**, **Evaluation 1**, **Award 1** / **3 outstanding matters**.
- Outstanding matters by waiting time: one row **Tender proceedings** with **0–7 days 2**, **8–30 days 1**, no bar-end total (v0.7 read: **8–30 days 1**, total **3**); beneath **Needs, departmental planning, annual planning and requisitions: no outstanding matters recorded.**
- Plan coverage: **96% of planned value is covered by authorised requisitions**; **Planned value KES 22,500,000 in the Active Plan**; segments **Covered by authorised requisitions KES 21,500,000**, **Not yet covered KES 1,000,000**; **3 Plan items fully covered, 1 partly covered, 0 not covered.**
- Time between key steps rows, in ANL-DES-21 order, with A2 values: **4** / **7 days** / **6 days** / **12 days**; **4** / **3.5 days** / **1 day** / **5 days**; **3** / **29 days** / **21 days** / **56 days**; **1** / **28 days** / **28 days** / **28 days**; **1** / **13 days** / **13 days** / **13 days**.
- Funding line: **Choose a financial year to see its funding position.** (v0.4 read: Funding line: **Funding position is shown only for a site-wide view with All departments selected.**)
- No site-wide total, 044 or 046 appears.

**ANL-DES-29F — Peter's Overview with FY 2027/28 selected (v0.5).** ANL-DES-29 with Financial year **FY 2027/28** applied; route `/app/analytics?fy={FY 2027/28 ID}&dept={HRMD ID}`. Every count, chart and figure is unchanged. The funding line is replaced by the region **Funding position**, placed after Time between key steps:

- Secondary line **Ministry of Health procurement budget FY 2027/28**; quiet text **Current version 1**; scope text **Human Resources Management and Development**.
- Subheading **Budget lines available to Human Resources Management and Development**; result line **Registered allocation KES 30,000,000**; one horizontal segmented bar, segments in order **Reserved for requisitions KES 13,500,000**, **Committed to contracts KES 0**, **Available to reserve KES 16,500,000**. The zero segment has no width; its legend entry remains.
- Subheading **Budget lines available to all departments**; two labelled figures **Reserved for this department's requisitions** **KES 8,000,000** and **Committed to contracts for this department** **KES 0**. No bar, allocation or available amount.
- Caption: **Budget lines available to all departments are shared, so their allocation and available amount are not divided by department. Available to reserve is not a cash balance.**

**ANL-DES-30 — Peter's Tender proceedings tab.** ANL-DES-22 with A2. Area result **4 Tenders**. Outstanding work rows for IT peripherals (**Waiting 2 days**), Office desks (**Waiting 15 days**) and Monitors (**Waiting 1 day**) with ANL-DES-22 text. Tenders by stage: **Tender preparation and publication** / **1** / **KES 2,500,000**; **Open for bids** / **1** / **KES 8,000,000**; **Evaluation** / **1** / **KES 3,500,000**; **Award** / **1** / **KES 7,500,000**; no award amount sentence. Recorded each month: Apr 2027 **Published 2**; May 2027 **Published 1**; Jun 2027 (to date) **AO award decisions 1**. Time strip rows T2 to T5 with A2 values. Register rows 041, 042, 043 and 045 with ANL-DES-22 text except: 041 value **KES 2,500,000** with secondary **HRMD share of KES 6,500,000** and secondary position line **HRMD contributes; Lead: Digital Health**; 045 Recorded AO outcome **Award decision recorded 17 June 2027, 11:00 EAT** with no amount line. Footer **Showing 4 of 4 Tenders**. Stage options All stages / Tender preparation and publication / Open for bids / Evaluation / Award. (v0.8: outstanding rows use the ANL-DES-22 v0.8 row form.)

**ANL-DES-30B — Peter's Annual planning tab.** ANL-DES-25 with A2. Area result **4 Plan items in the Active Plan**. Result figures **Planned value KES 22,500,000**; **Covered by authorised requisitions KES 21,500,000 (96%)**. Coverage by Plan item rows: **Network switches** Covered **KES 8,000,000**, Not yet covered **KES 1,000,000**; **Monitors** Covered **KES 7,500,000**; **Office desks** Covered **KES 3,500,000**; **IT peripherals** Covered **KES 2,500,000** with label **HRMD share**. Coverage by department: one row **Human Resources Management and Development**, Covered **KES 21,500,000**, Not yet covered **KES 1,000,000**, **96%**; no shared-item caption. Tender invitation timing rows: **Network switches** **25 days after approved date**; **Office desks** **7 days after approved date**; **Monitors** **On the approved date**; **IT peripherals** **No date recorded**. Register rows IT peripherals, Network switches, Office desks and Monitors; IT peripherals Planned value **KES 2,500,000** with secondary **HRMD share of KES 6,500,000** and Covered **KES 2,500,000**; others as ANL-DES-25. Footer **Showing 4 of 4 Plan items**. The count unit never changes from Plan items to Plan roots.

### 10A.11 ANL-DES-31 — Search, empty, failure, loading and access variants

- **ANL-DES-31A — no search match.** ANL-DES-22 with search **laboratory** and stage **All stages**. Outstanding work, both charts and the time strip remain, with label **All 6 Tenders in this area** above the stage chart. The register rows are replaced by **No records match these filters.** with enabled text **Clear search**; footer **0 matching Tenders**. This is a search result, not an empty owner feed.
- **ANL-DES-31B — no records in the selection.** Separate complete dataset A3 with no records in any included area. ANL-DES-21 header, tabs and filters; the strip, charts and time strip are omitted; one line **No records are available in this selection.** with enabled text **Clear filters**; context links retained. No count, chart, zero coverage or No outstanding claim. (v0.8: the context links are removed, so only Clear filters remains.)
- **ANL-DES-31C — one area unavailable.** ANL-DES-21 with the Needs read unavailable. The Needs strip column shows **Needs could not be loaded.** and a standard button **Try again** in place of headline, bar, outstanding line and link. The other four columns, both charts and the time strip are unchanged. The definitions end **The Needs read is unavailable. Other area reads completed at 10:00 EAT.** instead of the last sentence.
- **ANL-DES-31D — all reads failed.** Header, tabs and filters only; no update time, strip, charts, context links or definitions; one line **Analytics could not be loaded.** and primary button **Try again**.
- **ANL-DES-31E — one measure unavailable.** ANL-DES-21 with Planning's coverage read unavailable. The Plan coverage region shows **Plan coverage could not be loaded.** and standard button **Try again**; no percentage, bar or item sentence. The Annual planning strip column keeps **7 Plan items in the Active Plan** and **No outstanding matters recorded**; its bar is replaced by quiet text **Coverage unavailable**. Everything else unchanged.
- **ANL-DES-31F — one Tender's stage unavailable.** ANL-DES-22 with 044's Award stage read unavailable. Area result **6 Tenders** retained. Tenders by stage: **Award** **1** **KES 7,500,000**, and an added last row **Status unavailable** **1** **KES 5,000,000**. The 044 register row: Current position **Status unavailable**; Recorded AO outcome **Could not be loaded**; value **KES 5,000,000**; **View record** enabled. Its outstanding row becomes **Supply of printers — We could not load the current Award position.** with no waiting time. Time strip row T5 unchanged. Other rows unchanged.
- **ANL-DES-31G — loading.** Header title and description, tabs and the line **Loading Analytics…**; no counts, filter values, update time, charts or record actions.
- **ANL-DES-31H — no permitted area.** Nadia Kamau, release operator, direct entry to `/app/analytics`. Title **Procurement Analytics**; one line **No Analytics records are available to your responsibilities.**; no tabs, area list, totals, charts, rows or actions. This retains v0.3 ANL-DES-11B content with a different actor. (v0.4 read: **ANL-DES-31H — no permitted area.** Daniel Otieno, direct entry to `/app/analytics`. Title **Procurement Analytics**; one line **No Analytics records are available to your responsibilities.**; no tabs, area list, totals, charts, rows or actions. This retains v0.3 ANL-DES-11B; §17.1 records an unresolved conflict with KT-STD-001 v1.16 §8.3 and KT-STD-001 v1.16 §3A.6.)
- **ANL-DES-31J — Technical Operator (v0.5).** Daniel Otieno, Technical Operator, site-wide read-only under D-ANL-10; fixture A1; route `/app/analytics`. Content exactly as ANL-DES-21. Refresh, tabs, filters, strip links, context links and the disclosure are the only controls; no business action exists on any Analytics artboard.

### 10A.12 Design inventory

| Artboard | Tab | Actor and fixture | Based on |
|---|---|---|---|
| ANL-DES-21 | Overview | Charles, A1 | Complete brief |
| ANL-DES-21X | Overview | Charles, A1 | ANL-DES-21, definitions expanded |
| ANL-DES-22 | Tender proceedings | Charles, A1 | ANL-DES-21 |
| ANL-DES-23 | Tender proceedings, Award | Charles, A1 | ANL-DES-22 |
| ANL-DES-24 | Requisitions | Charles, A1 | ANL-DES-21 |
| ANL-DES-25 | Annual planning | Charles, A1 | ANL-DES-21 |
| ANL-DES-26 | Needs | Charles, A1 | ANL-DES-21 |
| ANL-DES-27 | Departmental planning | Charles, A1 | ANL-DES-21 |
| ANL-DES-28 | Overview, FY 2027/28 | Charles, A1 | ANL-DES-21 (v0.8: actor Amina Hassan, Accounting Officer.) |
| ANL-DES-29 | Overview, HRMD | Peter, A2 | ANL-DES-21 |
| ANL-DES-30 | Tender proceedings, HRMD | Peter, A2 | ANL-DES-22 |
| ANL-DES-30B | Annual planning, HRMD | Peter, A2 | ANL-DES-25 |
| ANL-DES-31A to ANL-DES-31H | As stated | As stated | As stated (v0.5: ANL-DES-31H actor is Nadia Kamau.) |
| ANL-DES-29F | Overview, HRMD, FY 2027/28 | Peter, A2 | ANL-DES-29 |
| ANL-DES-31J | Overview | Daniel Otieno, A1 | ANL-DES-21 |

Every artboard is 1440 × 1024 under KT-STD-001 v1.16 §2.2. The first view of ANL-DES-21 must show the strip, both Level 1 and Level 2 chart regions and at least the first three time-strip rows. (v0.8: the first view of ANL-DES-21 must show the header, filters, summary strip and both chart regions; Time between key steps may begin at the fold, as in the accepted render.)


## 11. Functional interaction requirements — excluded from design prompts

| Control | Exact effect / destination |
|---|---|
| View selector / View records | Select named area and GetProcurementAnalytics area read; clear old area search/state. No record creation or scope change. |
| Financial year / Department / Apply filters | Apply validated owner-data selection to overview and selected area; re-read current permissions and reset paging. |
| Clear filters | All years and permitted All departments; clear local search/state; retain chosen area. No global saved context. |
| Search | Enter submits the selected area’s record search through the scoped adapter; result count matches filtered set; whole-area summary/chart unchanged. |
| Stage bar / local state / Clear stage filter | Same record filter; chart and whole-area summary remain unfiltered and labelled. Keyboard/visible selection agrees. |
| Clear search | Remove search only, retain year/department/state, return matching record results. |
| View record | §9 exact owner route for row identity/version; fresh owner permission read. A1 Requisition authorisation remains in owner module, not Analytics. |
| View Strategy register / View Budget & Funding register | Named registers `/app/strategy` and `/app/budget`; no guessed applicable record or confidential auto-selection. (v0.8: removed from Analytics.) |
| How these figures are counted | Toggle supplied definitions; no calculation or query change. |
| Refresh / Try again | Reread all selected applicable areas or the failed area. Clear stale affected facts rather than label failed data current. |
| Previous/Next on more than ten area results | Cursor read of same owner revision set; scoped matching total does not change with page size. No controls in the pictured short datasets. |
| v0.4: tab | Pushes the §9.1 route for that tab, keeping applied `fy` and `dept` and dropping `state`, search and cursor; then the GetProcurementAnalytics tab read. Replaces the v0.3 View selector. Navigation only. |
| v0.4: Apply filters / Clear filters | As v0.3, and pushes the §9.1 route with the applied `fy` and `dept`; Clear removes both parameters and `state` and keeps the tab. |
| v0.4: stage or state select / Clear stage filter | As v0.3, and pushes or removes `state` in the route. Measures and charts do not change. |
| v0.4: summary strip links and View annual planning | Push the named tab route with the current `fy` and `dept`. |
| v0.4: Try again in one region | Rereads only the measures of that region; other regions keep their values and read times. |
| v0.4: browser Back, refresh, opened link | Resolves the actor's verdict and rereads the route's tab and filters; an invalid or unpermitted value shows the §8 filter message. |
| v0.4: charts | Not interactive in this release, except the stage bar's selected state that mirrors the stage select. Every chart exposes its values as an accessible table to assistive technology, in the visual order, without a visible toggle. |

## 13. Seed contract and actor/state conformance

A1/A2/A3 are **illustrative design datasets**, not installed records. Shared actors follow KT-STD §8; Peter’s Directorate/HRMD authority follows approved SEED-OPS v1.22 decision D4. No new actor or automatic committee membership. The same titles do not prove lineage; each actual relationship must be recorded through owner commands.

A1 contains two accepted Need roots, two accepted DPP roots without candidates, one Active Annual Plan with seven stable items and seven Requisition roots exactly as pictured in DES-04/07 (Clinic equipment submitted to Procurement; the other six authorised with confirmed TPR consumption), and six Tender roots pictured in §10. 041 has HRMD contributor and Digital Health lead; 042/043/045 lead HRMD; 044/046 lead Digital Health. All five units are complete; Needs/Planning have no owner outstanding matters in this isolated dataset. 043 EVL intake and committee appointment are confirmed, automatic checks complete and committee review outstanding; Grace Wambui is its chair with eligible members Peter Mugo and Ruth Achieng; its administrative work is shown on its row. 044 exact report is delivered and AWD receipt creates the linked opinion task. 045 award decision retains unfinished required notices. 046 cancellation compliance evidence is complete.

**Explicit lineage:** each of the seven Plan items supplies one like-named Requisition. The six authorised Requisitions supply Tenders 041–046 in the exact one-to-one pairs in DES-04. Clinic equipment has no Tender. The two DPPs contain the required source entries for these seven items. The two optional Needs supply Clinic equipment (Digital Health) and Office desks (HRMD); remaining sources are direct departmental requirements. IT peripherals is the one combined Digital Health/HRMD item, and its exact Requisition/Tender retain that contributor. No six-Tender dataset is presented with only two consumed Requisitions. Each Requisition's quantities/values must fit its own Plan allowance at execution; no amounts are authored for display. (v0.4: §13.1 and §10A.2 now author illustrative display amounts and instants for A1 and A2; they remain design-only and must still fit owner allowances, budget lines and fixture windows at execution.)

**Selection consistency:** no root-creation-date filter. Fiscal-year IDs and bounds come from actual owner records/native configuration. Do not derive bounds from “2027” in an example Tender reference. Existing source-pack FY/date mismatches are not repaired by this Analytics fixture. All years permits cross-period display, but before executing each business fixture its own FY and dates must satisfy owner checks. Generate records and retain returned references/versions for screenshot binding; do not make false installed-ID claims.

| Chronological path / actor / source | Read/event and consumer | Guard/failure / next holder / clearing / disclosure |
|---|---|---|
| Accepted Need / Charles or Peter / A1–A2 | NDS scoped disposition read, no event | Acceptance not Active Plan usage; exact permitted revision only. |
| DPP accepted → Active APP / A1–A2 | PLN accepted and Active pointer reads | Candidate changes do not replace baseline; HoD counts relevant items once. |
| Submitted REQ → authorisation/consumption / A1 | REQ workspace/current/handoff read | Charles authorisation is owner work; authorisation/consumption remain distinct; Analytics clears neither. |
| Tender returned / Brian holder / A1 | TPR return fact and safe reason | Warranty requirement correction stays visible; resubmission changes owner work. |
| Completed nonempty Opening → EVL intake / A1 | BOP receipt → EVL safe administrative read | Checks automatic; committee holds outstanding review. No new receipt/start approval. |
| Signed report → AWD receipt / A1 | EVL delivery → linked opinion task | Charles prepares opinion; no duplicate review acknowledgement. HoD summary only. |
| AO awards → notices incomplete / A1 | AWD authority/cycle read | Award bucket retains outstanding notices; decision alone is not completion. |
| Cancelled → compliance complete / A1 | TPR terminal outcome/evidence | No current action; retained earlier facts are history; no fabricated evaluation. |
| Empty Opening / negative A4 | Verified BOP empty → EVL No evaluation required | Closed — no bids; no report, signature or Award case. |
| No award / correction / negative A5 | AWD exact current cycle/issue read | Closed outcome with explicit follow-up; reconsideration never deletes previous decision. |
| Provider unavailable / A1 variant | Typed safe read; no event | Identity/stage completeness separate; denied existence remains masked. |
| Actor scope expires / negative A6 | AUTH/owner re-read | No stale count/title; link checks repeat. |

### 13.1 v0.4 illustrative amounts, instants and actor/state conformance

§10A.2 is the single statement of the v0.4 amounts, instants, Budget position and derived figures for A1 and A2. They are illustrative design facts, not installed records or seed values. The instants fall inside KT-STD-001 v1.16 §8.4A windows for Needs (24 Nov 2026), Planning (24 Nov to 20 Dec 2026) and Requisition and Tender Preparation (1 Mar to 15 May 2027), and later Opening, Evaluation and Award facts follow v0.3's 16–18 June 2027 events. Attributing every A1 record to FY 2027/28 is a v0.4 fixture choice; §13's selection-consistency rule still applies before any business fixture executes.

| Chronological path / actor / source | Read/event and consumer | Guard/failure / disclosure |
|---|---|---|
| Charles opens Overview / A1 | All owner measure reads at 10:00 EAT | Every figure from owner reads; no client calculation. |
| Charles selects FY 2027/28 / A1 | Route pushed; BUD funding read | Funding shown only under §5.5 rule 5; read permission to be confirmed (§17.1). (v0.5: confirmed by D-ANL-07.) (v0.8: pictured for Amina Hassan, Accounting Officer, on ANL-DES-28.) |
| Charles opens Tender proceedings and selects Award / A1 | Route pushed with `state=award` | Charts unchanged; register filtered. |
| Peter opens Overview with HRMD / A2 | Owner reads under Peter's scope | Department shares only; no award amount; no funding position; no 044 or 046. |
| Coverage read fails / A1 variant | PLN coverage read typed failure | Region error only; no zero or percentage. |
| Daniel Otieno direct entry / A1 | Verdict read | Retained v0.3 copy; conflict recorded in §17.1. (v0.5: superseded by D-ANL-10; Daniel Otieno reads as ANL-DES-31J, and ANL-DES-31H uses Nadia Kamau.) |
| Peter selects FY 2027/28 with HRMD / A2 | BUD department-view read | Own-line positions and own reservations on shared lines only; shared allocation never divided. |
| Daniel Otieno opens Overview / A1 | Technical read | Site-wide read-only; no business action. |

## 14. Acceptance contract

| ID | Required result |
|---|---|
| ANL-AC-01 | A1 separately reconciles 2 Needs, 2 departmental plans, 7 Active Plan items, 7 Requisitions, 6 Tenders; no summed total or conversion funnel. |
| ANL-AC-02 | Older-created records are included by correct owner fiscal-year attribution; All years works without a current-year prerequisite. |
| ANL-AC-03 | Same Plan-item unit for site-wide and HoD; versions/contributors count once and operative/candidate facts remain distinct. |
| ANL-AC-04 | Tender chart reconciles 1 preparation + 1 open + 1 Evaluation + 2 Award + 1 Closed = 6. An award decision leaves unfinished notices visible. |
| ANL-AC-05 | Nonempty Opening leads to confirmed automated Evaluation intake; empty Opening produces no assessment/report/Award work. |
| ANL-AC-06 | No award, cancellation, pending receipt, corrections and missing status follow §5 without invented completion or hidden obligations. |
| ANL-AC-07 | A2 HRMD counts 1 Need, 1 DPP, 4 Plan items, 4 REQs, 4 Tenders; 041 contributor once; no 044/046 disclosure. |
| ANL-AC-08 | Identity-complete/stage-incomplete retains justified totals with Status unavailable; identity-incomplete never claims a full total. |
| ANL-AC-09 | Area/search/stage filters and paging have stated count meanings and preserve authorised return context. |
| ANL-AC-10 | Every link binds actual owner identity/version; no granted access, mutation or personal task from Analytics. |
| ANL-AC-11 | Static briefs contain full pictured content and named variants; first-view/keyboard/zoom checks preserve material reasons and read-only purpose. |
| ANL-AC-12 | Six tabs exist with the §9.1 routes; selecting a tab, applying or clearing filters and choosing a state each push a route; refresh, Back and an opened link reproduce the same tab, filters and state after a fresh verdict read; search text and cursor never appear in the URL. |
| ANL-AC-13 | An invalid or unpermitted `fy`, `dept` or `state` in a route shows the §8 filter message and never widens the selection. The Analytics menu item is visible to an actor with no permitted area. |
| ANL-AC-14 | A1 Overview reproduces every ANL-DES-21 figure from owner reads: strip counts and segments, waiting bands (Requisitions 0–7 days 1; Tender proceedings 0–7 days 3 and 8–30 days 1), coverage 55,500,000 of 68,500,000 shown as 81%, and the five §10A.2 transition rows. |
| ANL-AC-15 | Medians use the §5.4 rule: an even number of values gives the mean of the two middle values (8.5 for A1 T1); calendar days use site-timezone dates; only transitions ending inside the window count. |
| ANL-AC-16 | Changing the Financial year filter changes which records are included but not the twelve-month window. |
| ANL-AC-17 | Waiting time is shown in the four bands from the owner's `since`; no screen, label or count calls it late, overdue or at risk unless the owner supplies that fact. |
| ANL-AC-18 | Plan coverage equals Planning's `ProceedingCoverage` values; Fully, Partly and Not covered item counts reconcile to the Plan-item count; a department selection uses only that department's allocations (A2: 21,500,000 of 22,500,000, 96%). |
| ANL-AC-19 | Requisition and Tender-stage values reconcile to REQ drawdown values (A1: 12,000,000 requested; 55,500,000 authorised; stage values 6,500,000 + 8,000,000 + 3,500,000 + 12,500,000 + 25,000,000). No value of a different kind is added to them. |
| ANL-AC-20 | The award amount is the current committed Award decision amount; a superseded decision adds nothing; no department total of award amounts exists; an owner summary without an amount produces no amount. |
| ANL-AC-21 | The funding position appears only under §5.5 rule 5 and equals Budget's totals; Reserved, Committed and Available sum to Registered allocation; otherwise the §8 funding message appears. |
| ANL-AC-22 | Invitation timing equals Planning's Baseline lateness per proceeding; a missing actual shows No date recorded and is never zero. |
| ANL-AC-23 | A failed or incomplete measure read follows §8; no zero, partial total or percentage is presented as complete. |
| ANL-AC-24 | No forecast, trend line, savings figure, utilisation percentage, health or risk score, or sum of different kinds of amount appears on any artboard or in any response. |
| ANL-AC-25 | The funding region appears only for the §5.5 rule 5 audience and technical readers with one Financial year selected; an actor outside the audience sees no funding region or message; a filter never grants funding visibility. |
| ANL-AC-26 | The department view shows the department's own lines in full and only the department's own reservations and commitments on lines available to all departments (A2: 30,000,000; 13,500,000; 0; 16,500,000; and 8,000,000 reserved on the shared line); no shared line's allocation or available amount is divided. |
| ANL-AC-27 | The Technical Operator sees every Analytics figure, chart and row site-wide, including the funding position, and no business action (ANL-DES-31J equals ANL-DES-21). |
| ANL-AC-28 | Rendered artboards follow §10A.1 rules 3 and 6 to 10: each chart uses its stated colour role; each area uses one icon consistently on its tab, strip column and region titles; no status colour marks a category or band; every meaning remains carried by text. |

## 15. Implementation and test constraints

Apply KT-STD §§4–6. Adapter/schema and current stage/route bindings must be reviewed against owners before implementation acceptance. Verify source identities and all §13 branches, not just phrases or chart arithmetic. More-than-ten-results paging requires a separate runtime fixture. Approval of requirements does not prove services, seeds, rendered boards or representative-user tests exist.

## 16. Prohibited shortcuts — v0.4

Apply KT-STD-001 v1.16 §10. Domain-specific prohibitions:

- Do not compute a measure in the browser from rows, or from a page of rows.
- Do not query or join owner tables; use owner reads (§7.1).
- Do not add a forecast, expected date, trend line, savings, variance between award amount and authorised value, utilisation percentage, spend, payment, health or risk figure.
- Do not call waiting time late, overdue or at risk without an owner fact.
- Do not add different kinds of amount together, or divide one award amount or one shared Budget Line between departments.
- Do not show the funding position outside §5.5 rule 5.
- Do not write search text or a paging cursor into the URL, or swap a tab without pushing its route.
- Do not store any Analytics measure as a business record; responses are transient (§4).

## 17. Traceability and precedence

KT-STD governs document/design structure; OVS governs persistent disclosure; AUTH governs scope; CTX governs local filters; owners listed in §3 govern lifecycle and values. The approved source documents remain unchanged. Source interfaces requiring a safe aggregate/list/route projection are named in §7; implement in those canonical interfaces with their owners. No companion standard clarification or duplicate prompt is a dependency of this document. For later CM integration, contract identity is independent and Accounts ownership remains ERPNext.

**v0.4 addition.** The measures in §4A are Analytics compositions of owner facts. Each owner remains authoritative for its facts and labels: PLN for planned value, coverage and invitation timing; REQ for requested and authorised values; AWD for award amounts; BUD for the funding position. A correction to any of those owner facts changes the Analytics figure on the next read and needs no Analytics change.

### 17.1 Required corrections in other documents — v0.4

| Document | Required correction | Status |
|---|---|---|
| KT-STD-001 v1.16 | Add an **Analytics** archetype to §2.6.3 and chart forms to the approved visual system in §2.2 and §2.6.4, or record approval of this document's stated departure (§10A.1). | Required before design approval (v0.5: done by D-ANL-06 in KT-STD-001 v1.17 §§2.2, 2.6.3, 2.6.4, 2.6.10 and 2.9.3; status Proposed with KT-STD-001 v1.17.) |
| PLN-CHG-001 v1.29 | Expose, under its own read verdicts, the §7.1 Planning projections: departmental plan acceptance instants; Active Version item values and allocation amounts by source department; `ProceedingCoverage` covered values; invitation Baseline lateness per proceeding. | Required before implementation acceptance |
| REQ-CHG-001 v1.14 | Expose drawdown values by current Version state and contributing department, and submission, authorisation and handoff-consumption instants, under the neutral read scope. | Required before implementation acceptance |
| TPR-CHG-001 v0.17 | Expose `published_at` and cancellation `decided_at` in a safe read for permitted Tenders. | Required before implementation acceptance |
| BOP-CHG-001 v0.11 | Expose the Opening complete instant for nonempty openings without bid counts or sealed facts. | Required before implementation acceptance |
| EVL-CHG-001 v0.5 | Expose the first Report sent instant per Evaluation case. | Required before implementation acceptance |
| AWD-CHG-001 v0.5 | Expose case received time, first committed decision instant and outcome of cycle 1, and the current Award amount. Confirm whether the HoD scoped final-decision summary includes the award amount; A2 assumes it does not. | Required; HoD amount question before design approval |
| BUD-CHG-001 v1.12 | Expose Fiscal Year Active Version totals for Analytics and confirm which responsibilities may read the funding position; ANL-DES-28 pictures Charles Mutiso (Head of Procurement Function), who BUD-CHG-001 v1.12 §7 does not list. | Required before design approval (v0.5: audience decided by D-ANL-07. Required BUD correction: grant the funding-position read to the D-ANL-07 roles, give Head of User Department the department view only, and expose line Available to and reservation source department for Analytics.) |
| NDS-CHG-001 v1.16 | Expose first-acceptance decision timestamps per permitted Need. | Required before implementation acceptance |
| OVS-CHG-001 v0.6 (not read for v0.4) | Confirm the §7.1 reads fit OVS-CHG-001 v0.6 §4.1 read additions. Resolve the pre-existing conflict between this document's §6 and ANL-DES-11B/ANL-DES-31H (a technical operator receives no business aggregate) and KT-STD-001 v1.16 §8.3, which describes Daniel Otieno as a technical reader under KT-STD-001 v1.16 §3A.6, which says technical readers are never Forbidden and see every record. | Owner decision required (v0.5: the technical-operator conflict is resolved by D-ANL-10; OVS-CHG-001 §4.2 must record that the Technical Operator has site-wide read-only access. The §7.1 read-fit confirmation remains.) |
| KT-DOC-CTRL-001 | Record ANL-CHG-001 v0.4 as Proposed; on approval update its entry. The register was not supplied for v0.4. | On approval (v0.6: also record the Analytics area icons and the palette roles of §10A.1 rule 3 in the design system when Claude Design proposes them; KT-STD-001 v1.18 §2.6.11.) |

## 18. Approval effect

### 18.0C v0.8 approval effect — approved 4 October 2026 (heading read: v0.8 approval effect (proposed))

v0.8 is approved by the Project Owner (4 October 2026, “Yes”, answering “Shall I apply this pass, and then approve KT-STD v1.22, HOME v0.6 and ANL v0.8 together?”). It applies the KT-STD-001 v1.22 surfaces, the summary-column treatment, the figure colour and the D-ANL-14 render pass to every Analytics artboard, superseding v0.7 and v0.6. (Proposed text read: Approval of v0.8 would apply the Home summary column and the figure colour to the Analytics summary strip and result figures, with everything else in v0.7 unchanged.)

### 18.0B v0.7 approval effect (proposed)

Approval of v0.7 would make the KT-STD-001 v1.22 surfaces the design input for every Analytics artboard. Everything else approved in v0.6 is unchanged.

### 18.0A v0.6 approval effect — approved 4 October 2026 (heading read: v0.6 approval effect (proposed))

v0.6 is approved by the Project Owner (4 October 2026, “Mark the three documents as approved and give them to me to download”). It authorises everything §18.0 lists for v0.5, with the §10A.1 visual-language rules applying KT-STD-001 v1.18 §2.6.11, now within approved KT-STD-001 v1.21. It does not approve a palette, an icon set or token values, the owner read corrections in §17.1, or implementation, rendered comparison or representative-user acceptance. (Proposed text read: Approval of v0.6 would authorise everything §18.0 lists for v0.5, with the §10A.1 visual-language rules applying KT-STD-001 v1.18 §2.6.11. It does not approve KT-STD-001 v1.18, a palette, an icon set or token values; those are approved through the standard and the design system.)

### 18.0 v0.5 approval effect (proposed)

Approval of v0.5 would authorise everything §18.1 lists for v0.4, as amended by D-ANL-06 to D-ANL-10: the funding-position audience and department view, the Technical Operator's site-wide read-only Analytics access, ANL-DES-29F and ANL-DES-31J, and the KT-STD-001 v1.17 Analytics archetype as the cited standard. It does not approve KT-STD-001 v1.17 itself, any owner read correction in §17.1, or an AWD change; those require their own approvals.

### 18.1 v0.4 approval effect (proposed)

Approval of v0.4 would authorise the §4A measures, the §§5.4–5.5 time and value rules, the §9.1 tabs, routes and URL state, and §10A as the design input, superseding v0.3 and its §10 design contract, which is retained as history. It would not approve the KT-STD-001 archetype correction, any owner read projection in §17.1, the funding-position audience, or the HoD award-amount treatment; those are separate decisions. It would not approve deferred CM/Accounts measures, change owner business commands or establish implementation, rendered comparison or representative-user acceptance.

### 18.2 v0.3 approval effect (retained)

Approval would authorise the cross-module read-only scope, measures, selection contract and §10 design input. It would not approve deferred CM/Accounts measures, change owner business commands or declare internal-review readiness. Exact owner bindings, rendered comparison and representative-user acceptance remain required.
