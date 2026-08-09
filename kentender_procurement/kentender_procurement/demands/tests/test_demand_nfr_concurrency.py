# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-NFR-001 — approve/reserve + cancel/release transactional & idempotent."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.services.demand_lifecycle import (
	approve_and_reserve_demand,
	cancel_and_release_demand,
)
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles
from kentender_procurement.demands.tests._ac_helpers import (
	actor_bundle,
	advance_to_approved,
	advance_to_final_approval,
)


class TestDemandNfrConcurrency(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_nfr001_approve_idempotent_and_fail_closed(self) -> None:
		"""DIA-NFR-001 — same-key approve → one RSV; failed reserve leaves no partial."""
		actors = actor_bundle("dem-nfr001a")
		name = advance_to_final_approval(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="NFR001 approve idempotent",
		)
		code = frappe.db.get_value("Demand", name, "demand_code")
		key = f"nfr001-{code}"
		first = approve_and_reserve_demand(
			demand=name, user=actors["paa"], idempotency_key=key
		)
		self.assertEqual(first["demand"]["status"], "Approved")
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"demand_code": code}),
			1,
		)
		with self.assertRaises(Exception):
			approve_and_reserve_demand(
				demand=name, user=actors["paa"], idempotency_key=key
			)
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"demand_code": code}),
			1,
		)

		# Fail-closed path (AC-014 reuse).
		name2 = advance_to_final_approval(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="NFR001 fail-closed",
		)
		code2 = frappe.db.get_value("Demand", name2, "demand_code")
		before = frappe.db.count("Funding Reservation", {"demand_code": code2})
		with patch(
			"kentender_budget.services.budget_check_reserve_contracts.reserve_funding",
			side_effect=frappe.ValidationError("Forced reserve failure"),
		):
			with self.assertRaises(frappe.ValidationError):
				approve_and_reserve_demand(demand=name2, user=actors["paa"])
		self.assertNotEqual(frappe.db.get_value("Demand", name2, "status"), "Approved")
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"demand_code": code2}),
			before,
		)

	def test_nfr001_cancel_release_idempotent(self) -> None:
		"""DIA-NFR-001 — cancel twice: still Cancelled; RSV Released once; one Cancel decision."""
		actors = actor_bundle("dem-nfr001b")
		name = advance_to_approved(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="NFR001 cancel idempotent",
		)
		rsv = frappe.db.get_value(
			"Demand Funding Allocation",
			{"demand": name},
			"funding_reservation",
		)
		self.assertTrue(rsv)
		first = cancel_and_release_demand(
			demand=name, reason="Programme ended", user=actors["paa"]
		)
		self.assertEqual(first["demand"]["status"], "Cancelled")
		self.assertEqual(
			frappe.db.get_value("Funding Reservation", rsv, "status"),
			"Released",
		)
		cancel_decisions = frappe.db.count(
			"Demand Decision", {"demand": name, "decision": "Cancel"}
		)
		self.assertEqual(cancel_decisions, 1)

		second = cancel_and_release_demand(
			demand=name, reason="Repeat cancel", user=actors["paa"]
		)
		self.assertEqual(second["demand"]["status"], "Cancelled")
		self.assertTrue(second.get("idempotent"))
		self.assertEqual(
			frappe.db.count("Demand Decision", {"demand": name, "decision": "Cancel"}),
			1,
		)
		self.assertEqual(
			frappe.db.get_value("Funding Reservation", rsv, "status"),
			"Released",
		)
