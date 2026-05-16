# 6. Tender Management (TM2 + STD Instance + Publication)

## Goal

Document **Tender Management v2**: **TM2 Tender** as the sole tender header, **Tender STD Instance** binding and derived outputs, **publication** (readiness, snapshots, approval decisions, evidence), **supplier participation** surfaces, and **security/audit** integration.

> **Legacy note:** The historical **Procurement Tender** DocType and its desk POC stack were **removed** from the codebase; runtime and tests are **TM2-only**.

## Frappe app and module

- **App:** `kentender_procurement`
- **Frappe module:** *Kentender Procurement* (all DocTypes below share this module name in JSON.)

## DocType groups

### 6.1 TM2 Tender core and lifecycle

TM2 Addendum (+ Acknowledgement, Impact Record), TM2 Bid Draft Metadata, TM2 Bid Receipt, TM2 Bid Submission (+ Component), TM2 Clarification Request / Response, TM2 Contract Handoff Reference, TM2 Evaluation Handoff Record, TM2 Late Submission Attempt, TM2 Notification Record, TM2 Opening Readiness Record, TM2 Publication Readiness, TM2 Publication Record, TM2 Supplier Participation, **TM2 Tender**, TM2 Tender Access Rule, TM2 Tender Audit Event, TM2 Tender Closing Record, TM2 Tender Invitation, TM2 Tender STD Binding, TM2 Tender Timeline.

### 6.2 Tender STD Instance (binding + content)

Tender STD Instance (+ Snapshot, Parameter Value, BOQ / BOQ Bill / BOQ Item, Drawing Register Entry, Section Attachment, Works Requirement), Tender STD Generated Output, Tender Derived Model Readiness, Tender Hardening Finding (legacy naming; used in validation artefacts where still present), Tender BoQ Item, Tender Lot, Tender Required Form, Tender Section Attachment, Tender Validation Message, Tender Works Requirement.

### 6.3 Publication and governance bridge

Tender Publication Snapshot, Tender Publication Approval Decision.

### 6.4 Desk / navigation

**Procurement Navigation** — navigation DocType for procurement desk tiles (cross-cutting).

*Machine-readable full list:* [`doctypes_inventory.csv`](doctypes_inventory.csv) — filter rows where `doctype_name` starts with `TM2` or `Tender` or equals `Procurement Navigation`.

## Key Python packages (`tender_management/`)

| Area | Path (relative to `kentender_procurement/kentender_procurement/tender_management/`) |
|------|----------------------------------------------------------------------------------------|
| STD instance bind/state/output | `std_instance/` |
| Publication transaction / readiness / evidence | `tender_publication/` |
| Derived models (DSM/DOM/DEM/DCM) | `derived_models/` |
| Security (authz, audit, evidence export) | `security/` |
| Works completion (TM2-bound) | `works_completion/` |
| APIs (REST/whitelisted) | `api/` |
| Scenarios / smoke helpers | `scenarios/` |
| Seeds / fixtures | `seeds/`, `fixtures/`, `*/seeds/` (e.g. `works_completion/seeds/`, `derived_models/seeds/`, `tender_publication/seeds/`) |

## Desk and web

- **Tender Management v2 workbench page:** `page_js` → `tender-management-v2` → `public/js/tender_management_v2_workbench_page.js`
- **Supplier portal (website):** `website_route_rules` in `hooks.py` — `/supplier/tenders` and `/supplier/tenders/<tender_code>` → `www/supplier/tenders`
- **Procurement home workspace:** `workspace/procurement_home/` + `public/js/procurement_home_workspace.js`

## Integration from Procurement Planning

- **`release_procurement_package_to_tender`** hook (`hooks.py`) delegates to `tender_management.services.release_procurement_package_to_tender` to create/update **TM2 Tender** from a released package.

## Seeds and verification scripts (non-exhaustive)

| Script / area | Role |
|---------------|------|
| `tender_management/seeds/std_template_governance_seed.py` | Governance seed (after_migrate) |
| `tender_management/seeds/seed_std_inst_1400.py` | STD instance fixture chain |
| `tender_management/derived_models/seeds/seed_derived_moh_1200.py` | Derived model golden path |
| `tender_management/tender_publication/seeds/seed_pub_moh_1100.py` | Publication MOH slice |
| `tender_management/works_completion/seeds/works_completion_moh_fixture.py` | Works completion fixtures (TM2) |
| `procurement_planning/seeds/works_stdint_s01_verification.py` | Planning ↔ tender structural checks |

## Patches (representative)

`kentender_procurement/patches.txt` includes tender/STD DB integrity patches such as:

- `p6_clear_procurement_tender_dev` (legacy column/table cleanup pre-migrate)
- `stdinst_1300_db_constraints`, `stdinst_1302_tm2_only_active_slot_triggers`, `stdinst_1303_snapshot_append_only_tm2`
- `derived_0100_extend_stdout_published_trigger`

## Automated tests

- Primary suite: `bench --site <site> run-tests --app kentender_procurement`
- Deep coverage under `tender_management/tests/` (unit + integration), including P11 contamination scans for TM2 surfaces.
