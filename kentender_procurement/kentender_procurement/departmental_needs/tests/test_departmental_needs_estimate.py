"""NDS-CHG-001 v1.17 — the Need's estimated total cost (NDS17-AC-001 to 010).

One required, immutable amount: exact at the Budget currency's precision,
frozen with the revision, copied into the next Draft, carried on
`DepartmentalNeedAccepted.v3`, and absent (null) on a revision that predates
it. It is a requirement fact, not a funding specification: no currency, Budget
Line or funding source is stored with it.
"""

from __future__ import annotations

import json
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.command_write_guard import command_write
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	AUTHOR,
	DEPARTMENTAL_AUTHOR,
	FY,
	REVIEWER,
	_granted_units,
	upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services import estimate, events, lifecycle, workspace
from kentender_procurement.departmental_needs.services.events import LEGACY_EVENT_ACCEPTED
from kentender_procurement.departmental_needs.services.quantity import normalise_wire_payload
from kentender_procurement.departmental_needs.tests import support
from kentender_procurement.departmental_needs.write_family import NEEDS_WRITE_FAMILY


class EstimateCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()
		support.ensure_transitional_reviewer_grant(cls)
		cls.ou = _granted_units(AUTHOR, DEPARTMENTAL_AUTHOR)["Digital Health"]

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")

	def key(self) -> str:
		return f"nds-estimate-{uuid4().hex}"

	def content(self, **overrides):
		values = {
			"title": "Clinical deployment laptops for rollout",
			"description": "Laptop computers for deployment at priority health facilities.",
			"expected_operational_result": "Facilities can use the deployed digital health services.",
			"indicative_quantity": 10,
			"unit": "Each",
			"estimated_total_cost": 1500000,
			"required_by_date": "2027-12-31",
		}
		values.update(overrides)
		return values

	def create(self, **overrides):
		frappe.set_user(AUTHOR)
		return lifecycle.create_need(
			organisation_unit=self.ou, financial_year=FY, idempotency_key=self.key(), **self.content(**overrides)
		)

	def submit(self, created):
		return lifecycle.submit_need(
			need=created["need"], expected_version=created["record_version"], idempotency_key=self.key()
		)

	def accept(self, submitted):
		frappe.set_user(REVIEWER)
		token = frappe.db.get_value("Departmental Need Review Task", submitted["task"], "decision_token")
		return lifecycle.review_need(
			need=submitted["need"], decision="accept", task=submitted["task"],
			expected_version=submitted["record_version"], decision_token=token, idempotency_key=self.key(),
		)

	def accepted(self, **overrides):
		return self.accept(self.submit(self.create(**overrides)))

	def revision(self, need):
		return frappe.get_doc("Departmental Need Revision", frappe.db.get_value("Departmental Need", need, "current_revision"))

	def refuses(self, code, fn):
		with self.assertRaises(DepartmentalNeedError) as caught:
			fn()
		self.assertEqual(caught.exception.code, code)


class TestRequiredAtSubmission(EstimateCase):
	def test_a_draft_saves_without_an_estimate(self):
		created = self.create(estimated_total_cost=None)
		self.assertIsNone(estimate.wire_text(self.revision(created["need"]).estimated_total_cost))

	def test_submission_requires_an_estimate(self):
		created = self.create(estimated_total_cost=None)
		self.refuses("NDS_FIELD_REQUIRED", lambda: self.submit(created))
		self.assertEqual(frappe.db.get_value("Departmental Need", created["need"], "current_state"), "Draft")

	def test_a_zero_or_negative_estimate_is_refused_at_save(self):
		for bad in (0, -5, "-1"):
			self.refuses("NDS_ESTIMATE_PRECISION_INVALID", lambda bad=bad: self.create(estimated_total_cost=bad))

	def test_excess_precision_and_non_numbers_are_refused_not_rounded(self):
		self.refuses("NDS_ESTIMATE_PRECISION_INVALID", lambda: self.create(estimated_total_cost="100.005"))
		self.refuses("NDS_ESTIMATE_PRECISION_INVALID", lambda: self.create(estimated_total_cost="ten"))
		self.refuses("NDS_ESTIMATE_PRECISION_INVALID", lambda: self.create(estimated_total_cost="1e6"))

	def test_an_amount_at_the_currency_precision_is_exact(self):
		created = self.create(estimated_total_cost="1234567.89")
		self.assertEqual(estimate.wire_text(self.revision(created["need"]).estimated_total_cost), "1234567.89")

	def test_an_unreadable_currency_blocks_the_estimate_and_changes_nothing(self):
		from unittest import mock

		from kentender_procurement.services.budget_currency import BudgetCurrencyUnavailable

		with mock.patch.object(estimate, "currency_basis", side_effect=BudgetCurrencyUnavailable("none")):
			self.refuses("NDS_ESTIMATE_CURRENCY_UNAVAILABLE", lambda: self.create())


class TestImmutabilityAndCopy(EstimateCase):
	def test_the_estimate_is_frozen_once_the_revision_is_submitted(self):
		created = self.create()
		self.submit(created)
		revision = self.revision(created["need"])
		revision.estimated_total_cost = 9999999
		with self.assertRaises(DepartmentalNeedError) as caught, command_write(NEEDS_WRITE_FAMILY):
			revision.save(ignore_permissions=True)
		self.assertEqual(caught.exception.code, "NDS_STATE_CONFLICT")

	def test_acceptance_retains_it_and_a_successor_starts_as_a_copy(self):
		accepted = self.accepted(estimated_total_cost=2500000)
		need = accepted["need"]
		frappe.set_user(AUTHOR)
		opened = lifecycle.create_accepted_need_successor(
			need=need, expected_version=frappe.db.get_value("Departmental Need", need, "record_version"),
			idempotency_key=self.key(),
		)
		successor = frappe.get_doc("Departmental Need Revision", opened["current_revision"] if "current_revision" in opened else frappe.db.get_value("Departmental Need", need, "current_revision"))
		self.assertEqual(estimate.wire_text(successor.estimated_total_cost), "2500000")
		accepted_revision = frappe.get_doc("Departmental Need Revision", frappe.db.get_value("Departmental Need", need, "current_accepted_revision"))
		self.assertEqual(estimate.wire_text(accepted_revision.estimated_total_cost), "2500000")

	def test_a_returned_correction_starts_as_a_copy(self):
		submitted = self.submit(self.create(estimated_total_cost=3000000))
		frappe.set_user(REVIEWER)
		token = frappe.db.get_value("Departmental Need Review Task", submitted["task"], "decision_token")
		returned = lifecycle.review_need(
			need=submitted["need"], decision="return", task=submitted["task"], expected_version=submitted["record_version"],
			decision_token=token, idempotency_key=self.key(), reason="Please confirm the number of units and the estimate.",
		)
		copy = frappe.get_doc("Departmental Need Revision", returned["successor_revision"])
		self.assertEqual(estimate.wire_text(copy.estimated_total_cost), "3000000")


class TestHashAndLegacy(EstimateCase):
	def test_the_hash_covers_the_estimate_only_when_present(self):
		with_estimate = self.revision(self.create(estimated_total_cost=1000000)["need"])
		self.assertIn("estimated_total_cost", lifecycle._content_payload(with_estimate))
		without = self.revision(self.create(estimated_total_cost=None)["need"])
		self.assertNotIn("estimated_total_cost", lifecycle._content_payload(without))

	def test_a_pre_v1_17_hash_still_verifies_at_acceptance(self):
		"""A revision submitted before v1.17 has no estimate; its stored hash was
		computed over the six facts and must still verify (NDS17-AC-004)."""
		created = self.create(estimated_total_cost=1000000)
		submitted = self.submit(created)
		revision = self.revision(created["need"])
		# emulate a revision from before the field: no estimate, original six-fact hash
		frappe.db.set_value("Departmental Need Revision", revision.name, "estimated_total_cost", 0, update_modified=False)
		revision.reload()
		legacy = lifecycle._content_hash(revision)
		frappe.db.set_value("Departmental Need Revision", revision.name, "content_hash", legacy, update_modified=False)
		accepted = self.accept(submitted)
		self.assertTrue(accepted.get("event_id"))
		event = json.loads(frappe.db.get_value("Departmental Need Event", accepted["event_id"], "payload"))
		self.assertIsNone(event["estimated_total_cost"])


class TestEventAndRead(EstimateCase):
	def test_the_accepted_event_is_v3_and_carries_the_estimate_as_text(self):
		result = self.accepted(estimated_total_cost="1234567.5")
		row = frappe.db.get_value("Departmental Need Event", result["event_id"], ["event_type", "payload"], as_dict=True)
		self.assertEqual(row.event_type, "DepartmentalNeedAccepted.v3")
		body = json.loads(row.payload)
		self.assertEqual(body["estimated_total_cost"], "1234567.5")
		for excluded in ("currency", "budget_line", "indicative_amount", "funding_source"):
			self.assertNotIn(excluded, body)

	def test_the_typed_read_carries_the_same_estimate(self):
		result = self.accepted(estimated_total_cost=2000000)
		frappe.set_user("Administrator")
		read = workspace.get_current_accepted_need(need=result["need"], user="Administrator")
		self.assertEqual(read["contract"], "DepartmentalNeedAccepted.v3")
		self.assertEqual(read["estimated_total_cost"], "2000000")

	def test_a_v2_replay_reads_as_a_revision_with_no_estimate(self):
		legacy = {"accepted_version_id": "X-V001", "title": "Old", "indicative_quantity": "1"}
		self.assertIsNone(normalise_wire_payload(legacy)["estimated_total_cost"])
		self.assertEqual(LEGACY_EVENT_ACCEPTED, "DepartmentalNeedAccepted.v2")

	def test_the_detail_projection_labels_the_estimate_with_the_budget_currency(self):
		created = self.create(estimated_total_cost=80000000)
		facts = workspace._version_facts(frappe.db.get_value("Departmental Need", created["need"], "current_revision"))
		self.assertEqual(facts["estimated_total_cost"], "80000000")
		self.assertTrue(facts["estimated_total_cost_label"].endswith("80,000,000"))
		self.assertTrue(facts["estimated_total_cost_currency"])

	def test_a_revision_without_an_estimate_projects_absence_not_zero(self):
		created = self.create(estimated_total_cost=None)
		facts = workspace._version_facts(frappe.db.get_value("Departmental Need", created["need"], "current_revision"))
		self.assertIsNone(facts["estimated_total_cost"])
		self.assertEqual(facts["estimated_total_cost_label"], "")
