import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender_budget.services.budget_guards import assert_budget_draft_for_mutation


class BudgetAllocation(Document):
	def before_insert(self):
		if not self.created_by:
			self.created_by = frappe.session.user

	def validate(self):
		assert_budget_draft_for_mutation(self.budget)
		self._sync_from_budget()
		self._validate_budget_and_program()
		self._validate_amount()
		self._validate_duplicate_program()
		self._validate_total_ceiling()

	def on_trash(self):
		assert_budget_draft_for_mutation(self.budget)

	def _sync_from_budget(self):
		if not self.budget:
			return
		b = frappe.db.get_value(
			"Budget",
			self.budget,
			["procuring_entity", "strategic_plan", "currency", "total_budget_amount", "status"],
			as_dict=True,
		)
		if not b:
			frappe.throw(_("Budget does not exist."))
		self.procuring_entity = b.procuring_entity
		self.strategic_plan = b.strategic_plan
		self.currency = b.currency

	def _validate_budget_and_program(self):
		if not self.program:
			frappe.throw(_("Program is required."))
		prog_plan = frappe.db.get_value("Strategy Program", self.program, "strategic_plan")
		if not prog_plan:
			frappe.throw(_("Strategy Program does not exist."))
		if prog_plan != self.strategic_plan:
			frappe.throw(
				_("Program must belong to the same Strategic Plan as the Budget (ALLOC-004).")
			)
		plan_entity = frappe.db.get_value("Strategic Plan", self.strategic_plan, "procuring_entity")
		if plan_entity != self.procuring_entity:
			frappe.throw(_("Procuring Entity must match Budget (ALLOC-005)."))

	def _validate_amount(self):
		if self.amount is None or flt(self.amount) <= 0:
			frappe.throw(_("Allocation Amount must be greater than zero (ALLOC-003)."))

	def _validate_duplicate_program(self):
		"""ALLOC-007: unique (budget, program)."""
		filters = {"budget": self.budget, "program": self.program}
		existing = frappe.get_all("Budget Allocation", filters=filters, pluck="name")
		others = [n for n in existing if n != self.name]
		if others:
			frappe.throw(_("An allocation for this Program already exists on this Budget (ALLOC-007)."))

	def _validate_total_ceiling(self):
		"""ALLOC-008: cap only when a positive total is set (unset often stores as 0)."""
		total_cap = frappe.db.get_value("Budget", self.budget, "total_budget_amount")
		if total_cap is None or flt(total_cap) <= 0:
			return
		cap = flt(total_cap)
		rows = frappe.get_all(
			"Budget Allocation",
			filters={"budget": self.budget},
			fields=["name", "amount"],
		)
		total_others = sum(flt(r.amount) for r in rows if r.name != self.name)
		if total_others + flt(self.amount) > cap + 1e-9:
			frappe.throw(
				_("Total allocations cannot exceed the Budget Total Budget Amount (ALLOC-008).")
			)
