# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-SVC Wave 3 — lifecycle services happy path + key gates."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from kentender_procurement.demands.services.demand_lifecycle import (
	approve_and_reserve_demand,
	confirm_demand_funding,
	consume_demand_in_planning,
	create_or_update_demand,
	enrich_demand,
	get_demand_audit,
	get_demand_performance,
	list_demands_for_workspace,
	record_business_decision,
	submit_demand,
	suggest_funding_allocations,
	suggest_strategy_context,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUDGET,
	ROLE_BUSINESS,
	ROLE_PAA,
	ROLE_PLANNING,
	ROLE_REQUESTER,
	ensure_demand_roles,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"


def _ensure_user(email: str, roles: list[str]) -> str:
	ensure_demand_roles()
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	have = {r.role for r in user.roles}
	for role in roles:
		if role not in have:
			user.append("roles", {"role": role})
	user.save(ignore_permissions=True)
	# Scope assignment
	existing = frappe.db.exists(
		"User Scope Assignment",
		{"user": email, "procuring_entity": PE, "organisation_unit": OU, "role": roles[0]},
	)
	if not existing:
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": email,
				"role": roles[0],
				"procuring_entity": PE,
				"organisation_unit": OU,
				"include_descendants": 1,
				"fixture_namespace": "DEMANDS_WAVE3_TEST",
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()
	return email


def _budget_line() -> str:
	name = frappe.db.get_value(
		"Budget Line", {"generated_reference": "MOH-BL-DHI-2027"}, "name"
	)
	if not name:
		name = frappe.db.get_value(
			"Budget Line", {"fixture_namespace": "KENTENDER_MVP_V1"}, "name"
		)
	if not name:
		raise frappe.ValidationError("No Budget Line fixture for Wave 3 tests")
	return name


class TestDemandLifecycleServices(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()
		if not frappe.db.exists("Procuring Entity", PE):
			raise frappe.ValidationError("PE-MOH required for Wave 3 tests")
		if not frappe.db.exists("Organisation Unit", OU):
			raise frappe.ValidationError("MOH-DIR-DHP required for Wave 3 tests")

	def test_create_submit_business_enrich_confirm_approve_consume(self) -> None:
		req = _ensure_user("dem-svc-req@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-svc-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-svc-paa@example.com", [ROLE_PAA])
		bo = _ensure_user("dem-svc-bo@example.com", [ROLE_BUDGET])
		planner = _ensure_user("dem-svc-plan@example.com", [ROLE_PLANNING])
		line = _budget_line()

		created = create_or_update_demand(
			values={
				"procuring_entity": PE,
				"owner_org_unit": OU,
				"title": "Wave 3 lifecycle test demand",
				"need_statement": "Need connectivity upgrades",
				"expected_outcome": "Reliable clinic links",
				"beneficiaries": "County clinics",
				"delivery_location": "Nairobi",
				"required_by_date": add_days(today(), 90),
				"demand_route": "Standard",
				"urgency": "Medium",
				"requester_estimate": 1000,
				"currency": "KES",
				"fixture_namespace": "DEMANDS_WAVE3_TEST",
			},
			items=[{"description": "Network gear", "quantity": 1, "requester_estimate": 1000}],
			user=req,
		)
		self.assertTrue(created["ok"])
		demand_code = created["demand"]["demand_code"]
		self.assertTrue(demand_code.startswith("DMD-MOH-"))
		name = created["demand"]["name"]

		submitted = submit_demand(demand=name, user=req)
		self.assertEqual(submitted["demand"]["status"], "In Review")
		self.assertEqual(submitted["demand"]["current_stage"], "Business Review")

		supported = record_business_decision(
			demand=name, decision="Support", comment="Aligned", user=ba
		)
		self.assertEqual(supported["demand"]["current_stage"], "Procurement Enrichment")

		enriched = enrich_demand(
			demand=name,
			values={
				"confirmed_estimate": 1000,
				"procurement_category": "Works",
				"estimate_basis": "Market check",
			},
			strategy_references=[
				{
					"reference_type": "Primary",
					"target_code": "T-TEST",
					"target_name": "Test Target",
					"snapshot_label": "Test Target (T-TEST)",
					"hierarchy_path": "Outcome > Target",
					"selection_source": "Manual",
					"confirmation_reason": "Best fit",
				}
			],
			value_treatments=[],
			send_for_budget=True,
			user=paa,
		)
		self.assertEqual(enriched["demand"]["current_stage"], "Budget Confirmation")

		suggestion = suggest_funding_allocations(
			demand=name, budget_line=line, user=paa
		)
		self.assertTrue(suggestion["ok"])
		# Insufficient / match depending on line headroom — force BO confirm with explicit alloc.
		if suggestion.get("exception_type") == "Insufficient Funding":
			self.skipTest("Budget line has insufficient headroom for Wave 3 amount")

		# Clear any open exception created for Multiple Matches before confirm.
		for exc in frappe.get_all(
			"Funding Exception",
			filters={"demand": name, "status": ["in", ["Open", "In Progress"]]},
			pluck="name",
		):
			frappe.db.set_value("Funding Exception", exc, "status", "Resolved")

		confirmed = confirm_demand_funding(
			demand=name,
			allocations=[
				{
					"budget_line": line,
					"allocation_amount": 1000,
					"matching_source": "Budget Officer",
				}
			],
			user=bo,
		)
		self.assertEqual(confirmed["demand"]["current_stage"], "Final Approval")

		approved = approve_and_reserve_demand(demand=name, user=paa)
		self.assertEqual(approved["demand"]["status"], "Approved")
		self.assertEqual(approved["demand"]["current_stage"], "Complete")
		self.assertEqual(approved["demand"]["planning_ready"], 1)
		self.assertTrue(approved["reservations"])

		# Idempotent re-approve path should conflict (no longer Final Approval).
		with self.assertRaises(Exception):
			approve_and_reserve_demand(demand=name, user=paa)

		item = frappe.db.get_value("Demand Item", {"demand": name}, "name")
		consumed = consume_demand_in_planning(
			demand=name,
			demand_item=item,
			consumed_amount=400,
			plan_item_code="PPI-TEST-001",
			user=planner,
		)
		self.assertEqual(consumed["demand"]["planning_usage"], "Partially planned")
		self.assertEqual(consumed["demand"]["status"], "Approved")

		audit = get_demand_audit(demand=name, user=paa)
		self.assertGreaterEqual(len(audit["decisions"]), 4)

		ws = list_demands_for_workspace(user=paa, filters={"limit": 50})
		self.assertTrue(any(r.demand_code == demand_code for r in ws["rows"]))

		perf = get_demand_performance(user=paa, procuring_entity=PE)
		self.assertTrue(perf["ok"])
		self.assertIn("as_at", perf)

	def test_suggest_strategy_context_requires_paa(self) -> None:
		req = _ensure_user("dem-svc-req2@example.com", [ROLE_REQUESTER])
		created = create_or_update_demand(
			values={
				"procuring_entity": PE,
				"owner_org_unit": OU,
				"title": "Strategy suggest gate",
				"need_statement": "n",
				"expected_outcome": "o",
				"beneficiaries": "b",
				"delivery_location": "loc",
				"required_by_date": add_days(today(), 30),
				"demand_route": "Standard",
				"fixture_namespace": "DEMANDS_WAVE3_TEST",
			},
			items=[{"description": "Item A"}],
			user=req,
		)
		with self.assertRaises(frappe.PermissionError):
			suggest_strategy_context(demand=created["demand"]["name"], user=req)
