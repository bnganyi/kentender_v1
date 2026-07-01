# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""D7 — role-aware detail actions (`get_dia_demand_detail` actions list).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_detail_d7
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from kentender_core.seeds._common import ensure_currency_kes, ensure_department, ensure_procuring_entity
from kentender_procurement.demand_intake.api.dia_detail import get_dia_demand_detail


class TestDiaDetailD7(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand"):
			self._skipped_no_demand = True
			return
		self._skipped_no_demand = False
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"MOH_D7_{h}", f"Entity D7 {h}")
		self.dept = ensure_department(f"Dept D7 {h}", self.entity)
		self._demand_names: list[str] = []

	def tearDown(self):
		if getattr(self, "_skipped_no_demand", False):
			return
		frappe.set_user("Administrator")
		for name in getattr(self, "_demand_names", []):
			if frappe.db.exists("Demand", name):
				frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
		dept = getattr(self, "dept", None)
		if dept and frappe.db.exists("Procuring Department", dept):
			frappe.delete_doc("Procuring Department", dept, force=True, ignore_permissions=True)
		ent = getattr(self, "entity", None)
		if ent and frappe.db.exists("Procuring Entity", ent):
			frappe.delete_doc("Procuring Entity", ent, force=True, ignore_permissions=True)

	def _mk_demand(self, **kwargs) -> str:
		doc = frappe.get_doc(
			{
				"doctype": "Demand",
				"title": kwargs.pop("title", None) or f"D7 {frappe.generate_hash(length=4)}",
				"procuring_entity": self.entity,
				"requesting_department": self.dept,
				"request_date": today(),
				"required_by_date": today(),
				"items": [
					{
						"item_description": "Line",
						"category": "c",
						"uom": "ea",
						"quantity": 1,
						"estimated_unit_cost": 10,
					}
				],
				**kwargs,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self._demand_names.append(doc.name)
		return doc.name

	def test_actions_requisitioner_draft_submit_cancel(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		email = f"req_d7_{frappe.generate_hash(length=4)}@test.local"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "D7",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Requisitioner")
		try:
			frappe.set_user(user.name)
			name = self._mk_demand(requested_by=user.name, status="Draft")
			out = get_dia_demand_detail(name)
			self.assertTrue(out.get("ok"))
			ids = [a.get("id") for a in (out.get("actions") or [])]
			self.assertIn("open_form", ids)
			self.assertIn("submit_demand", ids)
			self.assertIn("cancel_demand", ids)
			sub = next(a for a in out["actions"] if a["id"] == "submit_demand")
			self.assertIn("lifecycle.submit_demand", sub.get("method", ""))
			self.assertFalse(sub.get("danger"))
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("User", user.name):
				frappe.delete_doc("User", user.name, force=True, ignore_permissions=True)

	def test_actions_hod_pending_includes_return_reject(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		email = f"hod_d7_{frappe.generate_hash(length=4)}@test.local"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "HoD",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Department Approver")
		name = self._mk_demand(requested_by="Administrator", title="Pending for D7")
		frappe.db.set_value("Demand", name, "status", "Pending HoD Approval", update_modified=False)
		try:
			frappe.set_user(user.name)
			out = get_dia_demand_detail(name)
			self.assertTrue(out.get("ok"))
			ids = {a.get("id") for a in (out.get("actions") or [])}
			self.assertIn("approve_hod", ids)
			self.assertIn("return_from_hod", ids)
			self.assertIn("reject_from_hod", ids)
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("User", user.name):
				frappe.delete_doc("User", user.name, force=True, ignore_permissions=True)

	def test_cancel_rejected_allowed_for_owner(self):
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		from kentender_procurement.demand_intake.api.lifecycle import _cancel_allowed_for_current_user

		email = f"req_d7b_{frappe.generate_hash(length=4)}@test.local"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Own",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Requisitioner")
		try:
			frappe.set_user(user.name)
			name = self._mk_demand(requested_by=user.name)
			frappe.db.sql("UPDATE `tabDemand` SET `status`=%s WHERE `name`=%s", ("Rejected", name))
			frappe.db.commit()
			doc = frappe.get_doc("Demand", name)
			self.assertTrue(_cancel_allowed_for_current_user(doc))
		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("User", user.name):
				frappe.delete_doc("User", user.name, force=True, ignore_permissions=True)

	# ── Regression: workbench_actions — open_form visibility ──────────────────

	def test_workbench_actions_draft_includes_open_form_as_edit(self):
		"""Draft demands: _workbench_actions must include open_form with edit=True.

		Regression guard: previously get_dia_demand_detail used _form_header_actions
		(which always strips open_form) so the Edit Demand button never appeared in
		the workbench for Draft demands.
		"""
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		from kentender_procurement.demand_intake.api.dia_detail import _workbench_actions

		name = self._mk_demand(status="Draft")
		doc = frappe.get_doc("Demand", name)
		actions = _workbench_actions(doc, "admin")
		ids = [a.get("id") for a in actions]
		self.assertIn("open_form", ids, "Edit Demand button must appear for Draft in workbench")
		open_form_action = next(a for a in actions if a["id"] == "open_form")
		self.assertTrue(open_form_action.get("edit"), "open_form.edit must be True for Draft demand")
		self.assertEqual(open_form_action.get("label"), "Edit Demand")

	def test_workbench_actions_submitted_excludes_open_form(self):
		"""Submitted demands: _workbench_actions must NOT include open_form.

		Regression guard: 'View demand' button was shown in the workbench for
		non-editable demands (e.g. Pending HoD Approval).  Since the user is already
		looking at the demand in the workbench the button was a no-op and confusing.
		"""
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		from kentender_procurement.demand_intake.api.dia_detail import _workbench_actions

		name = self._mk_demand(status="Draft")
		frappe.db.set_value("Demand", name, "status", "Pending HoD Approval", update_modified=False)
		doc = frappe.get_doc("Demand", name)
		actions = _workbench_actions(doc, "admin")
		ids = [a.get("id") for a in actions]
		self.assertNotIn(
			"open_form",
			ids,
			"View demand button must NOT appear for non-editable demands in workbench",
		)

	def test_get_dia_demand_detail_draft_actions_include_edit_button(self):
		"""End-to-end: get_dia_demand_detail for a Draft demand returns open_form=edit.

		Regression guard for the fix in get_dia_demand_detail that switched from
		_landing_actions (showed 'View demand' for all) to _workbench_actions
		(correct: show 'Edit Demand' for editable, hide 'View demand' for submitted).
		"""
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		name = self._mk_demand(status="Draft")
		out = get_dia_demand_detail(name)
		self.assertTrue(out.get("ok"))
		ids = [a.get("id") for a in (out.get("actions") or [])]
		self.assertIn("open_form", ids, "Edit Demand must be in workbench actions for Draft")
		open_form_action = next(a for a in out["actions"] if a["id"] == "open_form")
		self.assertTrue(open_form_action.get("edit"))

	def test_get_dia_demand_detail_hod_pending_actions_exclude_open_form(self):
		"""End-to-end: get_dia_demand_detail for Pending HoD Approval excludes open_form."""
		if getattr(self, "_skipped_no_demand", False):
			self.skipTest("Demand DocType not installed")
		name = self._mk_demand(status="Draft")
		frappe.db.set_value("Demand", name, "status", "Pending HoD Approval", update_modified=False)
		out = get_dia_demand_detail(name)
		self.assertTrue(out.get("ok"))
		ids = [a.get("id") for a in (out.get("actions") or [])]
		self.assertNotIn("open_form", ids, "View demand must NOT appear for Pending HoD Approval in workbench")
