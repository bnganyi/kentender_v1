# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-UI-04 Business review API — load + Support/Return/Reject whitelist."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from kentender_procurement.demands.api import (
	get_demand_review,
	prepare_business_review_ui04,
	record_business_decision_form,
)
from kentender_procurement.demands.services.demand_lifecycle import (
	create_or_update_demand,
	submit_demand,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUSINESS,
	ROLE_REQUESTER,
	ensure_demand_roles,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"


def _ensure_requester(email: str = "dem-review-req@example.com") -> str:
	ensure_demand_roles()
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "DemReview",
				"last_name": "Requester",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	have = {r.role for r in user.roles}
	if ROLE_REQUESTER not in have:
		user.append("roles", {"role": ROLE_REQUESTER})
		user.save(ignore_permissions=True)
	if not frappe.db.exists(
		"User Scope Assignment",
		{"user": email, "procuring_entity": PE, "organisation_unit": OU, "role": ROLE_REQUESTER},
	):
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": email,
				"role": ROLE_REQUESTER,
				"procuring_entity": PE,
				"organisation_unit": OU,
				"include_descendants": 1,
				"fixture_namespace": "DEMANDS_UI04_TEST",
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()
	return email


def _ensure_ba(email: str = "dem-review-ba@example.com") -> str:
	ensure_demand_roles()
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "DemReview",
				"last_name": "Approver",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	have = {r.role for r in user.roles}
	if ROLE_BUSINESS not in have:
		user.append("roles", {"role": ROLE_BUSINESS})
		user.save(ignore_permissions=True)
	if not frappe.db.exists(
		"User Scope Assignment",
		{"user": email, "procuring_entity": PE, "organisation_unit": OU, "role": ROLE_BUSINESS},
	):
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": email,
				"role": ROLE_BUSINESS,
				"procuring_entity": PE,
				"organisation_unit": OU,
				"include_descendants": 1,
				"fixture_namespace": "DEMANDS_UI04_TEST",
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()
	return email


def _submit_in_review(req: str) -> str:
	created = create_or_update_demand(
		values={
			"procuring_entity": PE,
			"owner_org_unit": OU,
			"title": "UI04 review API demand",
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
			"fixture_namespace": "DEMANDS_UI04_TEST",
		},
		items=[
			{
				"description": "Resilient compute capacity",
				"quantity": 1,
				"uom": "Lot",
				"requester_estimate": 300000000,
			},
			{
				"description": "Network and monitoring",
				"quantity": 1,
				"uom": "Lot",
				"requester_estimate": 155000000,
			},
		],
		user=req,
	)
	name = created["demand"]["name"]
	submit_demand(demand=name, user=req)
	return name


class TestDemandsReviewApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()
		if not frappe.db.exists("Procuring Entity", PE):
			raise frappe.ValidationError("PE-MOH required for DEM-UI-04 API tests")
		if not frappe.db.exists("Organisation Unit", OU):
			raise frappe.ValidationError("MOH-DIR-DHP required for DEM-UI-04 API tests")

	def test_get_review_and_support(self) -> None:
		req = _ensure_requester()
		ba = _ensure_ba()
		name = _submit_in_review(req)

		frappe.set_user(ba)
		loaded = get_demand_review(demand=name)
		self.assertTrue(loaded["ok"])
		self.assertEqual(loaded["stage"], "Business Review")
		self.assertTrue(loaded["can_decide"])
		self.assertEqual(
			set(loaded["allowed_actions"]),
			{"Support", "Return", "Reject"},
		)
		self.assertTrue(loaded["show_non_final_disclaimer"])
		demand = loaded["demand"]
		self.assertEqual(demand["status"], "In Review")
		self.assertEqual(demand["current_stage"], "Business Review")
		self.assertIn("requester_estimate_display", demand)
		self.assertGreaterEqual(len(demand.get("items") or []), 2)
		stages = {s["key"]: s["state"] for s in loaded["stage_indicator"]}
		self.assertEqual(stages["Request Preparation"], "Complete")
		self.assertEqual(stages["Business Review"], "Current")
		self.assertEqual(stages["Procurement Enrichment"], "Not started")
		self.assertEqual(len(loaded["review_prompts"]), 4)

		supported = record_business_decision_form(
			demand=name,
			decision="Support",
			comment="Aligned with unit responsibilities",
		)
		self.assertTrue(supported["ok"])
		self.assertEqual(supported["demand"]["current_stage"], "Procurement Enrichment")
		self.assertEqual(supported["demand"]["status"], "In Review")

	def test_return_requires_reason_and_stores_hints(self) -> None:
		req = _ensure_requester("dem-review-req-return@example.com")
		ba = _ensure_ba()
		name = _submit_in_review(req)
		frappe.set_user(ba)
		with self.assertRaises(Exception):
			record_business_decision_form(demand=name, decision="Return", reason="")
		returned = record_business_decision_form(
			demand=name,
			decision="Return",
			reason="Revise participant counts and estimate",
			correction_hints=[
				{"key": "items", "label": "Need items and participant quantities"},
				{"key": "requester_estimate", "label": "Requester estimate"},
			],
		)
		self.assertTrue(returned["ok"])
		self.assertEqual(returned["demand"]["status"], "Returned")
		self.assertEqual(returned["demand"]["current_stage"], "Request Preparation")

	def test_reject_requires_reason(self) -> None:
		req = _ensure_requester("dem-review-req-reject@example.com")
		ba = _ensure_ba()
		name = _submit_in_review(req)
		frappe.set_user(ba)
		with self.assertRaises(Exception):
			record_business_decision_form(demand=name, decision="Reject")
		rejected = record_business_decision_form(
			demand=name,
			decision="Reject",
			reason="Need is outside unit mandate",
		)
		self.assertTrue(rejected["ok"])
		self.assertEqual(rejected["demand"]["status"], "Rejected")

	def test_requester_cannot_decide(self) -> None:
		req = _ensure_requester("dem-review-req-sod@example.com")
		name = _submit_in_review(req)
		frappe.set_user(req)
		loaded = get_demand_review(demand=name)
		self.assertTrue(loaded["ok"])
		self.assertFalse(loaded["can_decide"])
		with self.assertRaises(Exception):
			record_business_decision_form(
				demand=name,
				decision="Support",
				comment="Should fail SoD",
			)

	def test_prepare_business_review_ui04_factory(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_business_review_ui04(requester=_ensure_requester())
		self.assertTrue(payload["ok"])
		self.assertEqual(payload["status"], "In Review")
		self.assertEqual(payload["current_stage"], "Business Review")
		self.assertTrue(payload["business_approver"])
		review = get_demand_review(demand=payload["demand"])
		# Admin may read; can_decide depends on BA role
		self.assertTrue(review["ok"])
		frappe.set_user(payload["business_approver"])
		as_ba = get_demand_review(demand=payload["demand"])
		self.assertTrue(as_ba["can_decide"])
