import frappe
from frappe import _
from frappe.model.document import Document


class SubProgram(Document):
	def validate(self):
		if self.sub_program_code and str(self.sub_program_code).strip():
			code = str(self.sub_program_code).strip()
			self.sub_program_code = code
			existing = frappe.db.get_value(
				"Sub Program",
				{"program": self.program, "sub_program_code": code},
				"name",
			)
			if existing and existing != self.name:
				frappe.throw(_("Sub-Program Code must be unique per Program."))
