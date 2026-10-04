"""CFG-CHG-002 v0.14 §5 + owner decision D16 (24 Sep 2026) — an overlap is
a declared replacement or it is refused.

"An unrelated overlap is rejected on save … An intentional correcting
overlap requires explicit predecessor linkage." Before this, saving any
version whose dates overlapped an Active one silently retired it — the
settings suite's own comment records that registering a test version
retired the site's canonical rules. Covers all four version families:
procurement rules, method eligibility, procurement schedules and working-day
calendars, for new versions and for in-place corrections (D15).

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_cfg_supersession
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import site_setup
from kentender_core.services import procurement_settings as settings
from kentender_core.services import regulatory_reference as register
from kentender_core.services.configuration_errors import ConfigurationError
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.test_procurement_settings import _milestones

NS = "KT_TEST_CFG_SUPERSESSION"
PLAN = {"obligation_code": "AGPO-30", "measure_stage": "PlanningAllocation", "target_percent": 30}
CONDITIONS = [{"condition_id": "G-VALUE", "kind": "Known fact", "description": "Goods.", "procurement_category": "Goods", "maximum_amount": 0, "cumulative_basis": "Funds allocated"}]


class TestDeclaredSupersession(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_site_configured()
		site_setup._seed_catalogues()
		cls._purge()
		cls.addClassCleanup(cls._purge)
		frappe.db.commit()

	@staticmethod
	def _purge():
		register.purge_fixture_references(NS)
		settings.purge_fixture_profiles(NS)
		frappe.db.commit()

	def code(self, caught) -> str:
		return getattr(caught.exception, "code", "")

	def status(self, doctype, name):
		return frappe.db.get_value(doctype, name, "status")

	# ---- procurement rules -------------------------------------------------

	def _rule(self, reference_set, start, until="", supersedes=None):
		return register.save_regulatory_reference_version(
			reference_set=reference_set, payload=PLAN, effective_from=start, effective_until=until,
			applicability_basis="FiscalYearStart", supersedes_version_ids=supersedes or [], fixture_namespace=NS,
		)

	def test_a_rule_overlap_must_be_declared(self):
		ref = register.create_regulatory_reference(reference_key="KT-TEST-SUPERSESSION", reference_kind="Reservation rules", fixture_namespace=NS)["reference_set"]
		first = self._rule(ref, "2150-07-01", "2151-06-30")["reference"]
		with self.assertRaises(ConfigurationError) as caught:
			self._rule(ref, "2151-01-01", "2151-12-31")
		self.assertEqual(self.code(caught), "CFG_SUPERSESSION_INVALID")
		self.assertEqual(frappe.db.count(register.DOCTYPE, {"reference_set": ref}), 1, "nothing written")
		self.assertEqual(self.status(register.DOCTYPE, first), "Active")

		second = self._rule(ref, "2151-01-01", "2151-12-31", supersedes=[first])
		self.assertEqual(second["superseded"], [first])
		self.assertEqual(self.status(register.DOCTYPE, first), "Superseded")

	def test_a_rule_that_does_not_overlap_needs_no_declaration(self):
		ref = register.create_regulatory_reference(reference_key="KT-TEST-SUPERSESSION-GAP", reference_kind="Reservation rules", fixture_namespace=NS)["reference_set"]
		first = self._rule(ref, "2152-07-01", "2153-06-30")["reference"]
		self._rule(ref, "2153-07-01")
		self.assertEqual(self.status(register.DOCTYPE, first), "Active")

	# ---- method eligibility -------------------------------------------------

	def _method(self, start, until="", replaces=""):
		return settings.register_method_profile_version(
			procurement_method="Direct Procurement", effective_from=start, effective_until=until,
			conditions=CONDITIONS, replaces=replaces, fixture_namespace=NS,
		)

	def test_a_method_overlap_must_be_declared(self):
		first = self._method("2154-07-01", "2155-06-30")["profile"]
		with self.assertRaises(ConfigurationError) as caught:
			self._method("2155-01-01", "2155-12-31")
		self.assertEqual(self.code(caught), "CFG_SUPERSESSION_INVALID")
		self.assertEqual(self.status(settings.METHOD_PROFILE, first), "Active")
		self._method("2155-01-01", "2155-12-31", replaces=first)
		self.assertEqual(self.status(settings.METHOD_PROFILE, first), "Superseded")

	# ---- procurement schedules ----------------------------------------------

	def _schedule(self, start, until="", supersedes=None):
		return settings.register_schedule_profile_version(
			procurement_method="Direct Procurement", procurement_category="Goods", profile_name="KT Test supersession",
			effective_from=start, effective_until=until, milestones=_milestones(),
			supersedes_version_ids=supersedes or [], fixture_namespace=NS,
		)

	def test_a_schedule_overlap_must_be_declared(self):
		first = self._schedule("2156-07-01", "2157-06-30")["profile"]
		with self.assertRaises(ConfigurationError) as caught:
			self._schedule("2157-01-01", "2157-12-31")
		self.assertEqual(self.code(caught), "CFG_SUPERSESSION_INVALID")
		self.assertEqual(self.status(settings.SCHEDULE_PROFILE, first), "Active")
		self._schedule("2157-01-01", "2157-12-31", supersedes=[first])
		self.assertEqual(self.status(settings.SCHEDULE_PROFILE, first), "Superseded")

	def test_an_in_place_correction_cannot_move_into_an_undeclared_overlap(self):
		"""D15 keeps correcting an unused version in place; D16 still applies."""
		first = self._schedule("2158-07-01", "2158-12-31")["profile"]
		second = self._schedule("2159-07-01", "2159-12-31")["profile"]
		with self.assertRaises(ConfigurationError) as caught:
			settings.update_schedule_profile(
				profile=second, profile_name="KT Test supersession", effective_from="2158-10-01",
				effective_until="2159-12-31", milestones=_milestones(),
			)
		self.assertEqual(self.code(caught), "CFG_SUPERSESSION_INVALID")
		self.assertEqual(self.status(settings.SCHEDULE_PROFILE, first), "Active")

	# ---- working-day calendars ----------------------------------------------

	def _calendar(self, start, until="", supersedes=None):
		return settings.register_business_day_calendar_version(
			calendar_name="KT Test supersession calendar", effective_from=start, effective_until=until,
			weekend_days=["Saturday", "Sunday"], supersedes_version_ids=supersedes or [], fixture_namespace=NS,
		)

	def test_a_calendar_overlap_must_be_declared(self):
		first = self._calendar("2160-01-01", "2160-12-31")["calendar"]
		with self.assertRaises(ConfigurationError) as caught:
			self._calendar("2160-06-01", "2160-12-31")
		self.assertEqual(self.code(caught), "CFG_SUPERSESSION_INVALID")
		self.assertEqual(self.status(settings.CALENDAR, first), "Active")
		self._calendar("2160-06-01", "2160-12-31", supersedes=[first])
		self.assertEqual(self.status(settings.CALENDAR, first), "Superseded")

	def test_declaring_something_that_is_not_an_overlapping_version_of_the_same_record_is_refused(self):
		first = self._calendar("2161-01-01", "2161-06-30")["calendar"]
		with self.assertRaises(ConfigurationError) as caught:
			self._calendar("2161-07-01", supersedes=[first])  # does not overlap
		self.assertEqual(self.code(caught), "CFG_SUPERSESSION_INVALID")
