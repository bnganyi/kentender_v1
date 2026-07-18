# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-01 profile GET/POST contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.profile import (
	LOT_MULTIPLE,
	LOT_SINGLE,
	MSG_LOT,
	MSG_SCOPE,
	MSG_TITLE,
	get_configuration_profile,
	save_configuration_profile,
)


class TestConfigurationProfileApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_get_profile_shape(self):
		out = get_configuration_profile(self.cfg_id)
		for key in (
			"configuration_id",
			"tender_title",
			"short_scope_summary",
			"lot_structure",
			"lots",
			"standard_tender_document_label",
			"std_version_label",
			"can_continue",
			"context",
			"helpers",
		):
			self.assertIn(key, out)
		self.assertIn("procurement_package_ref", out["context"])

	def test_save_requires_scope_and_lot(self):
		out = save_configuration_profile(
			self.cfg_id,
			{
				"tender_title": "ERP Implementation Services",
				"short_scope_summary": "",
				"lot_structure": "",
				"lots": [],
				"configuration_note": "",
			},
		)
		self.assertFalse(out["can_continue"])
		msgs = {b["message"] for b in out["blockers"]}
		self.assertIn(MSG_SCOPE, msgs)
		self.assertIn(MSG_LOT, msgs)

	def test_save_complete_single_lot_can_continue(self):
		out = save_configuration_profile(
			self.cfg_id,
			{
				"tender_title": "ERP Implementation Services",
				"short_scope_summary": (
					"Procurement of ERP software licences, implementation, training, "
					"and support for national treasury systems."
				),
				"lot_structure": LOT_SINGLE,
				"lots": [],
				"configuration_note": "Internal note only",
			},
		)
		self.assertTrue(out["can_continue"])
		self.assertEqual(out["blocker_count"], 0)
		self.assertEqual(out["lot_structure"], LOT_SINGLE)
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.lot_structure, LOT_SINGLE)
		from kentender_procurement.tender_configurations.services.configuration_home import (
			_parse_steps_state,
		)

		state = _parse_steps_state(doc.steps_state)
		self.assertEqual((state.get("CFG-01") or {}).get("status_label"), "Complete")

	def test_multiple_lots_requires_rows(self):
		out = save_configuration_profile(
			self.cfg_id,
			{
				"tender_title": "ERP Implementation Services",
				"short_scope_summary": (
					"Procurement of ERP software licences, implementation, training, "
					"and support for national treasury systems."
				),
				"lot_structure": LOT_MULTIPLE,
				"lots": [],
				"configuration_note": "",
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_LOT for b in out["blockers"]))

		out2 = save_configuration_profile(
			self.cfg_id,
			{
				"tender_title": "ERP Implementation Services",
				"short_scope_summary": (
					"Procurement of ERP software licences, implementation, training, "
					"and support for national treasury systems."
				),
				"lot_structure": LOT_MULTIPLE,
				"lots": [
					{
						"lot_no": "Lot 1",
						"lot_title": "Licences",
						"short_description": "Software licences",
					}
				],
				"configuration_note": "",
			},
		)
		self.assertTrue(out2["can_continue"])
		self.assertEqual(len(out2["lots"]), 1)

	def test_forbidden_payload_keys_ignored(self):
		out = save_configuration_profile(
			self.cfg_id,
			{
				"tender_title": "ERP Implementation Services",
				"short_scope_summary": (
					"Procurement of ERP software licences, implementation, training, "
					"and support for national treasury systems."
				),
				"lot_structure": LOT_SINGLE,
				"lots": [],
				"std_version_hash": "should-not-persist",
				"binding_id": "x",
			},
		)
		self.assertTrue(out["can_continue"])
		blob = frappe.as_json(out).lower()
		self.assertNotIn("should-not-persist", blob)

	def test_missing_title_blocker(self):
		out = save_configuration_profile(
			self.cfg_id,
			{
				"tender_title": "",
				"short_scope_summary": (
					"Procurement of ERP software licences, implementation, training, "
					"and support for national treasury systems."
				),
				"lot_structure": LOT_SINGLE,
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_TITLE for b in out["blockers"]))
