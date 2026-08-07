# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-UI-05 Procurement enrichment API — load, save, strategy, send, return."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from kentender_procurement.demands.api import (
	enrich_demand_form,
	get_demand_review,
	prepare_enrichment_ui05,
	record_business_decision_form,
	record_procurement_decision_form,
	suggest_strategy_context_form,
)
from kentender_procurement.demands.services.demand_lifecycle import (
	create_or_update_demand,
	submit_demand,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUSINESS,
	ROLE_PAA,
	ROLE_REQUESTER,
	ensure_demand_roles,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"


def _ensure_user(email: str, roles: list[str], ns: str = "DEMANDS_UI05_TEST") -> str:
	ensure_demand_roles()
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "DemEnrich",
				"last_name": email.split("@")[0][:20],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	have = {r.role for r in user.roles}
	changed = False
	for role in roles:
		if role not in have:
			user.append("roles", {"role": role})
			changed = True
	if changed:
		user.save(ignore_permissions=True)
	for role in roles:
		if not frappe.db.exists(
			"User Scope Assignment",
			{
				"user": email,
				"procuring_entity": PE,
				"organisation_unit": OU,
				"role": role,
			},
		):
			frappe.get_doc(
				{
					"doctype": "User Scope Assignment",
					"user": email,
					"role": role,
					"procuring_entity": PE,
					"organisation_unit": OU,
					"include_descendants": 1,
					"fixture_namespace": ns,
				}
			).insert(ignore_permissions=True)
	frappe.db.commit()
	return email


def _to_enrichment(req: str, ba: str) -> str:
	created = create_or_update_demand(
		values={
			"procuring_entity": PE,
			"owner_org_unit": OU,
			"title": "UI05 enrichment API demand",
			"need_statement": "Need resilient clinic connectivity",
			"need_rationale": "Service continuity requires upgrades",
			"expected_outcome": "Stable clinic links",
			"beneficiaries": "County clinics",
			"delivery_location": "Nairobi",
			"required_by_date": add_days(today(), 90),
			"demand_route": "Standard",
			"urgency": "Medium",
			"estimate_confidence": "Medium",
			"estimate_basis": "Market scan",
			"currency": "KES",
			"fixture_namespace": "DEMANDS_UI05_TEST",
		},
		items=[
			{
				"description": "Resilient compute capacity",
				"quantity": 1,
				"uom": "Lot",
				"requester_estimate": 300000,
			}
		],
		user=req,
	)
	name = created["demand"]["name"]
	submit_demand(demand=name, user=req)
	frappe.set_user(ba)
	record_business_decision_form(demand=name, decision="Support", comment="Supported")
	return name


class TestDemandsEnrichmentApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()
		if not frappe.db.exists("Procuring Entity", PE):
			raise frappe.ValidationError("PE-MOH required for DEM-UI-05 API tests")
		if not frappe.db.exists("Organisation Unit", OU):
			raise frappe.ValidationError("MOH-DIR-DHP required for DEM-UI-05 API tests")

	def test_get_enrichment_projection_and_save(self) -> None:
		req = _ensure_user("dem-enrich-req@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-enrich-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-enrich-paa@example.com", [ROLE_PAA])
		name = _to_enrichment(req, ba)

		frappe.set_user(paa)
		loaded = get_demand_review(demand=name)
		self.assertTrue(loaded["ok"])
		self.assertEqual(loaded["stage"], "Procurement Enrichment")
		self.assertTrue(loaded["can_enrich"])
		self.assertFalse(loaded["can_decide"])
		self.assertIn("Save enrichment", loaded["allowed_actions"])
		self.assertIn("Send for budget confirmation", loaded["allowed_actions"])
		enrichment = loaded["enrichment"]
		self.assertIsNotNone(enrichment)
		self.assertEqual(enrichment["strategy_alignment"], "Not assigned")
		self.assertFalse(enrichment["send_ready"])
		demand = loaded["demand"]
		self.assertNotIn("procurement_method", demand)
		self.assertNotIn("tender_method", demand)
		self.assertIn("duplicate_assessment", demand)
		stages = {s["key"]: s["state"] for s in loaded["stage_indicator"]}
		self.assertEqual(stages["Business Review"], "Complete")
		self.assertEqual(stages["Procurement Enrichment"], "Current")

		item = (demand.get("items") or [])[0]
		saved = enrich_demand_form(
			demand=name,
			values={
				"confirmed_estimate": 320000,
				"procurement_category": "ICT infrastructure and services",
				"estimate_basis": "Updated market check",
				"duplicate_assessment": "None found",
				"related_demands_note": "2 related infrastructure needs",
				"aggregation_treatment": "Proceed independently",
				"aggregation_rationale": "Distinct delivery window",
			},
			items=[
				{
					"name": item["name"],
					"description": item["description"],
					"quantity": item.get("quantity"),
					"uom": item.get("uom"),
					"requester_estimate": item.get("requester_estimate"),
					"confirmed_quantity": 1,
					"confirmed_uom": "Lot",
					"confirmed_estimate": 320000,
				}
			],
			strategy_references=None,
			value_treatments=[],
			send_for_budget=0,
		)
		self.assertTrue(saved["ok"])
		self.assertEqual(flt_safe(saved["demand"]["confirmed_estimate"]), 320000)
		self.assertEqual(
			saved["demand"]["procurement_category"], "ICT infrastructure and services"
		)
		self.assertEqual(saved["demand"]["duplicate_assessment"], "None found")
		self.assertEqual(saved["demand"]["aggregation_treatment"], "Proceed independently")
		self.assertEqual(saved["stage"], "Procurement Enrichment")
		self.assertFalse(saved["enrichment"]["send_ready"])

	def test_assign_primary_and_send_for_budget(self) -> None:
		req = _ensure_user("dem-enrich-req2@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-enrich-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-enrich-paa@example.com", [ROLE_PAA])
		name = _to_enrichment(req, ba)
		frappe.set_user(paa)

		# Prefer a real Strategic Plan so plan_display resolves to title+code (not hash).
		plan = frappe.db.get_value(
			"Strategic Plan",
			{"status": "Active"},
			["name", "title", "plan_code"],
			as_dict=True,
		)
		ref = {
			"reference_type": "Primary",
			"target_code": "T-UI05",
			"target_name": "UI05 Primary Target",
			"snapshot_label": "UI05 Primary Target (T-UI05)",
			"hierarchy_path": "Outcome > Target",
			"selection_source": "Manual",
			"confirmation_reason": "Best fit",
		}
		if plan:
			ref["plan"] = plan.name
			ref["plan_version_id"] = plan.name

		sent = enrich_demand_form(
			demand=name,
			values={
				"confirmed_estimate": 1000,
				"procurement_category": "Works",
				"estimate_basis": "Market check",
			},
			items=None,
			strategy_references=[ref],
			value_treatments=[],
			send_for_budget=1,
		)
		self.assertTrue(sent["ok"])
		self.assertEqual(sent["stage"], "Budget Confirmation")
		self.assertEqual(sent["demand"]["current_stage"], "Budget Confirmation")

	def test_strategy_ref_dto_exposes_plan_display_not_hash(self) -> None:
		req = _ensure_user("dem-enrich-req-plan@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-enrich-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-enrich-paa@example.com", [ROLE_PAA])
		name = _to_enrichment(req, ba)
		plan = frappe.db.get_value(
			"Strategic Plan",
			{"status": "Active"},
			["name", "title", "plan_code"],
			as_dict=True,
		)
		self.assertTrue(plan, "Need an Active Strategic Plan fixture for display DTO coverage")
		frappe.set_user(paa)
		enrich_demand_form(
			demand=name,
			values={
				"confirmed_estimate": 1000,
				"procurement_category": "ICT infrastructure and services",
			},
			strategy_references=[
				{
					"reference_type": "Primary",
					"plan": plan.name,
					"plan_version_id": plan.name,
					"target_code": "T-DISP",
					"target_name": "Display Target",
					"snapshot_label": "Display Target (T-DISP)",
					"hierarchy_path": "Programme > Target",
					"confirmation_reason": "Display check",
				}
			],
			value_treatments=[],
			send_for_budget=0,
		)
		payload = get_demand_review(demand=name)
		primary = payload["enrichment"]["primary_strategy"]
		self.assertIsNotNone(primary)
		self.assertEqual(primary["plan_name"], plan.title)
		self.assertEqual(primary["plan_code"], plan.plan_code)
		self.assertIn(plan.title, primary["plan_display"])
		self.assertIn(plan.plan_code, primary["plan_display"])
		self.assertNotEqual(primary["plan_display"], plan.name)
		self.assertNotIn(plan.name, primary["plan_display"])

	def test_send_blocked_without_primary(self) -> None:
		req = _ensure_user("dem-enrich-req3@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-enrich-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-enrich-paa@example.com", [ROLE_PAA])
		name = _to_enrichment(req, ba)
		frappe.set_user(paa)
		with self.assertRaises(Exception):
			enrich_demand_form(
				demand=name,
				values={
					"confirmed_estimate": 1000,
					"procurement_category": "Works",
				},
				strategy_references=[],
				value_treatments=[],
				send_for_budget=1,
			)

	def test_return_requires_reason_and_records_enrichment_stage(self) -> None:
		req = _ensure_user("dem-enrich-req4@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-enrich-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-enrich-paa@example.com", [ROLE_PAA])
		name = _to_enrichment(req, ba)
		frappe.set_user(paa)
		with self.assertRaises(Exception):
			record_procurement_decision_form(demand=name, decision="Return", reason="")
		returned = record_procurement_decision_form(
			demand=name,
			decision="Return",
			reason="Revise confirmed quantities before enrichment",
		)
		self.assertTrue(returned["ok"])
		self.assertEqual(returned["demand"]["status"], "Returned")
		decision = frappe.get_all(
			"Demand Decision",
			filters={"demand": name, "decision": "Return"},
			fields=["stage", "reason"],
			order_by="decided_at desc",
			limit=1,
		)[0]
		self.assertEqual(decision.stage, "Procurement Enrichment")
		self.assertIn("Revise confirmed", decision.reason or "")

	def test_suggest_strategy_context_form(self) -> None:
		req = _ensure_user("dem-enrich-req5@example.com", [ROLE_REQUESTER])
		ba = _ensure_user("dem-enrich-ba@example.com", [ROLE_BUSINESS])
		paa = _ensure_user("dem-enrich-paa@example.com", [ROLE_PAA])
		name = _to_enrichment(req, ba)
		frappe.set_user(paa)
		payload = suggest_strategy_context_form(demand=name)
		self.assertTrue(payload["ok"])
		self.assertIsInstance(payload.get("suggestions"), list)
		self.assertIn("filters", payload)
		self.assertIn("plans", payload["filters"])
		self.assertIn("effective_periods", payload["filters"])
		for s in payload["suggestions"][:3]:
			self.assertIn("display_name", s)
			self.assertIn("display_code", s)
			self.assertIn("target_id", s)
			self.assertIn("is_suggested", s)
			self.assertIn("why_suggested", s)
			self.assertIn("hierarchy_path", s)
		# Suggested rows (if any) sort ahead of non-suggested.
		flags = [bool(s.get("is_suggested")) for s in payload["suggestions"]]
		if any(flags) and not all(flags):
			first_false = flags.index(False)
			self.assertTrue(all(flags[:first_false]))

	def test_prepare_enrichment_ui05_factory(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_enrichment_ui05(
			requester=_ensure_user("dem-enrich-factory-req@example.com", [ROLE_REQUESTER])
		)
		self.assertTrue(payload["ok"])
		self.assertEqual(payload["current_stage"], "Procurement Enrichment")
		self.assertEqual(payload["enrichment"]["strategy_alignment"], "Not assigned")
		self.assertTrue(payload["procurement_approver"])

	def test_review_dto_falls_back_when_confirmed_item_fields_are_zero(self) -> None:
		"""Unset confirmed_* floats are 0.0 — DTO must surface requester qty/estimate."""
		frappe.set_user("Administrator")
		payload = prepare_enrichment_ui05(
			requester=_ensure_user("dem-enrich-zero-fallback@example.com", [ROLE_REQUESTER])
		)
		items = (payload.get("review") or {}).get("items") or []
		self.assertGreaterEqual(len(items), 2)
		first = items[0]
		self.assertEqual(flt_safe(first.get("quantity")), 2)
		self.assertEqual(flt_safe(first.get("requester_estimate")), 200000000)
		# DB confirmed_* stay 0 until PAA saves; projection must still paint usable values.
		self.assertGreater(flt_safe(first.get("confirmed_quantity")), 0)
		self.assertEqual(flt_safe(first.get("confirmed_quantity")), 2)
		self.assertGreater(flt_safe(first.get("confirmed_estimate")), 0)
		self.assertEqual(flt_safe(first.get("confirmed_estimate")), 200000000)
		self.assertEqual(flt_safe(first.get("unit_estimate")), 100000000)
		self.assertTrue(first.get("unit_estimate_display"))
		self.assertTrue(first.get("total_estimate_display"))


def flt_safe(v) -> float:
	from frappe.utils import flt

	return flt(v)
