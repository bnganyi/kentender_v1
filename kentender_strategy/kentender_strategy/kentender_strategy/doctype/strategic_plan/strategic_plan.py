import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class StrategicPlan(Document):
	def validate(self):
		if self.start_year and self.end_year and self.start_year > self.end_year:
			frappe.throw(_("Start year cannot be after end year."))
		if self.supersedes_plan and self.supersedes_plan == self.name:
			frappe.throw(_("Supersedes Plan cannot reference this document itself."))

	def autoname(self):
		self.name = self._make_autoname()

	def _make_autoname(self) -> str:
		if not self.procuring_entity:
			frappe.throw(_("Procuring Entity is required before naming."))
		abbr = frappe.db.get_value("Procuring Entity", self.procuring_entity, "entity_code")
		if not abbr:
			abbr = frappe.db.get_value("Procuring Entity", self.procuring_entity, "entity_name") or "ORG"
		year = self.start_year or frappe.utils.getdate().year
		prefix = f"{abbr}-.SP-.{year}-."
		return make_autoname(prefix + ".####", self.doctype)
