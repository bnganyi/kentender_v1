# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2 WORKS master Demand seed on the MVP Demand DocType (DEM-INT-010).

Creates ``DEM-MOH-2026-001`` as an Approved, planning-ready Demand so Planning
tests and the WORKS full seed no longer depend on the deleted DIA seed.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_lifecycle.demand_module_gate import (
	demand_doctype_available,
)
from kentender_procurement.procurement_lifecycle.legacy_demand_codes import (
	WORKS_DEMAND_CODE,
	WORKS_DEMAND_TITLE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	DEMAND_ITEM_CODE,
	ESTIMATED_VALUE,
	PE_CODE,
)

FIXTURE_NS = "WORKS_MASTER"
AMOUNT = float(ESTIMATED_VALUE)


def _upsert(doctype: str, filters: dict[str, Any], values: dict[str, Any]) -> str:
	name = frappe.db.get_value(doctype, filters, "name")
	if name:
		frappe.db.set_value(doctype, name, values, update_modified=False)
		return name
	doc = frappe.get_doc({"doctype": doctype, **filters, **values})
	doc.insert(ignore_permissions=True)
	return doc.name


def upsert_works_master_demand(*, commit: bool = True) -> dict[str, Any]:
	"""Idempotently seed the PP2 WORKS Approved Demand on MVP schema."""
	if not demand_doctype_available():
		frappe.throw("Demand DocType is not available", frappe.ValidationError)

	pe = frappe.db.get_value("Procuring Entity", {"entity_code": PE_CODE}, "name") or PE_CODE
	owner = (
		frappe.db.get_value("Organisation Unit", {"unit_code": C.OU_SDMS}, "name")
		or C.OU_SDMS
	)
	requester = (
		C.USER_MEDICAL
		if frappe.db.exists("User", C.USER_MEDICAL)
		else "Administrator"
	)

	budget_line = frappe.db.get_value(
		"Budget Line", {"generated_reference": BUDGET_LINE_CODE}, "name"
	)
	budget = (
		frappe.db.get_value("Budget Line", budget_line, "budget") if budget_line else None
	)

	demand = _upsert(
		"Demand",
		{"demand_code": WORKS_DEMAND_CODE},
		{
			"title": WORKS_DEMAND_TITLE,
			"procuring_entity": pe,
			"owner_org_unit": owner,
			"delivery_org_unit": owner,
			"requester": requester,
			"need_statement": (
				"Renovate and upgrade District Hospital building and associated "
				"civil works at Makutano District Hospital."
			),
			"need_rationale": "Facility condition impairs safe clinical service delivery",
			"expected_outcome": "Renovated district hospital fit for clinical use",
			"beneficiaries": "Makutano District Hospital patients and staff",
			"delivery_location": "Makutano District Hospital",
			"required_by_date": "2026-12-31",
			"demand_route": "Standard",
			"urgency": "Medium",
			"requester_estimate": AMOUNT,
			"confirmed_estimate": AMOUNT,
			"currency": "KES",
			"estimate_confidence": "Medium",
			"estimate_basis": "Quantity surveyor estimate",
			"procurement_category": "Works",
			"status": "Approved",
			"current_stage": "Complete",
			"planning_ready": 1,
			"planning_usage": "Not taken up",
			"approved_at": "2026-04-10 09:00:00",
			"fixture_namespace": FIXTURE_NS,
		},
	)

	_upsert(
		"Demand Item",
		{"item_code": DEMAND_ITEM_CODE},
		{
			"demand": demand,
			"description": WORKS_DEMAND_TITLE,
			"quantity": 1,
			"uom": "Lot",
			"requester_estimate": AMOUNT,
			"confirmed_quantity": 1,
			"confirmed_uom": "Lot",
			"confirmed_estimate": AMOUNT,
			"remaining_quantity": 1,
			"remaining_amount": AMOUNT,
			"currency": "KES",
			"fixture_namespace": FIXTURE_NS,
		},
	)

	allocation = None
	if budget_line and budget:
		allocation = _upsert(
			"Demand Funding Allocation",
			{"demand": demand, "budget_line": budget_line},
			{
				"budget": budget,
				"allocation_amount": AMOUNT,
				"currency": "KES",
				"matching_source": "Automatic",
				"funds_check_result": "Sufficient",
				"bo_confirmation_status": "Confirmed",
				"fixture_namespace": FIXTURE_NS,
			},
		)

	if commit:
		frappe.db.commit()

	return {
		"ok": True,
		"demand": demand,
		"demand_id": demand,
		"demand_code": WORKS_DEMAND_CODE,
		"title": WORKS_DEMAND_TITLE,
		"estimated_value": flt(AMOUNT),
		"item_code": DEMAND_ITEM_CODE,
		"allocation": allocation,
		"budget_line": budget_line,
		"planning_ready": 1,
		"planning_usage": "Not taken up",
	}
