# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.audit_events import (
	ensure_planning_audit_events,
)


def execute():
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		return
	ensure_planning_audit_events(checkpoint="CONSUMED_BY_TENDER")
