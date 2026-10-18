# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whole-Tender cancellation recovery against the REAL Planning, Requisitions, Tenders and Budget adapters
(PLN-/TPR-/REQ-/BUD-CR-AC-001 to 012 share this scenario; REQ-CHG-001 v1.20 §17.6, fixtures CR-F01 and CR-F02).

Simulated owners cannot close integration (CR-AC-012), so the world is built through the owners' own commands: a Plan Item with an
Active Annual Plan, an authorised Requisition that draws part of it (Planning drawdown, Budget reservation), a published Tender that
consumes the handoff, and the Accounting Officer's real `CancelTender`.

A world is built once per class and committed; every test that changes it runs inside a savepoint it rolls back, except the last test of
a class, which carries the recovery to its end. The negative cases patch an owner's *answer* (never the service under test) to put the
recovery in the situation under test."""

from __future__ import annotations

import json
from contextlib import contextmanager
from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import cancellation_recovery_contract as tender_seam
from kentender_core.services import contract_reservation_authority as authority
from kentender_procurement.procurement_requisitions.services import cancellation_recovery as recovery_service
from kentender_procurement.procurement_requisitions.services import eligibility_gateway, funding_gateway, recovery_sweep
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import cancellation_world as world
from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx
from kentender_procurement.procurement_planning.services import plan_read, progress_read, recovery_read
from kentender_procurement.procurement_requisitions.services import read as req_read
from kentender_procurement.tenders.services import award_seam, open_period_read
from kentender_procurement.tenders.tests import fixtures as tnd_fx
from kentender_procurement.tenders.tests.test_open_period import OpenPeriodCase

RECOVERY = recovery_service.DOCTYPE


class WorldCase(OpenPeriodCase):
	"""One cancelled Tender with its recovery registered, built once for the class."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.addClassCleanup(setattr, frappe.flags, "kt_tenders_clock", None)
		tnd_fx.wipe_all()
		builder = OpenPeriodCase("setUp")  # owns the channel-confirmation helper; never run as a test
		cls.authorised = cls.build_world()
		cls.sources_before = cls.snapshot()
		cls.tender = world.publish_tender(builder, cls.authorised)
		cls.before_cancel()
		cls.cancelled = world.cancel_tender(cls.tender)
		cls.recovery = cls.cancelled["resource_recovery"]
		frappe.db.commit()

	def setUp(self):  # the per-test publishing of `OpenPeriodCase` is not wanted: the world is the class's
		super(OpenPeriodCase, self).setUp()
		frappe.set_user("Administrator")
		self.addCleanup(frappe.set_user, "Administrator")

	@classmethod
	def snapshot(cls) -> dict:
		raise NotImplementedError

	@classmethod
	def before_cancel(cls) -> None:
		"""A subclass may add to the world between the published Tender and its cancellation."""

	@contextmanager
	def trial(self):
		"""Everything inside is rolled back, so the next test sees the committed world."""
		name = f"trial_{uuid4().hex[:10]}"
		frappe.db.savepoint(name)
		try:
			yield
		finally:
			frappe.db.rollback(save_point=name)

	def doc(self):
		return frappe.get_doc(RECOVERY, self.recovery)

	def hold_rows(self) -> list:
		return frappe.get_all("Plan Cancellation Recovery Hold", filters={"recovery_id": self.recovery}, fields=["name", "allocation_id", "state", "display_status", "quantity", "amount"])


# --------------------------------------------------------------------------
# CR-F01 — one source, 60 of 100 units / KES 6m of KES 10m
# --------------------------------------------------------------------------


class TestCrF01(WorldCase):
	@classmethod
	def build_world(cls):
		return world.single_source_requisition()

	@classmethod
	def snapshot(cls) -> dict:
		reservations = world.reservations_of(cls.authorised["requisition"])
		line = world.budget_line_of(reservations[0])
		return {"item": world.planning_remaining(cls.authorised["item_id"]), "line": line, "position": world.budget_position(line), "reservations": reservations}

	def balances(self) -> dict:
		line = self.sources_before["line"]
		return {"planning": world.planning_remaining(self.authorised["item_id"]), "position": world.budget_position(line)}

	# ---- the cancellation registered the recovery ----------------------------------------------------------------------------

	def test_the_cancellation_registered_a_pending_recovery_and_the_hold_with_the_decision(self):
		recovery = self.doc()
		self.assertEqual((recovery.status, recovery.status_revision, recovery.origin), ("Pending", 1, "Cancellation"))
		self.assertEqual((recovery.requisition, recovery.handoff, recovery.tender), (self.authorised["requisition"], self.authorised["handoff"], self.tender))
		self.assertEqual(len(recovery.sources), 1)
		source = recovery.sources[0]
		self.assertEqual((float(source.quantity), float(source.value)), (60.0, 6_000_000.0))
		self.assertTrue(source.drawdown_reference and source.reservation_id)
		cancellation = frappe.get_doc("Tender Cancellation", self.cancelled["cancellation"])
		self.assertEqual(cancellation.resource_recovery, self.recovery)
		# the existing TenderCancelled event keeps its Bid Opening fields and gains the exact consumed lineage
		event = frappe.get_all("Tender Event", filters={"tender": self.tender, "event_type": "TenderCancelled"}, fields=["payload"])
		payload = json.loads(event[0].payload)
		self.assertEqual(payload["cancellation_digest"], cancellation.cancellation_digest)
		self.assertEqual(payload["resource_recovery"]["recovery"], self.recovery)
		self.assertEqual(payload["resource_recovery"]["handoff"], self.authorised["handoff"])
		self.assertEqual(payload["resource_recovery"]["drawdown_references"], [source.drawdown_reference])
		self.assertEqual([(h["state"], h["display_status"]) for h in self.hold_rows()], [("Active", "Pending")])
		# nothing moved yet, and nothing the cancellation does reopens what it must not
		self.assertEqual(self.balances(), {"planning": self.sources_before["item"], "position": self.sources_before["position"]})
		self.assertEqual(frappe.db.get_value("Tender", self.tender, "overall_status"), "Cancelled")
		self.assertEqual(frappe.db.get_value("Procurement Requisition", self.authorised["requisition"], "current_state"), "Authorised")
		self.assertTrue(frappe.db.get_value("Authorised Requisition Handoff", self.authorised["handoff"], "consumed_at"))
		outcome = frappe.get_all("Requisition Event", filters={"event_type": "CancellationResourceRecoveryOutcome.v1", "requisition": self.authorised["requisition"]}, fields=["event_id", "status", "payload"])
		self.assertEqual([(e.event_id, e.status) for e in outcome], [(f"{self.recovery}:1", "Pending")])
		self.assertEqual(json.loads(outcome[0].payload)["status"], "Pending")

	def test_registering_again_reuses_it_and_a_changed_fact_conflicts(self):
		recovery = self.doc()
		with self.trial():
			again = recovery_service.register_cancellation_resource_recovery(
				tender=self.tender, cancellation=recovery.cancellation, cancellation_digest=recovery.cancellation_digest, cancelled_at=recovery.cancelled_at,
				handoff=recovery.handoff, registered_by=tnd_fx.AO,
			)
			self.assertEqual((again["recovery"], again["reused"]), (self.recovery, True))
			with self.assertRaises(ProcurementRequisitionsError) as caught:
				recovery_service.register_cancellation_resource_recovery(
					tender=self.tender, cancellation=recovery.cancellation, cancellation_digest="0" * 64, cancelled_at=recovery.cancelled_at, handoff=recovery.handoff, registered_by=tnd_fx.AO,
				)
			self.assertEqual(caught.exception.code, "REQ_IDEMPOTENCY_CONFLICT")
			self.assertEqual(frappe.db.count(RECOVERY, {"cancellation": recovery.cancellation}), 1)

	# ---- evidence the owners cannot give ---------------------------------------------------------------------------------------

	def attempt(self):
		return recovery_sweep.run_one(self.recovery)

	def assert_nothing_moved(self):
		self.assertEqual(self.balances(), {"planning": self.sources_before["item"], "position": self.sources_before["position"]})
		self.assertEqual({frappe.db.get_value("Funding Reservation", r, "status") for r in self.sources_before["reservations"]}, {"Active"})
		self.assertEqual(frappe.db.get_value("Tender", self.tender, "overall_status"), "Cancelled")  # a failed recovery never reopens the cancellation
		# ...and the cancellation's own compliance work goes on whatever the recovery does (TPR-CR-AC-009): the task is still open, the notices still due
		self.assertEqual(frappe.db.get_value("Tender Task", {"tender": self.tender, "task_type": "Cancellation compliance"}, "status"), "Open")
		obligations = frappe.get_doc("Tender Cancellation", self.cancelled["cancellation"]).obligations
		self.assertTrue([o for o in obligations if o.obligation_type == "Notice channel" and o.status == "Due"])

	def test_unavailable_evidence_leaves_it_pending_to_be_tried_again(self):
		with self.trial():
			with patch.object(award_seam, "downstream_disposition", return_value={"known": False}):
				outcome = self.attempt()
			doc = self.doc()
			self.assertEqual((outcome["status"], outcome["reason_code"]), ("Pending", "TENDER_BASIS_UNAVAILABLE"))
			self.assertEqual((doc.attempt_count, bool(doc.next_attempt_at)), (1, True))
			self.assert_nothing_moved()
			self.assertNotIn(self.recovery, recovery_sweep.due())  # not before its backoff has passed (other recoveries on a shared site may be due)

	def test_notices_being_issued_is_not_proof_either_way(self):
		with self.trial():
			with patch.object(award_seam, "downstream_disposition", return_value={"known": True, "notification_status": "Issue in progress", "case": "AWC-1", "package_status": ""}):
				self.assertEqual(self.attempt()["status"], "Pending")
			self.assert_nothing_moved()

	def test_an_award_notice_or_package_needs_attention_and_nothing_is_restored(self):
		for disposition in (
			{"known": True, "notification_status": "Issued", "case": "AWC-1", "package_status": ""},
			{"known": True, "notification_status": "Not issued", "case": "AWC-1", "package_status": "Delivered", "package_delivered": True},
		):
			with self.subTest(disposition=disposition), self.trial():
				with patch.object(award_seam, "downstream_disposition", return_value=disposition):
					outcome = self.attempt()
				self.assertEqual((outcome["status"], outcome["reason_code"]), ("Needs attention", "TENDER_BASIS_NEGATIVE"))
				self.assert_nothing_moved()
				self.assertEqual([h["display_status"] for h in self.hold_rows()], ["Needs attention"])
				self.assertFalse(self.attempt()["acted"])  # never retried by itself

	def test_a_converted_reservation_needs_attention_and_keeps_every_resource(self):
		reservation = self.sources_before["reservations"][0]
		authority.permit_all(self)  # the subject here is the recovery, not the contract's funding lineage
		with self.trial():
			from kentender_budget.services import budget_commitment_contracts as commit
			from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, service_caller

			commit.convert_reservation(
				reservation, "CTR-CR-INT", 1_000_000, uuid4().hex, contract_event_id="CTR-CR-INT:signed", contract_event_type="ContractSigned",
				caller=service_caller(PRINCIPAL_CONTRACT, reference="CTR-CR-INT"),
			)
			outcome = self.attempt()
			self.assertEqual((outcome["status"], outcome["reason_code"]), ("Needs attention", "BUDGET_DOES_NOT_SUPPORT_RELEASE"))
			self.assertIn("converted", outcome["reason"])
			self.assertEqual(world.planning_remaining(self.authorised["item_id"]), self.sources_before["item"])
			self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "status"), "Partially Converted")
			self.assertEqual([h["state"] for h in self.hold_rows()], ["Active"])

	def test_a_reservation_released_for_another_reason_is_never_released_again(self):
		reservation = self.sources_before["reservations"][0]
		with self.trial():
			funding_gateway.release_reservation(
				reservation=reservation, requisition_reference=frappe.db.get_value("Procurement Requisition", self.authorised["requisition"], "requisition_reference"),
				downstream_event_id="other", idempotency_key=uuid4().hex,
			)
			outcome = self.attempt()
			self.assertEqual((outcome["status"], outcome["reason_code"]), ("Needs attention", "BUDGET_DOES_NOT_SUPPORT_RELEASE"))
			self.assertEqual(world.planning_remaining(self.authorised["item_id"]), self.sources_before["item"])

	def test_a_draw_reversed_for_another_reason_rolls_the_budget_release_back_too(self):
		"""The Planning leg refuses after the Budget leg ran: both owners' effects are undone together."""
		drawdown = self.doc().sources[0].drawdown_reference
		with self.trial():
			frappe.db.set_value("Plan Drawdown Reference", drawdown, {"drawdown_state": "Reversed", "reversal_reason": "Requisition revoked"}, update_modified=False)  # a state the services forbid
			outcome = self.attempt()
			self.assertEqual((outcome["status"], outcome["reason_code"]), ("Needs attention", "OWNER_REFUSED"))
			self.assertIn("Planning", outcome["reason"])
			self.assertEqual({frappe.db.get_value("Funding Reservation", r, "status") for r in self.sources_before["reservations"]}, {"Active"})
			self.assertEqual(world.budget_position(self.sources_before["line"]), self.sources_before["position"])
			self.assertEqual(frappe.db.count("Reservation Cancellation Release", {"recovery_id": self.recovery}), 0)

	def test_a_failure_on_either_owner_leg_commits_neither_effect(self):
		for leg, target in (("budget", (funding_gateway, "release_reservations_for_cancelled_tender")), ("planning", (eligibility_gateway, "reverse_requisition_drawdowns_for_cancellation"))):
			with self.subTest(leg=leg), self.trial():
				with patch.object(target[0], target[1], side_effect=RuntimeError("the owner could not be reached")):
					outcome = self.attempt()
				self.assertEqual((outcome["status"], outcome["reason_code"]), ("Pending", "OWNER_UNAVAILABLE"))
				self.assert_nothing_moved()
				self.assertEqual(frappe.db.count("Reservation Cancellation Release", {"recovery_id": self.recovery}), 0)
				self.assertEqual([h["state"] for h in self.hold_rows()], ["Active"])

	def test_a_planning_failure_after_the_budget_leg_undoes_the_budget_leg(self):
		real = funding_gateway.release_reservations_for_cancelled_tender
		with self.trial():
			with patch.object(funding_gateway, "release_reservations_for_cancelled_tender", side_effect=real) as release, patch.object(
				eligibility_gateway, "reverse_requisition_drawdowns_for_cancellation", side_effect=RuntimeError("planning could not be reached")
			):
				outcome = self.attempt()
			self.assertEqual(release.call_count, 1)  # the Budget leg did run first
			self.assertEqual(outcome["status"], "Pending")
			self.assert_nothing_moved()
			self.assertEqual(frappe.db.count("Reservation Cancellation Release", {"recovery_id": self.recovery}), 0)

	def test_a_different_consumed_lineage_needs_attention(self):
		recovery = self.doc()
		wrong = {"verdict": "positive", "reason": "", "revision": "x", "lineage": {"requisition": recovery.requisition, "handoff": recovery.handoff, "sources": [{"drawdown_line_id": "DDL-NOT-THIS", "reservation_id": "RSV-X"}]}}
		with self.trial(), tender_seam.installed(tender_seam.Static(wrong)):
			outcome = self.attempt()
			self.assertEqual((outcome["status"], outcome["reason_code"]), ("Needs attention", "LINEAGE_MISMATCH"))
			self.assert_nothing_moved()

	def test_a_technical_operator_can_retry_the_same_intent_and_no_one_else(self):
		with self.trial():
			with patch.object(award_seam, "downstream_disposition", return_value={"known": True, "notification_status": "Issued", "case": "AWC-1", "package_status": ""}):
				self.attempt()
			self.assertEqual(self.doc().status, "Needs attention")
			frappe.set_user(req_fx.HOPF)
			with self.assertRaises(frappe.DoesNotExistError):
				recovery_service.retry_cancellation_recovery(recovery=self.recovery, user=req_fx.HOPF)
			frappe.set_user("Administrator")
			retried = recovery_service.retry_cancellation_recovery(recovery=self.recovery, user="Administrator")
			self.assertEqual((retried["status"], retried["status_revision"]), ("Pending", 3))
			self.assertEqual([h["display_status"] for h in self.hold_rows()], ["Pending"])

	def test_who_may_read_the_recovery(self):
		for reader, allowed in ((req_fx.HOPF, True), (req_fx.PLANNER, True), (req_fx.AUDITOR, True), (req_fx.AUTHOR, True), (req_fx.OUTSIDER, False)):
			frappe.set_user(reader)
			if allowed:
				read = recovery_service.get_cancellation_resource_recovery(recovery=self.recovery, user=reader)
				self.assertEqual((read["status"], len(read["sources"]), read["all_sources_shown"]), ("Pending", 1, True), reader)
			else:
				with self.assertRaises(frappe.DoesNotExistError):
					recovery_service.get_cancellation_resource_recovery(recovery=self.recovery, user=reader)
		frappe.set_user("Administrator")

	# ---- what the four owners' screens say, in each state --------------------------------------------------------------------

	def tender_section(self):
		return open_period_read.get_tender_cancellation(tender=self.tender, user=tnd_fx.AO)["resource_recovery"]

	def requisition_section(self, user=req_fx.HOPF):
		frappe.set_user(user)
		try:
			return req_read.get_requisition_record(requisition=self.authorised["requisition"], user=user)["cancellation_recovery"]
		finally:
			frappe.set_user("Administrator")

	def planning_sections(self):
		frappe.set_user(req_fx.PLANNER)
		try:
			rows = progress_read.get_procurement_progress(plan_reference="")["items"]
		finally:
			frappe.set_user("Administrator")
		return next(r for r in rows if r["plan_item_id"] == self.authorised["item_id"])["recoveries"]

	def plan_item_sections(self):
		"""The same recovery on the Plan Item's own detail (PLN-CHG-001 v1.32 §10.19)."""
		frappe.set_user(req_fx.PLANNER)
		try:
			return plan_read.get_plan_item(plan_item_id=self.authorised["item_id"])["recoveries"]
		finally:
			frappe.set_user("Administrator")

	def budget_line(self):
		from kentender_budget.services.budget_contracts import get_budget_line_position

		return get_budget_line_position(self.sources_before["line"])

	def test_the_four_screens_say_pending_in_their_own_words(self):
		tender = self.tender_section()
		self.assertEqual((tender["status"], tender["label"]), ("Pending", "Restoring unused allowance and funding"))
		self.assertEqual(tender["explanation"], "You can view the cancelled tender. The affected allowance cannot be used until restoration is complete.")
		self.assertEqual([(r["quantity"], r["value"]) for r in tender["rows"]], [("60 Each", "KES 6,000,000.00")])
		self.assertIsNone(tender["next_step"])
		self.assertIn(self.recovery, [t["value"] for t in tender["technical"]])  # identifiers only under Technical details
		self.assertNotIn(self.recovery, tender["explanation"] + tender["label"] + tender["rows"][0]["source"])
		self.assertEqual(self.requisition_section()["label"], "Restoring unused allowance and funding")
		planning = self.planning_sections()
		self.assertEqual([(s["status"], s["label"]) for s in planning], [("Pending", "Restoring unused allowance")])
		self.assertEqual([(s["status"], s["label"]) for s in self.plan_item_sections()], [("Pending", "Restoring unused allowance")])
		reservation = self.budget_line()["reservations"][0]
		self.assertEqual((reservation["status"], reservation["recovery"]["status"], reservation["recovery"]["label"]), ("Active", "Pending", "Being released after tender cancellation"))
		self.assertEqual(self.budget_line()["cancellation_releases"], [])

	def test_needs_attention_shows_the_owners_real_reason_everywhere(self):
		with self.trial():
			with patch.object(award_seam, "downstream_disposition", return_value={"known": True, "notification_status": "Issued", "case": "AWC-1", "package_status": ""}):
				self.attempt()
			tender = self.tender_section()
			self.assertEqual((tender["status"], tender["label"]), ("Needs attention", "Unused allowance and funding need attention"))
			self.assertIn("notices", tender["reason"].lower())
			self.assertEqual(self.requisition_section()["status"], "Needs attention")
			self.assertEqual(self.planning_sections()[0]["label"], "Unused allowance could not be restored")
			self.assertEqual(self.plan_item_sections()[0]["label"], "Unused allowance could not be restored")
			self.assertEqual(self.budget_line()["reservations"][0]["recovery"]["status"], "Needs attention")

	def test_a_departmental_reader_sees_only_the_permitted_rows(self):
		author = self.requisition_section(req_fx.AUTHOR)
		self.assertTrue(author["rows"] and author["partial_view"] is False)  # the Author's department is the only source here
		frappe.set_user(req_fx.OUTSIDER)
		try:
			self.assertIsNone(tender_view_for(self.tender, req_fx.OUTSIDER))
		finally:
			frappe.set_user("Administrator")

	# ---- the complete recovery, last: it carries the world to its end -----------------------------------------------------------

	def test_zz_the_exact_draw_is_restored_the_hold_released_and_a_fresh_requisition_can_use_it(self):
		line = self.sources_before["line"]
		reservation = self.sources_before["reservations"][0]
		source = self.doc().sources[0]
		before_lock = frappe.db.get_value("Plan Item", self.authorised["item_id"], ["scope_locked_since", "first_authorised_requisition"], as_dict=True)
		self.assertEqual(self.sources_before["item"][0].split(".")[0], "40")

		outcome = self.attempt()
		frappe.db.commit()

		doc = self.doc()
		self.assertEqual((outcome["status"], outcome["status_revision"], doc.status, doc.status_revision), ("Completed", 2, "Completed", 2))
		self.assertEqual((doc.reason_code, bool(doc.completed_at), doc.attempt_count), ("", True, 1))
		self.assertEqual([float(x) for x in world.planning_remaining(self.authorised["item_id"])], [100.0, 10_000_000.0])
		position, before = world.budget_position(line), self.sources_before["position"]
		self.assertEqual((float(position["reserved"]), float(position["committed"]), float(position["approved"])), (0.0, float(before["committed"]), float(before["approved"])))  # the release touches only what was reserved
		self.assertEqual(float(position["available"]), float(before["available"]) + 6_000_000.0)  # V rises by exactly what R fell by
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "status"), "Released")
		self.assertEqual(float(frappe.db.get_value("Funding Reservation", reservation, "original_amount")), 6_000_000.0)  # the authorisation is never edited
		reversed_row = frappe.db.get_value("Plan Drawdown Reference", source.drawdown_reference, ["drawdown_state", "reversal_reason", "recovery_id", "quantity", "amount"], as_dict=True)
		self.assertEqual((reversed_row.drawdown_state, reversed_row.reversal_reason, reversed_row.recovery_id), ("Reversed", "TenderCancelled", self.recovery))
		self.assertEqual([h["state"] for h in self.hold_rows()], ["Removed"])
		done = doc.sources[0]
		self.assertEqual((float(done.restored_quantity), float(done.restored_value), float(done.released_value)), (60.0, 6_000_000.0, 6_000_000.0))
		self.assertTrue(done.reversal_reference and done.release_reference and done.ledger_event)
		# what it must never touch
		self.assertEqual(frappe.db.get_value("Plan Item", self.authorised["item_id"], ["scope_locked_since", "first_authorised_requisition"], as_dict=True), before_lock)
		self.assertEqual(frappe.db.get_value("Tender", self.tender, "overall_status"), "Cancelled")
		self.assertEqual(frappe.db.get_value("Procurement Requisition", self.authorised["requisition"], "current_state"), "Authorised")
		self.assertTrue(frappe.db.get_value("Authorised Requisition Handoff", self.authorised["handoff"], "consumed_at"))
		events = frappe.get_all("Requisition Event", filters={"event_type": "CancellationResourceRecoveryOutcome.v1", "requisition": self.authorised["requisition"]}, fields=["event_id", "payload"], order_by="sequence asc")
		self.assertEqual([e.event_id for e in events], [f"{self.recovery}:1", f"{self.recovery}:2"])
		self.assertEqual(json.loads(events[1].payload)["status"], "Completed")

		# replay: the recorded result, no second effect
		again = self.attempt()
		self.assertEqual((again["status"], again["acted"]), ("Completed", False))
		release = funding_gateway.release_reservations_for_cancelled_tender(
			recovery_id=self.recovery, cancellation_id=doc.cancellation, requisition_reference=frappe.db.get_value("Procurement Requisition", self.authorised["requisition"], "requisition_reference"),
			releases=[{"reservation": reservation, "drawdown_line_id": done.drawdown_line_id, "plan_source_allocation": done.allocation_id, "amount": done.value}], idempotency_key=uuid4().hex,
		)
		self.assertTrue(release["all_reused"])  # a new key finds the one release for this cancellation and drawdown line
		reversed_again = eligibility_gateway.reverse_requisition_drawdowns_for_cancellation(
			recovery_id=self.recovery, cancellation_id=doc.cancellation, plan_item_id=self.authorised["item_id"],
			requisition_reference=frappe.db.get_value("Procurement Requisition", self.authorised["requisition"], "requisition_reference"),
			sources=[{"plan_source_allocation_id": done.allocation_id, "drawdown_reference": done.drawdown_reference, "quantity": done.quantity, "amount": done.value}],
		)
		self.assertTrue(reversed_again["idempotent"])
		self.assertEqual([float(x) for x in world.planning_remaining(self.authorised["item_id"])], [100.0, 10_000_000.0])

		# what the four owners now say
		tender = self.tender_section()
		self.assertEqual((tender["status"], tender["label"]), ("Completed", "Unused allowance and funding restored"))
		self.assertEqual(tender["rows"][0]["restored"], "60 Each · KES 6,000,000.00")
		self.assertEqual(tender["next_step"]["label"], "Start a new requisition for this purchase")  # offered because Planning currently offers the item
		self.assertTrue(tender["next_step"]["route"].endswith(f"/new/{self.authorised['item_id']}"))
		self.assertEqual(self.requisition_section()["label"], "Unused allowance and funding restored")
		self.assertEqual([(s["status"], s["label"]) for s in self.planning_sections()], [("Completed", "Unused allowance restored after tender cancellation")])
		self.assertEqual([(s["status"], s["label"]) for s in self.plan_item_sections()], [("Completed", "Unused allowance restored after tender cancellation")])
		# Desk routes travel as the segments frappe.set_route takes, never as a path string it would spread into letters
		offered = recovery_read.sections_for_item(self.authorised["item_id"], start_route=lambda: f"/app/procurement-requisitions/new/{self.authorised['item_id']}")
		self.assertEqual(offered[0]["next_step"]["route"], ["procurement-requisitions", "new", self.authorised["item_id"]])
		self.assertIsNone(recovery_read.sections_for_item(self.authorised["item_id"], start_route=lambda: "")[0]["next_step"])  # nothing offered, no link
		line_view = self.budget_line()
		self.assertEqual(line_view["reservations"], [])  # a released reservation is no longer a hold on the line
		self.assertEqual([(r["reservation"], r["closure"]) for r in line_view["cancellation_releases"]], [(reservation, "")])
		self.assertEqual(line_view["cancellation_releases"][0]["amount"], 6_000_000.0)

		# an ordinary fresh Requisition against the restored allowance: fresh identities, ordinary approvals
		fresh = world.single_source_requisition(item=(None, self.authorised["item_id"]))
		self.assertNotEqual(fresh["handoff"], self.authorised["handoff"])
		fresh_reservation = world.reservations_of(fresh["requisition"])[0]
		self.assertNotEqual(fresh_reservation, reservation)
		self.assertEqual([float(x) for x in world.planning_remaining(self.authorised["item_id"])], [40.0, 4_000_000.0])
		again_position = world.budget_position(line)
		self.assertEqual((float(again_position["reserved"]), float(again_position["available"])), (6_000_000.0, float(before["available"])))
		# replaying the OLD recovery leaves the new balances alone
		self.assertEqual(self.attempt()["status"], "Completed")
		self.assertEqual([float(x) for x in world.planning_remaining(self.authorised["item_id"])], [40.0, 4_000_000.0])
		self.assertEqual(frappe.db.get_value("Funding Reservation", fresh_reservation, "status"), "Active")


# --------------------------------------------------------------------------
# CR-F02 — two sources, each drawn in full, separate reservations on one Budget Line
# --------------------------------------------------------------------------


class TestCrF02(WorldCase):
	@classmethod
	def build_world(cls):
		return world.combined_requisition()

	@classmethod
	def snapshot(cls) -> dict:
		reservations = world.reservations_of(cls.authorised["requisition"])
		lines = {world.budget_line_of(r) for r in reservations}
		assert len(lines) == 1, f"CR-F02 needs both reservations on one Budget Line, got {lines}"
		line = next(iter(lines))
		return {"item": world.planning_remaining(cls.authorised["item_id"]), "line": line, "position": world.budget_position(line), "reservations": reservations}

	def test_both_sources_and_both_reservations_are_registered_and_none_is_omitted(self):
		doc = self.doc()
		self.assertEqual(sorted((float(s.quantity), float(s.value)) for s in doc.sources), [(40.0, 4_000_000.0), (60.0, 6_000_000.0)])
		self.assertEqual(len(self.hold_rows()), 2)
		self.assertEqual(len(set(self.sources_before["reservations"])), 2)
		self.assertEqual(float(self.sources_before["position"]["reserved"]), 10_000_000.0)

	def test_a_failure_on_either_source_commits_neither_restoration_nor_release(self):
		with self.trial():
			real = eligibility_gateway.reverse_requisition_drawdowns_for_cancellation
			second = self.doc().sources[1].drawdown_reference
			frappe.db.set_value("Plan Drawdown Reference", second, {"drawdown_state": "Reversed", "reversal_reason": "Requisition revoked"}, update_modified=False)
			outcome = recovery_sweep.run_one(self.recovery)
			self.assertEqual(outcome["status"], "Needs attention")
			self.assertEqual({frappe.db.get_value("Funding Reservation", r, "status") for r in self.sources_before["reservations"]}, {"Active"})
			self.assertEqual(world.budget_position(self.sources_before["line"]), self.sources_before["position"])
			first = self.doc().sources[0].drawdown_reference
			self.assertEqual(frappe.db.get_value("Plan Drawdown Reference", first, "drawdown_state"), "Active")
			self.assertIs(real, eligibility_gateway.reverse_requisition_drawdowns_for_cancellation)

	def test_zz_both_ceilings_are_restored_and_ten_million_released_in_one_transaction(self):
		outcome = recovery_sweep.run_one(self.recovery)
		frappe.db.commit()
		self.assertEqual((outcome["status"], outcome["status_revision"]), ("Completed", 2))
		position, before = world.budget_position(self.sources_before["line"]), self.sources_before["position"]
		self.assertEqual((float(position["reserved"]), float(position["committed"])), (0.0, float(before["committed"])))  # the release touches only what was reserved
		self.assertEqual(float(position["available"]), float(before["available"]) + 10_000_000.0)  # R down 10m, V up 10m, A and C unchanged
		self.assertEqual((float(position["approved"]), float(before["reserved"])), (float(before["approved"]), 10_000_000.0))
		self.assertEqual([float(x) for x in world.planning_remaining(self.authorised["item_id"])], [100.0, 10_000_000.0])
		self.assertEqual({frappe.db.get_value("Funding Reservation", r, "status") for r in self.sources_before["reservations"]}, {"Released"})
		self.assertEqual(frappe.db.count("Reservation Cancellation Release", {"recovery_id": self.recovery}), 2)
		self.assertEqual({h["state"] for h in self.hold_rows()}, {"Removed"})
		self.assertEqual(recovery_sweep.run_one(self.recovery)["acted"], False)


def tender_view_for(tender: str, user: str):
	"""What a reader without the Requisitions responsibilities is shown of a cancelled Tender's recovery: nothing."""
	from kentender_procurement.procurement_requisitions.services import recovery_view

	return recovery_view.for_tender(tender, owner="Tenders", user=user)
