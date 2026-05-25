# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.utils import flt

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	CURRENCY,
	ESTIMATED_VALUE,
	PKG_CODE,
	PKG_LINE_CODE,
	PKG_LINE_DESCRIPTION,
	PKG_LINE_QUANTITY,
	PKG_LINE_TITLE,
	PKG_LINE_UOM,
	PKG_PROCUREMENT_CATEGORY,
)


def execute():
	line_name = frappe.db.get_value(
		"Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
	)
	if not line_name:
		return
	frappe.db.set_value(
		"Procurement Package Line",
		line_name,
		{
			"line_title": PKG_LINE_TITLE,
			"line_description": PKG_LINE_DESCRIPTION,
			"unit_of_measure": PKG_LINE_UOM,
			"quantity": PKG_LINE_QUANTITY,
			"estimated_unit_cost": ESTIMATED_VALUE,
			"amount": ESTIMATED_VALUE,
			"currency": CURRENCY,
			"procurement_category": PKG_PROCUREMENT_CATEGORY,
			"is_master_seed": 1,
		},
		update_modified=False,
	)
