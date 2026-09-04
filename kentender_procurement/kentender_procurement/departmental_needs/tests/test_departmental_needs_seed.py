"""Phase 6 seed-contract tests for NDS-CHG-001 v1.1 §14.

Asserts the §14.1 prerequisites, the §14.2 actors and assignments, the exact
§14.3 default Needs, and that the §14.4/§14.5 profiles are independently
selectable and resettable (§14.7) — including that applying and resetting one
leaves the four-row default fixture untouched.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.departmental_needs.constants import (
	INTAKE_OPEN,
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_RETURNED,
	STATE_SUBMITTED,
	USAGE_FULL,
	USAGE_NOT_INCLUDED,
	VERSION_ACCEPTED,
	VERSION_DRAFT,
	VERSION_RETURNED,
	VERSION_SUBMITTED,
	VERSION_SUPERSEDED,
)
from kentender_core.seeds import kebs_foundation
from kentender_procurement.departmental_needs.seeds import profiles
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	ACTING_REVIEWER,
	AUDITOR,
	AUTHOR,
	FY,
	INTAKE_CLOSES_AT,
	INTAKE_OPENS_AT,
	INTAKE_WINDOW,
	ISOLATION_PE,
	ISOLATION_REQUESTER,
	OU_DIGITAL_HEALTH,
	OU_HRMD,
	PE,
	PLANNER,
	REVIEWER,
	upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services.context import needs_submission_state
from kentender_procurement.departmental_needs.services.usage import planning_usage

# NDS-CHG-001 v1.6 §14/§16.4 retargets this fixture onto ERPNext `Fiscal Year`
# and `UOM`, User Responsibility Assignment grants, and the plain Open/Closed
# Needs-submission flag — `seeds/kentender_mvp_r1.py` and this file still
# build/assert the pre-v1.6 world (`Needs Intake Window`, `Unit Of Measure`,
# `User Permission`). Tracked as IMPLEMENTATION_TRACKER.md NDS-G06 (seeds) /
# NDS-G07 (this suite); until the seed rewrite lands, `upsert_departmental_needs()`
# itself raises, so every class below errors at setUpClass regardless of this
# file's own content.

# §14.3 — reference, department, quantity, required-by, state.
DEFAULT_NEEDS = {
	"NDS-MOH-2027-0001": (OU_DIGITAL_HEALTH, 1, "2027-08-31", STATE_ACCEPTED),
	"NDS-MOH-2027-0002": (OU_HRMD, 1, "2027-12-31", STATE_SUBMITTED),
	"NDS-MOH-2027-0003": (OU_HRMD, 200, "2027-12-31", STATE_RETURNED),
	"NDS-MOH-2027-0004": (OU_DIGITAL_HEALTH, 300, "2027-12-31", STATE_DRAFT),
}

# §14.3 exact expected operational results.
EXPECTED_RESULTS = {
	"NDS-MOH-2027-0001": "Priority health facilities can use secure and interoperable digital health services.",
	"NDS-MOH-2027-0002": "Build internal capacity to operate and support national digital health platforms.",
	"NDS-MOH-2027-0003": "Provide the equipment required for staff training on the deployed digital health services.",
	"NDS-MOH-2027-0004": "Provide endpoint equipment required to use the deployed digital health services.",
}


class SeedCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")

	def need(self, reference: str):
		return frappe.get_doc("Departmental Need", reference)

	def current_version(self, reference: str):
		return frappe.get_doc("Departmental Need Version", self.need(reference).current_version)


class TestConfigurationPrerequisites(SeedCase):
	"""§14.1."""

	def test_the_governed_units_are_active(self):
		for code, label in (("UNIT-PROGRAMME", "Programme"), ("UNIT-EACH", "Each")):
			row = frappe.db.get_value(
				"Unit Of Measure", code, ["unit_label", "status"], as_dict=True
			)
			self.assertEqual((row.unit_label, row.status), (label, "Active"))

	def test_the_intake_window_holds_the_exact_specified_instants(self):
		row = frappe.db.get_value(
			"Needs Intake Window", INTAKE_WINDOW, ["opens_at", "closes_at"], as_dict=True
		)
		self.assertEqual(str(row.opens_at), INTAKE_OPENS_AT)
		self.assertEqual(str(row.closes_at), INTAKE_CLOSES_AT)

	def test_seeding_restores_the_window_it_opened_to_build(self):
		# The build needs an Open window; the fixture must not keep one.
		upsert_departmental_needs()
		row = frappe.db.get_value(
			"Needs Intake Window", INTAKE_WINDOW, ["opens_at", "closes_at"], as_dict=True
		)
		self.assertEqual(str(row.opens_at), INTAKE_OPENS_AT)
		self.assertEqual(str(row.closes_at), INTAKE_CLOSES_AT)

	def test_the_window_is_open_at_the_design_clock(self):
		# §14.1's design clock is 24 Nov 2026, inside the window.
		self.assertEqual(
			needs_submission_state(FY, at="2026-11-24 15:00:00")["state"], INTAKE_OPEN
		)


class TestActorsAndAssignments(SeedCase):
	"""§14.2."""

	def test_every_named_actor_exists_and_is_enabled(self):
		for user in (AUTHOR, REVIEWER, ACTING_REVIEWER, PLANNER, AUDITOR, ISOLATION_REQUESTER):
			self.assertTrue(frappe.db.get_value("User", user, "enabled"), f"{user} is disabled")

	def test_the_author_is_scoped_to_both_named_departments(self):
		units = set(
			frappe.get_all(
				"User Permission",
				filters={"user": AUTHOR, "allow": "Organisation Unit"},
				pluck="for_value",
			)
		)
		self.assertEqual(units, {OU_DIGITAL_HEALTH, OU_HRMD})

	def test_the_acting_head_is_scoped_to_one_department_only(self):
		units = frappe.get_all(
			"User Permission",
			filters={"user": ACTING_REVIEWER, "allow": "Organisation Unit"},
			pluck="for_value",
		)
		self.assertEqual(units, [OU_DIGITAL_HEALTH])

	def test_the_isolation_actor_is_scoped_to_another_entity(self):
		entities = frappe.get_all(
			"User Permission",
			filters={"user": ISOLATION_REQUESTER, "allow": "Procuring Entity"},
			pluck="for_value",
		)
		self.assertEqual(entities, [ISOLATION_PE])

	def test_the_isolation_actor_owns_no_seeded_need(self):
		# §14.5 — isolation records stay out of the four-row fixture.
		self.assertEqual(
			frappe.get_all("Departmental Need", filters={"owner": ISOLATION_REQUESTER}, pluck="name"),
			[],
		)


class TestDefaultNeeds(SeedCase):
	"""§14.3."""

	def test_exactly_the_four_specified_needs_exist(self):
		references = set(
			frappe.get_all("Departmental Need", filters={"procuring_entity": PE}, pluck="name")
		)
		self.assertEqual(references, set(DEFAULT_NEEDS))

	def test_each_need_matches_its_specified_row(self):
		for reference, (unit, quantity, required_by, state) in DEFAULT_NEEDS.items():
			need = self.need(reference)
			version = self.current_version(reference)
			self.assertEqual(need.organisation_unit, unit, reference)
			self.assertEqual(need.current_state, state, reference)
			self.assertEqual(int(version.indicative_quantity), quantity, reference)
			self.assertEqual(str(version.required_by_date), required_by, reference)

	def test_each_need_carries_its_exact_expected_operational_result(self):
		for reference, expected in EXPECTED_RESULTS.items():
			self.assertEqual(self.current_version(reference).expected_operational_result, expected)

	def test_the_returned_need_has_a_server_created_version_two(self):
		need = self.need("NDS-MOH-2027-0003")
		versions = frappe.get_all(
			"Departmental Need Version",
			filters={"departmental_need": need.name},
			fields=["name", "version_number", "version_status", "based_on_version"],
			order_by="version_number asc",
		)
		self.assertEqual([row.version_number for row in versions], [1, 2])
		self.assertEqual(versions[0].version_status, VERSION_RETURNED)
		self.assertEqual(versions[1].version_status, VERSION_DRAFT)
		self.assertEqual(versions[1].based_on_version, versions[0].name)
		self.assertEqual(need.current_version, versions[1].name)

	def test_the_accepted_need_points_at_its_accepted_version(self):
		need = self.need("NDS-MOH-2027-0001")
		self.assertEqual(need.current_accepted_version, need.current_version)
		self.assertEqual(
			frappe.db.get_value(
				"Departmental Need Version", need.current_accepted_version, "version_status"
			),
			VERSION_ACCEPTED,
		)

	def test_the_submitted_need_is_locked_and_hashed(self):
		version = self.current_version("NDS-MOH-2027-0002")
		self.assertEqual(version.version_status, VERSION_SUBMITTED)
		self.assertTrue(version.content_hash)

	def test_every_need_is_owned_by_the_named_author(self):
		owners = set(
			frappe.get_all("Departmental Need", filters={"procuring_entity": PE}, pluck="owner")
		)
		self.assertEqual(owners, {AUTHOR})

	def test_the_design_clock_decision_times_are_applied(self):
		expected = {
			("NDS-MOH-2027-0001", "Accept for planning"): "2026-11-24 14:00:00",
			("NDS-MOH-2027-0002", "Submit"): "2026-11-24 12:20:00",
			("NDS-MOH-2027-0003", "Return for correction"): "2026-11-24 13:35:00",
		}
		for (need, action), when in expected.items():
			occurred = frappe.db.get_value(
				"Departmental Need Decision",
				{"departmental_need": need, "action": action},
				"occurred_at",
				order_by="creation desc",
			)
			self.assertEqual(str(occurred), when, f"{need} {action}")

	def test_the_default_profile_reports_not_included_for_every_need(self):
		# §14.3 — the design-clock value, with no Planning usage profile loaded.
		for reference in DEFAULT_NEEDS:
			self.assertEqual(planning_usage(reference), USAGE_NOT_INCLUDED, reference)

	def test_reseeding_creates_nothing_new(self):
		before = (
			frappe.db.count("Departmental Need"),
			frappe.db.count("Departmental Need Version"),
			frappe.db.count("Departmental Need Decision"),
			frappe.db.count("Departmental Need Event"),
		)
		upsert_departmental_needs()
		after = (
			frappe.db.count("Departmental Need"),
			frappe.db.count("Departmental Need Version"),
			frappe.db.count("Departmental Need Decision"),
			frappe.db.count("Departmental Need Event"),
		)
		self.assertEqual(before, after)

	def test_the_accepted_need_published_its_event(self):
		# §14.7 requires the seed to use the real commands, so the outbox row is
		# produced by acceptance rather than written alongside it.
		need = self.need("NDS-MOH-2027-0001")
		self.assertTrue(
			frappe.db.exists(
				"Departmental Need Event",
				{
					"departmental_need": need.name,
					"event_type": "DepartmentalNeedAccepted.v2",
					"need_version": need.current_accepted_version,
				},
			)
		)


class TestSelectableProfiles(SeedCase):
	"""§14.7 — independently selectable and resettable."""

	def default_fingerprint(self):
		return frappe.get_all(
			"Departmental Need",
			filters={"procuring_entity": PE},
			fields=["name", "current_state", "current_version", "current_accepted_version"],
			order_by="name",
		)

	def test_an_unknown_profile_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			profiles.apply_profile("not_a_profile")

	def test_planning_usage_applies_and_resets(self):
		# §14.4 — Fully included in the named Active Plan and Plan Item.
		need = self.need("NDS-MOH-2027-0001")
		self.assertEqual(planning_usage(need.name), USAGE_NOT_INCLUDED)
		applied = profiles.apply_profile("planning_usage")
		self.assertEqual(applied["plan_item"], profiles.ACTIVE_PLAN_ITEM)
		self.assertEqual(planning_usage(need.name), USAGE_FULL)
		profiles.reset_profile("planning_usage")
		self.assertEqual(planning_usage(need.name), USAGE_NOT_INCLUDED)

	def test_the_successor_profile_changes_only_the_required_by_date(self):
		# §14.5 — Version 2 differs from Version 1 in one field.
		need = self.need("NDS-MOH-2027-0001")
		version_one = frappe.get_doc("Departmental Need Version", need.current_accepted_version)
		applied = profiles.apply_profile("successor")
		version_two = frappe.get_doc("Departmental Need Version", applied["accepted_version"])
		self.assertEqual(str(version_two.required_by_date), profiles.SUCCESSOR_REQUIRED_BY)
		for field in ("title", "description", "expected_operational_result", "unit"):
			self.assertEqual(version_two.get(field), version_one.get(field), field)
		self.assertEqual(version_two.indicative_quantity, version_one.indicative_quantity)
		# Version 1 is superseded, not altered.
		version_one.reload()
		self.assertEqual(version_one.version_status, VERSION_SUPERSEDED)
		self.assertEqual(str(version_one.required_by_date), "2027-08-31")

	def test_resetting_the_successor_restores_the_default_fixture(self):
		before = self.default_fingerprint()
		profiles.apply_profile("successor")
		self.assertNotEqual(self.default_fingerprint(), before)
		profiles.reset_profile("successor")
		self.assertEqual(self.default_fingerprint(), before)

	def test_the_withdrawal_profile_uses_the_specified_identifier_and_reason(self):
		applied = profiles.apply_profile("withdrawal_blocked")
		self.assertEqual(applied["withdrawal_request"], profiles.WITHDRAWAL_REQUEST_ID)
		request = frappe.get_doc("Need Withdrawal Request", profiles.WITHDRAWAL_REQUEST_ID)
		self.assertEqual(request.reason, profiles.WITHDRAWAL_REASON)
		self.assertEqual(request.requested_by, AUTHOR)
		profiles.reset_profile("withdrawal_blocked")

	def test_the_blocked_variant_carries_the_active_plan_dependency(self):
		profiles.apply_profile("withdrawal_blocked")
		self.assertEqual(planning_usage("NDS-MOH-2027-0001"), USAGE_FULL)
		profiles.reset_profile("withdrawal_blocked")

	def test_the_cleared_variant_supplies_no_plan_references(self):
		# §14.5 — the cleared variant is Not included with no Plan references.
		profiles.apply_profile("withdrawal_cleared")
		need = self.need("NDS-MOH-2027-0001")
		self.assertEqual(planning_usage(need.name), USAGE_NOT_INCLUDED)
		row = frappe.db.get_value(
			"Need Planning Usage Projection",
			need.current_accepted_version,
			["active_plan", "active_plan_item"],
			as_dict=True,
		)
		self.assertEqual((row.active_plan, row.active_plan_item), ("", ""))
		profiles.reset_profile("withdrawal_cleared")

	def test_a_profile_can_be_reapplied_after_reset(self):
		for _ in range(2):
			profiles.apply_profile("withdrawal_blocked")
			profiles.reset_profile("withdrawal_blocked")
		self.assertEqual(
			frappe.get_all(
				"Need Withdrawal Request", filters={"departmental_need": "NDS-MOH-2027-0001"}
			),
			[],
		)


class TestKebsFirstSlice(SeedCase):
	"""§14.6 / NDS-AC-045 — proved through the real Needs-origin route."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		kebs_foundation.install()
		profiles.apply_profile("kebs")

	def kebs_needs(self):
		# Scoped to the three §14.6 titles: this test owns the seed's records,
		# not the PE. Counting everything under PE-KEBS made the assertion fail
		# the moment a real KEBS author created and had a genuine Need accepted
		# on the same site (observed 2026-08-30), which is normal use, not a
		# seed defect.
		titles = tuple(spec["title"] for spec in profiles.KEBS_NEEDS)
		return frappe.db.sql(
			"""
			select n.name, n.current_state, n.organisation_unit, n.financial_year,
			       v.title, v.indicative_quantity, v.unit, v.expected_operational_result
			from `tabDepartmental Need` n
			join `tabDepartmental Need Version` v on v.name = n.current_accepted_version
			where n.procuring_entity = %s and v.title in %s order by n.name
			""",
			(kebs_foundation.PE, titles),
			as_dict=True,
		)

	def test_the_canonical_foundation_is_installed_and_usable(self):
		state = kebs_foundation.verify()
		self.assertTrue(state["installed"], state["missing"])
		self.assertTrue(state["usable"], state)

	def test_all_three_source_lines_reach_accepted_through_the_real_lifecycle(self):
		# NDS-AC-045 must not be satisfied by writing rows or by the direct
		# Planning route: each Need is created, submitted and accepted by real
		# actors, so the acceptance it claims actually happened.
		rows = self.kebs_needs()
		self.assertEqual(len(rows), 3)
		for row in rows:
			self.assertEqual(row.current_state, STATE_ACCEPTED, row.name)
			self.assertEqual(row.organisation_unit, kebs_foundation.OU)
			self.assertEqual(row.financial_year, kebs_foundation.FY)

	def test_the_source_facts_match_the_specified_first_slice(self):
		by_title = {row.title: row for row in self.kebs_needs()}
		for spec in profiles.KEBS_NEEDS:
			row = by_title[spec["title"]]
			self.assertEqual(int(row.indicative_quantity), spec["indicative_quantity"], spec["title"])
			self.assertEqual(row.unit, spec["unit"], spec["title"])
			self.assertEqual(
				row.expected_operational_result, spec["expected_operational_result"], spec["title"]
			)

	def test_each_accepted_need_published_its_source_payload(self):
		import json

		for row in self.kebs_needs():
			payload = frappe.db.get_value(
				"Departmental Need Event",
				{"departmental_need": row.name, "event_type": "DepartmentalNeedAccepted.v2"},
				"payload",
			)
			self.assertTrue(payload, row.name)
			body = json.loads(payload)
			self.assertEqual(body["title"], row.title)
			self.assertEqual(body["indicative_quantity"], row.indicative_quantity)
			self.assertEqual(body["expected_operational_result"], row.expected_operational_result)
			self.assertEqual(body["procuring_entity_id"], kebs_foundation.PE)

	def test_the_needs_belong_to_the_canonical_context(self):
		self.assertTrue(
			frappe.db.exists(
				"PE Fiscal Year Context",
				{
					"name": kebs_foundation.CONTEXT,
					"procuring_entity": kebs_foundation.PE,
					"financial_year": kebs_foundation.FY,
					"context_status": "Active",
				},
			)
		)

	def test_the_profile_is_resettable_and_reappliable(self):
		profiles.reset_profile("kebs")
		self.assertEqual(
			frappe.db.count("Departmental Need", {"procuring_entity": kebs_foundation.PE}), 0
		)
		profiles.apply_profile("kebs")
		self.assertEqual(
			frappe.db.count("Departmental Need", {"procuring_entity": kebs_foundation.PE}), 3
		)


class TestKebsFoundationGuards(SeedCase):
	"""The canonical fixture is never created silently by a consumer."""

	def test_the_profile_fails_clearly_when_the_foundation_is_absent(self):
		# §14.1/§14.6 — seeds never invent a fallback record.
		profiles.reset_profile("kebs")
		kebs_foundation.remove()
		self.assertFalse(kebs_foundation.verify()["installed"])
		with self.assertRaises(frappe.ValidationError) as caught:
			profiles.apply_profile("kebs")
		message = str(caught.exception)
		self.assertIn("canonical KEBS foundation fixture", message)
		self.assertIn("kebs_foundation.install", message)
		# The failure creates nothing.
		self.assertEqual(
			frappe.db.count("Departmental Need", {"procuring_entity": kebs_foundation.PE}), 0
		)
		self.assertFalse(frappe.db.exists("Procuring Entity", kebs_foundation.PE))

	def test_verify_names_exactly_what_is_missing(self):
		profiles.reset_profile("kebs")
		kebs_foundation.remove()
		state = kebs_foundation.verify()
		self.assertIn(f"Procuring Entity {kebs_foundation.PE}", state["missing"])
		self.assertIn(f"Organisation Unit {kebs_foundation.OU}", state["missing"])

	def test_the_foundation_refuses_to_drop_records_still_in_use(self):
		kebs_foundation.install()
		profiles.apply_profile("kebs")
		with self.assertRaises(frappe.ValidationError) as caught:
			kebs_foundation.remove()
		self.assertIn("still reference", str(caught.exception))
		profiles.reset_profile("kebs")
