"""My Work projection of open departmental review tasks.

The "Review tasks" sidebar entry NDS-CHG-001 v1.1 §10 specified was a
specification defect (removed 2026-08-30; to be corrected in the next complete
NDS successor): review decisions reach the Head of User Department through the
shared My Work queue and the notification deep link, both landing on the
protected task route. These tests prove the projection end to end:

- `my_work_provider.my_work_rows` mirrors the workspace's §12.2 eligibility
  (HoD role, exact PE/OU/FY scope, maker-checker exclusion);
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
	FY,
	OU_HRMD,
	PE,
	REVIEWER,
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
		# Both hold Head of User Department; only REVIEWER holds an
		# Organisation Unit permission for HRMD (§6). Offering the row to the
		# other would leak the existence of another department's Need.
		frappe.set_user(AUTHOR)
		submitted = self.submit(
			lifecycle.create_need(
				procuring_entity=PE,
				organisation_unit=OU_HRMD,
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
		self.assertEqual(len(self.rows_for(ACTING_REVIEWER, reference)), 1)

	def test_a_non_reviewer_gets_no_rows_at_all(self):
		self.submit(self.create())
		self.assertEqual(self.assigned_for(AUTHOR), [])

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
		returned = self.decide(self.submit(self.create()), "return", reason=REASON)
		reference = frappe.db.get_value("Departmental Need", returned["need"], "need_reference")
		self.assertEqual(
			self.link_for(returned["need"], AUTHOR, notifications.EVENT_RETURNED),
			f"/app/departmental-needs/{reference}",
		)
