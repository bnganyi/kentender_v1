# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Quiet Demand → Tender Configuration → bidder journey sample for manual testing.

Clears confusing parallel demos and leaves a tight set:

A. Exactly two Demand rows
   - DIA-MOH-2026-0001 — Draft
   - DIA-MOH-2026-0005 — Planning Ready

B. Distinct Tender Configuration samples (no per-CFG duplicate titles)
   - 1 Ready-to-Configure package (no configuration yet)
   - 1 In Progress configuration (walk CFG-01…09 on this one row)
   - 1 Needs Attention configuration
   - 1 Published lean IT tender for bidder submission

Usage:
  bench --site kentender.midas.com execute \\
    kentender_procurement.tender_configurations.seed.demand_to_bidder_journey_sample.run

Or:
  make -C apps/kentender_v1 seed-demand-to-bidder-journey SITE=kentender.midas.com
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import nowdate

from kentender_core.seeds._common import ensure_department
from kentender_core.seeds.stable_platform_seed.constants import (
	IT_BUDGET_LINE_CODE,
	IT_DEPT_NAME,
)
from kentender_procurement.demand_intake.seeds.dia_seed_common import (
	_release_active_reservation_for_demand,
	ensure_core_prerequisites,
)
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import (
	BUDGET_LINE_CODE as INFRA_BUDGET_LINE_CODE,
	DEPT_INFRA,
	resolve_procuring_entity_moh,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_APPROVED
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
	ensure_active_canonical_ppra_it_std,
)
from kentender_procurement.tender_configurations.constants import (
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
)
from kentender_procurement.tender_configurations.seed.e1_nssf_seed import (
	_clear_publication_artifacts as _clear_e1_pubs,
	_clear_seed as _clear_e1,
)
from kentender_procurement.tender_configurations.seed.lean_synthetic_it_seed import (
	CONFIG_REF as LEAN_CONFIG_REF,
	PACKAGE_CODE as LEAN_PACKAGE_CODE,
	seed_lean_synthetic_it_published,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import clear_ui00_seed
from kentender_procurement.tender_configurations.seed.ui01_mockup_seed import clear_ui01_mockup_seed
from kentender_procurement.tender_configurations.services.configuration_home import (
	steps_state_focus_cfg,
	steps_state_showcase_nine_cards,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	STEP_IN_PROGRESS,
	STEP_NEEDS_ATTENTION,
)
from kentender_procurement.tender_configurations.services.eligibility import ensure_fixture_std_version

_U_REQ = "requisitioner@moh.test"
_U_HOD = "hod.approver@moh.test"
_U_FIN = "finance.reviewer@moh.test"

JOURNEY_PREFIX = "TCFG-JOURNEY"
PKG_READY = f"{JOURNEY_PREFIX}-PKG-READY"
CFG_IN_PROGRESS = f"{JOURNEY_PREFIX}-CFG-IP"
PKG_IN_PROGRESS = f"{JOURNEY_PREFIX}-PKG-IP"
CFG_NEEDS_ATTENTION = f"{JOURNEY_PREFIX}-CFG-NA"
PKG_NEEDS_ATTENTION = f"{JOURNEY_PREFIX}-PKG-NA"
PE_CODE = f"{JOURNEY_PREFIX}-PE"

_NOISE_CONFIG_PREFIXES: tuple[str, ...] = (
	"TCFG-SEED%",
	"TCFG-MOCK%",
	"TCFG-LEAN%",
	"TCFG-E1%",
	"TCFG-PP%",
	"TCFG-JOURNEY%",
	"BWMF-CAL%",
)

_NOISE_PACKAGE_PREFIXES: tuple[str, ...] = (
	"TCFG-SEED%",
	"TCFG-MOCK%",
	"TCFG-LEAN%",
	"TCFG-E1%",
	"TCFG-PP%",
	"TCFG-JOURNEY%",
	"BWMF-CAL%",
)


def _delete_docs(doctype: str, names: list[str]) -> int:
	count = 0
	for name in names:
		if not name or not frappe.db.exists(doctype, name):
			continue
		frappe.delete_doc(
			doctype,
			name,
			force=True,
			ignore_permissions=True,
			delete_permanently=True,
		)
		count += 1
	return count


def _config_names_like(pattern: str) -> list[str]:
	names = set(
		frappe.get_all(
			"Tender Configuration",
			filters={"configuration_ref": ("like", pattern)},
			pluck="name",
		)
	)
	names |= set(
		frappe.get_all(
			"Tender Configuration",
			filters={"name": ("like", pattern)},
			pluck="name",
		)
	)
	return sorted(names)


def _package_names_like(pattern: str) -> list[str]:
	names = set(
		frappe.get_all(
			"Procurement Package",
			filters={"name": ("like", pattern)},
			pluck="name",
		)
	)
	names |= set(
		frappe.get_all(
			"Procurement Package",
			filters={"package_code": ("like", pattern)},
			pluck="name",
		)
	)
	return sorted(names)


def _purge_config_artifacts(config_names: list[str]) -> dict[str, int]:
	stats = {"bids": 0, "publications": 0, "confirmed_packages": 0}
	if not config_names:
		return stats

	bid_names: list[str] = []
	pub_names: list[str] = []
	pkg_names: list[str] = []
	for cfg in config_names:
		bid_names.extend(
			frappe.get_all(
				"Electronic Bid Submission",
				filters={"configuration": cfg},
				pluck="name",
			)
		)
		bid_names.extend(
			frappe.get_all(
				"Electronic Bid Submission",
				filters={"configuration_ref": cfg},
				pluck="name",
			)
		)
		pub_names.extend(
			frappe.get_all(
				"IT Tender Publication Record",
				filters={"configuration_ref": cfg},
				pluck="name",
			)
		)
		pub_names.extend(
			frappe.get_all(
				"IT Tender Publication Record",
				filters={"configuration": cfg},
				pluck="name",
			)
		)
		pkg_names.extend(
			frappe.get_all(
				"Confirmed Tender Document Package",
				filters={"configuration_ref": cfg},
				pluck="name",
			)
		)

	stats["bids"] = _delete_docs("Electronic Bid Submission", sorted(set(bid_names)))
	stats["publications"] = _delete_docs(
		"IT Tender Publication Record", sorted(set(pub_names))
	)
	stats["confirmed_packages"] = _delete_docs(
		"Confirmed Tender Document Package", sorted(set(pkg_names))
	)
	return stats


def _clear_noise_configurations() -> dict[str, Any]:
	"""Drop UI-00 / UI-01 / lean / E1 / wizard / prior journey configs and packages."""
	clear_ui00_seed()
	clear_ui01_mockup_seed()
	try:
		_clear_e1_pubs()
		_clear_e1()
	except Exception:
		frappe.log_error(title="journey sample: E1 clear")

	names: list[str] = []
	for pattern in _NOISE_CONFIG_PREFIXES:
		names.extend(_config_names_like(pattern))
	names = sorted(set(names))
	artifact_stats = _purge_config_artifacts(names)
	deleted_configs = _delete_docs("Tender Configuration", names)

	pkgs: list[str] = []
	for pattern in _NOISE_PACKAGE_PREFIXES:
		pkgs.extend(_package_names_like(pattern))
	deleted_packages = _delete_docs("Procurement Package", sorted(set(pkgs)))

	orphan_pubs = frappe.get_all(
		"IT Tender Publication Record",
		filters={"configuration_ref": ("like", "TCFG-%")},
		pluck="name",
	)
	artifact_stats["orphan_publications"] = _delete_docs(
		"IT Tender Publication Record", orphan_pubs
	)

	return {
		"configurations_deleted": deleted_configs,
		"packages_deleted": deleted_packages,
		**artifact_stats,
	}


def _clear_all_demands() -> list[str]:
	removed: list[str] = []
	for name in frappe.get_all("Demand", pluck="name"):
		try:
			_release_active_reservation_for_demand(name)
		except Exception:
			pass
		demand_id = frappe.db.get_value("Demand", name, "demand_id") or name
		frappe.delete_doc(
			"Demand", name, force=True, ignore_permissions=True, delete_permanently=True
		)
		removed.append(str(demand_id))
	return removed


def _resolve_budget_line(code: str) -> str:
	name = frappe.db.get_value("Budget Line", {"budget_line_code": code}, "name")
	if not name:
		frappe.throw(
			frappe._("Budget Line {0} not found. Run make seed-stable-platform first.").format(
				code
			),
			title="Journey sample",
		)
	return name


def _insert_sample_demand(
	*,
	demand_id: str,
	title: str,
	entity: str,
	dept: str,
	budget_line: str,
	requisition_type: str,
	item_description: str,
	item_category: str,
	unit_cost: float,
	beneficiary_summary: str,
	specification_summary: str,
) -> str:
	row = {
		"doctype": "Demand",
		"title": title,
		"demand_id": demand_id,
		"procuring_entity": entity,
		"requesting_department": dept,
		"requested_by": _U_REQ,
		"created_by": _U_REQ,
		"request_date": "2026-06-01",
		"required_by_date": "2026-12-31",
		"priority_level": "High",
		"demand_type": "Planned",
		"requisition_type": requisition_type,
		"budget_line": budget_line,
		"beneficiary_summary": beneficiary_summary,
		"specification_summary": specification_summary,
		"delivery_location": "Ministry of Health — Nairobi HQ / County referral sites",
		"items": [
			{
				"item_description": item_description,
				"category": item_category,
				"uom": "Lot",
				"quantity": 1.0,
				"estimated_unit_cost": unit_cost,
			}
		],
		"status": "Draft",
		"reservation_status": "None",
		"planning_status": "Not Planned",
	}
	doc = frappe.get_doc(row)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	if frappe.db.get_value("Demand", doc.name, "demand_id") != demand_id:
		frappe.db.set_value("Demand", doc.name, "demand_id", demand_id, update_modified=False)
	return doc.name


def _promote_planning_ready(demand_name: str) -> None:
	frappe.db.set_value(
		"Demand",
		demand_name,
		{
			"status": "Planning Ready",
			"planning_status": "Planning Ready",
			"submitted_by": _U_REQ,
			"submitted_at": "2026-06-05 09:00:00",
			"hod_approved_by": _U_HOD,
			"hod_approved_at": "2026-06-06 11:00:00",
			"finance_approved_by": _U_FIN,
			"finance_approved_at": "2026-06-07 15:00:00",
			"reservation_status": "Reserved",
			"reservation_reference": f"SEED-RES-{demand_name}",
		},
		update_modified=False,
	)


def _seed_two_demands() -> dict[str, str]:
	entity = resolve_procuring_entity_moh()
	if not entity:
		frappe.throw(
			frappe._("Procuring Entity PE-MOH not found. Run make seed-stable-platform first."),
			title="Journey sample",
		)

	infra_bl = _resolve_budget_line(INFRA_BUDGET_LINE_CODE)
	it_bl = _resolve_budget_line(IT_BUDGET_LINE_CODE)
	infra_entity = frappe.db.get_value("Budget Line", infra_bl, "procuring_entity") or entity
	it_entity = frappe.db.get_value("Budget Line", it_bl, "procuring_entity") or entity
	infra_dept = ensure_department(DEPT_INFRA, infra_entity)
	it_dept = ensure_department(IT_DEPT_NAME, it_entity)

	draft_name = _insert_sample_demand(
		demand_id="DIA-MOH-2026-0001",
		title="Ultrasound Diagnostic Machines — Level 4 Hospitals (10 Units)",
		entity=infra_entity,
		dept=infra_dept,
		budget_line=infra_bl,
		requisition_type="Goods",
		item_description=(
			"Ten cart-based ultrasound systems with obstetric and general probes, "
			"training, warranty, and on-site commissioning."
		),
		item_category="Goods",
		unit_cost=24_500_000,
		beneficiary_summary=(
			"Ten Level 4 hospitals need portable ultrasound capacity for maternity "
			"and emergency triage."
		),
		specification_summary=(
			"Cart-based ultrasound systems with obstetric and general probes, "
			"training, warranty, and on-site commissioning."
		),
	)

	ready_name = _insert_sample_demand(
		demand_id="DIA-MOH-2026-0005",
		title="County HMIS Upgrade and Secure Network Backbone — Embu",
		entity=it_entity,
		dept=it_dept,
		budget_line=it_bl,
		requisition_type="Services",
		item_description=(
			"HMIS implementation, data migration, secure WAN links, training, "
			"and 12-month support for Embu County Referral Hospital network."
		),
		item_category="Services",
		unit_cost=18_500_000,
		beneficiary_summary=(
			"Embu County Referral Hospital and linked facilities need an upgraded "
			"HMIS with secure WAN connectivity."
		),
		specification_summary=(
			"HMIS implementation, data migration, secure WAN links, training, "
			"and 12-month support."
		),
	)
	_promote_planning_ready(ready_name)

	return {
		"DIA-MOH-2026-0001": draft_name,
		"DIA-MOH-2026-0005": ready_name,
	}


def _ensure_pe() -> str:
	if not frappe.db.exists("Procuring Entity", PE_CODE):
		try:
			frappe.get_doc(
				{
					"doctype": "Procuring Entity",
					"entity_code": PE_CODE,
					"entity_name": "National Treasury",
				}
			).insert(ignore_permissions=True, ignore_mandatory=True)
		except Exception:
			existing = frappe.get_all("Procuring Entity", limit=1, pluck="name")
			return existing[0] if existing else PE_CODE
	return PE_CODE


def _insert_package(*, code: str, title: str, entity: str) -> str:
	if frappe.db.exists("Procurement Package", code):
		frappe.db.set_value(
			"Procurement Package",
			code,
			{
				"package_name": title,
				"status": PKG_APPROVED,
				"is_active": 1,
				"approved_at": nowdate(),
				"required_std_category": "Information Technology",
			},
		)
		return code
	doc = frappe.get_doc(
		{
			"doctype": "Procurement Package",
			"package_code": code,
			"package_name": title,
			"status": PKG_APPROVED,
			"procurement_method": "Open Tender",
			"contract_type": "Fixed Price",
			"procuring_entity_code": entity,
			"required_std_category": "Information Technology",
			"procurement_category": "Services",
			"currency": "KES",
			"is_active": 1,
			"approved_at": nowdate(),
			"method_override_flag": 0,
		}
	)
	doc.flags.ignore_validate = True
	doc.flags.ignore_links = True
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	frappe.db.set_value(
		"Procurement Package",
		doc.name,
		{"status": PKG_APPROVED, "approved_at": nowdate(), "package_code": code, "is_active": 1},
	)
	return doc.name


def _insert_config(
	*,
	ref: str,
	package_name: str,
	package_ref: str,
	title: str,
	status: str,
	std_version: str,
	entity_name: str,
	blockers: int,
	warnings: int,
	steps_state: dict[str, Any],
) -> str:
	if frappe.db.exists("Tender Configuration", ref):
		frappe.delete_doc(
			"Tender Configuration",
			ref,
			force=True,
			ignore_permissions=True,
			delete_permanently=True,
		)
	doc = frappe.get_doc(
		{
			"doctype": "Tender Configuration",
			"configuration_ref": ref,
			"tender_title": title,
			"status": status,
			"procurement_package": package_name,
			"procurement_package_ref": package_ref,
			"package_title": title,
			"procuring_entity_name": entity_name,
			"procuring_entity_code": entity_name,
			"procurement_method": "Open Tender",
			"std_family_key": "IT",
			"std_family_label": "Information Technology",
			"std_version": std_version,
			"std_document_label": "IT Standard Tender Document — April 2022",
			"blocker_count": blockers,
			"warning_count": warnings,
			"steps_state": steps_state,
			"approval_date": nowdate(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _seed_desk_configurations() -> dict[str, Any]:
	"""One ready package + one In Progress + one Needs Attention (distinct tenders)."""
	ensure_active_canonical_ppra_it_std(force_reimport=False)
	std_id = ensure_fixture_std_version()
	# Prefer canonical PPRA for desk walkthrough consistency with published lean.
	std_for_ip = CANONICAL_PACKAGE_ID if frappe.db.exists("STD Version", CANONICAL_PACKAGE_ID) else std_id

	entity = _ensure_pe()
	entity_name = frappe.db.get_value("Procuring Entity", entity, "entity_name") or "National Treasury"

	ready_pkg = _insert_package(
		code=PKG_READY,
		title="Data Center Hardware Refresh",
		entity=entity,
	)

	ip_pkg = _insert_package(
		code=PKG_IN_PROGRESS,
		title="County LAN Refresh",
		entity=entity,
	)
	ip_cfg = _insert_config(
		ref=CFG_IN_PROGRESS,
		package_name=ip_pkg,
		package_ref=PKG_IN_PROGRESS,
		title="County LAN Refresh",
		status=STATUS_IN_PROGRESS,
		std_version=std_for_ip,
		entity_name=entity_name,
		blockers=0,
		warnings=0,
		steps_state=steps_state_focus_cfg("CFG-01", status_label=STEP_IN_PROGRESS),
	)

	na_pkg = _insert_package(
		code=PKG_NEEDS_ATTENTION,
		title="Network Upgrade Phase 2",
		entity=entity,
	)
	na_cfg = _insert_config(
		ref=CFG_NEEDS_ATTENTION,
		package_name=na_pkg,
		package_ref=PKG_NEEDS_ATTENTION,
		title="Network Upgrade Phase 2",
		status=STATUS_NEEDS_ATTENTION,
		std_version=std_id,
		entity_name=entity_name,
		blockers=2,
		warnings=1,
		steps_state=steps_state_showcase_nine_cards(),
	)

	return {
		"ready_package": ready_pkg,
		"in_progress": {"configuration_ref": ip_cfg, "package_ref": PKG_IN_PROGRESS},
		"needs_attention": {"configuration_ref": na_cfg, "package_ref": PKG_NEEDS_ATTENTION},
		"std_version": std_for_ip,
		"entity": entity,
	}


def _polish_published_lean() -> dict[str, Any]:
	title = "Shared County IT Support Services"
	if frappe.db.exists("Tender Configuration", LEAN_CONFIG_REF):
		frappe.db.set_value(
			"Tender Configuration",
			LEAN_CONFIG_REF,
			{
				"tender_title": title,
				"package_title": title,
				"short_scope_summary": (
					"Managed IT support, service desk, and secure hosting for county "
					"shared services (electronic bidding enabled)."
				),
			},
		)
	if frappe.db.exists("Procurement Package", LEAN_PACKAGE_CODE):
		frappe.db.set_value("Procurement Package", LEAN_PACKAGE_CODE, "package_name", title)
	pub = frappe.get_all(
		"IT Tender Publication Record",
		filters={"configuration_ref": LEAN_CONFIG_REF, "status": "Published"},
		fields=["name", "publication_ref", "status"],
		limit=1,
	)
	return {
		"configuration_ref": LEAN_CONFIG_REF,
		"title": title,
		"publication": pub[0] if pub else None,
	}


def run(*, clear: bool = True) -> dict[str, Any]:
	"""Clear confusing demos and load the quiet journey sample set."""
	frappe.only_for(("System Manager", "Administrator"))
	frappe.set_user("Administrator")

	ensure_core_prerequisites()

	cleared: dict[str, Any] = {}
	if clear:
		cleared["demands"] = _clear_all_demands()
		cleared["tender_noise"] = _clear_noise_configurations()
		frappe.db.commit()

	demands = _seed_two_demands()
	frappe.db.commit()

	desk = _seed_desk_configurations()
	frappe.db.commit()

	lean = seed_lean_synthetic_it_published(clear=True)
	published = _polish_published_lean()
	frappe.db.commit()

	return {
		"pack": "demand_to_bidder_journey_sample",
		"cleared": cleared,
		"demands": {
			"draft": {
				"demand_id": "DIA-MOH-2026-0001",
				"name": demands["DIA-MOH-2026-0001"],
				"title": "Ultrasound Diagnostic Machines — Level 4 Hospitals (10 Units)",
				"status": "Draft",
			},
			"planning_ready": {
				"demand_id": "DIA-MOH-2026-0005",
				"name": demands["DIA-MOH-2026-0005"],
				"title": "County HMIS Upgrade and Secure Network Backbone — Embu",
				"status": "Planning Ready",
			},
		},
		"tender_configurations": {
			"ready_to_configure_package": {
				"package_ref": PKG_READY,
				"title": "Data Center Hardware Refresh",
				"note": "Create a new configuration from the Ready to Configure tab.",
			},
			"in_progress": {
				"configuration_ref": CFG_IN_PROGRESS,
				"title": "County LAN Refresh",
				"desk": f"/desk/it-tender-configuration-home/{CFG_IN_PROGRESS}",
				"note": "Walk CFG-01…09 on this single configuration.",
			},
			"needs_attention": {
				"configuration_ref": CFG_NEEDS_ATTENTION,
				"title": "Network Upgrade Phase 2",
				"desk": f"/desk/it-tender-configuration-home/{CFG_NEEDS_ATTENTION}",
			},
			"published_for_bidder": {
				"configuration_ref": published.get("configuration_ref") or LEAN_CONFIG_REF,
				"title": published.get("title"),
				"publication_ref": lean.get("publication_ref")
				or ((published.get("publication") or {}).get("publication_ref")),
				"publication_id": lean.get("publication_id"),
				"desk": f"/desk/it-tender-configuration-home/{LEAN_CONFIG_REF}",
			},
		},
		"desk_seed": desk,
	}
