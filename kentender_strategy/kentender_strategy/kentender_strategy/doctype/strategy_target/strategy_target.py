import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


NUMERIC_TYPES = ("Numeric", "Percentage", "Currency")
TEXT_TYPES = ("Milestone", "Boolean")


class StrategyTarget(Document):
	def validate(self):
		self._validate_hierarchy()
		self._validate_measurement_values()
		self._validate_period()
		self._validate_baseline()

	def _validate_hierarchy(self):
		if not frappe.db.exists("Strategic Plan", self.strategic_plan):
			frappe.throw(_("Strategic Plan does not exist."))
		if not frappe.db.exists("Strategy Program", self.program):
			frappe.throw(_("Program does not exist."))
		if not frappe.db.exists("Strategy Objective", self.objective):
			frappe.throw(_("Objective does not exist."))
		obj = frappe.get_cached_value(
			"Strategy Objective",
			self.objective,
			["strategic_plan", "program"],
			as_dict=True,
		)
		if obj.strategic_plan != self.strategic_plan:
			frappe.throw(_("Target Strategic Plan must match Objective Strategic Plan."))
		if obj.program != self.program:
			frappe.throw(_("Target Program must match Objective Program."))

	def _validate_measurement_values(self):
		mt = self.measurement_type
		if mt in NUMERIC_TYPES:
			if self.target_value_numeric is None:
				frappe.throw(_("Target Value (Numeric) is required for this measurement type."))
			if flt(self.target_value_numeric) < 0:
				frappe.throw(_("Target Value (Numeric) must be at least 0."))
			if self.target_value_text:
				frappe.throw(_("Target Value (Text) must be empty for numeric measurement types."))
			if not (self.target_unit and str(self.target_unit).strip()):
				frappe.throw(_("Target Unit is required for this measurement type."))
			if mt == "Percentage" and not (0 <= flt(self.target_value_numeric) <= 100):
				frappe.throw(_("Percentage target must be between 0 and 100."))
		elif mt in TEXT_TYPES:
			if not (self.target_value_text and str(self.target_value_text).strip()):
				frappe.throw(_("Target Value (Text) is required for this measurement type."))
			if self.target_value_numeric is not None:
				frappe.throw(_("Target Value (Numeric) must be empty for this measurement type."))
		else:
			frappe.throw(_("Invalid Measurement Type."))

	def _validate_period(self):
		plan = frappe.get_cached_value(
			"Strategic Plan",
			self.strategic_plan,
			["start_year", "end_year"],
			as_dict=True,
		)
		if not plan:
			return
		start_y = cint(plan.start_year)
		end_y = cint(plan.end_year)
		if self.target_period_type == "Annual":
			try:
				y = cint(str(self.target_period_value).strip())
			except Exception:
				frappe.throw(_("Annual period value must be a valid year."))
			if y < start_y or y > end_y + 5:
				frappe.throw(
					_("Annual period year must be between {0} and {1} (plan end + 5 buffer).").format(
						start_y, end_y + 5
					)
				)

	def _validate_baseline(self):
		mt = self.measurement_type
		if mt in NUMERIC_TYPES:
			if self.baseline_value_text:
				frappe.throw(_("Baseline text must be empty for numeric measurement types."))
			if self.baseline_value_numeric is not None and flt(self.baseline_value_numeric) < 0:
				frappe.throw(_("Baseline numeric value must be at least 0."))
		elif mt in TEXT_TYPES:
			if self.baseline_value_numeric is not None:
				frappe.throw(_("Baseline numeric must be empty for text-based measurement types."))
		if self.baseline_year is not None:
			plan_end = frappe.get_cached_value("Strategic Plan", self.strategic_plan, "end_year")
			if plan_end is not None and cint(self.baseline_year) > cint(plan_end):
				frappe.throw(_("Baseline year cannot be after plan end year."))
