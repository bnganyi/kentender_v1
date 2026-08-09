# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-AC-010 — cross-entity / OU denial (API)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.api import (
	get_demand_detail,
	get_demand_form,
	list_demands_workspace,
)
from kentender_procurement.demands.seeds.kentender_mvp_v1 import (
	upsert_county_draft_demand,
	upsert_principal_approved_demand,
)
from kentender_procurement.demands.services.demand_lifecycle import (
	cancel_and_release_demand,
	create_or_update_demand,
)
from kentender_procurement.demands.services.demand_permissions import (
	ERR_SCOPE,
	ROLE_PAA,
	ROLE_REQUESTER,
	ensure_demand_roles,
)
from kentender_procurement.demands.tests._ac_helpers import ensure_user


class TestDemandScope(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_ac010_cross_entity_denial_api(self) -> None:
		"""DIA-AC-010 — MOH denied county Draft; Kisumu denied MOH Approved mutate."""
		county = upsert_county_draft_demand(commit=False)
		principal = upsert_principal_approved_demand(commit=False)
		county_name = county["demand"]
		moh_name = principal["demand"]

		moh_req = ensure_user(
			"dem-ac010-moh@example.com",
			[ROLE_REQUESTER],
			pe=C.PE_MOH,
			ou=C.OU_DIR_DHP,
		)
		moh_paa = ensure_user(
			"dem-ac010-paa@example.com",
			[ROLE_PAA],
			pe=C.PE_MOH,
			ou=C.OU_DIR_DHP,
		)
		kisumu = ensure_user(
			"dem-ac010-kisumu@example.com",
			[ROLE_REQUESTER],
			pe=C.PE_CGKIS,
			ou=C.OU_CGK_HEALTH,
		)

		frappe.set_user(moh_req)
		ws = list_demands_workspace(page=1, page_size=200)
		codes = {r.get("demand_code") for r in (ws.get("rows") or [])}
		self.assertNotIn(C.DEMAND_CODE_COUNTY, codes)
		with self.assertRaises(frappe.PermissionError) as ctx:
			get_demand_form(demand=county_name)
		self.assertIn(ERR_SCOPE, str(ctx.exception))
		with self.assertRaises(frappe.PermissionError):
			create_or_update_demand(
				demand=county_name,
				values={"title": "Cross-entity tamper"},
				user=moh_req,
			)

		frappe.set_user(kisumu)
		ws_k = list_demands_workspace(page=1, page_size=200)
		codes_k = {r.get("demand_code") for r in (ws_k.get("rows") or [])}
		self.assertNotIn(C.DEMAND_CODE, codes_k)
		with self.assertRaises(frappe.PermissionError) as ctx2:
			get_demand_detail(demand=moh_name)
		self.assertIn(ERR_SCOPE, str(ctx2.exception))
		with self.assertRaises(frappe.PermissionError):
			cancel_and_release_demand(
				demand=moh_name, reason="Out of scope cancel", user=kisumu
			)

		# Positive control: MOH PAA can read principal Approved.
		frappe.set_user(moh_paa)
		ok = get_demand_detail(demand=moh_name)
		self.assertTrue(ok.get("ok") is not False)
		self.assertEqual((ok.get("demand") or {}).get("demand_code"), C.DEMAND_CODE)
