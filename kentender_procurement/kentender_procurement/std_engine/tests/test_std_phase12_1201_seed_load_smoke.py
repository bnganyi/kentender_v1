# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CURSOR-1201 — std_engine_works_seed_load_tests (Smoke Contract §22)."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.tests.phase12_smoke_helpers import (
	BUILDING_PROFILE_CODE,
	BUILDING_TEMPLATE_VERSION_CODE,
	DOC1_SOURCE_DOCUMENT_CODE,
	STD_WORKS_FAMILY_CODE,
	doc1_building_seed_loaded,
)


@unittest.skipUnless(doc1_building_seed_loaded(), "DOC1 Works Building seed not loaded on this site")
class TestStdEngineWorksSeedLoadTests(IntegrationTestCase):
	def test_doc1_source_document_exists(self):
		row = frappe.db.get_value(
			"Source Document Registry",
			{"source_document_code": DOC1_SOURCE_DOCUMENT_CODE},
			["source_document_code", "status", "procurement_category"],
			as_dict=True,
		)
		self.assertTrue(row, msg=f"Missing Source Document Registry:{DOC1_SOURCE_DOCUMENT_CODE}")
		self.assertEqual(row.source_document_code, DOC1_SOURCE_DOCUMENT_CODE)

	def test_std_works_family_active(self):
		row = frappe.db.get_value(
			"STD Template Family",
			{"template_code": STD_WORKS_FAMILY_CODE},
			["template_code", "family_status", "procurement_category"],
			as_dict=True,
		)
		self.assertTrue(row, msg=f"Missing STD Template Family:{STD_WORKS_FAMILY_CODE}")
		self.assertEqual(row.family_status, "Active")

	def test_building_template_version_active(self):
		row = frappe.db.get_value(
			"STD Template Version",
			{"version_code": BUILDING_TEMPLATE_VERSION_CODE},
			[
				"version_code",
				"version_status",
				"source_document_code",
				"legal_review_status",
				"policy_review_status",
				"structure_validation_status",
			],
			as_dict=True,
		)
		self.assertTrue(row, msg=f"Missing STD Template Version:{BUILDING_TEMPLATE_VERSION_CODE}")
		self.assertEqual(row.version_status, "Active")
		self.assertEqual(row.source_document_code, DOC1_SOURCE_DOCUMENT_CODE)
		self.assertEqual(row.legal_review_status, "Approved")
		self.assertEqual(row.policy_review_status, "Approved")
		self.assertEqual(row.structure_validation_status, "Pass")

	def test_building_civil_profile_active(self):
		row = frappe.db.get_value(
			"STD Applicability Profile",
			{"profile_code": BUILDING_PROFILE_CODE},
			["profile_code", "profile_status", "version_code"],
			as_dict=True,
		)
		self.assertTrue(row, msg=f"Missing STD Applicability Profile:{BUILDING_PROFILE_CODE}")
		self.assertEqual(row.profile_status, "Active")
		self.assertEqual(row.version_code, BUILDING_TEMPLATE_VERSION_CODE)

	def test_parts_exist_for_building_version(self):
		n = frappe.db.count("STD Part Definition", {"version_code": BUILDING_TEMPLATE_VERSION_CODE})
		self.assertGreaterEqual(n, 1, msg=f"Expected parts for version_code={BUILDING_TEMPLATE_VERSION_CODE}, count={n}")

	def test_sections_exist_for_building_version(self):
		n = frappe.db.count("STD Section Definition", {"version_code": BUILDING_TEMPLATE_VERSION_CODE})
		self.assertGreaterEqual(n, 9, msg=f"Expected sections for version_code={BUILDING_TEMPLATE_VERSION_CODE}, count={n}")

	def test_source_trace_on_sections(self):
		missing = frappe.db.sql(
			"""
			select section_code from `tabSTD Section Definition`
			where version_code = %s and (source_document_code is null or source_document_code = '')
			limit 5
			""",
			(BUILDING_TEMPLATE_VERSION_CODE,),
		)
		self.assertFalse(missing, msg=f"Sections missing source_document_code: {missing}")
