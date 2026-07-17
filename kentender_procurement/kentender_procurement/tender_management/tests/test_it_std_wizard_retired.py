# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Regression guards for IT STD Wizard retirement wiring."""

from __future__ import annotations

import os
import unittest

from kentender_procurement.tender_management.services import tm2_std_adapter


class TestItStdWizardRetired(unittest.TestCase):
	def test_hooks_no_active_it_wizard_assets(self) -> None:
		hooks_path = os.path.join(
			os.path.dirname(__file__),
			"..",
			"..",
			"hooks.py",
		)
		hooks_path = os.path.normpath(hooks_path)
		with open(hooks_path, encoding="utf-8") as f:
			text = f.read()
		self.assertIn("it_std_wizard_retired_page.js", text)
		self.assertIn("it-tender-configuration-dashboard", text)

	def test_tm2_adapter_returns_retired_for_instance_create(self) -> None:
		out = tm2_std_adapter.create_tender_std_instance("TND-TEST-001", "VER-1", "PROF-1")
		self.assertFalse(out.get("ok"))
		self.assertTrue(out.get("retired"))
		self.assertEqual(out.get("error_code"), "IT_STD_WIZARD_RETIRED")

	def test_retired_page_asset_exists(self) -> None:
		path = os.path.join(
			os.path.dirname(__file__),
			"..",
			"..",
			"public",
			"js",
			"it_std_wizard_retired_page.js",
		)
		self.assertTrue(os.path.exists(os.path.normpath(path)))
