# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""KenTender v1 seed packs — idempotency and counts.

Run:
  bench --site <site> run-tests --app kentender_core --module kentender_core.tests.test_seed_v1
"""

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import constants as C
from kentender_core.seeds.reset_core_seed import run as reset_core_seed
from kentender_core.seeds.seed_strategy_basic import run as run_strategy_basic


class TestSeedV1(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			reset_core_seed(dry_run=False)
		except Exception:
			frappe.db.rollback()
		super().tearDown()

	def test_1_seed_strategy_basic_idempotent_counts(self):
		frappe.set_user("Administrator")
		run_strategy_basic()
		p1 = frappe.db.get_value(
			"Strategic Plan",
			{"strategic_plan_name": C.PLAN_BASIC_NAME, "procuring_entity": C.ENTITY_MOH},
			"name",
		)
		self.assertTrue(p1)
		c1 = frappe.db.count("Strategy Program", {"strategic_plan": p1})
		self.assertEqual(c1, 2)
		run_strategy_basic()
		p2 = frappe.db.get_value(
			"Strategic Plan",
			{"strategic_plan_name": C.PLAN_BASIC_NAME, "procuring_entity": C.ENTITY_MOH},
			"name",
		)
		self.assertTrue(p2)
		c2 = frappe.db.count("Strategy Program", {"strategic_plan": p2})
		self.assertEqual(c2, 2)

	def test_2_roles_created_with_core_seed(self):
		from kentender_core.seeds.seed_core_minimal import run as run_core

		frappe.set_user("Administrator")
		run_core()
		for role in C.BUSINESS_ROLES:
			self.assertTrue(frappe.db.exists("Role", role))
