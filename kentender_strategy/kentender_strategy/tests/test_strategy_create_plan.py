# Copyright (c) 2026, KenTender and contributors
"""Create strategic plan workflow — REQ §9.1 / §10 / §12 / STR-AC-001."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_contracts import create_plan, get_create_plan_context
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles


def _ensure_user(email: str, roles: list[str], procuring_entity: str | None = None) -> str:
	ensure_strategy_roles()
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
	# Reset strategy roles so negative tests are not polluted by prior runs.
	have = set(frappe.get_roles(email))
	for role in (
		"Strategy Viewer",
		"Strategy Officer",
		"Strategy Manager",
		"Strategy Reviewer",
		"Planning Authority",
	):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles(*roles)
	if procuring_entity:
		frappe.defaults.set_user_default("Procuring Entity", procuring_entity, user=email)
	return email


class TestStrategyCreatePlan(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def _valid_payload(self, **over) -> dict:
		code = over.pop("plan_code", f"CRT-{frappe.generate_hash(length=6).upper()}")
		payload = {
			"plan_code": code,
			"title": "Create Plan Fixture",
			"plan_type": "Entity Strategic Plan",
			"procuring_entity": self.pe,
			"start_date": "2026-07-01",
			"end_date": "2030-06-30",
			"description": "Optional description",
		}
		payload.update(over)
		return payload

	def _cleanup_plan(self, plan_id: str | None):
		if not plan_id:
			return
		if frappe.db.exists("Strategic Plan", plan_id):
			frappe.delete_doc("Strategic Plan", plan_id, force=True, ignore_permissions=True)

	def test_officer_can_create_draft_with_audit_and_no_hierarchy(self):
		_ensure_user("str.officer.create@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.create@example.com")
		payload = self._valid_payload()
		result = create_plan(payload)
		self.assertTrue(result.get("ok"))
		plan = result["plan"]
		self.addCleanup(lambda: self._cleanup_plan(plan["id"]))
		self.assertEqual(plan["code"], payload["plan_code"])
		self.assertEqual(plan["status"], "Draft")
		self.assertEqual(plan["version_number"], 1)
		self.assertFalse(plan.get("supersedes_plan_version"))
		doc = frappe.get_doc("Strategic Plan", plan["id"])
		self.assertEqual(doc.owner, "str.officer.create@example.com")
		self.assertTrue(doc.creation)
		self.assertFalse(frappe.db.exists("Strategy Programme", {"plan_version": plan["id"]}))
		self.assertFalse(frappe.db.exists("Strategic Outcome", {"plan_version": plan["id"]}))
		self.assertFalse(frappe.db.exists("Performance Indicator", {"plan_version": plan["id"]}))
		self.assertFalse(frappe.db.exists("Performance Target", {"plan_version": plan["id"]}))
		self.assertFalse(frappe.db.exists("Strategy Sub Programme", {"plan_version": plan["id"]}))
		audit = frappe.get_all(
			"Strategy Audit Event",
			filters={"plan_version": plan["id"], "event_type": "Created"},
			fields=["name", "new_state", "actor"],
		)
		self.assertEqual(len(audit), 1)
		self.assertEqual(audit[0].new_state, "Draft")
		self.assertEqual(audit[0].actor, "str.officer.create@example.com")

	def test_viewer_cannot_create(self):
		_ensure_user("str.viewer.create@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.viewer.create@example.com")
		with self.assertRaises(frappe.PermissionError):
			create_plan(self._valid_payload())

	def test_entity_scope_blocks_other_pe_without_cross_authority(self):
		other_pe = "PE-OTHER-CREATE-TEST"
		if not frappe.db.exists("Procuring Entity", other_pe):
			frappe.get_doc(
				{
					"doctype": "Procuring Entity",
					"entity_code": "OTHER-CREATE",
					"entity_name": "Other PE Create Test",
				}
			).insert(ignore_permissions=True)
			# Prefer stable name when autoname is hash — look up by code.
			other_pe = frappe.db.get_value("Procuring Entity", {"entity_code": "OTHER-CREATE"}, "name")
		else:
			other_pe = frappe.db.get_value("Procuring Entity", {"entity_code": "OTHER-CREATE"}, "name") or other_pe
		_ensure_user("str.officer.scope@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.scope@example.com")
		result = create_plan(self._valid_payload(procuring_entity=other_pe))
		self.assertFalse(result.get("ok"))
		self.assertIn("procuring_entity", result.get("errors") or {})

	def test_plan_code_format_and_required(self):
		_ensure_user("str.manager.create@example.com", ["Strategy Manager"], self.pe)
		frappe.set_user("str.manager.create@example.com")
		missing = create_plan(self._valid_payload(plan_code=""))
		self.assertFalse(missing.get("ok"))
		self.assertIn("plan_code", missing["errors"])
		bad = create_plan(self._valid_payload(plan_code="moh sp 2026"))
		self.assertFalse(bad.get("ok"))
		self.assertIn("plan_code", bad["errors"])

	def test_plan_code_unique_within_entity(self):
		_ensure_user("str.manager.uniq@example.com", ["Strategy Manager"], self.pe)
		frappe.set_user("str.manager.uniq@example.com")
		dup = create_plan(self._valid_payload(plan_code=STRATEGY_PLAN_CODE))
		self.assertFalse(dup.get("ok"))
		self.assertIn("plan_code", dup["errors"])

	def test_date_validation_end_must_be_later(self):
		_ensure_user("str.manager.dates@example.com", ["Strategy Manager"], self.pe)
		frappe.set_user("str.manager.dates@example.com")
		equal = create_plan(self._valid_payload(start_date="2026-07-01", end_date="2026-07-01"))
		self.assertFalse(equal.get("ok"))
		self.assertIn("end_date", equal["errors"])
		before = create_plan(self._valid_payload(start_date="2026-07-01", end_date="2025-06-30"))
		self.assertFalse(before.get("ok"))
		self.assertIn("end_date", before["errors"])

	def test_rejects_successor_fields_and_keeps_partial_errors(self):
		_ensure_user("str.manager.succ@example.com", ["Strategy Manager"], self.pe)
		frappe.set_user("str.manager.succ@example.com")
		result = create_plan(
			self._valid_payload(
				plan_code="",
				title="",
				supersedes_plan_version=self.seed["plan"],
				version_number=2,
			)
		)
		self.assertFalse(result.get("ok"))
		errors = result["errors"]
		self.assertIn("plan_code", errors)
		self.assertIn("title", errors)
		self.assertIn("supersedes_plan_version", errors)

	def test_create_context_exposes_entity_and_types(self):
		_ensure_user("str.officer.ctx@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.ctx@example.com")
		ctx = get_create_plan_context()
		self.assertTrue(ctx["capabilities"]["create_plan"])
		self.assertFalse(ctx["capabilities"]["change_entity"])
		self.assertEqual(ctx["procuring_entity"]["id"], self.pe)
		self.assertIn("Entity Strategic Plan", ctx["plan_types"])
		self.assertIn("Sector Strategy", ctx["plan_types"])
		self.assertIn("Other", ctx["plan_types"])
