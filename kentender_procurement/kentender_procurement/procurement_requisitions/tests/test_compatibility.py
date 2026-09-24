# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §5A — the nine compatibility checks, pure and DB-free
(REQ19-AC-053, REQ19-AC-055, REQ110-AC-011, REQ111-AC-005)."""

from __future__ import annotations

import unittest

from kentender_procurement.procurement_requisitions.services import compatibility

TEMPLATE = {
	"template_key": "IT-EQUIPMENT-OPEN-V1", "available": True, "county_residents": False, "method": "Open Tender",
	"categories": ("None", "Youth", "Women", "Persons with disabilities"),
}


def projection(**overrides):
	base = {
		"procurement_category": "Goods", "requirement_type": "Goods", "reservation_category": "Youth",
		"reservation_rule": {"snapshot_id": "RRV-1", "available": True}, "county_resident_reservation": False,
		"county_rule": {"available": True}, "lotting_indicator": "Single lot", "currency": "KES", "award_packages": 1,
		"procurement_method": "Open Tender", "plan_horizon": "Single year",
	}
	base.update(overrides)
	return base


class TestNineChecks(unittest.TestCase):
	def test_the_youth_fixture_passes_all_nine_in_table_order_with_the_board_results(self):
		rows = compatibility.check(projection(), TEMPLATE)
		self.assertEqual(len(rows), 9)
		self.assertTrue(all(r.ok for r in rows))
		self.assertEqual(
			[(r.label, r.result) for r in rows],
			[
				("Procurement category", "Goods"),
				("Requirement type", "Straightforward off-the-shelf IT equipment"),
				("Planned designation", "Youth — supported; exact verified rule snapshot bound"),
				("County-residents restriction", "Not applicable"),
				("Lotting indicator", "Single lot"),
				("Currency", "KES"),
				("Award package", "One"),
				("Planned method", "Open Tender"),
				("Plan horizon", "Single year"),
			],
		)

	def test_none_designation_is_compatible_when_every_other_guard_passes(self):
		self.assertIsNone(compatibility.first_failure(projection(reservation_category="None"), TEMPLATE))

	def test_each_check_fails_independently_and_is_named(self):
		cases = {
			"procurement_category": projection(procurement_category="Works"),
			"requirement_type": projection(requirement_type="Consulting services"),
			"reservation_category": projection(reservation_category="Other disadvantaged group"),
			"county_resident_reservation": projection(county_resident_reservation=True),
			"lotting_indicator": projection(lotting_indicator="Packaged into lots"),
			"currency": projection(currency="USD"),
			"award_packages": projection(award_packages=2),
			"procurement_method": projection(procurement_method="Restricted Tender"),
			"plan_horizon": projection(plan_horizon="Multi-year"),
		}
		for expected, proj in cases.items():
			with self.subTest(expected):
				failures = [r.test for r in compatibility.check(proj, TEMPLATE) if not r.ok]
				self.assertEqual(failures, [expected])

	def test_a_supported_designation_with_no_verified_rule_is_rule_unavailable_not_unsupported(self):
		failure = compatibility.first_failure(projection(reservation_rule={"available": False}), TEMPLATE)
		self.assertEqual(failure.test, "reservation_category")
		self.assertEqual(failure.code, "REQ_RESERVATION_RULE_UNAVAILABLE")

	def test_an_unsupported_designation_is_product_unsupported(self):
		failure = compatibility.first_failure(projection(reservation_category="Other disadvantaged group"), TEMPLATE)
		self.assertEqual(failure.code, "REQ_PRODUCT_UNSUPPORTED")

	def test_a_template_that_is_not_available_fails_the_designation_check(self):
		failure = compatibility.first_failure(projection(), {**TEMPLATE, "available": False})
		self.assertEqual(failure.test, "reservation_category")

	def test_county_needs_template_support_and_then_a_verified_rule(self):
		self.assertEqual(compatibility.first_failure(projection(county_resident_reservation=True), TEMPLATE).code, "REQ_PRODUCT_UNSUPPORTED")
		with_county = {**TEMPLATE, "county_residents": True}
		failure = compatibility.first_failure(projection(county_resident_reservation=True, county_rule={"available": False}), with_county)
		self.assertEqual(failure.code, "REQ_RESERVATION_RULE_UNAVAILABLE")
		self.assertIsNone(compatibility.first_failure(projection(county_resident_reservation=True), with_county))

	def test_multi_year_has_no_justification_bypass(self):
		failure = compatibility.first_failure(projection(plan_horizon="Multi-year", multi_year_justification="A long justification text."), TEMPLATE)
		self.assertEqual(failure.test, "plan_horizon")
		self.assertEqual(failure.failure, "This release supports purchases completed within one financial year.")

	def test_no_app_wide_reservation_arithmetic_is_read(self):
		# REQ111-AC-001: a projection carrying APP-wide fields changes nothing.
		noisy = projection(eligible_value="1.00", target_percent=30, qualifying_share_percent=0, remaining="99.00")
		self.assertEqual([r.as_dict() for r in compatibility.check(noisy, TEMPLATE)], [r.as_dict() for r in compatibility.check(projection(), TEMPLATE)])
