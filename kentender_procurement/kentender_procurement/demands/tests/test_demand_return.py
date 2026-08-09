# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-018 — Return identifies correction owner; prior decisions preserved."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.api import get_demand_form
from kentender_procurement.demands.seeds.kentender_mvp_v1 import (
	upsert_returned_shortfall_demand,
)
from kentender_procurement.demands.services.demand_lifecycle import (
	record_business_decision,
	submit_demand,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUSINESS,
	ROLE_REQUESTER,
	ensure_demand_roles,
)
from kentender_procurement.demands.tests._ac_helpers import create_draft, ensure_user


class TestDemandReturn(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac018_return_sets_owner_and_keeps_decision_history(self) -> None:
		"""DIA-AC-018 — correction owner + prior decisions; SEED-002 evidence."""
		seed = upsert_returned_shortfall_demand(commit=False)
		demand = frappe.get_doc("Demand", seed["demand"])
		self.assertEqual(demand.demand_code, C.DEMAND_CODE_RETURNED)
		self.assertEqual(demand.status, "Returned")
		self.assertEqual(demand.current_stage, "Request Preparation")
		self.assertEqual(demand.current_owner, C.USER_PUBLIC)
		self.assertEqual(demand.requester, C.USER_PUBLIC)

		decisions = frappe.get_all(
			"Demand Decision",
			filters={"demand": demand.name},
			fields=["decision", "stage", "reason", "decision_input_snapshot"],
			order_by="decided_at asc",
		)
		self.assertTrue(decisions)
		# Prior funding/return rationale is retained on the seed decisions.
		joined = " ".join(
			f"{d.decision} {(d.reason or '')} {(d.decision_input_snapshot or '')}"
			for d in decisions
		)
		self.assertTrue(joined.strip())

		frappe.set_user(C.USER_PUBLIC)
		form = get_demand_form(demand=demand.name)
		self.assertEqual(form.get("mode"), "edit")
		self.assertEqual((form.get("demand") or {}).get("status"), "Returned")
		self.assertEqual((form.get("demand") or {}).get("current_owner"), C.USER_PUBLIC)

		# Live return path also assigns requester as correction owner.
		req = ensure_user("dem-ac018-req@example.com", [ROLE_REQUESTER])
		ba = ensure_user("dem-ac018-ba@example.com", [ROLE_BUSINESS])
		name = create_draft(req, estimate=1000, title="AC018 live return")
		submit_demand(demand=name, user=req)
		prior_count = frappe.db.count("Demand Decision", {"demand": name})
		returned = record_business_decision(
			demand=name,
			decision="Return",
			reason="Clarify beneficiaries and delivery location",
			comment="Needs correction",
			correction_hints=[{"key": "beneficiaries", "label": "Beneficiaries"}],
			user=ba,
		)
		self.assertEqual(returned["demand"]["status"], "Returned")
		self.assertEqual(returned["demand"]["current_stage"], "Request Preparation")
		self.assertEqual(returned["demand"]["current_owner"], req)
		self.assertGreater(
			frappe.db.count("Demand Decision", {"demand": name}),
			prior_count,
		)
		snap_row = frappe.get_all(
			"Demand Decision",
			filters={"demand": name, "decision": "Return"},
			fields=["decision_input_snapshot", "reason"],
			order_by="decided_at desc",
			limit=1,
		)[0]
		self.assertIn("Clarify beneficiaries", snap_row.reason or "")
		snap = json.loads(snap_row.decision_input_snapshot or "{}")
		self.assertTrue(snap.get("correction_hints") or snap.get("demand"))
