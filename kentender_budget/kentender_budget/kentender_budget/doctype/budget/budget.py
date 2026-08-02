import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from kentender_budget.services.budget_guards import assert_budget_total_reduction_safe
from kentender_budget.services.budget_permissions import (
	assert_allowed_transition_roles,
	enforce_budget_submitted_approved_immutability,
)

# B5.1 / B5.9 — approval workflow (see docs/prompts/budget/8.Budget-Approval-Flow.md, 8.a)
# v2 domain expansion: Active, Closed, Revised added (Budget Domain Revision.md)
# Revision workflow: Cancelled added for withdrawn revisions
VALID_BUDGET_STATUSES = frozenset((
	"Draft", "Submitted", "Approved", "Active",
	"Closed", "Revised", "Rejected", "Cancelled",
))
ALLOWED_STATUS_TRANSITIONS = frozenset(
	(
		("Draft",      "Submitted"),
		("Submitted",  "Approved"),
		("Submitted",  "Rejected"),
		("Rejected",   "Submitted"),
		# v2 lifecycle transitions
		("Approved",   "Active"),
		("Approved",   "Revised"),
		("Active",     "Closed"),
		("Active",     "Revised"),
		("Revised",    "Submitted"),
		("Revised",    "Active"),
		# Revision workflow transitions
		("Submitted",  "Draft"),      # Return revision for correction
		("Draft",      "Cancelled"),  # Cancel revision before submission
		("Submitted",  "Active"),     # Approve revision (combined approve+apply)
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
		self._validate_revision_guard()
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
				_("Status must be one of: {0}.").format(", ".join(sorted(VALID_BUDGET_STATUSES))),
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
					"Cannot change Budget status from {0} to {1}."
				).format(previous, self.status),
				title=_("Invalid status transition"),
			)
		assert_allowed_transition_roles(previous, self.status)

	def after_insert(self):
		# B2.1 "Save and Continue": redirect to workspace when explicitly requested.
		if cint(getattr(self, "save_and_continue", 0)):
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = "/app/budget-management"

	def _validate_required_links(self):
		if not self.budget_name:
			frappe.throw(_("Budget Name is required."))
		if not self.procuring_entity:
			frappe.throw(_("Procuring Entity is required."))
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

	def _validate_revision_guard(self):
		"""Block total_budget_amount reductions below active line obligations.

		Only runs on updates to non-new, non-Draft budgets that have existing
		lines.  New inserts and Draft saves skip this check to avoid blocking
		the budget creation flow.
		"""
		if self.is_new():
			return
		if self.status in ("Draft", "Rejected"):
			return
		if self.total_budget_amount is None:
			return
		# Only fire when total_budget_amount is actually being reduced.
		prev_total = frappe.db.get_value("Budget", self.name, "total_budget_amount")
		if prev_total is None:
			return
		if flt(self.total_budget_amount) >= flt(prev_total) - 1e-9:
			return
		assert_budget_total_reduction_safe(self.name, flt(self.total_budget_amount))

	def _validate_supersedes(self):
		if not self.supersedes_budget:
			return
		prev_entity = frappe.db.get_value("Budget", self.supersedes_budget, "procuring_entity")
		if not prev_entity:
			frappe.throw(_("Supersedes Budget does not exist."))
		if prev_entity != self.procuring_entity:
			frappe.throw(_("Supersedes Budget must belong to the same Procuring Entity (BUD-008)."))

	def _validate_version_uniqueness(self):
		"""BUD-009: (procuring_entity, fiscal_year, version_no) unique among non-cancelled budgets."""
		filters = {
			"procuring_entity": self.procuring_entity,
			"fiscal_year": self.fiscal_year,
			"version_no": self.version_no,
			"status": ["not in", ["Cancelled"]],
		}
		existing = frappe.get_all("Budget", filters=filters, pluck="name")
		others = [n for n in existing if n != self.name]
		if others:
			frappe.throw(
				_("A Budget already exists for this entity, year, and version (BUD-009).")
			)
