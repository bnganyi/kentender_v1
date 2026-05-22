import frappe
from frappe import _
from frappe.model.document import Document

from kentender_strategy.services.strategy_hierarchy_guards import assert_plan_is_draft_for_mutation


class SubProgram(Document):
	def validate(self):
		if not frappe.db.exists("Strategy Program", self.program):
			frappe.throw(_("Program does not exist."))
		prog_plan = frappe.db.get_value("Strategy Program", self.program, "strategic_plan")
		if not prog_plan:
			frappe.throw(_("Program has no Strategic Plan."))
		if not self.strategic_plan:
			self.strategic_plan = prog_plan
		if self.strategic_plan != prog_plan:
			frappe.throw(_("Sub-program Strategic Plan must match Program Strategic Plan."))
		assert_plan_is_draft_for_mutation(self.strategic_plan)
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

	def on_trash(self):
		assert_plan_is_draft_for_mutation(self.strategic_plan)
