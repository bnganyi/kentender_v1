# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §4.7 — a read-only projection supplied by Planning.

This is not Need lifecycle state and users cannot edit it (§4.7, NDS-BR-014).
It is written only by `project_need_planning_usage` (§8.2) from Planning's
`NeedPlanningUsageChanged.v1` event, and read by the workspace and the
withdrawal dependency check.

`active_plan` and `active_plan_item` are plain text, not Links: the firm D1
boundary forbids Departmental Needs from reaching into Procurement Planning's
tables, so these identifiers are carried by the event and never resolved here.
"""

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.constants import USAGE_FULL, USAGE_NOT_INCLUDED
from kentender_procurement.departmental_needs.errors import fail


class NeedPlanningUsageProjection(Document):
	def validate(self):
		version = frappe.db.get_value(
			"Departmental Need Version",
			self.accepted_version,
			["departmental_need"],
			as_dict=True,
		)
		if not version or version.departmental_need != self.departmental_need:
			fail(
				"NDS_STATE_CONFLICT",
				"The projected version does not belong to the selected Departmental Need.",
			)
		if self.usage == USAGE_NOT_INCLUDED:
			# §4.7 — Plan references are empty when the Need is not included.
			self.active_plan = ""
			self.active_plan_item = ""
		elif self.usage == USAGE_FULL and not self.active_plan_item:
			fail(
				"NDS_FIELD_REQUIRED",
				"A Fully included projection must identify the Active Plan Item.",
			)
