# Copyright (c) 2026, KenTender and contributors
"""STR-FR-003a — system-generated Strategy references."""

from __future__ import annotations

import re

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_reference import (
	allocate_reference,
	correct_reference,
	pe_slug,
)
from kentender_strategy.services.strategy_writes import (
	create_successor_version,
	upsert_structure_node,
)

TYPE_RE = {
	"SP": re.compile(r"^[A-Z0-9]+-SP-\d{4}$"),
	"OUT": re.compile(r"^[A-Z0-9]+-OUT-\d{4}$"),
	"TGT": re.compile(r"^[A-Z0-9]+-TGT-\d{4}$"),
}


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


class TestStrategyReference(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]
		cls.plan = cls.seed["plan"]

	def test_pe_slug_strips_pe_prefix(self):
		self.assertEqual(pe_slug(self.pe), "MOH")

	def test_allocate_increments_and_never_reuses_shape(self):
		a = allocate_reference(self.pe, "SP")
		b = allocate_reference(self.pe, "SP")
		self.assertRegex(a, TYPE_RE["SP"])
		self.assertRegex(b, TYPE_RE["SP"])
		self.assertNotEqual(a, b)

	def test_structure_node_gets_system_reference_ignoring_client_code(self):
		# Need a Draft plan to edit structure
		draft = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"title": "Ref Structure Draft",
				"procuring_entity": self.pe,
				"plan_type": "Entity Strategic Plan",
				"scope_type": "Procuring Entity",
				"scope_id": self.pe,
				"start_date": "2027-07-01",
				"end_date": "2031-06-30",
				"status": "Draft",
				"version_number": 1,
			}
		)
		draft.insert(ignore_permissions=True)
		self.addCleanup(
			lambda: frappe.delete_doc("Strategic Plan", draft.name, force=True, ignore_permissions=True)
		)
		self.assertRegex(draft.plan_code, TYPE_RE["SP"])

		prog = upsert_structure_node(
			{
				"type": "Programme",
				"plan_version": draft.name,
				"code": "CLIENT-PROG",
				"title": "Ref Programme",
				"responsible_function": "ICT",
			}
		)
		self.assertRegex(prog["code"], re.compile(r"^[A-Z0-9]+-PROG-\d{4}$"))
		self.assertNotEqual(prog["code"], "CLIENT-PROG")

		# Immutability on edit
		doc = frappe.get_doc("Strategy Programme", prog["id"])
		doc.programme_code = "HACKED-CODE"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_seed_uses_new_reference_format(self):
		self.assertEqual(STRATEGY_PLAN_CODE, "MOH-SP-2026-2030")
		self.assertEqual(TARGET_CODE, "MOH-TGT-AVAIL-2028")
		self.assertTrue(frappe.db.exists("Strategic Plan", {"plan_code": STRATEGY_PLAN_CODE, "status": "Active"}))
		self.assertTrue(frappe.db.exists("Performance Target", {"target_code": TARGET_CODE}))

	def test_successor_keeps_plan_reference(self):
		frappe.set_user("Administrator")
		# Seed may already have an open Draft successor for MOH-SP-2026-2030 — reuse or create.
		open_successor = frappe.db.get_value(
			"Strategic Plan",
			{"plan_code": STRATEGY_PLAN_CODE, "status": ["in", ("Draft", "Returned")], "name": ["!=", self.plan]},
			"name",
		)
		if open_successor:
			self.assertEqual(
				frappe.db.get_value("Strategic Plan", open_successor, "plan_code"),
				STRATEGY_PLAN_CODE,
			)
			return
		out = create_successor_version(self.plan)
		new_id = out["plan"]["id"]
		self.addCleanup(
			lambda: frappe.delete_doc("Strategic Plan", new_id, force=True, ignore_permissions=True)
			if frappe.db.exists("Strategic Plan", new_id)
			else None
		)
		self.assertEqual(out["plan"]["code"], STRATEGY_PLAN_CODE)

	def test_admin_can_correct_reference_pre_activation(self):
		draft = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"title": "Correction Draft",
				"procuring_entity": self.pe,
				"plan_type": "Entity Strategic Plan",
				"scope_type": "Procuring Entity",
				"scope_id": self.pe,
				"start_date": "2028-07-01",
				"end_date": "2032-06-30",
				"status": "Draft",
				"version_number": 1,
			}
		)
		draft.insert(ignore_permissions=True)
		self.addCleanup(
			lambda: frappe.delete_doc("Strategic Plan", draft.name, force=True, ignore_permissions=True)
		)
		prior = draft.plan_code
		# Pick a free SP code
		new_code = allocate_reference(self.pe, "SP")
		# allocate_reference reserved it in naming sense only if inserted — we didn't insert.
		# Use a high synthetic free code:
		new_code = f"{pe_slug(self.pe)}-SP-8888"
		if frappe.db.exists("Strategic Plan", {"plan_code": new_code}):
			new_code = f"{pe_slug(self.pe)}-SP-8889"
		result = correct_reference(
			"Strategic Plan",
			draft.name,
			new_code,
			"Seed typo correction before activation",
		)
		self.assertEqual(result["code"], new_code)
		self.assertEqual(result["prior"], prior)
		self.assertTrue(
			frappe.db.exists(
				"Strategy Audit Event",
				{"entity_name": draft.name, "event_type": "Reference Corrected"},
			)
		)

	def test_active_plan_reference_immutable_even_for_admin(self):
		with self.assertRaises(frappe.ValidationError):
			correct_reference(
				"Strategic Plan",
				self.plan,
				f"{pe_slug(self.pe)}-SP-7777",
				"Should be rejected after activation",
			)

	def test_planning_authority_can_correct_reference(self):
		"""STR-CHG-001 §5/§8 / SCL-501 — explicit capability, not a hardcoded
		System Manager/Administrator identity stand-in."""
		_ensure_user("str.planning.correct@example.com", ["Planning Authority"], self.pe)
		draft = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"title": "Planning Authority Correction Draft",
				"procuring_entity": self.pe,
				"plan_type": "Entity Strategic Plan",
				"scope_type": "Procuring Entity",
				"scope_id": self.pe,
				"start_date": "2028-07-01",
				"end_date": "2032-06-30",
				"status": "Draft",
				"version_number": 1,
			}
		)
		draft.insert(ignore_permissions=True)
		self.addCleanup(
			lambda: frappe.delete_doc("Strategic Plan", draft.name, force=True, ignore_permissions=True)
		)
		new_code = f"{pe_slug(self.pe)}-SP-8899"
		if frappe.db.exists("Strategic Plan", {"plan_code": new_code}):
			new_code = f"{pe_slug(self.pe)}-SP-8898"
		frappe.set_user("str.planning.correct@example.com")
		try:
			result = correct_reference(
				"Strategic Plan", draft.name, new_code, "Planning Authority correction"
			)
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(result["code"], new_code)

	def test_officer_cannot_correct_reference(self):
		"""A Strategy Officer (no Planning Authority / System Manager) is denied."""
		_ensure_user("str.officer.noplan@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.noplan@example.com")
		try:
			with self.assertRaises(frappe.PermissionError):
				correct_reference(
					"Strategic Plan",
					self.plan,
					f"{pe_slug(self.pe)}-SP-8897",
					"Should be denied",
				)
		finally:
			frappe.set_user("Administrator")
