# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Where an accepted Need stands against its department's plan — a
read-only projection supplied by Planning (owner decision 26 Sep 2026).

A Need accepted after its department's plan was accepted is in no plan until
the department creates an update; one accepted while the plan is with
Procurement goes into a later update. Neither is Need lifecycle state and
users cannot edit it. It is written only by `project_need_planning_intake`
from Planning's own reconciliation of the department's plan, and read by the
need detail screen.

`departmental_plan` is plain text, not a Link: the firm D1 boundary forbids
Departmental Needs from reaching into Procurement Planning's tables, so the
reference is carried by Planning and never resolved here.
"""

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.errors import fail


class NeedPlanningIntakeProjection(Document):
	def validate(self):
		for field in ("need_revision", "carried_revision"):
			revision = self.get(field)
			if not revision:
				continue
			owner = frappe.db.get_value("Departmental Need Revision", revision, "departmental_need")
			if owner != self.departmental_need:
				fail(
					"NDS_STATE_CONFLICT",
					"The projected revision does not belong to the selected Departmental Need.",
				)
		if self.position != "Update required":
			# Only an accepted plan missing the current revision can still be
			# carrying an earlier one.
			self.carried_revision = ""
