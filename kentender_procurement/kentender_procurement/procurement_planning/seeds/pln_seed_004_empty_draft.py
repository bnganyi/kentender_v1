# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SEED-004 — isolated empty Draft plan for UI/Playwright (non-canonical FY)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_planning.mvp1_constants import (
	PLAN_OPEN,
	PLAN_TYPE_ANNUAL,
	PUB_NOT_SUBMITTED,
	VALIDATION_NOT_RUN,
	VERSION_DRAFT,
)
from kentender_procurement.procurement_planning.services._invariants import (
	new_concurrency_token,
	period_dates_for_financial_year,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ensure_planning_roles,
)

# Deliberately not PLN-MOH-2027-001 / FY 2027/28 — must not contradict Approved V1 seed.
UI_PLAN_CODE = "PLN-MOH-UI-DRAFT-001"
UI_FY = "2029/30"
UI_PE = "PE-MOH"
UI_OU = "MOH-DIR-DHP"
UI_TITLE = "Ministry of Health Annual Procurement Plan 2029/30 (UI empty draft)"


def ensure_empty_draft_plan_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""Idempotent Open Plan + Draft V1 with zero Plan Items for PLN-UI-03 specs."""
	ensure_planning_roles()
	ensure_currency_kes()
	ensure_procuring_entity(UI_PE, "Ministry of Health")
	if not frappe.db.exists("Organisation Unit", UI_OU):
		ou_type = frappe.db.get_value("Organisation Unit Type", {}, "name")
		if not ou_type:
			ot = frappe.get_doc(
				{
					"doctype": "Organisation Unit Type",
					"type_reference": "DIR",
					"display_label": "Directorate",
					"status": "Active",
				}
			)
			ot.insert(ignore_permissions=True)
			ou_type = ot.name
		frappe.get_doc(
			{
				"doctype": "Organisation Unit",
				"unit_code": UI_OU,
				"unit_name": "Directorate of Digital Health and Policy",
				"unit_type": ou_type,
				"procuring_entity": UI_PE,
				"status": "Active",
			}
		).insert(ignore_permissions=True)

	period_start, period_end = period_dates_for_financial_year(UI_FY)
	if frappe.db.exists("Procurement Plan", {"plan_code": UI_PLAN_CODE}):
		plan_name = frappe.db.get_value(
			"Procurement Plan", {"plan_code": UI_PLAN_CODE}, "name"
		)
	else:
		plan = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_code": UI_PLAN_CODE,
				"title": UI_TITLE,
				"procuring_entity": UI_PE,
				"financial_year": UI_FY,
				"period_start": period_start,
				"period_end": period_end,
				"currency": "KES",
				"plan_type": PLAN_TYPE_ANNUAL,
				"coordinating_org_unit": UI_OU,
				"lifecycle_state": PLAN_OPEN,
				"publication_projection": PUB_NOT_SUBMITTED,
			}
		)
		plan.insert(ignore_permissions=True)
		plan_name = plan.name

	version_code = f"{UI_PLAN_CODE}-V1"
	if frappe.db.exists("Procurement Plan Version", {"version_code": version_code}):
		version_name = frappe.db.get_value(
			"Procurement Plan Version", {"version_code": version_code}, "name"
		)
		frappe.db.set_value(
			"Procurement Plan Version",
			version_name,
			{"status": VERSION_DRAFT, "validation_projection": VALIDATION_NOT_RUN},
			update_modified=False,
		)
	else:
		version = frappe.get_doc(
			{
				"doctype": "Procurement Plan Version",
				"plan": plan_name,
				"version_number": 1,
				"version_code": version_code,
				"status": VERSION_DRAFT,
				"version_reason": "PLN-SEED-004 empty draft for UI",
				"validation_projection": VALIDATION_NOT_RUN,
				"concurrency_token": new_concurrency_token(),
			}
		)
		version.insert(ignore_permissions=True)
		version_name = version.name

	# Ensure no plan items on this UI fixture plan
	for item in frappe.get_all(
		"Procurement Plan Item", filters={"plan": plan_name}, pluck="name"
	):
		for doctype in ("Plan Demand Allocation", "Procurement Plan Item Version"):
			for name in frappe.get_all(doctype, filters={"plan_item": item}, pluck="name"):
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
		frappe.delete_doc("Procurement Plan Item", item, force=1, ignore_permissions=True)

	frappe.db.set_value(
		"Procurement Plan",
		plan_name,
		{
			"open_draft_version": version_name,
			"current_approved_version": None,
			"lifecycle_state": PLAN_OPEN,
			"title": UI_TITLE,
		},
		update_modified=False,
	)
	if commit:
		frappe.db.commit()
	return {
		"ok": True,
		"plan": plan_name,
		"plan_code": UI_PLAN_CODE,
		"version": version_name,
		"version_code": version_code,
		"financial_year": UI_FY,
		"procuring_entity": UI_PE,
	}
