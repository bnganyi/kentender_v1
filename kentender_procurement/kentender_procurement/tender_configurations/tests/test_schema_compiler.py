# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Unit tests: schema compiler from CFG → schema 10 shape."""

from __future__ import annotations

import unittest

from kentender_procurement.tender_configurations.services.e1_nssf_fixture_mapper import (
	EXPECTED_PRELIM_COUNT,
	EXPECTED_PRICE_LINE_COUNT,
	EXPECTED_REQUIREMENT_COUNT,
	EXPECTED_TECH_QUAL_COUNT,
	map_all_cfg_blobs,
)
from kentender_procurement.tender_configurations.services.schema_compiler import (
	SECTION_KEYS,
	compile_schema_from_mapped,
)


class TestSchemaCompiler(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.mapped = map_all_cfg_blobs()
		cls.schema = compile_schema_from_mapped(
			cls.mapped,
			configuration_id="TCFG-E1-NSSF-ERP",
			std_version="TCFG-FIXTURE-IT-ACTIVE",
		)

	def test_ten_section_keys(self):
		keys = [s.get("key") for s in self.schema["sections"]]
		for key in SECTION_KEYS:
			self.assertIn(key, keys)

	def test_matrix_and_price_counts(self):
		by_key = {s["key"]: s for s in self.schema["sections"]}
		self.assertEqual(
			len(by_key["technical_compliance_matrix"].get("requirements") or []),
			EXPECTED_REQUIREMENT_COUNT,
		)
		self.assertEqual(
			len(by_key["price_schedule"].get("price_lines") or []),
			EXPECTED_PRICE_LINE_COUNT,
		)
		self.assertEqual(
			len(by_key["preliminary_documents"].get("requirements") or []),
			EXPECTED_PRELIM_COUNT,
		)
		self.assertEqual(
			len(by_key["technical_qualification"].get("requirements") or []),
			EXPECTED_TECH_QUAL_COUNT,
		)

	def test_stamps_and_hash(self):
		self.assertEqual(self.schema["configuration_id"], "TCFG-E1-NSSF-ERP")
		self.assertEqual(self.schema["std_version"], "TCFG-FIXTURE-IT-ACTIVE")
		self.assertEqual(self.schema["compiled_from"], "tender_configuration_cfg")
		self.assertTrue(self.schema.get("schema_hash"))
		self.assertEqual(len(self.schema["schema_hash"]), 64)
