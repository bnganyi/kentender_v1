import frappe
from frappe import _
from frappe.model.document import Document

from kentender_strategy.services.strategy_hierarchy_guards import assert_plan_is_draft_for_mutation


class StrategyObjective(Document):
	def validate(self):
		assert_plan_is_draft_for_mutation(self.strategic_plan)
		if not frappe.db.exists("Strategic Plan", self.strategic_plan):
			frappe.throw(_("Strategic Plan does not exist."))
		if not frappe.db.exists("Strategy Program", self.program):
			frappe.throw(_("Program does not exist."))
		prog = frappe.get_cached_value(
			"Strategy Program",
			self.program,
			["strategic_plan", "name"],
			as_dict=True,
		)
		if prog.strategic_plan != self.strategic_plan:
			frappe.throw(_("Objective Strategic Plan must match Program Strategic Plan."))
		if self.objective_code and str(self.objective_code).strip():
			code = str(self.objective_code).strip()
			existing = frappe.db.get_value(
				"Strategy Objective",
				{"program": self.program, "objective_code": code},
				"name",
			)
			if existing and existing != self.name:
				frappe.throw(_("Objective Code must be unique per Program."))

	def on_trash(self):
		assert_plan_is_draft_for_mutation(self.strategic_plan)
