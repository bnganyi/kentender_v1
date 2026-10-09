# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.29 §8 — "Page-load authorization failures are typed inline states, not
stock framework modals."

A Frappe Page that lists roles answers a user outside the list with the framework's own
"Not permitted" modal and a blank page, before the page's own script can say anything.
The Planning pages carry no role list: the server's read rules (`dpp_read_profile`,
`plan_source_access`, `require_site_read`) decide, and the screen shows their typed
answer. A role list here once locked the Accounting Officer out of a departmental plan
the server itself lets them read."""

import json
from pathlib import Path

from frappe.tests import IntegrationTestCase

PAGES = Path(__file__).resolve().parents[1] / "page"
SLUGS = ("procurement_planning", "departmental_procurement_plan", "annual_procurement_plan", "procurement_plan_item")


class TestPlanningPagesAreNotRoleGated(IntegrationTestCase):
	def test_no_planning_page_lists_roles(self):
		for slug in SLUGS:
			with self.subTest(page=slug):
				page = json.loads((PAGES / slug / f"{slug}.json").read_text(encoding="utf-8"))
				self.assertEqual(page.get("roles"), [], f"{slug} must leave access to the server's read rules")
