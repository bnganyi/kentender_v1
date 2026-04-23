# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Phase G — DIA seed packs (G1) and budget prerequisite check (G2).

Run:
  bench --site <site> run-tests --app kentender_procurement \\
    --module kentender_procurement.demand_intake.tests.test_dia_seed_phase_g
"""

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds.seed_budget_line_dia import verify_prerequisites_for_dia
from kentender_procurement.demand_intake.seeds.dia_seed_common import DIA_SEED_DEMAND_IDS
from kentender_procurement.demand_intake.seeds.seed_dia_basic import run as run_seed_dia_basic
from kentender_procurement.demand_intake.seeds.seed_dia_empty import run as run_seed_dia_empty
from kentender_procurement.demand_intake.seeds.seed_dia_extended import run as run_seed_dia_extended


class TestDiaSeedPhaseG(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		run_seed_dia_empty()

	def test_g2_verify_budget_lines_helper(self):
		out = verify_prerequisites_for_dia()
		self.assertIn("ok", out)
		self.assertIn("budget_lines", out)
		if not out.get("ok"):
			self.skipTest("Budget line prerequisite seed not present: " + str(out.get("missing")))

	def test_g1_basic_then_empty_idempotent(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		v = verify_prerequisites_for_dia()
		if not v.get("ok"):
			self.skipTest("Budget lines missing: " + str(v.get("missing")))
		out = run_seed_dia_basic()
		self.assertEqual(out.get("pack"), "seed_dia_basic")
		for did in DIA_SEED_DEMAND_IDS[:6]:
			self.assertTrue(frappe.db.exists("Demand", {"demand_id": did}), did)
		for did in DIA_SEED_DEMAND_IDS[6:]:
			self.assertFalse(frappe.db.exists("Demand", {"demand_id": did}), did)
		run_seed_dia_empty()
		for did in DIA_SEED_DEMAND_IDS:
			self.assertFalse(frappe.db.exists("Demand", {"demand_id": did}), did)

	def test_g1_extended_creates_nine_ids(self):
		if not frappe.db.exists("DocType", "Demand"):
			self.skipTest("Demand DocType not installed")
		v = verify_prerequisites_for_dia()
		if not v.get("ok"):
			self.skipTest("Budget lines missing: " + str(v.get("missing")))
		out = run_seed_dia_extended()
		self.assertEqual(out.get("pack"), "seed_dia_extended")
		for did in DIA_SEED_DEMAND_IDS:
			self.assertTrue(frappe.db.exists("Demand", {"demand_id": did}), did)
		d5 = frappe.db.get_value(
			"Demand",
			{"demand_id": "DIA-MOH-2026-0005"},
			["status", "planning_status", "reservation_status"],
			as_dict=True,
		)
		self.assertEqual(d5.status, "Planning Ready")
		self.assertEqual(d5.planning_status, "Planning Ready")
		self.assertEqual(d5.reservation_status, "Reserved")
		d9 = frappe.db.get_value("Demand", {"demand_id": "DIA-MOH-2026-0009"}, "status")
		self.assertEqual(d9, "Pending Finance Approval")
