# Tender Configurations inventory (WP4R-RG04) — written before any deletion, 7 Oct 2026

Owner decision (7 Oct 2026): the legacy Tender Configurations module (the "IT Tender ..." wizard, the BWMF
bidder-workspace-manifest framework, the publication pipeline that approves and publishes with no maker-checker)
is retired completely, with no reference left, exactly as Tender Management v2 was (`audit/tm2-inventory.md`).
Findings that close by deletion: AUD-XC-143 (26 `frappe.db.commit()`, GET that writes), AUD-XC-011 (reopened part),
RG-04 / REG-SOD-01 (publish with no maker-checker), RG-05 / REG-STATE-05 (publication record created already Published),
and INT-B 4 (16 test modules that never loaded).

Gate pattern at the end: `git grep -i -E 'tender_configurations|tender-configuration|bwmf|it-tender|IT Tender Publication|Confirmed Tender Document Package|publication-setup'`
excluding `.git`, `node_modules`, `archive/`, `docs/`, `audit/`.

## 1. What the module is

| Area | Path | Notes |
|---|---|---|
| Python package | `kentender_procurement/kentender_procurement/tender_configurations/` | 322 tracked files: `api.py`, `__init__.py` (wrappers), `constants.py`, `services/` (30 modules), `seed/` (13), `bidder_workspace_manifest/` (BWMF), `electronic_std_templates/`, `bidder_workspace_manifest/` schemas, `tests/` (46 modules + helpers), 40 doctype dirs |
| Doctypes (40, module `Tender Configurations`) | `tender_configurations/doctype/` | `Tender Configuration`, `IT Tender Publication Record`, `Confirmed Tender Document Package`, 37 `BWMF *` doctypes |
| Desk pages (19) | `kentender_procurement/kentender_procurement/page/`: `it_tender_configuration_*` (14), `it_tender_package_review`, `publications`, `publication_setup`, `it_std_wizard_retired` | routes `it-tender-configuration-*`, `it-tender-package-review`, `publications`, `publication-setup`, `it-std-wizard-retired` |
| Assets | `public/js/it_tender_configuration_*_page.js` (14), `it_tender_configuration_create_modal.js`, `it_tender_configurations_dashboard_page.js`, `it_tender_package_review_page.js`, `publication_setup_page.js`, `publications_page.js`, `it_std_wizard_retired_page.js` | 20 files; no CSS |
| hooks.py (procurement) | `app_include_js` create modal (line 84); 21 `page_js` entries (`it-std-wizard-retired`, `it-tender-configuration-*`, `it-tender-package-review`, `publications`, `publication-setup`); `doc_events["File"]["on_trash"]` BWMF CAS guard (line 480) | the File hook disappears with BWMF |
| modules.txt | `Tender Configurations` | whole module goes |
| Module Def | `Tender Configurations` | created by pre-sync patch `ensure_tender_configurations_module` |
| Patches | `ensure_tender_configurations_module` (pre-sync), `ensure_bwmf_doctypes_synced`, `ensure_bwmf_persistence_indexes`, `ensure_it_std_wizard_retired_page`; `retire_it_std_wizard_cleanup` (names the wizard pages/sidebar rows) | the first four re-create the module and are deleted; the cleanup patch is a historic one-shot: its page parts are trimmed (the drop patch owns them now) |
| Roles | `BWMF Auditor`, `BWMF Procurement Reviewer`, `BWMF Publication Service`, `BWMF Tender Approver`, `BWMF Tender Configurator` (created on demand by BWMF code/tests; present on the test site, absent on dev) | dropped by the drop patch when unused |
| File | folder `Home/BWMF-CAS` (private File folder, test site: 1 folder row, no files) | dropped by the drop patch when empty |

## 2. Importers / callers outside the module (every one is dealt with)

| Consumer | What it does | Decision |
|---|---|---|
| `kentender_core/seeds/demo_platform_seed/` (7 py files) + `seeds/seed_demo_platform.py` + `scripts/seed_demo_platform.sh` + Makefile `seed-demo-platform*` (3 targets + 2 help lines) + `seeds/README.md` section | "IT STD demo platform" seed: walks Tender Configurations (`actionable.py` imports 8 services; `clear/load/transitions/validate/pe_cleanup` too). It also builds DIA demands / Procurement Packages that no longer exist | DELETE whole pack (it is the Tender Configuration demo and cannot run without the module) |
| `kentender_core/tests/test_demo_platform_seed.py`, `test_demo_platform_transitions.py` | tests of the pack above | DELETE |
| `kentender_core/public/js/kt_cl_surface_registry.js` | the registry holds only the 19 A2 wizard screens (`UI-00` ... `PUB-A3`), crumbs for `it-tender-configuration-*`, `publications`, `publication-setup` | EMPTY the `surfaces` map (mechanism and file stay: other pages call `resolveFromRoute`) |
| `kentender_core/tests/test_kt_cl_surface_registry_contract.py` | asserts the 19 screen ids and the dashboard page script | REWRITE: registry mechanism present, no Tender Configuration surface/route |
| `kentender_core/tests/test_kt_cl_shell_layout_guard.py` (line ~279), `test_ui01_layout_css_contract.py` | assert `it-tender-configuration-dashboard` in sources / UI-01 CSS contract | ADJUST (see step 3) |
| `kentender_core/public/js/kt_cl_components.js:1686-1716` | create-configuration modal copy in the shared Civic Ledger components | LEFT unless it is wizard-only (checked at deletion time) |
| `kentender_core/seeds/mvp1_role_user_cleanup.py` | lists the 5 `BWMF *` roles in `ROLES_TO_DISABLE` | remove the 5 names (drop patch deletes the roles) |
| `kentender_core/tests/test_command_write_coverage.py` | lists the 3 legacy doctypes and the 37 BWMF tables as reviewed exceptions (`OPEN_FINDINGS`, `BWMF_TABLES`) | remove both sets |
| `kentender_procurement/setup/workspace_permissions.py` | `publications` route key and `_IT_WIZARD_PAGE_ROUTE_KEYS` (15 routes) -> Procurement rail | remove |
| `kentender_procurement/setup/sidebar_availability.py`, `setup/tests/test_procurement_sidebar_g0_012_contract.py` | `Tender Configurations` listed as a Planned sidebar label (no such item exists in `workspace_sidebar/procurement.json`) | remove the label |
| `kentender_procurement/setup/tests/test_workspace_sidebar_fastpath.py` (216-220), `test_sidebar_availability.py:37` | wizard routes in a fast-path test; a `publications` link as test input | trim |
| `kentender_procurement/public/js/procurement_sidebar_header.js:182` | maps `/desk/it-tender-configuration-*` to the dashboard | remove |
| `kentender_procurement/procurement_home/services/home_pipeline.py:78-95` | `if db.exists("DocType","Tender Configuration")` guarded count of packages that already have a configuration | remove the branch |
| `kentender_procurement/bid_submission/tests/test_legacy_retirement.py` | BDS Phase-1 retirement test: proves the retired *bid* slice of the module is gone; lines 191-194 import the module's package and api | KEEP but adjust: the module itself is now gone, so the import check becomes "package is gone"; docstring/FU-05 note updated |
| `kentender_procurement/patches/bds_chg_001_v08_retire_bid_slice.py` | docstring names the module; the patch drops the three legacy bid doctypes | KEEP, docstring only |
| `Makefile` | `ui-civic-ledger-*` (15 targets over `tests/ui/smoke/it-std-wizard`), `pub-domain-gate`, `ui-publications-gate`, `bw-manifest-phase1..5-gate`, `bw-manifest-phase2-reset/reseed`, `e1-nssf-seed-gate`, `e1-nssf-poc-gate`, help lines, `.PHONY` entries | DELETE targets |
| `tests/ui/smoke/it-std-wizard/` (18 specs), `tests/ui/smoke/publications/` (3 specs), `tests/ui/helpers/ktClUi01LayoutContract.ts`, `tests/ui/helpers/ktClQueueContract.ts` (UI-00 queue pattern) | browser tests of the wizard/publication pages | DELETE specs and the UI-01 helper; `ktClQueueContract.ts` is shared by 3 other specs -> KEEP |
| `.cursor/rules/kentender-civic-ledger-queue-lock.mdc` | editor rule scoped to `tender_configurations/**` and the wizard docs | DELETE (rule is only about this module) |
| docs/ trees (not `docs/mvp-1-r1`) | `docs/std-prod-impl/IT-STD-Wizard*`, `docs/tender-publications/`, `docs/std-prod/ux`, `docs/audit/...`, `docs/test-contracts/civic-ledger-queue-rollout-matrix.md` | NOT touched (kt_cl_code_spec.js and test_kt_cl_shell_layout_guard.py still read `IT-STD-Wizard-v3/B-Components/code.html` as the Civic Ledger component spec); listed as document follow-ups |
| `docs/mvp-1-r1/**` | 20+ approved/historic documents mention the module (BDS FU-05 / legacy_inventory, STD-TPL FU-08, CFG v0.11-0.18, ...) | NOT touched; document workstream |

## 3. Live-dependency check (what could be mistaken for "legacy Tender Configurations")

Searched all live modules (`tenders`, `std_templates`, `bid_submission`, `bid_opening`, `bid_evaluation`, `award`, `proceedings`, `procurement_planning`,
`procurement_requisitions`, `departmental_needs`, `procurement_lifecycle`, `procurement_home`, `contract_management`) and all other apps for: the Python package path,
the 40 doctype names, the 19 page names, the whitelisted function names, the BWMF Python names and the BWMF roles.

Result: **no live module imports, calls, links to or reads a Tender Configurations piece.** All "it_tender"/"IT Tender" hits in `tenders/` and `bid_submission/` are
substring false positives (`submit_tender_for_approval`, `submit_tender_clarification`). The only non-legacy consumers are the ones in section 2 (a core demo seed,
core registry/tests, setup tables, one guarded home count). The current Tenders module (`tenders/`, Module Def `Tenders`, doctype `Tender Publication`), STD Templates
(`std_templates/`, own release machinery), Bid Submission v0.8, Opening, Evaluation and Award do not depend on it. `tenders/services/digest.py` does not reuse the BWMF JCS
implementation (STD-TPL-IMP-001 §3 only says the BWMF `jcs.py` "can be adapted"; no code was adapted).

KEEP although they look related:

| Item | Why kept |
|---|---|
| Roles `Tender Manager`, `Planning Authority`, `Procurement Officer` | shared roles used by other modules; the module only borrowed them. Role *use* inside the module disappears with it |
| `kt-cl-shell-poc` page, `kt_cl_routes.js`, `kt_cl_shell_poc_page.js`, `kt_cl_shell.js`/router/components in kentender_core | the Civic Ledger shell mechanism and its own tests; shared infrastructure, not part of the module (the `Tender Configurations` label in the PoC's demo nav is sample text only) |
| `kt_cl_surface_registry.js` file | mechanism used by `kt_cl_shell_router.js`, `home_page.js`, `analytics_page.js`; only the wizard's surfaces leave |
| `STD Version`, `STD Parameter` ... tables (STD-TPL-IMP-001 FU-08) | the remaining empty `tabSTD *` tables were kept because "live Tender Configurations code still queries" them. With the module gone nothing queries them: follow-up F2 (drop them), not done here |
| `templates/std_works_poc/`, `templates/std_admin_console/` | no Python/JS reference anywhere (orphaned by the STD POC retirement, not owned by this module). Follow-up F3 |
| `tests/ui/smoke/procurement/officer-tender-poc-*.spec.ts`, `works-hardening-desk-wh012.spec.ts`, `tests/ui/helpers/stdAdminConsoleDesk.ts` | STD admin-console POC specs; no import of the module. Follow-up F3 |
| `stable_platform_seed` (core) | independent of the module (the demo pack called it, not the reverse) |
| `bds_chg_001_v08_retire_bid_slice.py`, `retire_it_std_wizard_pre_sync.py` | historic one-shots; `Module Def "IT Tender Wizard"` is a different, earlier retirement |

## 4. Site state (read-only SELECTs, 7 Oct 2026)

| Check | kentender-test.local | kentender.midas.com (dev, read-only) |
|---|---|---|
| DocTypes with module `Tender Configurations` | 40 | 40 |
| Rows in any of the 40 tables | 0 | 0 |
| Page rows (19 names above) | 19 | 19 |
| Custom DocPerm / Workflow / Report / Print Format / Server Script / Notification / User Permission on them | 0 | 0 |
| Workspace Sidebar Item rows linking the 19 pages | 0 | 0 |
| File folder `Home/BWMF-CAS` | 1 folder, no files | 0 |
| Roles `BWMF *` | 5 (test-run residue) | 0 |
| `tabDeleted Document` / `tabComment` ("Deleted") for BWMF doctypes | 3396 / 3396 (test-run residue) | 0 / 0 |

No business data to preserve on either site. The drop patch follows the TM2 precedent: **refuse** (throw `RETIRED_TABLE_NOT_EMPTY`) if any retired table holds rows
or the CAS folder holds files; otherwise raw existence-guarded deletes (no `frappe.delete_doc`, which in developer mode would delete files and fire events). It also
removes the deletion-log rows (`Deleted Document`, `Comment` type Deleted) for the retired doctypes, the 19 Pages, unused BWMF roles, the empty CAS folder and the
`Tender Configurations` Module Def.

## 5. Delete list / keep list summary

DELETE: the package `tender_configurations/` whole (code, 40 doctype dirs, services, seeds, BWMF, STD template JSON, 46 test modules including the 16 that never loaded);
19 page dirs; 20 public JS files; hooks (21 page_js, create-modal include, File on_trash); modules.txt entry; 4 patches + their patches.txt lines; core demo seed pack +
tests + script + Makefile targets; wizard/publication browser specs and Makefile gates; registry surfaces; setup route tables; sidebar label; home branch; `.cursor` rule.
ADD: one drop patch `drop_retired_tender_configurations` (pre_model_sync) with its guard test.
KEEP: everything in section 3's KEEP table.
DEV SITE: needs `migrate` (runs the drop patch) — listed in the progress file.
