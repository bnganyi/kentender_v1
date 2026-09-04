"""CFG-CHG-002 v0.6 §5–§8 — the site-configuration commands.

Covers §15.2 items 1–13: first-run atomicity, second-PE impossibility,
`pe_code` immutability, fiscal-year generation and uniqueness, the
single-open-year invariant, close-instant validation against the server
clock, scheduled closure, disable guards, version conflicts, idempotent
replay and configuration-authority boundaries.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_site_configuration
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_core.services import authorization as auth
from kentender_core.services import site_configuration as configuration
from kentender_core.services.configuration_errors import ConfigurationError
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

# Far-future start years so shared-fact ERPNext Fiscal Years are recognisably
# test data (purged by start_year >= 2095).
Y1 = 2096
Y2 = 2097


class ConfigurationTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(purge)
		# These tests move the single-open intake flags onto far-future years;
		# restore whichever years were open beforehand so the canonical §8 seed
		# world (and every sibling suite that depends on it) is left intact.
		cls._open_before = {
			flag: frappe.get_all("Fiscal Year", filters={flag: 1}, pluck="name")
			for flag in (configuration.FLAG_OPEN, configuration.DPP_FLAG_OPEN)
			if frappe.db.has_column("Fiscal Year", flag)
		}
		cls.addClassCleanup(cls._restore_open_flags)
		cls.root = fx.ensure_site_configured()
		frappe.db.commit()

	@classmethod
	def _restore_open_flags(cls):
		frappe.set_user("Administrator")
		for flag, years in cls._open_before.items():
			opener = (
				configuration.open_needs_submission
				if flag == configuration.FLAG_OPEN
				else configuration.open_dpp_submission
			)
			for year in years:
				if frappe.db.exists("Fiscal Year", year) and not frappe.db.get_value("Fiscal Year", year, flag):
					opener(fiscal_year=year, reason="test cleanup: restore the previously open year")
		frappe.db.commit()

	def code(self, caught) -> str:
		return getattr(caught.exception, "code", "")

	def blank_site(self):
		"""Unconfigure the Single inside this test; callers must restore via
		fx.ensure_site_configured() before the test ends (no per-test rollback
		on this runner)."""
		frappe.db.delete("Singles", {"doctype": configuration.SITE_PE_DOCTYPE})
		frappe.clear_document_cache(configuration.SITE_PE_DOCTYPE, configuration.SITE_PE_DOCTYPE)

	def fy(self, start_year: int) -> str:
		name = configuration._fy_name(start_year)
		if not frappe.db.exists("Fiscal Year", name):
			configuration.add_fiscal_year(start_year=start_year)
		return name


class TestSitePE(ConfigurationTestCase):
	def test_a_configured_site_reports_its_identity_and_root(self):
		out = configuration.get_site_configuration()
		self.assertTrue(out["configured"])
		self.assertEqual(out["procuring_entity"]["pe_code"], fx.SITE_PE_CODE)
		self.assertEqual(out["root_unit"]["id"], self.root)

	def test_configuring_twice_is_structurally_refused(self):
		"""CFG-AC-003 — the Single holds one identity; the command refuses."""
		with self.assertRaises(ConfigurationError) as caught:
			configuration.configure_procuring_entity(
				pe_name="Second Entity", pe_code="KT-TEST-2ND", pe_type="State Corporation"
			)
		self.assertEqual(self.code(caught), "CFG_PE_ALREADY_CONFIGURED")

	def test_first_run_configures_the_entity_and_ensures_the_root(self):
		"""CFG-AC-002 — one command; the page's other tabs unlock after it."""
		self.blank_site()
		try:
			self.assertFalse(configuration.is_configured())
			result = configuration.configure_procuring_entity(
				pe_name="KT Test Entity",
				pe_code="KT-TEST-CFG",
				pe_type="State Corporation",
				ppra_registration="PPRA/TEST/0001",
			)
			self.assertTrue(result["configured"])
			self.assertTrue(result["root_unit"])
			self.assertTrue(result["correlation_id"])
			self.assertTrue(configuration.is_configured())
		finally:
			self.blank_site()
			fx.ensure_site_configured()
			frappe.db.commit()

	def test_a_failure_inside_configure_commits_nothing(self):
		"""§15.2 item 1 — rollback leaves neither the PE nor a root behind."""
		self.blank_site()
		try:
			with patch.object(
				configuration, "_ensure_root_unit", side_effect=frappe.ValidationError("boom")
			):
				with self.assertRaises(frappe.ValidationError):
					configuration.configure_procuring_entity(
						pe_name="KT Test Broken",
						pe_code="KT-TEST-BROKEN",
						pe_type="State Corporation",
					)
			# The command never commits; rolling back the open transaction
			# must erase every write it made.
			frappe.db.rollback()
			frappe.clear_document_cache(
				configuration.SITE_PE_DOCTYPE, configuration.SITE_PE_DOCTYPE
			)
			self.assertTrue(configuration.is_configured())  # the committed canonical site
			self.assertEqual(
				frappe.db.get_single_value(configuration.SITE_PE_DOCTYPE, "pe_code"),
				fx.SITE_PE_CODE,
			)
		finally:
			fx.ensure_site_configured()
			frappe.db.commit()

	def test_an_invalid_code_or_type_is_refused(self):
		self.blank_site()
		try:
			for kwargs in (
				{"pe_name": "KT Test Entity", "pe_code": "x", "pe_type": "State Corporation"},
				{"pe_name": "K", "pe_code": "KT-TEST-OK", "pe_type": "State Corporation"},
				{"pe_name": "KT Test Entity", "pe_code": "KT-TEST-OK", "pe_type": "Parastatal"},
			):
				with self.assertRaises(ConfigurationError) as caught:
					configuration.configure_procuring_entity(**kwargs)
				self.assertEqual(self.code(caught), "CFG_PE_INVALID")
		finally:
			self.blank_site()
			fx.ensure_site_configured()
			frappe.db.commit()

	def test_pe_code_is_immutable_through_the_command_and_the_document(self):
		"""CFG-AC-004 — through the UI command and a direct document write."""
		with self.assertRaises(ConfigurationError) as caught:
			configuration.update_procuring_entity(payload={"pe_code": "KT-TEST-NEW"})
		self.assertEqual(self.code(caught), "CFG_PE_CODE_IMMUTABLE")

		single = frappe.get_doc(configuration.SITE_PE_DOCTYPE)
		single.pe_code = "KT-TEST-DIRECT"
		with self.assertRaises(frappe.ValidationError):
			single.save(ignore_permissions=True)
		single.reload()

	def test_update_changes_descriptive_fields_with_a_version_check(self):
		before = frappe.get_doc(configuration.SITE_PE_DOCTYPE)
		try:
			result = configuration.update_procuring_entity(
				payload={"ppra_registration": "PPRA/PE/2019/0114"},
				expected_version=str(before.modified),
			)
			self.assertTrue(result["updated"])
			with self.assertRaises(ConfigurationError) as caught:
				configuration.update_procuring_entity(
					payload={"ppra_registration": "PPRA/PE/2019/0115"},
					expected_version=str(before.modified),
				)
			self.assertEqual(self.code(caught), "CFG_VERSION_CONFLICT")
		finally:
			configuration.update_procuring_entity(
				payload={"ppra_registration": before.ppra_registration or ""}
			)
			frappe.db.commit()

	def test_an_ordinary_user_may_not_configure(self):
		ordinary = fx.user("cfg.ordinary")
		frappe.db.commit()
		frappe.set_user(ordinary)
		try:
			with self.assertRaises(ConfigurationError) as caught:
				configuration.update_procuring_entity(payload={"pe_name": "Nope"})
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(self.code(caught), "CFG_AUTHORITY_REQUIRED")

	def test_configuration_authority_is_not_business_authority(self):
		"""CFG-AC-019 — the administrator who maintains setup still cannot
		exercise a module responsibility without an assignment."""
		decision = auth.authorise_record("Administrator", "Departmental Author", self.root)
		self.assertFalse(decision.allowed)


class TestFiscalYears(ConfigurationTestCase):
	def test_dates_and_identity_are_generated_from_the_start_year(self):
		"""CFG-AC-008/009 — 1 Jul – 30 Jun; never user-entered."""
		preview = configuration.preview_fiscal_year(Y1)
		self.assertEqual(preview["fiscal_year"], f"{Y1}-{Y1 + 1}")
		self.assertEqual(preview["label"], f"FY {Y1}/{str(Y1 + 1)[-2:]}")

		name = self.fy(Y1)
		row = frappe.db.get_value(
			"Fiscal Year", name, ["year_start_date", "year_end_date"], as_dict=True
		)
		self.assertEqual(str(row.year_start_date), f"{Y1}-07-01")
		self.assertEqual(str(row.year_end_date), f"{Y1 + 1}-06-30")

	def test_a_duplicate_year_is_rejected_without_a_partial_record(self):
		self.fy(Y1)
		with self.assertRaises(ConfigurationError) as caught:
			configuration.add_fiscal_year(start_year=Y1)
		self.assertEqual(self.code(caught), "CFG_FY_ALREADY_EXISTS")

	def test_an_idempotent_replay_returns_the_original_result(self):
		"""CFG-AC-023 — same key, one record, one committed result."""
		key = "KT-TEST-FY-IDEMPOTENT"
		first = configuration.add_fiscal_year(start_year=Y2, idempotency_key=key)
		again = configuration.add_fiscal_year(start_year=Y2, idempotency_key=key)
		self.assertEqual(first, again)
		self.assertEqual(
			frappe.db.count("Fiscal Year", {"name": configuration._fy_name(Y2)}), 1
		)

	def test_the_listing_derives_phase_and_orders_descending(self):
		self.fy(Y1)
		self.fy(Y2)
		listing = configuration.list_fiscal_years()
		names = [row["fiscal_year"] for row in listing["fiscal_years"]]
		self.assertLess(names.index(configuration._fy_name(Y2)), names.index(configuration._fy_name(Y1)))
		by_name = {row["fiscal_year"]: row for row in listing["fiscal_years"]}
		self.assertEqual(by_name[configuration._fy_name(Y1)]["phase"], "Upcoming")


class TestNeedsSubmissionFlag(ConfigurationTestCase):
	def open(self, name, **kwargs):
		return configuration.open_needs_submission(fiscal_year=name, reason="Annual needs call.", **kwargs)

	def test_opening_a_second_year_closes_the_first_in_one_command(self):
		"""CFG-BR-006/CFG-AC-011 — at no instant are two years open."""
		one, two = self.fy(Y1), self.fy(Y2)
		self.open(one)
		result = self.open(two)
		self.assertIn(one, result["closed_other_years"])
		open_rows = frappe.get_all(
			"Fiscal Year", filters={configuration.FLAG_OPEN: 1}, pluck="name"
		)
		self.assertEqual(open_rows, [two])
		configuration.close_needs_submission(fiscal_year=two, reason="Test reset.")

	def test_a_past_close_instant_is_rejected_against_the_server_clock(self):
		"""CFG-AC-012."""
		one = self.fy(Y1)
		with self.assertRaises(ConfigurationError) as caught:
			self.open(one, closes_at="2020-01-01 00:00:00")
		self.assertEqual(self.code(caught), "CFG_INTAKE_CLOSE_INSTANT_INVALID")

	def test_the_scheduled_job_closes_a_due_year_and_audits_system(self):
		"""CFG-BR-008/CFG-AC-013."""
		one = self.fy(Y1)
		self.open(one, closes_at="2099-01-01 00:00:00")
		frappe.db.set_value(
			"Fiscal Year", one, configuration.FLAG_CLOSES_AT, now_datetime(), update_modified=False
		)
		result = configuration.close_due_needs_submissions()
		self.assertIn(one, result["closed"])
		self.assertFalse(frappe.db.get_value("Fiscal Year", one, configuration.FLAG_OPEN))
		audit = frappe.get_all(
			"Audit Event",
			filters={"document_type": "Fiscal Year", "document_name": one, "action": "close_needs_submission"},
			fields=["metadata"],
			order_by="creation desc",
			limit_page_length=1,
		)
		self.assertIn("System", str(audit[0]["metadata"]))

	def test_closing_a_year_that_is_not_open_is_refused(self):
		one = self.fy(Y1)
		with self.assertRaises(ConfigurationError) as caught:
			configuration.close_needs_submission(fiscal_year=one, reason="Nothing to close.")
		self.assertEqual(self.code(caught), "CFG_INTAKE_NOT_OPEN")

	def test_disable_is_blocked_while_intake_is_open_with_exact_blockers(self):
		"""CFG-BR-010/CFG-AC-016."""
		one = self.fy(Y1)
		self.open(one)
		try:
			with self.assertRaises(ConfigurationError) as caught:
				configuration.set_fiscal_year_disabled(fiscal_year=one, disabled=True)
			self.assertEqual(self.code(caught), "CFG_FY_IN_USE")
			self.assertIn("Needs submission is open", str(caught.exception))
		finally:
			configuration.close_needs_submission(fiscal_year=one, reason="Test reset.")

	def test_disable_and_re_enable_round_trip_when_unreferenced(self):
		one = self.fy(Y1)
		configuration.set_fiscal_year_disabled(fiscal_year=one, disabled=True)
		self.assertTrue(frappe.db.get_value("Fiscal Year", one, "disabled"))
		configuration.set_fiscal_year_disabled(fiscal_year=one, disabled=False)
		self.assertFalse(frappe.db.get_value("Fiscal Year", one, "disabled"))

	def test_a_stale_version_on_open_is_refused(self):
		one = self.fy(Y1)
		with self.assertRaises(ConfigurationError) as caught:
			self.open(one, expected_version="2000-01-01 00:00:00")
		self.assertEqual(self.code(caught), "CFG_VERSION_CONFLICT")

	def test_the_site_projection_reports_the_open_intake_year(self):
		one = self.fy(Y1)
		self.open(one, closes_at="2099-11-25 23:59:00")
		try:
			out = configuration.get_site_configuration()
			self.assertEqual(out["needs_submission"]["fiscal_year"], one)
			self.assertIn("2099-11-25", out["needs_submission"]["closes_at"])
		finally:
			configuration.close_needs_submission(fiscal_year=one, reason="Test reset.")


class TestDppIntakeFlag(ConfigurationTestCase):
	"""CFG-CHG-002 v0.9 §4.2 / CFG-BR-013 — the departmental-plan intake flag
	follows the needs-flag pattern and is independent of it."""

	def test_dpp_flag_opens_closes_and_is_independent_of_needs_intake(self):
		y1, y2 = self.fy(Y1), self.fy(Y2)
		configuration.open_needs_submission(fiscal_year=y1)
		out = configuration.open_dpp_submission(fiscal_year=y2, closes_at=str(now_datetime().replace(year=2099)))
		self.assertTrue(out["open"])
		state = configuration.get_dpp_submission_state(y2)
		self.assertTrue(state["open"])
		self.assertEqual(configuration.get_dpp_submission_state()["fiscal_year"], y2)
		# Independent flags: needs stays open on Y1 while DPP is open on Y2.
		self.assertTrue(frappe.db.get_value("Fiscal Year", y1, configuration.FLAG_OPEN))
		self.assertFalse(frappe.db.get_value("Fiscal Year", y1, configuration.DPP_FLAG_OPEN))
		site = configuration.get_site_configuration()
		self.assertEqual(site["needs_submission"]["fiscal_year"], y1)
		self.assertEqual(site["dpp_submission"]["fiscal_year"], y2)
		# At most one year open: opening Y1 closes Y2 atomically.
		moved = configuration.open_dpp_submission(fiscal_year=y1)
		self.assertEqual(moved["closed_other_years"], [y2])
		self.assertFalse(configuration.get_dpp_submission_state(y2)["open"])
		# Disable guard names the DPP flag.
		with self.assertRaises(ConfigurationError) as caught:
			configuration.set_fiscal_year_disabled(fiscal_year=y1, disabled=True)
		self.assertEqual(self.code(caught), "CFG_FY_IN_USE")
		configuration.close_dpp_submission(fiscal_year=y1, reason="test close")
		configuration.close_needs_submission(fiscal_year=y1, reason="test close")
		self.assertFalse(configuration.get_dpp_submission_state()["open"])

	def test_scheduled_close_reaches_the_dpp_flag(self):
		y2 = self.fy(Y2)
		configuration.open_dpp_submission(fiscal_year=y2, closes_at=str(now_datetime().replace(year=2099)))
		frappe.db.set_value(
			"Fiscal Year", y2, configuration.DPP_FLAG_CLOSES_AT, now_datetime().replace(year=2001), update_modified=False
		)
		closed = configuration.close_due_dpp_submissions()
		self.assertIn(y2, closed["closed"])
		self.assertFalse(frappe.db.get_value("Fiscal Year", y2, configuration.DPP_FLAG_OPEN))


class TestStatutoryApprovalRoute(ConfigurationTestCase):
	"""CFG-CHG-002 v0.9 §4.1 / CFG-BR-014 — a route is always present and
	never None; CFG-AC-030."""

	def test_site_carries_a_route_and_rejects_an_unknown_one(self):
		single = frappe.get_doc(configuration.SITE_PE_DOCTYPE)
		before = single.statutory_approval_route
		self.assertIn(before, configuration.STATUTORY_APPROVAL_ROUTES)
		out = configuration.update_procuring_entity(payload={"statutory_approval_route": "Council"})
		self.assertTrue(out["updated"])
		self.assertEqual(configuration.get_site_configuration()["procuring_entity"]["statutory_approval_route"], "Council")
		with self.assertRaises(ConfigurationError) as caught:
			configuration.update_procuring_entity(payload={"statutory_approval_route": "None"})
		self.assertEqual(self.code(caught), "CFG_PE_INVALID")
		configuration.update_procuring_entity(payload={"statutory_approval_route": before, "entity_is_county": False})
		self.assertFalse(configuration.get_site_configuration()["procuring_entity"]["entity_is_county"])

	def test_route_derives_from_entity_type_on_first_run(self):
		self.assertEqual(configuration._valid_route("", "County Government"), "County Executive Committee Member")
		self.assertEqual(configuration._valid_route("", "State Corporation"), "Board of Directors")
		self.assertEqual(configuration._valid_route("", "Public University"), "Council")
		self.assertEqual(configuration._valid_route("", "National Government Ministry"), "Cabinet Secretary")
