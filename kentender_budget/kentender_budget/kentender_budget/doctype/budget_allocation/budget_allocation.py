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
		self._validate_amount()
		self._validate_total_ceiling()

	def on_trash(self):
		assert_budget_draft_for_mutation(self.budget)

	def _sync_from_budget(self):
		if not self.budget:
			return
		b = frappe.db.get_value(
			"Budget",
			self.budget,
			["procuring_entity", "currency", "total_budget_amount", "status"],
			as_dict=True,
		)
		if not b:
			frappe.throw(_("Budget does not exist."))
		self.procuring_entity = b.procuring_entity
		self.currency = b.currency

	def _validate_amount(self):
		if self.amount is None or flt(self.amount) <= 0:
			frappe.throw(_("Allocation Amount must be greater than zero (ALLOC-003)."))

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
