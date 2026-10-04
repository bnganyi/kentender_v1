"""My Work projection of open departmental review tasks.

The "Review tasks" sidebar entry NDS-CHG-001 v1.1 §10 specified was a
specification defect (removed 2026-08-30; to be corrected in the next complete
NDS successor): review decisions reach the Head of User Department through the
shared My Work queue and the notification deep link, both landing on the
protected task route. These tests prove the projection end to end:

- `my_work_provider.my_work_rows` mirrors the workspace's §12.2 eligibility
  (HoD business role, exact Organisation Unit scope, maker-checker exclusion);
- kentender_core's `get_my_work` merges the provider rows through the
  `kt_my_work_providers` hook even for a user with no Operational Scope
  Assignment;
- the reviewer's notification links to the exact decision screen.
"""

from __future__ import annotations

import frappe

from kentender_core.services.my_work import get_my_work
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	ACTING_REVIEWER,
	AUTHOR,
	DEPARTMENTAL_AUTHOR,
	FY,
	REVIEWER,
	_granted_units,
)
from kentender_procurement.departmental_needs.services import lifecycle, notifications
from kentender_procurement.departmental_needs.services.my_work_provider import my_work_rows
from kentender_procurement.departmental_needs.tests.test_departmental_needs_lifecycle import (
	REASON,
	DepartmentalNeedsCommandCase,
)


class TestMyWorkProvider(DepartmentalNeedsCommandCase):
	def assigned_for(self, user: str) -> list[dict]:
		return my_work_rows(user=user)["assigned"]

	def rows_for(self, user: str, need: str) -> list[dict]:
		return [row for row in self.assigned_for(user) if row["reference"] == need]

	def reference(self, result) -> str:
		return frappe.db.get_value("Departmental Need", result["need"], "need_reference")

	def test_an_open_task_reaches_the_in_scope_reviewer_with_the_exact_route(self):
		submitted = self.submit(self.create())
		reference = self.reference(submitted)
		rows = self.rows_for(REVIEWER, reference)
		self.assertEqual(len(rows), 1)
		row = rows[0]
		self.assertEqual(row["route"], ["departmental-needs", "review", submitted["task"]])
		self.assertEqual(row["module"], "Departmental Needs")
		self.assertEqual(row["action_label"], "Review need")
		self.assertFalse(row["can_claim"])
		self.assertTrue(row["can_open"])

	def test_a_decided_task_leaves_the_queue(self):
		submitted = self.submit(self.create())
		reference = self.reference(submitted)
		self.assertEqual(len(self.rows_for(REVIEWER, reference)), 1)
		self.decide(submitted, "accept")
		self.assertEqual(self.rows_for(REVIEWER, reference), [])

	def test_an_out_of_scope_reviewer_is_never_offered_the_task(self):
		# Both hold Head of User Department somewhere; only REVIEWER holds a
		# grant for HRMD (§6). Offering the row to the other would leak the
		# existence of another department's Need. ACTING_REVIEWER's only
		# grant is Digital Health (Acting), so she is out of scope for HRMD
		# regardless of whether that Acting period is currently effective.
		ou_hrmd = _granted_units(AUTHOR, DEPARTMENTAL_AUTHOR)["Human Resources Management and Development"]
		frappe.set_user(AUTHOR)
		submitted = self.submit(
			lifecycle.create_need(
				organisation_unit=ou_hrmd,
				financial_year=FY,
				idempotency_key=self.key(),
				**self.content(),
			)
		)
		reference = self.reference(submitted)
		self.assertEqual(len(self.rows_for(REVIEWER, reference)), 1)
		self.assertEqual(self.rows_for(ACTING_REVIEWER, reference), [])

	def test_the_author_never_reviews_their_own_submission(self):
		# NDS-AC-042 maker-checker: the reviewer who also authored this Need
		# gets no My Work row for it, exactly as the workspace offers no action.
		user = self.author_reviewer()
		second = self.second_reviewer()
		created = self.create_as(user)
		# The shared submit() helper hard-sets the seeded AUTHOR; this Need's
		# author is the reviewer, so submit inline as them.
		frappe.set_user(user)
		submitted = lifecycle.submit_need(
			need=created["need"],
			expected_version=created["record_version"],
			idempotency_key=self.key(),
		)
		reference = self.reference(submitted)
		self.assertEqual(self.rows_for(user, reference), [])
		self.assertEqual(len(self.rows_for(second, reference)), 1)

	def test_a_non_reviewer_gets_no_review_row(self):
		# v1.15 §7.6: the author now has their own waiting-on item for this
		# Need, but never a decision row.
		reference = self.reference(self.submit(self.create()))
		self.assertEqual(self.rows_for(AUTHOR, reference), [])

	def test_a_technical_reader_gets_no_rows_even_though_frappe_projects_every_role(self):
		# KT-STD-001 v1.5 §3A.6 / AUTH-ADR-001 §8 — Administrator decides
		# nothing, so My Work must stay empty even though `frappe.get_roles`
		# projects every role (including Head of User Department) onto them,
		# which would otherwise let the role check alone pass it through.
		self.submit(self.create())
		self.assertEqual(self.assigned_for("Administrator"), [])

	def test_get_my_work_merges_the_provider_rows_for_a_role_assigned_reviewer(self):
		# The reviewer holds no Operational Scope Assignment, so without the
		# provider hook My Work would answer NO_ACTIVE_OPERATIONAL_ASSIGNMENT.
		submitted = self.submit(self.create())
		reference = self.reference(submitted)
		frappe.set_user(REVIEWER)
		result = get_my_work()
		self.assertEqual(result["state"], "ready")
		rows = [row for row in result["buckets"]["assigned"] if row["reference"] == reference]
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["route"], ["departmental-needs", "review", submitted["task"]])


class TestAuthorHandoffs(DepartmentalNeedsCommandCase):
	"""NDS-CHG-001 v1.15 §7.6 — the author's side of each hand-off."""

	def rows(self, user: str, bucket: str, reference: str) -> list[dict]:
		return [row for row in my_work_rows(user=user)[bucket] if row["reference"] == reference]

	def reference(self, result) -> str:
		return frappe.db.get_value("Departmental Need", result["need"], "need_reference")

	def test_a_submitted_need_is_the_authors_waiting_item_until_the_decision(self):
		submitted = self.submit(self.create())
		reference = self.reference(submitted)
		[row] = self.rows(AUTHOR, "waiting", reference)
		self.assertEqual(row["title"], "Waiting for Head of Department review")
		self.assertEqual(row["status"], "Waiting")
		self.assertEqual(row["route"], ["departmental-needs", reference])
		self.assertEqual(row["holder"]["role"], "Head of User Department")
		self.assertTrue(row["since"]["display"])
		self.assertFalse(row["can_open"])
		self.assertEqual(self.rows(AUTHOR, "assigned", reference), [])
		self.decide(submitted, "accept")
		self.assertEqual(self.rows(AUTHOR, "waiting", reference), [])

	def test_a_returned_need_is_the_authors_correction_with_the_reason(self):
		returned = self.decide(self.submit(self.create()), "return", reason=REASON)
		reference = self.reference(returned)
		[row] = self.rows(AUTHOR, "assigned", reference)
		self.assertEqual(row["title"], f"Correct and resubmit {self.content()['title']}")
		self.assertEqual(row["stage"], REASON)
		self.assertEqual(row["route"], ["departmental-needs", reference, "edit"])
		self.assertEqual(row["action_label"], "Correct need")
		self.assertRegex(row["received_at"], r"^\d{1,2} [A-Z][a-z]{2} \d{4}, \d{2}:\d{2} EAT$", "never a raw timestamp")
		self.assertTrue(row["can_open"])
		self.assertEqual(self.rows(AUTHOR, "waiting", reference), [])
		# The reviewer who returned it has nothing left for this Need.
		self.assertEqual(self.rows(REVIEWER, "assigned", reference), [])

	def test_a_requested_withdrawal_waits_on_the_decision(self):
		accepted = self.accepted()
		reference = self.reference(accepted)
		self.assertEqual(self.rows(AUTHOR, "waiting", reference), [])
		frappe.set_user(AUTHOR)
		lifecycle.request_withdrawal(
			need=accepted["need"],
			expected_version=accepted["record_version"],
			idempotency_key=self.key(),
			reason=REASON,
		)
		[row] = self.rows(AUTHOR, "waiting", reference)
		self.assertIn(row["title"], ("Waiting for the withdrawal decision", "Waiting for a Planning change"))


class TestReviewerNotificationRoute(DepartmentalNeedsCommandCase):
	def link_for(self, need: str, user: str, event_type: str) -> str:
		prefix = f"kt-nds:{event_type}:"
		rows = frappe.get_all(
			"Notification Log",
			filters={"document_type": "Departmental Need", "document_name": need, "for_user": user},
			fields=["link", "email_header"],
			limit_page_length=0,
		)
		links = [row.link for row in rows if (row.email_header or "").startswith(prefix)]
		self.assertEqual(len(links), 1)
		return links[0]

	def test_the_submission_notification_lands_on_the_decision_screen(self):
		submitted = self.submit(self.create())
		self.assertEqual(
			self.link_for(submitted["need"], REVIEWER, notifications.EVENT_SUBMITTED),
			f"/app/departmental-needs/review/{submitted['task']}",
		)

	def test_the_withdrawal_notification_lands_on_the_withdrawal_screen(self):
		accepted = self.accepted()
		frappe.set_user(AUTHOR)
		requested = lifecycle.request_withdrawal(
			need=accepted["need"],
			expected_version=accepted["record_version"],
			idempotency_key=self.key(),
			reason=REASON,
		)
		self.assertEqual(
			self.link_for(accepted["need"], REVIEWER, notifications.EVENT_WITHDRAWAL_REQUESTED),
			f"/app/departmental-needs/review/{requested['task']}/withdrawal",
		)

	def test_an_author_notification_still_opens_the_record(self):
		"""§12.1 — "Correct routes to the actor's editable current version": the
		author's return notification lands on the correction editor, not a
		read-only detail of the returned root (notifications.py's own
		documented reason for the /edit suffix — this test's own expectation
		was stale against that, pre-dating the single-sheet routing scheme
		where DepartmentalNeeds.vue's `screen` resolver maps a trailing "edit"
		segment to the editor)."""
		returned = self.decide(self.submit(self.create()), "return", reason=REASON)
		reference = frappe.db.get_value("Departmental Need", returned["need"], "need_reference")
		self.assertEqual(
			self.link_for(returned["need"], AUTHOR, notifications.EVENT_RETURNED),
			f"/app/departmental-needs/{reference}/edit",
		)
