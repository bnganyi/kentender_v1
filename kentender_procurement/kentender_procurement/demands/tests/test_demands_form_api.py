# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-UI-02 form API — create/update/submit via whitelist wrappers."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from kentender_procurement.demands.api import (
	get_demand_form,
	get_demand_form_context,
	save_demand_form,
	submit_demand_form,
)
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_REQUESTER,
	ensure_demand_roles,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"


def _ensure_requester(email: str = "dem-form-req@example.com") -> str:
	ensure_demand_roles()
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "DemForm",
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
	existing = frappe.db.exists(
		"User Scope Assignment",
		{"user": email, "procuring_entity": PE, "organisation_unit": OU, "role": ROLE_REQUESTER},
	)
	if not existing:
		frappe.get_doc(
			{
				"doctype": "User Scope Assignment",
				"user": email,
				"role": ROLE_REQUESTER,
				"procuring_entity": PE,
				"organisation_unit": OU,
				"include_descendants": 1,
				"fixture_namespace": "DEMANDS_UI02_TEST",
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()
	return email


class TestDemandsFormApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_demand_roles()
		if not frappe.db.exists("Procuring Entity", PE):
			raise frappe.ValidationError("PE-MOH required for DEM-UI-02 API tests")
		if not frappe.db.exists("Organisation Unit", OU):
			raise frappe.ValidationError("MOH-DIR-DHP required for DEM-UI-02 API tests")

	def test_form_context_and_create_save_submit(self) -> None:
		req = _ensure_requester()
		frappe.set_user(req)

		ctx = get_demand_form_context()
		self.assertTrue(ctx["ok"])
		self.assertEqual(ctx["procuring_entity"], PE)
		self.assertEqual(ctx["owner_org_unit"], OU)
		self.assertTrue(ctx["can_edit"])

		blank = get_demand_form()
		self.assertEqual(blank["mode"], "create")
		self.assertIsNone(blank["demand"])

		saved = save_demand_form(
			values={
				"title": "UI02 form API demand",
				"need_statement": "What is needed for clinics",
				"need_rationale": "Why continuity requires upgrades",
				"expected_outcome": "Stable services",
				"beneficiaries": "County clinics",
				"delivery_location": "Nairobi",
				"required_by_date": add_days(today(), 60),
				"demand_route": "Standard",
				"estimate_confidence": "Medium",
				"estimate_basis": "Market scan",
				"fixture_namespace": "DEMANDS_UI02_TEST",
			},
			items=[
				{
					"description": "Compute lot",
					"quantity": 1,
					"uom": "Lot",
					"requester_estimate": 100000,
				}
			],
		)
		self.assertTrue(saved["ok"])
		name = saved["demand"]["name"]
		self.assertEqual(saved["demand"]["need_rationale"], "Why continuity requires upgrades")
		self.assertEqual(saved["demand"]["status"], "Draft")

		loaded = get_demand_form(demand=name)
		self.assertEqual(loaded["mode"], "edit")
		self.assertEqual(loaded["demand"]["name"], name)
		self.assertGreaterEqual(len(loaded["demand"]["items"]), 1)

		submitted = submit_demand_form(
			demand=name,
			values={
				"title": "UI02 form API demand",
				"need_statement": "What is needed for clinics",
				"need_rationale": "Why continuity requires upgrades",
				"expected_outcome": "Stable services",
				"beneficiaries": "County clinics",
				"delivery_location": "Nairobi",
				"required_by_date": add_days(today(), 60),
				"demand_route": "Standard",
				"estimate_confidence": "Medium",
				"estimate_basis": "Market scan",
			},
			items=[
				{
					"description": "Compute lot",
					"quantity": 1,
					"uom": "Lot",
					"requester_estimate": 100000,
				}
			],
		)
		self.assertTrue(submitted["ok"])
		self.assertEqual(submitted["demand"]["status"], "In Review")
		self.assertEqual(submitted["demand"]["current_stage"], "Business Review")
