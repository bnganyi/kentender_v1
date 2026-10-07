# Copyright (c) 2026, KenTender and contributors
"""RG-20 / AUD-BUD-004: the database-level concurrency guards (one Active Budget Version per
Budget, one commitment per (contract, reservation)) exist on a site that was installed after the
patches landed. A fresh install marks every patch complete without running it, so the guards also
have to be ensured by the install and migrate hooks. The ensure step is idempotent."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget import hooks, install

VERSION_TABLE = "tabProcurement Budget Version"
VERSION_INDEX = "uq_procurement_budget_version_active_budget"
COMMITMENT_TABLE = "tabProcurement Commitment"
COMMITMENT_INDEX = "uq_commitment_contract_reservation"


class TestDatabaseGuardsAreEnsuredByTheInstallHooks(IntegrationTestCase):
	def test_the_install_and_migrate_hooks_ensure_the_guards(self):
		self.assertEqual(hooks.after_install, "kentender_budget.install.after_install")
		self.assertEqual(hooks.after_migrate, "kentender_budget.install.after_migrate")

	def test_a_missing_guard_is_recreated_and_a_second_run_changes_nothing(self):
		self.addCleanup(install.ensure_database_guards)
		if frappe.db.has_index(COMMITMENT_TABLE, COMMITMENT_INDEX):
			frappe.db.sql_ddl(f"alter table `{COMMITMENT_TABLE}` drop index `{COMMITMENT_INDEX}`")
		if frappe.db.has_index(VERSION_TABLE, VERSION_INDEX):
			frappe.db.sql_ddl(f"alter table `{VERSION_TABLE}` drop index `{VERSION_INDEX}`")
		self.assertFalse(frappe.db.has_index(COMMITMENT_TABLE, COMMITMENT_INDEX))
		self.assertFalse(frappe.db.has_index(VERSION_TABLE, VERSION_INDEX))

		install.ensure_database_guards()
		self.assertTrue(frappe.db.has_index(COMMITMENT_TABLE, COMMITMENT_INDEX))
		self.assertTrue(frappe.db.has_index(VERSION_TABLE, VERSION_INDEX))
		self.assertFalse(frappe.db.has_index(COMMITMENT_TABLE, "contract"), "the table-wide unique key on contract must stay dropped")

		install.ensure_database_guards()  # double run
		self.assertTrue(frappe.db.has_index(COMMITMENT_TABLE, COMMITMENT_INDEX))
		self.assertTrue(frappe.db.has_index(VERSION_TABLE, VERSION_INDEX))
