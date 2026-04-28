# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class KTSMPerformanceNote(Document):
	def before_insert(self):
		if not self.recorded_at:
			self.recorded_at = now_datetime()
		if not self.recorded_by:
			self.recorded_by = frappe.session.user
