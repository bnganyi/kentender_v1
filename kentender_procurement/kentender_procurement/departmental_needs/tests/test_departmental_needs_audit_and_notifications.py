"""§8.4 audit capture and §8.2 notification effects for NDS-CHG-001 v1.1.

Both surfaces were written in Phase 2 and never asserted. They are grouped here
because they share one property that makes them dangerous: **each is a durable
side effect that no user-visible behaviour depends on.** A Need still submits,
still reviews and still accepts with the audit envelope half-empty or with the
notification silently dropped, so every other test in the module passes either
way.

`notify_need_transition` makes that worse deliberately — it wraps its whole body
in `except Exception: return []` so a notification failure can never roll back a
committed state change (§8.2). That is the right call for the command, and it is
exactly why the recipient rules need direct tests: with the swallow in place, a
broken scope lookup would not raise, would not fail a command, and would not
show up anywhere except an absent row.

The scope assertions use the §14.2 seed's deliberate asymmetry: the substantive
Head of User Department is scoped to **both** organisation units, while the
acting Head is scoped to Digital Health **only**. A Need raised in HRMD must
therefore reach one of them and not the other — the cheapest available proof
that recipients come from User Permission scope rather than from the role name.
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	ACTING_REVIEWER,
	AUTHOR,
	FY,
	OU_DIGITAL_HEALTH,
	OU_HRMD,
	PE,
	PLANNER,
	REVIEWER,
)
from kentender_procurement.departmental_needs.services import lifecycle, notifications
from kentender_procurement.departmental_needs.tests.test_departmental_needs_lifecycle import (
	REASON,
	DepartmentalNeedsCommandCase,
)


class NotificationCase(DepartmentalNeedsCommandCase):
	def recipients(self, need: str, event_type: str) -> list[str]:
		"""Who actually received a Notification Log row for this event.

		Matched on the module's own correlation key rather than on subject text,
		so a copy change cannot quietly empty this assertion.
		"""
		rows = frappe.get_all(
			"Notification Log",
			filters={"document_type": "Departmental Need", "document_name": need},
			fields=["for_user", "email_header"],
			limit_page_length=0,
		)
		prefix = f"kt-nds:{event_type}:"
		return sorted({row.for_user for row in rows if cstr(row.email_header).startswith(prefix)})

	def create_in(self, unit: str):
		frappe.set_user(AUTHOR)
		return lifecycle.create_need(
			procuring_entity=PE,
			organisation_unit=unit,
			financial_year=FY,
			idempotency_key=self.key(),
			**self.content(),
		)


class TestTransitionNotificationRecipients(NotificationCase):
	"""§8.2 — durable notification effects, addressed by native scope (§6)."""

	def test_submission_reaches_the_reviewers_and_not_the_author(self):
		# The author already knows they submitted; the point of the effect is to
		# raise the task with whoever can act on it.
		submitted = self.submit(self.create_in(OU_DIGITAL_HEALTH))
		told = self.recipients(submitted["need"], notifications.EVENT_SUBMITTED)
		self.assertEqual(told, sorted([ACTING_REVIEWER, REVIEWER]))
		self.assertNotIn(AUTHOR, told)

	def test_a_reviewer_scoped_to_another_unit_is_never_told(self):
		# The disclosure case. Both users hold Head of User Department; only one
		# holds an Organisation Unit permission for HRMD. Telling the other would
		# leak the existence and title of another department's Need.
		submitted = self.submit(self.create_in(OU_HRMD))
		told = self.recipients(submitted["need"], notifications.EVENT_SUBMITTED)
		self.assertEqual(told, [REVIEWER])
		self.assertNotIn(ACTING_REVIEWER, told)

	def test_a_decision_goes_back_to_the_author_alone(self):
		accepted = self.accepted()
		told = self.recipients(accepted["need"], notifications.EVENT_ACCEPTED)
		self.assertEqual(told, [AUTHOR])

	def test_a_return_tells_the_author_it_needs_correction(self):
		returned = self.decide(self.submit(self.create()), "return", reason=REASON)
		self.assertEqual(
			self.recipients(returned["need"], notifications.EVENT_RETURNED), [AUTHOR]
		)

	def test_the_planner_is_never_a_recipient_of_a_need_decision(self):
		# NDS-AC-043 — Planning learns of an acceptance through the published
		# event (§7.1), not through a Desk notification addressed to a planner.
		accepted = self.accepted()
		rows = frappe.get_all(
			"Notification Log",
			filters={"document_type": "Departmental Need", "document_name": accepted["need"]},
			pluck="for_user",
		)
		self.assertNotIn(PLANNER, rows)

	def test_replaying_a_command_does_not_notify_twice(self):
		# The correlation key carries the state token, so a replay collapses onto
		# the row the first call wrote rather than re-alerting every reviewer.
		created = self.create_in(OU_DIGITAL_HEALTH)
		key = self.key()
		frappe.set_user(AUTHOR)
		payload = dict(
			need=created["need"],
			expected_version=created["record_version"],
			idempotency_key=key,
		)
		submitted = lifecycle.submit_need(**payload)
		lifecycle.submit_need(**payload)
		self.assertEqual(
			frappe.db.count(
				"Notification Log",
				{
					"document_name": submitted["need"],
					"email_header": (
						"like",
						f"kt-nds:{notifications.EVENT_SUBMITTED}:%:{REVIEWER}",
					),
				},
			),
			1,
		)

	def test_a_failing_notification_never_fails_the_committed_command(self):
		# The `except Exception` swallow is deliberate (§8.2): the state change
		# has already committed, so an alerting fault must not surface as a
		# command failure. Proven directly rather than assumed from reading it.
		created = self.create_in(OU_DIGITAL_HEALTH)
		original = notifications.emit_notification_log

		def explode(**kwargs):
			raise RuntimeError("notification backend unavailable")

		notifications.emit_notification_log = explode
		try:
			submitted = self.submit(created)
		finally:
			notifications.emit_notification_log = original
		self.assertTrue(submitted["ok"])
		self.assertEqual(self.recipients(submitted["need"], notifications.EVENT_SUBMITTED), [])
		# ...and the swallow is scoped to the effect, not to the state change.
		self.assertEqual(
			frappe.db.get_value("Departmental Need", submitted["need"], "current_state"),
			"Submitted",
		)


class TestDecisionAuditCapture(DepartmentalNeedsCommandCase):
	"""§8.4 — every command writes a complete, attributable audit envelope."""

	def envelope(self, need: str, action: str) -> dict:
		return frappe.db.get_value(
			"Departmental Need Decision",
			{"departmental_need": need, "action": action},
			[
				"actor",
				"scope",
				"effective_assignment",
				"correlation_id",
				"request_id",
				"session_id",
				"occurred_at",
				"prior_state",
				"result_state",
				"before_state_hash",
				"after_state_hash",
				"request_fingerprint",
			],
			as_dict=True,
		)

	def test_every_command_records_the_full_audit_envelope(self):
		accepted = self.accepted()
		row = self.envelope(accepted["need"], "Accept for planning")
		# Each of these is written by `_record_decision` and read by nothing the
		# UI depends on, so absence is invisible without this assertion.
		for field in (
			"actor",
			"scope",
			"effective_assignment",
			"correlation_id",
			"request_id",
			"occurred_at",
			"prior_state",
			"result_state",
			"before_state_hash",
			"after_state_hash",
			"request_fingerprint",
		):
			self.assertTrue(cstr(row.get(field)).strip(), f"§8.4 field not captured: {field}")

	def test_the_actor_recorded_is_the_deciding_user_not_the_author(self):
		accepted = self.accepted()
		self.assertEqual(self.envelope(accepted["need"], "Accept for planning").actor, REVIEWER)
		self.assertEqual(self.envelope(accepted["need"], "Submit").actor, AUTHOR)

	def test_the_scope_names_the_needs_own_pe_ou_and_year(self):
		accepted = self.accepted()
		self.assertEqual(
			self.envelope(accepted["need"], "Accept for planning").scope,
			f"{PE}/{OU_DIGITAL_HEALTH}/{FY}",
		)

	def test_the_effective_assignment_names_the_user_permissions_that_authorised_it(self):
		# NDS-AC-042 / §8.4 — the audit records *which native scope rows* carried
		# the authority, so an acting arrangement remains reconstructable after
		# the assignment is revoked and the User Permission rows are gone.
		accepted = self.accepted()
		assignment = self.envelope(accepted["need"], "Accept for planning").effective_assignment
		self.assertEqual(
			sorted(assignment.split(",")),
			sorted(
				[
					f"Financial Year:{FY}",
					f"Organisation Unit:{OU_DIGITAL_HEALTH}",
					f"Procuring Entity:{PE}",
				]
			),
		)

	def test_the_state_hashes_bracket_the_change_rather_than_repeating_it(self):
		# before != after is the whole point: a decision that recorded the same
		# hash twice would prove nothing about what it changed.
		accepted = self.accepted()
		row = self.envelope(accepted["need"], "Accept for planning")
		self.assertNotEqual(row.before_state_hash, row.after_state_hash)
		self.assertEqual(row.prior_state, "Submitted")
		self.assertEqual(row.result_state, "Accepted for planning")

	def test_each_command_in_a_chain_gets_its_own_correlation_id(self):
		accepted = self.accepted()
		ids = {
			action: self.envelope(accepted["need"], action).correlation_id
			for action in ("Create", "Submit", "Accept for planning")
		}
		self.assertEqual(len(set(ids.values())), 3, f"correlation ids collided: {ids}")
