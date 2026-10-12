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
from kentender_core.services.command_write_guard import fixture_insert, purge_doc

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

	def _pin_plan_item(self, profile: str, field: str = "method_profile_version") -> str:
		"""Stand in for the one thing that pins a method rule: an Annual Plan
		Item carrying its version. Planning owns that record, and building a
		real one here would drag its whole world into a Configuration test, so
		the row is written at the table level — it exists only to be seen by
		`_method_profile_referenced`, and it is removed again."""
		name = f"{NS}-PIN-{field}"
		frappe.db.sql(
			f"insert into `tabAnnual Plan Item` (name, creation, modified, owner, modified_by, {field}) "
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

		second = self._register_method("2095-01-01", "2095-06-30", verification_status=settings.VERIFICATION_FIXTURE, replaces=first["profile"])
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
		b = self._register_method("2093-07-01", "2093-12-31", replaces=a["profile"])
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

	def test_an_administrator_marks_a_rule_valid_while_it_is_in_force_and_in_use(self):
		"""Owner decision 23 Sep 2026 — the old "Source check needed" named a
		check that did not exist for a method rule, and once the version was in
		force there was no way to clear it at all: the rule blocked plan
		submission and the screen offered nothing to do about it. Validity is
		now the administrator's own recorded statement, and it is settable
		exactly when it is needed — in force, and pinned by a plan."""
		out = self._register_method("2018-07-01", "2018-12-31")
		self.assertFalse(settings.get_method_profile(out["profile"])["valid"])
		# In force, so its content is frozen...
		self.assertFalse(settings.get_method_profile(out["profile"])["can_edit"])
		item = self._pin_plan_item(out["profile"])
		try:
			# ...and pinned by a plan, which is the hardest case there is.
			settings.set_version_validity(doctype=settings.METHOD_PROFILE, name=out["profile"], valid=True, note="Checked against the gazette.")
			read = settings.get_method_profile(out["profile"])
			self.assertTrue(read["valid"])
			self.assertEqual(read["verification_status"], settings.VERIFICATION_VERIFIED)
			# Planning reads this same field, so the flag is live downstream.
			self.assertEqual(
				settings.resolve_method_profile(procurement_method="Open Tender", procurement_category="Goods", applicability_date="2018-09-01")["verification_status"],
				settings.VERIFICATION_VERIFIED,
			)
			# Marking it valid says nothing new about the rule's content, which
			# stays exactly as immutable as it was.
			doc = frappe.get_doc(settings.METHOD_PROFILE, out["profile"])
			doc.provision = "changed"
			with self.assertRaises(frappe.ValidationError):
				doc.save(ignore_permissions=True)
			# Who said it and when is recorded either way.
			self.assertTrue(
				frappe.db.exists("Audit Event", {"document_type": settings.METHOD_PROFILE, "document_name": out["profile"], "action": "set_version_validity"})
			)
			# It can be withdrawn again, and saying it twice is not an event.
			self.assertFalse(settings.set_version_validity(doctype=settings.METHOD_PROFILE, name=out["profile"], valid=True)["changed"])
			settings.set_version_validity(doctype=settings.METHOD_PROFILE, name=out["profile"], valid=False)
			self.assertFalse(settings.get_method_profile(out["profile"])["valid"])
			self.assertEqual(settings.get_method_profile(out["profile"])["verification_status"], settings.VERIFICATION_PENDING)
		finally:
			self._unpin_plan_item(item)

	def test_withdrawing_the_mark_does_not_delete_the_fixture_warning(self):
		"""'Fixture-verified — not production law' warns that a row is test
		data. Withdrawing a valid mark must put that warning back, not collapse
		it into an ordinary unmarked rule."""
		out = self._register_method("2017-07-01", "2017-12-31", verification_status=settings.VERIFICATION_FIXTURE)
		self.assertEqual(settings.get_method_profile(out["profile"])["verification_status"], settings.VERIFICATION_FIXTURE)
		settings.set_version_validity(doctype=settings.METHOD_PROFILE, name=out["profile"], valid=True)
		self.assertTrue(settings.get_method_profile(out["profile"])["valid"])
		settings.set_version_validity(doctype=settings.METHOD_PROFILE, name=out["profile"], valid=False)
		self.assertEqual(settings.get_method_profile(out["profile"])["verification_status"], settings.VERIFICATION_FIXTURE)

	def test_a_setting_with_a_real_source_check_does_not_take_the_flag(self):
		"""A reference rule and a calendar have the Check sources screen and its
		evidence trail — a real check, not a label implying one — so the flag
		would be a second, weaker way to make the same claim."""
		with self.assertRaises(ConfigurationError) as caught:
			settings.set_version_validity(doctype="Regulatory Reference", name="whatever", valid=True)
		self.assertEqual(self.code(caught), "CFG_PROFILE_INVALID")

	# --- schedule profiles -----------------------------------------------

	def test_a_schedule_nobody_uses_and_that_has_not_started_is_corrected_in_place(self):
		"""The same rule as a method rule, because there is one rule: an unused,
		not-yet-effective schedule is unfinished configuration and is corrected
		in place; it freezes once a plan pins it or it takes effect."""
		out = settings.register_schedule_profile_version(
			procurement_method="Open Tender",
			procurement_category="Goods",
			profile_name="KT Test — correctable",
			effective_from="2090-07-01",
			effective_until="2090-12-31",
			milestones=_milestones(),
			fixture_namespace=NS,
		)
		before_count = len(frappe.get_all(settings.SCHEDULE_PROFILE, filters={"fixture_namespace": NS}))
		version = settings.get_schedule_profile(out["profile"])
		self.assertTrue(version["can_edit"])

		settings.update_schedule_profile(
			profile=out["profile"],
			profile_name="KT Test — corrected",
			effective_from="2090-08-01",
			effective_until="2090-12-31",
			milestones=_milestones(bid_opening={"default_days": 28}, award_approval={"default_days": 9}),
			estimated_delivery_period_default_days=45,
		)
		corrected = settings.get_schedule_profile(out["profile"])
		self.assertEqual(corrected["version_number"], version["version_number"], "a correction is not a new version")
		self.assertEqual(corrected["profile_name"], "KT Test — corrected")
		self.assertEqual(corrected["effective_from"], "2090-08-01")
		self.assertEqual(corrected["estimated_delivery_period_default_days"], 45)
		# Every milestone row is rewritten, not just the first one that changed.
		self.assertEqual(corrected["periods"]["tendering_period_days"]["default_days"], 28)
		self.assertEqual(corrected["periods"]["award_approval_buffer_days"]["default_days"], 9)
		self.assertEqual({m["milestone"] for m in corrected["milestones"]}, set(settings.MILESTONES))
		self.assertEqual(before_count, len(frappe.get_all(settings.SCHEDULE_PROFILE, filters={"fixture_namespace": NS})))
		self.assertTrue(
			frappe.db.exists("Audit Event", {"document_type": settings.SCHEDULE_PROFILE, "document_name": out["profile"], "action": "update_schedule_profile"})
		)
		# Held to the same standard as registering one.
		with self.assertRaises(ConfigurationError) as caught:
			settings.update_schedule_profile(
				profile=out["profile"],
				profile_name="KT Test — corrected",
				effective_from="2090-08-01",
				milestones=_milestones(bid_opening={"default_days": 1, "minimum_days": 21}),
			)
		self.assertEqual(self.code(caught), "CFG_PROFILE_INVALID")

	def test_a_schedule_freezes_once_it_takes_effect_or_once_a_plan_uses_it(self):
		in_force = settings.register_schedule_profile_version(
			procurement_method="Open Tender",
			procurement_category="Works",
			profile_name="KT Test — in force",
			effective_from="2019-07-01",
			effective_until="2019-12-31",
			milestones=_milestones(),
			fixture_namespace=NS,
		)
		read = settings.get_schedule_profile(in_force["profile"])
		self.assertFalse(read["can_edit"])
		self.assertIn("already taken effect", read["edit_blocked_reason"])
		with self.assertRaises(ConfigurationError) as caught:
			settings.update_schedule_profile(
				profile=in_force["profile"], profile_name="x", effective_from="2019-07-01", milestones=_milestones()
			)
		self.assertEqual(self.code(caught), "CFG_CATALOGUE_IN_USE")
		doc = frappe.get_doc(settings.SCHEDULE_PROFILE, in_force["profile"])
		doc.provision = "changed"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

		future = settings.register_schedule_profile_version(
			procurement_method="Open Tender",
			procurement_category="Services",
			profile_name="KT Test — pinned",
			effective_from="2089-07-01",
			effective_until="2089-12-31",
			milestones=_milestones(),
			fixture_namespace=NS,
		)
		self.assertTrue(settings.get_schedule_profile(future["profile"])["can_edit"])
		item = self._pin_plan_item(future["profile"], "schedule_profile_version")
		try:
			blocked = settings.get_schedule_profile(future["profile"])
			self.assertFalse(blocked["can_edit"])
			self.assertIn("plan already uses this schedule", blocked["edit_blocked_reason"])
		finally:
			self._unpin_plan_item(item)


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
		# A throwaway row naming the source is enough to prove the guard reads
		# real usage, not a flag on the source itself — no other Budget Line
		# fields are required for `frappe.db.exists` to see the row. Budget
		# records are command-only (AUD-XC-006), so the fixture row is written
		# under the maintenance window.
		line = fixture_insert(
			frappe.get_doc({"doctype": "Procurement Budget Line Version", "funding_source": referenced}),
			ignore_mandatory=True,
		)
		self.addCleanup(lambda: purge_doc("Procurement Budget Line Version", line.name))

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
