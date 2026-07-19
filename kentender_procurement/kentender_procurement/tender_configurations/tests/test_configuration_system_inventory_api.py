# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-05 System Inventory & Bidder Background GET/POST contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.system_inventory import (
	MSG_DISCLOSURE_NOTE,
	MSG_EMPTY,
	MSG_OUT_OF_SCOPE,
	MSG_TITLE,
	get_configuration_system_inventory,
	save_configuration_system_inventory,
)


def _complete_item(**overrides):
	base = {
		"item_title": "Existing Server Room",
		"category_label": "Infrastructure Environment",
		"scope_label": "Context only",
		"item_description": (
			"Current server room with limited rack space and cooling constraints "
			"that bidders must account for during installation."
		),
		"bidder_consideration": (
			"Bidder should account for installation constraints and rack space limitations."
		),
		"disclosure_status_label": "Safe to disclose",
		"price_link_label": "May affect price schedule",
	}
	base.update(overrides)
	return base


class TestConfigurationSystemInventoryApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_get_shape(self):
		out = get_configuration_system_inventory(self.cfg_id)
		for key in (
			"configuration_id",
			"items",
			"next_inventory_id",
			"next_background_id",
			"available_requirements",
			"available_milestones",
			"can_continue",
			"has_progress",
			"blockers",
			"column_contract",
			"options",
			"guidance",
			"disclosure_banner",
		):
			self.assertIn(key, out)
		self.assertEqual(out["next_inventory_id"], "INV-001")
		self.assertEqual(out["next_background_id"], "BG-001")
		self.assertIn("Setup Status", out["column_contract"]["columns"])
		self.assertIn("Bidder Consideration", out["column_contract"]["columns"])
		self.assertNotIn("Acceptance", out["column_contract"]["columns"])

	def test_empty_cannot_continue(self):
		out = save_configuration_system_inventory(self.cfg_id, {"items": []})
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_EMPTY for b in out["blockers"]))

	def test_complete_item_can_continue(self):
		out = save_configuration_system_inventory(
			self.cfg_id, {"items": [_complete_item()]}
		)
		self.assertTrue(out["can_continue"])
		row = out["items"][0]
		self.assertEqual(row["item_id"], "INV-001")
		self.assertEqual(row["setup_status_label"], "Complete")
		self.assertEqual(
			row["bidder_consideration_display"],
			"Bidder should account for installation constraints and rack space limitations.",
		)
		blob = frappe.as_json(
			{
				"a": row["bidder_consideration_display"],
				"b": row["disclosure_status_display"],
				"c": row["price_link_display"],
			}
		).lower()
		self.assertNotIn("missing", blob)
		self.assertNotIn("acceptance defined", blob)

	def test_missing_title_blocker(self):
		out = save_configuration_system_inventory(
			self.cfg_id, {"items": [_complete_item(item_title="")]}
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_TITLE for b in out["blockers"]))

	def test_disclosure_note_required_for_review(self):
		out = save_configuration_system_inventory(
			self.cfg_id,
			{
				"items": [
					_complete_item(
						disclosure_status_label="Needs disclosure review",
						disclosure_note="",
					)
				]
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_DISCLOSURE_NOTE for b in out["blockers"]))

	def test_out_of_scope_note_required(self):
		out = save_configuration_system_inventory(
			self.cfg_id,
			{
				"items": [
					_complete_item(
						scope_label="Out of scope",
						category_label="Out of Scope",
						out_of_scope_note="",
					)
				]
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_OUT_OF_SCOPE for b in out["blockers"]))

	def test_background_id_prefix(self):
		out = save_configuration_system_inventory(
			self.cfg_id,
			{
				"items": [
					_complete_item(
						item_title="Current ICT Operating Environment",
						category_label="Background Notes",
						scope_label="Context only",
						price_link_label="No price link expected",
					)
				]
			},
		)
		self.assertTrue(out["can_continue"])
		self.assertEqual(out["items"][0]["item_id"], "BG-001")

	def test_related_refs_from_cfg03_cfg04(self):
		from kentender_procurement.tender_configurations.services.it_requirements import (
			save_configuration_requirements,
		)
		from kentender_procurement.tender_configurations.services.implementation_schedule import (
			APPROACH_PHASED,
			save_configuration_implementation_schedule,
		)
		from kentender_procurement.tender_configurations.tests.test_configuration_it_requirements_api import (
			_complete_requirement,
		)
		from kentender_procurement.tender_configurations.tests.test_configuration_implementation_schedule_api import (
			_complete_milestone,
		)

		save_configuration_requirements(
			self.cfg_id, {"requirements": [_complete_requirement()]}
		)
		save_configuration_implementation_schedule(
			self.cfg_id,
			{
				"delivery_approach": APPROACH_PHASED,
				"milestones": [_complete_milestone()],
			},
		)
		out = save_configuration_system_inventory(
			self.cfg_id,
			{
				"items": [
					_complete_item(
						related_requirement_ids=["REQ-001"],
						related_milestone_ids=["MS-001"],
					)
				]
			},
		)
		row = out["items"][0]
		self.assertEqual(row["related_requirement_ids"], ["REQ-001"])
		self.assertEqual(row["related_milestone_ids"], ["MS-001"])
		self.assertEqual(row["related_requirement_refs"][0]["code"], "REQ-001")
		self.assertEqual(row["related_milestone_refs"][0]["code"], "MS-001")
		avail = get_configuration_system_inventory(self.cfg_id)
		self.assertTrue(any(r["code"] == "REQ-001" for r in avail["available_requirements"]))
		self.assertTrue(any(r["code"] == "MS-001" for r in avail["available_milestones"]))

	def test_auto_ids_increment(self):
		out = save_configuration_system_inventory(
			self.cfg_id,
			{
				"items": [
					_complete_item(item_title="One"),
					_complete_item(item_title="Two"),
				]
			},
		)
		ids = [r["item_id"] for r in out["items"]]
		self.assertEqual(ids, ["INV-001", "INV-002"])
