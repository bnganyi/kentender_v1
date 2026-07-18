# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""UI-01 mockup seed — nine CFG focus configs + showcase."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui01_mockup_seed import (
	seed_ui01_mockup_configurations,
)
from kentender_procurement.tender_configurations.services.configuration_home import (
	get_configuration_home,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	ALLOWED_STEP_STATUSES,
)


class TestUi01MockupSeed(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui01_mockup_configurations(clear=True)

	def test_showcase_and_nine_focus_configs(self):
		self.assertEqual(len(self.seed["configurations"]), 10)
		self.assertIn("SHOWCASE", self.seed["by_step"])
		for i in range(1, 10):
			self.assertIn(f"CFG-0{i}", self.seed["by_step"])

	def test_showcase_exposes_all_allowed_step_statuses(self):
		home = get_configuration_home(self.seed["showcase_id"])
		labels = {s["status_label"] for s in home["configuration_steps"]}
		self.assertTrue(ALLOWED_STEP_STATUSES.issubset(labels))
		self.assertEqual(len(home["configuration_steps"]), 9)
		self.assertNotIn("Locked", labels)
		self.assertNotIn("Ready", labels)

	def test_cfg03_mock_is_needs_attention(self):
		cfg_id = self.seed["by_step"]["CFG-03"]
		home = get_configuration_home(cfg_id)
		step = next(s for s in home["configuration_steps"] if s["id"] == "CFG-03")
		self.assertEqual(step["status_label"], "Needs attention")
		self.assertIn("Fix IT Requirements", home["next_action"]["label"])
