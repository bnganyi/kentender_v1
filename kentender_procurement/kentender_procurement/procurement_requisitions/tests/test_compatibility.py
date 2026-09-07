# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §5A compatibility test — pure, DB-free (REQ-AC-053)."""

from __future__ import annotations

import unittest

from kentender_procurement.procurement_requisitions.services import compatibility


def _fixture_projection(**overrides):
	base = {
		"procurement_category": "Goods",
		"requirement_type": "Goods",
		"reservation_category": "None",
		"lotting_indicator": "Single lot",
		"currency": "KES",
		"award_packages": 1,
	}
	base.update(overrides)
	return base


class TestCompatibility(unittest.TestCase):
	def test_the_fixture_projection_is_compatible(self):
		self.assertTrue(compatibility.is_compatible(_fixture_projection()))
		self.assertIsNone(compatibility.first_failure(_fixture_projection()))

	def test_every_row_is_independently_named_on_failure(self):
		cases = {
			"procurement_category": _fixture_projection(procurement_category="Works"),
			"requirement_type": _fixture_projection(requirement_type="Consulting services"),
			"reservation_category": _fixture_projection(reservation_category="Micro, small and medium enterprise"),
			"lotting_indicator": _fixture_projection(lotting_indicator="Packaged into lots"),
			"currency": _fixture_projection(currency="USD"),
			"award_packages": _fixture_projection(award_packages=2),
		}
		for expected_test, projection in cases.items():
			failure = compatibility.first_failure(projection)
			self.assertIsNotNone(failure, f"{expected_test} case unexpectedly compatible")
			self.assertEqual(failure.test, expected_test)

	def test_every_tender_renderable_reservation_category_passes(self):
		for category in ("None", "Youth", "Women", "Persons with disabilities", "Other disadvantaged group"):
			self.assertTrue(compatibility.is_compatible(_fixture_projection(reservation_category=category)), category)

	def test_a_non_renderable_reservation_category_fails(self):
		self.assertFalse(compatibility.is_compatible(_fixture_projection(reservation_category="Regional — county")))
