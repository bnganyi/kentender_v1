"""Phase 2 command tests for NDS-CHG-001 v1.1 §5.

Traverses every row of the §5.1 initial lifecycle, the §5.2 accepted-successor
lifecycle and the §5.3 withdrawal decision table, plus the §5.4 controls that
apply to all of them: intake gating (NDS-BR-002/003), maker-checker
(NDS-BR-006), optimistic locking, decision tokens and idempotent replay
(NDS-BR-018, NDS-AC-028).

Commands run as the real seeded actors via `frappe.set_user`, because the
framework `owner` field is the Need's author (§4.2) and maker-checker is
decided from it.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_procurement.departmental_needs.constants import (
	ACTION_ACCEPT_SUCCESSOR,
	ACTION_EVALUATE_WITHDRAWAL,
	ACTION_REEVALUATE_WITHDRAWAL,
	DESCRIPTION_MAX,
	DESCRIPTION_MIN,
	INTAKE_CLOSED,
	INTAKE_OPEN,
	ROLE_DEPARTMENTAL_AUTHOR,
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_NOT_TAKEN_FORWARD,
	STATE_RETURNED,
	STATE_SUBMITTED,
	STATE_WITHDRAWN,
	TASK_COMPLETED,
	TASK_INITIAL_ACCEPTANCE,
	TASK_OPEN,
	TASK_SUCCESSOR_ACCEPTANCE,
	VERSION_ACCEPTED,
	VERSION_DRAFT,
	VERSION_NOT_TAKEN_FORWARD,
	VERSION_RETURNED,
	VERSION_SUBMITTED,
	VERSION_SUPERSEDED,
	VERSION_WITHDRAWN,
	WITHDRAWAL_AWAITING_CLEARANCE,
	WITHDRAWAL_AWAITING_REVIEW,
	USAGE_FULL,
	USAGE_NOT_INCLUDED,
	WITHDRAWAL_DECLINED,
)
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	ACTING_REVIEWER,
	AUTHOR,
	FY,
	PLANNER,
	REVIEWER,
	upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services import events, lifecycle, workspace
from kentender_procurement.departmental_needs.services.usage import project_planning_usage

# NDS-CHG-001 v1.6 §14 rewrote the seed onto the AUTH-ADR-001 v1.6 resolver;
# `PE`, `INTAKE_WINDOW` and the static `OU_DIGITAL_HEALTH` constant no longer
# exist (Organisation Units are resolved from each actor's real grant). This
# file's fixture helpers below (`open_window`/`close_window`/`create`/
# `create_as`) still build the pre-v1.6 world and are Phase 7 work
# (IMPLEMENTATION_TRACKER.md NDS-G07) — keeping this import block resolvable
# is what lets the rest of the app's test suite be discovered.

REASON = "The department no longer requires this equipment in the target financial year."


class DepartmentalNeedsCommandCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")
		self.open_window()

	# --- fixtures ----------------------------------------------------------

	def open_window(self):
		"""Put the seeded §14.1 window around "now" for this transaction only."""
		now = now_datetime()
		frappe.db.set_value(
			"Needs Intake Window",
			INTAKE_WINDOW,
			{"opens_at": add_days(now, -1), "closes_at": add_days(now, 1)},
			update_modified=False,
		)

	def close_window(self):
		now = now_datetime()
		frappe.db.set_value(
			"Needs Intake Window",
			INTAKE_WINDOW,
			{"opens_at": add_days(now, -3), "closes_at": add_days(now, -1)},
			update_modified=False,
		)

	def key(self) -> str:
		return f"nds-test-{uuid4().hex}"

	def author_reviewer(self) -> str:
		"""The reviewer, additionally holding the Departmental Author role.

		Maker-checker only becomes reachable for someone who *has* review
		authority: an author without the Head of User Department role is a plain
		scope denial, and naming maker-checker to them would disclose that the
		record exists.
		"""
		user = frappe.get_doc("User", REVIEWER)
		if not any(row.role == ROLE_DEPARTMENTAL_AUTHOR for row in user.roles):
			user.append("roles", {"role": ROLE_DEPARTMENTAL_AUTHOR})
			user.save(ignore_permissions=True)
			frappe.clear_cache(user=REVIEWER)
		return REVIEWER

	def create_as(self, user: str, **overrides):
		frappe.set_user(user)
		return lifecycle.create_need(
			procuring_entity=PE,
			organisation_unit=OU_DIGITAL_HEALTH,
			financial_year=FY,
			idempotency_key=self.key(),
			**self.content(**overrides),
		)

	def content(self, **overrides):
		values = {
			"title": "Clinical deployment laptops for rollout",
			"description": "Laptop computers for deployment at priority health facilities.",
			"expected_operational_result": "Facilities can use the deployed digital health services.",
			"indicative_quantity": 10,
			"unit": "UNIT-EACH",
			"required_by_date": "2027-12-31",
		}
		values.update(overrides)
		return values

	def create(self, **overrides):
		frappe.set_user(AUTHOR)
		return lifecycle.create_need(
			procuring_entity=PE,
			organisation_unit=OU_DIGITAL_HEALTH,
			financial_year=FY,
			idempotency_key=self.key(),
			**self.content(**overrides),
		)

	def submit(self, result):
		frappe.set_user(AUTHOR)
		return lifecycle.submit_need(
			need=result["need"],
			expected_version=result["record_version"],
			idempotency_key=self.key(),
		)

	def decide(self, result, decision: str, *, reason: str = "", token: str = ""):
		frappe.set_user(REVIEWER)
		task = result["task"]
		return lifecycle.review_need(
			need=result["need"],
			decision=decision,
			task=task,
			expected_version=result["record_version"],
			decision_token=token or self.token(task),
			idempotency_key=self.key(),
			reason=reason,
		)

	def token(self, task: str) -> str:
		return frappe.db.get_value("Departmental Need Review Task", task, "decision_token")

	def accepted(self):
		"""A Need that has completed §5.1 and is Accepted for planning."""
		return self.decide(self.submit(self.create()), "accept")

	def version(self, name: str):
		return frappe.get_doc("Departmental Need Version", name)

	def status_of(self, name: str) -> str:
		return frappe.db.get_value("Departmental Need Version", name, "version_status")

	def project_usage(self, need: str, version: str, usage: str) -> dict:
		"""Report Planning usage the way Planning does — through the §8.2 event.

		The withdrawal dependency is read from the §4.7 projection, never from
		Planning's tables (firm D1 boundary), so the fixture publishes an event
		rather than writing a Plan allocation.
		"""
		frappe.set_user(PLANNER)
		try:
			return project_planning_usage(
				departmental_need=need,
				accepted_version=version,
				usage=usage,
				source_event_id=self.key(),
				active_plan="PLN-NDS-LIFECYCLE-TEST" if usage == USAGE_FULL else "",
				active_plan_item="PPI-NDS-LIFECYCLE-TEST" if usage == USAGE_FULL else "",
			)
		finally:
			frappe.set_user("Administrator")

	def include_in_active_plan(self, need: str, version: str) -> dict:
		return self.project_usage(need, version, USAGE_FULL)

	def clear_from_active_plan(self, need: str, version: str) -> dict:
		return self.project_usage(need, version, USAGE_NOT_INCLUDED)


# NDS-CHG-001 v1.6 §4.1/§16.4.11 retired the windowed opens_at/closes_at model
# (and its "Scheduled" state) entirely — the old `TestNeedsIntakeWindow` class
# tested a mechanism that no longer exists. `services/context.py`'s
# `needs_submission_state()`/`require_open_intake()` implement the new plain
# Open/Closed flag; a regression suite for that lands with the Phase 6/7 seed
# and test rewrite (IMPLEMENTATION_TRACKER.md NDS-G06/NDS-G07), since the
# fixture this file's classes share (`DepartmentalNeedsCommandCase`) still
# builds through the pre-v1.6 `upsert_departmental_needs()`/window helpers.


class TestInitialNeedLifecycle(DepartmentalNeedsCommandCase):
	"""§5.1."""

	def test_create_generates_reference_and_draft_version_one(self):
		result = self.create()
		need = frappe.get_doc("Departmental Need", result["need"])
		version = self.version(need.current_version)
		self.assertEqual(need.current_state, STATE_DRAFT)
		self.assertEqual(version.version_number, 1)
		self.assertEqual(version.version_status, VERSION_DRAFT)
		self.assertTrue(need.need_reference.startswith("NDS-MOH-2027-"))
		self.assertFalse(need.current_accepted_version)

	def test_create_outside_the_intake_window_is_refused(self):
		self.close_window()
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.create()
		self.assertEqual(caught.exception.code, "NDS_INTAKE_NOT_OPEN")

	def test_create_is_allowed_for_a_future_target_financial_year(self):
		# §14.1 collects FY 2027/28 Needs during a 2026 window: a future target
		# year is the normal case, and the window alone governs timing.
		self.assertTrue(self.create()["ok"])

	def test_save_draft_updates_the_current_version(self):
		result = self.create()
		frappe.set_user(AUTHOR)
		saved = lifecycle.update_need(
			need=result["need"],
			expected_version=result["record_version"],
			idempotency_key=self.key(),
			**self.content(title="Revised clinical deployment laptops"),
		)
		self.assertEqual(saved["action"], "Save draft")
		self.assertEqual(
			self.version(saved["current_version"]).title, "Revised clinical deployment laptops"
		)

	def test_a_partial_draft_round_trips_through_its_own_saved_values(self):
		"""§12.3 — a partial Draft must stay saveable with what the read returns.

		Frappe stores a Float ``None`` as 0.0, so a title-only Draft's stored
		indicative_quantity is 0 — a value NDS-AC-005 forbids an author to
		*supply*. §8.1's read therefore reports the absence as absence
		(``None``), and an editor that round-trips exactly what it read saves
		cleanly instead of being refused over a value the author never typed.
		"""
		created = self.create(
			description="",
			expected_operational_result="",
			indicative_quantity=None,
			unit="",
			required_by_date=None,
		)
		read = workspace.get_need(need=created["need"])
		self.assertIsNone(read["current_version"]["indicative_quantity"])
		frappe.set_user(AUTHOR)
		saved = lifecycle.update_need(
			need=created["need"],
			expected_version=created["record_version"],
			idempotency_key=self.key(),
			title=read["current_version"]["title"],
			description=read["current_version"]["description"] or "",
			expected_operational_result=read["current_version"]["expected_operational_result"] or "",
			indicative_quantity=read["current_version"]["indicative_quantity"],
			unit=read["current_version"]["unit"] or "",
			required_by_date=read["current_version"]["required_by_date"],
		)
		self.assertEqual(saved["action"], "Save draft")

	def test_submission_still_rejects_a_missing_quantity(self):
		"""NDS-BR-007 keeps the presence invariant where it belongs — at submission."""
		created = self.create(
			description="A description long enough for the minimum bound.",
			expected_operational_result="An operational result long enough as well.",
			indicative_quantity=None,
			unit="UNIT-EACH",
			required_by_date="2027-12-31",
		)
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.submit(created)
		self.assertEqual(caught.exception.code, "NDS_FIELD_REQUIRED")

	def test_submit_locks_the_version_hashes_it_and_opens_one_task(self):
		result = self.submit(self.create())
		version = self.version(result["current_version"])
		self.assertEqual(result["current_state"], STATE_SUBMITTED)
		self.assertEqual(version.version_status, VERSION_SUBMITTED)
		self.assertTrue(version.content_hash)
		tasks = frappe.get_all(
			"Departmental Need Review Task",
			filters={"departmental_need": result["need"], "status": TASK_OPEN},
			fields=["name", "task_type"],
		)
		self.assertEqual(len(tasks), 1)
		self.assertEqual(tasks[0].task_type, TASK_INITIAL_ACCEPTANCE)

	def test_initial_submission_outside_the_window_is_refused(self):
		result = self.create()
		self.close_window()
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.submit(result)
		self.assertEqual(caught.exception.code, "NDS_INTAKE_NOT_OPEN")

	def test_a_returned_correction_may_be_resubmitted_after_the_window_closes(self):
		# NDS-BR-003 — the correction of a version submitted before close is not
		# re-gated on the window.
		returned = self.decide(self.submit(self.create()), "return", reason=REASON)
		self.close_window()
		resubmitted = self.submit(returned)
		self.assertEqual(resubmitted["action"], "Resubmit")
		self.assertEqual(resubmitted["current_state"], STATE_SUBMITTED)

	def test_return_preserves_the_submitted_version_and_copies_a_correction_draft(self):
		submitted = self.submit(self.create())
		original = submitted["current_version"]
		returned = self.decide(submitted, "return", reason=REASON)
		copy = self.version(returned["successor_version"])
		self.assertEqual(returned["current_state"], STATE_RETURNED)
		self.assertEqual(self.status_of(original), VERSION_RETURNED)
		self.assertEqual(copy.version_status, VERSION_DRAFT)
		self.assertEqual(copy.based_on_version, original)
		self.assertEqual(copy.title, self.version(original).title)

	def test_a_resubmitted_correction_keeps_the_returned_version_intact(self):
		# Revision integrity. The return path is asserted above; this is the other
		# half — that editing and resubmitting the correction writes to the *copy*
		# and leaves the returned version readable exactly as it was decided. If
		# the correction mutated the returned version instead, the Decision row
		# for the return would point at content that no longer matches the reason
		# it was returned for, and the audit trail would silently rewrite itself.
		submitted = self.submit(self.create())
		original = submitted["current_version"]
		original_title = self.version(original).title
		original_hash = self.version(original).content_hash
		returned = self.decide(submitted, "return", reason=REASON)
		correction = returned["successor_version"]

		frappe.set_user(AUTHOR)
		lifecycle.update_need(
			need=returned["need"],
			expected_version=returned["record_version"],
			idempotency_key=self.key(),
			**self.content(title="Clinical deployment laptops, corrected quantity"),
		)
		resubmitted = self.submit(
			{
				"need": returned["need"],
				"record_version": frappe.db.get_value(
					"Departmental Need", returned["need"], "record_version"
				),
			}
		)

		# The returned version is untouched in content, status and hash.
		self.assertEqual(self.version(original).title, original_title)
		self.assertEqual(self.version(original).content_hash, original_hash)
		self.assertEqual(self.status_of(original), VERSION_RETURNED)
		# The correction is a distinct, separately numbered version.
		self.assertEqual(resubmitted["current_version"], correction)
		self.assertEqual(self.status_of(correction), VERSION_SUBMITTED)
		self.assertNotEqual(self.version(correction).content_hash, original_hash)
		self.assertEqual(
			self.version(correction).version_number, self.version(original).version_number + 1
		)

	def test_return_without_a_reason_is_refused(self):
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.decide(self.submit(self.create()), "return")
		self.assertEqual(caught.exception.code, "NDS_FIELD_REQUIRED")

	def test_accept_sets_the_accepted_pointer_and_collects_no_reason(self):
		accepted = self.decide(self.submit(self.create()), "accept")
		need = frappe.get_doc("Departmental Need", accepted["need"])
		self.assertEqual(need.current_state, STATE_ACCEPTED)
		self.assertEqual(need.current_accepted_version, need.current_version)
		self.assertEqual(self.status_of(need.current_accepted_version), VERSION_ACCEPTED)
		decision = frappe.db.get_value(
			"Departmental Need Decision",
			{"departmental_need": need.name, "action": "Accept for planning"},
			"reason",
		)
		self.assertIn(decision, ("", None))

	def test_decline_requires_a_reason_and_closes_the_need(self):
		submitted = self.submit(self.create())
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.decide(submitted, "decline")
		self.assertEqual(caught.exception.code, "NDS_FIELD_REQUIRED")
		declined = self.decide(submitted, "decline", reason=REASON)
		self.assertEqual(declined["current_state"], STATE_NOT_TAKEN_FORWARD)
		self.assertEqual(self.status_of(declined["current_version"]), VERSION_NOT_TAKEN_FORWARD)

	def test_the_maker_of_a_version_cannot_decide_it(self):
		# NDS-BR-006 / NDS-AC-010 — a Head of User Department who authored the
		# Need still cannot decide it.
		maker = self.author_reviewer()
		created = self.create_as(maker)
		frappe.set_user(maker)
		submitted = lifecycle.submit_need(
			need=created["need"],
			expected_version=created["record_version"],
			idempotency_key=self.key(),
		)
		with self.assertRaises(DepartmentalNeedError) as caught:
			lifecycle.review_need(
				need=submitted["need"],
				decision="accept",
				task=submitted["task"],
				expected_version=submitted["record_version"],
				decision_token=self.token(submitted["task"]),
				idempotency_key=self.key(),
			)
		self.assertEqual(caught.exception.code, "NDS_MAKER_CHECKER")

	def test_an_author_without_review_authority_is_denied_before_maker_checker(self):
		# The scope check runs first so a user with no review authority is never
		# told which control they tripped.
		submitted = self.submit(self.create())
		frappe.set_user(AUTHOR)
		with self.assertRaises(DepartmentalNeedError) as caught:
			lifecycle.review_need(
				need=submitted["need"],
				decision="accept",
				task=submitted["task"],
				expected_version=submitted["record_version"],
				decision_token=self.token(submitted["task"]),
				idempotency_key=self.key(),
			)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_withdraw_closes_an_unaccepted_need(self):
		result = self.create()
		frappe.set_user(AUTHOR)
		withdrawn = lifecycle.withdraw_need(
			need=result["need"],
			expected_version=result["record_version"],
			idempotency_key=self.key(),
		)
		self.assertEqual(withdrawn["current_state"], STATE_WITHDRAWN)
		self.assertEqual(self.status_of(withdrawn["current_version"]), VERSION_WITHDRAWN)

	def test_an_accepted_need_cannot_use_self_service_withdrawal(self):
		accepted = self.accepted()
		frappe.set_user(AUTHOR)
		with self.assertRaises(DepartmentalNeedError) as caught:
			lifecycle.withdraw_need(
				need=accepted["need"],
				expected_version=accepted["record_version"],
				idempotency_key=self.key(),
			)
		self.assertEqual(caught.exception.code, "NDS_STATE_CONFLICT")


class ContentValidationCase(DepartmentalNeedsCommandCase):
	"""Shared saving helper for the two validation layers below."""

	def save_draft(self, **overrides):
		"""Save `overrides` onto a fresh Draft, returning the command result."""
		result = self.create()
		frappe.set_user(AUTHOR)
		return lifecycle.update_need(
			need=result["need"],
			expected_version=result["record_version"],
			idempotency_key=self.key(),
			**self.content(**overrides),
		)


class TestDraftContentBounds(ContentValidationCase):
	"""§4.3 — field *shape*, enforced by the version controller at save.

	The module splits content rules across two layers, and the split is load
	bearing rather than incidental: the controller checks the shape of a value
	that was supplied, while presence is deferred to submission so that §12.3 /
	NDS-AC-004's title-only Draft can still be saved. Asserting both here keeps
	the boundary honest — several `_validate_submission` branches are in fact
	unreachable through a normal save-then-submit because the controller has
	already refused the value, and that is defence in depth, not dead code.
	"""

	def refuses_at_save(self, code: str, **overrides):
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.save_draft(**overrides)
		self.assertEqual(caught.exception.code, code)

	def test_a_description_below_the_minimum_is_refused_at_save(self):
		self.refuses_at_save("NDS_FIELD_REQUIRED", description="x" * (DESCRIPTION_MIN - 1))

	def test_a_description_above_the_maximum_is_refused_at_save(self):
		self.refuses_at_save("NDS_FIELD_REQUIRED", description="x" * (DESCRIPTION_MAX + 1))

	def test_an_expected_operational_result_out_of_bounds_is_refused_at_save(self):
		# The v1.1 rename — the field Planning consumes downstream (§7.1).
		self.refuses_at_save(
			"NDS_FIELD_REQUIRED", expected_operational_result="x" * (DESCRIPTION_MIN - 1)
		)

	def test_a_zero_or_negative_quantity_is_refused_at_save(self):
		# NDS-AC-005 — "present" is not enough; it must be a real quantity.
		for quantity in (0, -1):
			with self.subTest(quantity=quantity):
				self.refuses_at_save("NDS_FIELD_REQUIRED", indicative_quantity=quantity)

	def test_a_quantity_beyond_the_allowed_precision_is_refused_at_save(self):
		# §4.3 allows three decimals; a fourth would be silently rounded into a
		# different requirement than the one the requester entered.
		self.refuses_at_save("NDS_FIELD_REQUIRED", indicative_quantity=2.5555)

	def test_an_empty_free_text_value_still_saves(self):
		# The boundary itself: bounds apply only to a supplied value, or the
		# title-only Draft that NDS-AC-004 requires could never be saved.
		saved = self.save_draft(description="", expected_operational_result="")
		self.assertEqual(self.version(saved["current_version"]).description, "")

	def test_a_unit_outside_the_governed_catalogue_cannot_be_stored(self):
		# NDS-AC-006 — §1.1 removed free-text "Other" outright. An unknown code
		# is refused by the Link itself, before any service-layer rule runs, so
		# no ungoverned unit can reach a version row at all.
		with self.assertRaises(frappe.LinkValidationError):
			self.save_draft(unit="UNIT-NOT-GOVERNED")


class TestSubmissionValidation(ContentValidationCase):
	"""§5 / NDS-BR-007 — every `_validate_submission` rejection path.

	Submission is where *completeness* is enforced. Each case below saves a
	Draft that is legitimately saveable and not submittable, so the failure is
	attributable to one submission rule rather than to a rejected save.
	"""

	def refuses(self, code: str, **overrides):
		draft = self.save_draft(**overrides)
		before = self.status_of(draft["current_version"])
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.submit(draft)
		self.assertEqual(caught.exception.code, code)
		# §5 — a rejected submission is a pure no-op, not a partial transition.
		self.assertEqual(self.status_of(draft["current_version"]), before)
		self.assertEqual(
			frappe.db.count(
				"Departmental Need Review Task",
				{"departmental_need": draft["need"], "status": TASK_OPEN},
			),
			0,
		)

	def test_a_missing_description_is_refused(self):
		self.refuses("NDS_FIELD_REQUIRED", description="")

	def test_a_missing_expected_operational_result_is_refused(self):
		self.refuses("NDS_FIELD_REQUIRED", expected_operational_result="")

	def test_a_missing_quantity_is_refused(self):
		self.refuses("NDS_FIELD_REQUIRED", indicative_quantity=None)

	def test_a_missing_unit_is_refused(self):
		self.refuses("NDS_FIELD_REQUIRED", unit="")

	def test_an_inactive_governed_unit_is_refused(self):
		# The subtler half of NDS-AC-006: the code exists and is spelled right,
		# but the catalogue has retired it. A Link check alone would pass this,
		# which is why the governance rule lives at submission and not only in
		# the Link.
		frappe.db.set_value(
			"Unit Of Measure", "UNIT-PROGRAMME", "status", "Inactive", update_modified=False
		)
		self.addCleanup(
			frappe.db.set_value,
			"Unit Of Measure",
			"UNIT-PROGRAMME",
			"status",
			"Active",
			update_modified=False,
		)
		self.refuses("NDS_UNIT_INELIGIBLE", unit="UNIT-PROGRAMME")

	def test_a_missing_required_by_date_is_refused(self):
		self.refuses("NDS_FIELD_REQUIRED", required_by_date=None)

	def test_a_required_by_date_outside_the_target_year_is_refused(self):
		# NDS-AC-005 — the Need is raised against one financial year, so a date
		# outside it would arrive in Planning as un-plannable in its own year.
		self.refuses("NDS_REQUIRED_BY_OUTSIDE_FY", required_by_date="2030-01-31")

	def test_a_complete_draft_submits(self):
		# The control: without this, every assertion above could pass because
		# submission is broken rather than because validation works.
		submitted = self.submit(self.save_draft())
		self.assertEqual(submitted["current_state"], STATE_SUBMITTED)


class TestCommandControls(DepartmentalNeedsCommandCase):
	"""§5.4 NDS-BR-018 / NDS-AC-028."""

	def test_a_stale_record_version_overwrites_nothing(self):
		result = self.create()
		frappe.set_user(AUTHOR)
		with self.assertRaises(DepartmentalNeedError) as caught:
			lifecycle.update_need(
				need=result["need"],
				expected_version=int(result["record_version"]) - 1,
				idempotency_key=self.key(),
				**self.content(title="Should never be written"),
			)
		self.assertEqual(caught.exception.code, "NDS_STALE_WRITE")
		self.assertNotEqual(self.version(result["current_version"]).title, "Should never be written")

	def test_a_stale_decision_token_is_refused(self):
		submitted = self.submit(self.create())
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.decide(submitted, "accept", token="not-the-current-token")
		self.assertEqual(caught.exception.code, "NDS_STALE_WRITE")

	def test_replaying_an_idempotency_key_creates_no_second_decision(self):
		result = self.create()
		key = self.key()
		frappe.set_user(AUTHOR)
		payload = dict(
			need=result["need"],
			expected_version=result["record_version"],
			idempotency_key=key,
			**self.content(title="Saved exactly once"),
		)
		first = lifecycle.update_need(**payload)
		second = lifecycle.update_need(**payload)
		self.assertFalse(first["idempotent"])
		self.assertTrue(second["idempotent"])
		self.assertEqual(
			frappe.db.count("Departmental Need Decision", {"idempotency_key": key}), 1
		)

	def test_replaying_an_accept_creates_no_second_decision_and_no_second_event(self):
		# The highest-consequence replay, and the one the other tests miss: every
		# replay assertion above drives `update_need`, whose worst case is a
		# duplicated Draft save. A repeated *decision* is different in kind — it
		# could accept twice, move `record_version` again, or emit a second
		# `DepartmentalNeedAccepted.v2` that Planning would consume as a fresh
		# acceptance. `review_need` reads the idempotency key before it touches
		# the task, so the replay must return the first result untouched rather
		# than failing on the now-consumed decision token.
		submitted = self.submit(self.create())
		key = self.key()
		frappe.set_user(REVIEWER)
		payload = dict(
			need=submitted["need"],
			decision="accept",
			task=submitted["task"],
			expected_version=submitted["record_version"],
			decision_token=self.token(submitted["task"]),
			idempotency_key=key,
		)
		first = lifecycle.review_need(**payload)
		second = lifecycle.review_need(**payload)
		self.assertFalse(first["idempotent"])
		self.assertTrue(second["idempotent"])
		# The replay reports the same committed state, and commits nothing new.
		self.assertEqual(first["record_version"], second["record_version"])
		self.assertEqual(
			first["current_accepted_version"], second["current_accepted_version"]
		)
		self.assertEqual(
			frappe.db.count("Departmental Need Decision", {"idempotency_key": key}), 1
		)
		self.assertEqual(
			frappe.db.count(
				"Departmental Need Event",
				{
					"departmental_need": submitted["need"],
					"event_type": events.EVENT_ACCEPTED,
				},
			),
			1,
		)
		self.assertEqual(
			frappe.db.count(
				"Departmental Need Review Task",
				{"departmental_need": submitted["need"], "status": TASK_OPEN},
			),
			0,
		)

	def test_replaying_a_successor_accept_supersedes_only_once(self):
		# §5.2 — a replayed successor acceptance is the one replay that could
		# corrupt lineage rather than merely duplicate a row: superseding twice
		# would mark the *successor* superseded by itself and leave Planning's
		# pinned source pointing at a version that no longer reads as accepted.
		accepted = self.accepted()
		frappe.set_user(AUTHOR)
		opened = lifecycle.create_accepted_need_successor(
			need=accepted["need"],
			expected_version=accepted["record_version"],
			idempotency_key=self.key(),
		)
		submitted = self.submit(opened)
		key = self.key()
		frappe.set_user(REVIEWER)
		payload = dict(
			need=submitted["need"],
			decision="accept",
			task=submitted["task"],
			expected_version=submitted["record_version"],
			decision_token=self.token(submitted["task"]),
			idempotency_key=key,
		)
		lifecycle.review_need(**payload)
		replay = lifecycle.review_need(**payload)
		self.assertTrue(replay["idempotent"])
		need = frappe.get_doc("Departmental Need", accepted["need"])
		self.assertEqual(need.current_accepted_version, opened["successor_version"])
		# The successor is accepted, not superseded by its own replay.
		self.assertEqual(self.status_of(opened["successor_version"]), VERSION_ACCEPTED)
		self.assertEqual(
			self.status_of(accepted["current_accepted_version"]), VERSION_SUPERSEDED
		)
		self.assertEqual(
			frappe.db.count(
				"Departmental Need Event",
				{
					"departmental_need": accepted["need"],
					"event_type": events.EVENT_SUPERSEDED,
				},
			),
			1,
		)

	def test_every_decision_records_the_review_task_that_authorised_it(self):
		accepted = self.accepted()
		self.assertEqual(
			frappe.db.get_value(
				"Departmental Need Decision",
				{"departmental_need": accepted["need"], "action": "Accept for planning"},
				"review_task",
			),
			accepted["task"],
		)


class TestAcceptedSuccessorLifecycle(DepartmentalNeedsCommandCase):
	"""§5.2."""

	def successor(self):
		accepted = self.accepted()
		frappe.set_user(AUTHOR)
		return accepted, lifecycle.create_accepted_need_successor(
			need=accepted["need"],
			expected_version=accepted["record_version"],
			idempotency_key=self.key(),
		)

	def test_create_update_copies_the_accepted_version_and_leaves_it_effective(self):
		accepted, opened = self.successor()
		need = frappe.get_doc("Departmental Need", accepted["need"])
		copy = self.version(opened["successor_version"])
		# NDS-AC-016 — the accepted version is untouched and still current.
		self.assertEqual(need.current_state, STATE_ACCEPTED)
		self.assertEqual(need.current_accepted_version, accepted["current_accepted_version"])
		self.assertEqual(self.status_of(need.current_accepted_version), VERSION_ACCEPTED)
		self.assertEqual(copy.version_status, VERSION_DRAFT)
		self.assertEqual(copy.based_on_version, need.current_accepted_version)
		self.assertEqual(need.current_version, copy.name)

	def test_only_one_successor_may_be_open(self):
		accepted, opened = self.successor()
		frappe.set_user(AUTHOR)
		with self.assertRaises(DepartmentalNeedError) as caught:
			lifecycle.create_accepted_need_successor(
				need=accepted["need"],
				expected_version=opened["record_version"],
				idempotency_key=self.key(),
			)
		self.assertEqual(caught.exception.code, "NDS_OPEN_SUCCESSOR_EXISTS")

	def test_saving_an_update_edits_only_the_successor(self):
		accepted, opened = self.successor()
		frappe.set_user(AUTHOR)
		saved = lifecycle.update_need(
			need=accepted["need"],
			expected_version=opened["record_version"],
			idempotency_key=self.key(),
			**self.content(required_by_date="2027-09-15"),
		)
		self.assertEqual(saved["action"], "Save successor")
		self.assertEqual(
			str(self.version(opened["successor_version"]).required_by_date), "2027-09-15"
		)
		self.assertEqual(
			str(self.version(accepted["current_accepted_version"]).required_by_date), "2027-12-31"
		)

	def test_cancelling_an_update_withdraws_only_the_successor(self):
		# NDS-AC-033.
		accepted, opened = self.successor()
		frappe.set_user(AUTHOR)
		cancelled = lifecycle.cancel_accepted_need_successor(
			need=accepted["need"],
			expected_version=opened["record_version"],
			idempotency_key=self.key(),
		)
		need = frappe.get_doc("Departmental Need", accepted["need"])
		self.assertEqual(self.status_of(opened["successor_version"]), VERSION_WITHDRAWN)
		self.assertEqual(need.current_state, STATE_ACCEPTED)
		self.assertEqual(need.current_version, accepted["current_accepted_version"])
		self.assertEqual(cancelled["current_accepted_version"], accepted["current_accepted_version"])

	def test_submitting_an_update_opens_a_successor_task_without_moving_the_root(self):
		accepted, opened = self.successor()
		submitted = self.submit(opened)
		self.assertEqual(submitted["action"], "Submit successor")
		# The earlier accepted version stays effective, so the root does not move.
		self.assertEqual(submitted["current_state"], STATE_ACCEPTED)
		self.assertEqual(
			submitted["current_accepted_version"], accepted["current_accepted_version"]
		)
		self.assertEqual(
			frappe.db.get_value(
				"Departmental Need Review Task", submitted["task"], "task_type"
			),
			TASK_SUCCESSOR_ACCEPTANCE,
		)

	def test_returning_a_successor_copies_a_correction_and_keeps_the_accepted_version(self):
		accepted, opened = self.successor()
		submitted = self.submit(opened)
		returned = self.decide(submitted, "return", reason=REASON)
		need = frappe.get_doc("Departmental Need", accepted["need"])
		self.assertEqual(self.status_of(opened["successor_version"]), VERSION_RETURNED)
		self.assertEqual(self.status_of(returned["successor_version"]), VERSION_DRAFT)
		self.assertEqual(need.current_state, STATE_ACCEPTED)
		self.assertEqual(need.current_accepted_version, accepted["current_accepted_version"])

	def test_accepting_a_successor_atomically_supersedes_the_earlier_version(self):
		# NDS-AC-017.
		accepted, opened = self.successor()
		result = self.decide(self.submit(opened), "accept")
		need = frappe.get_doc("Departmental Need", accepted["need"])
		self.assertEqual(result["action"], ACTION_ACCEPT_SUCCESSOR)
		self.assertEqual(result["superseded_version"], accepted["current_accepted_version"])
		self.assertEqual(
			self.status_of(accepted["current_accepted_version"]), VERSION_SUPERSEDED
		)
		self.assertEqual(need.current_accepted_version, opened["successor_version"])
		self.assertEqual(need.current_version, opened["successor_version"])
		self.assertEqual(self.status_of(opened["successor_version"]), VERSION_ACCEPTED)

	def test_declining_a_successor_leaves_the_earlier_version_current(self):
		# NDS-AC-018.
		accepted, opened = self.successor()
		declined = self.decide(self.submit(opened), "decline", reason=REASON)
		need = frappe.get_doc("Departmental Need", accepted["need"])
		self.assertEqual(self.status_of(opened["successor_version"]), VERSION_NOT_TAKEN_FORWARD)
		self.assertEqual(need.current_state, STATE_ACCEPTED)
		self.assertEqual(need.current_accepted_version, accepted["current_accepted_version"])
		self.assertEqual(need.current_version, accepted["current_accepted_version"])
		self.assertEqual(self.status_of(need.current_accepted_version), VERSION_ACCEPTED)
		self.assertEqual(declined["current_state"], STATE_ACCEPTED)


class TestAcceptedWithdrawalLifecycle(DepartmentalNeedsCommandCase):
	"""§5.3."""

	def requested(self):
		accepted = self.accepted()
		frappe.set_user(AUTHOR)
		return accepted, lifecycle.request_withdrawal(
			need=accepted["need"],
			expected_version=accepted["record_version"],
			idempotency_key=self.key(),
			reason=REASON,
		)

	def decide_withdrawal(self, result, decision: str, *, reason: str = "", token: str = ""):
		frappe.set_user(REVIEWER)
		task = result["task"]
		return lifecycle.decide_withdrawal(
			need=result["need"],
			task=task,
			decision=decision,
			expected_version=result["record_version"],
			decision_token=token or self.token(task),
			idempotency_key=self.key(),
			reason=reason,
		)

	def test_requesting_withdrawal_opens_one_request_and_keeps_the_need_accepted(self):
		accepted, requested = self.requested()
		request = frappe.get_doc("Need Withdrawal Request", requested["withdrawal_request"])
		self.assertEqual(request.status, WITHDRAWAL_AWAITING_REVIEW)
		self.assertEqual(request.accepted_version, accepted["current_accepted_version"])
		self.assertEqual(requested["current_state"], STATE_ACCEPTED)
		self.assertEqual(
			frappe.db.count(
				"Departmental Need Review Task",
				{"departmental_need": accepted["need"], "status": TASK_OPEN},
			),
			1,
		)

	def test_only_one_withdrawal_request_may_be_open(self):
		accepted, requested = self.requested()
		frappe.set_user(AUTHOR)
		with self.assertRaises(DepartmentalNeedError) as caught:
			lifecycle.request_withdrawal(
				need=accepted["need"],
				expected_version=requested["record_version"],
				idempotency_key=self.key(),
				reason=REASON,
			)
		self.assertEqual(caught.exception.code, "NDS_WITHDRAWAL_ALREADY_OPEN")

	def test_the_requester_cannot_decide_their_own_request(self):
		# NDS-AC-019 — maker-checker holds even when the requester is a reviewer.
		maker = self.author_reviewer()
		created = self.create_as(maker)
		frappe.set_user(maker)
		submitted = lifecycle.submit_need(
			need=created["need"],
			expected_version=created["record_version"],
			idempotency_key=self.key(),
		)
		# A second Head of User Department in the same scope accepts it.
		frappe.set_user(ACTING_REVIEWER)
		accepted = lifecycle.review_need(
			need=submitted["need"],
			decision="accept",
			task=submitted["task"],
			expected_version=submitted["record_version"],
			decision_token=self.token(submitted["task"]),
			idempotency_key=self.key(),
		)
		frappe.set_user(maker)
		requested = lifecycle.request_withdrawal(
			need=accepted["need"],
			expected_version=accepted["record_version"],
			idempotency_key=self.key(),
			reason=REASON,
		)
		with self.assertRaises(DepartmentalNeedError) as caught:
			lifecycle.decide_withdrawal(
				need=accepted["need"],
				task=requested["task"],
				decision="approve",
				expected_version=requested["record_version"],
				decision_token=self.token(requested["task"]),
				idempotency_key=self.key(),
			)
		self.assertEqual(caught.exception.code, "NDS_MAKER_CHECKER")

	def test_approve_without_a_plan_dependency_withdraws_the_need(self):
		accepted, requested = self.requested()
		approved = self.decide_withdrawal(requested, "approve")
		self.assertEqual(approved["current_state"], STATE_WITHDRAWN)
		self.assertEqual(approved["withdrawal_status"], "Approved")
		self.assertEqual(
			self.status_of(accepted["current_accepted_version"]), VERSION_WITHDRAWN
		)
		self.assertEqual(
			frappe.db.get_value("Departmental Need Review Task", requested["task"], "status"),
			TASK_COMPLETED,
		)

	def test_a_draft_plan_is_not_an_active_plan_dependency(self):
		"""§5.3 — a Draft or Submitted DPP does not block withdrawal.

		Planning publishes `NeedPlanningUsageChanged.v1` only when an *Active*
		Plan starts or stops representing the version (§7.2), so a Need sitting
		in a Draft DPP has no projection at all — and no dependency.
		"""
		accepted, requested = self.requested()
		self.assertFalse(
			frappe.db.exists(
				"Need Planning Usage Projection", accepted["current_accepted_version"]
			)
		)
		self.assertEqual(self.decide_withdrawal(requested, "approve")["current_state"], STATE_WITHDRAWN)

	def test_an_inclusion_that_planning_later_clears_stops_blocking(self):
		accepted, requested = self.requested()
		self.include_in_active_plan(accepted["need"], accepted["current_accepted_version"])
		self.clear_from_active_plan(accepted["need"], accepted["current_accepted_version"])
		self.assertEqual(self.decide_withdrawal(requested, "approve")["current_state"], STATE_WITHDRAWN)

	def test_approve_is_blocked_while_an_active_plan_dependency_exists(self):
		accepted, requested = self.requested()
		self.include_in_active_plan(accepted["need"], accepted["current_accepted_version"])
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.decide_withdrawal(requested, "approve")
		self.assertEqual(caught.exception.code, "NDS_ACTIVE_PLAN_DEPENDENCY")
		self.assertEqual(
			frappe.db.get_value("Departmental Need", accepted["need"], "current_state"),
			STATE_ACCEPTED,
		)

	def test_evaluate_moves_the_request_to_awaiting_planning_clearance(self):
		accepted, requested = self.requested()
		self.include_in_active_plan(accepted["need"], accepted["current_accepted_version"])
		evaluated = self.decide_withdrawal(requested, "evaluate")
		self.assertEqual(evaluated["action"], ACTION_EVALUATE_WITHDRAWAL)
		self.assertEqual(evaluated["withdrawal_status"], WITHDRAWAL_AWAITING_CLEARANCE)
		self.assertEqual(evaluated["current_state"], STATE_ACCEPTED)
		# The request is not resolved, so its task stays open for the next decision.
		self.assertEqual(
			frappe.db.get_value("Departmental Need Review Task", requested["task"], "status"),
			TASK_OPEN,
		)

	def test_re_evaluating_while_still_included_changes_no_state(self):
		accepted, requested = self.requested()
		self.include_in_active_plan(accepted["need"], accepted["current_accepted_version"])
		evaluated = self.decide_withdrawal(requested, "evaluate")
		again = self.decide_withdrawal(evaluated, "evaluate")
		self.assertEqual(again["action"], ACTION_REEVALUATE_WITHDRAWAL)
		self.assertEqual(again["withdrawal_status"], WITHDRAWAL_AWAITING_CLEARANCE)
		self.assertEqual(again["current_state"], STATE_ACCEPTED)

	def test_approve_succeeds_once_planning_clears_the_inclusion(self):
		accepted, requested = self.requested()
		self.include_in_active_plan(accepted["need"], accepted["current_accepted_version"])
		evaluated = self.decide_withdrawal(requested, "evaluate")
		# Planning clears the inclusion through its own governed route and
		# publishes NeedPlanningUsageChanged.v1.
		self.clear_from_active_plan(accepted["need"], accepted["current_accepted_version"])
		approved = self.decide_withdrawal(evaluated, "approve")
		self.assertEqual(approved["current_state"], STATE_WITHDRAWN)
		self.assertEqual(approved["withdrawal_status"], "Approved")

	def test_decline_requires_a_reason_and_leaves_the_need_accepted(self):
		accepted, requested = self.requested()
		with self.assertRaises(DepartmentalNeedError) as caught:
			self.decide_withdrawal(requested, "decline")
		self.assertEqual(caught.exception.code, "NDS_FIELD_REQUIRED")
		declined = self.decide_withdrawal(requested, "decline", reason=REASON)
		self.assertEqual(declined["withdrawal_status"], WITHDRAWAL_DECLINED)
		self.assertEqual(declined["current_state"], STATE_ACCEPTED)
		self.assertEqual(
			self.status_of(accepted["current_accepted_version"]), VERSION_ACCEPTED
		)


class TestSuccessorReachesTheReviewQueue(DepartmentalNeedsCommandCase):
	"""§12.2 — a submitted successor must appear in the reviewer's queue.

	NDS-UI-02's queue is the only route to NDS-UI-05 (§10 gives the task screen
	no menu entry of its own), so an action derived from the root Need state
	strands the whole successor lifecycle: §5.2 deliberately holds the root at
	`Accepted for planning` while the successor is under review, exactly so the
	earlier accepted version stays effective for Planning.

	Built through the real commands rather than the §14.5 `successor` seed
	profile, which drives supersession all the way to Accepted and so never
	leaves an open task to find.
	"""

	def submitted_successor(self):
		accepted = self.accepted()
		frappe.set_user(AUTHOR)
		opened = lifecycle.create_accepted_need_successor(
			need=accepted["need"],
			expected_version=accepted["record_version"],
			idempotency_key=self.key(),
		)
		saved = lifecycle.update_need(
			need=accepted["need"],
			expected_version=opened["record_version"],
			idempotency_key=self.key(),
			**self.content(required_by_date="2027-09-15"),
		)
		submitted = lifecycle.submit_need(
			need=accepted["need"],
			expected_version=saved["record_version"],
			idempotency_key=self.key(),
		)
		frappe.set_user("Administrator")
		return accepted, submitted

	def reviewer_row(self, need: str) -> dict:
		frappe.set_user(REVIEWER)
		try:
			result = workspace.get_workspace(
				user=REVIEWER, procuring_entity=PE, organisation_unit=OU_DIGITAL_HEALTH
			)
		finally:
			frappe.set_user("Administrator")
		reference = frappe.db.get_value("Departmental Need", need, "need_reference")
		rows = [row for row in result["needs"] if row["reference"] == reference]
		self.assertEqual(len(rows), 1, msg=f"{reference} missing from the reviewer's rows")
		return rows[0]

	def test_the_root_stays_accepted_while_the_successor_waits(self):
		accepted, _ = self.submitted_successor()
		need = frappe.get_doc("Departmental Need", accepted["need"])
		self.assertEqual(need.current_state, STATE_ACCEPTED)
		self.assertEqual(
			frappe.db.get_value(
				"Departmental Need Review Task",
				{"departmental_need": need.name, "status": TASK_OPEN},
				"task_type",
			),
			"Successor acceptance",
		)

	def test_the_reviewer_is_offered_the_open_successor_decision(self):
		accepted, _ = self.submitted_successor()
		row = self.reviewer_row(accepted["need"])
		self.assertEqual(row["actions"][0]["code"], "review")
		self.assertTrue(row["actions"][0]["task"], msg="the action must carry its task")

	def test_the_author_who_submitted_it_is_offered_no_decision(self):
		"""NDS-AC-010 — maker-checker survives the change of derivation."""
		accepted, _ = self.submitted_successor()
		frappe.set_user(AUTHOR)
		try:
			result = workspace.get_workspace(
				user=AUTHOR, procuring_entity=PE, organisation_unit=OU_DIGITAL_HEALTH
			)
		finally:
			frappe.set_user("Administrator")
		reference = frappe.db.get_value("Departmental Need", accepted["need"], "need_reference")
		row = next(row for row in result["needs"] if row["reference"] == reference)
		self.assertNotIn("review", {action["code"] for action in row["actions"]})
