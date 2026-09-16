"""PLN-CHG-001 v1.18 §5.5.1, §5.5.3, §10.11 (C03/C04), §11.6, §17.2 — the
Procurement settings Configuration & Governance maintains: funding sources,
versioned method eligibility and procedure schedule profiles resolved by the
legally applicable date, and the reminder threshold.

PLN18-UX-28 (usable under existing setup authority, immutable when
referenced, historically resolvable, auditable, no configuration approval);
PLN18-AC-071/072/091/115/132 on the resolver side.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_procurement_settings
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import site_setup
from kentender_core.services import procurement_settings as settings
from kentender_core.services.configuration_errors import ConfigurationError
from kentender_core.tests import v16_fixtures as fx
from kentender_core.tests.responsibility_test_cleanup import purge

NS = "KT_TEST_PROCSET"


def _milestones(**overrides):
	rows = []
	for index, (key, default, basis) in enumerate(
		(
			("invitation", None, "Statutory"),
			("bid_opening", 21, "Statutory"),
			("evaluation_completion", 30, "Statutory"),
			("award_approval", 5, "Planning assumption"),
			("award_notification", 2, "Planning assumption"),
			("contract_signing", 14, "Statutory"),
			("delivery_completion", None, "Source-derived"),
		)
	):
		row = {"milestone": key, "sequence": index + 1, "default_days": default, "basis": basis}
		row.update(overrides.get(key, {}))
		rows.append(row)
	return rows


class ProcurementSettingsTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_site_configured()
		site_setup._seed_catalogues()
		settings.purge_fixture_profiles(NS)
		for label in ("KT Test Donor", "KT Test Donor Renamed"):
			if frappe.db.exists(settings.FUNDING_SOURCE, label):
				frappe.delete_doc(settings.FUNDING_SOURCE, label, force=True, ignore_permissions=True)
		cls._threshold_before = settings.get_reminder_threshold_days()
		cls.addClassCleanup(cls._cleanup)
		frappe.db.commit()

	@classmethod
	def _cleanup(cls):
		frappe.set_user("Administrator")
		settings.purge_fixture_profiles(NS)
		for label in ("KT Test Donor", "KT Test Donor Renamed"):
			if frappe.db.exists(settings.FUNDING_SOURCE, label):
				frappe.delete_doc(settings.FUNDING_SOURCE, label, force=True, ignore_permissions=True)
		settings.set_reminder_threshold_days(days=cls._threshold_before)
		purge()
		frappe.db.commit()

	def setUp(self):
		frappe.set_user("Administrator")

	def code(self, caught) -> str:
		return getattr(caught.exception, "code", "")

	# --- method profiles -------------------------------------------------

	def _register_method(self, effective_from, effective_until="", **kwargs):
		return settings.register_method_profile_version(
			procurement_method="Open Tender",
			effective_from=effective_from,
			effective_until=effective_until,
			conditions=[
				{"condition_id": "G-VALUE", "kind": "Known fact", "description": "No fixed maximum for goods.", "procurement_category": "Goods", "maximum_amount": 0, "cumulative_basis": "Funds allocated"},
				{"condition_id": "S-VALUE", "kind": "Known fact", "description": "No fixed maximum for services.", "procurement_category": "Services", "maximum_amount": 0, "cumulative_basis": "Funds allocated"},
			],
			fixture_namespace=NS,
			**kwargs,
		)

	def test_a_new_version_supersedes_the_overlapping_one_and_resolves_by_applicability_date(self):
		first = self._register_method("2094-07-01", "2095-06-30")
		self.assertTrue(first["created"])
		resolved = settings.resolve_method_profile(procurement_method="Open Tender", procurement_category="Goods", applicability_date="2094-09-01")
		self.assertTrue(resolved["found"])
		self.assertEqual(resolved["profile"], first["profile"])
		self.assertEqual(resolved["verification_status"], settings.VERIFICATION_PENDING)
		self.assertEqual([c["condition_id"] for c in resolved["conditions"]], ["G-VALUE"])
		# Works has no condition row on this profile → not supported for it.
		self.assertFalse(settings.resolve_method_profile(procurement_method="Open Tender", procurement_category="Works", applicability_date="2094-09-01")["category_supported"])

		second = self._register_method("2095-01-01", "2095-06-30", verification_status=settings.VERIFICATION_FIXTURE)
		self.assertIn(first["profile"], second["superseded"])
		self.assertEqual(frappe.db.get_value(settings.METHOD_PROFILE, first["profile"], "status"), "Superseded")
		self.assertEqual(second["version_number"], first["version_number"] + 1)
		self.assertEqual(
			settings.resolve_method_profile(procurement_method="Open Tender", procurement_category="Goods", applicability_date="2095-02-01")["profile"],
			second["profile"],
		)
		# Outside every Active window → a gap, reported, never invented.
		gap = settings.resolve_method_profile(procurement_method="Open Tender", procurement_category="Goods", applicability_date="2096-01-01")
		self.assertFalse(gap["found"])
		self.assertEqual(gap["reason"], "no_profile")
		# The superseded Version is retained and readable by name.
		self.assertEqual(settings.get_method_profile(first["profile"])["status"], "Superseded")

	def test_two_active_versions_on_one_date_fail_closed(self):
		a = self._register_method("2093-07-01", "2093-12-31")
		b = self._register_method("2093-07-01", "2093-12-31")
		older = frappe.get_doc(settings.METHOD_PROFILE, a["profile"])
		older.flags.kt_supersede = True
		older.status = "Active"
		older.save(ignore_permissions=True)
		with self.assertRaises(ConfigurationError) as caught:
			settings.resolve_method_profile(procurement_method="Open Tender", procurement_category="Goods", applicability_date="2093-08-01")
		self.assertEqual(self.code(caught), "CFG_RULE_UNRESOLVED")
		self.assertTrue(b["created"])

	def test_a_profile_version_is_never_edited_in_place_or_deleted(self):
		out = self._register_method("2092-07-01", "2092-12-31")
		doc = frappe.get_doc(settings.METHOD_PROFILE, out["profile"])
		doc.provision = "changed"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc(settings.METHOD_PROFILE, out["profile"], ignore_permissions=True)
		with self.assertRaises(ConfigurationError) as caught:
			settings.register_method_profile_version(procurement_method="Open Tender", effective_from="2092-07-01", conditions=[], fixture_namespace=NS)
		self.assertEqual(self.code(caught), "CFG_PROFILE_INVALID")

	# --- schedule profiles -----------------------------------------------

	def test_schedule_profile_reports_periods_completeness_and_gaps(self):
		# Version numbers count every version of this method/category on the
		# site (the live seed may already hold one), so the assertion is relative.
		versions_before = len(frappe.get_all("Procedure Schedule Profile", filters={"procurement_method": "Open Tender", "procurement_category": "Goods"}))
		out = settings.register_schedule_profile_version(
			procurement_method="Open Tender",
			procurement_category="Goods",
			profile_name="KT Test — goods",
			procedure="Test",
			effective_from="2094-07-01",
			effective_until="2095-06-30",
			milestones=_milestones(),
			fixture_namespace=NS,
		)
		resolved = settings.resolve_schedule_profile(procurement_method="Open Tender", procurement_category="Goods", applicability_date="2094-10-01")
		self.assertTrue(resolved["found"])
		self.assertTrue(resolved["complete"])
		self.assertEqual([m["milestone"] for m in resolved["milestones"]], list(settings.MILESTONES))
		self.assertEqual(resolved["periods"]["tendering_period_days"]["default_days"], 21)
		self.assertEqual(resolved["periods"]["award_approval_buffer_days"]["basis"], "Planning assumption")
		self.assertIsNone(resolved["periods"]["tendering_period_days"]["minimum_days"])
		self.assertEqual(resolved["verification_status"], settings.VERIFICATION_PENDING)
		self.assertIsNone(resolved["estimated_delivery_period_default_days"])

		gapped = settings.register_schedule_profile_version(
			procurement_method="Open Tender",
			procurement_category="Services",
			profile_name="KT Test — services",
			effective_from="2094-07-01",
			effective_until="2095-06-30",
			milestones=_milestones(evaluation_completion={"default_days": None}),
			fixture_namespace=NS,
		)
		resolved = settings.resolve_schedule_profile(procurement_method="Open Tender", procurement_category="Services", applicability_date="2094-10-01")
		self.assertEqual(resolved["profile"], gapped["profile"])
		self.assertFalse(resolved["complete"])
		self.assertEqual(resolved["gaps"], ["evaluation_completion"])
		# No profile for Works in this window → a gap, no Open Tender fallback.
		self.assertFalse(settings.resolve_schedule_profile(procurement_method="Open Tender", procurement_category="Works", applicability_date="2094-10-01")["found"])
		self.assertEqual(out["version_number"], versions_before + 1)

	def test_schedule_profile_rejects_a_missing_milestone_and_a_default_outside_its_bounds(self):
		with self.assertRaises(ConfigurationError) as caught:
			settings.register_schedule_profile_version(
				procurement_method="Open Tender", procurement_category="Works", profile_name="KT Test — bad",
				effective_from="2094-07-01", milestones=_milestones()[:-1], fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_PROFILE_INVALID")
		with self.assertRaises(ConfigurationError) as caught:
			settings.register_schedule_profile_version(
				procurement_method="Open Tender", procurement_category="Works", profile_name="KT Test — bad",
				effective_from="2094-07-01", milestones=_milestones(bid_opening={"minimum_days": 30, "default_days": 21}), fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_PROFILE_INVALID")

	# --- funding sources and reminder ------------------------------------

	def test_funding_sources_are_maintained_under_configuration_authority(self):
		added = settings.add_funding_source(label="KT Test Donor")
		self.assertTrue(added["created"])
		self.assertFalse(settings.add_funding_source(label="KT Test Donor")["created"])
		row = next(r for r in settings.list_funding_sources() if r["name"] == "KT Test Donor")
		self.assertTrue(row["enabled"])
		self.assertFalse(row["referenced"])
		out = settings.update_funding_source(name="KT Test Donor", enabled=False, expected_version=row["expected_version"])
		self.assertFalse(out["enabled"])
		with self.assertRaises(ConfigurationError) as caught:
			settings.update_funding_source(name="KT Test Donor", enabled=True, expected_version="1999-01-01 00:00:00")
		self.assertEqual(self.code(caught), "CFG_VERSION_CONFLICT")
		renamed = settings.update_funding_source(name="KT Test Donor", label="KT Test Donor Renamed", enabled=True)
		self.assertEqual(renamed["name"], "KT Test Donor Renamed")
		self.assertTrue(renamed["enabled"])
		self.assertTrue(frappe.db.exists("Audit Event", {"document_type": settings.FUNDING_SOURCE, "action": "update_funding_source"}))

	def test_reminder_threshold_defaults_to_seven_and_is_bounded(self):
		before = settings.get_reminder_threshold_days()
		self.assertGreaterEqual(before, 1)
		out = settings.set_reminder_threshold_days(days=10)
		self.assertEqual(out["approaching_milestone_threshold_days"], 10)
		self.assertEqual(settings.get_reminder_threshold_days(), 10)
		# CFG-CHG-002 v0.11 §10.10 — 0 is legitimate (reminders begin on the
		# milestone date); the bound is 0–365, superseding the old 1–60.
		settings.set_reminder_threshold_days(days=0)
		self.assertEqual(settings.get_reminder_threshold_days(), 0)
		for refused in (-1, 366):
			with self.assertRaises(frappe.ValidationError) as caught:
				settings.set_reminder_threshold_days(days=refused)
			self.assertIn("0 to 365", str(caught.exception))
		settings.set_reminder_threshold_days(days=settings.DEFAULT_REMINDER_THRESHOLD_DAYS)
		self.assertEqual(settings.get_reminder_threshold_days(), 7)

	def test_the_settings_read_is_forbidden_without_configuration_authority(self):
		nobody = fx.user("procset.nobody", "Procset Nobody")
		frappe.set_user(nobody)
		try:
			self.assertEqual(settings.get_procurement_settings()["outcome"], "FORBIDDEN")
			with self.assertRaises(ConfigurationError) as caught:
				settings.add_funding_source(label="KT Test Donor")
			self.assertEqual(self.code(caught), "CFG_AUTHORITY_REQUIRED")
		finally:
			frappe.set_user("Administrator")
		read = settings.get_procurement_settings()
		self.assertEqual(read["outcome"], "OK")
		self.assertIn("funding_sources", read)
		self.assertIn("method_profiles", read)
		self.assertIn("schedule_profiles", read)
		self.assertIn("calendars", read)
		self.assertIn("reference_sets", read)
		self.assertIn("reference_kinds", read)
		self.assertEqual(read["verification_statuses"], list(settings.VERIFICATION_STATUSES))
