# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class KTSMStatusHistory(Document):
	def before_insert(self):
		if not self.changed_at:
			self.changed_at = now_datetime()
		if not self.changed_by:
			self.changed_by = frappe.session.user
