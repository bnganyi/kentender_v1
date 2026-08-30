# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime


class DepartmentalPlanSubmissionWindow(Document):
	def validate(self):
		if get_datetime(self.closes_at) <= get_datetime(self.opens_at):
			frappe.throw(_("Closes At must be later than Opens At."))
