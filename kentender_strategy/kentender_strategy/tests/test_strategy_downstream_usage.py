# Copyright (c) 2026, KenTender and contributors
"""STR-UI-12 / STR-AC-017 — derived Downstream Usage (get_strategy_usage)."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_contracts import create_plan, get_strategy_usage
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles


USAGE_MODULES = ("Budget", "Demand", "Planning", "Tender", "Contract", "Asset", "Disposal")


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


def _clear_strategy_ref(doctype: str, name: str) -> None:
	if not name or not frappe.db.exists(doctype, name):
		return
	if doctype == "Budget Line" and frappe.db.has_column(doctype, "primary_plan_version_id"):
		frappe.db.set_value(
			doctype,
			name,
			{
				"primary_target_id": "",
				"primary_target_code": "",
				"primary_target_name": "",
				"primary_plan_version_id": "",
				"primary_snapshot_label": "",
				"primary_strategy_linked": 0,
			},
			update_modified=False,
		)
		return
	if not frappe.db.has_column(doctype, "strategy_plan_version"):
		return
	frappe.db.set_value(
		doctype,
		name,
		{
			"strategy_plan_version": None,
			"strategy_target": None,
			"strategy_snapshot_label": None,
		},
		update_modified=False,
	)


class TestStrategyDownstreamUsage(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]
		cls.plan_id = cls.seed["plan"]
		cls.target_id = cls.seed["target"]
		if cls.plan_id:
			status = frappe.db.get_value("Strategic Plan", cls.plan_id, "status")
			if status != "Active":
				frappe.db.set_value("Strategic Plan", cls.plan_id, "status", "Active")

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_usage_shape_seven_modules_str_ac_017(self):
		_ensure_user("str.viewer.down@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.viewer.down@example.com")
		dto = get_strategy_usage(plan_code=STRATEGY_PLAN_CODE)
		self.assertIn("plan", dto)
		self.assertEqual(dto["plan"]["code"], STRATEGY_PLAN_CODE)
		self.assertIn("status", dto["plan"])
		# Shared plan chrome needs period label (same shape as overview binder).
		self.assertTrue(dto["plan"].get("effective_period_label"))
		self.assertRegex(
			dto["plan"]["effective_period_label"],
			r"^\d{2}-[A-Z][a-z]{2}-\d{4} - \d{2}-[A-Z][a-z]{2}-\d{4}$",
		)
		self.assertIn("start_date", dto["plan"])
		self.assertIn("end_date", dto["plan"])
		self.assertIn("counts", dto)
		self.assertIn("rows", dto)
		self.assertIn("groups", dto)
		for mod in USAGE_MODULES:
			self.assertIn(mod, dto["counts"])
			self.assertIn(mod, dto["groups"])
			self.assertIsInstance(dto["counts"][mod], int)
			self.assertIsInstance(dto["groups"][mod], list)
		# No write surface — DTO only.
		self.assertNotIn("upsert", dto)
		self.assertNotIn("save", dto)

	def test_empty_plan_has_zero_usage(self):
		_ensure_user("str.officer.down.empty@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.down.empty@example.com")
		created = create_plan(
			{
				"plan_code": "TEST-DOWN-EMPTY-PLAN",
				"title": "Empty downstream plan",
				"plan_type": "Entity Strategic Plan",
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
				"procuring_entity": self.pe,
			}
		)
		self.assertTrue(created.get("ok"), created)
		plan_id = created["plan"]["id"]
		plan_code = created["plan"]["code"]
		self.addCleanup(
			lambda: frappe.delete_doc("Strategic Plan", plan_id, force=True, ignore_permissions=True)
		)
		# create_plan may allocate an immutable code (ignore client plan_code).
		dto = get_strategy_usage(plan_version=plan_id)
		self.assertEqual(dto["plan"]["code"], plan_code)
		self.assertEqual(dto["rows"], [])
		for mod in USAGE_MODULES:
			self.assertEqual(dto["counts"][mod], 0)
			self.assertEqual(dto["groups"][mod], [])

	def test_demand_and_budget_rows_derived(self):
		"""STR-SUP-001 / XMOD-STR-006 — Demand + Budget + Planning package strategy projection."""
		frappe.set_user("Administrator")
		from kentender_strategy.seeds.moh_downstream_usage import (
			SEED_BUDGET_LINE_CODE,
			SEED_PACKAGE_CODE,
			seed_moh_downstream_usage_refs,
		)

		result = seed_moh_downstream_usage_refs(plan_name=self.plan_id, target_name=self.target_id)
		self.assertTrue(result.get("ok"), result)
		demand_name = result["linked"]["demand"]
		budget_line_name = result["linked"].get("budget_line")
		package_name = result["linked"].get("package")
		self.assertTrue(budget_line_name, result)
		if demand_name:
			self.addCleanup(lambda: _clear_strategy_ref("Demand", demand_name))
		self.addCleanup(lambda: _clear_strategy_ref("Budget Line", budget_line_name))
		if package_name:
			self.addCleanup(lambda: _clear_strategy_ref("Procurement Package", package_name))

		demand_code = (
			frappe.db.get_value("Demand", demand_name, "demand_id") if demand_name else None
		)

		_ensure_user("str.viewer.down.rows@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.viewer.down.rows@example.com")
		dto = get_strategy_usage(plan_code=STRATEGY_PLAN_CODE)
		if demand_name:
			self.assertGreaterEqual(dto["counts"]["Demand"], 1)
		self.assertGreaterEqual(dto["counts"].get("Budget", 0), 1)
		if not package_name:
			self.skipTest("PKG-MOH-2026-001 not available for Planning usage projection")
		self.assertGreaterEqual(dto["counts"]["Planning"], 1)

		demand_rows = [r for r in dto["rows"] if r["module"] == "Demand"]
		budget_rows = [r for r in dto["rows"] if r["module"] == "Budget"]
		planning_rows = [r for r in dto["rows"] if r["module"] == "Planning"]
		if demand_code:
			self.assertTrue(any(r["record"]["code"] == demand_code for r in demand_rows))
			sample = next(r for r in demand_rows if r["record"]["code"] == demand_code)
			self.assertEqual(sample["doctype"], "Demand")
			self.assertEqual(sample["reference_type"], "Primary alignment")
			self.assertEqual(sample["target"]["code"], TARGET_CODE)
			self.assertTrue(sample["target"]["name"])
			self.assertTrue(sample["record"]["code"])
			self.assertIn("status", sample)
			self.assertIn("modified", sample)

		b_sample = next(
			(r for r in budget_rows if r["record"]["code"] == SEED_BUDGET_LINE_CODE),
			None,
		)
		self.assertTrue(b_sample, budget_rows)
		self.assertEqual(b_sample["doctype"], "Budget Line")
		self.assertEqual(b_sample["reference_type"], "Primary alignment")
		self.assertEqual(b_sample["target"]["code"], TARGET_CODE)

		p_sample = next(
			(r for r in planning_rows if r["record"]["code"] == SEED_PACKAGE_CODE),
			None,
		)
		self.assertTrue(p_sample, planning_rows)
		self.assertEqual(p_sample["doctype"], "Procurement Package")
		self.assertEqual(p_sample["reference_type"], "Primary alignment")
		self.assertEqual(p_sample["target"]["code"], TARGET_CODE)
		self.assertTrue(p_sample["record"]["name"])
		self.assertEqual(len(dto["groups"]["Demand"]), dto["counts"]["Demand"])
		self.assertEqual(len(dto["groups"]["Budget"]), dto["counts"]["Budget"])
		self.assertEqual(len(dto["groups"]["Planning"]), dto["counts"]["Planning"])
