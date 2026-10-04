# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`kentender_core.seeds.canonical` — the progressive canonical-world seed
(KT-STD-001 §8 + SEED-001): selection of non-canonical rows, the stage
ladder, idempotency of a rerun and the fail-closed validator."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import canonical


class TestCanonicalSelection(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self._cleanup: list[tuple[str, str]] = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)

	def test_stage_ladder_is_ordered_and_closed(self):
		self.assertEqual(
			canonical.STAGES,
			(
				"site", "strategy", "budget", "needs", "planning", "requisitions", "tenders", "bid_submission", "bid_opening",
				"bid_evaluation", "award",
			),
		)
		with self.assertRaises(frappe.ValidationError):
			canonical._stage_index("tender")

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
		budget = frappe.get_doc(
			{"doctype": "Procurement Budget", "generated_reference": f"STRAY-{uuid4().hex[:6]}", "fiscal_year": fy, "currency": "KES"}
		).insert(ignore_permissions=True)
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
		frappe.set_user("Administrator")
		canonical.run(through="site", reset=True, validate=False, force=True, commit=False)
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

		canonical.run(through="site", reset=False, validate=False, force=True, commit=False)
		self.assertEqual(check_password(email, TEST_PASSWORD), email)


	def test_the_technical_operator_release_operator_and_public_observer_are_seeded(self):
		"""KT-STD-001 v1.11 §8.3 (seeded at the Project Owner's instruction of
		30 Sep 2026): Daniel Otieno is a technical reader holding Technical
		Operator; Jane Wanjiku is a Website User with no supplier link. Both sign
		in with the shared fixture password."""
		from frappe.utils.password import check_password

		from kentender_core.seeds.constants import TEST_PASSWORD

		frappe.set_user("Administrator")
		canonical.run(through="site", reset=False, validate=False, force=True, commit=False)
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
	"""Runs the real seed on the test site (the seed is idempotent and only
	adds canonical rows; `reset=False` keeps this to the seed itself)."""

	def test_seed_through_budget_is_idempotent(self):
		frappe.set_user("Administrator")
		first = canonical.run(through="budget", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(first["ok"])
		budgets = frappe.db.count("Procurement Budget")
		versions = frappe.db.count("Procurement Budget Version")
		plans = frappe.db.count("Strategic Plan", {"fixture_namespace": canonical.STRATEGY_NS})
		units = frappe.db.count("Organisation Unit")
		assignments = frappe.db.count("User Responsibility Assignment")

		second = canonical.run(through="budget", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(second["ok"])
		self.assertFalse(second["seeded"]["budget"]["moh"]["created"])
		self.assertEqual(frappe.db.count("Procurement Budget"), budgets)
		self.assertEqual(frappe.db.count("Procurement Budget Version"), versions)
		self.assertEqual(frappe.db.count("Strategic Plan", {"fixture_namespace": canonical.STRATEGY_NS}), plans)
		self.assertEqual(frappe.db.count("Organisation Unit"), units)
		self.assertEqual(frappe.db.count("User Responsibility Assignment"), assignments)

	def test_seed_through_budget_leaves_procurement_rules_fixture_verified(self):
		"""Reported bug: a shallow reseed (`through="budget"`, well before
		the "planning" stage) left every Procurement Rule permanently at
		`Production verification pending` — unusable — because the upgrade
		to `Fixture-verified — not production law` used to happen only
		inside the Planning stage's own seed. Procurement Rules are
		`site_setup.run()`'s own concern (seeded on every stage, "budget"
		included), so making them usable cannot depend on how far the
		caller happens to go afterward."""
		frappe.set_user("Administrator")
		result = canonical.run(through="budget", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(result["ok"])
		from kentender_core.services import procurement_settings as settings

		for doctype in (settings.METHOD_PROFILE, "Regulatory Reference"):
			statuses = set(frappe.get_all(doctype, filters={"status": "Active"}, pluck="verification_status"))
			self.assertTrue(statuses, f"expected at least one Active {doctype} row")
			self.assertEqual(
				statuses, {settings.VERIFICATION_FIXTURE},
				f"{doctype} rows must be fixture-verified regardless of `through`, found {statuses}",
			)

	def test_validate_fails_closed_on_a_stray_budget(self):
		frappe.set_user("Administrator")
		canonical.run(through="budget", reset=False, validate=True, force=True, commit=False)
		stray = frappe.get_doc(
			{"doctype": "Procurement Budget", "generated_reference": f"STRAY-{uuid4().hex[:6]}", "fiscal_year": "2026-2027", "currency": "KES"}
		).insert(ignore_permissions=True)
		try:
			with self.assertRaises(frappe.ValidationError):
				canonical.validate(through="budget")
		finally:
			frappe.delete_doc("Procurement Budget", stray.name, force=1, ignore_permissions=True)


class TestCanonicalSeedFullChain(IntegrationTestCase):
	"""The full site → strategy → budget → needs → planning → requisitions →
	tenders → bid_submission → bid_opening → bid_evaluation → award chain, on
	the real test site, `reset=False` so this stays scoped
	to the seed's own rows (as `TestCanonicalSeedRun` already does for
	budget)."""

	def test_seed_through_requisitions_is_idempotent(self):
		frappe.set_user("Administrator")
		first = canonical.run(through="requisitions", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(first["ok"])
		counts = {dt: frappe.db.count(dt) for dt in ("Departmental Need", "Annual Plan", "Procurement Requisition")}

		second = canonical.run(through="requisitions", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(second["ok"])
		self.assertTrue(second["seeded"]["requisitions"]["idempotent"])
		for dt, count in counts.items():
			self.assertEqual(frappe.db.count(dt), count, dt)

	def test_seed_through_tenders_is_idempotent(self):
		"""TPR-CHG-001 v0.8 TND-804 (AC-078) — a second `through="tenders"`
		run creates no duplicate Tender and reports idempotent."""
		frappe.set_user("Administrator")
		first = canonical.run(through="tenders", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(first["ok"])
		counts = {dt: frappe.db.count(dt) for dt in ("Procurement Requisition", "Tender", "Tender Addendum", "Tender Clarification", "Tender Submission Handoff")}

		second = canonical.run(through="tenders", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(second["ok"])
		self.assertTrue(second["seeded"]["tenders"]["idempotent"])
		for dt, count in counts.items():
			self.assertEqual(frappe.db.count(dt), count, dt)


	def test_seed_through_award_is_idempotent(self):
		"""The four stages after Tenders (bid, opening, evaluation, award): a
		second `through="award"` run tells nothing again and duplicates
		nothing. Runs only on a test site (their simulated services)."""
		frappe.set_user("Administrator")
		first = canonical.run(through="award", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(first["ok"])
		counts = {dt: frappe.db.count(dt) for dt in ("Tender", "Bid Submission Version", "Bid Opening Case", "Evaluation Case", "Award Case")}

		second = canonical.run(through="award", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(second["ok"])
		for stage in ("bid_submission", "bid_opening", "bid_evaluation", "award"):
			self.assertTrue(second["seeded"][stage]["idempotent"], stage)
		for dt, count in counts.items():
			self.assertEqual(frappe.db.count(dt), count, dt)


class TestDemoProfilesReleased(IntegrationTestCase):
	"""A reseed after a walkthrough: a loaded Bid Opening or Award demo
	profile leaves the site-wide test clock on its moment (12 Jun 2027 …),
	so every module's live pages read that day until something clears it.
	The canonical world has no test clock."""

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
			test_clock.set_instant(None)
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
			test_clock.set_instant(None)


class TestCanonicalReservationNamespace(IntegrationTestCase):
	"""REQ-CHG-001 v1.6 — reservation begins at Procurement Requisition, not a
	canonical stage yet. A row stamped `REQUISITIONS_NS` is canonical evidence
	of an authorised Requisition; anything else on the canonical budget is a
	stray the seed's own reservation checks must still catch."""

	def setUp(self):
		frappe.set_user("Administrator")
		canonical.run(through="budget", reset=False, validate=True, force=True, commit=False)
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
				frappe.delete_doc("Funding Reservation", name, force=1, ignore_permissions=True)

	def _reserve(self, *, fixture_namespace: str, plan_source_allocation: str) -> str:
		doc = frappe.get_doc(
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
		).insert(ignore_permissions=True)
		self._reservations.append(doc.name)
		return doc.name

	def test_a_reservation_stamped_requisitions_ns_is_not_a_stray(self):
		self._reserve(fixture_namespace=canonical.REQUISITIONS_NS, plan_source_allocation=f"TEST-PSA-{uuid4().hex[:8]}")
		plan = canonical.collect_non_canonical()
		self.assertNotIn(self._reservations[0], plan.get("Funding Reservation", []))
		canonical.validate(through="budget")  # must not raise

	def test_a_reservation_outside_requisitions_ns_is_a_stray(self):
		self._reserve(fixture_namespace="", plan_source_allocation=f"TEST-PSA-{uuid4().hex[:8]}")
		plan = canonical.collect_non_canonical()
		self.assertIn(self._reservations[0], plan.get("Funding Reservation", []))
		with self.assertRaises(frappe.ValidationError):
			canonical.validate(through="budget")


class TestFreshSite(IntegrationTestCase):
	"""Found 4 Oct 2026 on a new server: the seed ran only where the dev site
	already had everything set by hand. One allowed run must be enough."""

	def test_the_run_prepares_what_the_stages_need(self):
		from unittest import mock

		with mock.patch("kentender_procurement.std_templates.services.installer.ensure_site_release") as ensure, \
				mock.patch("kentender_procurement.std_templates.services.binding.require"), \
				mock.patch("frappe.installer.update_site_config") as update, mock.patch.dict(frappe.conf, {"kt_bds_simulation_environment": 0}):
			out = canonical.prepare_site(through="tenders")
			ensure.assert_called_once()  # the tender template, before requisitions
			update.assert_not_called()  # no bid stage, no simulated services
			self.assertFalse(out["simulation_switched_on"])
			out = canonical.prepare_site(through="bid_opening")
			update.assert_called_once_with("kt_bds_simulation_environment", 1)
			self.assertTrue(out["simulation_switched_on"])
			self.assertEqual(frappe.conf.get("kt_bds_simulation_environment"), 1)
		with mock.patch("kentender_procurement.std_templates.services.installer.ensure_site_release") as ensure:
			canonical.prepare_site(through="budget")
			ensure.assert_not_called()

	def test_an_open_tender_switches_on_the_simulated_bid_services(self):
		"""A Tender left open is there to be bid on: signing and submitting need
		the simulated services, even seeded only through `tenders`."""
		from unittest import mock

		with mock.patch("kentender_procurement.std_templates.services.installer.ensure_site_release"), \
				mock.patch("kentender_procurement.std_templates.services.binding.require"), \
				mock.patch("frappe.installer.update_site_config") as update, mock.patch.dict(frappe.conf, {"kt_bds_simulation_environment": 0}):
			out = canonical.prepare_site(through="tenders", open_tender=True)
		update.assert_called_once_with("kt_bds_simulation_environment", 1)
		self.assertTrue(out["simulation_switched_on"])

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
				canonical.prepare_site(through="requisitions")
		self.assertIn("wkhtmltopdf 0.12.6 found; wkhtmltopdf 0.12.6.1 (with patched qt) needed", str(ctx.exception))

	def test_allow_canonical_seed_alone_lets_every_stage_run(self):
		"""Each module seed keeps its own demo-data guard; an allowed run
		(developer_mode, allow_canonical_seed or force) satisfies them all."""
		from unittest import mock

		frappe.set_user("Administrator")
		# the test runner sets in_test itself, which the module guards accept; take it away
		with mock.patch.dict(frappe.conf, {"developer_mode": 0, "allow_tests": 0, "allow_canonical_seed": 1}), mock.patch.dict(frappe.flags, {"in_test": False}):
			out = canonical.run(through="planning", reset=False, validate=False, force=False, commit=False)
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

		def fake_run_seed(*, through, **_kwargs):
			calls.append(through)
			if len(calls) == 1:
				raise CanonicalTenderIncomplete("The canonical Tender TND-X was seeded without the bid lifecycle.")
			return {"ok": True}

		frappe.set_user("Administrator")
		with mock.patch.object(canonical, "seed", side_effect=fake_run_seed), mock.patch.object(canonical, "clear_canonical_modules", return_value={}) as rebuild, \
				mock.patch.object(canonical, "clear_non_canonical", return_value={}), mock.patch("kentender_strategy.services.strategy_reference.reset_reference_series"):
			out = canonical.run(through="award", validate=False, force=True, commit=False)
		self.assertEqual(calls, ["award", "award"])
		rebuild.assert_called_once()
		self.assertTrue(out["rebuilt_after_partial_world"])


class TestOpenTender(IntegrationTestCase):
	"""Owner, 4 Oct 2026: a demo site needs a Tender anyone can see on
	/tenders and start a bid on. `open_tender` (make `OPEN=True`) stops the
	canonical story before the submission deadline; a run asking for the
	other shape rebuilds by itself. Runs only on a test site."""

	def test_open_goes_only_with_the_stages_before_the_deadline(self):
		frappe.set_user("Administrator")
		for through in ("requisitions", "bid_opening", "award"):
			with self.assertRaisesRegex(frappe.ValidationError, "OPEN=True"):
				canonical.run(through=through, open_tender=True, reseed=True, validate=False, force=True, commit=False)

	def test_an_open_tender_is_listed_for_anyone_and_a_closed_run_rebuilds_it(self):
		from kentender_procurement.bid_submission.seeds.kentender_mvp_v1 import BIDDERS, bidder_bid, canonical_bid
		from kentender_procurement.bid_submission.services import reads

		frappe.set_user("Administrator")
		out = canonical.run(through="tenders", open_tender=True, validate=True, force=True, commit=True)
		tender = out["seeded"]["tenders"]["tender"]
		self.assertEqual(frappe.db.get_value("Tender", tender, "overall_status"), "Published — open")
		reference = frappe.db.get_value("Tender", tender, "tender_reference")
		frappe.set_user("Guest")
		self.assertIn(reference, [r["reference"] for r in reads.get_available_tenders()["rows"]])
		frappe.set_user("Administrator")
		again = canonical.run(through="tenders", open_tender=True, validate=True, force=True, commit=True)
		self.assertTrue(again["seeded"]["tenders"]["idempotent"])

		# with the bids: all four submitted, the Tender still open
		out = canonical.run(through="bid_submission", open_tender=True, validate=True, force=True, commit=True)
		tender = out["seeded"]["bid_submission"]["tender"]
		self.assertEqual(frappe.db.get_value("Tender", tender, "overall_status"), "Published — open")
		bids = [canonical_bid(tender)] + [bidder_bid(tender, b) for b in BIDDERS]
		self.assertEqual([frappe.db.get_value("Bid Workspace", b, "status") for b in bids], ["Submitted"] * 4)
		again = canonical.run(through="bid_submission", open_tender=True, validate=True, force=True, commit=True)
		self.assertTrue(again["seeded"]["bid_submission"]["idempotent"])

		# the ordinary story again: the Tender closes at its deadline
		out = canonical.run(through="tenders", validate=True, force=True, commit=True)
		self.assertEqual(frappe.db.get_value("Tender", out["seeded"]["tenders"]["tender"], "overall_status"), "Submission period ended")
