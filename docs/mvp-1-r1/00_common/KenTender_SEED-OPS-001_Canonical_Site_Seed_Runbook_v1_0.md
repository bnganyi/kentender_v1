# SEED-OPS-001 — Canonical Site Seed Runbook

| Control | Value |
|---|---|
| Document ID | SEED-OPS-001 |
| Version | 1.1 |
| Date | 9 September 2026 |
| Status | Maintained — update whenever a module stage is added to the seed or the canonical world changes |
| Purpose | The one command that resets a KenTender site to the canonical seed world and how to keep it truthful as modules land |
| Standards | KT-STD-001 v1.3 §8 (shared fixture register, §8.6 seed execution rules, §10 prohibited shortcuts); SEED-001 v1.0 (harmonized end-to-end fixture) |
| Owner | `kentender_core` (`kentender_core/kentender_core/seeds/canonical.py`) |

**Controlling decision:** a KenTender site has exactly one canonical world — the KT-STD-001 §8 configuration and the SEED-001 module chain. Everything else on the site (browser-test fixtures, isolated test profiles, hand-made drafts, demo journeys from retired seed packs) is disposable. One command removes the disposable rows and reseeds the canonical ones, progressively, one module stage at a time, and refuses to report success unless the result validates.

---

## 1. The command

Run from the repository root (`apps/kentender_v1/`), never from the bench root — the `make` targets live in this repository's `Makefile`.

```bash
cd /home/midasuser/frappe-bench/apps/kentender_v1
make seed-canonical SITE=kentender.midas.com THROUGH=budget
```

Companions:

```bash
make seed-canonical-dry-run SITE=kentender.midas.com    # list what would be removed; deletes nothing
make seed-canonical-validate SITE=kentender.midas.com   # validate the canonical world only; no writes
```

Underneath, the targets call the `bench execute` entry points directly, which is the form to use for the optional switches in §4:

```bash
cd /home/midasuser/frappe-bench
bench --site kentender.midas.com execute kentender_core.seeds.canonical.run \
  --kwargs '{"through": "budget", "reset": true, "validate": true}'
bench --site kentender.midas.com execute kentender_core.seeds.canonical.dry_run
bench --site kentender.midas.com execute kentender_core.seeds.canonical.validate \
  --kwargs '{"through": "budget"}'
```

Success prints one line, `CANONICAL_SEED_OK through=<stage> removed={…}`, followed by the JSON report. Any failure raises, and the whole run — clear and reseed — is rolled back as one transaction; the site is never left half-cleared.

### 1.1 Prerequisites

- The site's apps are migrated (`bench --site <site> migrate` clean).
- `developer_mode` is on in `site_config.json`, or `allow_canonical_seed` is set there, or `"force": true` is passed. The seed refuses otherwise: it deletes rows and, in developer mode, sets the fixture password on the register's actors.
- The site is configured as `PE-MOH` or not configured at all. A site configured as a different Procuring Entity fails the seed rather than being repaired (KT-STD-001 §8.6).
- Run it as `Administrator` (the `bench execute` default).

---

## 2. What "canonical" means, per stage

Stages are cumulative and ordered. `THROUGH=<stage>` seeds that stage and every stage before it.

| Stage | Seed of record | What it creates or converges | Seeded by |
|---|---|---|---|
| `site` | KT-STD-001 v1.3 §8.1–§8.5, CFG-CHG-002 v0.9 | Site Procuring Entity `PE-MOH`; the root unit and the three §8.2 units by name (codes are server-generated `OU-MOH-{n}`, never the mnemonic codes); ERPNext Company (an existing one is kept); Fiscal Years 2026-2027 and 2027-2028 with the Needs and DPP intake windows; Requirement Type and Procurement Method catalogues; the `Government of Kenya` Funding Source; the FY 2027/28 Regulatory Reference; the ten enabled UOMs; the §8.3 actors and their responsibility assignments (Grace, Peter, Julia acting, Mercy, Samuel expired, Naomi, Esther, Alfred, Josphat, Beatrice) | `kentender_core.seeds.site_setup.run` |
| `strategy` | STR-CHG-001 v1.7 §14, SEED-001 §3.4 | The single MOH strategic plan, hierarchy, indicator and target, driven through the governed commands as Esther and Alfred; Version 1 Active | `kentender_strategy.seeds.kentender_mvp_v1_strategy.upsert_kentender_mvp_v1_strategy` |
| `budget` | BUD-CHG-001 v1.6 §15.3–§15.4, SEED-001 §3.5 | `MOH-BUD-2027-001` Version 1 Active, `MOH-BL-DHI-2027` (Digital Health, KES 100m) and `MOH-BL-HWD-2027` (Entity-wide, KES 60m), registered by Josphat and approved by Beatrice through the real commands; no reservation (§15.4A's reservation exists only once a Requisition creates it); no isolated profiles (§15.5/§15.6 are created and removed by the tests that need them) | `kentender_budget.seeds.kentender_mvp_v1_portfolio.upsert_kentender_mvp_v1_portfolio(include_test_edges=False)` |
| `needs` | NDS-CHG-001 v1.6 §14.3, SEED-001 §3.2–§3.3 | The four default MOH Needs (`NDS-MOH-2027-0001..0004`), driven through the governed commands as Grace/Peter/Julia; `NDS-MOH-2027-0001/0003/0004` Accepted, `NDS-MOH-2027-0002` Submitted | `kentender_procurement.departmental_needs.seeds.kentender_mvp_r1.upsert_departmental_needs` |
| `planning` | PLN-CHG-001 v1.13 §14, SEED-001 §3.6 | `PLN-MOH-2027-001` Version 1 Active — the pre-existing single-department item plus the harmonized two-department combined item (2 items, KES 130,000,000), driven through the real commands as Grace/Peter/Mercy/Josphat/Amina/Daniel; no reservation (holds none by design) | `kentender_procurement.procurement_planning.seeds.kentender_mvp_v1.upsert_planning_base` |
| `requisitions` | REQ-CHG-001 v1.6 §16, SEED-001 | The Authorised Requisition on the one eligible combined Plan Item (§16.4 fixture 4's exact timeline), driven through the real commands as Grace/Peter/Charles; both Budget reservations opened by the real command, stamped `KENTENDER_MVP_1_R1_REQ` by this orchestrator itself (the sibling module has no fixture concept and must not write Budget's doctype directly) | `kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1.upsert_requisitions_base` |
| `tender_preparation` | TPR-CHG-001 v0.6 §16 | A Tender approved for publication on the Requisition's handoff, walked through prepare→readiness→submit→return→correct→resubmit→approve→acknowledge as Brian/Charles; stamps the handoff's consumption instant back onto Requisitions and a real `actual_invitation_date` onto Planning's combined item (FU-16 — expected, not drift) | `kentender_procurement.tender_preparation.seeds.kentender_mvp_v1.upsert_tender_preparation` |

Every stage's seed is idempotent: a second run creates nothing and changes nothing (KT-STD-001 §8.6), which the validator and `kentender_core.tests.test_canonical_seed` both assert. Every stage calls its owning module's canonical-shaped seed function directly — never `kentender_core.seeds.kentender_mvp_v1.orchestrator` (the legacy multi-PE-era pack) — so seeding through any stage never creates `PE-CGKIS` or a second Procuring Entity.

Because `requisitions` and `tender_preparation` each consume exactly one Plan Item / Requisition from the stage before them, seeding past `planning` legitimately advances that earlier stage's own state in ways its own module validator (written for "seeded alone") cannot see coming — `validate(through=…)` accounts for this (§5).

---

## 3. What the clear removes, and what it never touches

Selection is by explicit identity, namespace or fixture e-mail domain — never "everything in a table". `make seed-canonical-dry-run` shows the exact list before anything is deleted.

### 3.1 Removed

| Area | Rule |
|---|---|
| Budget | Every Procurement Budget other than `MOH-BUD-2027-001`, with its versions, lines, reservations, commitments, audit events and attachments. On the canonical budget: any version that is not Active, and any Funding Reservation not stamped `KENTENDER_MVP_1_R1_REQ` (§8.6 — that stamp is this orchestrator's own evidence of the canonical Requisition, not a stray). |
| Departmental Needs | Every Need (with its versions, decisions, review tasks, events, projections) whose `fixture_namespace` is not `KENTENDER_MVP_1_R1_NDS`, including unstamped rows. Review tasks are "retained permanently" through the document API, so the purge uses the module's own raw-delete mechanism (`departmental_needs.seeds.playwright_ui_fixtures.purge_fixture_needs`). |
| Procurement Planning | Annual Plans and Departmental Plans (and their submissions, validations, items, allocations, finance and governance rows) outside `KENTENDER_MVP_1_R1_PLN`, through `procurement_planning.seeds.kentender_mvp_v1.clear_planning_fixture_rows`. |
| Procurement Requisitions | Requisitions carry no `fixture_namespace` column; "canonical" means rows tied to the one eligible combined Plan Item. `include_canonical=False` on `procurement_requisitions.seeds.clear.clear_requisition_fixture_rows` — run unconditionally on every `reset`, not gated on a namespace check — removes only Playwright-owned residue, so the canonical Requisition survives. |
| Tender Preparation | Every `Prepared Tender` (and its versions, decisions, tasks, handoffs) whose `fixture_namespace` is not `KENTENDER_MVP_1_R1_TPR`, through `tender_preparation.seeds.clear.clear_tender_fixture_rows`. |
| Regulatory Reference | Versions outside the `KT_STD_001_S8` namespace (isolation-year references from test fixtures), through the document's own `kt_fixture_purge` flag. |
| Legacy demo journeys | Every `Procurement Handoff Card` and `Procurement Journey` (the retired stable-platform Works demo). |
| Responsibility assignments | Rows outside the canonical namespaces (`KT_STD_001_S8`, `KENTENDER_MVP_V1`, `KENTENDER_MVP_1_R1_NDS`, `KENTENDER_MVP_1_R1_PLN`, `KENTENDER_MVP_1_R1_REQ`, `KENTENDER_MVP_1_R1_TPR`, `str-chg-001-mvp1`) or held by a fixture-domain user who is not in the §8.3 register. |
| Users | Accounts on a fixture e-mail domain (`@moh.example.test`, `@example.test`, `@test.local`, `@moh.test`, `@moe.test`) that are not in the §8.3 register — any user type, with their Contact, User Permission, User Scope Assignment and notification rows. |
| Organisation Units | Units that no canonical row points at (the root, the register's assignments, canonical Needs and Departmental Plans, and Budget Line Versions keep theirs, with ancestors), children before parents. |
| Fiscal Years | KenTender-created years other than 2026-2027 and 2027-2028 that nothing references any more (the isolation years test suites create) — recomputed fresh after every other deletion in the same clear, since a year can go from referenced to unreferenced as a side effect of them (its own Annual Plan or stray Budget going with it). |

### 3.2 Never touched

- A real person's account: any user on a non-fixture domain, whatever its name.
- ERPNext-owned records: `_Test Fiscal Year …` rows, Company, UOM, ERPNext `Budget`/`Cost Center` (KT-STD-001 §10; BUD-CHG-001 §18).
- The pre-cutover legacy reference doctypes owned by AUTH-ADR-001's removal phase RM-1xx: `Procuring Entity`, `Financial Year`, `PE Fiscal Year Context`, `Procuring Department`, `PE Type` (KT-STD-001 §10: legacy records go with the cutover, not with a module cleanup).
- Frappe Roles, Module Defs, Pages, Workspaces and other metadata.

---

## 4. Options

| Switch | Default | Effect |
|---|---|---|
| `through` / `THROUGH` | `tender_preparation` | Last stage to seed (`site`, `strategy`, `budget`, `needs`, `planning`, `requisitions`, `tender_preparation`). |
| `reset` | `true` | Run the §3.1 clear before seeding. `false` seeds only. |
| `rebuild` | `false` | Also drop the canonical module rows before seeding — Tender Preparation, then Requisitions, then Planning, then Needs, then Budget, then Strategy (downstream first, since each consumes the one before it) — and rebuild from scratch. Use it when a canonical record is wrong, not merely missing. Stages beyond `through` are cleared but not reseeded. |
| `validate` | `true` | Run §5 after seeding; a failure rolls the run back. |
| `force` | `false` | Bypass the developer-mode guard. |
| `commit` | `true` | Commit at the end (tests pass `false`). |

---

## 5. Validation

`validate(through=…)` asserts the canonical facts for every stage up to `through` and raises listing every failed check. It is the definition of "the site is canonical":

- `site`: the site Procuring Entity is `PE-MOH`; exactly one root unit and exactly one unit per §8.2 name, four units in total; both site fiscal years exist and no other non-`_Test` fiscal year does; the funding source is Available; every §8.3 actor exists with the assignments `site_setup.ASSIGNMENTS` lists; no fixture-domain account outside the register.
- `strategy`: exactly one plan in the `str-chg-001-mvp1` namespace with exactly one Active version.
- `budget`: `MOH-BUD-2027-001` is the only budget, on FY 2027-2028, with exactly one version (`MOH-BUD-2027-001-V1`, Active); `MOH-BL-DHI-2027` approved 100,000,000 and `MOH-BL-HWD-2027` approved 60,000,000 and Entity-wide; no Funding Reservation and no Procurement Commitment outside `KENTENDER_MVP_1_R1_REQ`.
- `needs`: exactly the four canonical Needs (`NDS-MOH-2027-0001..0004`), each in the exact state `departmental_needs.seeds.kentender_mvp_r1.NEEDS` declares.
- `planning`: the canonical FY 2027-2028 Annual Plan is Active. When `through="planning"` exactly, additionally the module's own `validate_planning_seed()` in full (2 items, KES 130,000,000, no actuals) — not re-asserted past `planning`, because `requisitions`/`tender_preparation` legitimately advance this same Plan Item's schedule (see §2).
- `requisitions`: the module's own `validate_requisitions_seed()` (the combined item's Requisition Authorised, the exact §16.3 package, both drawdown lines).
- `tender_preparation`: the module's own `validate_tender_preparation_seed()` (one Tender on the handoff, Approved for publication, the handoff consumed by it).

Automated coverage: `bench --site <site> run-tests --app kentender_core --module kentender_core.tests.test_canonical_seed` (selection rules, dry-run safety, stage ladder, idempotent double run through Budget and through the full chain, validator failing closed on a stray budget, a fiscal year only unreferenced by the same clear pass). The test module uses `frappe.tests.IntegrationTestCase`; a `FrappeTestCase`-based module in `kentender_core` triggers Frappe's app-wide test-record preload, which fails on this site's overlapping Fiscal Years.

---

## 6. Adding the next module stage

When a module's canonical seed is cut over to the one-site model:

1. Append the stage name to `canonical.STAGES` after the stage it depends on, and add a branch in `canonical.seed()` that calls the module's own upsert with its canonical-only shape (no test edges, no isolated profiles, no commit).
2. Keep the module's canonical namespace in `canonical.CANONICAL_NAMESPACES` and make sure the module's rows are stamped with it; unstamped rows are treated as disposable by §3.1.
3. Extend `canonical.collect_non_canonical()` with the module's disposable-row rule, and `clear_canonical_modules()` with its canonical clear, in dependency order (downstream modules before the ones they reference).
4. Add the stage's facts to `canonical.validate()`.
5. Add the stage's actors to `site_setup.ACTORS`/`ASSIGNMENTS` if KT-STD-001 §8.3 lists them and no earlier stage seeds them; never create actors inside the module seed.
6. Extend `kentender_core.tests.test_canonical_seed`, run it, then run the full command on a dirtied site and confirm the dry run and the removal report match.
7. Update §2 and §3 of this document, the seeds README and the command card in `CLAUDE.md`.

Everything the module seed writes must go through the same commands the UI uses, as the named actors, never Administrator, and must be idempotent (KT-STD-001 §8.6; SEED-001 §8).

---

## 7. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `make: No rule to make target 'seed-canonical'` | Run from `apps/kentender_v1/`, not the bench root. |
| `Canonical seed refused: enable developer_mode…` | The site is not in developer mode; set `developer_mode` or `allow_canonical_seed` in `site_config.json`, or pass `"force": true` on the `bench execute` form. |
| `This site is configured as PE-XXX, not PE-MOH` | The seed never overwrites a different site identity (§8.6). Reconfigure the site deliberately, or use a different site. |
| Validation fails on "no non-canonical Fiscal Years" or "no fixture-domain users outside the register" | Something referenced the row so the clear skipped it (a year referenced by a Need, a user holding a canonical assignment). The dry run shows the plan; resolve the reference, then rerun. |
| `BUDGET_CONFIG_MISSING` from the Budget stage | The `site` stage did not complete (fiscal year or funding source absent). The whole run rolled back; read the earlier error. |
| Strategy stage `STRATEGY_CONFIG_MISSING` | Same — FY 2027-2028 is created by the `site` stage. |
| Every Desk page load logs two console 404s afterwards | Unrelated to the seed: the dev server's socket.io long-poll and Frappe's sidebar divider image (see the Budget tracker, 2026-09-06). |

---

## 8. Relationship to other seed entry points

- `make seed-kentender-mvp-v1` (`kentender_core.seeds.kentender_mvp_v1.orchestrator`) is the earlier multi-PE-era pack: it still creates a second Procuring Entity and legacy personas through `org.py`/`users.py`. As of v1.1 every module through `tender_preparation` has its own canonical stage in `make seed-canonical`, so this pack is no longer needed to reach any of them — its `departmental_needs`/`planning`/`requisitions`/`tender_preparation` result keys call the exact same module-owned upsert functions `seed-canonical` does, just behind the legacy `org`/`users`/`strategy`/`budget` stages this pack still seeds its own way. Do not run it on a site you have just made canonical unless you intend to reintroduce that data; `make seed-canonical` will remove the legacy personas again.
- `make ui-budget-fidelity-gate` and the module Playwright gates seed their own isolated fixtures (namespaced or on isolation fiscal years). They are disposable by design; `make seed-canonical` removes them.
- `bench execute kentender_core.seeds.site_setup.run` is the `site` stage alone, without a clear.

---

## 9. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 6 September 2026 | First issue, alongside `kentender_core.seeds.canonical` with stages `site`, `strategy`, `budget`; `site_setup` extended with the Budget actors and the funding source. |
| 1.1 | 9 September 2026 | Promoted `needs`, `planning`, `requisitions`, `tender_preparation` per §6 — the chain now reaches the same latest stage `make seed-kentender-mvp-v1` does, with no legacy multi-PE orchestrator anywhere in the path. Closed two defects the promotion surfaced: (1) Requisitions' `authorise_requisition()` opened Budget reservations with no `fixture_namespace`, so `reset` deleted its own canonical evidence every time — the orchestrator (not the sibling module, which must not write Budget's doctype directly) now stamps `KENTENDER_MVP_1_R1_REQ` on them, healing pre-existing unstamped rows too; (2) the Fiscal Year removal list was computed once, before the rest of the same clear pass ran, so a year that only became unreferenced as a result of that same pass (its Annual Plan or stray Budget going with it) was missed — now recomputed fresh at the point of deletion. `validate()` calls each later module's own validator only when it is exactly the last stage seeded, since a downstream stage's real consumption of an earlier one's canonical row (Requisitions on Planning's Plan Item, Tender Preparation on Requisitions' handoff and Planning's `actual_invitation_date`, FU-16) is expected progress, not drift. `THROUGH`'s default is now the last stage (`tender_preparation`), matching `canonical.STAGES[-1]`. |
