# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-UI-02 form API — create/update/submit via whitelist wrappers."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from kentender_procurement.demands.api import (
	cancel_demand_form,
	get_demand_form,
	get_demand_form_context,
	prepare_returned_demand_ui03,
	remove_demand_attachment_form,
	save_demand_form,
	submit_demand_form,
)
from kentender_procurement.demands.services.demand_lifecycle import record_business_decision
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUSINESS,
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
		self.assertEqual(ctx["selection_mode"], "single_readonly")
		self.assertEqual(ctx["procuring_entity"], PE)
		self.assertEqual(ctx["owner_org_unit"], OU)
		self.assertTrue(ctx["can_edit"])
		self.assertEqual(ctx["selected_pair"]["procuring_entity"], PE)

		blank = get_demand_form()
		self.assertEqual(blank["mode"], "create")
		self.assertIsNone(blank["demand"])
		blank_stages = {s["key"]: s["state"] for s in blank["stage_indicator"]}
		self.assertEqual(blank_stages.get("Request Preparation"), "Current")
		self.assertEqual(blank_stages.get("Business Review"), "Not started")
		ctx_stages = {s["key"]: s["state"] for s in ctx["stage_indicator"]}
		self.assertEqual(ctx_stages.get("Request Preparation"), "Current")

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
		self.assertEqual(loaded["demand"]["status_display"], "Draft")
		self.assertIn("estimate_header_display", loaded["demand"])
		edit_stages = {s["key"]: s["state"] for s in loaded["stage_indicator"]}
		self.assertEqual(edit_stages.get("Request Preparation"), "Current")

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

	def test_create_context_blocked_without_requester_pair(self) -> None:
		email = "dem-form-noscope@example.com"
		ensure_demand_roles()
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "No",
					"last_name": "Scope",
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			).insert(ignore_permissions=True)
		user = frappe.get_doc("User", email)
		user.add_roles("System Manager")
		user.roles = [r for r in user.roles if r.role != ROLE_REQUESTER]
		user.save(ignore_permissions=True)
		for name in frappe.get_all(
			"User Scope Assignment",
			filters={"user": email, "role": ROLE_REQUESTER},
			pluck="name",
		):
			frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)
		frappe.db.commit()
		frappe.set_user(email)
		ctx = get_demand_form_context()
		self.assertEqual(ctx["selection_mode"], "blocked")
		self.assertFalse(ctx["can_edit"])
		self.assertIsNone(ctx["procuring_entity"])
		with self.assertRaises(Exception):
			save_demand_form(
				values={"title": "Should fail", "fixture_namespace": "DEMANDS_UI02_TEST"},
				items=[],
			)

	def test_multi_scope_requires_explicit_pair(self) -> None:
		email = "dem-form-multi@example.com"
		ensure_demand_roles()
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Multi",
					"last_name": "Form",
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			).insert(ignore_permissions=True)
		user = frappe.get_doc("User", email)
		have = {r.role for r in user.roles}
		if ROLE_REQUESTER not in have:
			user.append("roles", {"role": ROLE_REQUESTER})
			user.save(ignore_permissions=True)
		for pe, ou in ((PE, OU), ("PE-CGKIS", "CGK-DEPT-HEALTH")):
			if not frappe.db.exists("Procuring Entity", pe):
				continue
			if not frappe.db.exists("Organisation Unit", ou):
				continue
			exists = frappe.db.exists(
				"User Scope Assignment",
				{
					"user": email,
					"procuring_entity": pe,
					"organisation_unit": ou,
					"role": ROLE_REQUESTER,
				},
			)
			if not exists:
				frappe.get_doc(
					{
						"doctype": "User Scope Assignment",
						"user": email,
						"role": ROLE_REQUESTER,
						"procuring_entity": pe,
						"organisation_unit": ou,
						"include_descendants": 1,
						"fixture_namespace": "DEMANDS_UI02_TEST",
					}
				).insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.set_user(email)
		ctx = get_demand_form_context()
		if len(ctx.get("pairs") or []) < 2:
			self.skipTest("PE-CGKIS / CGK-DEPT-HEALTH required for multi-scope form API test")
		self.assertEqual(ctx["selection_mode"], "multi_required")
		self.assertIsNone(ctx["selected_pair"])
		with self.assertRaises(Exception):
			save_demand_form(
				values={
					"title": "Multi without pair",
					"fixture_namespace": "DEMANDS_UI02_TEST",
				},
				items=[],
			)
		saved = save_demand_form(
			values={
				"title": "Multi with pair",
				"need_statement": "Need",
				"need_rationale": "Why",
				"expected_outcome": "Outcome",
				"beneficiaries": "People",
				"delivery_location": "Nairobi",
				"required_by_date": add_days(today(), 30),
				"demand_route": "Standard",
				"procuring_entity": PE,
				"owner_org_unit": OU,
				"fixture_namespace": "DEMANDS_UI02_TEST",
			},
			items=[{"description": "Lot", "quantity": 1, "uom": "Lot", "requester_estimate": 1}],
		)
		self.assertTrue(saved["ok"])
		self.assertEqual(saved["demand"]["procuring_entity"], PE)

	def test_returned_form_notice_hints_funding_and_cancel(self) -> None:
		"""DEM-UI-03 — return_notice carries Stitch correction hints + available funding."""
		req = _ensure_requester("dem-form-ui03-req@example.com")
		ba_email = "dem-form-ui03-ba@example.com"
		ensure_demand_roles()
		if not frappe.db.exists("User", ba_email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": ba_email,
					"first_name": "Form",
					"last_name": "BA",
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			).insert(ignore_permissions=True)
		ba = frappe.get_doc("User", ba_email)
		have = {r.role for r in ba.roles}
		if ROLE_BUSINESS not in have:
			ba.append("roles", {"role": ROLE_BUSINESS})
			ba.save(ignore_permissions=True)
		if not frappe.db.exists(
			"User Scope Assignment",
			{
				"user": ba_email,
				"procuring_entity": PE,
				"organisation_unit": OU,
				"role": ROLE_BUSINESS,
			},
		):
			frappe.get_doc(
				{
					"doctype": "User Scope Assignment",
					"user": ba_email,
					"role": ROLE_BUSINESS,
					"procuring_entity": PE,
					"organisation_unit": OU,
					"include_descendants": 1,
					"fixture_namespace": "DEMANDS_UI03_TEST",
				}
			).insert(ignore_permissions=True)
		frappe.db.commit()

		frappe.set_user(req)
		saved = save_demand_form(
			values={
				"title": "UI03 returned form demand",
				"need_statement": "Need certification seats",
				"need_rationale": "Skills gap",
				"expected_outcome": "Certified cohort",
				"beneficiaries": "County teams",
				"delivery_location": "Nairobi",
				"required_by_date": add_days(today(), 90),
				"demand_route": "Standard",
				"estimate_confidence": "Medium",
				"estimate_basis": "Unit cost",
				"fixture_namespace": "DEMANDS_UI03_TEST",
			},
			items=[
				{
					"description": "Seats",
					"quantity": 100,
					"uom": "Pieces",
					"requester_estimate": 95000000,
				}
			],
		)
		name = saved["demand"]["name"]
		submit_demand_form(
			demand=name,
			values={
				"title": "UI03 returned form demand",
				"need_statement": "Need certification seats",
				"need_rationale": "Skills gap",
				"expected_outcome": "Certified cohort",
				"beneficiaries": "County teams",
				"delivery_location": "Nairobi",
				"required_by_date": add_days(today(), 90),
				"demand_route": "Standard",
				"estimate_confidence": "Medium",
				"estimate_basis": "Unit cost",
			},
			items=[
				{
					"description": "Seats",
					"quantity": 100,
					"uom": "Pieces",
					"requester_estimate": 95000000,
				}
			],
		)

		frappe.set_user(ba_email)
		record_business_decision(
			demand=name,
			decision="Return",
			reason=(
				"The proposed scope exceeds available funding by KES 15,000,000. "
				"Revise the number of participants or provide a phased delivery approach."
			),
			user=ba_email,
			correction_hints=[
				{"key": "items", "label": "Need items and participant quantities"},
				{"key": "expected_outcome", "label": "Expected outcome for the revised scope"},
				{"key": "requester_estimate", "label": "Requester estimate"},
			],
			available_funding=80000000,
		)

		frappe.set_user(req)
		loaded = get_demand_form(demand=name)
		self.assertEqual(loaded["demand"]["status"], "Returned")
		notice = loaded["demand"]["return_notice"]
		self.assertIsNotNone(notice)
		self.assertIn("Business Approver", notice["returned_by"])
		self.assertIn("15,000,000", notice["reason"])
		keys = {h["key"] for h in notice["correction_hints"]}
		self.assertEqual(keys, {"items", "expected_outcome", "requester_estimate"})
		self.assertEqual(notice["available_funding"], 80000000)
		self.assertEqual(notice["available_funding_display"], "80,000,000.00")
		self.assertEqual(loaded["demand"]["available_funding_display"], "80,000,000.00")

		cancelled = cancel_demand_form(demand=name, reason="No longer required")
		self.assertTrue(cancelled["ok"])
		self.assertEqual(cancelled["demand"]["status"], "Cancelled")

	def test_prepare_returned_demand_ui03_factory(self) -> None:
		frappe.set_user("Administrator")
		payload = prepare_returned_demand_ui03(requester=_ensure_requester())
		self.assertTrue(payload["ok"])
		self.assertEqual(payload["status"], "Returned")
		form = payload["form"]
		self.assertEqual(len(form["return_notice"]["correction_hints"]), 3)
		self.assertEqual(form["available_funding_display"], "80,000,000.00")

	def test_need_item_uom_units_and_set_round_trip(self) -> None:
		"""Need Items UOM must preserve values outside Lot/Pieces/Months (blank select bug)."""
		req = _ensure_requester("dem-form-uom-req@example.com")
		frappe.set_user(req)
		saved = save_demand_form(
			values={
				"title": "UOM round-trip demand",
				"need_statement": "Need items with non-lot units",
				"need_rationale": "Factory-style uoms",
				"expected_outcome": "Units preserved",
				"beneficiaries": "Clinics",
				"delivery_location": "Nairobi",
				"required_by_date": add_days(today(), 60),
				"demand_route": "Standard",
				"estimate_confidence": "Medium",
				"estimate_basis": "Market scan",
				"fixture_namespace": "DEMANDS_UI02_TEST",
			},
			items=[
				{
					"description": "High-performance compute cluster",
					"quantity": 2,
					"uom": "units",
					"requester_estimate": 200000000,
				},
				{
					"description": "Scalable storage arrays (10 PB)",
					"quantity": 1,
					"uom": "set",
					"requester_estimate": 255000000,
				},
			],
		)
		self.assertTrue(saved["ok"])
		uoms = {it["description"]: it["uom"] for it in saved["demand"]["items"]}
		self.assertEqual(uoms["High-performance compute cluster"], "units")
		self.assertEqual(uoms["Scalable storage arrays (10 PB)"], "set")
		loaded = get_demand_form(demand=saved["demand"]["name"])
		loaded_uoms = {it["description"]: it["uom"] for it in loaded["demand"]["items"]}
		self.assertEqual(loaded_uoms["High-performance compute cluster"], "units")
		self.assertEqual(loaded_uoms["Scalable storage arrays (10 PB)"], "set")
		ctx = get_demand_form_context()
		self.assertIn("units", ctx.get("uom_options") or [])
		self.assertIn("set", ctx.get("uom_options") or [])

	def test_supporting_document_attachment_roundtrip(self) -> None:
		"""DEM-UI-02 — File attachments appear on form DTO and can be removed."""
		req = _ensure_requester("dem-form-docs@example.com")
		frappe.set_user(req)
		saved = save_demand_form(
			values={
				"title": "UI02 supporting docs demand",
				"need_statement": "Need statement",
				"need_rationale": "Rationale",
				"expected_outcome": "Outcome",
				"beneficiaries": "Beneficiaries",
				"delivery_location": "Nairobi",
				"required_by_date": add_days(today(), 45),
				"demand_route": "Standard",
				"estimate_confidence": "Medium",
				"estimate_basis": "Quote",
				"fixture_namespace": "DEMANDS_UI02_DOCS",
			},
			items=[
				{
					"description": "Docs lot",
					"quantity": 1,
					"uom": "Lot",
					"requester_estimate": 50000,
				}
			],
		)
		self.assertTrue(saved["ok"])
		name = saved["demand"]["name"]
		self.assertEqual(saved["demand"].get("attachments"), [])

		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "ui02-support.txt",
				"is_private": 1,
				"content": "dem-ui02 supporting document",
				"attached_to_doctype": "Demand",
				"attached_to_name": name,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()

		loaded = get_demand_form(demand=name)
		atts = loaded["demand"].get("attachments") or []
		self.assertEqual(len(atts), 1)
		self.assertEqual(atts[0]["file_name"], "ui02-support.txt")
		self.assertEqual(atts[0]["id"], file_doc.name)

		removed = remove_demand_attachment_form(demand=name, file_id=file_doc.name)
		self.assertTrue(removed["ok"])
		self.assertEqual(removed["demand"].get("attachments"), [])
		self.assertFalse(frappe.db.exists("File", file_doc.name))
