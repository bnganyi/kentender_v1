# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

KENTENDER_V1_ROOT = Path(__file__).resolve().parents[4]
if str(KENTENDER_V1_ROOT) not in sys.path:
	sys.path.insert(0, str(KENTENDER_V1_ROOT))

PYMUPDF_AVAILABLE = importlib.util.find_spec("fitz") is not None


@unittest.skipUnless(PYMUPDF_AVAILABLE, "pymupdf is required for verbatim extraction tests")
class TestVerbatimExtraction(unittest.TestCase):
	def setUp(self) -> None:
		from scripts.std_extraction.verbatim.extract_clauses import SYNTHETIC_MARKER, extract_verbatim_clauses
		from scripts.std_extraction.verbatim.extract_parameters import extract_verbatim_parameters
		from scripts.std_extraction.verbatim.reconcile_verbatim import build_reconciliation

		self.SYNTHETIC_MARKER = SYNTHETIC_MARKER
		self.extract_verbatim_clauses = extract_verbatim_clauses
		self.extract_verbatim_parameters = extract_verbatim_parameters
		self.build_reconciliation = build_reconciliation

	def test_all_locked_clauses_have_pdf_text(self) -> None:
		clauses = self.extract_verbatim_clauses()
		self.assertEqual(len(clauses), 94)
		missing = [row.clause_code for row in clauses if not row.full_clause_text]
		self.assertEqual(missing, [])

	def test_clause_text_is_not_register_synthetic_template(self) -> None:
		clauses = self.extract_verbatim_clauses()
		for clause in clauses:
			self.assertNotIn(self.SYNTHETIC_MARKER, clause.full_clause_text)

	def test_all_parameters_have_source_text(self) -> None:
		parameters = self.extract_verbatim_parameters()
		self.assertEqual(len(parameters), 155)
		missing = [row.parameter_code for row in parameters if not row.source_text]
		self.assertEqual(missing, [])

	def test_reconciliation_has_no_extraction_blockers(self) -> None:
		payload = self.build_reconciliation()
		extraction_blockers = [
			row
			for row in payload["findings"]
			if row.get("severity") == "BLOCKER"
			and row.get("finding_code")
			in {"CLAUSE_TEXT_MISSING", "PARAMETER_SOURCE_TEXT_MISSING", "EXTRACTION_LOW_CONFIDENCE"}
		]
		self.assertEqual(extraction_blockers, [])
