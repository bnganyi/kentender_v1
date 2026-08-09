# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-022 — workspace counts match scoped records."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.api import _summary_for_actor, list_demands_workspace
from kentender_procurement.demands.seeds.kentender_mvp_v1 import (
	upsert_county_draft_demand,
	upsert_principal_approved_demand,
	upsert_returned_shortfall_demand,
)
from kentender_procurement.demands.services.demand_permissions import ensure_demand_roles


class TestDemandWorkspace(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac022_workspace_counts_match_scoped_rows(self) -> None:
		"""DIA-AC-022 — summary counts equal filtered scoped rows for the actor."""
		upsert_principal_approved_demand(commit=False)
		upsert_returned_shortfall_demand(commit=False)
		upsert_county_draft_demand(commit=False)

		# Canonical seed users (avoid User insert rate-limit in rapid AC suites).
		moh = C.USER_MEDICAL  # PE-MOH / MOH-DIR-DHP
		kisumu = C.USER_KISUMU_OFFICER
		self.assertTrue(frappe.db.exists("User", moh), moh)
		self.assertTrue(frappe.db.exists("User", kisumu), kisumu)

		frappe.set_user(moh)
		payload = list_demands_workspace(page=1, page_size=500)
		self.assertTrue(payload.get("ok"))
		rows = list(payload.get("rows") or [])
		codes = {r.get("demand_code") for r in rows}
		self.assertIn(C.DEMAND_CODE, codes)
		self.assertNotIn(C.DEMAND_CODE_COUNTY, codes)
		summary = payload["summary"]
		recomputed = _summary_for_actor(moh, rows)
		self.assertEqual(summary, recomputed)

		drafts = list_demands_workspace(queue="my_drafts", page=1, page_size=500)
		self.assertEqual(int(drafts.get("total") or 0), summary["my_drafts"])
		for row in drafts.get("rows") or []:
			self.assertEqual(row.get("status"), "Draft")
			self.assertEqual(row.get("requester"), moh)

		frappe.set_user(kisumu)
		k_payload = list_demands_workspace(page=1, page_size=500)
		k_rows = list(k_payload.get("rows") or [])
		k_codes = {r.get("demand_code") for r in k_rows}
		self.assertIn(C.DEMAND_CODE_COUNTY, k_codes)
		self.assertNotIn(C.DEMAND_CODE, k_codes)
		self.assertEqual(k_payload["summary"], _summary_for_actor(kisumu, k_rows))
