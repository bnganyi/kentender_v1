# Copyright (c) 2026, KenTender and contributors
"""STR-UI-15 / STR-FR-130+ Strategy Performance projection evidence."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_performance import (
	can_export_strategy_performance,
	export_strategy_performance_report,
	get_strategy_performance,
)
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
	have = set(frappe.get_roles(email))
	for role in (
		"Strategy Viewer",
		"Strategy Officer",
		"Strategy Manager",
		"Strategy Reviewer",
		"Planning Authority",
		"Performance Officer",
		"Performance Verifier",
	):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles(*roles)
	if procuring_entity:
		frappe.defaults.set_user_default("Procuring Entity", procuring_entity, user=email)
	return email


class TestStrategyPerformance(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_viewer_can_load_projection(self):
		_ensure_user("str.viewer.perf@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.viewer.perf@example.com")
		dto = get_strategy_performance(procuring_entity=self.pe, plan_code=STRATEGY_PLAN_CODE)
		self.assertEqual(dto["plan"]["code"], STRATEGY_PLAN_CODE)
		self.assertIn("strip", dto)
		self.assertIn("as_at", dto)
		self.assertIn("source_coverage", dto)
		self.assertIn("outcomes", dto)
		self.assertIn("exceptions", dto)
		self.assertIn("procurement", dto)
		self.assertTrue(dto["capabilities"]["export_report"])
		self.assertFalse(dto["capabilities"]["open_portfolio"])

	def test_officer_cannot_export(self):
		_ensure_user("str.officer.perf@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.perf@example.com")
		self.assertFalse(can_export_strategy_performance())
		with self.assertRaises(frappe.PermissionError):
			export_strategy_performance_report(procuring_entity=self.pe, plan_code=STRATEGY_PLAN_CODE)

	def test_manager_export_includes_meta(self):
		_ensure_user("str.manager.perf@example.com", ["Strategy Manager"], self.pe)
		frappe.set_user("str.manager.perf@example.com")
		out = export_strategy_performance_report(procuring_entity=self.pe, plan_code=STRATEGY_PLAN_CODE)
		self.assertTrue(out.get("ok"))
		self.assertIn("as_at", out)
		self.assertIn("source_coverage", out)
		self.assertIn("filters", out)
		self.assertIn("Strategy Performance", out["content"])
		self.assertIn(STRATEGY_PLAN_CODE, out["content"])
		# Formula injection guard — leading = becomes quoted
		self.assertNotRegex(out["content"], r"(?m)^=\+")

	def test_strip_and_stages_are_derived(self):
		frappe.set_user("Administrator")
		dto = get_strategy_performance(plan_code=STRATEGY_PLAN_CODE)
		strip = dto["strip"]
		self.assertGreaterEqual(strip["active_targets"], 1)
		# Lifecycle stages present and not presented as a single summed total field
		stages = dto["procurement"]["stages"]
		self.assertGreaterEqual(len(stages), 2)
		self.assertNotIn("total_procurement_value", dto["procurement"])
		self.assertIn("non_additivity_note", dto["procurement"]["funding"])

	def test_entity_scope_blocks_other_pe(self):
		other = "PE-PERF-SCOPE-TEST"
		if not frappe.db.exists("Procuring Entity", {"entity_code": "PERF-SCOPE"}):
			frappe.get_doc(
				{
					"doctype": "Procuring Entity",
					"entity_code": "PERF-SCOPE",
					"entity_name": "Perf Scope PE",
				}
			).insert(ignore_permissions=True)
		other = frappe.db.get_value("Procuring Entity", {"entity_code": "PERF-SCOPE"}, "name")
		_ensure_user("str.viewer.scope.perf@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.viewer.scope.perf@example.com")
		with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
			get_strategy_performance(procuring_entity=other)
