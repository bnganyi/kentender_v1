# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 — suspended supplier accounts on Home (owner decision 5 Oct 2026, FU-HOME-46: they were on My Work for
the Supplier Account support officer and must not be lost when My Work is retired). Same facts as `my_work_provider`
(BDS-CHG-001 v0.8 §5.14): one row per Suspended account, cleared only by the restore decision.

Run:
  bench --site kentender-test.local run-tests --app kentender_suppliers \\
    --module kentender_suppliers.supplier_accounts.tests.test_home_provider
"""

from __future__ import annotations

from datetime import datetime

import frappe

from kentender_core.services import home_entries as he
from kentender_core.services import home_support
from kentender_core.services import home_workspace as hw
from kentender_suppliers.supplier_accounts.services import access
from kentender_suppliers.supplier_accounts.services.home_provider import entries
from kentender_suppliers.supplier_accounts.tests.support import AMINA, MARY, AccountsCase, key

AFYA = "Afya Digital Supplies Limited"
NOW = datetime(2027, 6, 18, 10, 0)


class TestSuspendedAccountsOnHome(AccountsCase):
	def setUp(self):
		super().setUp()
		home_support.reset()

	def _version(self, org):
		return frappe.db.get_value("Supplier Organisation", org, "record_version")

	def suspend(self):
		org = self.active_account()
		self.at("2027-05-19 08:00:00")
		access.suspend_supplier_account(organisation=org, reason="Reported misuse of the account.", expected_version=self._version(org), idempotency_key=key(), user=AMINA)
		return org

	def mine(self, org, user=AMINA, region="my_work"):
		home_support.reset()
		return [r for r in entries(user=user, region=region) or [] if r["root"] == org]

	def test_a_suspended_account_is_one_my_work_row_for_the_support_officer(self):
		org = self.suspend()
		(row,) = self.mine(org)
		self.assertEqual((row["region"], row["owner"], row["action_id"]), ("my_work", "suppliers", "review-suspended-access"))
		self.assertEqual((row["title"], row["action"]), (AFYA, "Review suspended supplier account access"))
		self.assertEqual((row["entered_verb"], str(row["entered_at"])), ("Suspended", "2027-05-19 08:00:00"))
		self.assertEqual(row["destination"], {"route": ["Form", "Supplier Organisation", org], "route_options": {}})

	def test_restoring_the_account_clears_the_row(self):
		org = self.suspend()
		access.restore_supplier_account(organisation=org, reason="Misuse report was withdrawn by the reporter.", expected_version=self._version(org), idempotency_key=key(), user=AMINA)
		self.assertEqual(self.mine(org), [])

	def test_it_applies_to_the_support_officer_only_and_to_my_work_only(self):
		org = self.suspend()
		self.assertIsNone(entries(user=MARY, region="my_work"))
		self.assertIsNone(entries(user="Guest", region="my_work"))
		for region in ("coming_up", "waiting", "oversight", "completed"):
			self.assertIsNone(entries(user=AMINA, region=region), region)
		self.assertTrue(self.mine(org))

	def test_through_home_the_row_leads_with_the_business_name_and_opens_the_record(self):
		org = self.suspend()
		frappe.set_user(AMINA)
		self.addCleanup(frappe.set_user, "Administrator")
		page = hw.get_workspace(AMINA, regions=["my_work"], providers=[entries], at=NOW)["regions"]["my_work"]
		shown = [r for r in page["entries"] if r["destination"]["route"][-1] == org]
		self.assertEqual(len(shown), 1)
		self.assertEqual((shown[0]["module"], shown[0]["title"], shown[0]["destination"]["route"][:2]), ("Supplier accounts", AFYA, ["Form", "Supplier Organisation"]))

	def test_the_hook_registers_the_provider(self):
		self.assertIn("kentender_suppliers.supplier_accounts.services.home_provider.entries", frappe.get_hooks("kt_home_providers"))

	def test_reading_writes_nothing(self):
		org = self.suspend()
		before = frappe.db.get_value("Supplier Organisation", org, ["record_version", "modified"])
		self.mine(org)
		self.assertEqual(frappe.db.get_value("Supplier Organisation", org, ["record_version", "modified"]), before)
