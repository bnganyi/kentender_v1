# Seed scenario map (row HOME6-0005)

Date: 4 October 2026. Sources: SEED-OPS-001 v1.24 (latest; no v1_25), SEED-001 v1.4, KT-STD-001 v1.22 §8.3, `kentender_core/seeds/{canonical,site_setup,clock,constants}.py`, the module profile files, and the Home spec's §10A.2, §10B.2 and §13. Read only; nothing was loaded or run. Neither the runbook nor SEED-001 mentions Home.

## 1. What the canonical world holds

`make seed-canonical SITE=… THROUGH=award` builds one chain through the real commands: one Tender (reference generated, `TND-MOH-2027-002` on dev; title "Supply and delivery of business laptops"), one Requisition, one eligible Plan Item, four Needs (`NDS-MOH-2027-0001/0003/0004` Accepted; `NDS-MOH-2027-0002` "Digital health workforce certification programme" stays Submitted since 24 Nov 2026), four bids, one opening, one evaluation (report delivered 16 Jun 2027, 14:07), one award (recorded 17 Jun 2027, 10:00; sent to Contracting 2 Jul 2027, 09:00).

Open work at the end of the chain with no profile and no clock: Dr Peter Kimani's review of `NDS-MOH-2027-0002`. Everything else is complete. Technical readers get nothing from My Work.

## 2. Demo profiles that exist

Profiles are mutually exclusive named states, each loaded from the base and set with a site-wide test clock (test environments only). Loading a profile rebuilds the Planning namespace, clearing the Tender and everything downstream.

| Module | Profiles / moments | File |
|---|---|---|
| Requisitions | `REQ-SC-HOLD`, `REQ-SC-SHARED-LINE-SHORT` (Charles has a Requisition to authorise) | `procurement_requisitions/seeds/profiles.py` |
| Bid Opening | `BOP-DEMO-BEFORE-JOIN` (an Upcoming "Start opening"), others between 10 Jun 10:10 and 12 Jun 11:10 | `bid_opening/seeds/profiles.py` |
| Award | `AWD-DEMO-OPINION` (17 Jun 09:00), `AWD-DEMO-DECISION` (17 Jun 10:00), `AWD-DEMO-NOTICE` (17 Jun 10:10), `AWD-DEMO-WAIT` (18 Jun 09:05), `AWD-DEMO-DELIVERED` (2 Jul 09:00) | `award/seeds/profiles.py` |
| Needs | profiles present | `departmental_needs/seeds/profiles.py` |
| Evaluation | **none** (FU-EVL-08 names them; not built) | n/a |
| Tenders | isolated single-state worlds under `pw.*` users | `tenders/seeds/playwright_ui_fixtures.py` |

## 3. Personas (logins end `@moh.example.test`; the shared fixture password is in `apps/kentender_v1/.env.ui`, not copied here)

| Persona | Responsibility | Home scenario |
|---|---|---|
| Charles Mutiso | Head of Procurement Function, site-wide | H10 (HOME-DES-21), also the Award opinion holder |
| Brian Wafula | Procurement Officer, site-wide | H1, H3, H8 (HOME-DES-22, 25, 26) |
| Amina Hassan | Accounting Officer, site-wide | H2 (HOME-DES-23), H12 (HOME-DES-29) |
| Dr Peter Kimani | Head of User Department, HRMD | H11 (HOME-DES-24) |
| Daniel Otieno | Technical Operator, site-wide, read-only | HOME-DES-27 |
| Jane Wanjiku | Public observer, no responsibility | HOME-DES-28F (denied); supplier portal users get the same |
| Naomi Chebet | Auditor, site-wide, read-only | an extra oversight-only check (not a board) |

## 4. Scenario by scenario

| Scenario | Board | Source | Notes |
|---|---|---|---|
| H2 Amina, 16 Jun 2027, 16:00 | 23 | **Canonical data + `AWD-DEMO-OPINION` with the clock set to 16 Jun 16:00.** The profile's own moment is 17 Jun 09:00, so setting an earlier instant must be proven in Phase 7 (the state is the same between 14:07 on 16 Jun and the opinion signing at 09:10 on 17 Jun). | Title "Supply and delivery of business laptops" matches the board. "View report" blocked (FU-HOME-04). |
| H4 empty (Brian) | 28A | End of the canonical chain; no profile | Brian has nothing open. |
| H7 Technical Operator | 27 | Canonical; no profile | By design no business entries. |
| H9B denied (Jane) | 28F | Canonical | Any non-internal user. |
| H11 Peter, 18 Jun 2027, 10:00 | 24 | **Partly.** Real: Peter's review of `NDS-MOH-2027-0002` (submitted 24 Nov 2026, not "yesterday"; the board text "Staff training laptops" is synthetic). Oversight rows 043 and 041 are synthetic. | Phase 7 builds a Need "Staff training laptops" submitted 17 Jun 14:00 and two oversight Tenders. |
| H10 Charles, 18 Jun 2027, 10:00 | 21, 21N | **One row of nine real.** "Prepare professional opinion" (received 16 Jun 14:07) at `AWD-DEMO-OPINION`; an Upcoming "Start opening" at `BOP-DEMO-BEFORE-JOIN`. Authorise requisition, 045, 043, 047, 041 are synthetic. | Profiles cannot be stacked: `REQ-SC-HOLD` rebuilds Planning and clears the Tender. Needs a Home fixture module. |
| H12 Amina, 18 Jun 2027, 10:00 | 29 | **One of four My work rows real** ("Decide award" at `AWD-DEMO-DECISION`; the profile's 17 Jun 10:00 versus the board's "received 17 June, 16:00" differ). 042 appointment, 039, 047, 048 synthetic. | Tender 042 here is not H10's 042 (FU-HOME-08). |
| H1 Brian, 17 Jun 2027, 10:00 | 22 | **Synthetic.** Four distinct Tenders (034 cancellation evidence due 18 Jun; 039 cancellation under review; 040 clarification; 037 submitted for approval). | Built through owner commands, one authorised Requisition per Tender. |
| H3 Brian blocked | 25 | **Synthetic.** Needs a published Tender with a clarification that triggers the addendum guard. The canonical clarification is already answered. | |
| H8 Brian, six clarifications | 26, 26B | **Synthetic.** Six Tenders (050 to 055) or six clarifications on one Tender if the identity rule keeps them separate actions; to be decided in Phase 3A. | |
| H5 waiting failed, H6 total failure, H9A loading | 28B, 28D, 28E | **Not seed data.** Injected provider failure and an unresolved read. | Test hooks, not fixtures. |
| H10 Coming up failed | 28C | Not seed data; injected | |

## 5. Dates and the clock

The spec's read times (16, 17, 18 June 2027) fall in the canonical award week. The real date is 4 October 2026, so every canonical row is future-dated; Home reads `kentender_core/services/test_clock.py::current_instant()` (hook `kt_test_clock`, test environments only). Seed commands freeze their own instant through `seeds/clock.py` (`clock.at("<instant>")`) and the real clock resumes afterwards. Each Home fixture records the exact instant it expects so the relative labels (e.g. "Received 2 days ago (16 June, 11:00)") are testable.

## 6. What Phase 7 must add (never a direct write to a governed table)

1. A Home fixture module with named worlds (H1, H3, H8, H10, H11, H12), each built through owner commands as the named actors, loading and releasing like the other profile sets (`list_profiles`, `load_profile`, `restore_base`, a loaded marker), released by `canonical.release_demo_profiles()`.
2. Makefile targets beside `seed-awd-profiles`, `seed-bop-profiles`, `seed-req-profiles`; a case in `kentender_core/tests/test_canonical_seed.py`.
3. SEED-OPS-001 v1.25: a Home section beside §9 to §9B, and the §11 register entries. Check the latest runbook version first and never reuse an existing filename.
4. New personas only through `seeds/site_setup.ACTORS` and `ASSIGNMENTS`, never inside a module seed; none are expected (the table above covers every board).
5. Isolation: a Home world must not overwrite or leave behind the canonical Tender; its reseed path is the runbook's `REBUILD=True`.
