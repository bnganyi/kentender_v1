import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from kentender_budget.services.budget_permissions import (
	assert_allowed_transition_roles,
	enforce_budget_submitted_approved_immutability,
)

# B5.1 / B5.9 — approval workflow (see docs/prompts/budget/8.Budget-Approval-Flow.md, 8.a)
VALID_BUDGET_STATUSES = frozenset(("Draft", "Submitted", "Approved", "Rejected"))
ALLOWED_STATUS_TRANSITIONS = frozenset(
	(
		("Draft", "Submitted"),
		("Submitted", "Approved"),
		("Submitted", "Rejected"),
		("Rejected", "Submitted"),
	)
)


class Budget(Document):
	def before_insert(self):
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.status:
			self.status = "Draft"
		if self.status != "Draft":
			frappe.throw(_("New budgets must be in Draft status."))

	def validate(self):
		self._validate_status_field_and_transitions()
		enforce_budget_submitted_approved_immutability(self)
		self._validate_required_links()
		self._validate_fiscal_year()
		self._validate_total_amount()
		self._validate_entity_plan_alignment()
		self._validate_supersedes()
		self._validate_version_uniqueness()

	def on_trash(self):
		if self.status and self.status != "Draft":
			frappe.throw(_("Only Draft budgets can be deleted."))

	def _validate_status_field_and_transitions(self):
		if not self.status:
			self.status = "Draft"
		if self.status not in VALID_BUDGET_STATUSES:
			frappe.throw(
				_("Status must be one of Draft, Submitted, Approved, or Rejected."),
				title=_("Invalid status"),
			)
		if self.is_new():
			return

		previous = frappe.db.get_value("Budget", self.name, "status")
		if not previous:
			previous = "Draft"
		if previous not in VALID_BUDGET_STATUSES:
			frappe.throw(
				_("This Budget has an invalid stored status. Contact an administrator."),
				title=_("Invalid status"),
			)
		if self.status == previous:
			return
		if (previous, self.status) not in ALLOWED_STATUS_TRANSITIONS:
			frappe.throw(
				_(
					"Cannot change Budget status from {0} to {1}. Allowed: Draft → Submitted; Submitted → Approved or Rejected; Rejected → Submitted."
				).format(previous, self.status),
				title=_("Invalid status transition"),
			)
		assert_allowed_transition_roles(previous, self.status)

	def after_insert(self):
		# B2.1 "Save and Continue": redirect to builder only when explicitly requested
		# by client-side create flow; regular Save remains unchanged.
		if cint(getattr(self, "save_and_continue", 0)):
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = f"/app/budget-builder/{self.name}"

	def _validate_required_links(self):
		if not self.budget_name:
			frappe.throw(_("Budget Name is required."))
		if not self.procuring_entity:
			frappe.throw(_("Procuring Entity is required."))
		if not self.strategic_plan:
			frappe.throw(_("Strategic Plan is required."))
		if not self.currency:
			frappe.throw(_("Currency is required."))

	def _validate_fiscal_year(self):
		if self.fiscal_year is None:
			frappe.throw(_("Fiscal Year is required."))
		year = cint(self.fiscal_year)
		if year != self.fiscal_year:
			frappe.throw(_("Fiscal Year must be a whole number."))
		if year < 2000 or year > 2099:
			frappe.throw(_("Fiscal Year must be between 2000 and 2099."))

	def _validate_total_amount(self):
		if self.total_budget_amount is not None and flt(self.total_budget_amount) < 0:
			frappe.throw(_("Total Budget Amount cannot be negative."))

	def _validate_entity_plan_alignment(self):
		plan_entity = frappe.db.get_value("Strategic Plan", self.strategic_plan, "procuring_entity")
		if not plan_entity:
			frappe.throw(_("Strategic Plan is invalid or missing Procuring Entity."))
		if plan_entity != self.procuring_entity:
			frappe.throw(
				_("Strategic Plan must belong to the same Procuring Entity as this Budget (BUD-007).")
			)

	def _validate_supersedes(self):
		if not self.supersedes_budget:
			return
		prev_entity = frappe.db.get_value("Budget", self.supersedes_budget, "procuring_entity")
		if not prev_entity:
			frappe.throw(_("Supersedes Budget does not exist."))
		if prev_entity != self.procuring_entity:
			frappe.throw(_("Supersedes Budget must belong to the same Procuring Entity (BUD-008)."))

	def _validate_version_uniqueness(self):
		"""BUD-009: (procuring_entity, fiscal_year, version_no, strategic_plan) unique."""
		filters = {
			"procuring_entity": self.procuring_entity,
			"fiscal_year": self.fiscal_year,
			"version_no": self.version_no,
			"strategic_plan": self.strategic_plan,
		}
		existing = frappe.get_all("Budget", filters=filters, pluck="name")
		others = [n for n in existing if n != self.name]
		if others:
			frappe.throw(
				_("A Budget already exists for this entity, year, version, and strategic plan (BUD-009).")
			)
