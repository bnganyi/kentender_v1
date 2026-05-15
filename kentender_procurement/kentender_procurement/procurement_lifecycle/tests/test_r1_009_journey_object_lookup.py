# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-009 / LV-R1-009-02 — object→journey lookup resolves Demand / Package / TM2 to same journey_code."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.journey_object_lookup import (
	JOURNEY_OBJECT_LOOKUP_REF_FIELDS,
	get_procurement_journey_by_object,
	journey_lookup_sql_explanation,
	ref_field_for_object_type,
	resolve_journey_code_for_object,
)


class TestR1009ObjectTypeToRefField(unittest.TestCase):
	"""LV-R1-009-01 — canonical object_type strings map to Journey ref columns."""

	def test_pack_examples(self):
		self.assertEqual(ref_field_for_object_type("Demand"), "demand_ref")
		self.assertEqual(ref_field_for_object_type("Procurement Package"), "procurement_package_ref")
		self.assertEqual(ref_field_for_object_type("TM2 Tender"), "tm2_tender_ref")

	def test_whitespace_insensitive(self):
		self.assertEqual(ref_field_for_object_type("  demand  "), "demand_ref")

	def test_unknown_returns_none(self):
		self.assertIsNone(ref_field_for_object_type("Unknown Widget"))


class TestR1009QueryPlanDoc(unittest.TestCase):
	def test_explanation_mentions_indexed_column(self):
		text = journey_lookup_sql_explanation("Demand")
		self.assertIn("demand_ref", text)
		self.assertIn("tabProcurement Journey", text)

	def test_explanation_unknown_type(self):
		text = journey_lookup_sql_explanation("NoSuchType")
		self.assertIn("not supported", text.lower())


class TestR1009JourneyObjectLookupIntegration(IntegrationTestCase):
	"""LV-R1-009-02 — one journey row; three object lookups share journey_code."""

	JOURNEY = "JRN-TEST-R1009-001"
	DEM = "DEM-TEST-R1009-001"
	PKG = "PKG-TEST-R1009-001"
	TND = "TND-TEST-R1009-001"

	def tearDown(self):
		frappe.db.delete("Procurement Journey", {"name": self.JOURNEY})
		super().tearDown()

	def _insert_fixture_journey(self):
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": self.JOURNEY,
				"journey_title": "R1-009 object lookup fixture",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "tender_published",
				"current_stage_label": "Tender Published",
				"current_status_category": "Completed",
				"current_owner_module": "Tender Management",
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
				"demand_ref": self.DEM,
				"procurement_package_ref": self.PKG,
				"tm2_tender_ref": self.TND,
			}
		)
		doc.insert()

	def test_demand_package_tm2_resolve_same_journey_code(self):
		self._insert_fixture_journey()
		jd = resolve_journey_code_for_object("Demand", self.DEM)
		jp = resolve_journey_code_for_object("Procurement Package", self.PKG)
		jt = resolve_journey_code_for_object("TM2 Tender", self.TND)
		self.assertEqual(jd, self.JOURNEY)
		self.assertEqual(jp, self.JOURNEY)
		self.assertEqual(jt, self.JOURNEY)

	def test_get_procurement_journey_by_object_minimal_payload(self):
		self._insert_fixture_journey()
		row = get_procurement_journey_by_object("TM2 Tender", self.TND)
		self.assertIsNotNone(row)
		self.assertEqual(row.get("journey_code"), self.JOURNEY)
		self.assertEqual(row.get("journey_title"), "R1-009 object lookup fixture")

	def test_empty_code_returns_none(self):
		self._insert_fixture_journey()
		self.assertIsNone(resolve_journey_code_for_object("Demand", ""))
		self.assertIsNone(resolve_journey_code_for_object("Demand", "   "))

	def test_unknown_type_returns_none(self):
		self._insert_fixture_journey()
		self.assertIsNone(resolve_journey_code_for_object("Unknown", self.DEM))

	def test_miss_returns_none(self):
		self._insert_fixture_journey()
		self.assertIsNone(resolve_journey_code_for_object("Demand", "DEM-NONEXISTENT-999"))

	def test_pack_ref_columns_are_search_indexed(self):
		"""LV-R1-009-01 — DocType indexes support point lookups on ref fields."""
		meta = frappe.get_meta("Procurement Journey")
		indexed = {df.fieldname for df in (meta.fields or []) if getattr(df, "search_index", None)}
		for fn in sorted(JOURNEY_OBJECT_LOOKUP_REF_FIELDS):
			with self.subTest(field=fn):
				self.assertIn(fn, indexed)
