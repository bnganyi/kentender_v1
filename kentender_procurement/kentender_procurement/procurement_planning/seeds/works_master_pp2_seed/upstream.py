# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Validate upstream WORKS master references before PP2 planning seed load."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	JOURNEY_CODE,
	STD_VERSION_CODE,
	TENDER_CODE,
)

_APPROVED_DEMAND_STATUSES = frozenset(("Approved", "Planning Ready"))


def _fail(error_code: str, message: str) -> dict[str, Any]:
	return {"ok": False, "error_code": error_code, "message": message}


def validate_upstream_for_checkpoint(checkpoint: str) -> dict[str, Any]:
	"""Return ``{ok: True, links: {...}}`` or structured failure."""
	checkpoint = (checkpoint or "").strip().upper()
	missing: list[dict[str, str]] = []
	links: dict[str, str] = {}

	entity = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-MOH"}, "name")
	if not entity:
		entity = frappe.db.get_value("Procuring Entity", {"entity_code": "MOH"}, "name")
	if not entity:
		missing.append(
			{"code": "MISSING_PROCURING_ENTITY", "ref": "PE-MOH", "message": "Procuring Entity PE-MOH not found."}
		)
	else:
		links["procuring_entity"] = entity

	demand_status = frappe.db.get_value("Demand", {"demand_id": DEMAND_CODE}, "status")
	if not demand_status:
		missing.append(
			{"code": "MISSING_DEMAND", "ref": DEMAND_CODE, "message": f"Demand {DEMAND_CODE} not found."}
		)
	elif (demand_status or "").strip() not in _APPROVED_DEMAND_STATUSES:
		missing.append(
			{
				"code": "DEMAND_NOT_APPROVED",
				"ref": DEMAND_CODE,
				"message": f"Demand {DEMAND_CODE} is not approved.",
			}
		)
	else:
		links["demand"] = DEMAND_CODE
		demand_name = frappe.db.get_value("Demand", {"demand_id": DEMAND_CODE}, "name")
		item_count = frappe.db.count(
			"Demand Item",
			{"parent": demand_name, "parenttype": "Demand"},
		)
		if not item_count:
			missing.append(
				{
					"code": "MISSING_DEMAND_ITEM",
					"ref": DEMAND_ITEM_CODE,
					"message": f"Demand item line for {DEMAND_CODE} not found.",
				}
			)
		else:
			links["demand_item"] = DEMAND_ITEM_CODE

	if not frappe.db.get_value("Budget Line", {"budget_line_code": BUDGET_LINE_CODE}, "name"):
		missing.append(
			{
				"code": "MISSING_BUDGET_LINE",
				"ref": BUDGET_LINE_CODE,
				"message": f"Budget Line {BUDGET_LINE_CODE} not found.",
			}
		)
	else:
		links["budget_line"] = BUDGET_LINE_CODE

	if not frappe.db.exists("Procurement Journey", JOURNEY_CODE):
		missing.append(
			{
				"code": "MISSING_JOURNEY",
				"ref": JOURNEY_CODE,
				"message": f"Procurement Journey {JOURNEY_CODE} not found.",
			}
		)
	else:
		links["journey"] = JOURNEY_CODE

	if checkpoint in ("READY_FOR_RELEASE", "RELEASED_TO_TENDER", "CONSUMED_BY_TENDER"):
		std_ok = bool(
			frappe.db.get_value("Procurement Journey", JOURNEY_CODE, "std_template_version_ref")
			== STD_VERSION_CODE
			or frappe.db.exists("STD Template", {"template_code": "KE-PPRA-WORKS-BLDG-2022-04-POC"})
			or frappe.db.exists("STD Template", {"template_code": STD_VERSION_CODE})
		)
		if not std_ok:
			missing.append(
				{
					"code": "MISSING_STD_VERSION",
					"ref": STD_VERSION_CODE,
					"message": f"STD template reference {STD_VERSION_CODE} not found.",
				}
			)
		else:
			links["std_version"] = STD_VERSION_CODE

	if checkpoint == "CONSUMED_BY_TENDER":
		if not frappe.db.exists("TM2 Tender", TENDER_CODE):
			missing.append(
				{
					"code": "MISSING_TENDER",
					"ref": TENDER_CODE,
					"message": f"TM2 Tender {TENDER_CODE} not found.",
				}
			)
		else:
			links["tender"] = TENDER_CODE

	if missing:
		first = missing[0]
		return {
			"ok": False,
			"error_code": first["code"],
			"message": first["message"],
			"missing": missing,
		}
	return {"ok": True, "links": links}
