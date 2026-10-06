# ANL-CHG-001 v0.8: real-data walk on the two-year seed world (rows ANL8-0701 to 0712)

Run 5 October 2026 on `kentender-test.local` (http://127.0.0.1:8001) after the seed session reported the world ready (SEED-002 v0.1; commits 505be8dc and 92f62e7d). Test clock 18 June 2027, 10:00 EAT. The owner's release of the seed hold: the owner's 5 October instruction "send a message to the seed building session to begin" (the seed session notes the owner's own record of the release is still to be made).

## Expected figures, derived independently (row 0703)

Plain SQL on the owner tables, never through an Analytics provider: `kentender_core/tests/analytics_seed_world_expected.py`. Compared with the endpoint (Charles Mutiso, All years, FY 2026/27, FY 2027/28):

| Figure | Derived from tables | Analytics | Match |
|---|---|---|---|
| Needs (non-Draft, non-Withdrawn), FY 2026/27 / 2027/28 / all | 3 / 4 (3 accepted + 1 submitted) / 7 | 3 / 4 / 7 | yes |
| Plan items in the Active Plan, 2026/27 / 2027/28 / all | 14 / 3 / 17 | 14 / 3 / 17 | yes |
| Coverage states 2026/27 (full, partly, not) | 11, 1, 2 | 11, 1, 2 (all years 11, 1, 5) | yes |
| Planned value 2026/27 / 2027/28 / all | 236,500,000 / 102,000,000 / 338,500,000 | same | yes |
| Covered value 2026/27 (authorised drawdown) / 2027/28 | 143,000,000 / 0 | same | yes |
| Requisitions 2026/27 | 12 Authorised + 1 Submitted to Procurement | same | yes |
| Tenders 2026/27 by owner status | Approved 1, Draft 1, Published 2, Submission period ended 5, Cancelled 2 | Preparation 2, Open 2, Opening 1, Evaluation 1, Award 3, Closed 2 | yes (see T5) |
| HRMD selected: needs / plan items / planned / covered / Tenders | 3 / 8 / 70,500,000 / 57,000,000 / 6 | same | yes |
| Digital Health selected | 4 / 11 / 268,000,000 / 86,000,000 / 7 | same | yes |
| Budget FY 2026/27 registered | KES 290,000,000 on four lines (SEED-002) | KES 290,000,000; reserved 143,000,000 (= covered); available 147,000,000 | yes |
| Award amount | `AWD-MOH-2026-002-DEC-01` submitted 46,400,000 (evaluated 46,400,000) | "Award amount KES 46,400,000" | yes |
| Laptops invitation timing | SEED-002 corrections: published 103 days after the approved date | "103 days after approved date" | yes |
| Steps (completed) | T1 12 authorised Requisitions; T2 11 (monitors authorised, not taken up); T3 9 published; T4 3 (reports sent); T5 1 (one committed decision) | 12, 11, 9, 3, 1 | yes |

Judgement recorded: **T5 network switches** has Opening complete but its Evaluation case holds no opening handoff, no `opening_completed_at` and no intake, so Evaluation has not received the package. ANL §5.2 puts that in **Opening** ("its confirmed completed package awaits EVL receipt"). Analytics shows Opening 1, Evaluation 1.

## Persona walks, from the sidebar (rows 0704 to 0708)

Each opened Analytics from the "Analytics" sidebar item at `/desk/analytics`, logged in with the shared fixture password (never printed).

| Persona | Observed |
|---|---|
| Charles Mutiso (HoPF) | Needs 7, Departmental planning 4, Annual planning 17, Requisitions 13, Tender proceedings 11; planned KES 338,500,000; six tabs; FY 2026/27 applied gives `?fy=2026-2027` and the funding position (registered 290,000,000); Tender tab shows the outstanding matters in the wording of the seed's own states (eight when first walked; nine after the seed correction below) |
| Amina Hassan (AO) | Same figures as Charles on every tab, including the 13 Requisitions (the aggregate widening, OD-2); funding KES 290,000,000 with reserved 143,000,000, committed 0, available 147,000,000 on a shared FY link |
| Dr Peter Kimani (HoD) | Heads HRMD, Digital Health and the Directorate in this world, so his scope is the whole ministry and his figures equal the site-wide ones; his Tender tab note reads "1 AO award decision recorded." with **no award amount** (Charles, Amina and Daniel see "Award amount KES 46,400,000") |
| Daniel Otieno (Technical Operator) | Identical to Charles on every tab; no business action |
| Nadia Kamau (release operator) | Menu item visible; the page shows the title, a lock illustration and "No Analytics records are available to your responsibilities." with no tabs, totals or rows (ANL-DES-31H) |

A department-limited reader is shown by the endpoint (not a browser): Grace Wanjiku (Head of User Department for HRMD, Departmental Author in both departments) sees Planned KES 70,500,000 and Covered 57,000,000 for the plan items she heads (HRMD's slice exactly) and the whole of what she authors in the other areas; Digital Health plan items are not shown to her.

## Route and interaction checks (row 0709)

As Charles: selecting a year changes nothing until Apply, then the URL is `/desk/analytics?fy=2026-2027`; the Tender proceedings tab keeps `fy`; the stage select adds `&state=award` and the register reads "Showing 3 of 3 matching Tenders" with "All 11 Tenders in this area" and "Clear stage filter"; Back, Back, Forward walk `…tender-proceedings?fy=2026-2027`, `/desk/analytics?fy=2026-2027`, `…tender-proceedings?fy=2026-2027`; a direct load of `/desk/analytics/tender-proceedings?fy=2026-2027&state=award` reproduces the same view. Paging: "Showing 10 of 11 Tenders", Next gives "Showing 11 of 11 Tenders"; a search for "printers" gives "Showing 1 of 1 matching Tenders" with the URL unchanged. All six tabs load without an error panel for Charles, Amina, Peter and Daniel.

## Found live and changed

An invalid `fy` (`?fy=bogus`) showed the message beside All-years figures. ANL-AC-13 says an invalid value "never widens the selection", so the server now returns the message, the valid parts of the selection and no figures, and the page draws only the filter row and the message (conflicts C25, FU-ANL-29).

## Re-check after the seed session's correction (c8efeb05)

The seed session changed the field laptops Tender (TND-MOH-2026-006): Brian drafts an addendum on 16 Jun 2027 at 11:00 and asks Amina on the same day at 14:00 to consider cancellation, so it now has no recommendation and waits on Amina. Read-only re-check on the test site as Charles: the Tender stays in **Open** (Published — open), the strip reads "9 outstanding matters" (was 8), and the Tender tab lists "Supply of field laptops — Waiting for Amina Hassan to consider cancellation. Waiting 2 days since 16 June, 14:00". Waiting bands for Tender proceedings are now 0–7 days 8 and 8–30 days 1. No figure in the derivation table above changed.

## Not done

Failure of one area or one measure was exercised by tests, not forced live. Screen reader, real browser zoom, Firefox and WebKit not run. The Home page's Analytics link was not re-walked on the seed world. No Playwright spec was written.
