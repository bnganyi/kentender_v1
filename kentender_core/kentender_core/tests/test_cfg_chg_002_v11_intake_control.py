"""CFG-CHG-002 v0.11 §4.3/§7 Phase 2a — Intake Control locking and
disposal-plan intake, generalized to all three module keys (needs/dpp/
disposal_plan).

Covers: disposal-plan open/close/independence, the `Intake Control` lock
(row creation, per-module-key token), the per-module namespaced audit
fields replacing the retired shared pair, `update_intake_close_instant`,
`effective_open` (disabled-year correctness) and the scheduled closure job
recording distinct effective/cleanup instants.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_cfg_chg_002_v11_intake_control
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_core.services import site_configuration as configuration
from kentender_core.services.configuration_errors import ConfigurationError
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

# Far-future start years, well clear of test_site_configuration.py's own
# 2096/2097 (each suite may run in the same process) and recognisable as
# test data for the purge cleanup.
Y1 = 2196
Y2 = 2197
Y3 = 2198


class IntakeControlTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(purge)
		# Capture the exact closing instant too — a bare reopen with no
		# `closes_at` silently wipes it to "no closing date" (root-caused
		# 2026-09-16 after it corrupted the canonical seed's own needs/dpp
		# closing instants; repaired via `update_intake_close_instant`).
		cls._open_before = {
			flag: frappe.get_all("Fiscal Year", filters={flag: 1}, fields=["name", closes_field])
			for flag, closes_field in (
				(configuration.FLAG_OPEN, configuration.FLAG_CLOSES_AT),
				(configuration.DPP_FLAG_OPEN, configuration.DPP_FLAG_CLOSES_AT),
				(configuration.DISPOSAL_FLAG_OPEN, configuration.DISPOSAL_FLAG_CLOSES_AT),
			)
			if frappe.db.has_column("Fiscal Year", flag)
		}
		cls.addClassCleanup(cls._restore_open_flags)
		fx.ensure_site_configured()
		frappe.db.commit()

	@classmethod
	def _restore_open_flags(cls):
		"""Put the canonical intake world back exactly as the seed documents it.

		This deliberately does **not** trust a value captured in `setUpClass`:
		classes in this module run in sequence, so a later class can capture a
		value an earlier one has already damaged and then faithfully restore
		the damage. `site_setup`'s own constants are the single source of
		truth, so the canonical year is reasserted from those and any other
		year this suite opened is closed.
		"""
		frappe.set_user("Administrator")
		from kentender_core.seeds import site_setup

		canonical = {
			"needs": (site_setup.INTAKE, configuration.FLAG_OPEN, configuration.open_needs_submission),
			"dpp": (site_setup.DPP_INTAKE, configuration.DPP_FLAG_OPEN, configuration.open_dpp_submission),
		}
		for module_key, (intake, flag, opener) in canonical.items():
			year = configuration._fy_name(intake["start_year"])
			if not frappe.db.exists("Fiscal Year", year):
				continue
			closes_at = intake["closes_at"]
			try:
				if frappe.db.get_value("Fiscal Year", year, flag):
					configuration.update_intake_close_instant(
						module_key=module_key,
						fiscal_year=year,
						closes_at=closes_at,
						reason="test cleanup: reassert the seed's documented closing instant",
					)
				else:
					# Reopening also closes whichever far-future test year this
					# suite left holding the module's single open slot.
					opener(
						fiscal_year=year,
						closes_at=closes_at,
						reason="test cleanup: restore the canonical open year",
					)
			except Exception:
				# Cleanup must never mask the test result that preceded it.
				pass
		frappe.db.commit()

	def code(self, caught) -> str:
		return getattr(caught.exception, "code", "")

	def fy(self, start_year: int) -> str:
		name = configuration._fy_name(start_year)
		if not frappe.db.exists("Fiscal Year", name):
			configuration.add_fiscal_year(start_year=start_year)
		return name


class TestDisposalPlanIntake(IntakeControlTestCase):
	def test_disposal_opens_closes_independently_of_needs_and_dpp(self):
		y1, y2, y3 = self.fy(Y1), self.fy(Y2), self.fy(Y3)
		configuration.open_needs_submission(fiscal_year=y1, reason="Annual needs call.")
		configuration.open_dpp_submission(fiscal_year=y2, reason="Annual planning call.")
		try:
			out = configuration.open_disposal_plan_submission(fiscal_year=y3, reason="Disposal intake opened.")
			self.assertTrue(out["open"])
			self.assertTrue(frappe.db.get_value("Fiscal Year", y1, configuration.FLAG_OPEN))
			self.assertTrue(frappe.db.get_value("Fiscal Year", y2, configuration.DPP_FLAG_OPEN))
			self.assertTrue(frappe.db.get_value("Fiscal Year", y3, configuration.DISPOSAL_FLAG_OPEN))
			state = configuration.get_disposal_plan_submission_state(y3)
			self.assertTrue(state["open"])
			self.assertEqual(configuration.get_disposal_plan_submission_state()["fiscal_year"], y3)
			site = configuration.get_site_configuration()
			self.assertEqual(site["needs_submission"]["fiscal_year"], y1)
			self.assertEqual(site["dpp_submission"]["fiscal_year"], y2)
			self.assertEqual(site["disposal_plan_submission"]["fiscal_year"], y3)
		finally:
			configuration.close_disposal_plan_submission(fiscal_year=y3, reason="Test reset.")
			configuration.close_dpp_submission(fiscal_year=y2, reason="Test reset.")
			configuration.close_needs_submission(fiscal_year=y1, reason="Test reset.")

	def test_opening_a_second_disposal_year_closes_the_first(self):
		y1, y2 = self.fy(Y1), self.fy(Y2)
		configuration.open_disposal_plan_submission(fiscal_year=y1, reason="r")
		result = configuration.open_disposal_plan_submission(fiscal_year=y2, reason="r")
		try:
			self.assertIn(y1, result["closed_other_years"])
			open_rows = frappe.get_all("Fiscal Year", filters={configuration.DISPOSAL_FLAG_OPEN: 1}, pluck="name")
			self.assertEqual(open_rows, [y2])
		finally:
			configuration.close_disposal_plan_submission(fiscal_year=y2, reason="Test reset.")

	def test_disposal_close_error_names_disposal_plan_not_needs(self):
		"""§8 — the message names the correct activity, not a hardcoded default."""
		y1 = self.fy(Y1)
		with self.assertRaises(ConfigurationError) as caught:
			configuration.close_disposal_plan_submission(fiscal_year=y1, reason="r")
		self.assertEqual(self.code(caught), "CFG_INTAKE_NOT_OPEN")
		self.assertIn("Disposal plan", str(caught.exception))
		self.assertNotIn("Needs", str(caught.exception))


class TestIntakeControlLock(IntakeControlTestCase):
	def test_acquiring_the_control_creates_the_row_and_increments_the_token(self):
		frappe.db.delete("Intake Control", {"module_key": "needs"})
		frappe.db.commit()
		y1, y2 = self.fy(Y1), self.fy(Y2)
		configuration.open_needs_submission(fiscal_year=y1, reason="r")
		first = frappe.db.get_value("Intake Control", "needs", "control_token")
		self.assertIsNotNone(first)
		configuration.open_needs_submission(fiscal_year=y2, reason="r")
		second = frappe.db.get_value("Intake Control", "needs", "control_token")
		self.assertGreater(second, first)
		configuration.close_needs_submission(fiscal_year=y2, reason="r")

	def test_each_module_key_has_its_own_control_row(self):
		y1 = self.fy(Y1)
		configuration.open_needs_submission(fiscal_year=y1, reason="r")
		configuration.open_dpp_submission(fiscal_year=y1, reason="r")
		configuration.open_disposal_plan_submission(fiscal_year=y1, reason="r")
		try:
			self.assertTrue(frappe.db.exists("Intake Control", "needs"))
			self.assertTrue(frappe.db.exists("Intake Control", "dpp"))
			self.assertTrue(frappe.db.exists("Intake Control", "disposal_plan"))
		finally:
			configuration.close_needs_submission(fiscal_year=y1, reason="r")
			configuration.close_dpp_submission(fiscal_year=y1, reason="r")
			configuration.close_disposal_plan_submission(fiscal_year=y1, reason="r")


class TestPerModuleAuditFields(IntakeControlTestCase):
	def test_the_retired_shared_fields_are_gone(self):
		self.assertFalse(frappe.db.has_column("Fiscal Year", "kentender_flag_changed_by"))
		self.assertFalse(frappe.db.has_column("Fiscal Year", "kentender_flag_changed_at"))

	def test_opening_and_closing_writes_the_namespaced_module_fields(self):
		y1 = self.fy(Y1)
		configuration.open_needs_submission(fiscal_year=y1, reason="r")
		try:
			row = frappe.db.get_value(
				"Fiscal Year",
				y1,
				[
					"kentender_needs_intake_changed_by",
					"kentender_needs_intake_changed_at",
					"kentender_needs_intake_revision",
				],
				as_dict=True,
			)
			self.assertEqual(row["kentender_needs_intake_changed_by"], "Administrator")
			self.assertTrue(row["kentender_needs_intake_changed_at"])
			self.assertEqual(row["kentender_needs_intake_revision"], 1)
			configuration.close_needs_submission(fiscal_year=y1, reason="r")
			self.assertEqual(frappe.db.get_value("Fiscal Year", y1, "kentender_needs_intake_revision"), 2)
		finally:
			if frappe.db.get_value("Fiscal Year", y1, configuration.FLAG_OPEN):
				configuration.close_needs_submission(fiscal_year=y1, reason="test reset")

	def test_opening_dpp_never_touches_the_needs_audit_fields(self):
		y1 = self.fy(Y1)
		configuration.open_needs_submission(fiscal_year=y1, reason="r")
		try:
			before = frappe.db.get_value("Fiscal Year", y1, "kentender_needs_intake_revision")
			configuration.open_dpp_submission(fiscal_year=y1, reason="r")
			try:
				after = frappe.db.get_value("Fiscal Year", y1, "kentender_needs_intake_revision")
				self.assertEqual(before, after)
				self.assertEqual(frappe.db.get_value("Fiscal Year", y1, "kentender_dpp_intake_revision"), 1)
			finally:
				configuration.close_dpp_submission(fiscal_year=y1, reason="r")
		finally:
			configuration.close_needs_submission(fiscal_year=y1, reason="r")


class TestUpdateIntakeCloseInstant(IntakeControlTestCase):
	def test_changes_only_the_close_time_without_touching_other_modules(self):
		y1, y2 = self.fy(Y1), self.fy(Y2)
		configuration.open_needs_submission(fiscal_year=y1, reason="r")
		configuration.open_dpp_submission(fiscal_year=y2, reason="r")
		try:
			out = configuration.update_intake_close_instant(
				module_key="needs", fiscal_year=y1, closes_at="2199-01-01 00:00:00", reason="Extended."
			)
			self.assertEqual(out["fiscal_year"], y1)
			self.assertIn("2199-01-01", str(frappe.db.get_value("Fiscal Year", y1, configuration.FLAG_CLOSES_AT)))
			self.assertTrue(frappe.db.get_value("Fiscal Year", y1, configuration.FLAG_OPEN))
			self.assertTrue(frappe.db.get_value("Fiscal Year", y2, configuration.DPP_FLAG_OPEN))
		finally:
			configuration.close_needs_submission(fiscal_year=y1, reason="r")
			configuration.close_dpp_submission(fiscal_year=y2, reason="r")

	def test_rejects_a_past_instant(self):
		y1 = self.fy(Y1)
		configuration.open_needs_submission(fiscal_year=y1, reason="r")
		try:
			with self.assertRaises(ConfigurationError) as caught:
				configuration.update_intake_close_instant(
					module_key="needs", fiscal_year=y1, closes_at="2020-01-01 00:00:00", reason="r"
				)
			self.assertEqual(self.code(caught), "CFG_INTAKE_CLOSE_INSTANT_INVALID")
		finally:
			configuration.close_needs_submission(fiscal_year=y1, reason="r")

	def test_rejects_a_year_not_open_for_that_module(self):
		y1 = self.fy(Y1)
		with self.assertRaises(ConfigurationError) as caught:
			configuration.update_intake_close_instant(
				module_key="needs", fiscal_year=y1, closes_at="2199-01-01 00:00:00", reason="r"
			)
		self.assertEqual(self.code(caught), "CFG_INTAKE_NOT_OPEN")


class TestEffectiveOpen(IntakeControlTestCase):
	def test_a_disabled_year_reads_as_not_effectively_open(self):
		y1 = self.fy(Y1)
		configuration.open_needs_submission(fiscal_year=y1, reason="r")
		try:
			frappe.db.set_value("Fiscal Year", y1, "disabled", 1, update_modified=False)
			listing = configuration.list_fiscal_years()
			row = next(r for r in listing["fiscal_years"] if r["fiscal_year"] == y1)
			self.assertFalse(row["needs_submission_open"])
			site = configuration.get_site_configuration()
			self.assertIsNone(site["needs_submission"])
		finally:
			frappe.db.set_value("Fiscal Year", y1, "disabled", 0, update_modified=False)
			configuration.close_needs_submission(fiscal_year=y1, reason="r")

	def test_an_expired_close_instant_reads_as_not_effectively_open(self):
		y1 = self.fy(Y1)
		configuration.open_needs_submission(fiscal_year=y1, closes_at="2199-01-01 00:00:00", reason="r")
		try:
			frappe.db.set_value(
				"Fiscal Year", y1, configuration.FLAG_CLOSES_AT, now_datetime().replace(year=2001), update_modified=False
			)
			state = configuration.get_dpp_submission_state  # sanity: unrelated getter unaffected
			listing = configuration.list_fiscal_years()
			row = next(r for r in listing["fiscal_years"] if r["fiscal_year"] == y1)
			self.assertFalse(row["needs_submission_open"])
		finally:
			# The flag column is still 1 (never cleaned up); close_needs_submission
			# still works because it only checks the raw stored flag, matching
			# CFG10-AC-013 ("effective intake is closed even if the physical
			# flag has not yet been cleaned up").
			configuration.close_needs_submission(fiscal_year=y1, reason="r")


class TestCloseDueDisposal(IntakeControlTestCase):
	def test_the_scheduled_job_closes_a_due_disposal_year_with_distinct_instants(self):
		y1 = self.fy(Y1)
		configuration.open_disposal_plan_submission(fiscal_year=y1, closes_at="2199-01-01 00:00:00", reason="r")
		frappe.db.set_value(
			"Fiscal Year", y1, configuration.DISPOSAL_FLAG_CLOSES_AT, now_datetime(), update_modified=False
		)
		result = configuration.close_due_disposal_plan_submissions()
		self.assertIn(y1, result["closed"])
		self.assertFalse(frappe.db.get_value("Fiscal Year", y1, configuration.DISPOSAL_FLAG_OPEN))
		audit = frappe.get_all(
			"Audit Event",
			filters={"document_type": "Fiscal Year", "document_name": y1, "action": "close_disposal_plan_submission"},
			fields=["metadata"],
			order_by="creation desc",
			limit_page_length=1,
		)
		self.assertTrue(audit)
		self.assertIn("effective_close_at", str(audit[0]["metadata"]))
		self.assertIn("cleanup_recorded_at", str(audit[0]["metadata"]))

	def test_close_expired_intakes_covers_all_three_module_keys(self):
		y1, y2, y3 = self.fy(Y1), self.fy(Y2), self.fy(Y3)
		configuration.open_needs_submission(fiscal_year=y1, closes_at="2199-01-01 00:00:00", reason="r")
		configuration.open_dpp_submission(fiscal_year=y2, closes_at="2199-01-01 00:00:00", reason="r")
		configuration.open_disposal_plan_submission(fiscal_year=y3, closes_at="2199-01-01 00:00:00", reason="r")
		for fy, field in (
			(y1, configuration.FLAG_CLOSES_AT),
			(y2, configuration.DPP_FLAG_CLOSES_AT),
			(y3, configuration.DISPOSAL_FLAG_CLOSES_AT),
		):
			frappe.db.set_value("Fiscal Year", fy, field, now_datetime(), update_modified=False)
		result = configuration.close_expired_intakes()
		self.assertIn(y1, result["needs"]["closed"])
		self.assertIn(y2, result["dpp"]["closed"])
		self.assertIn(y3, result["disposal_plan"]["closed"])
