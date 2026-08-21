# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.constants import (
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_NOT_TAKEN_FORWARD,
	STATE_RETURNED,
	STATE_SUBMITTED,
	STATE_WITHDRAWN,
)

STATES = {STATE_DRAFT, STATE_SUBMITTED, STATE_RETURNED, STATE_ACCEPTED, STATE_NOT_TAKEN_FORWARD, STATE_WITHDRAWN}


class DepartmentalNeed(Document):
	def validate(self):
		if self.status not in STATES:
			frappe.throw("Invalid Departmental Need state.", title="NDS_STATE_INVALID")
		if frappe.db.get_value("Organisation Unit", self.organisation_unit, "procuring_entity") != self.procuring_entity:
			frappe.throw("Organisation Unit must belong to the selected Procuring Entity.", title="NDS_ORGANISATION_UNIT_PE_MISMATCH")

	def on_trash(self):
		frappe.throw("Departmental Needs are retained and cannot be deleted.", frappe.PermissionError, title="NDS_DELETE_FORBIDDEN")
