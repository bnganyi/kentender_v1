"""Phase 5 event tests for NDS-CHG-001 v1.1 §7.

Covers the three published contracts, transactional-outbox delivery that is
idempotent and ordered per Need, and the firm D1 boundary: Procurement Planning
reaches accepted Needs only through the published handoff contract.
"""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_procurement.departmental_needs.constants import STATE_WITHDRAWN
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	AUTHOR,
	FY,
	INTAKE_WINDOW,
	OU_DIGITAL_HEALTH,
	PE,
	REVIEWER,
	upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services import events, lifecycle

# §7.1 — the exact `DepartmentalNeedAccepted.v2` field set, plus event identity.
ACCEPTED_FIELDS = {
	"event_id",
	"event_type",
	"occurred_at",
	"need_id",
	"need_reference",
	"accepted_version_id",
	"version_number",
	"content_hash",
	"procuring_entity_id",
	"org_unit_id",
	"financial_year_id",
	"title",
	"description",
	"expected_operational_result",
	"indicative_quantity",
	"unit_id",
	"unit_display_value",
	"required_by_date",
}

# NDS-AC-024 — none of these may ever appear in a published payload.
EXCLUDED_FIELDS = (
	"budget_line",
	"budget_line_id",
	"indicative_cost",
	"amount",
	"funding_source",
	"currency",
	"strategy",
	"strategic_objective",
	"requirement_type",
	"procurement_method",
	"delivery_or_use_location",
	"location",
	"attachments",
	"source_reference",
	"evidence",
	"notes",
)


class EventCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")
		now = now_datetime()
		frappe.db.set_value(
			"Needs Intake Window",
			INTAKE_WINDOW,
			{"opens_at": add_days(now, -1), "closes_at": add_days(now, 1)},
			update_modified=False,
		)

	def key(self) -> str:
		return f"nds-event-{uuid4().hex}"

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

	def accepted(self, **overrides):
		"""Drive a Need through §5.1 to Accepted for planning."""
		frappe.set_user(AUTHOR)
		created = lifecycle.create_need(
			procuring_entity=PE,
			organisation_unit=OU_DIGITAL_HEALTH,
			financial_year=FY,
			idempotency_key=self.key(),
			**self.content(**overrides),
		)
		submitted = lifecycle.submit_need(
			need=created["need"],
			expected_version=created["record_version"],
			idempotency_key=self.key(),
		)
		frappe.set_user(REVIEWER)
		return lifecycle.review_need(
			need=submitted["need"],
			decision="accept",
			task=submitted["task"],
			expected_version=submitted["record_version"],
			decision_token=self.token(submitted["task"]),
			idempotency_key=self.key(),
		)

	def token(self, task: str) -> str:
		return frappe.db.get_value("Departmental Need Review Task", task, "decision_token")

	def payload_of(self, event_id: str) -> dict:
		return json.loads(frappe.db.get_value("Departmental Need Event", event_id, "payload"))

	def events_for(self, need: str) -> list[dict]:
		return frappe.get_all(
			"Departmental Need Event",
			filters={"departmental_need": need},
			fields=["event_id", "event_type", "sequence", "status"],
			order_by="sequence asc",
		)


class TestAcceptedEvent(EventCase):
	"""§7.1 `DepartmentalNeedAccepted.v2`."""

	def test_acceptance_publishes_exactly_one_event(self):
		result = self.accepted()
		rows = self.events_for(result["need"])
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["event_type"], events.EVENT_ACCEPTED)
		self.assertEqual(rows[0]["event_id"], result["event_id"])

	def test_the_payload_is_exactly_the_seven_one_field_set(self):
		payload = self.payload_of(self.accepted()["event_id"])
		self.assertEqual(set(payload), ACCEPTED_FIELDS)

	def test_the_payload_carries_the_expected_operational_result(self):
		# NDS-AC-038.
		payload = self.payload_of(self.accepted()["event_id"])
		self.assertEqual(
			payload["expected_operational_result"],
			"Facilities can use the deployed digital health services.",
		)

	def test_the_payload_carries_no_excluded_concept(self):
		# NDS-AC-024.
		payload = self.payload_of(self.accepted()["event_id"])
		for excluded in EXCLUDED_FIELDS:
			self.assertNotIn(excluded, payload)

	def test_a_returned_or_declined_version_publishes_nothing(self):
		frappe.set_user(AUTHOR)
		created = lifecycle.create_need(
			procuring_entity=PE,
			organisation_unit=OU_DIGITAL_HEALTH,
			financial_year=FY,
			idempotency_key=self.key(),
			**self.content(),
		)
		submitted = lifecycle.submit_need(
			need=created["need"],
			expected_version=created["record_version"],
			idempotency_key=self.key(),
		)
		frappe.set_user(REVIEWER)
		lifecycle.review_need(
			need=submitted["need"],
			decision="decline",
			task=submitted["task"],
			expected_version=submitted["record_version"],
			decision_token=self.token(submitted["task"]),
			idempotency_key=self.key(),
			reason="The department will meet this requirement from existing stock this year.",
		)
		self.assertEqual(self.events_for(created["need"]), [])


class TestSupersededEvent(EventCase):
	"""§7.1 `DepartmentalNeedSuperseded.v1` / NDS-BR-015."""

	def superseded(self):
		accepted = self.accepted()
		frappe.set_user(AUTHOR)
		opened = lifecycle.create_accepted_need_successor(
			need=accepted["need"],
			expected_version=accepted["record_version"],
			idempotency_key=self.key(),
		)
		# §14.5's successor profile changes the required-by date and nothing
		# else, which is also what makes the two content hashes differ.
		saved = lifecycle.update_need(
			need=opened["need"],
			expected_version=opened["record_version"],
			idempotency_key=self.key(),
			**self.content(required_by_date="2027-09-15"),
		)
		submitted = lifecycle.submit_need(
			need=saved["need"],
			expected_version=saved["record_version"],
			idempotency_key=self.key(),
		)
		frappe.set_user(REVIEWER)
		result = lifecycle.review_need(
			need=submitted["need"],
			decision="accept",
			task=submitted["task"],
			expected_version=submitted["record_version"],
			decision_token=self.token(submitted["task"]),
			idempotency_key=self.key(),
		)
		return accepted, opened, result

	def test_successor_acceptance_publishes_supersession_not_a_second_accepted(self):
		accepted, opened, result = self.superseded()
		rows = self.events_for(result["need"])
		self.assertEqual(
			[row["event_type"] for row in rows],
			[events.EVENT_ACCEPTED, events.EVENT_SUPERSEDED],
		)
		self.assertEqual(rows[-1]["event_id"], result["event_id"])

	def test_the_payload_carries_exact_old_and_new_lineage(self):
		accepted, opened, result = self.superseded()
		payload = self.payload_of(result["event_id"])
		self.assertEqual(
			payload["earlier_accepted_version_id"], accepted["current_accepted_version"]
		)
		self.assertEqual(
			payload["successor_accepted_version_id"], opened["successor_version"]
		)
		self.assertTrue(payload["earlier_content_hash"])
		self.assertTrue(payload["successor_content_hash"])
		self.assertNotEqual(payload["earlier_content_hash"], payload["successor_content_hash"])

	def test_the_payload_embeds_the_successor_accepted_payload(self):
		_, opened, result = self.superseded()
		embedded = self.payload_of(result["event_id"])["successor_accepted_payload"]
		self.assertEqual(embedded["accepted_version_id"], opened["successor_version"])
		for excluded in EXCLUDED_FIELDS:
			self.assertNotIn(excluded, embedded)


class TestWithdrawnEvent(EventCase):
	"""§7.1 `DepartmentalNeedWithdrawn.v1`."""

	def withdrawn(self):
		accepted = self.accepted()
		frappe.set_user(AUTHOR)
		requested = lifecycle.request_withdrawal(
			need=accepted["need"],
			expected_version=accepted["record_version"],
			idempotency_key=self.key(),
			reason="The department no longer requires this equipment in the target year.",
		)
		frappe.set_user(REVIEWER)
		result = lifecycle.decide_withdrawal(
			need=accepted["need"],
			task=requested["task"],
			decision="approve",
			expected_version=requested["record_version"],
			decision_token=self.token(requested["task"]),
			idempotency_key=self.key(),
		)
		return accepted, requested, result

	def test_approved_withdrawal_publishes_the_withdrawn_event(self):
		accepted, requested, result = self.withdrawn()
		self.assertEqual(result["current_state"], STATE_WITHDRAWN)
		rows = self.events_for(result["need"])
		self.assertEqual(
			[row["event_type"] for row in rows],
			[events.EVENT_ACCEPTED, events.EVENT_WITHDRAWN],
		)
		payload = self.payload_of(result["event_id"])
		self.assertEqual(payload["withdrawn_version_id"], accepted["current_accepted_version"])
		self.assertEqual(payload["withdrawal_request_id"], requested["withdrawal_request"])
		self.assertEqual(payload["decided_by"], REVIEWER)

	def test_a_declined_withdrawal_publishes_nothing(self):
		accepted = self.accepted()
		frappe.set_user(AUTHOR)
		requested = lifecycle.request_withdrawal(
			need=accepted["need"],
			expected_version=accepted["record_version"],
			idempotency_key=self.key(),
			reason="The department no longer requires this equipment in the target year.",
		)
		frappe.set_user(REVIEWER)
		lifecycle.decide_withdrawal(
			need=accepted["need"],
			task=requested["task"],
			decision="decline",
			expected_version=requested["record_version"],
			decision_token=self.token(requested["task"]),
			idempotency_key=self.key(),
			reason="The Plan still depends on this requirement for the coming year.",
		)
		types = [row["event_type"] for row in self.events_for(accepted["need"])]
		self.assertEqual(types, [events.EVENT_ACCEPTED])


class TestOutboxDelivery(EventCase):
	"""§7.1 — transactional, idempotent, ordered per Need."""

	def test_events_are_ordered_per_need(self):
		accepted = self.accepted()
		frappe.set_user(AUTHOR)
		requested = lifecycle.request_withdrawal(
			need=accepted["need"],
			expected_version=accepted["record_version"],
			idempotency_key=self.key(),
			reason="The department no longer requires this equipment in the target year.",
		)
		frappe.set_user(REVIEWER)
		lifecycle.decide_withdrawal(
			need=accepted["need"],
			task=requested["task"],
			decision="approve",
			expected_version=requested["record_version"],
			decision_token=self.token(requested["task"]),
			idempotency_key=self.key(),
		)
		rows = self.events_for(accepted["need"])
		self.assertEqual([row["sequence"] for row in rows], [1, 2])

	def test_a_failed_command_leaves_no_event(self):
		# Transactional outbox: the event exists only if the change committed.
		accepted = self.accepted()
		before = len(self.events_for(accepted["need"]))
		frappe.set_user(AUTHOR)
		with self.assertRaises(DepartmentalNeedError):
			# A stale record version: the acceptance must not be repeatable.
			lifecycle.create_accepted_need_successor(
				need=accepted["need"],
				expected_version=int(accepted["record_version"]) - 1,
				idempotency_key=self.key(),
			)
		self.assertEqual(len(self.events_for(accepted["need"])), before)

	def test_consume_returns_pending_events_without_acknowledging_them(self):
		accepted = self.accepted()
		drained = events.consume_events(consumer="procurement_planning", need=accepted["need"])
		self.assertEqual(len(drained["events"]), 1)
		self.assertEqual(drained["events"][0]["event_id"], accepted["event_id"])
		self.assertEqual(
			frappe.db.get_value("Departmental Need Event", accepted["event_id"], "status"),
			"Pending",
		)

	def test_acknowledged_events_are_not_redelivered(self):
		accepted = self.accepted()
		events.acknowledge(consumer="procurement_planning", event_ids=[accepted["event_id"]])
		again = events.consume_events(consumer="procurement_planning", need=accepted["need"])
		self.assertEqual(again["events"], [])
		row = frappe.db.get_value(
			"Departmental Need Event",
			accepted["event_id"],
			["status", "consumer"],
			as_dict=True,
		)
		self.assertEqual((row.status, row.consumer), ("Delivered", "procurement_planning"))

	def test_acknowledging_twice_is_harmless(self):
		accepted = self.accepted()
		first = events.acknowledge(consumer="procurement_planning", event_ids=[accepted["event_id"]])
		second = events.acknowledge(consumer="procurement_planning", event_ids=[accepted["event_id"]])
		self.assertEqual(len(first["acknowledged"]), 1)
		self.assertEqual(second["acknowledged"], [])

	def test_a_published_event_is_immutable(self):
		accepted = self.accepted()
		doc = frappe.get_doc("Departmental Need Event", accepted["event_id"])
		doc.payload = json.dumps({"tampered": True})
		with self.assertRaises(DepartmentalNeedError) as caught:
			doc.save(ignore_permissions=True)
		self.assertEqual(caught.exception.code, "NDS_STATE_CONFLICT")

	def test_current_accepted_events_replays_the_context(self):
		accepted = self.accepted()
		payloads = events.current_accepted_events(procuring_entity=PE, financial_year=FY)
		by_need = {row["need_id"]: row for row in payloads}
		self.assertIn(accepted["need"], by_need)
		self.assertEqual(
			by_need[accepted["need"]]["accepted_version_id"],
			accepted["current_accepted_version"],
		)


class TestPlanningBoundary(EventCase):
	"""Superseded by NDS-910 — see `test_departmental_needs_architecture.py`.

	Phase 5 wrote the D1 boundary guard here, scanning the two Planning files it
	was rewriting at the time and only the Planning → Needs direction. Phase 9
	replaced it with a scan over both packages in full, in both directions: the
	narrow version passed while a deliberate `frappe.get_all("Departmental Need
	Version", ...)` sat in `procurement_planning/services/__init__.py`, one of the
	hundred-odd files it never opened.

	The DEBT-03 closure evidence points at the Phase 5 guard, so this class stays
	as a signpost rather than vanishing from the history.
	"""

	def test_the_boundary_guard_lives_in_the_architecture_module(self):
		from kentender_procurement.departmental_needs.tests import (
			test_departmental_needs_architecture as architecture,
		)

		self.assertTrue(hasattr(architecture, "data_access_violations"))
		self.assertTrue(hasattr(architecture, "import_violations"))
