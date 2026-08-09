# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-NFR-006 — datetimes projected in user timezone with explicit label."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.services.demand_lifecycle import get_demand_audit
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles
from kentender_procurement.demands.tests._ac_helpers import (
	actor_bundle,
	advance_to_approved,
)


class TestDemandNfrTimezone(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_nfr006_audit_uses_user_timezone(self) -> None:
		"""DIA-NFR-006 — audit decided_at_display includes Africa/Nairobi."""
		actors = actor_bundle("dem-nfr006")
		# Pin user timezone away from UTC.
		frappe.db.set_value(
			"User",
			actors["paa"],
			"time_zone",
			"Africa/Nairobi",
		)
		name = advance_to_approved(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="NFR006 timezone audit",
		)
		audit = get_demand_audit(demand=name, user=actors["paa"])
		self.assertTrue(audit.get("ok"))
		self.assertEqual(audit.get("timezone"), "Africa/Nairobi")
		self.assertTrue(audit.get("approved_at_display"))
		self.assertIn("Africa/Nairobi", audit["approved_at_display"] or "")
		self.assertTrue(audit.get("decisions"))
		approve_rows = [d for d in audit["decisions"] if d.get("decision") == "Approve"]
		self.assertTrue(approve_rows)
		self.assertIn("Africa/Nairobi", approve_rows[0].get("decided_at_display") or "")
		self.assertEqual(approve_rows[0].get("timezone"), "Africa/Nairobi")
