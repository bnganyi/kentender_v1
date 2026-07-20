# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Evidence: ACTIVE KE-PPRA-IT-2022-04 includes full form locked legal text."""

from __future__ import annotations

import unittest

import frappe

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
	ensure_active_canonical_ppra_it_std,
)
from kentender_procurement.std_engine.services.form_locked_text import (
	assert_form_locked_text_complete,
	inventory_form_locked_text,
)
from kentender_procurement.std_engine.services.render_service import render_section_preview


class TestFormLockedTextActivation(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		cls.result = ensure_active_canonical_ppra_it_std(force_reimport=False)

	def test_package_active(self):
		self.assertEqual(self.result.get("lifecycleState"), "ACTIVE")
		self.assertEqual(
			frappe.db.get_value("STD Version", CANONICAL_PACKAGE_ID, "lifecycle_state"),
			"ACTIVE",
		)

	def test_form_locked_inventory_complete(self):
		inv = inventory_form_locked_text(CANONICAL_PACKAGE_ID)
		self.assertTrue(inv.get("complete"), inv)
		self.assertEqual(inv.get("expectedFormCount"), 25)
		self.assertGreaterEqual(inv.get("formClauseCount"), 25)
		self.assertGreaterEqual(inv.get("contractClauseCount"), 1)
		assert_form_locked_text_complete(CANONICAL_PACKAGE_ID)

	def test_render_forms_and_contract_have_bodies(self):
		forms = render_section_preview(CANONICAL_PACKAGE_ID, "forms")
		self.assertGreaterEqual(int(forms.get("clauseCount") or 0), 25)
		self.assertIn("Form of Tender", forms.get("html") or "")
		contract = render_section_preview(CANONICAL_PACKAGE_ID, "contract_forms")
		self.assertGreaterEqual(int(contract.get("clauseCount") or 0), 1)
		self.assertGreater(len(contract.get("html") or ""), 500)

	def test_itt_is_official_not_fixture_sample(self):
		itt = render_section_preview(CANONICAL_PACKAGE_ID, "itt")
		html = (itt.get("html") or "").lower()
		self.assertIn("scope of tender", html)
		self.assertNotIn("tenderer shall prepare the tender in accordance", html)
