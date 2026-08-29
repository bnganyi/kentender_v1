# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning's record of an accepted Need represented in a Plan Item.

BOUNDARY NOTE (firm D1 decision, 2026-08-29): Procurement Planning consumes
Accepted Needs only through the published handoff contract. The direct reads
below still reach into Departmental Needs tables and are therefore a known
violation, carried until Phase 5 replaces them with the accepted-source
contract and the `NeedPlanningUsageChanged.v1` projection event. The Phase 9
architecture test (NDS-910) fails while any of them remain.

NDS-CHG-001 v1.1 §1.1 also removes partial Need allocation: when Planning uses
an accepted Need it takes the full accepted quantity (NDS-AC-014). Phase 5
reshapes this doctype accordingly.
"""

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.constants import STATE_ACCEPTED


class PlanNeedAllocation(Document):
	def validate(self):
		if float(self.allocated_quantity or 0) <= 0:
			frappe.throw(
				"Allocated quantity must be greater than zero.",
				title="NDS_ALLOCATION_QUANTITY_INVALID",
			)
		version = frappe.db.get_value(
			"Departmental Need Version",
			self.departmental_need_version,
			["departmental_need", "indicative_quantity", "version_status"],
			as_dict=True,
		)
		if not version or version.departmental_need != self.departmental_need:
			frappe.throw(
				"The source version does not belong to the selected Departmental Need.",
				title="NDS_ALLOCATION_LINE_MISMATCH",
			)
		need = frappe.db.get_value(
			"Departmental Need",
			self.departmental_need,
			["current_state", "current_accepted_version"],
			as_dict=True,
		)
		if not need or need.current_state != STATE_ACCEPTED:
			frappe.throw(
				"Only Accepted for planning Needs may be allocated.",
				title="NDS_NEED_NOT_ELIGIBLE",
			)
		# §7.2 / NDS-AC-014 — Planning consumes only the current accepted version.
		if need.current_accepted_version != self.departmental_need_version:
			frappe.throw(
				"Only the current accepted version of a Need may be allocated.",
				title="NDS_SOURCE_STALE",
			)
		if float(self.allocated_quantity) > float(version.indicative_quantity or 0):
			frappe.throw(
				"Allocated quantity exceeds the accepted Need quantity.",
				title="NDS_ALLOCATION_EXCEEDS_LINE",
			)
