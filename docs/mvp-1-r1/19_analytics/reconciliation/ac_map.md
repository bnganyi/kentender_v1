# ANL-CHG-001 v0.8: acceptance map (row ANL8-0007)

Authority: ANL-CHG-001 v0.8 §14, copied verbatim. Tracker rows come from the tracker's acceptance map. Status of each acceptance row is recorded in the tracker, never here.

| Acceptance row | Required result (verbatim, ANL v0.8 §14) | Tracker rows |
|---|---|---|
| ANL-AC-01 | A1 separately reconciles 2 Needs, 2 departmental plans, 7 Active Plan items, 7 Requisitions, 6 Tenders; no summed total or conversion funnel. | ANL8-0305, ANL8-0308 |
| ANL-AC-02 | Older-created records are included by correct owner fiscal-year attribution; All years works without a current-year prerequisite. | ANL8-0243, ANL8-0308 |
| ANL-AC-03 | Same Plan-item unit for site-wide and HoD; versions/contributors count once and operative/candidate facts remain distinct. | ANL8-0203, ANL8-0308 |
| ANL-AC-04 | Tender chart reconciles 1 preparation + 1 open + 1 Evaluation + 2 Award + 1 Closed = 6. An award decision leaves unfinished notices visible. | ANL8-0242, ANL8-0308, ANL8-0704 |
| ANL-AC-05 | Nonempty Opening leads to confirmed automated Evaluation intake; empty Opening produces no assessment/report/Award work. | ANL8-0242, ANL8-0308 |
| ANL-AC-06 | No award, cancellation, pending receipt, corrections and missing status follow §5 without invented completion or hidden obligations. | ANL8-0242, ANL8-0308 |
| ANL-AC-07 | A2 HRMD counts 1 Need, 1 DPP, 4 Plan items, 4 REQs, 4 Tenders; 041 contributor once; no 044/046 disclosure. | ANL8-0306, ANL8-0308, ANL8-0706 |
| ANL-AC-08 | Identity-complete/stage-incomplete retains justified totals with Status unavailable; identity-incomplete never claims a full total. | ANL8-0304, ANL8-0308 |
| ANL-AC-09 | Area/search/stage filters and paging have stated count meanings and preserve authorised return context. | ANL8-0111, ANL8-0302, ANL8-0516 |
| ANL-AC-10 | Every link binds actual owner identity/version; no granted access, mutation or personal task from Analytics. | ANL8-0224, ANL8-0516, ANL8-0709 |
| ANL-AC-11 | Static briefs contain full pictured content and named variants; first-view/keyboard/zoom checks preserve material reasons and read-only purpose. | ANL8-0801, ANL8-0804, ANL8-0805 |
| ANL-AC-12 | Six tabs exist with the §9.1 routes; selecting a tab, applying or clearing filters and choosing a state each push a route; refresh, Back and an opened link reproduce the same tab, filters and state after a fresh verdict read; search text and cursor never appear in the URL. | ANL8-0502, ANL8-0709 |
| ANL-AC-13 | An invalid or unpermitted `fy`, `dept` or `state` in a route shows the §8 filter message and never widens the selection. The Analytics menu item is visible to an actor with no permitted area. | ANL8-0110, ANL8-0303, ANL8-0502, ANL8-0603, ANL8-0708 |
| ANL-AC-14 | A1 Overview reproduces every ANL-DES-21 figure from owner reads: strip counts and segments, waiting bands (Requisitions 0–7 days 1; Tender proceedings 0–7 days 3 and 8–30 days 1), coverage 55,500,000 of 68,500,000 shown as 81%, and the five §10A.2 transition rows. | ANL8-0301, ANL8-0308, ANL8-0505 |
| ANL-AC-15 | Medians use the §5.4 rule: an even number of values gives the mean of the two middle values (8.5 for A1 T1); calendar days use site-timezone dates; only transitions ending inside the window count. | ANL8-0106, ANL8-0308 |
| ANL-AC-16 | Changing the Financial year filter changes which records are included but not the twelve-month window. | ANL8-0102, ANL8-0308 |
| ANL-AC-17 | Waiting time is shown in the four bands from the owner's `since`; no screen, label or count calls it late, overdue or at risk unless the owner supplies that fact. | ANL8-0103, ANL8-0308 |
| ANL-AC-18 | Plan coverage equals Planning's `ProceedingCoverage` values; Fully, Partly and Not covered item counts reconcile to the Plan-item count; a department selection uses only that department's allocations (A2: 21,500,000 of 22,500,000, 96%). | ANL8-0204, ANL8-0107, ANL8-0308 |
| ANL-AC-19 | Requisition and Tender-stage values reconcile to REQ drawdown values (A1: 12,000,000 requested; 55,500,000 authorised; stage values 6,500,000 + 8,000,000 + 3,500,000 + 12,500,000 + 25,000,000). No value of a different kind is added to them. | ANL8-0221, ANL8-0308 |
| ANL-AC-20 | The award amount is the current committed Award decision amount; a superseded decision adds nothing; no department total of award amounts exists; an owner summary without an amount produces no amount. | ANL8-0113, ANL8-0247, ANL8-0308 |
| ANL-AC-21 | The funding position appears only under §5.5 rule 5 and equals Budget's totals; Reserved, Committed and Available sum to Registered allocation; otherwise the §8 funding message appears. | ANL8-0112, ANL8-0227, ANL8-0225, ANL8-0308 |
| ANL-AC-22 | Invitation timing equals Planning's Baseline lateness per proceeding; a missing actual shows No date recorded and is never zero. | ANL8-0205, ANL8-0308 |
| ANL-AC-23 | A failed or incomplete measure read follows §8; no zero, partial total or percentage is presented as complete. | ANL8-0101, ANL8-0304, ANL8-0308 |
| ANL-AC-24 | No forecast, trend line, savings figure, utilisation percentage, health or risk score, or sum of different kinds of amount appears on any artboard or in any response. | ANL8-0308, ANL8-0801 |
| ANL-AC-25 | The funding region appears only for the §5.5 rule 5 audience and technical readers with one Financial year selected; an actor outside the audience sees no funding region or message; a filter never grants funding visibility. | ANL8-0112, ANL8-0308 |
| ANL-AC-26 | The department view shows the department's own lines in full and only the department's own reservations and commitments on lines available to all departments (A2: 30,000,000; 13,500,000; 0; 16,500,000; and 8,000,000 reserved on the shared line); no shared line's allocation or available amount is divided. | ANL8-0226, ANL8-0308 |
| ANL-AC-27 | The Technical Operator sees every Analytics figure, chart and row site-wide, including the funding position, and no business action (ANL-DES-31J equals ANL-DES-21). | ANL8-0114, ANL8-0249, ANL8-0707 |
| ANL-AC-28 | Rendered artboards follow §10A.1 rules 3 and 6 to 10: each chart uses its stated colour role; each area uses one icon consistently on its tab, strip column and region titles; no status colour marks a category or band; every meaning remains carried by text. | ANL8-0403, ANL8-0404, ANL8-0801 |
