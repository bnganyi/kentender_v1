"""Phase C — business ID numbering service."""

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.business_id_service import generate_business_id


class TestBusinessIdNumbering(IntegrationTestCase):
	doctype = None

	def tearDown(self):
		frappe.db.delete(
			"Business ID Counter",
			{"prefix": "KT-TEST", "entity": "ENT", "year": 2030},
		)
		frappe.db.commit()
		super().tearDown()

	def test_generate_business_id_increments_sequence(self):
		frappe.db.delete(
			"Business ID Counter",
			{"prefix": "KT-TEST", "entity": "ENT", "year": 2030},
		)
		frappe.db.commit()

		a = generate_business_id("KT-TEST", "ENT", 2030)
		b = generate_business_id("KT-TEST", "ENT", 2030)

		self.assertEqual(a, "KT-TEST-ENT-2030-0001")
		self.assertEqual(b, "KT-TEST-ENT-2030-0002")

	def test_different_year_independent_sequence(self):
		frappe.db.delete("Business ID Counter", {"prefix": "KT-Y", "entity": "E", "year": 2031})
		frappe.db.delete("Business ID Counter", {"prefix": "KT-Y", "entity": "E", "year": 2032})
		frappe.db.commit()

		x = generate_business_id("KT-Y", "E", 2031)
		y = generate_business_id("KT-Y", "E", 2032)
		self.assertTrue(x.endswith("-0001"))
		self.assertTrue(y.endswith("-0001"))

		frappe.db.delete("Business ID Counter", {"prefix": "KT-Y", "entity": "E", "year": 2031})
		frappe.db.delete("Business ID Counter", {"prefix": "KT-Y", "entity": "E", "year": 2032})
		frappe.db.commit()
