# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DepartmentalNeedReview(Document):
	def before_save(self):
		if not self.is_new():
			frappe.throw("Departmental Need review history is immutable.", frappe.PermissionError, title="NDS_REVIEW_IMMUTABLE")

	def on_trash(self):
		frappe.throw("Departmental Need review history is immutable.", frappe.PermissionError, title="NDS_REVIEW_IMMUTABLE")
