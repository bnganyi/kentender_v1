# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-001 — governance Role bootstrap (idempotent, no DocPerms).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_roles
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_roles import (
	STD_TEMPLATE_GOVERNANCE_ROLES,
	ensure_std_template_governance_roles,
)


class TestStdTemplateGovernanceRoles(IntegrationTestCase):
	def test_std_gov_001_roles_idempotent_and_exact_names(self) -> None:
		frappe.set_user("Administrator")
		ensure_std_template_governance_roles()
		ensure_std_template_governance_roles()

		for role_name in STD_TEMPLATE_GOVERNANCE_ROLES:
			with self.subTest(role=role_name):
				self.assertTrue(
					frappe.db.exists("Role", role_name),
					f"Role {role_name!r} must exist after ensure_std_template_governance_roles",
				)
				rows = frappe.get_all(
					"Role",
					filters={"name": role_name},
					pluck="name",
				)
				self.assertEqual(
					len(rows),
					1,
					f"Role {role_name!r} must be unique (no duplicate inserts)",
				)

	def test_std_gov_001_does_not_touch_system_manager(self) -> None:
		frappe.set_user("Administrator")
		self.assertTrue(
			frappe.db.exists("Role", "System Manager"),
			"Frappe core role System Manager must still exist",
		)

	def test_std_gov_001_role_tuple_excludes_qa_and_system_manager(self) -> None:
		# Pack §6: QA / Test User only in test fixtures; System Manager is core Frappe.
		self.assertNotIn("QA / Test User", STD_TEMPLATE_GOVERNANCE_ROLES)
		self.assertNotIn("System Manager", STD_TEMPLATE_GOVERNANCE_ROLES)
