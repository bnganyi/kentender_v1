# Bid Opening (BOP-CHG-001 v0.10) and Proceedings (PRC-CHG-001 v0.9) — operational runbooks

Procedures for running, verifying and recovering electronic bid opening on
`kentender.midas.com`, and what must be in place before it can ever run in
production. Plain English; command blocks are exact. Written 30 Sep 2026
(plan Phase 11).

## 1. Running the module's gates

Run `make` targets from `apps/kentender_v1`, `bench` commands from
`/home/midasuser/frappe-bench`. Never run the Python gates and a Playwright
run at the same time: both move the same test controls and clocks.
`make bop-preflight` refuses to start a Python gate while Playwright is
running, and `make ui-queue-check` should be green before any UI run.

```bash
make prc-services-gate SITE=kentender.midas.com    # the shared Proceedings service against its simulated owner (about 5 min)
make bop-services-gate SITE=kentender.midas.com    # every Bid Opening service module, the API and the public page (about 15 min)
make bop-dead-end-gate SITE=kentender.midas.com    # every state x reader; writes evidence/v0_10/state_actor_matrix.md
make bop-leakage-gate SITE=kentender.midas.com     # nothing before Start states or implies the bid count
make ui-bop-fidelity-gate                          # 49 boards against captured server answers (no browser)
make ui-bop-gate SITE=kentender.midas.com          # every Desk slice and the public page in a browser
```

One module: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.bid_opening.tests.<module>`
(`bench run-tests` ignores `--test`; run whole modules). One browser slice:
`make ui-bop-<slice>-gate` with `prepare`, `before-start`, `ceremony`,
`pauses`, `no-bids`, `record`, `completed` or `public`.

A Python run writes for real (there is no rollback). The Bid Opening tests
build their worlds on the Tenders test Tenders (fiscal years from 2100) and
remove every opening, Proceeding, audit row and render they wrote. Afterwards
clear any residue and re-validate:

```bash
cd /home/midasuser/frappe-bench
bench --site kentender.midas.com console   # then: import kentender_core.seeds.canonical as c; c.clear_non_canonical(); frappe.db.commit()
cd apps/kentender_v1 && make seed-canonical-validate SITE=kentender.midas.com THROUGH=bid_opening
```

## 2. The canonical opening (seed stage `bid_opening`)

The last canonical stage opens the canonical Tender (TND-MOH-2027-002) the way
the boards tell it:

- On 10 Jun 2027, Amina Hassan appoints Charles Mutiso (chair and recorder), Brian Wafula and Beatrice Kamau (independent member) at 10:15, and publishes how to attend at 10:20.
- On 12 Jun, the three members join from 10:55 and David Ouma joins at 10:58.
- Charles starts the opening at 11:00:12.
- What Brian read aloud at 11:01:30 is recorded at 11:01:45.
- David's request to repeat the total is answered.
- The opening ends at 11:04, and the record is finished at 11:07.
- The last signature, at 11:10:30, completes the opening and hands the bid to Evaluation.

```bash
make seed-canonical SITE=kentender.midas.com THROUGH=bid_opening     # idempotent: a completed opening is left as it is
make seed-canonical-validate SITE=kentender.midas.com THROUGH=bid_opening
```

- It runs only on a test site, because the signatures come from the test attestation service (section 4).
- It needs the `bid_submission` stage, whose close at 11:00 leaves the sealed box.
- A partial opening, from an interrupted seed or a browser pass on the canonical Tender, is removed and told again from the start.
- Jane Wanjiku joins as a public observer at 10:59. Daniel Otieno holds Opening access support (Technical Operator); the canonical opening needs none. Both are seeded by the site stage (KT-STD-001 v1.11 §8.3).
- Everyone signs in with the shared fixture password (`.env.ui`), the canonical supplier people (David Ouma, Mary Wanjiku) and Jane Wanjiku included.
- The canonical world is dated 2027. A browser walk of it pins the site's test clock just after the opening (`make ui-bop-release-evidence-gate` sets 12 Jun 2027 11:15 and clears it afterwards); without that, roles that start in 2027 are not yet in force.

## 3. The browser worlds

`bid_opening/seeds/playwright_ui_fixtures.py` builds one world per board
state on the Bid Submission test Tender (TND-MOH-2099-001, deadline 5 Jun
2027 11:00). Each of its 32 stages (`STAGES`) runs the real commands as their
actors at the board's instant, walking the clock in 30-second steps so the
members' pages stay present (the lapse is 60 seconds).

```bash
bench --site kentender.midas.com execute kentender_procurement.bid_opening.seeds.playwright_ui_fixtures.reset_opening_fixture --kwargs "{'stage': 'answered'}"
bench --site kentender.midas.com execute kentender_procurement.bid_opening.seeds.playwright_ui_fixtures.restore_site
```

If `bench execute` answers `NameError: name 'kentender_procurement' is not defined`, the real error is hidden: run the call through
`env/bin/python` with `frappe.init`/`frappe.connect` to see it, and check `make ui-queue-check`.

The component fidelity fixtures in `public/js/bid_opening/fixtures/` are the
server's own answers captured from these worlds (`capture()` and
`capture_public()`), never written by hand. After any change to what
GetOpening or the public read returns, re-capture them:

1. For each stage: `reset_opening_fixture(stage=…)`, then save `capture()` as `fixtures/<stage>.json`.
2. For the public boards: save `capture_public()` for the prepared, published, joined, answered and complete stages, and for complete after a register request with self-service off and with it on.
3. Finish with `restore_site()`, then run `make ui-bop-fidelity-gate`.

## 4. The test stand-ins (plan OD-C)

On this site `site_config.kt_bds_simulation_environment = 1` enables the
stand-ins:

- the Test Tender Box's release and reveal (Bid Submission);
- the default renderer (wkhtmltopdf);
- the test attestation service (Proceedings);
- the public attendance channel;
- the support notice transport.

Each is switched through test controls, never through site settings:

| To picture | Control |
|---|---|
| The opening service is down (board c2c/c2d) | `BOP Test Environment Controls.opening_profile_down = 1` |
| Support cannot be told | `notify_outcome = "Fail"`, then `"Deliver"` |
| The public attendance service is down (board n1) | `attendance_service_down = 1` |
| A bid cannot be rendered (board c11) | `render_outcome = "Unreadable"` |
| A bid does not match the closed box (board c11d) | Bid Submission's `reveal_outcome = "Mismatch"` |
| Secure access is not ready (board c2b) | Bid Submission's `custody_service_down = 1` |

`simulation.reset_controls()` puts all of them back. A test attestation is
not an electronic signature: the verification label appears only in tests
(TRUST-ADR-001 v0.1 §2).

## 5. Recovering an opening

- **A member's page stops, and they lapse.** The next heartbeat from another member, the next material action or the sweep pauses the opening ("Opening is paused because [name] is not present"). Nothing else is recorded until every member is present. Rejoining resumes it from the last committed step. If the member cannot return, the Accounting Officer appoints a replacement, with a reason.
- **A bid cannot be opened or does not match.** An incident goes to Opening access support.
  - When support records it resolved, the chair's **Retry opening** opens the same bid again.
  - When support records it not resolved, the Accounting Officer is given the paused-decision item. Its only route, a Tender decision, is not available in this version (TPR-CHG-001 v0.14; FU-BOP-06).
- **The opening never started.** After the deadline, the Accounting Officer records that it did not take place, with the reason. The bids stay sealed; this is final for this opening.
- **A command was sent twice, or from a stale page.** The idempotency journal returns the first result. A stale page is told "Someone updated this opening record. Refresh the page before continuing." and reloads. Nothing is duplicated or backdated.
- **The completed record needs a correction.** The recorder adds one of the four kinds (Attendance note, Procedural note, Typographical error in a note, Observer name or organisation). The signed record is unchanged, and any other kind is refused.

## 6. Before production (Phase 12, owner-gated)

None of these is in place, and `production_bid_opening_enabled` stays off
until every one is decided:

- the legal trace (LAW-V-001, Act sections 78, 67 and 82);
- the operating profile (presence timeout, custody threshold and key holders, page and initial equivalence, attendee authentication, recovery);
- real signing and custody through the TRUST-ADR-001 support module;
- the security review (BOP v0.10 §15), including response timing (FU-BOP-19);
- Evaluation's uptake of the `Evaluation Handoff`;
- the TPR-CHG-001 v0.14 post-close decision route;
- the owner's production enablement decision.
