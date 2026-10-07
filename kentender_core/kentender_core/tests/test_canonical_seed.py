# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`kentender_core.seeds.canonical` — the canonical-world seed (KT-STD-001 §8
+ SEED-001, two-year seed world): selection of non-canonical rows, the two
year ladders, idempotency of a rerun and the fail-closed validator.

Seed runs persist on this bench, so every test that seeds either repeats the
full world (`_full`, idempotent) or, like `TestTwoYearLadders`, ends with it."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import calendar, canonical
from kentender_core.services.command_write_guard import fixture_insert
from kentender_core.services.command_write_guard import purge_doc


def _full(**kwargs):
	"""The full canonical world, as `make seed-canonical` builds it; on a site
	that already holds it, an idempotent repeat."""
	frappe.set_user("Administrator")
	return canonical.run(**{"reset": False, "validate": False, "force": True, "commit": False, **kwargs})


class TestCanonicalSelection(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self._cleanup: list[tuple[str, str]] = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)

	def test_the_two_year_ladders_are_ordered_and_closed(self):
		self.assertEqual(
			canonical.CURRENT_STAGES,
			("annual_plan", "requisitions", "tenders", "bid_submission", "bid_opening", "bid_evaluation", "award"),
		)
		self.assertEqual(canonical.NEXT_STAGES, ("none", "budget", "needs", "departmental_plans", "annual_plan"))
		self.assertEqual(canonical.resolve_years(), ("award", "annual_plan"))  # the plain seed: the full world (plan D6)
		self.assertEqual(canonical.resolve_years(current="requisitions", next_year="budget"), ("requisitions", "budget"))
		with self.assertRaises(frappe.ValidationError):
			canonical.resolve_years(current="tender")
		# the prepared year never goes past an approved Annual Plan
		with self.assertRaises(frappe.ValidationError):
			canonical.resolve_years(next_year="requisitions")

	def test_the_retired_through_maps_onto_the_two_years(self):
		"""THROUGH stays one release as an alias: up to `planning` it moves only
		the prepared year (the executed year always has its Active plan); a
		later stage moves the executed year with the prepared year complete."""
		self.assertEqual(canonical.resolve_years(through="site"), ("annual_plan", "none"))
		self.assertEqual(canonical.resolve_years(through="budget"), ("annual_plan", "budget"))
		self.assertEqual(canonical.resolve_years(through="planning"), ("annual_plan", "annual_plan"))
		self.assertEqual(canonical.resolve_years(through="tenders"), ("tenders", "annual_plan"))
		with self.assertRaises(frappe.ValidationError):
			canonical.resolve_years(through="tender")

	def test_the_world_is_read_as_at_18_june_2027_with_year_1_fifty_two_weeks_earlier(self):
		self.assertEqual(calendar.AS_AT, "2027-06-18 10:00:00")
		self.assertEqual((calendar.YEAR1.fiscal_year, calendar.YEAR2.fiscal_year), ("2026-2027", "2027-2028"))
		# 364 days keeps each weekday (Mon 7 Dec 2026 -> Mon 8 Dec 2025)
		self.assertEqual(calendar.YEAR1.at("2026-12-07 10:00:00"), "2025-12-08 10:00:00")
		self.assertEqual(calendar.YEAR1.at("2026-11-30"), "2025-12-01")
		self.assertEqual(calendar.YEAR2.at("2026-12-07 10:00:00"), "2026-12-07 10:00:00")

	def test_register_actor_and_real_person_are_never_selected(self):
		plan = canonical.collect_non_canonical()
		for email in canonical.REGISTER_USERS:
			self.assertNotIn(email, plan.get("User", []))
		# A non-fixture domain is never a seed's to delete, whatever its name.
		self.assertTrue(all(canonical._fixture_email(u) for u in plan.get("User", [])))

	def test_reserved_placeholder_domains_are_fixture_emails_and_real_domains_are_not(self):
		"""Stray hand-made test accounts land on example.com/.org/.net (RFC 2606),
		which the seed once missed (52180618); a real person's domain, or one that
		merely contains a fixture domain's name, must never match."""
		for email in ("test@example.com", "qa@example.org", "x@example.net", "a@moh.example.test"):
			self.assertTrue(canonical._fixture_email(email), email)
		for email in ("person@gmail.com", "x@notexample.com", "x@example.com.au", "x@sub.example.com", "x@moh.go.ke"):
			self.assertFalse(canonical._fixture_email(email), email)

	def test_reset_removes_a_fiscal_year_only_unreferenced_by_this_same_clear(self):
		"""Regression: the fiscal-year removal list must be recomputed after
		the other deletions in `clear_non_canonical()`, not read from the
		pre-clear snapshot — a year referenced only by a stray Procurement
		Budget only becomes deletable once that budget is gone."""
		year = 2500 + int(uuid4().hex[:2], 16)
		fy = f"{year}-{year + 1}"
		frappe.get_doc(
			{"doctype": "Fiscal Year", "year": fy, "year_start_date": f"{year}-07-01", "year_end_date": f"{year + 1}-06-30"}
		).insert(ignore_permissions=True)
		self._cleanup.append(("Fiscal Year", fy))
		budget = fixture_insert(frappe.get_doc(
			{"doctype": "Procurement Budget", "generated_reference": f"STRAY-{uuid4().hex[:6]}", "fiscal_year": fy, "currency": "KES"}
		))
		self._cleanup.append(("Procurement Budget", budget.name))

		self.assertTrue(canonical._fiscal_year_referenced(fy))
		canonical.clear_non_canonical()
		self.assertFalse(frappe.db.exists("Procurement Budget", budget.name))
		self.assertFalse(frappe.db.exists("Fiscal Year", fy), "the year must be removed once its only reference is gone")

	def test_dry_run_selects_an_isolation_fiscal_year_without_deleting_it(self):
		year = 2400 + int(uuid4().hex[:2], 16)  # far outside any real or test year
		fy = f"{year}-{year + 1}"
		frappe.get_doc(
			{"doctype": "Fiscal Year", "year": fy, "year_start_date": f"{year}-07-01", "year_end_date": f"{year + 1}-06-30"}
		).insert(ignore_permissions=True)
		self._cleanup.append(("Fiscal Year", fy))

		report = canonical.dry_run()
		self.assertIn(fy, report["would_remove"].get("Fiscal Year", []))
		self.assertTrue(frappe.db.exists("Fiscal Year", fy), "dry_run must delete nothing")

	def test_fixture_user_outside_the_register_is_selected(self):
		email = f"canonical.stray.{uuid4().hex[:6]}@example.test"
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": "Stray", "send_welcome_email": 0, "user_type": "System User"}
		).insert(ignore_permissions=True)
		self._cleanup.append(("User", email))
		self.assertIn(email, canonical.collect_non_canonical().get("User", []))

	def test_a_seeded_assignment_the_seed_no_longer_declares_is_removed_with_its_role(self):
		"""A grant stamped with the site stage's namespace that `site_setup.ASSIGNMENTS`
		no longer lists (KT-STD-001 v1.13 dropped the Evaluation committee's
		Departmental Author grants) survives a plain reseed otherwise, since
		the namespace marks it canonical. The clear removes it and takes the
		Frappe role it projected with it."""
		from kentender_core.seeds import site_setup
		from kentender_core.services import responsibility_administration as administration

		user = "grace.wanjiku@moh.example.test"
		self.assertNotIn("Auditor", frappe.get_roles(user))
		row = administration.grant(user=user, business_role="Auditor", fixture_namespace=site_setup.FIXTURE_TAG, actor="Administrator")
		name = row.get("assignment") or row.get("name")
		def cleanup():
			if frappe.db.exists("User Responsibility Assignment", name):
				frappe.delete_doc("User Responsibility Assignment", name, force=1, ignore_permissions=True)
			administration._sync_projection(user)
			frappe.db.commit()

		self.addCleanup(cleanup)
		self.assertIn("Auditor", frappe.get_roles(user))
		self.assertIn(name, canonical.collect_non_canonical().get("User Responsibility Assignment", []))
		canonical.clear_non_canonical()
		self.assertFalse(frappe.db.exists("User Responsibility Assignment", name))
		self.assertNotIn("Auditor", frappe.get_roles(user))

	def test_a_stray_departmental_need_outside_the_namespace_is_a_stray(self):
		need = frappe.get_doc({"doctype": "Departmental Need", "need_reference": f"STRAY-NDS-{uuid4().hex[:6]}", "current_state": "Draft"})
		# Only the namespace stamp matters to selection; a minimal insert
		# would fail on this doctype's own required fields, so bypass them —
		# `collect_non_canonical()` reads the raw db row, not the full doc.
		need.flags.ignore_mandatory = True
		need.insert(ignore_permissions=True)
		try:
			self.assertIn(need.name, canonical.collect_non_canonical().get("Departmental Need", []))
		finally:
			# `on_trash` refuses every delete on this doctype by design (a
			# Need is "retained and cannot be deleted") — the seed's own
			# purge goes raw for exactly this reason; mirror it here.
			frappe.db.delete("Departmental Need", {"name": need.name})

	def test_reset_removes_a_stray_tender_and_keeps_the_canonical_one(self):
		"""Found 26 Sep 2026: nothing in the clear looked at Tenders, so a
		Tender left by an interrupted browser run survived every reseed."""
		from kentender_procurement.tenders.seeds import clear as tender_clear

		tag = uuid4().hex[:8]
		tender = f"TDR-CS-{tag}"
		# Raw insert: selection reads only the Requisition link, and the
		# Tender controller refuses ordinary inserts and deletes by design.
		frappe.get_doc({"doctype": "Tender", "name": tender, "tender_reference": f"CS-{tag}", "requisition": f"PRQ-CS-{tag}"}).db_insert()
		self.addCleanup(frappe.db.delete, "Tender", {"name": tender})
		kept = sorted(tender_clear.canonical_tenders())

		plan = canonical.collect_non_canonical()
		self.assertIn(tender, plan.get("Tender", []))
		self.assertFalse(set(kept) & set(plan.get("Tender", [])), "a canonical Tender was selected")
		canonical.clear_non_canonical()
		self.assertFalse(frappe.db.exists("Tender", tender))
		self.assertEqual(sorted(tender_clear.canonical_tenders()), kept)

	def test_reset_removes_a_stray_strategic_plan_and_keeps_the_canonical_one(self):
		"""Found 26 Sep 2026: nothing in the clear looked at Strategy, so a
		plan left by a test run survived every reseed (STR-CHG-001 v1.8
		§14.3: "There is no second seeded plan")."""
		tag = uuid4().hex[:8]
		plan = f"SP-CS-{tag}"
		frappe.get_doc({"doctype": "Strategic Plan", "name": plan, "plan_id": f"CS-SP-{tag}", "title": f"Stray plan {tag}"}).db_insert()
		self.addCleanup(frappe.db.delete, "Strategic Plan", {"name": plan})
		kept = frappe.get_all("Strategic Plan", filters={"fixture_namespace": canonical.STRATEGY_NS}, pluck="name")

		plan_rows = canonical.collect_non_canonical().get("Strategic Plan", [])
		self.assertIn(plan, plan_rows)
		self.assertFalse(set(kept) & set(plan_rows), "a canonical plan was selected")
		canonical.clear_non_canonical()
		self.assertFalse(frappe.db.exists("Strategic Plan", plan))
		self.assertEqual(frappe.get_all("Strategic Plan", filters={"fixture_namespace": canonical.STRATEGY_NS}, pluck="name"), kept)

	def test_reset_removes_planning_dispositions_whose_need_is_gone(self):
		"""Found 26 Sep 2026: 11 Need Planning Disposition Projection rows
		pointed at Needs that no longer existed — the reseed's Need delete
		never covered that table."""
		tag = uuid4().hex[:8]
		row = f"NPDP-CS-{tag}"
		frappe.get_doc(
			{"doctype": "Need Planning Disposition Projection", "name": row, "departmental_need": f"NDS-GONE-{tag}", "disposition_key": row}
		).db_insert()
		self.addCleanup(frappe.db.delete, "Need Planning Disposition Projection", {"name": row})
		self.assertIn(row, canonical.collect_non_canonical().get("Need Planning Disposition Projection", []))
		canonical.clear_non_canonical()
		self.assertFalse(frappe.db.exists("Need Planning Disposition Projection", row))

	def test_a_planning_position_whose_need_is_gone_is_a_stray(self):
		"""Owner decision 26 Sep 2026 — Planning's position for an accepted
		Need is written unstamped, like the disposition above, and is named
		after the Need: left behind, a reused Need reference would inherit
		it. Selection only — the clear itself is the loop proved above."""
		tag = uuid4().hex[:8]
		need = f"NDS-GONE-{tag}"
		frappe.get_doc(
			{"doctype": "Need Planning Intake Projection", "name": need, "departmental_need": need, "position": "Update required"}
		).db_insert()
		self.addCleanup(frappe.db.delete, "Need Planning Intake Projection", {"name": need})
		self.assertIn(need, canonical.collect_non_canonical().get("Need Planning Intake Projection", []))

	def test_reset_removes_child_rows_and_files_whose_record_is_gone(self):
		"""Found 26 Sep 2026: about 50,000 child-table rows and 1,734 files
		on the dev site belonged to records that no longer existed — module
		clean-ups that delete a record directly leave both behind, and no
		screen can ever reach them again."""
		tag = uuid4().hex[:8]
		row = f"CS-{tag}"
		frappe.get_doc(
			{
				"doctype": "Requisition Contributing Unit",
				"name": row,
				"parenttype": "Procurement Requisition",
				"parent": f"PRQ-GONE-{tag}",
				"parentfield": "contributing_org_units",
			}
		).db_insert()
		self.addCleanup(frappe.db.delete, "Requisition Contributing Unit", {"name": row})
		orphan_file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"canonical-orphan-{tag}.txt",
				"content": tag.encode(),
				"attached_to_doctype": "Tender Document",
				"attached_to_name": f"TDOC-GONE-{tag}",
				"is_private": 1,
			}
		).insert(ignore_permissions=True)
		self._cleanup.append(("File", orphan_file.name))

		plan = canonical.collect_non_canonical()
		self.assertIn(row, plan.get("Requisition Contributing Unit", []))
		self.assertIn(orphan_file.name, plan.get("File", []))
		canonical.clear_non_canonical()
		self.assertFalse(frappe.db.exists("Requisition Contributing Unit", row))
		self.assertFalse(frappe.db.exists("File", orphan_file.name))


class TestEvaluationPeople(IntegrationTestCase):
	def test_the_evaluation_people_hold_what_kt_std_v1_13_registers(self):
		"""KT-STD-001 v1.13 §8.3: the committee holds no standing responsibility
		(its authority is the appointment), and Esther Njeri holds Evaluation
		Technical Support, not Daniel Otieno's Technical Operator."""
		_full(reset=True)
		held = lambda local: frappe.get_all("User Responsibility Assignment", filters={"user": f"{local}@moh.example.test", "status": "Enabled"},  # noqa: E731
			pluck="business_role")
		for local in ("grace.wambui", "peter.mugo", "ruth.achieng"):
			self.assertEqual(held(local), [], local)
			self.assertTrue(frappe.db.exists("User", f"{local}@moh.example.test"))
		self.assertEqual(held("esther.njeri"), ["Evaluation Technical Support"])
		self.assertNotIn("Technical Operator", frappe.get_roles("esther.njeri@moh.example.test"))


class TestFixturePasswords(IntegrationTestCase):
	def test_the_register_actors_can_log_in_after_a_seed_run_without_developer_mode(self):
		"""Found 26 Sep 2026: on a new site without developer_mode the
		canonical seed (run with force) created the actors with no password,
		so nobody could log in until an administrator set one."""
		from frappe.utils.password import check_password, update_password

		from kentender_core.seeds.constants import TEST_PASSWORD

		frappe.set_user("Administrator")
		email = "esther.muthoni@moh.example.test"
		developer_mode = frappe.conf.get("developer_mode")
		self.addCleanup(update_password, email, TEST_PASSWORD)
		self.addCleanup(setattr, frappe.conf, "developer_mode", developer_mode)
		update_password(email, f"Not-the-fixture-{uuid4().hex[:8]}!")
		frappe.conf.developer_mode = 0

		_full()
		self.assertEqual(check_password(email, TEST_PASSWORD), email)


	def test_the_technical_operator_release_operator_and_public_observer_are_seeded(self):
		"""KT-STD-001 v1.11 §8.3 (seeded at the Project Owner's instruction of
		30 Sep 2026): Daniel Otieno is a technical reader holding Technical
		Operator; Jane Wanjiku is a Website User with no supplier link. Both sign
		in with the shared fixture password."""
		from frappe.utils.password import check_password

		from kentender_core.seeds.constants import TEST_PASSWORD

		_full()
		daniel = "daniel.otieno@moh.example.test"
		self.assertIn("System Manager", frappe.get_roles(daniel))
		self.assertTrue(frappe.db.exists("User Responsibility Assignment", {"user": daniel, "business_role": "Technical Operator", "status": "Enabled"}))
		jane = "jane.wanjiku@observer.example"
		self.assertEqual(frappe.db.get_value("User", jane, "user_type"), "Website User")
		self.assertFalse(frappe.db.exists("User Responsibility Assignment", {"user": jane}))
		for email in (daniel, jane):
			self.assertEqual(check_password(email, TEST_PASSWORD), email)
		self.assertIn(daniel, canonical.REGISTER_USERS)
		# KT-STD-001 v1.12 §8.3 — the release operator: a Desk user, not a technical reader
		nadia = "nadia.kamau@moh.example.test"
		self.assertTrue(frappe.db.exists("User Responsibility Assignment", {"user": nadia, "business_role": "Release Operator", "status": "Enabled"}))
		self.assertNotIn("System Manager", frappe.get_roles(nadia))
		self.assertEqual(check_password(nadia, TEST_PASSWORD), nadia)
		self.assertIn(nadia, canonical.REGISTER_USERS)


class TestCanonicalSeedRun(IntegrationTestCase):
	"""Runs the real seed on the test site (idempotent on the full world;
	`reset=False` keeps this to the seed itself)."""

	def test_a_second_full_run_changes_nothing(self):
		first = _full(validate=True)
		self.assertTrue(first["ok"])
		counts = {
			dt: frappe.db.count(dt)
			for dt in (
				"Procurement Budget", "Procurement Budget Version", "Organisation Unit", "User Responsibility Assignment", "Departmental Need",
				"Annual Plan", "Annual Plan Item", "Procurement Requisition", "Tender", "Bid Submission Version", "Bid Opening Case",
				"Evaluation Case", "Award Case",
			)
		}
		second = _full(validate=True)
		self.assertTrue(second["ok"])
		for year in ("year1", "year2"):
			self.assertFalse(second["seeded"]["budget"]["years"][year]["created"], year)
			self.assertTrue(second["seeded"]["planning"]["years"][year]["idempotent"], year)
		for stage in ("requisitions", "bid_submission", "bid_opening", "bid_evaluation", "award"):
			self.assertTrue(second["seeded"][stage]["idempotent"], stage)
		for dt, count in counts.items():
			self.assertEqual(frappe.db.count(dt), count, dt)

	def test_procurement_rules_are_fixture_verified(self):
		"""Reported bug: a shallow reseed left every Procurement Rule at
		`Production verification pending` — unusable — because the upgrade to
		`Fixture-verified — not production law` happened only inside the
		Planning stage's own seed. It is the site stage's own concern."""
		self.assertTrue(_full(validate=True)["ok"])
		from kentender_core.services import procurement_settings as settings

		for doctype in (settings.METHOD_PROFILE, "Regulatory Reference"):
			statuses = set(frappe.get_all(doctype, filters={"status": "Active"}, pluck="verification_status"))
			self.assertTrue(statuses, f"expected at least one Active {doctype} row")
			self.assertEqual(statuses, {settings.VERIFICATION_FIXTURE}, f"{doctype} rows must be fixture-verified, found {statuses}")

	def test_validate_fails_closed_on_a_stray_budget(self):
		"""Each seeded year already has its one budget (one per Fiscal Year),
		so the stray sits on an isolation year of its own."""
		from kentender_core.services import site_configuration as configuration

		_full()
		year = configuration._fy_name(2099)
		created_year = not frappe.db.exists("Fiscal Year", year)
		if created_year:
			configuration.add_fiscal_year(start_year=2099)
		stray = fixture_insert(frappe.get_doc(
			{"doctype": "Procurement Budget", "generated_reference": f"STRAY-{uuid4().hex[:6]}", "fiscal_year": year, "currency": "KES"}
		))
		try:
			with self.assertRaisesRegex(frappe.ValidationError, "the canonical budgets"):
				canonical.validate()
		finally:
			purge_doc("Procurement Budget", stray.name)
			if created_year:
				frappe.delete_doc("Fiscal Year", year, force=1, ignore_permissions=True)

	def test_the_executed_year_carries_the_chain_and_the_prepared_year_only_planning(self):
		"""Plan D1/D8: FY 2026/27 is carried out against its Active plan (the
		canonical Tender spends it); FY 2027/28 is prepared up to its Active
		plan and nothing is bought against it; the live pages read 18 Jun 2027."""
		from kentender_core.services import test_clock
		from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import year_plan

		_full()
		self.assertTrue(year_plan("year1").active_version and year_plan("year2").active_version)
		requisition = frappe.get_all("Procurement Requisition", fields=["plan_item_id"], limit=1)[0]
		plan = frappe.db.get_value("Plan Item", requisition.plan_item_id, "annual_plan")
		self.assertEqual(frappe.db.get_value("Annual Plan", plan, "fiscal_year"), calendar.YEAR1.fiscal_year)
		y2_items = frappe.get_all("Plan Item", filters={"annual_plan": year_plan("year2").name}, pluck="name")
		self.assertFalse(frappe.db.exists("Procurement Requisition", {"plan_item_id": ("in", y2_items or ("",))}))
		if frappe.conf.get("kt_bds_simulation_environment"):
			self.assertEqual(str(test_clock.current_instant())[:19], calendar.AS_AT)


class TestTwoYearLadders(IntegrationTestCase):
	"""The two controls move independently, and a run asking for less of a
	year than the site holds rebuilds by itself. The steps run in name order
	(each stays inside the runner's five-minute limit per test) and the last
	one leaves the full world."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_1_a_lower_stage_on_both_ladders_rebuilds(self):
		from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import year_plan

		out = canonical.run(current="annual_plan", next_year="budget", force=True, commit=True)
		self.assertTrue(out.get("rebuilt_after_partial_world"))
		self.assertTrue(year_plan("year1").active_version)
		self.assertTrue(frappe.db.exists("Procurement Budget", {"fiscal_year": calendar.YEAR2.fiscal_year}))
		self.assertFalse(frappe.db.exists("Departmental Need", {"financial_year": calendar.YEAR2.fiscal_year}))
		self.assertEqual(frappe.db.count("Procurement Requisition"), 0)

	def test_2_a_higher_stage_builds_on_what_is_there(self):
		from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import year_plan

		out = canonical.run(current="requisitions", next_year="departmental_plans", force=True, commit=True)
		self.assertFalse(out.get("rebuilt_after_partial_world"))
		self.assertGreater(frappe.db.count("Procurement Requisition"), 0)
		self.assertEqual(frappe.db.count("Tender"), 0)
		self.assertTrue(year_plan("year2") and not year_plan("year2").active_version)

	def test_3_the_bid_stage_tells_every_tender_with_its_bids(self):
		out = canonical.run(current="bid_submission", next_year="annual_plan", force=True, commit=True)
		self.assertFalse(out.get("rebuilt_after_partial_world"))
		self.assertGreater(frappe.db.count("Bid Workspace", {"status": "Submitted"}), 4)

	def test_4_the_full_world_again(self):
		from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import year_plan

		out = canonical.run(force=True, commit=True)
		self.assertTrue(out["ok"])
		self.assertTrue(year_plan("year2").active_version)


class TestDemoProfilesReleased(IntegrationTestCase):
	"""A reseed after a walkthrough: a loaded Bid Opening or Award demo
	profile leaves the site-wide test clock on its moment (12 Jun 2027 …);
	a reseed clears it first, then leaves the canonical world's own moment,
	18 Jun 2027 10:00 (two-year seed world plan D1)."""

	def test_a_reseed_releases_a_loaded_opening_profile_and_the_test_clock(self):
		from kentender_core.services import test_clock
		from kentender_procurement.bid_opening.seeds import profiles as bop_profiles

		frappe.set_user("Administrator")
		if not test_clock.set_instant("2027-06-12 11:00:05"):
			self.skipTest("not a test environment: nothing keeps a test clock")
		frappe.db.set_default(bop_profiles.LOADED_KEY, "BOP-DEMO-READY")
		try:
			released = canonical.release_demo_profiles()
			self.assertFalse(test_clock.current_instant())
			self.assertEqual(bop_profiles.loaded_profile(), "")
			self.assertEqual(released["bid_opening"]["loaded"], "BOP-DEMO-READY")
		finally:
			canonical.set_as_at()  # the canonical world's own moment
			frappe.db.set_default(bop_profiles.LOADED_KEY, "")

	def test_a_reseed_clears_an_award_profile_clock(self):
		"""Award's profiles keep no loaded marker, only the clock."""
		from kentender_core.services import test_clock

		frappe.set_user("Administrator")
		if not test_clock.set_instant("2027-06-17 10:00:00"):
			self.skipTest("not a test environment: nothing keeps a test clock")
		try:
			canonical.release_demo_profiles()
			self.assertFalse(test_clock.current_instant())
		finally:
			canonical.set_as_at()


class TestCanonicalReservationNamespace(IntegrationTestCase):
	"""REQ-CHG-001 v1.6 — reservation begins at Procurement Requisition, not a
	canonical stage yet. A row stamped `REQUISITIONS_NS` is canonical evidence
	of an authorised Requisition; anything else on the canonical budget is a
	stray the seed's own reservation checks must still catch."""

	def setUp(self):
		_full()
		from kentender_budget.seeds.kentender_mvp_v1_portfolio import canonical_budget

		self.budget = canonical_budget()
		self.budget_version = frappe.db.get_value(
			"Procurement Budget Version", {"budget": self.budget, "status": "Active"}, "name"
		)
		self.budget_line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": self.budget_version}, "budget_line")
		self._reservations: list[str] = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in self._reservations:
			if frappe.db.exists("Funding Reservation", name):
				purge_doc("Funding Reservation", name)

	def _reserve(self, *, fixture_namespace: str, plan_source_allocation: str) -> str:
		doc = fixture_insert(frappe.get_doc(
			{
				"doctype": "Funding Reservation",
				"generated_reference": f"RSV-TEST-{uuid4().hex[:8]}",
				"budget": self.budget,
				"budget_version_at_creation": self.budget_version,
				"budget_line": self.budget_line,
				"status": "Active",
				"plan_item": "TEST-PLAN-ITEM",
				"plan_source_allocation": plan_source_allocation,
				"original_amount": 1,
				"remaining_amount": 1,
				"currency": "KES",
				"correlation_id": plan_source_allocation,
				"fixture_namespace": fixture_namespace,
			}
		))
		self._reservations.append(doc.name)
		return doc.name

	def test_a_reservation_stamped_requisitions_ns_is_not_a_stray(self):
		self._reserve(fixture_namespace=canonical.REQUISITIONS_NS, plan_source_allocation=f"TEST-PSA-{uuid4().hex[:8]}")
		plan = canonical.collect_non_canonical()
		self.assertNotIn(self._reservations[0], plan.get("Funding Reservation", []))
		canonical.validate()  # must not raise

	def test_a_reservation_outside_requisitions_ns_is_a_stray(self):
		self._reserve(fixture_namespace="", plan_source_allocation=f"TEST-PSA-{uuid4().hex[:8]}")
		plan = canonical.collect_non_canonical()
		self.assertIn(self._reservations[0], plan.get("Funding Reservation", []))
		with self.assertRaises(frappe.ValidationError):
			canonical.validate()


class TestFreshSite(IntegrationTestCase):
	"""Found 4 Oct 2026 on a new server: the seed ran only where the dev site
	already had everything set by hand. One allowed run must be enough."""

	def test_the_run_prepares_what_the_stages_need(self):
		from unittest import mock

		with mock.patch("kentender_procurement.std_templates.services.installer.ensure_site_release") as ensure, \
				mock.patch("kentender_procurement.std_templates.services.binding.require"), \
				mock.patch("frappe.installer.update_site_config") as update, mock.patch.dict(frappe.conf, {"kt_bds_simulation_environment": 0}):
			out = canonical.prepare_site(current="tenders")
			ensure.assert_called_once()  # the tender template, before requisitions
			update.assert_not_called()  # no bid stage, no simulated services
			self.assertFalse(out["simulation_switched_on"])
			out = canonical.prepare_site(current="bid_opening")
			update.assert_called_once_with("kt_bds_simulation_environment", 1)
			self.assertTrue(out["simulation_switched_on"])
			self.assertEqual(frappe.conf.get("kt_bds_simulation_environment"), 1)
		with mock.patch("kentender_procurement.std_templates.services.installer.ensure_site_release") as ensure:
			canonical.prepare_site(current="annual_plan")
			ensure.assert_not_called()

	def test_an_unusable_template_stops_the_run_at_once_and_says_why(self):
		"""Found 4 Oct 2026: with the wrong wkhtmltopdf build the run went on to
		fail at the requisition with "Youth is not supported"."""
		from unittest import mock

		from kentender_procurement.std_templates.compiler.errors import STDTemplateError

		renderer = STDTemplateError("STD_RENDERER_UNSUPPORTED", detail={"health": {"document": {
			"engine": "wkhtmltopdf", "found_version": "wkhtmltopdf 0.12.6", "expected_version": "wkhtmltopdf 0.12.6.1 (with patched qt)"}}})
		with mock.patch("kentender_procurement.std_templates.services.installer.ensure_site_release", return_value="stdr-x"), \
				mock.patch("kentender_procurement.std_templates.services.binding.require", side_effect=renderer):
			with self.assertRaises(frappe.ValidationError) as ctx:
				canonical.prepare_site(current="requisitions")
		self.assertIn("wkhtmltopdf 0.12.6 found; wkhtmltopdf 0.12.6.1 (with patched qt) needed", str(ctx.exception))

	def test_allow_canonical_seed_alone_lets_every_stage_run(self):
		"""Each module seed keeps its own demo-data guard; an allowed run
		(developer_mode, allow_canonical_seed or force) satisfies them all."""
		from unittest import mock

		frappe.set_user("Administrator")
		# the test runner sets in_test itself, which the module guards accept; take it away
		with mock.patch.dict(frappe.conf, {"developer_mode": 0, "allow_tests": 0, "allow_canonical_seed": 1}), mock.patch.dict(frappe.flags, {"in_test": False}):
			out = canonical.run(reset=False, validate=False, force=False, commit=False)
		self.assertTrue(out["ok"])
		self.assertIn("planning", out["seeded"])


class TestPartialBidWorld(IntegrationTestCase):
	"""Found 4 Oct 2026: submitting a bid commits at once (the attempt must
	survive a crash), so a run that failed after the bids left a canonical
	Tender without its lifecycle, and the next run stopped asking for
	REBUILD=True. The run now rebuilds by itself, once."""

	def test_a_tender_left_without_its_bid_lifecycle_is_rebuilt_automatically(self):
		from unittest import mock

		from kentender_procurement.bid_submission.seeds.kentender_mvp_v1 import CanonicalTenderIncomplete

		calls = []

		def fake_run_seed(*, current, next_year, **_kwargs):
			calls.append(current)
			if len(calls) == 1:
				raise CanonicalTenderIncomplete("The canonical Tender TND-X was seeded without the bid lifecycle.")
			return {"ok": True}

		frappe.set_user("Administrator")
		with mock.patch.object(canonical, "seed", side_effect=fake_run_seed), mock.patch.object(canonical, "clear_canonical_modules", return_value={}) as rebuild, \
				mock.patch.object(canonical, "clear_non_canonical", return_value={}), mock.patch("kentender_strategy.services.strategy_reference.reset_reference_series"):
			out = canonical.run(current="award", validate=False, force=True, commit=False)
		self.assertEqual(calls, ["award", "award"])
		rebuild.assert_called_once()
		self.assertTrue(out["rebuilt_after_partial_world"])


class TestPublicTenders(IntegrationTestCase):
	"""Owner, 4 Oct 2026: a demo site needs a Tender anyone can see on
	/tenders. The executed portfolio's Medical-grade tablets Tender is open
	past the as-at instant (deadline 25 Jun 2027), so the full world always
	lists one (OPEN=True, which stopped the canonical Tender before its
	deadline, was retired on 5 Oct 2026)."""

	def test_the_open_portfolio_tender_is_listed_for_anyone(self):
		from kentender_procurement.bid_submission.services import reads

		_full()
		tender = frappe.db.get_value("Tender", {"overall_status": "Published — open", "submission_deadline": (">", calendar.AS_AT)}, "tender_reference")
		self.assertTrue(tender)
		try:
			frappe.set_user("Guest")
			self.assertIn(tender, [r["reference"] for r in reads.get_available_tenders()["rows"]])
		finally:
			frappe.set_user("Administrator")


class TestFieldLaptopsCancellationReview(IntegrationTestCase):
	"""HOME-CHG-001 v0.6 H1/H12 and TPR-CHG-001 v0.17 §5.11: Supply of field
	laptops waits on the Accounting Officer to consider cancellation. That
	work item exists only on the material-addendum route (a quantity change no
	addendum may issue, sent by the Procurement Officer); a Head of
	Procurement recommendation is optional and opens none (found 5 Oct 2026:
	the seed used the recommendation, so Amina had nothing to do)."""

	def test_amina_holds_consider_cancellation_and_brian_waits(self):
		from kentender_core.services.my_work import get_my_work

		_full()
		from kentender_core.seeds import portfolio

		reference = next(r["tender"] for r in portfolio.binding_rows() if r["ref"] == "T9")
		tender = frappe.db.get_value("Tender", {"tender_reference": reference}, ["name", "tender_reference"], as_dict=True) if reference else None
		self.assertTrue(tender, "the field laptops Tender exists")
		task = frappe.db.get_value("Tender Task", {"tender": tender.name, "task_type": "AO cancellation review", "status": "Open"}, ["sender", "creation"], as_dict=True)
		self.assertTrue(task, "an open cancellation review on the field laptops Tender")
		self.assertEqual(task.sender, "brian.wafula@moh.example.test")
		self.assertEqual(str(task.creation)[:19], "2027-06-16 14:00:00")
		try:
			frappe.set_user("amina.hassan@moh.example.test")
			mine = [r["title"] for r in get_my_work()["buckets"].get("assigned", [])]
			frappe.set_user("brian.wafula@moh.example.test")
			waiting = [r["title"] for r in get_my_work()["buckets"].get("waiting", [])]
		finally:
			frappe.set_user("Administrator")
		self.assertIn(f"Consider cancellation of {tender.tender_reference}", mine)
		self.assertIn(f"Waiting for Amina Hassan to consider cancellation of {tender.tender_reference}", waiting)
