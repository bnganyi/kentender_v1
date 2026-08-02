# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class BudgetLine(Document):
	def before_validate(self):
		if self.budget_line_code and str(self.budget_line_code).strip():
			self.budget_line_code = str(self.budget_line_code).strip()
			return
		self.budget_line_code = self._generate_budget_line_code()

	def autoname(self):
		self.name = (self.budget_line_code or self._generate_budget_line_code()).strip()

	def validate(self):
		self._validate_controlled_balance_fields()
		self._validate_amounts_bl001_to_004()
		self._validate_entity_and_year_bl007()
		self._recompute_amount_available()

	def on_trash(self):
		if getattr(frappe.flags, "budget_line_force_delete", False):
			return
		frappe.throw(
			_("Budget Lines cannot be deleted from the desk. Use Budget Builder removal or contact an administrator."),
			title=_("Budget Line"),
		)

	def _validate_controlled_balance_fields(self):
		if self.is_new():
			return
		if getattr(frappe.flags, "budget_control_service_write", False):
			return
		changed = (
			self.has_value_changed("amount_reserved")
			or self.has_value_changed("amount_committed")
			or self.has_value_changed("amount_consumed")
		)
		if not changed:
			return
		frappe.throw(
			_("Reserved, committed, and consumed balances are service-controlled and cannot be edited directly."),
			title=_("Budget Line"),
		)

	def _validate_amounts_bl001_to_004(self):
		alloc = flt(self.amount_allocated)
		res   = flt(self.amount_reserved)
		com   = flt(self.amount_committed or 0)
		con   = flt(self.amount_consumed or 0)
		if alloc < 0:
			frappe.throw(_("Amount allocated must be zero or greater (BL-001)."), title=_("Budget Line"))
		if res < 0:
			frappe.throw(_("Amount reserved must be zero or greater (BL-002)."), title=_("Budget Line"))
		if com < 0:
			frappe.throw(_("Amount committed must be zero or greater (BL-002b)."), title=_("Budget Line"))
		if con < 0:
			frappe.throw(_("Amount consumed must be zero or greater (BL-003)."), title=_("Budget Line"))
		# BL-004: reserved + committed cannot exceed allocated.
		# Consumed (actual spend) is bounded within committed; it is tracked separately
		# and not deducted from available balance (per procurement-control model §7).
		if res + com > alloc + 1e-9:
			frappe.throw(
				_("Reserved plus committed cannot exceed allocated (BL-004)."),
				title=_("Budget Line"),
			)

	def _validate_entity_and_year_bl007(self):
		if not self.budget:
			return
		b_ent, b_year, b_currency = frappe.db.get_value(
			"Budget",
			self.budget,
			("procuring_entity", "fiscal_year", "currency"),
		)
		if not b_ent:
			frappe.throw(_("Budget is invalid."), title=_("Budget Line"))
		if self.procuring_entity and self.procuring_entity != b_ent:
			frappe.throw(
				_("Budget line procuring entity must match parent budget (BL-007)."),
				title=_("Budget Line"),
			)
		if self.fiscal_year is not None and b_year is not None and cint(self.fiscal_year) != cint(b_year):
			frappe.throw(
				_("Fiscal Year must match the selected Budget's fiscal year."),
				title=_("Budget Line"),
			)
		if not self.currency:
			self.currency = b_currency

	def _recompute_amount_available(self):
		alloc = flt(self.amount_allocated)
		res   = flt(self.amount_reserved)
		com   = flt(self.amount_committed or 0)
		# Available = Allocated − Reserved − Committed (procurement-control model §7).
		# amount_consumed (actual spend) is tracked separately and NOT deducted here;
		# it is bounded within committed via Committed Balance = Committed − Actual Spend.
		self.amount_available = flt(alloc - res - com)

	def _generate_budget_line_code(self) -> str:
		year = cint(self.fiscal_year) if self.fiscal_year is not None else cint(frappe.utils.now_datetime().year)
		prefix = f"BL-{year}"
		existing_codes = frappe.get_all(
			"Budget Line",
			filters={"budget_line_code": ["like", f"{prefix}-%"]},
			fields=["budget_line_code"],
			order_by="modified desc",
			limit=5000,
		)
		max_seq = 0
		for row in existing_codes:
			code = str(row.get("budget_line_code") or "").strip()
			if not code.startswith(f"{prefix}-"):
				continue
			suffix = code.split("-")[-1]
			if suffix.isdigit():
				max_seq = max(max_seq, cint(suffix))
		next_seq = max_seq + 1
		candidate = f"{prefix}-{next_seq:04d}"
		while frappe.db.exists("Budget Line", {"budget_line_code": candidate}):
			next_seq += 1
			candidate = f"{prefix}-{next_seq:04d}"
		return candidate
