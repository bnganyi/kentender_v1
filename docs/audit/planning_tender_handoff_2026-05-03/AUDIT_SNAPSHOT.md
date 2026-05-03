# KenTender v1 — Planning → Tender implementation snapshot (2026-05-03)

Scope: in-repo apps under `apps/kentender_v1/` (`kentender_strategy`, `kentender_budget`, `kentender_core`, `kentender_procurement`, …). This folder contains **copies** of DocType JSON sources, tender/officer Python/JS, planning/budget/strategy services, seed scripts, and the STD Works POC JSON package (runtime files). These JSONs are the **version-controlled DocType definitions** (same shape as a Frappe “Export DocType”).

---

## 1. DocTypes by functional area

| Area | DocType | In `kentender_v1`? | Notes |
|------|---------|-------------------|--------|
| Strategy | Strategic Plan | Yes | Versioning (`status`: Draft / Active / Archived). |
| Strategy | Strategy Program, Sub Program, Strategy Objective, Strategy Target, Strategy Node | Yes | Objectives link plan + program; no separate “Goal” DocType — hierarchy uses program / target / node as needed. |
| Budget | Budget | Yes | Links `Strategic Plan`, `Procuring Entity`. |
| Budget | Budget Line | Yes | Links budget, funding source, strategy hierarchy fields. |
| Budget | Funding Source | Yes | |
| Budget | Budget Allocation, Budget Reservation | Yes | Present; not all audit flows reference them explicitly. |
| Budget | Cost Centre | **No** | No Cost Centre DocType under this tree (ERPNext `Cost Center` not bundled here as a first-class KenTender model in the copied set). |
| Planning | Procurement Plan | Yes | |
| Planning | Procurement Package | Yes | Links plan + `Procurement Template`. |
| Planning | Procurement Package Line | Yes | **Line** model: package ↔ `Demand` ↔ `Budget Line` (not named “Procurement Plan Line”). |
| Planning | Procurement Template | Yes | Planning template master. |
| Planning / demand | Demand (DIA) | Yes | Closest in-tree **requisition-style** object; not named Purchase Requisition. |
| Tender | Procurement Tender | Yes | STD/officer POC surface. |
| Tender | STD Template | Yes | |
| Tender | Tender Lot, Tender BoQ Item, Tender Required Form, Tender Validation Message | Yes | Child / related tables on tender. |

**Planning → Tender schema gap:** `Procurement Tender` has **no** Link field to `Procurement Plan` or `Procurement Package` in `procurement_tender.json`. The tender is anchored on `std_template` plus officer/engine fields. Any plan→tender bridge is **not** modeled as a persistent FK on the tender DocType today.

---

## 2. Workflow / status values (upstream + tender)

| Object | Field | Values (from DocType `options`) |
|--------|--------|-----------------------------------|
| Strategic Plan | `status` | Draft, Active, Archived |
| Strategy Objective | — | **No status field** on this DocType |
| Budget | `status` | Draft, Submitted, Approved, Rejected |
| Procurement Plan | `status` | Draft, Submitted, Approved, Locked, Rejected, Returned |
| Procurement Package | `status` | Draft, Completed, Submitted, Approved, Ready for Tender, Released to Tender, Returned, Rejected |
| Procurement Package Line | — | **`is_active` only** (no workflow status Select) |
| Demand | `status` | Draft, Pending HoD Approval, Pending Finance Approval, Approved, Planning Ready, Rejected, Cancelled |
| Procurement Tender | `tender_status` | Draft, Configured, Validation Failed, Validated, Tender Pack Generated, POC Demonstrated, Cancelled |
| Procurement Tender | `validation_status` | Not Validated, Passed, Passed With Warnings, Failed, Blocked |

Officer UX labels vs stored `tender_status` are documented in `officer_tender_config.py` (`tender_status_to_officer_ux_label`).

---

## 3. Relationships (Link fields — “what links to what”)

| Source DocType | Link field | Target DocType |
|----------------|------------|----------------|
| Strategic Plan | `procuring_entity` | Procuring Entity |
| Strategic Plan | `supersedes_plan` | Strategic Plan |
| Strategy Objective | `strategic_plan` | Strategic Plan |
| Strategy Objective | `program` | Strategy Program |
| Strategy Program | `strategic_plan` | Strategic Plan |
| Sub Program | `program` | Strategy Program |
| Budget | `procuring_entity` | Procuring Entity |
| Budget | `strategic_plan` | Strategic Plan |
| Budget Line | `budget` | Budget |
| Budget Line | `funding_source` | Funding Source |
| Budget Line | `strategic_plan`, `program`, `sub_program`, `output_indicator`, `performance_target` | Strategy hierarchy DocTypes |
| Procurement Plan | `procuring_entity` | Procuring Entity |
| Procurement Plan | `currency` | Currency |
| Procurement Package | `plan_id` | Procurement Plan |
| Procurement Package | `template_id` | Procurement Template |
| Procurement Package Line | `package_id` | Procurement Package |
| Procurement Package Line | `demand_id` | Demand |
| Procurement Package Line | `budget_line_id` | Budget Line |
| Demand | `budget_line`, `strategic_plan`, `program`, `sub_program`, `output_indicator`, `performance_target`, `budget`, `funding_source` | As named |
| Procurement Tender | `std_template` | STD Template |
| Procurement Tender | `lots` (Table) | Tender Lot |
| Procurement Tender | `boq_items` (Table) | Tender BoQ Item |
| Procurement Tender | `required_forms` (Table) | Tender Required Form |
| Procurement Tender | `validation_messages` (Table) | Tender Validation Message |

**Example chain from the brief** (“Strategy Objective → Budget Line → Plan Line → Package → Tender”):

- Strategy Objective → Budget Line: **indirect** (both can reference the same strategic hierarchy; no direct Link from Budget Line to Strategy Objective).
- Budget Line → Procurement Package Line: **`budget_line_id`** on `Procurement Package Line`.
- Procurement Package Line → Procurement Package: **`package_id`**.
- Procurement Package → Procurement Plan: **`plan_id`**.
- Package / Plan → Procurement Tender: **no DocType Link** in schema; release hook payload only (see below).

---

## 4. Seed data layout (Strategy / Budget / Planning / STD)

| Kind | Location in repo |
|------|-------------------|
| Core/strategy/budget seeds | `kentender_core/kentender_core/seeds/` — e.g. `seed_strategy_basic.py`, `seed_strategy_extended.py`, `seed_budget_basic.py`, `seed_budget_extended.py`, `_budget_seed_common.py`, `seed_core_minimal.py`, … |
| Planning seeds | `kentender_procurement/.../procurement_planning/seeds/` — `seed_procurement_planning_f1.py`, `seed_planning_pp3_slice.py`, `validate_planning_seed_dependencies.py` |
| Demand intake seeds | `kentender_procurement/.../demand_intake/seeds/` — `seed_dia_basic.py`, `seed_dia_extended.py`, `dia_seed_common.py`, … |
| **STD package (WORKS POC)** | `kentender_procurement/.../tender_management/std_templates/ke_ppra_works_building_2022_04_poc/` — `manifest.json`, `fields.json`, `rules.json`, `forms.json`, `sample_tender.json`, etc. (copied under `std_package/` here) |
| Template code constant | `KE-PPRA-WORKS-BLDG-2022-04-POC` in `std_template_loader.py` / `officer_tender_config.OFFICER_POC_TEMPLATE_CODE` |

Concrete sample record names are defined inside the seed Python modules (search for `insert`, `frappe.get_doc`, or fixture dicts per scenario). There is **no** separate “golden JSON” tender seed file in this snapshot beyond `sample_tender.json` inside the STD package.

---

## 5. Officer POC — implementation names (Cursor-ready)

| Item | Implementation |
|------|----------------|
| Officer field list | All `og_*` and shared columns are defined on `Procurement Tender` (`procurement_tender.json`) and driven by **`officer_guided_field_registry.py`** (`OfficerGuidedFieldSpec`, `doctype_fieldname_for_field_code`, `build_officer_config_overlay_from_registry`). |
| Sync into `configuration_json` | **`sync_officer_configuration`** (whitelist) → **`merge_officer_overlay_into_configuration`** → **`merge_registry_overlay_into_configuration`** (`officer_tender_config` + `officer_guided_field_registry`). Keys: **`get_officer_sync_config_keys`** → `get_officer_sync_field_codes`. |
| Validation | **`validate_officer_configuration`** (calls `sync_officer_configuration` then **`validate_tender_configuration`**). Engine: `std_template_engine`. |
| Forms | **`generate_officer_required_forms`**; admin/demo path: **`generate_required_forms`**. |
| BoQ | **`generate_officer_representative_boq`**; admin/demo path: **`generate_sample_boq`** (loads from **`engine.load_sample_boq_rows`** / `sample_tender.json`). |
| Preview | **`generate_officer_preview`**; admin/demo path: **`generate_tender_pack_preview`**. |
| Status mapping | Stored: `officer_tender_config` `TENDER_STATUS_*`; UX: **`tender_status_to_officer_ux_label`** / **`officer_ux_label_to_tender_status`**. |

Additional officer read APIs (Desk): **`get_officer_validation_feedback`**, **`get_officer_required_forms_checklist`**, **`get_officer_boq_status`**, **`get_officer_preview_audit_summary`**, **`get_officer_conditional_state_for_tender`** (conditional UI hints; config side in **`get_officer_conditional_state`** in `officer_tender_config.py`).

Desk `procurement_tender.js` calls the above via `frappe.call` on `kentender_procurement.kentender_procurement.doctype.procurement_tender.procurement_tender` (see `PT_MODULE`).

---

## 6. Tender BoQ Item — fields and data origin

**Fields** (all present on child DocType): `item_code`, `lot_code`, `item_category`, `description`, `unit`, `quantity`, `rate`, `amount`, `is_priced_by_bidder`, plus `notes`.

**Origin today:** **Mixed**

1. **Seeded / generated from package JSON** — `generate_sample_boq` / `generate_officer_representative_boq` read **`sample_tender.json`** via the template engine (`load_sample_boq_rows`, `build_boq_child_rows`).
2. **Loaded with sample tender** — `load_sample_tender` / `load_sample_variant` populate lots + BoQ from the same package.
3. **Manual** — child table remains editable on the form where permissions allow.

---

## 7. Release-to-tender handoff (service)

- **`tendering_handoff.build_release_payload`** builds a dict including `package`, `plan_id`, `template_id`, etc.
- **`deliver_procurement_package_release`** invokes hooks named **`release_procurement_package_to_tender`**.
- In `kentender_procurement/hooks.py` this hook list is currently **`[]`** (empty). **No registered handler** creates or updates `Procurement Tender` from a released package in this repo state.

---

## 8. Known gaps / issues (short list)

| Issue | Severity | Keep / Fix / Defer |
|-------|----------|-------------------|
| No DocType link from **Procurement Tender** to **plan/package**; hand-off model cannot assume FK integrity on tender | High | **Fix** (when v2 handoff is in scope) |
| **`release_procurement_package_to_tender`** hooks empty — release event does not create/link tender | High | **Fix** or **Defer** with explicit “manual tender” assumption |
| **Cost Centre** / **Purchase Requisition** naming not mirrored as DocTypes in this tree (Demand used for intake; PR may live elsewhere) | Medium | **Defer** / document mapping |
| **Procurement Package Line** has no workflow `status` (only `is_active`) | Low | **Keep** unless plan line states are required |
| **Estimated cost** on tender is officer field **`og_tender_estimated_cost`**, not sourced automatically from package `estimated_value` | Medium | **Fix** when integrating plan→tender |
| **BoQ** is POC/sample-driven, not production import pipeline | Medium | **Defer** (per POC boundary) |
| **Strategy Objective** has no `status` — strategy “state” is on **Strategic Plan** | Low | **Keep** / document |

---

## Folder contents

| Path | Purpose |
|------|---------|
| `doctypes/*.json` | Listed DocType schemas |
| `procurement_tender/procurement_tender.py`, `.js` | Controller + Desk |
| `officer_tender_config.py`, `officer_guided_field_registry.py` | Officer POC config |
| `services/planning/`, `services/budget/`, `services/strategy/` | Copied `services/*.py` |
| `seeds/*.py` | Aggregated seed scripts from core + planning + DIA |
| `std_package/*.json` | STD Works POC JSON pack (subset of full package; no README copy) |

Original paths are under `apps/kentender_v1/<app>/...`.
