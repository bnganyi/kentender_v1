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
		self._validate_strategy_linkage_bl006()
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
		if not self.has_value_changed("amount_reserved") and not self.has_value_changed("amount_consumed"):
			return
		frappe.throw(
			_("Reserved and consumed balances are service-controlled and cannot be edited directly."),
			title=_("Budget Line"),
		)

	def _validate_amounts_bl001_to_004(self):
		alloc = flt(self.amount_allocated)
		res = flt(self.amount_reserved)
		con = flt(self.amount_consumed or 0)
		if alloc < 0:
			frappe.throw(_("Amount allocated must be zero or greater (BL-001)."), title=_("Budget Line"))
		if res < 0:
			frappe.throw(_("Amount reserved must be zero or greater (BL-002)."), title=_("Budget Line"))
		if con < 0:
			frappe.throw(_("Amount consumed must be zero or greater (BL-003)."), title=_("Budget Line"))
		if res + con > alloc + 1e-9:
			frappe.throw(
				_("Reserved plus consumed cannot exceed allocated (BL-004)."),
				title=_("Budget Line"),
			)

	def _validate_entity_and_year_bl007(self):
		if not self.budget:
			return
		b_ent, b_plan, b_year, b_currency = frappe.db.get_value(
			"Budget",
			self.budget,
			("procuring_entity", "strategic_plan", "fiscal_year", "currency"),
		)
		if not b_ent:
			frappe.throw(_("Budget is invalid."), title=_("Budget Line"))
		if self.procuring_entity and self.procuring_entity != b_ent:
			frappe.throw(
				_("Budget line procuring entity must match parent budget (BL-007)."),
				title=_("Budget Line"),
			)
		if self.strategic_plan and b_plan and self.strategic_plan != b_plan:
			frappe.throw(
				_("Strategic Plan must match the selected Budget's strategic plan."),
				title=_("Budget Line"),
			)
		if self.fiscal_year is not None and b_year is not None and cint(self.fiscal_year) != cint(b_year):
			frappe.throw(
				_("Fiscal Year must match the selected Budget's fiscal year."),
				title=_("Budget Line"),
			)
		if not self.currency:
			self.currency = b_currency

	def _validate_strategy_linkage_bl006(self):
		if not self.strategic_plan or not self.program:
			return
		prog_plan = frappe.db.get_value("Strategy Program", self.program, "strategic_plan")
		if not prog_plan or prog_plan != self.strategic_plan:
			frappe.throw(
				_("Program must belong to the selected Strategic Plan (BL-006)."),
				title=_("Budget Line"),
			)
		if self.sub_program:
			sp_prog = frappe.db.get_value("Sub Program", self.sub_program, "program")
			if not sp_prog or sp_prog != self.program:
				frappe.throw(
					_("Sub-Program must belong to the selected Program (BL-006)."),
					title=_("Budget Line"),
				)
		if self.output_indicator:
			obj_plan, obj_prog = frappe.db.get_value(
				"Strategy Objective",
				self.output_indicator,
				("strategic_plan", "program"),
			)
			if not obj_plan or obj_plan != self.strategic_plan or obj_prog != self.program:
				frappe.throw(
					_("Output Indicator must belong to the selected plan and program (BL-006)."),
					title=_("Budget Line"),
				)
		if self.performance_target:
			t_plan, t_prog, t_obj = frappe.db.get_value(
				"Strategy Target",
				self.performance_target,
				("strategic_plan", "program", "objective"),
			)
			if not t_plan or t_plan != self.strategic_plan or t_prog != self.program:
				frappe.throw(
					_("Performance Target must belong to the selected plan and program (BL-006)."),
					title=_("Budget Line"),
				)
			if self.output_indicator and t_obj and t_obj != self.output_indicator:
				frappe.throw(
					_("Performance Target must reference the selected Output Indicator (BL-006)."),
					title=_("Budget Line"),
				)

	def _recompute_amount_available(self):
		alloc = flt(self.amount_allocated)
		res = flt(self.amount_reserved)
		con = flt(self.amount_consumed or 0)
		self.amount_available = flt(alloc - res - con)

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
