# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Integration helpers — released IT Procurement Package rows for Screen 01 create modal."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.stable_platform_seed.constants import (
	IT_PROCUREMENT_CATEGORY,
	IT_REQUIRED_STD_CATEGORY,
	IT_REQUIRED_STD_TYPE,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_RELEASED

_CREATED: list[tuple[str, str]] = []


def _resolve_plan_id() -> str | None:
	return frappe.db.get_value("Procurement Plan", {}, "name", order_by="modified desc")


def ensure_released_it_procurement_package(
	*,
	package_code: str,
	package_name: str,
	procuring_entity_code: str = "PE-NATIONAL-TREASURY",
	procurement_method: str = "Open Tender",
) -> dict[str, Any]:
	"""Create or update a released IT package eligible for wizard create options."""
	if frappe.db.exists("Procurement Package", package_code):
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			{
				"package_name": package_name,
				"status": PKG_RELEASED,
				"procuring_entity_code": procuring_entity_code,
				"procurement_method": procurement_method,
				"required_std_category": IT_REQUIRED_STD_CATEGORY,
				"required_std_type": IT_REQUIRED_STD_TYPE,
				"procurement_category": IT_PROCUREMENT_CATEGORY,
				"is_active": 1,
			},
		)
		return {"name": package_code, "package_code": package_code, "created": False}

	plan_id = _resolve_plan_id()
	doc = frappe.get_doc(
		{
			"doctype": "Procurement Package",
			"name": package_code,
			"package_code": package_code,
			"package_name": package_name,
			"plan_id": plan_id,
			"procuring_entity_code": procuring_entity_code,
			"procurement_method": procurement_method,
			"contract_type": "Fixed Price",
			"currency": "KES",
			"procurement_category": IT_PROCUREMENT_CATEGORY,
			"required_std_category": IT_REQUIRED_STD_CATEGORY,
			"required_std_type": IT_REQUIRED_STD_TYPE,
			"status": PKG_RELEASED,
			"is_active": 1,
		}
	)
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_validate = True
	doc.insert(ignore_permissions=True)
	_CREATED.append(("Procurement Package", doc.name))
	return {"name": doc.name, "package_code": package_code, "created": True}


def cleanup_created_packages() -> None:
	while _CREATED:
		dt, name = _CREATED.pop()
		if frappe.db.exists(dt, name):
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
