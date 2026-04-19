import frappe
from frappe import _
from frappe.model.document import Document

from kentender_strategy.services.strategy_hierarchy_guards import assert_plan_is_draft_for_mutation


class StrategyProgram(Document):
	def validate(self):
		assert_plan_is_draft_for_mutation(self.strategic_plan)
		if not frappe.db.exists("Strategic Plan", self.strategic_plan):
			frappe.throw(_("Strategic Plan does not exist."))
		if self.program_code and str(self.program_code).strip():
			code = str(self.program_code).strip()
			existing = frappe.db.get_value(
				"Strategy Program",
				{"strategic_plan": self.strategic_plan, "program_code": code},
				"name",
			)
			if existing and existing != self.name:
				frappe.throw(_("Program Code must be unique per Strategic Plan."))

	def on_trash(self):
		assert_plan_is_draft_for_mutation(self.strategic_plan)
