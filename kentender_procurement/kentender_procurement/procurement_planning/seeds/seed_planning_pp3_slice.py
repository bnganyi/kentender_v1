# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""C4 — PP3 end-to-end slice (Cursor Pack): profiles, TPL-MED-001, PP-MOH-2026, DIA 0011, apply template.

Prerequisites: ``seed_core_minimal`` (if MOH/KES missing), DIA budget lines (``seed_budget_line_dia``),
``seed_dia_basic`` for ``DIA-MOH-2026-0004``. Sets ``DIA-MOH-2026-0004`` / ``DIA-MOH-2026-0011``
``total_amount`` to **3,000,000** / **2,000,000** via ``frappe.db.set_value`` (Approved demands lock item edits;
new **0011** uses **BL-MOH-2026-002** with small line totals for finance reservation, then header total aligned).

Grouping on the template uses ``{"group_by": []}`` (full 6. Seed Data region/equipment grouping is F1).

Run::

	bench --site <site> execute \\
	  kentender_procurement.procurement_planning.seeds.seed_planning_pp3_slice.run
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import flt

from kentender_core.seeds import constants as C
from kentender_procurement.demand_intake.seeds.dia_seed_common import (
	U_REQ,
	_fin_approve,
	_hod_approve,
	_insert_demand,
	_new_demand_dict,
	_submit,
	ensure_budget_line_prerequisites,
	ensure_core_prerequisites,
)
from kentender_procurement.procurement_planning.services.planning_references import (
	resolve_demand_name,
	resolve_procurement_plan_name,
	resolve_procurement_template_name,
)
from kentender_procurement.procurement_planning.services.template_application import (
	apply_template_to_demands,
)

PP3_PLAN_CODE = "PP-MOH-2026"
PP3_TEMPLATE_CODE = "TPL-MED-001"
PP3_PACKAGE_CODE = "PKG-MOH-2026-001"
PP3_PACKAGE_NAME = "Diagnostic Imaging Equipment - Western Region"
DEMAND_0004 = "DIA-MOH-2026-0004"
DEMAND_0011 = "DIA-MOH-2026-0011"
TARGET_0004 = 3_000_000.0
TARGET_0011 = 2_000_000.0


def _item_row(qty: float, unit_cost: float) -> dict:
	return {
		"item_description": "PP3 seed catalogue line",
		"category": "Medical supplies",
		"uom": "ea",
		"quantity": qty,
		"estimated_unit_cost": unit_cost,
	}


def _set_demand_reported_total(demand_name: str, target_total: float) -> None:
	"""Set ``Demand.total_amount`` without resaving lines (Approved demands lock item edits)."""
	frappe.db.set_value("Demand", demand_name, "total_amount", flt(target_total), update_modified=False)


def _ensure_profile_by_code(
	doctype: str,
	*,
	profile_code: str,
	profile_name: str,
	extra_fields: dict,
) -> str:
	name = frappe.db.get_value(doctype, {"profile_code": profile_code}, "name")
	if name:
		return name
	row = {"doctype": doctype, "profile_code": profile_code, "profile_name": profile_name}
	row.update(extra_fields)
	doc = frappe.get_doc(row)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_pp3_profiles() -> dict[str, str]:
	"""Insert minimal profiles from Procurement Planning 6. Seed Data §3."""
	risk = _ensure_profile_by_code(
		"Risk Profile",
		profile_code="RISK-STANDARD",
		profile_name="Standard Risk",
		extra_fields={
			"risk_level": "Medium",
			"risks": json.dumps(
				[
					{"risk": "Delivery delay", "mitigation": "Penalty clauses"},
					{"risk": "Quality failure", "mitigation": "Inspection checkpoints"},
				]
			),
		},
	)
	kpi = _ensure_profile_by_code(
		"KPI Profile",
		profile_code="KPI-STANDARD",
		profile_name="Standard Procurement KPIs",
		extra_fields={
			"metrics": json.dumps(["Cost savings %", "Lead time adherence", "Delivery completeness"]),
		},
	)
	crit = _ensure_profile_by_code(
		"Decision Criteria Profile",
		profile_code="CRIT-STANDARD",
		profile_name="Standard Weighted Criteria",
		extra_fields={
			"criteria": json.dumps(
				[
					{"criterion": "Price", "weight": 40},
					{"criterion": "Quality", "weight": 30},
					{"criterion": "Delivery", "weight": 20},
					{"criterion": "Compliance", "weight": 10},
				]
			),
		},
	)
	vm = _ensure_profile_by_code(
		"Vendor Management Profile",
		profile_code="VM-STANDARD",
		profile_name="Standard Monitoring",
		extra_fields={
			"monitoring_rules": json.dumps({"cadence": ["Monthly review"]}),
			"escalation_rules": json.dumps({"paths": ["Standard escalation"]}),
		},
	)
	return {
		"risk_profile_id": risk,
		"kpi_profile_id": kpi,
		"decision_criteria_profile_id": crit,
		"vendor_management_profile_id": vm,
	}


def _ensure_pp3_template(profile_links: dict) -> str:
	name = frappe.db.get_value("Procurement Template", {"template_code": PP3_TEMPLATE_CODE}, "name")
	if name:
		return name
	doc = frappe.get_doc(
		{
			"doctype": "Procurement Template",
			"template_code": PP3_TEMPLATE_CODE,
			"template_name": "Medical Equipment Procurement",
			"category": "Healthcare",
			"is_active": 1,
			"applicable_requisition_types": json.dumps(["Goods", "Works", "Services"]),
			"applicable_demand_types": json.dumps(["Planned", "Unplanned", "Emergency"]),
			"default_method": "Open Tender",
			"default_contract_type": "Fixed Price",
			"grouping_strategy": json.dumps({"group_by": []}),
			"threshold_rules": json.dumps([]),
			"planning_lead_days": 30,
			"procurement_cycle_days": 90,
			"override_requires_justification": 1,
			"high_risk_escalation_required": 0,
			"schedule_required": 0,
			**profile_links,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_pp3_plan() -> str:
	name = frappe.db.get_value("Procurement Plan", {"plan_code": PP3_PLAN_CODE}, "name")
	if name:
		return name
	currency = "KES"
	if not frappe.db.exists("Currency", currency):
		frappe.throw(_("Currency KES is missing. Run seed_core_minimal."), title=_("Missing prerequisite"))
	doc = frappe.get_doc(
		{
			"doctype": "Procurement Plan",
			"plan_name": "FY2026 Procurement Plan",
			"plan_code": PP3_PLAN_CODE,
			"fiscal_year": 2026,
			"procuring_entity": C.ENTITY_MOH,
			"currency": currency,
			"status": "Draft",
			"is_active": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_demand_0011() -> str:
	name = frappe.db.get_value("Demand", {"demand_id": DEMAND_0011}, "name")
	if name:
		_set_demand_reported_total(name, TARGET_0011)
		return name
	d = _insert_demand(
		_new_demand_dict(
			title="Ultrasound Units",
			demand_id=DEMAND_0011,
			requested_by=U_REQ,
			demand_type="Planned",
			bl_code="BL-MOH-2026-002",
			qty=2,
			unit_cost=5000.0,
		)
	)
	_submit(d.name)
	_hod_approve(d.name)
	_fin_approve(d.name)
	# After finance approval (reservation uses line totals), align header total to PP3 smoke amounts.
	_set_demand_reported_total(d.name, TARGET_0011)
	return d.name


def _existing_pp3_package(plan_name: str) -> str | None:
	return frappe.db.get_value(
		"Procurement Package",
		{"plan_id": plan_name, "package_code": PP3_PACKAGE_CODE},
		"name",
	)


def _ensure_core_if_needed() -> None:
	"""Avoid re-running full core seed on every call (reduces races in parallel tests)."""
	if frappe.db.exists("Procuring Entity", C.ENTITY_MOH) and frappe.db.exists("Currency", "KES"):
		return
	ensure_core_prerequisites()


def run():
	"""Idempotent PP3 slice: seed prerequisites, ensure data, apply template once."""
	frappe.only_for(("System Manager", "Administrator"))
	_ensure_core_if_needed()
	ensure_budget_line_prerequisites()

	if not frappe.db.exists("Demand", {"demand_id": DEMAND_0004}):
		frappe.throw(
			_("Demand {0} is missing. Run seed_dia_basic first.").format(DEMAND_0004),
			title=_("Missing prerequisite"),
		)

	name4 = frappe.db.get_value("Demand", {"demand_id": DEMAND_0004}, "name")
	_set_demand_reported_total(name4, TARGET_0004)

	_ensure_demand_0011()
	profiles = _ensure_pp3_profiles()
	template_name = _ensure_pp3_template(profiles)
	plan_name = _ensure_pp3_plan()

	existing_pkg = _existing_pp3_package(plan_name)
	if existing_pkg:
		ev = flt(frappe.db.get_value("Procurement Package", existing_pkg, "estimated_value"))
		return {
			"skipped": True,
			"pack": "seed_planning_pp3_slice",
			"plan": plan_name,
			"template": template_name,
			"package": existing_pkg,
			"package_code": PP3_PACKAGE_CODE,
			"estimated_value": ev,
		}

	plan_resolved = resolve_procurement_plan_name(PP3_PLAN_CODE)
	template_resolved = resolve_procurement_template_name(PP3_TEMPLATE_CODE)
	d4 = resolve_demand_name(DEMAND_0004)
	d11 = resolve_demand_name(DEMAND_0011)

	out = apply_template_to_demands(
		plan_resolved,
		template_resolved,
		[d4, d11],
		actor=frappe.session.user,
		options={"package_code": PP3_PACKAGE_CODE, "package_name": PP3_PACKAGE_NAME},
	)
	pkg_row = (out.get("packages") or [{}])[0]
	pkg_name = pkg_row.get("name")
	ev = flt(frappe.db.get_value("Procurement Package", pkg_name, "estimated_value")) if pkg_name else 0.0
	frappe.db.commit()
	return {
		"skipped": False,
		"pack": "seed_planning_pp3_slice",
		"plan": plan_name,
		"template": template_name,
		"package": pkg_name,
		"package_code": pkg_row.get("package_code"),
		"lines_created": out.get("lines_created"),
		"estimated_value": ev,
	}
