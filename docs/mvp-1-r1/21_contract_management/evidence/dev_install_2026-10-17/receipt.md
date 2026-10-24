# Contract Management installed on the development site — receipt

| | |
|---|---|
| Site | `kentender.midas.com` (the development site) |
| Date | 17 October 2026, 13:09 to 13:20 EAT |
| Authority | Project Owner, 17 October 2026: “3. Commit and install dev site” (tracker CM8-411, follow-up FU-CM-62) |
| Repository commit | `16664ccf` on `mvp1/dev` (the app installed is the committed code; the working tree held other sessions' uncommitted files, none under `kentender_contracts` apart from the documents) |
| Done by | the Contract Management session (c6); the seed session confirmed the site was free (its reseed and migrate had finished at about 11:20) |

## What was run

| Step | Command | Result |
|---|---|---|
| 1. State before | `mariadb` counts (table below), `list-apps`, active workflows | the app was not installed; no active Payment Entry workflow; no `cm_` custom field |
| 2. Backup | `bench --site kentender.midas.com backup` | `sites/kentender.midas.com/private/backups/20261017_130959-kentender_midas_com-database.sql.gz` (378.2 MiB) and its site-config file; the seed session's backup of 12:02 is also there |
| 3. Install | `bench --site kentender.midas.com install-app kentender_contracts` | exit 0 in 9 s: DocTypes updated, Workspace Sidebars, Desktop Icons and Dashboard created (output in the session log) |
| 4. Build | `./scripts/bench-with-node.sh build --app kentender_contracts` | exit 0 in 6.5 s; the bundle hashes changed (`contracts.bundle` 6KSFESX6 → SXXZ5OO7, `contracts_portal.bundle` GNLKMDG2 → W5X7KNNQ) |
| 5. Cache | `bench --site kentender.midas.com clear-cache` | done; the running development server needed no restart (it answered the new app's pages at once) |
| 6. Canonical seed check | `make seed-canonical-validate SITE=kentender.midas.com` | `ok: true`, no failures, anchor Fri 16 Oct 2026 10:00 |
| 7. Wave-zero smoke | `test_wave0_smoke` now lists `kentender_contracts`; run on the test site | 5 of 5 pass (one of its tests also needed `reporting_currency`, which it had lacked; fixed) |

## The native configuration before and after

| Count | Before | After |
|---|---|---|
| Custom fields, all | 34 | 41 |
| Custom fields with the `cm_` prefix | 0 | 7 |
| Active workflows | 0 | 0 |
| Active Payment Entry workflows | 0 | 0 |
| Module Defs, all / of this app | 55 / 0 | 56 / 1 |
| DocTypes of this app | 0 | 33 |
| Workspaces | 24 | 24 |
| Pages | 44 | 45 (the Contracts page) |
| Purchase Invoices, Payment Entries | 0, 0 | 0, 0 |
| Organisation Units, Award Cases, Funding Reservations | 6, 6, 17 | 6, 6, 17 |
| Contract Cases, Contract Tasks | – | 0, 0 |
| Enabled users | 35 | 35 |

No seeded row changed. The install creates no contract and no demonstration data.

## Smoke after the install (read only, as the Administrator)

* `POST /api/method/login` 200; `kentender_contracts.api.workspace.get_contract_workspace` answers with an empty list (0 rows, no error); `/desk/contracts` 200; the Desk sidebar lists **Contract Management** between the Tender Management entries and Supplier Management.
* A real browser (Chromium) opened `/desk/contracts` after login: the Contracts page drew its heading, the **My work** and **All contracts** switch, search, the status filter and “No contracts are available.” (`contracts_page.png`); a reload kept it (second first-paint). The only failed request was `404 /undefined`, the Desk's known sidebar-divider image noise (it is not this app's).

## What installing it changes on the development site, as the runbook promised

* The module, its 33 record types, 7 custom fields on native documents, the Contracts page and the Contract Management rail slot (above).
* **The payment guards on Payment Entry and Journal Entry** for suppliers that have contract invoices are now registered on the development site's document events (checked on the site: 4 handlers of the app on Payment Entry, 2 on Journal Entry, 1 each on Purchase Invoice and Purchase Receipt). No supplier has a contract invoice there yet, so no payment is held.
* **The simulation stand-ins answer on the development site**, because it carries `kt_bds_simulation_environment`: the signing provider, the synthetic rule profile, the synthetic Award source provider and the simulated funding owner. A production site must never carry that flag.

## Not done

* **Rollback is written, not tried.** To undo: restore the database backup named above with `bench --site kentender.midas.com restore <file> --force` (this also undoes everything else done on the site since 13:09), or `bench --site kentender.midas.com uninstall-app kentender_contracts`, which removes the module and its record types but leaves custom-field and desk residue that has not been checked. Neither was run, because the install worked; the follow-up FU-CM-62 stays open for it.
* **No demonstration profile is loaded** (`make seed-cm-profile`): it activates a Payment Entry workflow that Frappe makes the only active one for that document and `clean` restores nothing (FU-CM-124). The dev site has none of its own now, so it would be safe today, but it adds non-canonical rows and the seed session asked that none be left loaded. Say if the profiles are wanted.
* **A Contract Management journey on the canonical award** is not run on the development site; the test site's release evidence of 17 October 2026 (11 of 11 gates, commit `02c15f1a`) stands as the proof of the application.
