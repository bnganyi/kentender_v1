# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""UI-01 get_tender_configuration_home contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.configuration_home import (
	get_configuration_home,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	ALLOWED_STEP_STATUSES,
)


class TestConfigurationHomeApi(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.seed = seed_ui00_dashboard(clear=True)

	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)

	def _needs_attention_id(self) -> str:
		refs = self.seed["configurations"]
		# SEED-TCFG-NA is second config in seed list
		for name in refs:
			if frappe.db.get_value("Tender Configuration", name, "status") == "Needs Attention":
				return name
		return refs[1]

	def test_it_family_returns_exactly_cfg_01_to_09(self):
		cfg_id = self._needs_attention_id()
		home = get_configuration_home(cfg_id)
		steps = home["configuration_steps"]
		self.assertEqual(len(steps), 9)
		ids = [s["id"] for s in steps]
		self.assertEqual(
			ids,
			[
				"CFG-01",
				"CFG-02",
				"CFG-03",
				"CFG-04",
				"CFG-05",
				"CFG-06",
				"CFG-07",
				"CFG-08",
				"CFG-09",
			],
		)
		self.assertEqual(steps[0]["title"], "Tender Profile")
		self.assertIn("Confirm the tender identity", steps[0]["description"])
		self.assertEqual(steps[2]["title"], "IT Requirements")
		self.assertEqual(steps[4]["title"], "System Inventory & Bidder Background")
		self.assertEqual(steps[8]["title"], "Contract Values")

	def test_step_statuses_are_allowed_only(self):
		home = get_configuration_home(self._needs_attention_id())
		for step in home["configuration_steps"]:
			self.assertIn(step["status_label"], ALLOWED_STEP_STATUSES)
			self.assertNotIn(step["status_label"].lower(), ("ready", "locked"))

	def test_context_strip_dto_has_eight_fields(self):
		home = get_configuration_home(self._needs_attention_id())
		ctx = home["context"]
		for key in (
			"procurement_package_ref",
			"procurement_title",
			"procuring_entity_name",
			"procurement_method_label",
			"std_family_label",
			"standard_tender_document_label",
			"configuration_status_label",
			"blocker_count",
			"warning_count",
			"issues_label",
			"status_tone",
		):
			self.assertIn(key, ctx)
		self.assertGreater(ctx["blocker_count"], 0)
		self.assertTrue(ctx["standard_tender_document_label"])
		self.assertEqual(home["standard_tender_document_label"], ctx["standard_tender_document_label"])

	def test_next_action_and_handoff_present(self):
		home = get_configuration_home(self._needs_attention_id())
		na = home["next_action"]
		self.assertTrue(na.get("label"))
		self.assertTrue(na.get("reason"))
		self.assertTrue(na.get("button_label"))
		self.assertIn("Fix IT Requirements", na["label"])
		handoff = home["handoff"]
		for key in (
			"readiness_check",
			"review_status",
			"tender_document_preview",
		):
			self.assertIn(key, handoff)
			self.assertEqual(
				handoff[key]["label"],
				{
					"readiness_check": "Readiness Check",
					"review_status": "Review Status",
					"tender_document_preview": "Tender Document Preview",
				}[key],
			)
		self.assertNotIn("publication_handoff", handoff)

	def test_forbidden_terms_absent_from_payload_labels(self):
		home = get_configuration_home(self._needs_attention_id())
		blob = frappe.as_json(home).lower()
		for term in (
			"tender shell",
			"tenderstdinstance",
			"finalize configuration",
			"publish tender",
			'"locked"',
		):
			self.assertNotIn(term, blob)
