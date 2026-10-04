# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The `annual-procurement-plan` and `procurement-plan-item` Pages each carry
a hand-maintained role list — a second, cruder gate that Frappe checks only
on a hard page load, ahead of `get_annual_plan`/`get_plan_item`'s own
`PLAN_READERS` check. It fell out of sync with `PLAN_READERS` (found live 23
Sep 2026): the Head of Procurement Function could open a plan through normal
in-app navigation, since that never re-checks the Page's own role list, but
hit a bare "Not permitted" modal on refresh — nothing tied the Page's list to
the real authorisation source of truth. This locks the two together."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.plan_read import PLAN_READERS

PAGES = ("annual-procurement-plan", "procurement-plan-item")


class TestPageRoleContract(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_every_plan_reader_role_is_granted_on_both_record_pages(self):
		for page_name in PAGES:
			with self.subTest(page=page_name):
				page_roles = {r.role for r in frappe.get_doc("Page", page_name).roles}
				missing = set(PLAN_READERS) - page_roles
				self.assertEqual(missing, set(), f"{page_name}: PLAN_READERS grants {missing} but the Page's own role list does not")
