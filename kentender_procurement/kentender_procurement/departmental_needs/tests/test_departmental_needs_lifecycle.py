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
	INTAKE_CLOSED,
	INTAKE_OPEN,
	INTAKE_SCHEDULED,
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
	INTAKE_WINDOW,
	OU_DIGITAL_HEALTH,
	PE,
	PLANNER,
	REVIEWER,
	upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services import lifecycle
from kentender_procurement.departmental_needs.services.context import intake_window
from kentender_procurement.departmental_needs.services.usage import project_planning_usage

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


class TestNeedsIntakeWindow(DepartmentalNeedsCommandCase):
	"""§4.1 / NDS-AC-003 — derived state with inclusive boundaries."""

	def test_state_is_derived_with_inclusive_boundaries(self):
		frappe.db.set_value(
			"Needs Intake Window",
			INTAKE_WINDOW,
			{"opens_at": "2026-09-01 00:00:00", "closes_at": "2026-11-25 23:59:59"},
			update_modified=False,
		)
		states = {
			at: intake_window(PE, FY, at=at)["state"]
			for at in (
				"2026-08-31 23:59:59",
				"2026-09-01 00:00:00",
				"2026-11-25 23:59:59",
				"2026-11-26 00:00:00",
			)
		}
		self.assertEqual(
			states,
			{
				"2026-08-31 23:59:59": INTAKE_SCHEDULED,
				# Both boundary instants are inside the window.
				"2026-09-01 00:00:00": INTAKE_OPEN,
				"2026-11-25 23:59:59": INTAKE_OPEN,
				"2026-11-26 00:00:00": INTAKE_CLOSED,
			},
		)

	def test_unconfigured_window_reports_rather_than_raises(self):
		window = intake_window(PE, "FY-1999-2000")
		self.assertFalse(window["configured"])
		self.assertEqual(window["state"], "Not configured")


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
