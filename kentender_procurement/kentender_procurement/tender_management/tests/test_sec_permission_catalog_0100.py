# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0100 — canonical ``Security Permission`` catalogue seed.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_permission_catalog_0100
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.permissions.catalog import (
	CANONICAL_PERMISSION_IDS,
	canonical_permission_definitions,
)
from kentender_procurement.tender_management.security.permissions.service import (
	PermissionService,
)


class TestSecPermissionCatalog0100(IntegrationTestCase):
	def test_sec_0100_seed_idempotent_and_matches_canonical(self) -> None:
		n = len(canonical_permission_definitions())
		self.assertEqual(n, 46)
		self.assertEqual(len(CANONICAL_PERMISSION_IDS), 46)

		r1 = PermissionService.ensure_catalog_seeded()
		self.assertTrue(r1.get("ok"))
		self.assertEqual(r1.get("total"), 46)

		ids_db = set(
			frappe.get_all("Security Permission", pluck="permission_id"),
		)
		self.assertEqual(ids_db, set(CANONICAL_PERMISSION_IDS))

		r2 = PermissionService.ensure_catalog_seeded()
		self.assertTrue(r2.get("ok"))
		self.assertEqual(r2.get("created"), 0)
		self.assertEqual(r2.get("total"), 46)

		ids_db_after = set(
			frappe.get_all("Security Permission", pluck="permission_id"),
		)
		self.assertEqual(ids_db_after, set(CANONICAL_PERMISSION_IDS))

	def test_sec_0100_risk_and_audit_columns(self) -> None:
		PermissionService.ensure_catalog_seeded()
		low = PermissionService.get_permission_row("PERM_TEMPLATE_VIEW")
		self.assertIsNotNone(low)
		assert low is not None
		self.assertEqual(low.get("risk_level"), "Low")
		self.assertEqual(int(low.get("audit_required") or 0), 0)

		crit = PermissionService.get_permission_row("PERM_TEMPLATE_CONFIGURE_MAPPINGS")
		self.assertIsNotNone(crit)
		assert crit is not None
		self.assertEqual(crit.get("risk_level"), "Critical")
		self.assertEqual(int(crit.get("audit_required") or 0), 1)
