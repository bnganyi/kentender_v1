# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §14 — deterministic seed contract (tracker PLN-701..703).

The seed is proved against the live site world the orchestrator builds (the
§8 site seed, Strategy, Budget and Departmental Needs stages): prerequisites
verified rather than invented, the integrated baseline driven by the named
actors, idempotent on rerun, and the boundary guard that keeps the seed on
published contracts."""

from __future__ import annotations

import ast
import os
import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.seeds import kentender_mvp_v1 as seed

SEED_PATH = os.path.abspath(seed.__file__)


def _world_available() -> bool:
	try:
		seed.verify_prerequisites()
		return True
	except Exception:
		return False


class TestSeedStaticContract(IntegrationTestCase):
	def test_no_seed_business_decision_names_administrator_and_no_retired_concept_survives(self):
		source = open(SEED_PATH, encoding="utf-8").read()
		# spelled by concatenation so this module never trips the scan itself
		retired = (
			"pe_fy" + "_context", "procuring" + "_entity=", "User " + "Permission", "Departmental Plan Submission " + "Window",
			"Plan Reservation " + "Reference", "reserve" + "_funding", "request_finance" + "_confirmation", "Budget " + "Officer",
		)
		for token in retired:
			self.assertNotIn(token, source, token)
		self.assertIn("responsibility_administration", source)

	def test_the_seed_touches_departmental_needs_only_through_published_contracts(self):
		"""§14.10 / D5 — no direct Needs model access from the seed."""
		tree = ast.parse(open(SEED_PATH, encoding="utf-8").read())
		imported = set()
		for node in ast.walk(tree):
			if isinstance(node, ast.ImportFrom) and node.module:
				imported.add(node.module)
		self.assertTrue(all(not m.startswith("kentender_procurement.departmental_needs.doctype") for m in imported))
		self.assertTrue(
			{"kentender_procurement.departmental_needs.services", "kentender_procurement.departmental_needs.services.usage"} & imported,
			"the seed reverses the Need usage projection only through the published usage service",
		)

	def test_the_kebs_profiles_fail_loudly_by_design(self):
		with self.assertRaises(frappe.ValidationError) as caught:
			seed.seed_kebs_profiles()
		self.assertIn("§14.9", str(caught.exception))


@unittest.skipUnless(_world_available(), "the KENTENDER_MVP_V1 world is not seeded on this site (make seed-kentender-mvp-v1)")
class TestSeedContract(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.baseline = seed.upsert_planning_base(commit=False)

	def test_prerequisites_resolve_the_authoritative_records(self):
		resolved = seed.verify_prerequisites()
		self.assertTrue(resolved["bl_dhi"] and resolved["bl_hwd"] and resolved["objective"] and resolved["dhi"] and resolved["hrmd"])
		self.assertEqual(frappe.db.get_value("Organisation Unit", resolved["dhi"], "unit_name"), seed.DHI_NAME)

	def test_the_named_actors_hold_their_responsibilities_and_no_planning_role_uses_administrator(self):
		for actor, role in (
			(seed.PLANNER, "Procurement Planner"), (seed.FINANCE, "Finance Confirmation Officer"),
			(seed.ACCOUNTING_OFFICER, "Accounting Officer"), (seed.STATUTORY, "Plan Statutory Approver"), (seed.AUDITOR, "Auditor"),
		):
			self.assertTrue(frappe.db.exists("User Responsibility Assignment", {"user": actor, "business_role": role, "status": "Enabled"}), f"{actor} {role}")
		self.assertTrue(frappe.db.get_value("User", seed.NO_AUTHORITY, "enabled"))
		self.assertFalse(
			frappe.db.exists("User Responsibility Assignment", {"user": seed.NO_AUTHORITY, "status": "Enabled", "effective_to": ("is", "not set")})
		)

	def test_the_annual_plan_is_active_with_one_confirmed_item_at_80m_and_no_reservation(self):
		failures = [row for row in seed.validate_planning_seed() if not row["ok"]]
		self.assertEqual(failures, [])

	def test_the_design_clock_instants_render_exactly(self):
		from kentender_procurement.procurement_planning.services import plan_read

		plan = plan_read.get_annual_plan(plan_reference=self.baseline["plan_reference"], user=seed.PLANNER)
		card = plan["active_view"]["governance_card"]
		self.assertEqual(card["ao_adoption_line"], "Amina Hassan · 8 Dec 2026, 10:00 EAT")
		self.assertIn("9 Dec 2026, 11:00 EAT", card["statutory_approval_line"])
		self.assertEqual(card["publication_line"], "Acknowledged · 10 Dec 2026, 15:00 EAT")

	def test_a_rerun_is_idempotent(self):
		before = frappe.db.count("Annual Plan Version", {"annual_plan": ("in", frappe.get_all("Annual Plan", filters={"fiscal_year": seed.FY}, pluck="name") or ("",))})
		again = seed.upsert_planning_base(commit=False)
		self.assertTrue(again["idempotent"])
		self.assertEqual(again["plan_reference"], self.baseline["plan_reference"])
		self.assertEqual(frappe.db.count("Annual Plan Version", {"annual_plan": ("in", frappe.get_all("Annual Plan", filters={"fiscal_year": seed.FY}, pluck="name") or ("",))}), before)
