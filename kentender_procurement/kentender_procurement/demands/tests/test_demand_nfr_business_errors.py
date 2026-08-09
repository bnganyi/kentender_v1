# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-NFR-008 — validation messages include issue, owner, corrective action."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.services.demand_lifecycle import (
	create_or_update_demand,
	submit_demand,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_REQUESTER,
	ensure_demand_roles,
)
from kentender_procurement.demands.tests._ac_helpers import create_draft, ensure_user


class TestDemandNfrBusinessErrors(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_nfr008_business_error_shape(self) -> None:
		"""DIA-NFR-008 — issue / owner / action present on key validation paths."""
		req = ensure_user("dem-nfr008-req@example.com", [ROLE_REQUESTER])
		name = create_draft(req, estimate=1000, title="NFR008 business errors")
		frappe.db.set_value("Demand", name, {"need_statement": "", "beneficiaries": ""})

		with self.assertRaises(frappe.ValidationError) as ctx:
			submit_demand(demand=name, user=req)
		msg = str(ctx.exception)
		self.assertIn("Owner:", msg)
		self.assertIn("Action:", msg)
		self.assertIn("Requester", msg)
		flags = getattr(frappe.flags, "demand_error", None) or {}
		self.assertTrue(flags.get("issue") or "incomplete" in msg.lower())
		self.assertEqual(flags.get("owner"), "Requester")
		self.assertTrue(flags.get("action"))

		# Stale version also carries business fields.
		modified = str(frappe.db.get_value("Demand", name, "modified"))
		create_or_update_demand(
			demand=name,
			values={"title": "NFR008 touched", "need_statement": "restored need"},
			user=req,
		)
		with self.assertRaises(frappe.ValidationError) as ctx2:
			create_or_update_demand(
				demand=name,
				values={"title": "stale", "expected_modified": modified},
				user=req,
			)
		msg2 = str(ctx2.exception)
		self.assertIn("Owner:", msg2)
		self.assertIn("Action:", msg2)
		self.assertIn("Reload", msg2)
