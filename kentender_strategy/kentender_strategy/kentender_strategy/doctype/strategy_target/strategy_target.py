import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from kentender_strategy.services.strategy_hierarchy_guards import assert_plan_is_draft_for_mutation

NUMERIC_TYPES = ("Numeric", "Percentage", "Currency")
TEXT_TYPES = ("Milestone", "Boolean")


class StrategyTarget(Document):
	def validate(self):
		assert_plan_is_draft_for_mutation(self.strategic_plan)
		self._normalize_measurement_defaults()
		self._validate_hierarchy()
		self._validate_measurement_values()
		self._validate_period_fields()
		self._validate_baseline_fields()

	def on_trash(self):
		assert_plan_is_draft_for_mutation(self.strategic_plan)

	def _normalize_measurement_defaults(self):
		if self.measurement_type == "Percentage":
			self.target_unit = "Percent"
		if self.measurement_type == "Currency" and not (self.target_unit and str(self.target_unit).strip()):
			self.target_unit = "KES"

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
				frappe.throw(_("Target Value (Numeric) is required for Numeric, Percentage, or Currency measurement types."))
			if flt(self.target_value_numeric) < 0:
				frappe.throw(_("Target Value (Numeric) must be at least 0."))
			if self.target_value_text:
				frappe.throw(_("Target Value (Text) must be empty for numeric-style measurement types."))
			if not (self.target_unit and str(self.target_unit).strip()):
				frappe.throw(_("Target Unit is required for this measurement type."))
			if mt == "Percentage":
				if str(self.target_unit).strip() != "Percent":
					frappe.throw(_("For Percentage measurement, Target Unit must be Percent."))
				if not (0 <= flt(self.target_value_numeric) <= 100):
					frappe.throw(_("Percentage target must be between 0 and 100."))
		elif mt in TEXT_TYPES:
			if not (self.target_value_text and str(self.target_value_text).strip()):
				frappe.throw(_("Target Value (Text) is required for Milestone or Boolean measurement types."))
			if self.target_value_numeric is not None:
				frappe.throw(_("Target Value (Numeric) must be empty for Milestone or Boolean measurement types."))
		else:
			frappe.throw(_("Invalid Measurement Type."))

	def _validate_period_fields(self):
		pt = self.target_period_type
		if pt not in ("Annual", "End of Plan", "Milestone Date"):
			frappe.throw(_("Target Period Type must be Annual, End of Plan, or Milestone Date."))

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

		ty = self.target_year
		td = self.target_due_date

		if pt == "Annual":
			if ty is None:
				frappe.throw(_("Target Year is required when Target Period Type is Annual."))
			if td is not None:
				frappe.throw(_("Target Due Date must be empty when Target Period Type is Annual."))
			y = cint(ty)
			if y < start_y or y > end_y:
				frappe.throw(
					_("Target Year must be between the strategic plan start year ({0}) and end year ({1}).").format(
						start_y, end_y
					)
				)
		elif pt == "End of Plan":
			if ty is not None:
				frappe.throw(_("Target Year must be empty when Target Period Type is End of Plan."))
			if td is not None:
				frappe.throw(_("Target Due Date must be empty when Target Period Type is End of Plan."))
		elif pt == "Milestone Date":
			if td is None:
				frappe.throw(_("Target Due Date is required when Target Period Type is Milestone Date."))
			if ty is not None:
				frappe.throw(_("Target Year must be empty when Target Period Type is Milestone Date."))

	def _validate_baseline_fields(self):
		mt = self.measurement_type
		if mt in NUMERIC_TYPES:
			if self.baseline_value_text:
				frappe.throw(_("Baseline Value (Text) must be empty for numeric-style measurement types."))
			if self.baseline_value_numeric is not None and flt(self.baseline_value_numeric) < 0:
				frappe.throw(_("Baseline numeric value must be at least 0."))
		elif mt in TEXT_TYPES:
			if self.baseline_value_numeric is not None:
				frappe.throw(_("Baseline Value (Numeric) must be empty for Milestone or Boolean measurement types."))
		if self.baseline_year is not None:
			plan_end = frappe.get_cached_value("Strategic Plan", self.strategic_plan, "end_year")
			if plan_end is not None and cint(self.baseline_year) > cint(plan_end):
				frappe.throw(_("Baseline year cannot be after the strategic plan end year ({0}).").format(plan_end))
