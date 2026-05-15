# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-007 — Technical references JSON separated from summaries + Desk collapsible section."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.technical_refs import (
	TECHNICAL_REFS_JSON_MAX_SERIALIZED_BYTES,
	parse_validate_technical_refs_json,
)


class TestR1007TechnicalRefsPure(unittest.TestCase):
	def test_empty_returns_none(self):
		self.assertIsNone(parse_validate_technical_refs_json(None))
		self.assertIsNone(parse_validate_technical_refs_json({}))
		self.assertIsNone(parse_validate_technical_refs_json([]))

	def test_accepts_object_and_array(self):
		self.assertEqual(parse_validate_technical_refs_json({"tender_code": "TND-1"}), {"tender_code": "TND-1"})
		self.assertEqual(parse_validate_technical_refs_json(["a", "b"]), ["a", "b"])

	def test_rejects_primitive(self):
		with self.assertRaises(ValueError):
			parse_validate_technical_refs_json('"x"')

	def test_rejects_oversized(self):
		big = {"k": "z" * (TECHNICAL_REFS_JSON_MAX_SERIALIZED_BYTES + 10)}
		with self.assertRaises(ValueError) as ctx:
			parse_validate_technical_refs_json(big)
		self.assertIn("bytes", str(ctx.exception))


class TestR1007TechnicalRefsMeta(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.clear_cache(doctype="Procurement Handoff Card")

	def test_section_and_field_exist(self):
		meta = frappe.get_meta("Procurement Handoff Card")
		names = {df.fieldname for df in meta.fields}
		self.assertIn("section_technical_refs", names)
		self.assertIn("technical_refs_json", names)
		section = next(df for df in meta.fields if df.fieldname == "section_technical_refs")
		self.assertEqual(int(section.collapsible or 0), 1)


class TestR1007TechnicalRefsOnHandoffCard(IntegrationTestCase):
	_journey_code = "JRN-TEST-R1007-001"
	_handoff_code = "HOFF-TEST-R1007-001"

	def tearDown(self):
		frappe.db.delete("Procurement Handoff Card", {"handoff_code": self._handoff_code})
		frappe.db.delete("Procurement Journey", {"journey_code": self._journey_code})
		super().tearDown()

	def _insert_journey(self):
		frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": self._journey_code,
				"journey_title": "R1-007 parent",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "tender_published",
				"current_stage_label": "Tender Published",
				"current_status_category": "Completed",
				"current_owner_module": "Tender Management",
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
			}
		).insert()

	def _minimal_evidence(self):
		return {
			"links": [
				{
					"label": "Publication Snapshot",
					"object_type": "Publication Snapshot",
					"object_code": "PUBSNAP-TST-007",
					"module": "Tender Management",
					"route": "/desk/",
					"visibility": "Internal",
				}
			]
		}

	def _base(self):
		return {
			"doctype": "Procurement Handoff Card",
			"handoff_code": self._handoff_code,
			"handoff_title": "R1-007 technical refs",
			"journey_code": self._journey_code,
			"source_module": "Planning",
			"target_module": "Tender Management",
			"source_object_type": "Procurement Package",
			"source_object_code": "PKG-007",
			"status": "Draft",
			"generated_by": "USER-007",
			"locked_summary": {},
			"passed_forward_summary": {},
			"next_action": "n/a",
			"evidence_links_json": self._minimal_evidence(),
			"is_master_seed": 0,
		}

	def test_insert_with_technical_refs_object(self):
		self._insert_journey()
		kw = self._base()
		kw["technical_refs_json"] = {
			"tender_code": "TND-MOH-2026-001",
			"std_template_version_code": "STDTV-WORKS-BUILDING-CIVIL-APR2022",
			"publication_snapshot_code": "PUBSNAP-TND-MOH-2026-001-V2",
		}
		frappe.get_doc(kw).insert()
		reloaded = frappe.get_doc("Procurement Handoff Card", self._handoff_code)
		tr = reloaded.technical_refs_json
		if isinstance(tr, str):
			tr = frappe.parse_json(tr)
		self.assertEqual(tr.get("tender_code"), "TND-MOH-2026-001")

	def test_insert_rejects_oversized_technical_refs(self):
		self._insert_journey()
		kw = self._base()
		kw["technical_refs_json"] = {"blob": "x" * (TECHNICAL_REFS_JSON_MAX_SERIALIZED_BYTES + 500)}
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(kw).insert()
