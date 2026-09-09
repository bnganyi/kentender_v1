# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §8 — the control catalogue itself (pure tests, §18
layer 1): types, ranges, options, conditionality, defaults, allow-lists."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_preparation.services import controls
from kentender_procurement.tender_preparation.services.errors import TenderPreparationError


class TestCatalogue(IntegrationTestCase):
	def test_the_catalogue_covers_exactly_the_three_officer_tasks(self):
		self.assertEqual(set(controls.FIELDS_BY_TASK), {1, 4, 5})
		self.assertEqual(len(controls.FIELDS_BY_TASK[1]), 11)
		self.assertEqual(len(controls.FIELDS_BY_TASK[4]), 7)
		self.assertEqual(len(controls.FIELDS_BY_TASK[5]), 7)

	def test_booleans_reject_free_text(self):
		for bad in ("yes", "no", "maybe", 2, "Y", None):
			_, error = controls.coerce("pre_tender_meeting", bad)
			self.assertTrue(error, repr(bad))
		for good, expected in ((True, True), ("1", True), (0, False), ("false", False)):
			value, error = controls.coerce("pre_tender_meeting", good)
			self.assertEqual((value, error), (expected, ""))

	def test_finite_choices_reject_unknown_values(self):
		self.assertTrue(controls.coerce("payment_timing_days", "35")[1])
		self.assertEqual(controls.coerce("payment_timing_days", "45"), ("45", ""))
		self.assertTrue(controls.coerce("after_sales_evidence", "Something else")[1])
		self.assertTrue(controls.coerce("experience_period_years", 4)[1])

	def test_numeric_ranges_and_precision(self):
		self.assertTrue(controls.coerce("tender_validity_days", 0)[1])
		self.assertTrue(controls.coerce("tender_validity_days", 366)[1])
		self.assertEqual(controls.coerce("tender_validity_days", "120"), (120, ""))
		self.assertTrue(controls.coerce("performance_security_percent", 0.5)[1])
		self.assertEqual(controls.coerce("performance_security_percent", "7.5"), (7.5, ""))
		self.assertTrue(controls.coerce("delay_damages_per_week_percent", 1.5)[1])
		self.assertTrue(controls.coerce("maximum_delay_damages_percent", 4)[1])
		self.assertTrue(controls.coerce("tender_security_amount", 0)[1])
		self.assertTrue(controls.coerce("tender_security_amount", -5)[1])
		self.assertEqual(controls.coerce("tender_security_amount", "500,000.00"), (500000.0, ""))

	def test_text_controls_reject_markup(self):
		self.assertTrue(controls.coerce("tender_title", "<b>Laptops</b>")[1])
		self.assertTrue(controls.coerce("tender_title", "x" * 161)[1])
		self.assertEqual(controls.coerce("tender_title", "  Supply of laptops ")[0], "Supply of laptops")

	def test_conditionality_follows_the_switches(self):
		state = {"pre_tender_meeting": False}
		self.assertFalse(controls.applies("meeting_datetime", state))
		self.assertFalse(controls.applies("meeting_venue", {"pre_tender_meeting": True, "meeting_mode": "Online"}))
		self.assertTrue(controls.applies("meeting_venue", {"pre_tender_meeting": True, "meeting_mode": "Physical"}))
		self.assertFalse(controls.applies("performance_security_percent", {"performance_security_required": False}))

	def test_defaults_match_the_spec(self):
		snapshot = {"requirement_title": "Clinical training laptops", "onsite_support_required": True, "manufacturer_support_required": True}
		d = controls.defaults(snapshot)
		self.assertEqual(d["tender_validity_days"], 120)
		self.assertTrue(d["manufacturer_authorisation_required"] and d["datasheets_required"])
		self.assertFalse(d["past_experience_required"])
		self.assertEqual(d["payment_timing_days"], "30")
		self.assertEqual(d["performance_security_percent"], 10)
		self.assertEqual(d["delay_damages_per_week_percent"], 0.5)
		self.assertEqual(d["maximum_delay_damages_percent"], 10)
		self.assertEqual(d["tender_title"], "Clinical training laptops")
		self.assertTrue(d["after_sales_evidence_required"])
		self.assertFalse(controls.defaults({"requirement_title": "x"})["after_sales_evidence_required"])

	def test_validate_rejects_inherited_names_and_unknown_fields(self):
		with self.assertRaises(TenderPreparationError) as ctx:
			controls.validate({"quantity": 5}, {})
		self.assertEqual(ctx.exception.code, "TPR_INHERITED_EDIT")
		clean, errors = controls.validate({"tender_title": "Laptops", "colour": "blue"}, {})
		self.assertEqual(clean, {"tender_title": "Laptops"})
		self.assertEqual(errors, {"colour": "Unknown field."})

	def test_missing_lists_only_applicable_required_fields(self):
		state = {f: None for f in controls.CATALOGUE}
		state.update({"pre_tender_meeting": False, "past_experience_required": False, "after_sales_evidence_required": False, "performance_security_required": False})
		missing = {field for _, field, _ in controls.missing(state)}
		self.assertIn("issue_date", missing)
		self.assertNotIn("meeting_datetime", missing)
		self.assertNotIn("minimum_comparable_contracts", missing)
		self.assertNotIn("performance_security_percent", missing)

	def test_no_scope_argument_exists_in_the_catalogue(self):
		"""TPR-AC-030 — no PE/FY control anywhere."""
		for name in controls.CATALOGUE:
			self.assertNotIn("procuring_entity", name)
			self.assertNotIn("fiscal_year", name)
			self.assertNotIn("pe_fy", name)
