# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from kentender_procurement.procurement_planning.doctype.procurement_package.procurement_package import (
	recompute_package_estimated_value,
)

ALLOWED_DEMAND_STATUSES = frozenset(("Approved", "Planning Ready"))
PACKAGE_EDITABLE_STATUSES = frozenset(("Draft", "Completed", "Returned"))
PRIORITY_LEVELS = frozenset(("Low", "Normal", "High", "Critical"))


class ProcurementPackageLine(Document):
	def validate(self):
		self._set_defaults()
		self._validate_amount()
		self._validate_parent_package_mutable()
		self._validate_demand()
		self._validate_budget_line()
		self._validate_budget_line_matches_demand()
		self._validate_priority()
		self._validate_one_demand_one_active_line()

	def after_insert(self):
		self._rollup_totals()

	def on_update(self):
		self._rollup_totals()

	def on_trash(self):
		self._rollup_totals(on_trash=True)

	def _rollup_totals(self, on_trash=False):
		if not self.package_id:
			return
		if frappe.flags.get("skip_package_line_rollup"):
			return
		recompute_package_estimated_value(
			self.package_id, exclude_line_name=self.name if on_trash else None
		)

	def _set_defaults(self):
		if self.is_active is None:
			self.is_active = 1

	def _validate_amount(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero."), title=_("Invalid amount"))

	def _validate_parent_package_mutable(self):
		if not self.package_id:
			return
		status = frappe.db.get_value("Procurement Package", self.package_id, "status")
		if status and status not in PACKAGE_EDITABLE_STATUSES:
			frappe.throw(
				_(
					"Package lines can only be edited while the package is Draft, Completed, or Returned. "
					"They cannot be changed when the package is Submitted, Approved, Ready for Tender, Released to Tender, or Rejected."
				),
				title=_("Record locked"),
			)

	def _validate_demand(self):
		if not self.demand_id:
			frappe.throw(_("Demand is required."), title=_("Missing demand"))
		if not frappe.db.exists("Demand", self.demand_id):
			frappe.throw(_("Demand does not exist."), title=_("Invalid demand"))
		status = frappe.db.get_value("Demand", self.demand_id, "status")
		if status not in ALLOWED_DEMAND_STATUSES:
			frappe.throw(
				_("Demand must be Approved or Planning Ready before it can be added to a package."),
				title=_("Demand not eligible"),
			)

	def _validate_budget_line(self):
		if not self.budget_line_id:
			frappe.throw(_("Budget Line is required."), title=_("Missing budget line"))
		if not frappe.db.exists("Budget Line", self.budget_line_id):
			frappe.throw(_("Budget Line does not exist."), title=_("Invalid budget line"))

	def _validate_budget_line_matches_demand(self):
		"""Traceability: line budget line must match the demand's budget line."""
		demand_bl = frappe.db.get_value("Demand", self.demand_id, "budget_line")
		if not demand_bl:
			frappe.throw(_("Demand has no budget line set."), title=_("Invalid demand"))
		if demand_bl != self.budget_line_id:
			frappe.throw(
				_("Budget Line must match the selected Demand's budget line."),
				title=_("Budget mismatch"),
			)

	def _validate_priority(self):
		if self.priority and self.priority not in PRIORITY_LEVELS:
			frappe.throw(
				_("Priority must be one of: Low, Normal, High, Critical."),
				title=_("Invalid priority"),
			)

	def _validate_one_demand_one_active_line(self):
		"""v1: at most one active line per demand across all packages."""
		if not self.is_active or not self.demand_id:
			return
		filters = {"demand_id": self.demand_id, "is_active": 1}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		if frappe.db.exists("Procurement Package Line", filters):
			frappe.throw(
				_("This demand is already linked to an active package line (one demand per package in v1)."),
				title=_("Duplicate demand"),
			)
