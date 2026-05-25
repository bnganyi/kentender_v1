# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKGREL_CODE,
	PKG_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.consumption import (
	ensure_release_consumed,
)


def execute():
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		return
	if not frappe.db.exists("Procurement Handoff Card", PKGREL_CODE):
		return
	ensure_release_consumed()
