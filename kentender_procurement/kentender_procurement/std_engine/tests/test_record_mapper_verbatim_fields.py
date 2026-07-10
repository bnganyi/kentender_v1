# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Record mapper coverage for verbatim package fields."""

from __future__ import annotations

import unittest

from kentender_procurement.std_engine.package_import.record_mapper import (
	PackageContext,
	map_clause_record,
	map_parameter_record,
	map_source_anchor_record,
)


class TestRecordMapperVerbatimFields(unittest.TestCase):
	def setUp(self) -> None:
		self.ctx = PackageContext(
			package_id="KE-PPRA-IT-2022-04",
			family_code="KE-PPRA-IT",
			version_code="KE-PPRA-IT-2022-04",
		)

	def test_source_anchor_maps_page_and_hash_fields(self) -> None:
		mapped = map_source_anchor_record(
			{
				"source_anchor_key": "KE-PPRA-IT-2022-04.anchor.itt.itt_001",
				"source_document_key": "DOC-10-IT-STD-2022-04",
				"source_section_ref": "ITT",
				"source_clause_ref": "ITT-001",
				"source_page_start": 17,
				"source_page_end": 17,
				"normalized_text_hash": "abc123",
				"verification_status": "PENDING_LEGAL_REVIEW",
			},
			self.ctx,
		)
		self.assertEqual(mapped["page_from"], 17)
		self.assertEqual(mapped["page_to"], 17)
		self.assertEqual(mapped["anchor_hash"], "abc123")
		self.assertEqual(mapped["validation_status"], "PENDING_LEGAL_REVIEW")

	def test_clause_maps_verification_status(self) -> None:
		mapped = map_clause_record(
			{
				"clause_key": "KE-PPRA-IT-2022-04.clause.itt.itt_001_scope",
				"section_key": "KE-PPRA-IT-2022-04.section.itt",
				"clause_code": "ITT-001",
				"display_title": "Scope of Tender",
				"full_clause_text": "1.1 Example",
				"normalized_text_hash": "hash-1",
				"verification_status": "PENDING_LEGAL_REVIEW",
				"clause_text_source": "PDF_VERBATIM",
			},
			self.ctx,
		)
		self.assertEqual(mapped["validation_status"], "PENDING_LEGAL_REVIEW")
		self.assertEqual(mapped["content_hash"], "hash-1")

	def test_parameter_maps_content_hash(self) -> None:
		mapped = map_parameter_record(
			{
				"parameter_key": "KE-PPRA-IT-2022-04.parameter.tds.013",
				"parameter_code": "TDS-013",
				"display_label": "Procuring Entity",
				"normalized_text_hash": "param-hash",
				"verification_status": "PENDING_LEGAL_REVIEW",
			},
			self.ctx,
		)
		self.assertEqual(mapped["content_hash"], "param-hash")
		self.assertEqual(mapped["validation_status"], "PENDING_LEGAL_REVIEW")
