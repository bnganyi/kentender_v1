# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-12 Audit History — get_budget_audit + immutability + live record."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_budget.seeds.budget_activity_test_fixture import (
	TEST_COM_CODE,
	TEST_EXP_CODE,
	TEST_RSV_CODE,
	upsert_budget_activity_test_fixture,
)
from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_audit_contracts import (
	EVENT_ACTIVATED,
	EVENT_RESERVED,
	get_budget_audit,
	record_event,
)
from kentender_budget.services.budget_check_reserve_contracts import reserve_funding
from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_budget.services.budget_authorization import create_budget_task
from kentender_budget.seeds.budget_authorization_seed import upsert_budget_test_authorization
from kentender_budget.services.budget_readiness_contracts import (
	activate_budget,
	mark_budget_reviewed,
)


class TestBudgetAudit(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		upsert_budget_test_authorization()
		cls.seed = upsert_budget_activity_test_fixture()

	def setUp(self):
		upsert_budget_activity_test_fixture()
		frappe.db.delete("Budget Audit Event", {"record_code": "RSV-MOH-0001"})

	def _task_payload(self, budget: str) -> dict:
		name = frappe.db.get_value("Budget", {"generated_reference": budget}, "name")
		task_name = frappe.db.get_value(
			"Workflow Task",
			{
				"subject_type": "Budget",
				"subject_id": name,
				"state": "Open",
				"assigned_user_id": frappe.session.user,
			},
			"name",
		)
		if not task_name:
			task = create_budget_task(frappe.get_doc("Budget", name), capability="budget.review", task_type="budget.review", iteration=0)
		else:
			task = frappe.get_doc("Workflow Task", task_name)
		return {"budget": budget, "task_id": task.name, "concurrency_token": task.concurrency_token}

	def test_seeded_moh_0001_ledger_pack_codes_and_full_money(self):
		dto = get_budget_audit("MOH-BUD-2027-2028")
		self.assertEqual(dto["budget"]["code"], "MOH-BUD-2027-2028")
		self.assertTrue(dto["capabilities"]["read_only"])
		self.assertGreaterEqual(dto["row_count"], 7)
		codes = {r["record_code"] for r in dto["rows"]}
		self.assertIn("MOH-BUD-2027-2028", codes)
		self.assertIn(TEST_RSV_CODE, codes)
		self.assertIn(TEST_COM_CODE, codes)
		self.assertIn(TEST_EXP_CODE, codes)
		self.assertNotIn("RSV-MOH-0001", codes)
		self.assertIn("BR-MOH-0000", codes)
		joined = " ".join(r["change_summary_display"] for r in dto["rows"])
		self.assertIn("KES 455,000,000", joined)
		self.assertIn("KES 145,000,000", joined)
		self.assertIn("KES 310,000,000", joined)
		self.assertNotIn("455M", joined)
		self.assertNotIn("RSV-2023-01", joined)
		self.assertEqual(dto["rows"][0]["action_label"], "View")

	def test_filter_by_event_type(self):
		dto = get_budget_audit("MOH-BUD-2027-2028", event_type="Funding reserved")
		self.assertGreaterEqual(dto["row_count"], 1)
		for r in dto["rows"]:
			self.assertEqual(r["event_type"], "Funding reserved")
		self.assertIn(TEST_RSV_CODE, {r["record_code"] for r in dto["rows"]})

	def test_immutability_blocks_delete(self):
		name = frappe.db.get_value(
			"Budget Audit Event",
			{"record_code": TEST_RSV_CODE, "event_type": "Funding reserved"},
			"name",
		)
		self.assertTrue(name)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Budget Audit Event", name, ignore_permissions=True)

	def test_activate_appends_live_event(self):
		# Use Submitted 0002: mark + activate, then assert audit row.
		name = frappe.db.get_value("Budget", {"generated_reference": "MOH-BUD-0002"}, "name")
		frappe.db.set_value(
			"Budget",
			name,
			{
				"submitted_by": "budget.rev.seed@example.com",
				"reviewed_by": None,
				"reviewed_at": None,
			},
		)
		before = frappe.db.count("Budget Audit Event", {"budget": name})
		self.assertTrue(mark_budget_reviewed(self._task_payload("MOH-BUD-0002")).get("ok"))
		self.assertTrue(activate_budget(self._task_payload("MOH-BUD-0002")).get("ok"))
		after = frappe.db.count("Budget Audit Event", {"budget": name})
		self.assertGreater(after, before)
		types = frappe.get_all(
			"Budget Audit Event",
			filters={"budget": name, "event_type": EVENT_ACTIVATED},
			pluck="event_type",
		)
		self.assertTrue(types)

	def test_pe_scope_denial(self):
		email = "budget.audit.pe.deny@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Audit",
					"last_name": "Deny",
					"send_welcome_email": 0,
					"new_password": "Test@12345",
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Budget Viewer")
		frappe.set_user(email)
		try:
			with self.assertRaises(frappe.PermissionError):
				get_budget_audit("MOH-BUD-2027-2028")
		finally:
			frappe.set_user("Administrator")

	def test_record_event_helper(self):
		name = frappe.db.get_value("Budget", {"generated_reference": "MOH-BUD-2026-2027"}, "name")
		ev = record_event(
			budget=name,
			event_type="Baseline registered",
			record_code="MOH-BUD-2026-2027",
			actor="test",
			actor_kind="system",
			change_summary="Test event",
		)
		self.assertTrue(ev)
		self.assertTrue(frappe.db.exists("Budget Audit Event", ev))

	def test_reserve_path_creates_event_reserved(self):
		"""BUD-SUP-005 — live reserve_funding emits Funding reserved audit evidence."""
		line = frappe.db.get_value("Budget Line", {"generated_reference": "MOH-BL-HWD-2027"}, "name")
		key = "TEST:AUDIT-RSV:MOH-BL-HWD-2027:11000000.00"
		result = reserve_funding(
			budget_line=line,
			demand_name="DMD-TEST-AUDIT-RSV",
			requested_amount=11_000_000,
			idempotency_key=key,
		)
		self.assertTrue(result["ok"])
		name = frappe.db.get_value(
			"Budget Audit Event",
			{
				"record_code": result["reservation_code"],
				"event_type": EVENT_RESERVED,
			},
			"name",
		)
		self.assertTrue(name)
		dto = get_budget_audit("MOH-BUD-2027-2028", event_type=EVENT_RESERVED)
		self.assertTrue(any(r["record_code"] == result["reservation_code"] for r in dto["rows"]))
