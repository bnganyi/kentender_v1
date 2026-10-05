# SEED-002 — Canonical Seed World

| Control | Value |
|---|---|
| Document ID | SEED-002 (new; the identifier is proposed for the Project Owner's confirmation) |
| Version | 0.1 |
| Date | 5 October 2026 |
| Status | **Proposed — Project Owner approval required.** Not approved. |
| Replaces | On approval: **SEED-001** Harmonized End-to-End Fixture (approved v1.4) and **SEED-OPS-001** Canonical Site Seed Runbook (approved v1.24; v1.25 proposed, never approved). Both are retired as history, not amended (Appendix A records what each rule became). |
| Basis | Two-year seed world proposal, decisions D1–D7 (Project Owner, 4 October 2026: "Decisions for the owner: recommendations accepted"); fixture answers D8–D10 ("1. Accepted 2. Accepted 3. Accepted"); D11 ("include documentation revamp as one task. If it is easier, the current document can be retired completely so the next version can start on a clean slate without the previous baggage."); D12 ("one new document to replace both the fixture document and the runbook"). Plan and tracker: `Two_Year_Seed_World_Implementation_Plan.md`, `Two_Year_Seed_World_IMPLEMENTATION_TRACKER.md`. |
| Owner | `kentender_core` (`kentender_core/kentender_core/seeds/canonical.py`, `calendar.py`, `portfolio.py`) |
| Shared register | KT-STD-001 §8.1–§8.3 (site, units, people) stays the shared fixture register. Its §8.4 (Fiscal years) and §8.4A (Fixture instants) are replaced by this document's Part A §A3 when the Project Owner applies the pointer in Appendix C. |
| Evidence | Built and validated on `kentender-test.local` on 5 October 2026 (commits bedf8a5b and later; Appendix B lists the generated references). Approval of this document does not establish implementation, test coverage or production readiness. |

**Controlling decision.** A KenTender site has exactly one canonical world: two financial years read as at **18 June 2027, 10:00 EAT**. **FY 2026/27** is the year being carried out: its plan is Active and locked, and requisitions, Tenders, bids, openings, evaluations and awards run against it. **FY 2027/28** is the year being prepared: its budget, Needs, departmental plans and, at most, its approved Annual Plan. Everything else on a site (browser-test worlds, isolated profiles, hand-made drafts) is disposable. One command removes the disposable rows, reseeds the canonical ones through the same commands the screens use, and refuses to report success unless the result validates.

---

# Part A — The world

## A1. One moment, two years

| | Value |
|---|---|
| The as-at instant | **18 June 2027, 10:00 EAT** (`calendar.AS_AT`) — the read time of HOME-CHG-001 v0.6 H10–H12 and ANL-CHG-001 v0.8 dataset A1. Every recorded fixture event is at or before it; every live deadline is after it. |
| Year 1 | **FY 2026/27** (1 Jul 2026 – 30 Jun 2027), carried out. |
| Year 2 | **FY 2027/28** (1 Jul 2027 – 30 Jun 2028), being prepared. Nothing is bought against it. |
| The clock a test site reads | A test site (site_config `kt_bds_simulation_environment`) runs its live pages on the as-at instant through the site test clock; the seed sets it at the end of every run. A site that is not a test environment reads the real clock (decision D2: until the story is moved, such a site shows a story dated ahead of the real calendar). |
| How the dates are made | Every seeded command runs **at** its fixture instant under the frozen seed clock (`kentender_core.seeds.clock`); nothing is back-stamped, except the two publication-attempt instants one inline worker run cannot both hold. Year 2 keeps the module seeds' instants; Year 1's planning history is the same journey **364 days (52 weeks) earlier**, so each event keeps its weekday and spacing. Year 1's execution keeps its own March–July 2027 instants. |

**Each year's planned dates fit inside that year** (decision D8). Needs and departmental-plan requirements refuse a Required by outside their year, and Planning blocks an item whose baseline signing plus delivery ends after its completion boundary (`PLN_DELIVERY_BOUNDARY_INSUFFICIENT`). So every Year 1 Required by is 30 June 2027 at the latest, and each Year 1 item's approved invitation date (February–March 2027) leaves room to finish by then. Year 1's Tenders publish in April–May 2027, later than those approved dates, which Planning reads as Baseline lateness (ANL-M-05).

**Only off-the-shelf IT equipment can be bought.** The one installed Tender format is `IT-EQUIPMENT-OPEN-V1`; Requisitions admit nine equipment categories, Tenders eight (Laptop, Desktop computer, Tablet, Monitor, Printer, Scanner, Network equipment, Power-protection equipment). Every executed item is one of these.

## A2. Site and people

KT-STD-001 §8.1–§8.3 is the register: Procuring Entity `PE-MOH` (Ministry of Health, Africa/Nairobi), the three units (Directorate of Digital Health and Policy, Digital Health under it, Human Resources Management and Development), and every named person. This world adds no person.

Dated responsibilities (all others are open-ended; `site_setup.ASSIGNMENTS`):

| Person | Responsibility | Term | Why |
|---|---|---|---|
| Esther Muthoni, Dr Alfred Ochieng | Strategy Author, Strategy Approver | from 1 Jul 2023 | the 2023 Strategy baseline (owner, 26 Sep 2026: "Backdate") |
| Samuel Otieno | Head of User Department, Directorate | 2 Jan – 1 Sep 2025 (expired) | the register's expired appointment, before Year 1's history |
| Dr Peter Kimani | Head of User Department, Directorate | from 2 Sep 2025 | covers Digital Health through the parent unit (owner, 26 Sep 2026, D4) |
| Julia Njeri | Head of User Department, Digital Health, **Acting** (`MOH/HR/ACT/2025/041`) | 2 Oct – 1 Dec 2025 | accepts Year 1's Digital Health Needs and certifies its departmental plan (26 Nov 2025) |
| Dr Peter Kimani | Head of User Department, Digital Health | from 2 Dec 2025 | takes Digital Health over; decides Year 2's Digital Health Needs |

The supplier companies (KT-STD-001 v1.14 §8.3) register their accounts through Supplier Accounts' own commands before the first executed bid: Afya Digital Supplies Limited 1 Mar 2027 09:00, Jirani Office Supplies Limited 2 Mar 09:00, Pwani Tech Distributors Limited 3 Mar 10:00, Mlima Computer Solutions Limited 4 Mar 14:00. Every seeded person signs in with the shared fixture password (`kentender_core.seeds.constants.TEST_PASSWORD`, also in `.env.ui`).

## A3. Fiscal years and fixture instants

(Replaces KT-STD-001 §8.4 and §8.4A — Appendix C.)

| Year | Period | Role | Needs submission at the as-at instant |
|---|---|---|---|
| FY 2026/27 | 1 Jul 2026 – 30 Jun 2027 | Year 1, carried out | Closed (its intake closed 26 Nov 2025, 23:59) |
| FY 2027/28 | 1 Jul 2027 – 30 Jun 2028 | Year 2, being prepared | Closed (closed 25 Nov 2026, 23:59; on the real calendar before then it reads Open) |

| Purpose | Instants (EAT) |
|---|---|
| Strategy baseline | 1 Jul 2023, 08:00–09:15 (the Version 2 profiles keep 24–25 Nov 2026) |
| Year 1 Budget | created 2 Oct 2025 09:20, lines 15:55, submitted 16:20, approved 4 Oct 2025 11:15; external approval dated 1 Oct 2025 |
| Year 1 Needs | 25 Nov 2025, 09:00–14:00; decisions 25–26 Nov 2025 |
| Year 1 departmental plans | opened 26 Nov 2025; certified 10:30 (Digital Health) and 11:00 (HRMD); accepted 28 Nov 2025 14:00 and 14:05 |
| Year 1 Annual Plan | items formed 2 Dec 2025; funding requested 4 Dec, confirmed 5 Dec 10:00; signed 8 Dec 10:00; adopted 9 Dec 10:00; approved 10 Dec 11:00; Treasury evidence 11 Dec 14:00; published and Active 11 Dec 2025 15:00 |
| Year 1 execution | Requisitions 1 Mar – 16 Jun 2027; Tenders 16 Mar – 16 Jun 2027; bids, openings, evaluations and awards to 18 Jun 2027 09:00 |
| Year 2 Budget | created 1 Oct 2026 09:20 … approved 3 Oct 2026 11:15; external approval dated 30 Sep 2026 |
| Year 2 Needs | 24 Nov 2026, 09:00–14:00; decisions 24–25 Nov 2026 |
| Year 2 departmental plans | certified 25 Nov 2026 10:30 and 11:00; accepted 27 Nov 2026 14:00 and 14:05 |
| Year 2 Annual Plan | confirmed 4 Dec, signed 7 Dec, adopted 8 Dec, approved 9 Dec; published and Active 10 Dec 2026 15:00 |

## A4. Year 1 — FY 2026/27, carried out

### A4.1 Budget

`MOH-FIN-BUD-2026-01 (Demo)`, KES 290,000,000, approval document `MOH Approved Procurement Budget 2026-27 (Demo).pdf`, registered by Josphat Mwangi and approved by Beatrice Kamau.

| Line (generated reference) | Available to | Approved |
|---|---|---|
| Digital health infrastructure programme | Digital Health | KES 120,000,000 |
| Digital health workforce development | All departments | KES 60,000,000 |
| Ministry-wide ICT infrastructure | All departments | KES 80,000,000 |
| Office equipment for Human Resources Management and Development | HRMD | KES 30,000,000 |

### A4.2 Needs

| Reference | Title | Department | Quantity | Required by | State |
|---|---|---|---|---|---|
| NDS-MOH-2026-0001 | National digital health infrastructure upgrade | Digital Health | 1 Programme | 30 Jun 2027 | Accepted by Julia Njeri |
| NDS-MOH-2026-0002 | Clinical training laptops for digital health rollout | HRMD | 200 → 100 Each (Revision 1 returned by Dr Peter Kimani, Revision 2 accepted) | 30 Jun 2027 | Accepted |
| NDS-MOH-2026-0003 | Clinical deployment laptops for digital health rollout | Digital Health | 150 Each | 30 Jun 2027 | Accepted by Julia Njeri |

### A4.3 Departmental plans and the Annual Plan

The Digital Health plan funds Needs 0001 and 0003 and carries the Digital Health portfolio requirements; the HRMD plan funds Need 0002 and carries HRMD's. The **Annual Procurement Plan 2026/27** (`PLN-MOH-2026-001`, Treasury reference `MOH/APP/2026/001`) has 14 items, KES 236,500,000:

| Plan Item | Department(s) | Budget line | KES | Designation | Approved invitation | Delivery |
|---|---|---|---|---|---|---|
| Clinical training and deployment laptops for digital health rollout | HRMD 100 + Digital Health 150 Each | Workforce | 50,000,000 | Youth | 1 Feb 2027 | 60 days |
| National digital health infrastructure upgrade | Digital Health | Digital Health | 80,000,000 | None | 1 Mar 2027 | 30 days |
| Printers | Digital Health | Digital Health | 5,000,000 | None | 15 Feb 2027 | 30 days |
| Laboratory desktop computers | Digital Health | ICT | 9,000,000 | None | 22 Feb 2027 | 30 days |
| Medical-grade tablets | Digital Health | Digital Health | 6,000,000 | None | 15 Mar 2027 | 21 days |
| Field laptops | Digital Health | Digital Health | 7,000,000 | None | 1 Mar 2027 | 30 days |
| Core network routers | Digital Health | ICT | 25,000,000 | Women | 1 Feb 2027 | 60 days |
| Clinic desktop computers | Digital Health | Digital Health | 12,000,000 | None | 15 Mar 2027 | 21 days |
| Document scanners | HRMD | HRMD | 3,500,000 | None | 1 Mar 2027 | 21 days |
| Network switches | HRMD | ICT | 9,000,000 | None | 8 Feb 2027 | 45 days |
| UPS units | HRMD | ICT | 4,000,000 | None | 8 Mar 2027 | 21 days |
| Desktop computers | HRMD | HRMD | 12,000,000 | None | 22 Feb 2027 | 30 days |
| Monitors | HRMD | HRMD | 7,500,000 | None | 1 Mar 2027 | 21 days |
| Wireless access points | Digital Health 4,000,000 + HRMD 2,500,000 | ICT | 6,500,000 | None | 15 Feb 2027 | 30 days |

The 30% planning reservation (of what the plan procures, CFG-CHG-002 v0.13 §4.7) needs KES 70,950,000; the laptops (Youth, 50m) and the routers (Women, 25m) give 75m. Every line stays within its budget (Digital Health 110m of 120m, ICT 53.5m of 80m, HRMD 23m of 30m, workforce 50m of 60m).

### A4.4 What is carried out, and where each record stands at the as-at instant

Every record below is built through the owning module's real commands by the named people. Afya Digital Supplies Limited and Jirani Office Supplies Limited bid on T2–T5 (each bid started, filled, its physical security original recorded by Charles Mutiso, priced and signed); all four suppliers bid on T1.

| Ref | Requisition (state) | Tender | State at 18 Jun 2027, 10:00 | Next step and holder |
|---|---|---|---|---|
| T1 | Laptops — Authorised 15 Mar 2027 | Supply and delivery of business laptops (published 15 May; deadline 12 Jun 11:00) | Four bids; opening complete 12 Jun; report delivered 16 Jun 14:07; opinion signed 17 Jun 09:10; Award for Afya (KES 46,400,000) 17 Jun 10:00; Mary Wanjiku accepted 18 Jun 09:00 | The waiting period runs (delivery to Contracting 2 Jul is the AWD-DEMO-DELIVERED profile) |
| T2 | Printers — Authorised 12 Mar | Supply of printers (9 Apr – 10 May 12:00) | Two bids; opening complete 10 May; report delivered 16 Jun 11:30; Award case received | Prepare professional opinion — Charles Mutiso |
| T3 | Laboratory desktop computers — Authorised 11 Mar | Supply of laboratory desktop computers (6 Apr – 7 May 12:00) | Two bids; report delivered 4 Jun 15:00; opinion signed 17 Jun 16:00 | Decide award — Amina Hassan |
| T4 | Document scanners — Authorised 15 Mar | Supply of document scanners (16 Apr – 3 Jun 10:00) | Two bids; opening complete 3 Jun; committee appointed, members declared, opening taken up | Committee review — Grace Wambui's committee |
| T5 | Network switches — Authorised 15 Mar (25 of 30, KES 7,500,000) | Supply of network switches (14 May – 14 Jun 11:00) | Two bids; opening complete 14 Jun; evaluation prepared | Appoint the evaluation committee — Amina Hassan |
| T6 | Medical-grade tablets — Authorised 20 Apr | Supply of medical-grade tablets (24 May – **25 Jun 2027 11:00**) | Open for bids; four candidate Draft bids; six supplier clarifications received 2–17 Jun, unanswered; opening committee appointed 15 Jun | Answer the clarifications — Brian Wafula; Start opening on 25 Jun — Charles Mutiso |
| T7 | UPS units — Authorised 10 May | Supply of UPS units | Submitted 8 Jun; approved by Charles Mutiso 16 Jun 15:30 | Authorise publication — Amina Hassan |
| T8 | Wireless access points (both departments) — Authorised 15 Mar | Supply of wireless access points | Submitted 14 Jun; returned 16 Jun 09:00: "State the warranty period required from suppliers." | Correct and resubmit — Brian Wafula |
| T9 | Field laptops — Authorised 12 Apr | Supply of field laptops (10 May – 21 Jun) | Cancellation recommended by Charles Mutiso 16 Jun 14:00 (the need has ceased) | Consider cancellation — Amina Hassan |
| T10 | Desktop computers — Authorised 22 Mar | Supply of desktop computers (26 Apr – 28 Jun) | Recommended 14 Jun; cancelled by Amina Hassan 15 Jun 12:00 | Record the cancellation compliance evidence (notices, PPRA report, candidate notice; due within 14 days) — Brian Wafula |
| T11 | Core network routers — Authorised 15 Mar | Supply of core network routers (12 Apr – 30 Jun) | Recommended 14 Jun; cancelled 16 Jun 12:00; all six obligations evidenced 16 Jun 14:00–15:30 | None |
| — | Clinic desktop computers — **Submitted to Procurement** 16 Jun 11:00 | — | Awaiting authorisation | Authorise requisition — Charles Mutiso |
| — | Monitors — **Authorised** 10 Jun 11:00 | — | Not yet taken up by a Tender | Start a Tender — Brian Wafula |

Every authorised Requisition reserves its drawdown against the FY 2026/27 budget (14 reservations, KES 143,000,000, each stamped `KENTENDER_MVP_1_R1_REQ`). The laptops' latest delivery date is the plan boundary, 30 Jun 2027, and the four bids offer 22–30 Jun 2027: a Requisition refuses a later date and a Tender's bid form refuses a later offer (plan BF-04).

The laptops' opening, evaluation and award keep their own story: opening committee Charles Mutiso (chair and recorder), Brian Wafula and Beatrice Kamau (independent member); David Ouma's request to repeat the total answered; Pwani Tech Distributors Limited fails the 16 GB memory requirement automatically and Mlima Computer Solutions Limited's expired tax compliance certificate fails eligibility in the committee's evidence review; Afya is recommended at KES 46,400,000 and Jirani ranked second. The portfolio's evaluations use the same committee (Grace Wambui chair, Peter Mugo, Ruth Achieng; Brian Wafula secretary), find every bid responsive and recommend Afya.

## A5. Year 2 — FY 2027/28, being prepared

| | |
|---|---|
| Budget | `MOH-FIN-BUD-2027-01 (Demo)`, KES 160,000,000: Digital health infrastructure programme (Digital Health, 100m) and Digital health workforce development (all departments, 60m). |
| Needs | NDS-MOH-2027-0001 Health information exchange platform upgrade (Digital Health, 1 Programme, by 31 Aug 2027, accepted by Dr Peter Kimani); **NDS-MOH-2027-0002 Digital health workforce certification programme (HRMD, 1 Programme, Submitted 24 Nov 2026 — Dr Peter Kimani's review is open)**; NDS-MOH-2027-0003 Training centre audio-visual equipment (HRMD, 20 → 12 Each, returned then accepted); NDS-MOH-2027-0004 Clinical decision-support software licences (Digital Health, 150 Each, accepted). |
| Departmental plans | Digital Health (Needs 0001 and 0004) and HRMD (Need 0003), certified by Dr Peter Kimani, accepted by Mercy Kilonzo. |
| Annual Plan | `PLN-MOH-2027-001`, Treasury reference `MOH/APP/2027/001`, Active from 10 Dec 2026: Health information exchange platform upgrade (Digital Health line, 70m, invitation 3 May 2027, 30 days), Training centre audio-visual equipment (workforce line, 12m, Women, 2 Aug 2027, 45 days), Clinical decision-support software licences (workforce line, 20m, Youth, 15 Jul 2027, 60 days). KES 102m; the reservation needs 30.6m and has 32m. |
| Not there | No Requisition, Tender or reservation on FY 2027/28, ever. |

## A6. Identities and rules the world keeps

- **One site, one Procuring Entity.** `PE-MOH` is a fixture reference, not a selector or a per-record field. Nothing creates a second entity.
- **Generated references** (owner, 26 Sep 2026 and 1 Oct 2026: "Keep generated codes"). References are the ones the system generates, so a document's `TND-MOH-2027-033` is an example of the form; the seed finds records by content (a budget by its approval reference, a line by its title, an item by its title). Appendix B lists them on the test site.
- **The same commands as the screens, as the named people**, never Administrator for a business decision, each at its fixture instant. No direct write to a governed record, except the namespace stamps that let `reset` recognise canonical rows and the publication attempt's two instants.
- **Exact money and quantities.** Amounts cross module boundaries as exact decimals; quantities are whole Each where the unit is Each.
- **Lineage.** Each Plan Item's sources are the exact accepted Need revisions or direct departmental requirements; each Requisition draws on one Plan Item; each Tender consumes one authorised hand-off; each bid, opening, evaluation and award belongs to its Tender. Inclusion in the plan, authorised coverage, publication and award are separate facts.
- **Idempotent and deterministic.** A second run with the same controls creates nothing and changes nothing.
- **Fixture rules are fixture rules.** Procurement Rules are stamped `Fixture-verified — not production law`; no legal proposition is certified by the seed.

---

# Part B — How to seed it

## B1. The command

Run from the repository root (`apps/kentender_v1/`), where the `Makefile` is:

```bash
make seed-canonical SITE=<site>                                       # the full world: CURRENT=award NEXT=annual_plan
make seed-canonical SITE=<site> CURRENT=requisitions NEXT=budget      # requisitions in progress; next year's budget only
make seed-canonical SITE=<site> CURRENT=annual_plan NEXT=needs        # nothing bought yet; next year's Needs in
make seed-canonical SITE=<site> REBUILD=True                          # drop and rebuild the canonical module rows
make seed-canonical SITE=<site> WIPE=True FORCE=True RESEED=True      # from nothing: the site stage too
make seed-canonical SITE=<site> WIPE=True FORCE=True                  # wipe only: an empty, unconfigured site
make seed-canonical-dry-run SITE=<site>                               # what the clear would remove; deletes nothing
make seed-canonical-validate SITE=<site> [CURRENT=…] [NEXT=…]         # validate only; no writes
```

| Control | Year | Stages, in order | Meaning |
|---|---|---|---|
| `CURRENT` | FY 2026/27 | `annual_plan`, `requisitions`, `tenders`, `bid_submission`, `bid_opening`, `bid_evaluation`, `award` | `annual_plan` is the always-built base (budget, Needs, departmental plans, the Active plan). Each later stage takes every executed record as far as that stage (§A4.4); a record whose story stops earlier stops there. |
| `NEXT` | FY 2027/28 | `none`, `budget`, `needs`, `departmental_plans`, `annual_plan` | How far the prepared year goes; `annual_plan` is the ceiling. |

The site, its people and the Strategy are shared and always built. Both controls default to the full world. A lower stage stops each record where it leaves it, even where its dates say it would have moved on (decision D5): at `CURRENT=tenders`, the Tenders whose deadlines are before the as-at instant are closed with no bids.

**Moving a control.** A run that asks for more than the site holds builds on what is there (a prepared year taken from its departmental plans to its Annual Plan carries on from the accepted plans). A run that asks for less — or finds a Tender told without the bids it now asks for, or a world half-built by a failed run — prints `NOTICE: the canonical world is not in the shape this run builds on …` and rebuilds the canonical module records by itself, once.

**`THROUGH` (retired).** The single-year ladder (`site … planning … award`) maps for one release: up to `planning` it moves only the prepared year (`THROUGH=budget` is `CURRENT=annual_plan NEXT=budget`); a later stage moves the executed year with the prepared year complete (`THROUGH=tenders` is `CURRENT=tenders NEXT=annual_plan`). It prints a notice. **`OPEN=True` is retired:** the executed portfolio's Medical-grade tablets Tender is open past the as-at instant, so the public Tenders page always lists a Tender.

Underneath, `make` calls `bench execute`:

```bash
cd /home/midasuser/frappe-bench
bench --site <site> execute kentender_core.seeds.canonical.run --kwargs '{"current": "award", "next_year": "annual_plan", "reset": True, "validate": True}'
bench --site <site> execute kentender_core.seeds.canonical.validate --kwargs '{"current": "award", "next_year": "annual_plan"}'
```

`--kwargs` is a Python literal: `True`/`False`/`None`, never `true`/`false`. Success prints `CANONICAL_SEED_OK current=<stage> next=<stage> removed={…}`. Any failure raises, and the run — clear and reseed — is rolled back as one transaction, with one exception: submitting a bid commits at once, so a run that fails after the bids leaves a half-built Tender, which the next run rebuilds by itself.

## B2. Prerequisites

- The site's apps are migrated (`bench --site <site> migrate`).
- `developer_mode` or `allow_canonical_seed` in `site_config.json`, or `FORCE=True`. One of them is enough for every stage.
- The site is configured as `PE-MOH`, or not configured. A different Procuring Entity fails the run rather than being repaired.
- The stages from `bid_submission` on use the simulated signing, tender-box, attestation, notice-delivery and Contracting services, which answer only on a test site; a run that reaches them switches site_config `kt_bds_simulation_environment` on itself, with a notice. Never on a site that takes real bids.
- Run as `Administrator` (the `bench execute` default).

**A new server, once:** the Python packages (`bench setup requirements --python`, or `./env/bin/pip install "freezegun~=1.5.5"` — every command runs at its fixture instant under freezegun); wkhtmltopdf **0.12.6.1 (with patched qt)** exactly, for the IT-equipment Tender template; a migrate after every pull (it also re-registers a KenTender module a migrate put under Frappe). The browser-test tooling is not needed: without it the target drains the background queue with a plain bench worker. The seed installs the tender template itself and stops at once, with the reason, if the template cannot be used.

**A site reachable from the internet:** every seeded person shares the fixture password and the simulated services are on. Use such a site for demonstrations only; restrict who can reach it or disable the fixture accounts afterwards.

## B3. What the clear removes, and what it never touches

Selection is by identity, namespace or fixture e-mail domain — never "everything in a table". The dry run shows the exact list first.

**Removed by every run (`reset`):**

| Area | Rule |
|---|---|
| Budget | Every budget other than the two canonical ones (found by their approval references); on them, any version that is not Active and any reservation or commitment not stamped `KENTENDER_MVP_1_R1_REQ`. |
| Departmental Needs | Every Need outside `KENTENDER_MVP_1_R1_NDS`, with its revisions, decisions, review tasks, events and projections. |
| Strategy | Every plan outside `str-chg-001-mvp1`, and every version of the canonical plan other than Version 1. |
| Planning | Annual and departmental plans outside `KENTENDER_MVP_1_R1_PLN`. Accepting a Need starts its department's Draft plan unstamped; the planning build stamps the plans it uses. |
| Requisitions | Every Requisition not on a Plan Item of the executed year's canonical plan (the laptops and the portfolio). |
| Tenders | Every Tender not on a canonical Requisition, with its family rows, journal entries and files; the bid, opening, evaluation and award rows hanging off a removed Tender go with it (`kt_tender_removal_consumers`). |
| Loaded demo profiles | Undone first, through each module's own release (§B6); the test clock is cleared, and the run sets it again to the as-at instant at its end. |
| Leftovers | Child rows and files whose record is gone, and Planning's disposition, intake and usage projections whose Need is gone. |
| Regulatory Reference | Versions outside `KT_STD_001_S8`. |
| Legacy demo journeys | Every `Procurement Handoff Card` and `Procurement Journey`. |
| Responsibility assignments | Rows outside the canonical namespaces, or held by a fixture-domain user outside the register, and `KT_STD_001_S8` grants `site_setup.ASSIGNMENTS` no longer declares; the people who stay have their Frappe roles re-synced. |
| Users | Accounts on a fixture e-mail domain (`@moh.example.test`, `@example.test`, `@test.local`, `@moh.test`, `@moe.test`, `@example.com/.org/.net`) not in the register, with their Contact and permission rows. |
| Organisation Units, Fiscal Years | Units no canonical row points at; KenTender-created years other than 2026-2027 and 2027-2028 that nothing references. |

**Also removed by `REBUILD`:** every canonical module row, downstream first — the canonical Tenders' award, evaluation, opening and bid rows; the Tenders; every canonical Requisition (an unconsumed authorisation revoked through the real command first); both years' Planning rows (each Need's usage projection reversed); both years' Needs; both budgets; the Strategy; and the canonical supplier accounts (`KENTENDER_MVP_1_R1_BDS`), so they register again at their own instants.

**Also removed by `WIPE`:** the site stage — the Procuring Entity, units, years, Regulatory Reference, rule profiles and the register's own actors — and every row in Requisitions, Planning and Tenders; then, unless `RESEED=True`, nothing is rebuilt.

**Never touched:** a real person's account (any non-fixture domain); ERPNext-owned records (Company, UOM, ERPNext Budget and Cost Center), except that `wipe` purges `_Test Fiscal Year …` rows; the legacy reference doctypes the AUTH-ADR-001 removal phase owns (`Procuring Entity`, `Financial Year`, `PE Fiscal Year Context`, `Procuring Department`, `PE Type`); Frappe metadata.

## B4. Options

| Switch | Default | Effect |
|---|---|---|
| `current` / `CURRENT` | `award` | How far the executed year goes (§B1). |
| `next_year` / `NEXT` | `annual_plan` | How far the prepared year goes (§B1). |
| `through` / `THROUGH` | — | Retired; mapped for one release (§B1). |
| `reset` | `True` | Run the §B3 clear first. |
| `rebuild` / `REBUILD` | `False` | Also drop the canonical module rows (§B3) and rebuild. |
| `wipe` / `WIPE` | `False` | Also drop the site stage. Implies `rebuild`. |
| `reseed` / `RESEED` | `not wipe` | Reseed after the clear; `WIPE=True` alone leaves an empty site. |
| `validate` | `True` | Validate after seeding; a failure rolls the run back. |
| `force` / `FORCE` | `False` | Bypass the developer-mode guards for this run. It does not make the site a test site. |
| `commit` | `True` | Commit at the end (tests pass `False`). |

## B5. Validation — what "canonical" means

`validate(current=…, next_year=…)` raises listing every failed check:

- **Site:** `PE-MOH`; one root and the three named units; both years and no other; the funding sources; every register person with exactly the assignments and terms `site_setup.ASSIGNMENTS` lists; every unit-scoped role held by someone in force today (counting an ancestor's grant); no fixture-domain account outside the register.
- **Strategy:** the one plan, Version 1 Active, its hierarchy, indicator and target, its 2023 history.
- **Budgets:** exactly the year budgets `NEXT` asks for, each with its version, lines, owners, amounts, approval document and four lifecycle events at their instants; no reservation or commitment outside `KENTENDER_MVP_1_R1_REQ`.
- **Needs:** each year's Needs with their references, states, revisions, required-by dates and every decision by its actor at its instant; no FY 2027/28 Needs below `NEXT=needs`.
- **Planning:** each year's departmental certifications and acceptances; for an Active plan its signature, item count, each item's approved invitation, estimate basis and completion inside the year, activation instant, Treasury evidence and reference, and each funded Need Fully included; at `NEXT=departmental_plans`, a Draft Annual Plan; below it, no FY 2027/28 plan past Draft. At `CURRENT=annual_plan` also the plan's full read (items, value, eligibility, Finance, governance, publication).
- **The laptops' chain** at each stage reached: the Requisition and its hand-off (instants, package, two reservations, 13 Jun 2027 estimated completion, the HRMD Need's Revision 2); the Tender's lifecycle; the four bids at their instants; the four-bid opening; the evaluation's ranking and report delivery; the award to Mary Wanjiku's acceptance, nothing delivered to Contracting.
- **The portfolio:** every record of §A4.4 at its state for the stage reached (Requisition state, Tender status, bids, candidates and clarifications, opening, evaluation and award stage).
- **The clock:** on a test site, the test clock reads the as-at instant.

`kentender_core.tests.test_canonical_seed` covers the selection rules, the two ladders and the `THROUGH` alias, the calendar, an idempotent full run, the executed and prepared years, the two controls moving independently (a lower stage rebuilds; a higher one builds on), the validator failing closed on a stray budget, the public Tenders list, and the automatic rebuild of a half-built Tender.

## B6. Demo profiles

Profiles are named, mutually exclusive states of the canonical laptops story, built through the same commands, for walking a screen as the person named. They are not part of the canonical world. Every profile still works on the laptops chain, now on FY 2026/27 (references such as `TND-MOH-2026-002` and `PPI-MOH-2026-002` on the test site). A plain `make seed-canonical` undoes a loaded profile first and puts the test clock back on the as-at instant; each module's restore does the same.

| Module | Commands | Profiles |
|---|---|---|
| Requisitions (REQ-CHG-001 v1.11 §16.4A) | `make seed-req-profiles`, `seed-req-profile PROFILE=…`, `seed-req-profile-restore` | The thirteen `REQ-SC-*` states on the laptops item (hold, multiple requests, correction resolved, closed without change, outcome ordering, shared-line short, scope lock, sequential, lead change, revoke–consume race, precision, compatibility, open slot). A load that finds the item locked, held or changed rebuilds the executed year's Planning world through this orchestrator (`clear_canonical_modules()` then `seed(current="annual_plan")`). Proof: `procurement_requisitions.tests.test_requisitions_profiles`. |
| Bid Opening (BOP-CHG-001 v0.10) | `make seed-bop-profiles`, `seed-bop-profile PROFILE=…`, `seed-bop-profile-restore` | Fifteen `BOP-DEMO-*` moments of the laptops opening, 10–12 Jun 2027, each with the test clock at its moment; the no-bids profile uses the browser-test Tender. Full walk-through: `docs/mvp-1-r1/14_bid_opening/RUNBOOKS.md` §3. Proof: `make bop-profiles-gate`, `bop-demo-walk.spec.ts`. |
| Award (AWD-CHG-001 v0.4) | `make seed-awd-profiles`, `seed-awd-profile PROFILE=…`, `seed-awd-profile-restore` | `AWD-DEMO-OPINION` (17 Jun 09:00), `-DECISION` (10:00), `-NOTICE` (10:10), `-WAIT` (18 Jun 09:05 — the canonical world's own state), `-DELIVERED` (2 Jul 09:00). Proof: `awd-demo-walk.spec.ts`. |
| Procurement meetings (OVS-CHG-001 v0.6) | `make seed-ovs-register-branch`, `seed-ovs-register-branch-restore` | Tender B: a second department's Tender whose opening was recorded Not held, on the Bid Opening browser-test world; the register lists it once and does not count it. |

While a profile is loaded, every live page reads its moment, `seed-canonical-validate` reports the profile's stage as not canonical, and the profile's own limits apply (each module's run book states them).

## B7. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `make: No rule to make target 'seed-canonical'` | Run from `apps/kentender_v1/`. |
| `Canonical seed refused: enable developer_mode…` | Set `developer_mode` or `allow_canonical_seed`, or pass `FORCE=True`. |
| `NameError: name 'true' is not defined` | `--kwargs` takes Python literals: `True`/`False`/`None`. |
| `NameError: name 'kentender_core' is not defined` from `make seed-canonical` | Nearly always the background queue is full or another error is hidden by `bench execute`: read the traceback above it. The target drains the queue before and after; if it recurs, `make ui-queue-check FIX=1` and rerun. |
| `This site is configured as PE-XXX, not PE-MOH` | The seed never overwrites another site identity. |
| Validation fails on an assignment's term ("… a changed term needs WIPE=True") | An existing grant is returned as it is, so a term the seed changes lands only where the seed retires the old row first. The four terms the two-year world moved are retired by a plain reseed (`site_setup.SUPERSEDED_BY_TWO_YEAR_WORLD`, revoked with a reason); any other changed term needs `WIPE=True FORCE=True RESEED=True`. |
| `Set up your supplier account before starting a bid` at the bid stage | A supplier account registered before 5 Oct 2026 (18 May–3 Jun 2027) cannot act for the April 2027 bids. `REBUILD=True` removes and re-registers the canonical accounts. |
| `This idempotency key was already used with a different request` | A journal entry left by an older world; `REBUILD=True` (or `WIPE`). Report it if it recurs on current code. |
| `REQ_PRODUCT_UNSUPPORTED` / `TND_PRODUCT_UNSUPPORTED` | An item is not off-the-shelf IT equipment in a category the module admits (§A1). |
| `The canonical bid evaluation signs with the test attestation service…` | The site is not a test site; the run switches it on itself from `bid_submission` (§B2). |
| Every live page shows 18 June 2027 | Expected on a test site: the world is read as at that instant. A demo profile moves it to the profile's moment; restore or reseed puts it back. |
| `Youth is not supported by the installed IT-equipment Tender format` | The tender template is missing or unusable — nearly always the wrong wkhtmltopdf build (§B2). |
| `No module named 'frappe.core.doctype.supplier_business_profile'` | Pull and migrate: the migrate repairs the module registration. |
| `TimestampMismatchError … BDS Test Environment Controls` | Two seed runs at once on one site; wait for the other, then rerun. |
| After `make ui-budget-gate`, validation fails on the budget lines or the reservations | The Budget browser specs work on the canonical budgets; run `REBUILD=True`. |
| `PLN_ITEM_SCOPE_LOCKED` or "already has an authorised Requisition" | An item's scope lock is permanent; `REBUILD=True` once. |

## B8. Other seed entry points

- `make seed-kentender-mvp-v1` (the multi-PE-era pack) still creates a second Procuring Entity and legacy personas; do not run it on a canonical site. `make seed-canonical` removes them again.
- Module browser gates and Python test worlds seed their own isolated fixtures (namespaced or on isolation years); they are disposable and `make seed-canonical` removes them. Tests write real rows with no rollback: run them on the test site and reseed after.
- `bench execute kentender_core.seeds.site_setup.run` is the site stage alone, without a clear.
- `make awd-seams-gate` builds a persistent Evaluation test world; reseed afterwards.

---

# Part C — How a module adds to the world

When a module builds a seeded story (decision D20, 1 Oct 2026: "The seed should exercise all stages as they are built"):

1. **Place it on a ladder.** A preparation module (budget, Needs, planning) belongs to both years: give its seed a per-year spec (`calendar.YEAR1`/`YEAR2`), Year 1 the same journey 364 days earlier unless its dates must differ, every planned date inside its own year. An execution module belongs to the executed year only: add a stage to `canonical.CURRENT_STAGES` after the stage it consumes, and never touch FY 2027/28.
2. **Use the real commands as the named people, at fixture instants** (`kentender_core.seeds.clock.at`, or the module's own trusted-clock flag). No direct governed writes; no actor created inside a module seed — add people to KT-STD-001 §8.3 and `site_setup.ACTORS`/`ASSIGNMENTS`.
3. **Make it idempotent and recognisable.** Stamp the module's canonical namespace and add it to `canonical.CANONICAL_NAMESPACES`; extend `collect_non_canonical()` with the disposable-row rule and `clear_canonical_modules()` with the canonical clear, downstream first (a module hanging off a Tender registers `kt_tender_removal_consumers`). If a later stage's records consume yours, make `canonical.world_ahead()` recognise them so a lower `CURRENT` rebuilds.
4. **Give the portfolio its states.** For a stage after `tenders`, decide which portfolio records reach it and where they stop at the as-at instant (`portfolio.PORTFOLIO`), so Home and Analytics see the module's work in several states at once; extend `portfolio.validate_portfolio()` and the binding table (`portfolio.binding_rows()`, Appendix B).
5. **Validate it.** Add the stage's facts to `canonical.validate()` (the module's own `validate_…_seed()`), extend `kentender_core.tests.test_canonical_seed`, run it on the test site, then run the full command on a dirtied site and compare the dry run with the removal report.
6. **Demo profiles**, if any: their release in `canonical.release_demo_profiles()`, a restore that puts the test clock back on the as-at instant, and a row in §B6.
7. **Keep this document true:** Part A's tables, §B5 and Appendix B; the `make help` line and the Makefile comment; the module docstring of `canonical.py`; the seeds README and the command card in `CLAUDE.md`.

---

# Appendix A — Carry-over register

Every rule of the two retired documents, and what it became. **Carried**: stated here, changed only as noted. **Superseded**: replaced by a decision this document records. **Dropped**: no longer applies, with the reason. Section numbers are the retired documents'.

## A.1 SEED-001 v1.4 (Harmonized End-to-End Fixture)

| SEED-001 rule | Disposition | Where / why |
|---|---|---|
| Front matter — OVS amendment: SEED-OPS v1.21 decisions D3, D4, D7, D8, D23; Julia's 2026 term expired at June 2027 instants | Carried, dates moved | §A2 (Julia's term is now Oct–Dec 2025, expired at the as-at instant); D3 §A6; D4 §A2; D7 and D8 below; D23 §A4.4 |
| One site = one Procuring Entity `PE-MOH`; KEBS examples are template-curation evidence only | Carried | §A6 |
| §1.1 source documents and §1.1 "actual approval records govern" | Dropped | Version citations of September 2026; this document cites its own basis (control table) |
| §1.2 BASE / READY — visual / READY — integrated; BASE canonical | Superseded | Owner D7 (26 Sep 2026): "Ready one is canonical". The canonical plans are Active with their reservations met (§A4.3, §A5); BASE and the visual variant remain Planning's isolated profiles and screens |
| §1.3 fixture rules labelled `Fixture-verified — not production law`, never `Verified`; production must not accept fixture configuration | Carried | §A6 |
| §1.3 executable manifest (scenario, versions, build, timezone, FY bounds, rule ids, actors, instants, results, hashes) | Carried in part | The validator and the run report record scenario (controls), instants and results; artifact hashes are not recorded — an open item for the owner |
| §1.3 "The source pack labels the period FY 2027/28 while using the dates below … an open CFG/SEED reconciliation issue" | Superseded | Resolved by the two-year world: the executed chain is FY 2026/27 and every planned date fits it (§A1, D8) |
| §2 lineage: two laptop Needs → one combined item (250 Each, KES 50m, HWD line, HRMD 20m + DHI 30m allocations) → one Requisition → one Tender | Carried, year moved | §A4.2–§A4.4 (Year 1; references generated, e.g. NDS-MOH-2026-0002/0003, PLN-MOH-2026-001) |
| §2 infrastructure Need and item in the same plan | Carried | §A4.3 |
| §2 plan inclusion, coverage, publication and fulfilment are separate facts | Carried | §A6 |
| §3.1 actors and their authority (Grace both units; Julia acting DHI; Peter HRMD and DHI from December; Mercy; Josphat both capacities; Charles; Amina; Daniel Rotich; Brian; Naomi) | Carried, dates moved | §A2 (Julia 2 Oct–1 Dec 2025, Peter DHI from 2 Dec 2025) |
| §3.2 the three accepted Needs' facts (titles, quantities, units, departments, acceptance by Julia and Peter) | Carried, dates moved | §A4.2: Required by 30 Jun 2027 (was 31 Aug / 31 Dec 2027 — Needs refuse a date outside their year); acceptances 26 Nov 2025 |
| §3.2 infrastructure acceptance instant left open | Carried as fixed | Accepted 25 Nov 2025 14:00 by Julia Njeri (the seed's instant; before the Digital Health certification) |
| §3.3 certification and acceptance chronology; DPP intake open to 30 Nov 23:59 | Carried, moved 364 days | §A3: 26 Nov 2025 10:30/11:00, accepted 28 Nov 14:00/14:05, intake to 1 Dec 2025 23:59 |
| §3.3 Julia acting from an expired page is refused | Carried | Validation of assignments and the module's own tests |
| §3.4 Strategy objective and approval-time snapshot | Carried | §A3 (Strategy baseline); the Planning approval takes the snapshot |
| §3.5 Budget `MOH-BUD-2027-001`, two lines, KES 160m | Superseded for Year 1, carried for Year 2 | §A4.1 (Year 1: 290m, four lines — the executed portfolio needs the money, plan BF-06); §A5 (Year 2: the 160m budget) |
| §3.5 30% arithmetic on the KES 160m budget | Superseded | Owner D8 (26 Sep 2026): the plan's eligible value is the denominator (§A4.3, §A5) |
| §3.5 exact decimal money and quantities | Carried | §A6 |
| §3.6 item boundaries (laptops 31 Dec 2027, REQ 30 Sep 2027, completion 24 Sep 2027) | Superseded | D8: boundary 30 Jun 2027, approved invitation 1 Feb 2027, completion 13 Jun 2027; the latest delivery is 30 Jun 2027 (a Requisition refuses a date after the boundary, plan BF-04) |
| §3.6 plan title "Annual Procurement Plan 2027/28" | Superseded | Year 1's plan is the Annual Procurement Plan 2026/27 (§A4.3); Year 2 keeps its own (§A5) |
| §3.7 governance chronology and Treasury dispatch `MOH/APP/2027/001` | Carried, moved 364 days for Year 1 | §A3; Year 1 Treasury reference `MOH/APP/2026/001`, Year 2 keeps `MOH/APP/2027/001` |
| §3.7 synthetic Treasury evidence bytes, labelled; publication by the sandbox adapter, labelled simulation | Carried | `Treasury-dispatch-evidence-example.pdf` per plan version |
| §4.1–§4.3 Requisition identity, drawdown lines, two reservations, scope lock, 1/8/15 March 2027 | Carried | §A4.4 (references generated: REQ-MOH-2026-002-001) |
| §5.1–§5.3 Tender identity, one consolidated schedule line, lifecycle (prepare 20 Mar, approve 20 Apr, publish 15 May) | Carried | §A4.4 |
| §5.2 baseline dates (invitation 15 May …) | Superseded | D8: the laptops' approved invitation is 1 Feb 2027; the actual publication (15 May) is 103 days later — Baseline lateness |
| §5.2 "No opening/evaluation/award actual generated by this seed" | Superseded | Owner D20 (1 Oct 2026): "The seed should exercise all stages as they are built" — the opening, evaluation and award are seeded (§A4.4) |
| §5.3 only the supported invitation event writes an actual; duplicates harmless | Carried | Planning records the Tender's invitation actual |
| §6 naming (Head of Procurement Function; PlanPublication; Submission/Version counters; no KEBS identities) | Carried | §A2, §A6 |
| §7.1 deterministic execution through the real commands, isolated worlds, failure on conflicting data | Carried | §A6, Part B |
| §7.2 coordinated owner updates | Dropped | Historical coordination list of September 2026; Appendix C names what remains |
| §7.3 completion claims (specified/approved/implemented/verified) | Carried | Control table: approval does not establish implementation or verification |
| §8 SEED-AC-001 … SEED-AC-030 | Carried in substance, renumbered | §B5 is the acceptance contract; AC-008–010 (BASE blocked) superseded by D7; AC-015/016 dates per D8 |
| §9 change register SEED13-CHG-001…023 | Dropped | History of v1.3; retained in the retired file |
| §10 dispositions | Superseded | Infrastructure acceptance fixed (above); FY bounds resolved (D8); the rest are module follow-ups |

## A.2 SEED-OPS-001 v1.25 (Canonical Site Seed Runbook; v1.24 approved)

| SEED-OPS-001 rule | Disposition | Where / why |
|---|---|---|
| Controlling decision: one canonical world; everything else disposable; one command; validates or fails | Carried | Controlling decision above |
| Approval records and source-status paragraphs v1.19–v1.25 | Dropped | History; retained in the retired files |
| §1 the command, `THROUGH` ladder, examples | Superseded | §B1 (`CURRENT`/`NEXT`; `THROUGH` mapped for one release) |
| §1 one transaction; bid submissions commit at once; a half-built Tender rebuilds itself | Carried | §B1 |
| §1.1 prerequisites (migrate, permission, `PE-MOH`, Administrator, test site from `bid_submission`) | Carried | §B2 |
| §1.1 fixture password for the register, Jane Wanjiku and the supplier people | Carried | §A2 |
| §1.2 a new server (packages, wkhtmltopdf 0.12.6.1, migrate, permission, no test tooling; what the seed does for itself; internet-facing sites) | Carried | §B2 |
| §1.3 `OPEN=True` (v1.25, never approved) | Dropped | Retired 5 Oct 2026: the executed portfolio's Medical-grade tablets Tender is open past the as-at instant (§A4.4, §B1) |
| §2 stage table (what each stage creates) | Superseded | Part A states the world per year and record; §B1 the stages |
| §2 every stage idempotent; never the legacy multi-PE orchestrator | Carried | §A6, §B8 |
| §2 generated references; EVL/AWD "tender 033" as an example of the form (D19) | Carried | §A6 |
| §2 the Evaluation people hold no standing responsibility; Esther Njeri holds Evaluation Technical Support (v1.18) | Carried | KT-STD-001 §8.3; §A2 |
| §2 four bids (v1.21): suppliers, people, prices, failures, ranking, notices | Carried | §A4.4 (accounts now registered 1–4 Mar 2027; offered deliveries 22–30 Jun 2027) |
| §3.1 what the clear removes | Carried, updated | §B3 (canonical Requisitions are every one on the executed plan; canonical Tenders every one on those; usage projections swept; a rebuild removes the canonical supplier accounts) |
| §3.1 the canonical world has no test clock | Superseded | D1: a test site reads the as-at instant (§A1) |
| §3.2 never touched | Carried | §B3 |
| §4 options | Carried, updated | §B4 |
| §5 validation | Carried, updated | §B5 (two years, the portfolio, the clock; the award stops at the acceptance, plan BF-10) |
| §6 adding the next module stage | Superseded | Part C |
| §7 troubleshooting rows | Carried where they still apply | §B7. Dropped: rows for faults fixed on 4 Oct 2026 or earlier whose cause no longer exists (`esbuild`, `freezegun` message, guard refusals, `lead_org_unit`, the evaluation presence lapse, the `OPEN=True` rows, the v1.3–v1.5 `wipe` rows, the v1.20 preparation-minimum patch) — each is in the retired file's history |
| §8 other seed entry points | Carried | §B8 |
| §9 Requisitions demo profiles | Carried | §B6 |
| §9A Bid Opening demo profiles | Carried | §B6 (restore now puts the as-at clock back) |
| §9B Award demo profiles | Carried | §B6 (`AWD-DEMO-WAIT` is the canonical world's own state; restore sets the as-at clock) |
| §9C Tender B for the Procurement meetings register; the clock for each persona case | Carried in part | §B6. The persona-clock table (Peter's Digital Health assignment from 1 Dec 2026; Julia's term to 30 Nov 2026) is superseded by §A2's dates |
| §10 change log | Dropped | History; retained in the retired files |
| §11 D1 Strategy title without "(Demo)" | Carried | Decided 26 Sep 2026 |
| §11 D2 2023 Strategy authority backdated | Carried | §A2 |
| §11 D3 generated references | Carried | §A6 |
| §11 D4 Peter heads the Directorate | Carried, date moved | §A2 (from 2 Sep 2025) |
| §11 D5 Grace as HRMD Head of User Department in the canonical world | Carried as open | Still granted (KT-STD-001 §8.3 regression fixture); owner decision pending |
| §11 D6 Need 0004 submission time | Carried as open | Year 2's Need 0004 is submitted 10:45 |
| §11 D7 READY canonical | Carried | §A4.3, §A5 |
| §11 D8 130m denominator | Carried, generalised | The plan's own value each year (§A4.3, §A5) |
| §11 D9–D14 (rule verification by direct stamp; rule window; disposal intake; Company; UOMs; schedule content) | Carried as open | Unchanged by this document |
| §11 D15 site configuration and grants at fixture instants | Superseded in part | The dated grants follow §A2; site configuration still happens at seeding time |
| §11 D16–D18 | Carried as open | Unchanged |
| §11 D19–D22 | Carried | Decided 1 Oct 2026 |
| §11 D23–D24 four bids and the suppliers' names | Carried | §A4.4; the names stand in KT-STD-001 v1.14 |
| §11 "not yet done" list (Planning back-stamping …) | Superseded in part | Every canonical Planning step now runs under the frozen clock; the isolated profiles' back-stamping and the two old Requisitions profiles remain open |

---

# Appendix B — Binding table (generated references on the test site)

The executed year's records as `kentender_core.seeds.portfolio.binding_rows()` reads them on `kentender-test.local` after a full seed. References are generated, so another site may number them differently; titles, states and holders are the same everywhere. The Home and Analytics fixtures are illustrative (HOME-CHG-001 v0.6 §13, ANL-CHG-001 v0.8 §13), so a design's own number (for example "Tender 042") maps to the record that carries its state, not to a reference.

Generated 5 October 2026 from a full seed (`CURRENT=award NEXT=annual_plan`), read as at 18 June 2027, 10:00 EAT.

| Ref | Plan Item | Requisition | Tender | State | Serves |
|---|---|---|---|---|---|
| T1 | Clinical training and deployment laptops for digital health rollout (PPI-MOH-2026-002) | REQ-MOH-2026-002-001 | TND-MOH-2026-002 | Submission period ended; opening Opening complete; evaluation Report sent; award Waiting to proceed | ANL Award bucket and award amount; HOME H12 recently completed (Amina's award decision); AWD-DEMO-* profiles |
| T2 | Printers (PPI-MOH-2026-003) | REQ-MOH-2026-003-001 | TND-MOH-2026-003 | Submission period ended; opening Opening complete; evaluation Report sent; award Opinion | HOME H2/H10 Prepare professional opinion (Charles); ANL 044 shape |
| T3 | Laboratory desktop computers (PPI-MOH-2026-004) | REQ-MOH-2026-004-001 | TND-MOH-2026-004 | Submission period ended; opening Opening complete; evaluation Report sent; award Decision | HOME H12 Decide award (Amina) |
| T4 | Document scanners (PPI-MOH-2026-009) | REQ-MOH-2026-009-001 | TND-MOH-2026-009 | Submission period ended; opening Opening complete; evaluation Reviewing | HOME H10–H12 committee review outstanding and evaluation deadline; ANL 043 shape |
| T5 | Network switches (PPI-MOH-2026-010) | REQ-MOH-2026-010-001 | TND-MOH-2026-010 | Submission period ended; opening Opening complete; evaluation Preparing | HOME H12 Appoint the evaluation committee (Amina) |
| T6 | Medical-grade tablets (PPI-MOH-2026-005) | REQ-MOH-2026-005-001 | TND-MOH-2026-005 | Published — open; opening Awaiting deadline | Anonymous /tenders list; HOME H1 clarification, H3 addendum guard, H8 paging; H10 Start opening (Coming up); ANL Open bucket |
| T7 | UPS units (PPI-MOH-2026-011) | REQ-MOH-2026-011-001 | TND-MOH-2026-011 | Approved | HOME H1 completed submission, H10 waiting on Amina, H12 Authorise publication |
| T8 | Wireless access points (PPI-MOH-2026-014) | REQ-MOH-2026-014-001 | TND-MOH-2026-014 | Draft | ANL preparation bucket and warranty outstanding matter (041 shape); combined Digital Health + HRMD item |
| T9 | Field laptops (PPI-MOH-2026-006) | REQ-MOH-2026-006-001 | TND-MOH-2026-006 | Published — open | HOME H1 waiting on Amina, H12 Consider cancellation |
| T10 | Desktop computers (PPI-MOH-2026-012) | REQ-MOH-2026-012-001 | TND-MOH-2026-012 | Cancelled | HOME H1/H12 cancellation compliance evidence pending (034 shape) |
| T11 | Core network routers (PPI-MOH-2026-007) | REQ-MOH-2026-007-001 | TND-MOH-2026-007 | Cancelled | ANL Closed bucket, cancellation complete (046 shape); Women reservation |
| R-clinic | Clinic desktop computers (PPI-MOH-2026-008) | REQ-MOH-2026-008-001 | — | Submitted to Procurement | HOME H10 Authorise requisition (Charles); ANL R-A |
| R-monitors | Monitors (PPI-MOH-2026-013) | REQ-MOH-2026-013-001 | — | Authorised | ANL requisition authorised but not taken up (T2 transition open) |

Notes:

- T9's "Consider cancellation" (Amina Hassan) is not on her work list. The recommendation is recorded and the Tender shows it, but Tenders' direct recommendation command opens no Accounting Officer task; only the addendum route opens one. This is a Tenders module gap found while checking the binding, not a seed fault. It is reported to the Project Owner.
- FY 2027/28 has no executed records: its budget, needs, departmental plans and Annual Plan (PLN-MOH-2027-001) are listed in Part A.


# Appendix C — Required correction in KT-STD-001 (the Project Owner's document)

Replace §8.4 (Fiscal years) and §8.4A (Fixture instants) with:

> **8.4 Fiscal years and fixture instants.** The shared fixture is two financial years read as at 18 June 2027, 10:00 EAT: FY 2026/27 (1 Jul 2026 – 30 Jun 2027), the year being carried out, and FY 2027/28 (1 Jul 2027 – 30 Jun 2028), the year being prepared. SEED-002 Part A states each year's records and every fixture instant; a change unit takes its fixture dates from there. (v1.22 read: §8.4 listed FY 2026/27 Closed and FY 2027/28 Open, closing 25 Nov 2026 23:59 EAT; §8.4A listed one window per module composing "one coherent year".)

and in §8.3, the dated terms: Julia Njeri, Head of User Department (Acting), Digital Health, 2 Oct – 1 Dec 2025; Dr Peter Kimani, Head of User Department, Digital Health from 2 Dec 2025 and the Directorate from 2 Sep 2025; Samuel Otieno's expired term 2 Jan – 1 Sep 2025.

# Appendix D — New content for review and open questions

**New content, not from an approved source** (each was accepted in the two-year proposal or its answers, except where marked):

- The document identifier SEED-002 and its title (new here).
- The as-at instant and the 364-day shift (D1, D8).
- Year 1 Required by dates and approved invitation dates (D8); the Year 1 budget of KES 290m on four lines (plan BF-06; new here).
- The Year 2 Need titles (D10) and their descriptions, quantities and amounts (new here); Year 2's item values, designations and approved invitation dates (new here).
- The portfolio's items, quantities, amounts, lines, designations and approved invitation dates; the IT substitutes for the design titles that are not IT equipment (plan BF-05; new here); the Tender titles, security amounts and dates; the bids' models, prices and security references; the six T6 questions; the cancellation reasons and evidence references (new here).
- The laptops' latest delivery date and the four bids' offered dates (plan BF-04; new here).
- The supplier accounts' registration instants (plan BF-09; new here).

**Questions for the Project Owner**, each with a recommendation:

1. *Approve SEED-002 as the replacement of SEED-001 and SEED-OPS-001?* Recommended: yes; the retired files move to `20_seed_data/retired/` and every link changes in the same step.
2. *Apply Appendix C to KT-STD-001?* Recommended: yes, in the next KT-STD-001 version.
3. *Record artifact hashes in a run manifest (SEED-001 §1.3)?* Recommended: not now; the validator's report and the commit identify a run.
4. *D5 — move Grace Wanjiku's HRMD Head of User Department grant to the isolated permissions fixture?* Recommended: yes, in a later change; it does not affect the two-year world.
