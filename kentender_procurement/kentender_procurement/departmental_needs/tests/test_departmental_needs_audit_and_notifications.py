"""§8.4 audit capture and §8.2 notification effects for NDS-CHG-001 v1.6.

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

The scope assertions use a deliberate asymmetry: REVIEWER (Peter) holds Head of
User Department in **both** Organisation Units the fixture Needs live in
(NDS-CHG-001 v1.6 §14.2), while a second, test-local Head of User Department is
granted **Digital Health only**. A Need raised in HRMD must therefore reach
Peter and not the other — the cheapest available proof that recipients come
from a real `User Responsibility Assignment` scope, never from the role name
alone. `ACTING_REVIEWER` (Julia) is deliberately not used for this: her real
Acting grant is effective only 1 Oct-30 Nov 2026 (§14.2), so a notification
count that depended on it would only pass during that window.
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_core.services.responsibility_administration import grant
from kentender_procurement.departmental_needs.constants import ROLE_HEAD_OF_USER_DEPARTMENT
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	ACTING_REVIEWER,
	AUTHOR,
	DEPARTMENTAL_AUTHOR,
	FY,
	PLANNER,
	REVIEWER,
	_granted_units,
)
from kentender_procurement.departmental_needs.services import lifecycle, notifications
from kentender_procurement.departmental_needs.tests.test_departmental_needs_lifecycle import (
	REASON,
	NS_TEST_GRANT,
	DepartmentalNeedsCommandCase,
)

# A second Head of User Department, Digital Health only — distinct from both
# REVIEWER (who holds it in both units) and AUTHOR (the fixture Need's owner,
# so reusing DepartmentalNeedsCommandCase.second_reviewer() here would make
# the author their own reviewer and defeat the "not the author" assertion).
SECOND_HOD = "nds.test.second.hod@example.test"


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
			organisation_unit=unit,
			financial_year=FY,
			idempotency_key=self.key(),
			**self.content(),
		)

	def ensure_second_hod(self) -> str:
		if not frappe.db.exists("User", SECOND_HOD):
			doc = frappe.get_doc(
				{
					"doctype": "User",
					"email": SECOND_HOD,
					"first_name": "Second",
					"last_name": "Reviewer",
					"send_welcome_email": 0,
					"user_type": "System User",
					"enabled": 1,
				}
			)
			doc.insert(ignore_permissions=True)
			doc.add_roles("Desk User")
		grant(
			user=SECOND_HOD,
			business_role=ROLE_HEAD_OF_USER_DEPARTMENT,
			organisation_unit=self.ou,
			fixture_namespace=NS_TEST_GRANT,
			actor="Administrator",
		)
		return SECOND_HOD


class TestTransitionNotificationRecipients(NotificationCase):
	"""§8.2 — durable notification effects, addressed by real scope (§6)."""

	def test_submission_reaches_the_reviewers_and_not_the_author(self):
		# The author already knows they submitted; the point of the effect is to
		# raise the task with whoever can act on it.
		second = self.ensure_second_hod()
		submitted = self.submit(self.create_in(self.ou))
		told = self.recipients(submitted["need"], notifications.EVENT_SUBMITTED)
		self.assertEqual(told, sorted([REVIEWER, second]))
		self.assertNotIn(AUTHOR, told)

	def test_a_reviewer_scoped_to_another_unit_is_never_told(self):
		# The disclosure case. REVIEWER and ACTING_REVIEWER both hold Head of
		# User Department somewhere; only REVIEWER holds it for HRMD (KT-STD-001
		# §8.3's own Cartesian-product fixture also gives AUTHOR — the Need's
		# own owner — Head of User Department there, independent of this
		# submission's authorship: `_reviewers()` scans by real scope, not by
		# excluding the owner, so she is correctly told about it too, in her
		# reviewer capacity). Telling ACTING_REVIEWER would leak the existence
		# and title of another department's Need.
		ou_hrmd = _granted_units(AUTHOR, DEPARTMENTAL_AUTHOR)["Human Resources Management and Development"]
		submitted = self.submit(self.create_in(ou_hrmd))
		told = self.recipients(submitted["need"], notifications.EVENT_SUBMITTED)
		self.assertEqual(told, sorted([AUTHOR, REVIEWER]))
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
		created = self.create_in(self.ou)
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
		created = self.create_in(self.ou)
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

	def test_the_scope_names_the_needs_own_organisation_unit_and_year(self):
		# AUTH-ADR-001 v1.6 §1.1 — the site is exactly one implicit Procuring
		# Entity, so the scope string carries no PE segment any more.
		accepted = self.accepted()
		self.assertEqual(
			self.envelope(accepted["need"], "Accept for planning").scope,
			f"{self.ou}/{FY}",
		)

	def test_the_effective_assignment_names_the_authorising_ura(self):
		# AUTH-ADR-001 v1.6 §15 — the audit records the exact User
		# Responsibility Assignment that authorised the decision, so an
		# acting arrangement remains reconstructable after the assignment is
		# later revoked.
		accepted = self.accepted()
		assignment = self.envelope(accepted["need"], "Accept for planning").effective_assignment
		row = frappe.db.get_value(
			"User Responsibility Assignment",
			assignment,
			["user", "business_role", "organisation_unit", "status"],
			as_dict=True,
		)
		self.assertEqual(row.user, REVIEWER)
		self.assertEqual(row.business_role, ROLE_HEAD_OF_USER_DEPARTMENT)
		self.assertEqual(row.organisation_unit, self.ou)
		self.assertEqual(row.status, "Enabled")

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
