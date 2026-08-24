# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.3 Phase 5 — seed contract (§16).

Covers STR-AC-023, 024. Runs against the real, already-seeded site data
(idempotent by design) rather than tearing the default seed down —
consistent with §16.6's "second seed run shall produce no semantic
change."
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.kentender_mvp_v1_strategy import (
	ACTORS,
	PE_CGK,
	PE_MOH,
	_ensure_config_prerequisites,
	seed_str_des_v2_fixture,
	teardown_str_des_v2_fixture,
	upsert_kentender_mvp_v1_strategy,
)


class TestSeedIdempotency(FrappeTestCase):
	def test_seed_runs_twice_with_no_duplicates(self):
		first = upsert_kentender_mvp_v1_strategy()
		second = upsert_kentender_mvp_v1_strategy()

		self.assertEqual(first["moh"]["plan"], second["moh"]["plan"])
		self.assertEqual(first["moh"]["plan_version"], second["moh"]["plan_version"])
		self.assertEqual(first["kisumu"]["plan"], second["kisumu"]["plan"])
		self.assertEqual(first["kisumu"]["plan_version"], second["kisumu"]["plan_version"])
		self.assertTrue(second["moh"].get("already_seeded"))
		self.assertTrue(second["kisumu"].get("already_seeded"))

		self.assertEqual(
			frappe.db.count("Strategic Plan", {"title": "Ministry of Health Strategic Plan (Demo)"}), 1
		)
		self.assertEqual(
			frappe.db.count("Strategic Plan", {"title": "Kisumu County Development Strategy (Demo)"}), 1
		)
		for user in ACTORS.values():
			self.assertEqual(frappe.db.count("User", {"email": user}), 1)

	def test_seed_produces_exact_spec_content(self):
		out = upsert_kentender_mvp_v1_strategy()

		moh_version = frappe.get_doc("Strategic Plan Version", out["moh"]["plan_version"])
		self.assertEqual(moh_version.status, "Active")
		self.assertEqual(str(moh_version.effective_from), "2023-07-01")
		self.assertEqual(str(moh_version.effective_to), "2028-06-30")

		moh_plan = frappe.get_doc("Strategic Plan", out["moh"]["plan"])
		self.assertEqual(moh_plan.procuring_entity_id, PE_MOH)
		self.assertEqual(moh_plan.plan_role, "Primary")

		kisumu_plan = frappe.get_doc("Strategic Plan", out["kisumu"]["plan"])
		self.assertEqual(kisumu_plan.procuring_entity_id, PE_CGK)

		kisumu_indicator = frappe.db.get_value(
			"Performance Indicator", {"plan_version_id": out["kisumu"]["plan_version"]}, "name"
		)
		kisumu_target = frappe.get_doc(
			"Performance Target", frappe.db.get_value("Performance Target", {"indicator_id": kisumu_indicator}, "name")
		)
		self.assertEqual(str(kisumu_target.target_by_date), "2027-12-31")
		self.assertEqual(kisumu_target.target_value, 70)

		events = frappe.get_all(
			"Audit Event",
			filters={"document_type": "Strategic Plan Version", "document_name": out["moh"]["plan_version"]},
			fields=["action", "performed_by", "timestamp"],
		)
		by_action = {e.action: e for e in events}
		self.assertEqual(by_action["Submit for review"].performed_by, ACTORS["author_moh"])
		self.assertEqual(str(by_action["Submit for review"].timestamp), "2023-06-28 09:10:00")
		self.assertEqual(by_action["Activate"].performed_by, ACTORS["approver_moh"])
		self.assertEqual(str(by_action["Activate"].timestamp), "2023-07-01 00:00:00")

	def test_no_actor_holds_strategy_authority_via_administrator_alone(self):
		upsert_kentender_mvp_v1_strategy()
		for key, email in ACTORS.items():
			roles = frappe.get_roles(email)
			self.assertNotIn("System Manager", roles, f"{key} must not hold System Manager")
			self.assertNotIn("Administrator", roles, f"{key} must not hold Administrator")


class TestConfigPrerequisiteGuard(FrappeTestCase):
	def test_fails_closed_on_missing_prerequisite(self):
		import kentender_strategy.seeds.kentender_mvp_v1_strategy as seed_mod

		original = seed_mod.FY_2027_2028
		seed_mod.FY_2027_2028 = "FY-DOES-NOT-EXIST"
		try:
			with self.assertRaises(frappe.ValidationError):
				_ensure_config_prerequisites()
		finally:
			seed_mod.FY_2027_2028 = original

	def test_passes_with_real_configuration(self):
		_ensure_config_prerequisites()  # must not raise


class TestVersion2DesignFixture(FrappeTestCase):
	def test_v2_fixture_created_and_torn_down_cleanly(self):
		upsert_kentender_mvp_v1_strategy()
		out = seed_str_des_v2_fixture()
		try:
			version = frappe.get_doc("Strategic Plan Version", out["plan_version"])
			self.assertEqual(version.status, "Awaiting Approval")
			self.assertEqual(version.version_number, 2)
			target = frappe.get_doc("Performance Target", out["target"])
			self.assertEqual(target.target_value, 85)
		finally:
			teardown_str_des_v2_fixture(out["plan_version"])
		self.assertFalse(frappe.db.exists("Strategic Plan Version", out["plan_version"]))
		self.assertFalse(frappe.db.exists("Performance Indicator", out["indicator"]))
