# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-06 Price Schedule GET/POST contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.price_schedule import (
	MSG_CONDITIONAL,
	MSG_EMPTY,
	MSG_NAME,
	MSG_QUANTITY,
	get_configuration_price_schedule,
	save_configuration_price_schedule,
)


def _complete_item(**overrides):
	base = {
		"item_name": "Server compute nodes",
		"price_group": "Supply & Installation",
		"bidder_facing_description": (
			"Provide unit prices for server compute nodes including delivery to site."
		),
		"source_type": "User added",
		"pricing_basis": "Unit price",
		"quantity": "12",
		"unit": "units",
		"evaluated_price_treatment": "Included",
		"bidder_pricing_instruction": (
			"Enter a firm unit price for each server compute node as specified."
		),
	}
	base.update(overrides)
	return base


class TestConfigurationPriceScheduleApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_get_shape(self):
		out = get_configuration_price_schedule(self.cfg_id)
		for key in (
			"configuration_id",
			"price_items",
			"next_item_id",
			"summary",
			"available_requirements",
			"available_milestones",
			"available_inventory",
			"can_continue",
			"has_progress",
			"blockers",
			"column_contract",
			"options",
			"import_candidate_count",
		):
			self.assertIn(key, out)
		self.assertEqual(out["next_item_id"], "PRI-001")
		self.assertIn("Setup Status", out["column_contract"]["columns"])
		self.assertIn("Evaluated Price", out["column_contract"]["columns"])
		self.assertNotIn("Acceptance", out["column_contract"]["columns"])

	def test_empty_cannot_continue(self):
		out = save_configuration_price_schedule(self.cfg_id, {"items": []})
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_EMPTY for b in out["blockers"]))

	def test_complete_item_can_continue(self):
		out = save_configuration_price_schedule(
			self.cfg_id, {"items": [_complete_item()]}
		)
		self.assertTrue(out["can_continue"])
		row = out["price_items"][0]
		self.assertEqual(row["item_id"], "PRI-001")
		self.assertEqual(row["setup_status_label"], "Complete")
		self.assertEqual(row["quantity_display"], "12 units")
		self.assertEqual(row["evaluated_price_display"], "Included")
		blob = frappe.as_json(
			{
				"a": row["quantity_display"],
				"b": row["source_label"],
				"c": row["evaluated_price_display"],
			}
		).lower()
		self.assertNotIn("missing", blob)
		self.assertNotIn("acceptance defined", blob)

	def test_missing_name_blocker(self):
		out = save_configuration_price_schedule(
			self.cfg_id, {"items": [_complete_item(item_name="")]}
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_NAME for b in out["blockers"]))

	def test_conditional_rule_required(self):
		out = save_configuration_price_schedule(
			self.cfg_id,
			{
				"items": [
					_complete_item(
						evaluated_price_treatment="Conditional",
						conditional_rule="",
					)
				]
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_CONDITIONAL for b in out["blockers"]))

	def test_quantity_required_for_unit_price(self):
		out = save_configuration_price_schedule(
			self.cfg_id,
			{"items": [_complete_item(quantity="", unit="")]},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_QUANTITY for b in out["blockers"]))

	def test_recurrent_quantity_unit_required(self):
		out = save_configuration_price_schedule(
			self.cfg_id,
			{
				"items": [
					_complete_item(
						price_group="Recurrent Cost",
						pricing_basis="Annual",
						quantity="",
						unit="",
					)
				]
			},
		)
		self.assertFalse(out["can_continue"])
		self.assertTrue(any(b["message"] == MSG_QUANTITY for b in out["blockers"]))

	def test_recurrent_quantity_with_unit_can_continue(self):
		out = save_configuration_price_schedule(
			self.cfg_id,
			{
				"items": [
					_complete_item(
						price_group="Recurrent Cost",
						pricing_basis="Annual",
						quantity="3",
						unit="years",
					)
				]
			},
		)
		self.assertTrue(out["can_continue"])
		self.assertEqual(out["price_items"][0]["quantity_display"], "3 years")

	def test_lump_sum_skips_quantity(self):
		out = save_configuration_price_schedule(
			self.cfg_id,
			{
				"items": [
					_complete_item(
						pricing_basis="Lump sum",
						quantity="",
						unit="",
					)
				]
			},
		)
		self.assertTrue(out["can_continue"])

	def test_import_from_upstream(self):
		from kentender_procurement.tender_configurations.services.it_requirements import (
			save_configuration_requirements,
		)
		from kentender_procurement.tender_configurations.services.implementation_schedule import (
			APPROACH_PHASED,
			save_configuration_implementation_schedule,
		)
		from kentender_procurement.tender_configurations.services.system_inventory import (
			save_configuration_system_inventory,
		)
		from kentender_procurement.tender_configurations.tests.test_configuration_it_requirements_api import (
			_complete_requirement,
		)
		from kentender_procurement.tender_configurations.tests.test_configuration_implementation_schedule_api import (
			_complete_milestone,
		)
		from kentender_procurement.tender_configurations.tests.test_configuration_system_inventory_api import (
			_complete_item as _complete_inv,
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
		save_configuration_system_inventory(
			self.cfg_id, {"items": [_complete_inv()]}
		)
		before = get_configuration_price_schedule(self.cfg_id)
		self.assertGreaterEqual(before["import_candidate_count"], 3)
		out = save_configuration_price_schedule(self.cfg_id, {"items": [], "import": 1})
		self.assertGreaterEqual(len(out["price_items"]), 3)
		sources = {r["source_type"] for r in out["price_items"]}
		self.assertIn("Requirement", sources)
		self.assertIn("Inventory", sources)
		self.assertIn("Schedule", sources)
		# Drafts are not complete without evaluated treatment / instruction
		self.assertFalse(out["can_continue"])

	def test_auto_ids_increment(self):
		out = save_configuration_price_schedule(
			self.cfg_id,
			{
				"items": [
					_complete_item(item_name="One"),
					_complete_item(item_name="Two"),
				]
			},
		)
		ids = [r["item_id"] for r in out["price_items"]]
		self.assertEqual(ids, ["PRI-001", "PRI-002"])
		self.assertEqual(out["summary"]["total_items"], 2)
		self.assertEqual(out["summary"]["supply_installation_count"], 2)
