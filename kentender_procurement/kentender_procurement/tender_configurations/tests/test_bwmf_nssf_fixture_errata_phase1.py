# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G1 Phase 1 — NSSF fixture errata + corrected BWMF-T049 / BWMF-T054."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compatibility import (
	LEGACY_PACK10_BIDDER_SUBMISSION_SCHEMA_COMPATIBILITY_BOUNDARY,
	LEGACY_PACK10_IS_CANONICAL_RUNTIME_CONTRACT,
	LEGACY_PACK10_SCHEMA_DIGEST,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.nssf_fixture_errata import (
	NSSF_CANONICAL_CONTENT_SECTION_KEYS,
	NSSF_DEADLINE,
	NSSF_EXPECTED_CONTENT_SECTION_COUNT,
	NSSF_FORBIDDEN_LEGACY_CONTENT_SECTION_KEYS,
	NSSF_LOT_MODEL,
	NSSF_SECURITY_DECISION_ID,
	assert_nssf_content_sections,
	lots_and_alternatives_omitted,
	publication_readiness_requires_security_decision,
)
from kentender_procurement.tender_configurations.services.schema_compiler import SECTION_KEYS

_EXPECTATION = (
	Path(__file__).resolve().parents[1]
	/ "bidder_workspace_manifest"
	/ "fixtures"
	/ "nssf_golden_section_expectation.json"
)


class TestBwmfNssfFixtureErrataPhase1(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		with _EXPECTATION.open(encoding="utf-8") as fh:
			cls.expectation = json.load(fh)

	def test_bwmf_t049_expects_ten_nssf_content_sections(self):
		"""BWMF-T049 (corrected): ten content sections, not nine."""
		keys = self.expectation["content_section_keys"]
		self.assertEqual(len(keys), 10)
		self.assertEqual(len(keys), NSSF_EXPECTED_CONTENT_SECTION_COUNT)
		assert_nssf_content_sections(keys)
		# Stale nine-section expectation must fail
		nine = [k for k in keys if k != "tender_security"]
		self.assertEqual(len(nine), 9)
		with self.assertRaises(ValueError):
			assert_nssf_content_sections(nine)

	def test_bwmf_t054_security_decision_bound_readiness_passes(self):
		"""BWMF-T054 (corrected): NSSF-DEC-SEC-001 bound → readiness passes."""
		self.assertEqual(self.expectation["security_decision_id"], NSSF_SECURITY_DECISION_ID)
		self.assertTrue(
			publication_readiness_requires_security_decision(NSSF_SECURITY_DECISION_ID)
		)
		self.assertFalse(publication_readiness_requires_security_decision(None))
		self.assertFalse(publication_readiness_requires_security_decision("unresolved_pi"))
		# Stale expectation: "must be resolved before readiness" as a permanent block is wrong
		# once SEC-001 is bound — readiness helper returns True.
		self.assertTrue(
			publication_readiness_requires_security_decision(
				self.expectation["security_decision_id"]
			)
		)

	def test_errata_includes_tender_security_and_statutory_declarations(self):
		keys = set(NSSF_CANONICAL_CONTENT_SECTION_KEYS)
		self.assertIn("tender_security", keys)
		self.assertIn("statutory_declarations", keys)

	def test_errata_omits_lots_and_alternatives(self):
		self.assertTrue(lots_and_alternatives_omitted(NSSF_LOT_MODEL))
		self.assertTrue(lots_and_alternatives_omitted(self.expectation["lot_model"]))
		self.assertFalse(
			lots_and_alternatives_omitted(
				{"mode": "multi_lot", "bidder_selectable_lots": True, "alternatives_permitted": True}
			)
		)

	def test_errata_removes_contract_conditions_and_final_declaration_content(self):
		keys = set(NSSF_CANONICAL_CONTENT_SECTION_KEYS)
		for forbidden in NSSF_FORBIDDEN_LEGACY_CONTENT_SECTION_KEYS:
			self.assertNotIn(forbidden, keys)
		self.assertNotIn("contract_terms_acknowledgement", keys)
		self.assertNotIn("final_declaration_and_submit", keys)

	def test_errata_deadline(self):
		self.assertEqual(self.expectation["deadline"], NSSF_DEADLINE)
		self.assertEqual(NSSF_DEADLINE, "2026-06-30T11:00:00+03:00")

	def test_legacy_pack10_is_negative_fixture_only(self):
		self.assertEqual(
			LEGACY_PACK10_BIDDER_SUBMISSION_SCHEMA_COMPATIBILITY_BOUNDARY,
			"LEGACY_PACK10_BIDDER_SUBMISSION_SCHEMA_COMPATIBILITY_BOUNDARY",
		)
		self.assertFalse(LEGACY_PACK10_IS_CANONICAL_RUNTIME_CONTRACT)
		self.assertTrue(LEGACY_PACK10_SCHEMA_DIGEST.startswith("sha256:4d461f49"))
		# Live pack-10 SECTION_KEYS must not equal canonical errata (compat boundary)
		self.assertNotEqual(tuple(SECTION_KEYS), NSSF_CANONICAL_CONTENT_SECTION_KEYS)
		self.assertIn("contract_terms_acknowledgement", SECTION_KEYS)
		self.assertIn("final_declaration_and_submit", SECTION_KEYS)
		self.assertNotIn("tender_security", SECTION_KEYS)
