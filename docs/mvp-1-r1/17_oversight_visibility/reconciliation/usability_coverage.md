# OVS-CHG-001 v0.6: register and record usability coverage (Phase 11, OVS6-1101 to OVS6-1114)

**What this is.** The recorded coverage result for each of the twelve modules, as OVS-AC-018 asks: "Every applicable module has a recorded usability coverage result; an exclusion has a specific reason and owner, not a silent omission."

**How it was made (4 October 2026).** A read-only audit of the code: the registers, workspace screens, page controllers and the server list and read services of each module. **Nothing was run in a browser.** "Met" means the code was seen doing the thing. "Kept on return" for a module marked Partly is an inference from the screen staying mounted and the filters living in component state; it needs a browser check. The audit did not open every record sub-screen (for example Evaluation's committee and report screens) and did not read `technical_read.py` in any module. **This file records results. It does not fix the gaps.** The gaps are in the follow-ups file (FU-OVS-51, 53, 54, 55 and 58).

## The checklist

From OVS v0.6 §5.2, §6 and §12, as the spec words them:

1. **Active / All** — "Provide clear **Active** and **All records** choices"; "Every module register includes authorised active and historical records."
2. **Search** — "search by reference/title"; "Search must not depend on remembering an internal database identifier."
3. **Filters** — "use supplier, department, status, date or outcome filters only where applicable and backed by existing data."
4. **Clear filters** — "Display active filters, filtered result count and **Clear filters**."
5. **Count** — the filtered result count.
6. **Kept on return** — "Preserve filters, sort order and page position on returning from a record"; "Preserve filters, selected versions and record context through browser back/forward and refresh."
7. **Historical findable** — "Completed, cancelled and returned records remain findable."
8. **Record view** — identity and position; current disclosed decision; supporting information; history; "Use **Not recorded** when a missing expected fact matters."
9. **Empty and error states** — "A no-result state distinguishes no matching records from a source-loading failure"; loading, no records, no matches, unavailable data, permission denial and completed work are distinct.

## Result per module

M = Met, P = Partly, N = Not met, NA = Not applicable. Anchors are relative to the app's own folder (`PJ` = `kentender_procurement/kentender_procurement/public/js`, `PS` = `kentender_procurement/kentender_procurement`).

| Module | Active / All | Search | Filters | Clear | Count | Kept on return | Historical | Record view | Empty / error |
|---|---|---|---|---|---|---|---|---|---|
| Configuration | P: status select with "All statuses"; "Include disabled years" on the years tab | P: user, email and role only; an assignment has no business reference | M | P: on the responsibilities register only | M | P: tabs kept alive, filters in memory | M | M | M |
| Strategy | P: status select only | M: reference and title | M | P: only inside the filtered-empty state | P: "Showing N of N" uses one number for both; server cap is 200 | P: filters in component state, not in the URL | P: latest version's status per plan | M | M |
| Budget | P: one budget per financial year, the year picker reaches closed years | N: no search on the workspace or lines tab | P: financial year; funding activity | P: only on activity | N | P: year kept in the browser | M | M | P: a failing year list may leave the skeleton up |
| Departmental Needs | P: status select; Withdrawn needs are excluded | M | M | M | M | P: search and status in the root, year and unit remembered on the server, not in the URL | P: Returned, Accepted, Not taken forward findable; Withdrawn not | M | M |
| Procurement Planning | NA: no register; one annual plan per financial year | N | P: financial year only | P: "Reset" only for a saved default | N | P | P | M | M |
| Requisitions | P: status select including Withdrawn and Revoked | M | M | P: business mode only | N: the total is returned and not shown | P | M | M | M |
| Tenders | P: status select with grouped "In progress" and "Closed" | M | M | M | N: the count label is returned and not shown | P | M | M | P: the empty text says "match these filters" even with none set |
| Bid Submission (supplier) | M | M | M | P: My bids and Available tenders; Receipts has no filters | M | M: filters live in the URL query | M | P: no tender outcome shown on the bid screens | M |
| Bid Opening | NA: no register; reached through the Tender record | NA | NA | NA | NA | NA | M | M | M |
| Bid Evaluation | P: state select | M | P: state only | P: "Clear search" shows only when nothing matches | N | P | M | M | P: on a workspace failure the board still says no evaluations are assigned |
| Award | N: the workspace is "Your award tasks" only | N | N | N | N | NA | N: open, non-cancelled cases only | M | P: forbidden and technical both read "You have no award tasks." |
| Proceedings | P: every started session is listed with a state filter | M | M | M | M | P: filters in memory | M | P: rows link to the owner's record | M |

## Gaps worth fixing, by effort

**Small**
- Configuration: send `start` and `page_length` from the responsibilities UI (the server cuts at 50 while the count shows the full total); add Clear filters to the rules filter.
- Strategy: show a real total, and label or raise the 200 cap; show Clear filters whenever a filter is set.
- Budget: a visible Reset for the remembered year; a failure branch in the year-list load and the tab loads.
- Requisitions: render the count; a Clear control in technical mode.
- Tenders: render the count label; fix the empty text when no filter is set.
- Bid Evaluation: make the failure state exclusive, add Try again, rename "Clear search" to "Clear filters", show a count.
- Award: separate the forbidden and technical text from the empty text.
- Proceedings: keep the filters in the URL.

**Medium**
- Filters in the route query everywhere except Bid Submission (one shared helper would cover Tenders, Requisitions, Needs, Evaluation, Strategy and Proceedings).
- Budget: search on the budget-lines tab.
- Departmental Needs: decide whether a withdrawn Need should be findable by its author or an auditor.
- Procurement Planning: a plans or items register with search, count and Clear filters, if the item list grows.

**Large**
- Award: a read-only register of award records (every stage, including cancelled and completed) with search, a state filter, a count and Clear filters.

## Candidate exclusions (reason and owner)

The audit did not invent owner names. "Module owner" is for the Project Owner to name.

| Exclusion | Reason | Owner |
|---|---|---|
| Bid Opening: search, Active/All, filters, Clear, count, return state | Opening has no register of its own; it is a route under a Tender (`PJ/bid_opening/BidOpening.vue`). Finding an opening is covered by the Tenders register and the Procurement meetings register. | Bid Opening module owner, with Proceedings |
| Bid Evaluation record screens: register criteria | The same reason, per Tender. The workspace is covered in the table. | Bid Evaluation module owner |
| Procurement Planning: Active/All and reference search | One annual plan per financial year plus the departmental plan; items live inside it. A plan-items search remains a gap if the list grows. | Planning module owner |
| Budget: Active/All and reference search | One budget per financial year; the picker reaches closed years. The residual gap is budget-line search. | Budget module owner |
| Configuration: reference search on responsibilities | An assignment has no business reference; searching by user and role is the nearest equivalent. | Configuration and AUTH owner |
| Proceedings: record view | The register links to the Opening or Evaluation record, which applies its own permission. | Proceedings module owner |
| Bid Submission: decision visibility in the bid record | A supplier's award or evaluation outcome belongs to the Award portal, not the bid screens. The audit did not read the portal, so this is **unverified**. | Bid Submission and Award owners |

## Reading this result

- No module is "Met" on every criterion. Award is the weakest (no register at all); the shared gaps are filters not kept in the URL and a result count the server sends and the screen does not show.
- OVS-AC-018 asks for a recorded result or a reasoned exclusion for every module. This file is that record; the exclusions above wait for the Project Owner to confirm them and name the owners.
- Per tracker rule 14, OVS is not "implemented" while a coverage row is open. The rows are closed as *result recorded*, and the fixes are follow-ups.
