# Bid Submission (BDS-CHG-001 v0.8) — operational runbooks

Procedures for running, verifying and recovering the supplier portal and
electronic bid submission on `kentender.midas.com`, and for what must be in
place before it can ever run in production. Plain English; command blocks are
exact. Written 28 Sep 2026 (plan Phase 12).

## 1. Running the module's gates

Run `make` targets from `apps/kentender_v1`, `bench` commands from
`/home/midasuser/frappe-bench`. Never run the Python suite and a Playwright
run at the same time (both write the same test worlds); `make bds-preflight`
refuses to start a Python gate while Playwright is running, and
`make ui-queue-check` should be green before any UI run.

```bash
make bds-services-gate SITE=kentender.midas.com            # every Bid Submission service module (about an hour)
make supplier-accounts-services-gate SITE=kentender.midas.com
make bds-dead-end-gate SITE=kentender.midas.com            # writes evidence/v0_8/dead_end_matrix.md
make ui-bds-fidelity-gate                                   # every portal screen against boards A–E at 1440 and 390
make ui-bds-release-evidence-gate SITE=kentender.midas.com  # the §13.3 persona pass; writes evidence/v0_8/screens/bds-release-*.png
```

One module: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.bid_submission.tests.<module>`.
One portal slice: `make ui-bds-<slice>-gate SITE=kentender.midas.com` (the
targets are listed in `make help`; each runs that slice's Python module, the
`bid-portal` component tests and its Playwright spec).

A Python run writes for real (there is no rollback). The Bid Submission tests
build their own Tenders test worlds (fiscal years from 2100), which the
Tenders clean-up removes, but afterwards clear the residue and re-validate:

```bash
cd /home/midasuser/frappe-bench
bench --site kentender.midas.com console   # then: import kentender_core.seeds.canonical as c; c.clear_non_canonical(); frappe.db.commit()
cd apps/kentender_v1 && make seed-canonical-validate SITE=kentender.midas.com THROUGH=bid_submission
```

## 2. The canonical bid (seed stage `bid_submission`)

The last canonical stage builds the canonical Tender with Afya's bid
lifecycle interleaved at the §13.3 instants: Start bid (19 May 2027 09:20),
the company and requirements tasks with the §10.1 facts (20 May), the
addendum acknowledgement (1 Jun 12:10), Charles Mutiso's blind physical
intake (10 Jun 10:00), the price (13:50), Mary Wanjiku's signed submission
(received 14:31:58, accepted 14:32:01) and, after Tenders ends the period on
12 Jun 11:00, Bid Submission's close and the sealed Bid Opening hand-off.

```bash
make seed-canonical SITE=kentender.midas.com THROUGH=bid_submission REBUILD=True   # first time, or over a world seeded only through tenders
make seed-canonical SITE=kentender.midas.com THROUGH=bid_submission                # later runs: idempotent
make seed-canonical-validate SITE=kentender.midas.com THROUGH=bid_submission
```

- It runs only on a test site: it signs with the Test Trust Service and
  deposits in the Test Tender Box (section 3). Everything it creates is
  labelled simulation.
- Over a world seeded only through `tenders` it refuses with a message asking
  for `REBUILD=True`: the Requisition's hand-off is consumed once, so the
  Tender cannot be rebuilt without rebuilding the stages below it.
- `validate` checks the bid is Submitted Version 1, the receipt's received
  and accepted instants, the submitter, the simulation label, the addendum
  acknowledgement, the matched intake, the close, one sealed envelope, the
  Bid Opening hand-off, and that a second run changes nothing.

## 3. The test environment (simulated services)

Owner decision OD-C. On a test site, site_config sets:

```bash
bench --site kentender.midas.com set-config -p kt_bds_simulation_environment 1
bench --site kentender.midas.com set-config -p production_bid_submission_enabled 1   # test site only; see section 7
```

With the first set, these register and every supplier page shows a "Test
environment" strip:

| Service | What it does | Where its data lives |
|---|---|---|
| Test Trust Service | test certificates (`Test Trust Certificate`) and signatures | records carrying `fixture_namespace` |
| Test Tender Box | receives, accepts or rejects deposits; closes the box | `sites/<site>/private/kt_test_tender_box/` (files only, no read API) |
| Test Scanner | Clean for any file, Infected for the EICAR test signature | the evidence rows |
| Test Mailbox | captures supplier messages (verification links) | `sites/<site>/private/kt_test_mailbox/messages.jsonl` |
| Test clock | the pages' trusted time for browser worlds | `BDS Test Environment Controls.current_instant` |

The Single `BDS Test Environment Controls` also forces the operating worlds
(fixtures and tests only; no role can read or write it):
`gate_closed` (production gate closed), `trust_service_down`,
`time_service_down`, `custody_service_down`, `deposit_outcome`
(Accept / Reject / Uncertain), `rejection_reference`,
`uncertain_resolution`, `accept_after_seconds`. The browser worlds reset
them through `restore_site`; a stuck world can be reset directly:

```bash
bench --site kentender.midas.com execute kentender_procurement.bid_submission.services.simulation.reset_controls
```

On this dev site the production switch is on, so a live Submit is possible
in a browser; the "not enabled" state is shown by closing the gate through
the controls (`gate_closed`), never by the site's own setting.

## 4. Browser worlds

The portal specs build their own world on the Tenders Playwright Tender
(`TND-MOH-2099-001`) with namespaced test suppliers (Afya (Test):
`pw.bds.mary@afya-pw.example` signatory, `pw.bds.david@afya-pw.example`
representative; Kisiwa (Test): `pw.bds.peter@kisiwa-pw.example`; password
`Test@123`). Fixtures: `kentender_procurement.bid_submission.seeds.playwright_ui_fixtures`
(`reset_my_bids_fixture(state=…)`, `set_instant`, `set_gate`,
`set_submission_world`, `fill_world_bid`, `issue_world_addendum`,
`close_world`, …). Every spec restores the site afterwards, and the global
teardown runs the Bid Submission and Supplier Account restores first, then
Planning, Requisitions and Tenders. A world interrupted mid-run is removed by:

```bash
bench --site kentender.midas.com execute kentender_procurement.bid_submission.seeds.playwright_ui_fixtures.restore_site
bench --site kentender.midas.com execute kentender_suppliers.supplier_accounts.seeds.playwright_ui_fixtures.restore_site
```

## 5. Scheduled work this module depends on

`hooks.py` `scheduler_events["all"]` runs:

- `close.consume_tender_events` — closes Bid Submission for each Tender whose
  submission period Tenders has ended (Drafts closed without submission,
  arrangements closed, the box closed, the Bid Opening hand-off written);
- `submission.reconcile_uncertain_attempts` — settles attempts whose
  tender-box result was uncertain, from the same correlation, never
  dispatching again;
- `handoffs.sweep` — raises and clears supplier hand-offs and operational
  incidents as service health, newly effective addenda and the deadline
  change.

The dev site's scheduler is disabled, so none of these run on their own
there. Run them by hand when a world needs them:

```bash
bench --site kentender.midas.com execute kentender_procurement.bid_submission.services.close.consume_tender_events
bench --site kentender.midas.com execute kentender_procurement.bid_submission.services.submission.reconcile_uncertain_attempts
```

### 5.1 An overdue close

A Tender whose deadline passed more than 15 minutes ago with no Bid
Submission close is **overdue** — the scheduler is off, or a close failed
(for example the tender box was unavailable). Every supplier command already
refuses after the deadline on its own trusted clock, so nothing late can be
submitted; what is missing is the close and the Bid Opening hand-off.

- It shows without the scheduler in the Technical Operator's service status
  (`kentender_procurement.bid_submission.api.get_submission_service_status`,
  `overdue_closes`), and — whenever the sweep runs — as a **Submission close**
  incident for the Technical Operator.
- Recovery (Technical Operator, System Manager or Administrator): ends the
  Tenders submission period if it is still open, then closes Bid Submission
  and issues the hand-off. Safe to run twice.

```bash
bench --site kentender.midas.com execute kentender_procurement.bid_submission.services.close.recover_overdue_close --kwargs '{"tender_reference": "TND-…", "user": "Administrator"}'
```

or `POST /api/method/kentender_procurement.bid_submission.api.recover_overdue_close` with `tender_reference`.

## 6. An uncertain submission attempt

A supplier sees "Submission confirmation is still pending. Do not submit
again." with a correlation (`COR-BDS-…`) and a support reference
(`SUP-BDS-…`), and View status (`/tenders/<ref>/bid/status`) reads the same
attempt without dispatching. Recovery is the reconciler (section 5): it asks
the tender box about that correlation only and records one outcome —
accepted (the receipt appears), rejected (the supplier may confirm again
before the deadline) or still pending. Never create a second attempt for the
same bid by hand; an attempt still pending at the deadline is listed as
unresolved in the Bid Opening hand-off.

## 7. Before the production switch may be turned on (owner-blocked)

`production_bid_submission_enabled` stays false on any production site until
the Project Owner accepts each of these (recorded as "Blocked — owner" in the
tracker, BDS-CHG-001 §5.10 and §15.3–15.6); none is claimed by this build:

1. an approved licensed trust service with its production adapter configured
   (certificates and signatures verified by the service, not by KenTender);
2. an approved custody service (the tender box) with its adapter, including
   the encryption and access model and the residual noted in plan D7
   (Administrator database access to working copies);
3. an approved malware scanner registered on `kt_file_scanners`;
4. the trusted time source;
5. the operating-profile, security and legal evidence of §15.3–15.6;
6. the production signing client (FU-V08-57: a site without the Test Trust
   Service says signing is unavailable and submits nothing).

The switch is read in one place only (`bid_submission/services/availability.py`);
a repository test fails if anything else names it.

## 8. Troubleshooting

- `bench execute` reports `NameError: name 'kentender_…' is not defined`:
  the real error is inside the called function (an import error or a thrown
  validation). Re-run it in `bench console` with a `traceback.print_exc()`.
- A page shows stale layout or text after a change: rebuild with
  `./scripts/bench-with-node.sh build --app kentender_procurement`, touch
  `kentender_procurement/hooks.py`, `bench clear-cache`, and confirm the
  `bid_portal.bundle.*.js` hash changed.
- Tenders' protected reads name a candidate whose arrangement is Closed: the
  candidate registry answers for Active and Closed arrangements (a closed
  period does not unregister anyone); only an Active candidate may ask a
  question, and only candidates active at an instant receive notices.
