# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-004 — WORKS master strategy seed (spec §8) + VAL-SEED-003 alignment.

Run:
  bench --site kentender.midas.com run-tests --app kentender_strategy \\
    --module kentender_strategy.tests.test_r2_004_works_master_strategy_seed
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_procuring_entity
from kentender_strategy.seeds import works_master_strategy_hierarchy as wsh
from kentender_strategy.seeds.seed_works_master_strategy_hierarchy import run as seed_run_works_master_strategy


def _purge_plan_chain_for_tests(pe_name: str) -> None:
	"""Remove §8 seed rows for this PE+year slice when they match master codes/title (test isolation)."""
	rows = frappe.get_all(
		"Strategic Plan",
		filters={
			"procuring_entity": pe_name,
			"start_year": wsh.START_YEAR,
			"end_year": wsh.END_YEAR,
		},
		fields=["name", "strategic_plan_name"],
	)
	for row in rows:
		pid = row.name
		has_seed_prog = frappe.db.exists(
			"Strategy Program",
			{"strategic_plan": pid, "program_code": wsh.PROGRAM_CODE},
		)
		title_match = (row.strategic_plan_name or "").strip() == wsh.PLAN_TITLE
		if not (has_seed_prog or title_match):
			continue
		plan_doc = frappe.get_doc("Strategic Plan", pid)
		if (plan_doc.status or "").strip() != "Draft":
			plan_doc.status = "Draft"
			plan_doc.save(ignore_permissions=True)
		for tgt in frappe.get_all("Strategy Target", filters={"strategic_plan": pid}, pluck="name"):
			frappe.delete_doc("Strategy Target", tgt, force=1, ignore_permissions=True)
		for obj in frappe.get_all("Strategy Objective", filters={"strategic_plan": pid}, pluck="name"):
			frappe.delete_doc("Strategy Objective", obj, force=1, ignore_permissions=True)
		for sp in frappe.get_all("Sub Program", filters={"strategic_plan": pid}, pluck="name"):
			frappe.delete_doc("Sub Program", sp, force=1, ignore_permissions=True)
		for prog in frappe.get_all("Strategy Program", filters={"strategic_plan": pid}, pluck="name"):
			frappe.delete_doc("Strategy Program", prog, force=1, ignore_permissions=True)
		frappe.delete_doc("Strategic Plan", pid, force=1, ignore_permissions=True)


def _val_seed_003_ok() -> bool:
	obj = frappe.get_all(
		"Strategy Objective",
		filters={"objective_code": wsh.OBJECTIVE_CODE},
		fields=["name", "program", "strategic_plan"],
		limit=1,
	)
	if not obj:
		return False
	o = obj[0]
	return bool(o.get("program")) and bool(o.get("strategic_plan"))


class TestR2004WorksMasterStrategySeed(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.pe = ensure_procuring_entity("PE-MOH", "Ministry of Health")
		_purge_plan_chain_for_tests(self.pe)

	def tearDown(self):
		_purge_plan_chain_for_tests(self.pe)

	def test_upsert_satisfies_val_seed_003_shape(self):
		out = wsh.upsert_works_master_strategy_hierarchy()
		self.assertTrue(out.get("ok"), msg=str(out))
		self.assertEqual(out.get("codes", {}).get("objective_code"), wsh.OBJECTIVE_CODE)
		self.assertTrue(_val_seed_003_ok())

	def test_upsert_is_idempotent_when_plan_active(self):
		out1 = wsh.upsert_works_master_strategy_hierarchy()
		self.assertTrue(out1.get("ok"))
		out2 = wsh.upsert_works_master_strategy_hierarchy()
		self.assertTrue(out2.get("ok"))
		self.assertEqual(out1.get("strategic_plan"), out2.get("strategic_plan"))
		self.assertEqual(out1.get("strategy_objective"), out2.get("strategy_objective"))
		self.assertTrue(out2.get("idempotent"))

	def test_seed_run_includes_desk_visibility_hint(self):
		out = seed_run_works_master_strategy()
		self.assertTrue(out.get("ok"), msg=str(out))
		self.assertIn("desk_visibility", out)
		self.assertEqual(out["desk_visibility"]["procuring_entity"], out["procuring_entity"])

	def test_run_sync_scope_adds_user_permission(self):
		email = f"kt_r2_scope_{frappe.generate_hash(length=6)}@example.com"
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Scope",
					"last_name": "Test",
					"send_welcome_email": 0,
					"enabled": 1,
					"user_type": "System User",
				}
			).insert(ignore_permissions=True)
		out = seed_run_works_master_strategy(sync_scope_user_email=email)
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("user_permission_synced_for"), email)
		self.assertTrue(
			frappe.db.exists(
				"User Permission",
				{"user": email, "allow": "Procuring Entity", "for_value": self.pe},
			)
		)

	def test_missing_procuring_entity_returns_error_dict(self):
		with patch.object(wsh, "resolve_procuring_entity_moh", return_value=None):
			out = wsh.upsert_works_master_strategy_hierarchy()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "MISSING_PROCURING_ENTITY")
