"""CFG-CHG-002 v0.14 §10.1/§13 (tracker CFG14-401) — the System setup
Playwright fixture worlds and the restore that follows every spec.

Each world is built from the real commands, is idempotent, and is undone by
`restore_site`, because the intake flags it moves are read by Needs,
Planning and Budget. CONFIG-FIRST and CONFIG-EMPTY are browser-side response
substitutes (tests/ui/smoke/system_setup/helpers.ts), never site worlds:
unconfiguring or emptying the one shared site would break every module.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_system_setup_fixtures
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import playwright_ui_fixtures as worlds
from kentender_core.seeds import site_setup
from kentender_core.services import regulatory_reference as register
from kentender_core.services import site_configuration as configuration

UPCOMING = configuration._fy_name(site_setup.DPP_INTAKE["start_year"])
CURRENT = configuration._fy_name(site_setup.DPP_INTAKE["start_year"] - 1)


def _flags(fy):
	return frappe.db.get_value(
		"Fiscal Year",
		fy,
		[
			configuration.FLAG_OPEN,
			configuration.DPP_FLAG_OPEN,
			configuration.DPP_FLAG_CLOSES_AT,
			configuration.DISPOSAL_FLAG_OPEN,
		],
		as_dict=True,
	)


class TestSystemSetupWorlds(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.addClassCleanup(lambda: worlds.restore_site())

	def test_config_is_the_canonical_site_with_disposal_submissions_closed(self):
		first = worlds.reset_config()
		second = worlds.reset_config()
		self.assertEqual(first["fiscal_year_open"], UPCOMING)
		self.assertEqual(second["fiscal_year_open"], UPCOMING)
		upcoming = _flags(UPCOMING)
		self.assertTrue(upcoming[configuration.FLAG_OPEN])
		self.assertTrue(upcoming[configuration.DPP_FLAG_OPEN])
		self.assertFalse(upcoming[configuration.DISPOSAL_FLAG_OPEN], "CONFIG draws disposal plans Closed")
		current = _flags(CURRENT)
		self.assertFalse(current[configuration.FLAG_OPEN] or current[configuration.DPP_FLAG_OPEN] or current[configuration.DISPOSAL_FLAG_OPEN])

	def test_config_swap_opens_departmental_plans_for_the_current_year_with_no_closing_date(self):
		worlds.reset_config_swap()
		current = _flags(CURRENT)
		self.assertTrue(current[configuration.DPP_FLAG_OPEN])
		self.assertIsNone(current[configuration.DPP_FLAG_CLOSES_AT])
		self.assertFalse(_flags(UPCOMING)[configuration.DPP_FLAG_OPEN], "one year at a time")
		self.assertTrue(_flags(UPCOMING)[configuration.FLAG_OPEN], "needs untouched")

	def test_config_rules_adds_a_pending_reservation_specimen(self):
		out = worlds.reset_config_rules()
		version = register.get_regulatory_reference_version(out["reservation_version"])
		self.assertEqual(version["version_number"], 1)
		self.assertEqual(version["verification_status"], register.VERIFICATION_PENDING)

	def test_restore_puts_the_canonical_flags_and_planning_read_back(self):
		worlds.reset_config_swap()
		worlds.reset_config_rules()
		worlds.restore_site()
		upcoming = _flags(UPCOMING)
		self.assertTrue(upcoming[configuration.DPP_FLAG_OPEN])
		self.assertTrue(upcoming[configuration.DISPOSAL_FLAG_OPEN], "the canonical seed opens disposal")
		self.assertFalse(_flags(CURRENT)[configuration.DPP_FLAG_OPEN])
		self.assertEqual(frappe.db.count(register.SET_DOCTYPE, {"fixture_namespace": worlds.FIXTURE_NAMESPACE}), 0)
		# The CONFIG-RULES specimen would otherwise make Planning's reservation
		# read ambiguous (two planning rules in force).
		self.assertTrue(register.get_regulatory_reference(UPCOMING)["available"])
