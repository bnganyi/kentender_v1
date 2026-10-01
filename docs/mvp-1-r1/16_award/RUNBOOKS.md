# Award (AWD-CHG-001 v0.4) — runbooks

Written for: engineers and testers working on the dev site (`kentender.midas.com`). Commands run from `apps/kentender_v1/` unless shown otherwise.

## 1. Where things are

| What | Where |
|---|---|
| Module | `kentender_procurement/kentender_procurement/award/` (`services/`, `api.py`, `portal.py`, `seeds/`, `test_services/`, `tests/`) |
| Desk page | `/app/award` (workspace) and `/app/award/{award_id}` (record; `/requests/{id}` and `/view/{what}` sub-routes) |
| Supplier notice | `/supplier/awards/{notice_id}` in the public portal |
| Screens | `public/js/award/` (`board/AwdBoard.vue` renders every board; `screens/*.js` build them from server reads) |
| Upstream seams | `bid_evaluation/services/award_seam.py`, `tenders/services/award_seam.py`, `bid_submission/services/award_gateway.py` |
| Stand-ins (test environment only) | `award/test_services/sources.py` (synthetic upstream), `award/test_services/contracting_receiver.py` (Contracting), the test profile in `award/services/profile.py`, switches in **Award Test Environment Controls** |

Every stand-in answers only when `site_config.json` sets `kt_bds_simulation_environment`. Without it there is no verified operating profile, so every positive advance is refused with "The applicable rules have not been confirmed. The award cannot proceed yet."

## 2. Tests and gates

| Command | What it proves | Time (1 Oct 2026) |
|---|---|---|
| `make awd-services-gate` | 16 service modules on the synthetic sources (no tender, bid, opening or evaluation is built) | ≈ 1 minute |
| `make awd-seams-gate` | The real Evaluation → Award seam: read-only contract checks against the canonical report, plus one real Evaluation world | ≈ 40 seconds |
| `make awd-leakage-gate` / `make awd-dead-end-gate` | Who sees what; every stage × viewer has a sound next step; retries and stale writes | ≈ 20 seconds |
| `make ui-awd-fidelity-gate` | All 47 boards compared container for container (also inside `make ui-structure-gate`) | seconds |
| `make ui-awd-<slice>-gate` | One browser spec per slice (opinion, decision, notices, supplier, wait, debrief, correction) | 15–30 seconds each |
| `make ui-awd-demo-walk-gate` | The canonical award walked from the menu, the bell and the portal (needs `seed-canonical THROUGH=award`) | ≈ 35 seconds |

Rules that keep runs fast and the site clean:

- Never run an `award` Python module while a Playwright run is active (`awd-preflight` refuses).
- Award service tests write only rows stamped `AWD_TEST` and remove them; they never touch the canonical award, so no reseed is needed after them.
- `awd-seams-gate` builds one real Evaluation world (Evaluation's own shared test world), whose Planning and Tenders fixtures persist (test users, 2101/2103 fiscal years, a test budget). Run `make seed-canonical SITE=kentender.midas.com THROUGH=award` afterwards; `seed-canonical-validate` fails until you do.
- Re-run another module's tests only when a file that module depends on changed, and only the affected test module.

## 3. Browser worlds

```bash
cd /home/midasuser/frappe-bench
bench --site kentender.midas.com execute kentender_procurement.award.seeds.playwright_ui_fixtures.reset_award_fixture --kwargs '{"stage": "received"}'
bench --site kentender.midas.com execute kentender_procurement.award.seeds.playwright_ui_fixtures.restore_site
```

`STAGES` in `award/seeds/playwright_ui_fixtures.py` lists the 34 stages, one per board branch (`received`, `signed`, `notified`, `accepted`, `delivered`, `request`, `returned`, `source-incomplete`, `expired`, `no-award`, `notice-failed`, `declined`, `no-response`, `order-hold`, `challenge-hold`, `post-decision-correction`, `correction-decision`, `receiver-down`, `cancelled`, `signing-unavailable`, `unsuccessful`, `rules-unverified`, `status-unknown`, `technical`, `tie`, `correction-authorised`, `corrected-report`, `closed-correction`, `late-response`, `corrected-opinion`, `corrected-opinion-positive`, `revised-held`, `revised-ready`, `request-closed`). A stage takes about a second and leaves the site's test clock at the stage's moment. Rows are stamped `PW_AWARD`.

To refresh the fidelity fixtures after changing a read: `bench --site kentender.midas.com execute kentender_procurement.award.seeds.playwright_ui_fixtures.capture_all` (≈ 20 seconds; writes `public/js/award/fixtures/*.json`).

## 4. Canonical award and demo profiles

```bash
make seed-canonical SITE=kentender.midas.com THROUGH=award
make seed-canonical-validate SITE=kentender.midas.com THROUGH=award
make seed-awd-profiles
make seed-awd-profile PROFILE=AWD-DEMO-OPINION   # or -DECISION, -NOTICE, -WAIT, -DELIVERED
make seed-awd-profile-restore
```

The canonical award (`AWD-MOH-2027-002`) is told with the real commands on the real Evaluation delivery of TND-MOH-2027-002: received 16 Jun 2027 14:07:01; opinion signed 17 Jun 09:10 (Charles Mutiso); award and notices 17 Jun 10:00 (Amina Hassan); accepted 18 Jun 09:00 (Mary Wanjiku); delivered to the test Contracting receiver 2 Jul 09:00. A demo profile stops the story at one step and sets the site's test clock to that moment; restore tells it to the end and clears the clock. Persona password: the seeded default (`UI_SEED_PASSWORD`, `Test@123`).

## 5. Simulation switches (Award Test Environment Controls)

| Switch | Effect |
|---|---|
| `signing_outcome` = Unavailable / Indeterminate / Rejected | The opinion's signing attempt fails; the draft is kept; a Support Issue "Restore signing" opens |
| `email_failure_organisations` (names or ids, one per line) | Those recipients' notice emails are rejected ("The notice address was rejected.") |
| `email_service_down` | Every email attempt reports "Service unavailable"; a Support Issue "Restore notice delivery" opens |
| `status_service_down` | Tender status and validity cannot be read (unknown, never negative) |
| `contracting_down` / `event_delivery_down` | The test Contracting receiver refuses packages / decision events |
| `rule_unverified` | The test profile counts as unverified (every positive advance refused) |
| `revised_treatment_unverified` | Revised notices after a corrected award stay held |

Set from a shell: `bench --site kentender.midas.com execute kentender_procurement.award.seeds.playwright_ui_fixtures.set_controls --kwargs '{"contracting_down": 1}'`.

## 6. Recovery

| Situation | What happens | What to do |
|---|---|---|
| Evaluation delivered but Award did not receive | The delivery stays "Open"; a Support Issue "Restore evaluation report receipt" names the technical operator | The scheduler sweep retries with the same delivery identity (`award.services.intake.retry_pending`); run `bench execute kentender_procurement.award.services.sweep.run` to retry now |
| A notice was rejected by the address | Issue "A required notice is not yet confirmed." for the Head of Procurement | The supplier corrects its notice contact with its own contact form; the Head presses **Correct contact**, which retries the same notice |
| Email service down | Support Issue "Restore notice delivery" for the technical operator | The sweep retries; the operator can press **Retry operation** on `/app/award/{id}` |
| Contracting unavailable | "Contracting is unavailable. KenTender will check that the award can still proceed before sending it." | The sweep rechecks conditions 1–6 and retries the same package; a restriction that arose meanwhile keeps it held |
| Signing unavailable | Draft kept, same attempt | Pressing **Sign opinion** again completes the same attempt once signing is back |
