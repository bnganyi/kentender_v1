# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class ProcurementBudgetVersion(Document):
	def validate(self):
		if self.based_on_budget_version and not self.revision_type:
			frappe.throw(_("Revision type is required for a successor Budget Version."))
		if not self.based_on_budget_version and self.revision_type:
			frappe.throw(_("Revision type is not permitted on the initial Budget Version."))
		if self.approval_date and getdate(self.approval_date) > getdate():
			frappe.throw(_("Approval date cannot be in the future."))
