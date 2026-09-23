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
		# Registering a Version supersedes every Active one whose window it
		# overlaps — including the site's own. Purging the fixture afterwards
		# deletes it but does not undo that, so the statuses are restored
		# explicitly rather than trusted to the purge.
		cls._status_before = {
			row["name"]: row["status"]
			for row in frappe.get_all(settings.METHOD_PROFILE, fields=["name", "status"])
		}
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
		for name, status in cls._status_before.items():
			if frappe.db.exists(settings.METHOD_PROFILE, name) and frappe.db.get_value(settings.METHOD_PROFILE, name, "status") != status:
				doc = frappe.get_doc(settings.METHOD_PROFILE, name)
				doc.flags.kt_supersede = True
				doc.status = status
				doc.save(ignore_permissions=True)
		purge()
		frappe.db.commit()

	def setUp(self):
		frappe.set_user("Administrator")

	def code(self, caught) -> str:
		return getattr(caught.exception, "code", "")

	# --- method profiles -------------------------------------------------

	def _pin_plan_item(self, profile: str) -> str:
		"""Stand in for the one thing that pins a method rule: an Annual Plan
		Item carrying its version. Planning owns that record, and building a
		real one here would drag its whole world into a Configuration test, so
		the row is written at the table level — it exists only to be seen by
		`_method_profile_referenced`, and it is removed again."""
		name = f"{NS}-PIN-1"
		frappe.db.sql(
			"insert into `tabAnnual Plan Item` (name, creation, modified, owner, modified_by, method_profile_version) "
			"values (%s, now(), now(), %s, %s, %s)",
			(name, "Administrator", "Administrator", profile),
		)
		return name

	def _unpin_plan_item(self, name: str) -> None:
		frappe.db.sql("delete from `tabAnnual Plan Item` where name=%s", (name,))

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

	def test_a_profile_version_in_force_is_never_edited_in_place_or_deleted(self):
		# Already in force, so frozen (an unused future one is correctable —
		# see test_a_rule_nobody_uses_and_that_has_not_started_is_corrected_in_place).
		# Its window is in the past and cannot touch the live rule's: registering
		# a Version that overlaps the canonical one supersedes it for real, and
		# purging the fixture afterwards does not bring it back.
		out = self._register_method("2019-07-01", "2019-12-31")
		doc = frappe.get_doc(settings.METHOD_PROFILE, out["profile"])
		doc.provision = "changed"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc(settings.METHOD_PROFILE, out["profile"], ignore_permissions=True)
		with self.assertRaises(ConfigurationError) as caught:
			settings.register_method_profile_version(procurement_method="Open Tender", effective_from="2092-07-01", conditions=[], fixture_namespace=NS)
		self.assertEqual(self.code(caught), "CFG_PROFILE_INVALID")

	def test_a_rule_nobody_uses_and_that_has_not_started_is_corrected_in_place(self):
		"""Owner decision 23 Sep 2026 — an unused, not-yet-effective rule is
		unfinished configuration; correcting it should not leave a dead Version
		behind. The freeze is by effect or by use, whichever comes first."""
		out = self._register_method("2090-07-01", "2090-12-31")
		before_count = len(frappe.get_all(settings.METHOD_PROFILE, filters={"procurement_method": "Open Tender", "fixture_namespace": NS}))
		version = settings.get_method_profile(out["profile"])
		self.assertTrue(version["can_edit"])
		self.assertEqual(version["edit_blocked_reason"], "")

		settings.update_method_profile(
			profile=out["profile"],
			effective_from="2090-08-01",
			effective_until="2090-12-31",
			conditions=[
				{"condition_id": "G-VALUE", "kind": "Known fact", "description": "Corrected in place.", "procurement_category": "Goods", "maximum_amount": 750000, "cumulative_basis": "Per request"},
			],
		)
		corrected = settings.get_method_profile(out["profile"])
		# Same record, same version number — no replacement was created.
		self.assertEqual(corrected["version_number"], version["version_number"])
		self.assertEqual(corrected["effective_from"], "2090-08-01")
		self.assertEqual([c["condition_id"] for c in corrected["conditions"]], ["G-VALUE"])
		self.assertEqual(corrected["conditions"][0]["maximum_amount"], 750000)
		self.assertEqual(before_count, len(frappe.get_all(settings.METHOD_PROFILE, filters={"procurement_method": "Open Tender", "fixture_namespace": NS})))
		# A correction is as visible in the history as a replacement.
		self.assertTrue(
			frappe.db.exists("Audit Event", {"document_type": settings.METHOD_PROFILE, "document_name": out["profile"], "action": "update_method_profile"})
		)
		# It is held to the same standard as registering one.
		with self.assertRaises(ConfigurationError) as caught:
			settings.update_method_profile(profile=out["profile"], effective_from="2090-08-01", conditions=[])
		self.assertEqual(self.code(caught), "CFG_PROFILE_INVALID")

	def test_a_rule_freezes_once_it_takes_effect_or_once_a_plan_uses_it(self):
		"""Either half is enough to freeze it, and the reason says which."""
		in_force = self._register_method("2020-07-01", "2020-12-31")
		version = settings.get_method_profile(in_force["profile"])
		self.assertFalse(version["can_edit"])
		self.assertIn("already taken effect", version["edit_blocked_reason"])
		with self.assertRaises(ConfigurationError) as caught:
			settings.update_method_profile(
				profile=in_force["profile"],
				effective_from="2020-07-01",
				conditions=[{"condition_id": "G-VALUE", "kind": "Known fact", "description": "x", "procurement_category": "Goods"}],
			)
		self.assertEqual(self.code(caught), "CFG_CATALOGUE_IN_USE")
		# A raw Desk edit of the same row is refused for the same reason, so the
		# rule cannot be answered differently depending on the way in.
		doc = frappe.get_doc(settings.METHOD_PROFILE, in_force["profile"])
		doc.provision = "changed"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

		# A future rule that a plan already pins is frozen too.
		future = self._register_method("2089-07-01", "2089-12-31")
		self.assertTrue(settings.get_method_profile(future["profile"])["can_edit"])
		item = self._pin_plan_item(future["profile"])
		try:
			blocked = settings.get_method_profile(future["profile"])
			self.assertFalse(blocked["can_edit"])
			self.assertIn("plan already uses this rule", blocked["edit_blocked_reason"])
		finally:
			self._unpin_plan_item(item)
		# Unpinned again, it is correctable again — the test is the live fact,
		# never a flag stamped on the record.
		self.assertTrue(settings.get_method_profile(future["profile"])["can_edit"])

	def test_a_correction_records_why_it_was_made_and_what_it_replaces(self):
		"""§4.6 — the only way to change a method rule is a new Version, so the
		administrator's reason and the Version it corrects are kept with it;
		otherwise the history is a pile of versions with no account of why."""
		first = self._register_method("2091-07-01", "2091-12-31")
		second = self._register_method(
			"2091-07-01",
			"2091-12-31",
			change_reason="  Maximum for goods raised by the 2091 threshold review.  ",
			replaces=first["profile"],
		)
		version = settings.get_method_profile(second["profile"])
		self.assertEqual(version["change_reason"], "Maximum for goods raised by the 2091 threshold review.")
		self.assertEqual(version["supersedes_version_ids"], [first["profile"]])
		self.assertIn(first["profile"], second["superseded"])

		# Version references are recycled on this long-lived site, so this reads
		# the event this registration wrote, not every event ever written under
		# that name.
		event = frappe.get_all(
			"Audit Event",
			filters={"document_type": settings.METHOD_PROFILE, "document_name": second["profile"], "action": "register_method_profile_version"},
			fields=["metadata"],
			order_by="creation desc",
			limit_page_length=1,
		)
		self.assertEqual(len(event), 1)
		metadata = frappe.parse_json(event[0]["metadata"])
		self.assertEqual(metadata["change_reason"], "Maximum for goods raised by the 2091 threshold review.")
		self.assertEqual(metadata["replaces"], first["profile"])

		# A first Version carries neither, and says so as an absence.
		self.assertEqual(settings.get_method_profile(first["profile"])["change_reason"], "")
		self.assertEqual(settings.get_method_profile(first["profile"])["supersedes_version_ids"], [])

	def test_the_settings_read_publishes_the_vocabularies_the_editor_offers(self):
		"""The Method eligibility editor never invents its own choices: the
		condition kinds and the value bases come from the server, and the
		bases come from the stored Select so the two cannot drift apart."""
		read = settings.get_procurement_settings()
		self.assertEqual(read["condition_kinds"], ["Known fact", "Declaration"])
		self.assertEqual(read["method_applicability_bases"], list(settings.METHOD_APPLICABILITY_BASES))
		self.assertIn("Invitation date", read["method_applicability_bases"])
		stored = frappe.get_meta("Method Profile Condition").get_field("cumulative_basis").options.split("\n")
		self.assertEqual(read["cumulative_bases"], [o for o in stored if o.strip()])
		# Every basis a live Version already uses is offered, so opening the
		# editor on one of them cannot silently drop its value.
		for used in frappe.get_all("Method Profile Condition", pluck="cumulative_basis", distinct=True):
			if used:
				self.assertIn(used, read["cumulative_bases"])

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

	def test_an_unused_funding_source_can_be_removed_but_a_referenced_one_cannot(self):
		created = settings.add_funding_source(label="KT Test Removable")
		self.assertTrue(created["created"])
		self.assertFalse(settings.delete_funding_source(name=created["name"])["deleted"] is False)
		self.assertFalse(frappe.db.exists(settings.FUNDING_SOURCE, created["name"]))
		self.assertTrue(
			frappe.db.exists("Audit Event", {"document_type": settings.FUNDING_SOURCE, "action": "delete_funding_source"})
		)

		referenced = settings.add_funding_source(label="KT Test Referenced")["name"]
		self.addCleanup(lambda: frappe.delete_doc(settings.FUNDING_SOURCE, referenced, force=True, ignore_permissions=True))
		line = frappe.get_doc(
			{
				"doctype": "Procurement Budget Line Version",
				"funding_source": referenced,
			}
		)
		# A throwaway row naming the source is enough to prove the guard reads
		# real usage, not a flag on the source itself — no other Budget Line
		# fields are required for `frappe.db.exists` to see the row.
		line.flags.ignore_mandatory = True
		line.insert(ignore_permissions=True)
		self.addCleanup(lambda: frappe.delete_doc("Procurement Budget Line Version", line.name, force=True, ignore_permissions=True))

		row = next(r for r in settings.list_funding_sources() if r["name"] == referenced)
		self.assertTrue(row["referenced"])
		with self.assertRaises(ConfigurationError) as caught:
			settings.delete_funding_source(name=referenced)
		self.assertEqual(self.code(caught), "CFG_CATALOGUE_IN_USE")
		self.assertTrue(frappe.db.exists(settings.FUNDING_SOURCE, referenced))

		with self.assertRaises(ConfigurationError) as caught:
			settings.delete_funding_source(name="KT Test Does Not Exist")
		self.assertEqual(self.code(caught), "CFG_PROFILE_INVALID")

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
