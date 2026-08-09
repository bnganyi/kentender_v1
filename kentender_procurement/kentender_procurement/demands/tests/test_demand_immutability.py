# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-015 — Approved Demand baseline immutable."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.services.demand_lifecycle import create_or_update_demand
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles
from kentender_procurement.demands.tests._ac_helpers import (
	actor_bundle,
	advance_to_approved,
)


class TestDemandImmutability(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac015_approved_demand_not_directly_editable(self) -> None:
		"""DIA-AC-015 — Approved Demand cannot be edited; baseline snapshot retained."""
		actors = actor_bundle("dem-ac015")
		name = advance_to_approved(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="AC015 immutable approved",
		)
		doc = frappe.get_doc("Demand", name)
		baseline = doc.approved_baseline_snapshot
		self.assertTrue(baseline)
		baseline_title = json.loads(baseline).get("title")
		self.assertEqual(baseline_title, "AC015 immutable approved")
		original_estimate = float(doc.confirmed_estimate)

		with self.assertRaises(Exception):
			create_or_update_demand(
				demand=name,
				values={"title": "Tampered title", "requester_estimate": 1},
				user=actors["req"],
			)

		doc.reload()
		self.assertEqual(doc.title, "AC015 immutable approved")
		self.assertEqual(float(doc.confirmed_estimate), original_estimate)
		self.assertEqual(doc.approved_baseline_snapshot, baseline)
		self.assertEqual(doc.status, "Approved")
