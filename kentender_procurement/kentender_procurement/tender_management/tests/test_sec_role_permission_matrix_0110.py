# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0110 — canonical role–permission matrix seed and non-grant checks.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_role_permission_matrix_0110
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.permissions.role_matrix import (
	CANONICAL_ROLE_CODES,
	ROLE_MATRIX,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)


class TestSecRolePermissionMatrix0110(IntegrationTestCase):
	def test_sec_0110_seed_idempotent_and_roles_exist(self) -> None:
		self.assertEqual(len(CANONICAL_ROLE_CODES), 9)

		r1 = RolePermissionService.ensure_matrix_seeded()
		self.assertTrue(r1.get("ok"))
		self.assertEqual(r1.get("roles_total"), 9)

		for code in CANONICAL_ROLE_CODES:
			self.assertTrue(
				frappe.db.exists("Security Role", code),
				msg=f"Missing Security Role {code!r}",
			)

		r2 = RolePermissionService.ensure_matrix_seeded()
		self.assertTrue(r2.get("ok"))
		self.assertEqual(r2.get("roles_created"), 0)

	def test_sec_0110_grants_match_matrix_and_non_grants_absent(self) -> None:
		RolePermissionService.ensure_matrix_seeded()

		for role_code, spec in ROLE_MATRIX.items():
			with self.subTest(role=role_code):
				granted = RolePermissionService.granted_ids_for_role(role_code)
				self.assertEqual(
					granted,
					spec.grants,
					msg=f"{role_code}: DB grants must match matrix exactly",
				)
				for perm in spec.explicit_non_grants:
					self.assertNotIn(
						perm,
						granted,
						msg=f"{role_code}: explicit non-grant {perm!r} must not be granted",
					)
