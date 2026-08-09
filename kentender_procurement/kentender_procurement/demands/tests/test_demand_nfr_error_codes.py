# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-NFR-009 — stable error codes for permission, validation, conflict, funding, stale."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.demands.services.demand_lifecycle import (
	ERR_CONFLICT,
	ERR_FUNDING,
	ERR_STALE_VERSION,
	ERR_VALIDATION,
	approve_and_reserve_demand,
	confirm_demand_funding,
	create_or_update_demand,
	submit_demand,
)
from kentender_procurement.demands.services.demand_permissions import (
	ERR_PERMISSION,
	ERR_SCOPE,
	ROLE_PAA,
	ROLE_REQUESTER,
	assert_demand_scope,
	ensure_demand_roles,
	require_operational_roles,
)
from kentender_procurement.demands.tests._ac_helpers import (
	actor_bundle,
	advance_to_final_approval,
	budget_line,
	create_draft,
	ensure_user,
)


class TestDemandNfrErrorCodes(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()

	def test_nfr009_stable_error_codes(self) -> None:
		"""DIA-NFR-009 — exception text/title carry stable DEMAND_* codes."""
		# Permission
		with self.assertRaises(frappe.PermissionError) as ctx_perm:
			require_operational_roles(ROLE_PAA, user="Guest")
		self.assertIn(ERR_PERMISSION, str(ctx_perm.exception))

		# Scope
		req = ensure_user("dem-nfr009-req@example.com", [ROLE_REQUESTER])
		with self.assertRaises(frappe.PermissionError) as ctx_scope:
			assert_demand_scope(
				procuring_entity="PE-DOES-NOT-EXIST",
				owner_org_unit="OU-DOES-NOT-EXIST",
				user=req,
				require_write=True,
			)
		self.assertIn(ERR_SCOPE, str(ctx_scope.exception))

		# Validation
		name = create_draft(req, estimate=1000, title="NFR009 validation")
		frappe.db.set_value("Demand", name, "need_statement", "")
		with self.assertRaises(frappe.ValidationError) as ctx_val:
			submit_demand(demand=name, user=req)
		self.assertIn(ERR_VALIDATION, str(ctx_val.exception))

		# Conflict — edit Approved blocked via create path after approve
		actors = actor_bundle("dem-nfr009")
		approved = advance_to_final_approval(
			req=actors["req"],
			ba=actors["ba"],
			paa=actors["paa"],
			bo=actors["bo"],
			estimate=1000,
			title="NFR009 conflict",
		)
		approve_and_reserve_demand(demand=approved, user=actors["paa"])
		with self.assertRaises(frappe.ValidationError) as ctx_conf:
			create_or_update_demand(
				demand=approved,
				values={"title": "nope"},
				user=actors["req"],
			)
		self.assertIn(ERR_CONFLICT, str(ctx_conf.exception))

		# Funding — alloc mismatch blocks confirm
		name2 = create_draft(actors["req"], estimate=1000, title="NFR009 funding")
		submit_demand(demand=name2, user=actors["req"])
		# Force to Budget Confirmation with mismatch via confirm after staging
		from kentender_procurement.demands.services.demand_lifecycle import (
			enrich_demand,
			record_business_decision,
		)

		record_business_decision(
			demand=name2, decision="Support", comment="ok", user=actors["ba"]
		)
		enrich_demand(
			demand=name2,
			values={"confirmed_estimate": 1000, "procurement_category": "Works"},
			strategy_references=[
				{
					"reference_type": "Primary",
					"target_code": "T-NFR009",
					"target_name": "NFR009",
					"snapshot_label": "NFR009 (T-NFR009)",
					"hierarchy_path": "O > T",
					"selection_source": "Manual",
					"confirmation_reason": "fit",
				}
			],
			value_treatments=[],
			send_for_budget=True,
			user=actors["paa"],
		)
		for exc in frappe.get_all(
			"Funding Exception",
			filters={"demand": name2, "status": ["in", ["Open", "In Progress"]]},
			pluck="name",
		):
			frappe.db.set_value("Funding Exception", exc, "status", "Resolved")
		with self.assertRaises(frappe.ValidationError) as ctx_fund:
			confirm_demand_funding(
				demand=name2,
				allocations=[
					{
						"budget_line": budget_line(),
						"allocation_amount": 900,
						"matching_source": "Budget Officer",
					}
				],
				user=actors["bo"],
			)
		self.assertIn(ERR_FUNDING, str(ctx_fund.exception))

		# Stale version
		draft = create_draft(actors["req"], estimate=500, title="NFR009 stale")
		modified = str(frappe.db.get_value("Demand", draft, "modified"))
		create_or_update_demand(
			demand=draft,
			values={"title": "NFR009 stale v2"},
			user=actors["req"],
		)
		with self.assertRaises(frappe.ValidationError) as ctx_stale:
			create_or_update_demand(
				demand=draft,
				values={"title": "NFR009 stale v3", "expected_modified": modified},
				user=actors["req"],
			)
		self.assertIn(ERR_STALE_VERSION, str(ctx_stale.exception))
