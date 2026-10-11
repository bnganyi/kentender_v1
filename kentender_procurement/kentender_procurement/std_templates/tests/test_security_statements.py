# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Tender's own security statements travel into the published facts (Project Owner, 10 October 2026), only when the
projection states them: every frozen release vector, built before they existed, compiles exactly as it did."""

from __future__ import annotations

import json
from pathlib import Path

from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.compiler import projection as proj, selectors

VECTORS = Path(__file__).resolve().parent / "vectors" / "release_1_4"
CONSTANTS = {"bank_guarantee_extra_days": 28, "insurance_guarantee_extra_days": 28}


class TestSecurityStatements(IntegrationTestCase):
	def projection(self, **stated):
		built = json.loads((VECTORS / "moh_input.json").read_text(encoding="utf-8"))
		built["tender"]["tender_security"].update(stated)
		return built

	def facts(self, built):
		return selectors._tender_security(built, {}, CONSTANTS)[0]["facts"]

	def test_a_projection_that_states_nothing_adds_no_fact(self):
		facts = self.facts(self.projection())
		self.assertNotIn("submission_method", facts)
		self.assertNotIn("original_delivery", facts)

	def test_a_stated_method_and_original_delivery_become_published_facts(self):
		built = self.projection(submission_method="Issuer supplies the instrument directly", original_delivery="Not required")
		proj.validate(built)  # the structural schema accepts them as optional
		facts = self.facts(built)
		self.assertEqual((facts["submission_method"], facts["original_delivery"]), ("Issuer supplies the instrument directly", "Not required"))

	def test_the_selector_declares_both_facts(self):
		declared = selectors.SELECTORS["SEL-TENDER-SECURITY"].facts
		self.assertIn("submission_method", declared)
		self.assertIn("original_delivery", declared)
