# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Register approved budget — BUD-FR-003–006 / Pack Phase 2."""

from __future__ import annotations

import re

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_contracts import get_register_form_context, register_budget
from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity

BUD_REF_RE = re.compile(r"^[A-Z0-9]+-BUD-\d{4}$")


def _ensure_user(email: str, roles: list[str], procuring_entity: str | None = None) -> str:
	ensure_budget_roles()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.enabled = 1
	user.save(ignore_permissions=True)
	have = set(frappe.get_roles(email))
	for role in (
		"Budget Viewer",
		"Budget Officer",
		"Budget Reviewer",
		"Budget Authority",
		"Auditor",
	):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles(*roles)
	if procuring_entity:
		# Clear prior PE permissions then set default.
		for row in frappe.get_all(
			"User Permission",
			filters={"user": email, "allow": "Procuring Entity"},
			pluck="name",
		):
			frappe.delete_doc("User Permission", row, force=1, ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": email,
				"allow": "Procuring Entity",
				"for_value": procuring_entity,
				"is_default": 1,
			}
		).insert(ignore_permissions=True)
	return email


def _make_evidence_file() -> str:
	"""Return a File URL suitable for Budget.approval_evidence Attach."""
	# Use PNG bytes — fake PDF content fails Frappe's pdf_contains_js check.
	content = (
		b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
		b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
		b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
	)
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": "MOH_Budget_Approval_test.png",
			"content": content,
			"is_private": 1,
		}
	)
	file_doc.insert(ignore_permissions=True)
	return file_doc.file_url


class TestBudgetRegister(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		ensure_currency_kes()
		cls.seed = upsert_moh_mvp_v1_portfolio()
		cls.pe = cls.seed["procuring_entity"]

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def _valid_payload(self, **over) -> dict:
		# High FY values avoid collisions with MOH seed (2026–28) and Playwright smokes.
		payload = {
			"title": "Ministry of Health Procurement Budget FY 2040/41",
			"fiscal_period": "2040/41",
			"currency": "KES",
			"budget_owner": "Director, Finance and Accounts",
			"authoritative_reference": "MOH-FIN-BUD-2040-01",
			"approval_date": "2040-06-15",
			"external_approved_total": "450,000,000",
			"approval_evidence": _make_evidence_file(),
		}
		payload.update(over)
		return payload

	def _cleanup_budget(self, budget_id: str | None):
		if not budget_id:
			return
		if frappe.db.exists("Budget", budget_id):
			frappe.delete_doc("Budget", budget_id, force=True, ignore_permissions=True)

	def test_officer_registers_draft_with_system_reference(self):
		_ensure_user("bud.officer.reg@example.com", ["Budget Officer"], self.pe)
		frappe.set_user("bud.officer.reg@example.com")
		result = register_budget(self._valid_payload(generated_reference="USER-TYPED-BUD"))
		self.assertTrue(result.get("ok"), result)
		budget = result["budget"]
		self.addCleanup(lambda: self._cleanup_budget(budget["id"]))
		self.assertRegex(budget["code"], BUD_REF_RE)
		self.assertNotEqual(budget["code"], "USER-TYPED-BUD")
		self.assertEqual(budget["status"], "Draft")
		self.assertEqual(budget["registration_source"], "Direct capture")
		self.assertEqual(budget["fiscal_period"], "2040/41")
		self.assertEqual(str(budget["start_date"]), "2040-07-01")
		self.assertEqual(str(budget["end_date"]), "2041-06-30")
		self.assertEqual(flt(budget["external_approved_total"]), 450_000_000)
		self.assertFalse(frappe.db.exists("Budget Line", {"budget": budget["id"]}))

	def test_second_register_increments_reference(self):
		_ensure_user("bud.officer.reg2@example.com", ["Budget Officer"], self.pe)
		frappe.set_user("bud.officer.reg2@example.com")
		a = register_budget(
			self._valid_payload(
				title="Register A",
				fiscal_period="2041/42",
				authoritative_reference="MOH-FIN-BUD-2041-A",
			)
		)
		b = register_budget(
			self._valid_payload(
				title="Register B",
				fiscal_period="2042/43",
				authoritative_reference="MOH-FIN-BUD-2042-B",
			)
		)
		self.assertTrue(a.get("ok") and b.get("ok"), (a, b))
		self.addCleanup(lambda: self._cleanup_budget(a["budget"]["id"]))
		self.addCleanup(lambda: self._cleanup_budget(b["budget"]["id"]))
		self.assertRegex(a["budget"]["code"], BUD_REF_RE)
		self.assertRegex(b["budget"]["code"], BUD_REF_RE)
		self.assertNotEqual(a["budget"]["code"], b["budget"]["code"])

	def test_viewer_cannot_register(self):
		_ensure_user("bud.viewer.reg@example.com", ["Budget Viewer"], self.pe)
		frappe.set_user("bud.viewer.reg@example.com")
		with self.assertRaises(frappe.PermissionError):
			register_budget(self._valid_payload())

	def test_validation_requires_approval_fields(self):
		_ensure_user("bud.officer.val@example.com", ["Budget Officer"], self.pe)
		frappe.set_user("bud.officer.val@example.com")
		result = register_budget(
			self._valid_payload(
				title="",
				authoritative_reference="",
				approval_date="",
				external_approved_total="0",
				approval_evidence="",
			)
		)
		self.assertFalse(result.get("ok"))
		errors = result["errors"]
		self.assertIn("title", errors)
		self.assertIn("authoritative_reference", errors)
		self.assertIn("approval_date", errors)
		self.assertIn("external_approved_total", errors)
		# Evidence is optional at Draft registration.
		self.assertNotIn("approval_evidence", errors)
		self.assertNotIn("generated_reference", errors)
		self.assertNotIn("code", errors)

	def test_register_succeeds_without_approval_evidence(self):
		_ensure_user("bud.officer.noevi@example.com", ["Budget Officer"], self.pe)
		frappe.set_user("bud.officer.noevi@example.com")
		result = register_budget(
			self._valid_payload(
				fiscal_period="2043/44",
				title="Register without evidence FY 2043/44",
				authoritative_reference="MOH-FIN-BUD-NO-EVI-2043",
				approval_evidence="",
			)
		)
		self.assertTrue(result.get("ok"), result)
		self.addCleanup(lambda: self._cleanup_budget(result["budget"]["id"]))
		self.assertEqual((result.get("budget") or {}).get("approval_evidence") or "", "")

	def test_duplicate_active_fiscal_period_rejected(self):
		"""MOH-BUD-2027-2028 is Active for 2027/28 — second Draft/Active blocked."""
		_ensure_user("bud.officer.dup@example.com", ["Budget Officer"], self.pe)
		frappe.set_user("bud.officer.dup@example.com")
		result = register_budget(
			self._valid_payload(
				fiscal_period="2027/28",
				title="Duplicate Active period",
				authoritative_reference="MOH-FIN-BUD-DUP-ACTIVE",
			)
		)
		self.assertFalse(result.get("ok"), result)
		self.assertIn("fiscal_period", result.get("errors") or {})

	def test_duplicate_draft_fiscal_period_rejected(self):
		_ensure_user("bud.officer.dupd@example.com", ["Budget Officer"], self.pe)
		frappe.set_user("bud.officer.dupd@example.com")
		first = register_budget(
			self._valid_payload(
				fiscal_period="2043/44",
				authoritative_reference="MOH-FIN-BUD-2043-D1",
			)
		)
		self.assertTrue(first.get("ok"), first)
		self.addCleanup(lambda: self._cleanup_budget(first["budget"]["id"]))
		second = register_budget(
			self._valid_payload(
				fiscal_period="2043/44",
				title="Second draft same period",
				authoritative_reference="MOH-FIN-BUD-2043-D2",
			)
		)
		self.assertFalse(second.get("ok"), second)
		self.assertIn("fiscal_period", second.get("errors") or {})

	def test_closed_period_allows_new_draft(self):
		"""MOH-BUD-2026-2027 Closed for 2026/27 — new Draft for that period is allowed."""
		_ensure_user("bud.officer.closed@example.com", ["Budget Officer"], self.pe)
		frappe.set_user("bud.officer.closed@example.com")
		result = register_budget(
			self._valid_payload(
				fiscal_period="2026/27",
				title="Re-register after closed",
				authoritative_reference="MOH-FIN-BUD-2026-REREG",
			)
		)
		self.assertTrue(result.get("ok"), result)
		self.addCleanup(lambda: self._cleanup_budget(result["budget"]["id"]))
		self.assertEqual(result["budget"]["status"], "Draft")

	def test_register_context_lists_entity_and_periods(self):
		_ensure_user("bud.officer.ctx@example.com", ["Budget Officer"], self.pe)
		frappe.set_user("bud.officer.ctx@example.com")
		ctx = get_register_form_context()
		self.assertTrue(ctx.get("procuring_entity"))
		self.assertTrue(ctx["procuring_entity"].get("name"))
		self.assertTrue(ctx["procuring_entity"].get("code"))
		self.assertTrue(ctx.get("fiscal_periods"))
		self.assertTrue(ctx.get("capabilities", {}).get("register_budget"))
		self.assertEqual(ctx.get("defaults", {}).get("currency"), "KES")
