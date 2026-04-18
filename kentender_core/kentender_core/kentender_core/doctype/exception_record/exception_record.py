import frappe
from frappe.model.document import Document


class ExceptionRecord(Document):
	def before_insert(self):
		if not self.created_by:
			self.created_by = frappe.session.user
