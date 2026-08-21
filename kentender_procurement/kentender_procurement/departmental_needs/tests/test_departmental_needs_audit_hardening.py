from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.financial_context import enabled_fiscal_years
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	OU, PE, REQUESTER, REVIEWER, upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services.lifecycle import create_need, review_need, submit_need


class TestDepartmentalNeedsAuditHardening(IntegrationTestCase):
	"""NDS-CHG-002 Phase 8 (NDC-801..803): §8.4 audit-event field capture,
	the maker-checker self-decision guard (NDS-FR-031/AC-028), and the
	resubmission-revision contract (NDS-FR-033/AC-030)."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def _key(self, label: str) -> str:
		return f"TEST-NDS-AUDIT-{label}-{uuid4().hex}"

	def _current_fy(self):
		return next(row for row in enabled_fiscal_years() if row["is_current"])

	def _create_and_submit(self, *, user=REQUESTER):
		fy = self._current_fy()
		created = create_need(
			procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"],
			title=f"Audit hardening need {uuid4().hex[:8]}",
			business_justification="Phase 8 audit-hardening regression coverage exercising the full submit-review lifecycle.",
			required_by_date=fy["end_date"], delivery_or_use_location="Digital Health Directorate",
			items=[{"description": "Field kits", "indicative_quantity": 5, "unit_code": "Set"}],
			idempotency_key=self._key("CREATE"), user=user,
		)
		submitted = submit_need(need=created["need"], expected_token=created["concurrency_token"], idempotency_key=self._key("SUBMIT"), user=user)
		return created, submitted

	# NDC-802 — NDS-FR-031/AC-028: a submitter cannot make the departmental
	# decision on their own Need, as a direct assertion (not merely untested
	# because no task exists — the guard fires before any task lookup).
	def test_submitter_cannot_review_own_need(self):
		created, submitted = self._create_and_submit()
		with self.assertRaises(DepartmentalNeedError) as ctx:
			review_need(
				need=created["need"], decision="accept", task=submitted["task"],
				expected_token=submitted["concurrency_token"], task_token="",
				idempotency_key=self._key("SELF-REVIEW"), user=REQUESTER,
			)
		self.assertEqual(ctx.exception.code, "NDS_SELF_REVIEW_NOT_ALLOWED")
		# A true no-op: status is unchanged, no new review event recorded beyond
		# the Create + Submit pair _create_and_submit() itself already made.
		self.assertEqual(frappe.db.get_value("Departmental Need", created["need"], "status"), "Submitted")
		self.assertEqual(
			frappe.db.count("Departmental Need Review", {"departmental_need": created["need"]}), 2,
		)

	# NDC-803 — NDS-FR-033/AC-030: resubmission increments revision_no exactly
	# once and the prior (first) Submit snapshot is byte-identical afterwards.
	def test_resubmission_increments_revision_without_modifying_prior_snapshot(self):
		created, submitted = self._create_and_submit()
		self.assertEqual(frappe.db.get_value("Departmental Need", created["need"], "revision_no"), 1)

		first_submit_event = frappe.db.get_value(
			"Departmental Need Review", {"departmental_need": created["need"], "action": "Submit"},
			["review_reference", "prior_state", "result_state", "reason", "actor", "occurred_at", "before_state_hash", "after_state_hash"],
			as_dict=True,
		)
		self.assertIsNotNone(first_submit_event)

		task = frappe.get_doc("Workflow Task", submitted["task"])
		returned = review_need(
			need=created["need"], decision="return", task=submitted["task"],
			expected_token=submitted["concurrency_token"], task_token=task.concurrency_token,
			idempotency_key=self._key("RETURN"), reason="Clarify the delivery timeline before this can proceed to review.",
			user=REVIEWER,
		)
		self.assertEqual(returned["status"], "Returned")

		resubmitted = submit_need(
			need=created["need"], expected_token=returned["concurrency_token"],
			idempotency_key=self._key("RESUBMIT"), user=REQUESTER,
		)
		self.assertEqual(resubmitted["status"], "Submitted")
		self.assertEqual(frappe.db.get_value("Departmental Need", created["need"], "revision_no"), 2)

		# The first Submit event's own snapshot is unchanged by the later Resubmit.
		first_submit_event_after = frappe.db.get_value(
			"Departmental Need Review", {"departmental_need": created["need"], "action": "Submit"},
			["review_reference", "prior_state", "result_state", "reason", "actor", "occurred_at", "before_state_hash", "after_state_hash"],
			as_dict=True,
		)
		self.assertEqual(first_submit_event, first_submit_event_after)
		# A distinct Resubmit event exists alongside it — the history accumulates, it doesn't overwrite.
		self.assertEqual(frappe.db.count("Departmental Need Review", {"departmental_need": created["need"], "action": "Resubmit"}), 1)

	# NDC-801 — §8.4: audit events capture actor, effective assignment, request
	# identifier, source IP/session, scope and before/after state hashes.
	def test_audit_event_captures_section_8_4_fields(self):
		created, submitted = self._create_and_submit()
		event = frappe.db.get_value(
			"Departmental Need Review", {"departmental_need": created["need"], "action": "Submit"},
			["actor", "effective_assignment", "scope", "request_id", "before_state_hash", "after_state_hash"],
			as_dict=True,
		)
		self.assertEqual(event.actor, REQUESTER)
		self.assertTrue(event.effective_assignment, "effective_assignment should record the governed assignment that authorized this Submit.")
		self.assertEqual(event.scope, f"{PE}/{OU}/{self._current_fy()['id']}")
		self.assertTrue(event.request_id, "request_id should never be blank — a console/test context still generates one.")
		self.assertTrue(event.before_state_hash and event.after_state_hash)
		self.assertNotEqual(event.before_state_hash, event.after_state_hash, "Submit changes status/revision_no, so the hash must differ.")
