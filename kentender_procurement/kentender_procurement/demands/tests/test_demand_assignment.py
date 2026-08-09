# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-002 — Business Approver visibility by entity/OU."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.api import get_demand_review
from kentender_procurement.demands.services.demand_lifecycle import (
	record_business_decision,
	submit_demand,
)
from kentender_procurement.demands.services.demand_permissions import (
	ERR_SCOPE,
	ROLE_BUSINESS,
	ROLE_REQUESTER,
	ensure_demand_roles,
)
from kentender_procurement.demands.tests._ac_helpers import create_draft, ensure_user


class TestDemandAssignment(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac002_ba_matching_scope_can_review_wrong_ou_denied(self) -> None:
		"""DIA-AC-002 — matching BA sees Business Review; wrong OU denied."""
		req = ensure_user(
			"dem-ac002-req@example.com",
			[ROLE_REQUESTER],
			pe=C.PE_MOH,
			ou=C.OU_DIR_DHP,
		)
		ba_ok = ensure_user(
			"dem-ac002-ba-ok@example.com",
			[ROLE_BUSINESS],
			pe=C.PE_MOH,
			ou=C.OU_DIR_DHP,
		)
		ba_wrong = ensure_user(
			"dem-ac002-ba-wrong@example.com",
			[ROLE_BUSINESS],
			pe=C.PE_MOH,
			ou=C.OU_DIR_HRMD,
		)

		name = create_draft(
			req,
			estimate=1000,
			title="AC002 BA scope demand",
			pe=C.PE_MOH,
			ou=C.OU_DIR_DHP,
		)
		submit_demand(demand=name, user=req)
		self.assertEqual(
			frappe.db.get_value("Demand", name, "current_stage"),
			"Business Review",
		)

		frappe.set_user(ba_ok)
		review = get_demand_review(demand=name)
		self.assertTrue(review.get("ok") is not False)
		self.assertEqual(review.get("stage"), "Business Review")
		self.assertTrue(review.get("can_decide"))
		supported = record_business_decision(
			demand=name, decision="Support", comment="In scope", user=ba_ok
		)
		self.assertEqual(supported["demand"]["current_stage"], "Procurement Enrichment")

		# Reset a second demand for wrong-OU denial (first already advanced).
		name2 = create_draft(
			req,
			estimate=1000,
			title="AC002 BA wrong OU demand",
			pe=C.PE_MOH,
			ou=C.OU_DIR_DHP,
		)
		submit_demand(demand=name2, user=req)
		frappe.set_user(ba_wrong)
		with self.assertRaises(frappe.PermissionError) as ctx:
			get_demand_review(demand=name2)
		self.assertIn(ERR_SCOPE, str(ctx.exception))
		with self.assertRaises(frappe.PermissionError) as ctx2:
			record_business_decision(
				demand=name2, decision="Support", comment="Out of scope", user=ba_wrong
			)
		self.assertIn(ERR_SCOPE, str(ctx2.exception))
