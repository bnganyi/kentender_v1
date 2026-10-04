"""CFG-CHG-002 v0.14 §7.4 (CFG11-AC-030, CFG12-AC-015, CFG-UX-AC-24) — System
setup's records resolve in the shared Technical record search to their own
System setup links, with no CFG-local search.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_cfg_technical_read
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import technical_search


class TestSystemSetupTechnicalSearch(IntegrationTestCase):
	def test_every_cfg_record_family_is_registered_with_the_shared_search(self):
		registered = {r["doctype"] for r in technical_search._resolvers()}
		for doctype in (
			"Regulatory Reference Set",
			"Procurement Method Profile",
			"Procedure Schedule Profile",
			"Business Day Calendar",
			"Funding Source",
			"Intake Control",
		):
			self.assertIn(doctype, registered)

	def test_a_funding_source_resolves_to_its_own_system_setup_link(self):
		name = frappe.get_all("Funding Source", pluck="name", limit=1)
		self.assertTrue(name, "the site has a funding source")
		row = technical_search.resolve(name[0], user="Administrator")
		self.assertEqual(row["route"], ["system-setup", f"#procurement-settings/funding-sources/{name[0]}"])

	def test_a_rule_resolves_to_its_latest_version_link(self):
		sets = frappe.get_all("Regulatory Reference Set", fields=["name", "reference_key"], limit=1)
		self.assertTrue(sets, "the site has a procurement rule")
		row = technical_search.resolve(sets[0]["reference_key"], user="Administrator")
		self.assertEqual(row["route"][0], "system-setup")
		self.assertTrue(row["route"][1].startswith(f"#procurement-settings/procurement-rules/{sets[0]['name']}"))
