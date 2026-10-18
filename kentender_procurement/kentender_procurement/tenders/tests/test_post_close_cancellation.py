# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.24 §5.7, §5.12, §7.4, §7.6, §8, §10.13 POSTCLOSE, §10.19 — the post-close cancellation route and the durable delivery of the
existing `TenderCancelled` event (TPR-OF-AC-003..008, TPR-OF-AC-011).

`CancelTender` is supported from Submission period ended before authoritative Award notification, and only when every guard passes: a verified applicable
ground, the Award authority's durable Tender-level record saying Not issued, and the cancellation consumers able to take the event. The read answers the
same question the command does; a blocked decision lists every blocker with its Tenders code, holder and route. A technical failure alone is no ground."""

from __future__ import annotations

import importlib
import json
from unittest import mock

import frappe

from kentender_core.seeds.calendar import fiscal as F, world as W  # noqa: F401
from kentender_procurement.tenders.services import cancellation, cancellation_delivery, errors, events, open_period_read, read, submission_close
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.test_services import ground_verifier
from kentender_procurement.tenders.tests import fake_candidates
from kentender_procurement.tenders.tests import fixtures as fx
from kentender_procurement.tenders.tests.test_open_period import OpenPeriodCase

REASON = "The confirmed budget available for this procurement is insufficient to proceed."
CONSUMER = "kentender_procurement.bid_opening.services.cancellation_consumer"


class PostCloseCase(OpenPeriodCase):
	def setUp(self):
		super().setUp()
		ground_verifier.reset_controls()
		self.addCleanup(ground_verifier.reset_controls)
		frappe.flags.kt_tenders_clock = W("2027-06-05 11:00:00")
		self.assertEqual(submission_close.close_due_submission_periods()["closed"], [self.name])
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Submission period ended")

	def verify(self, *grounds: str) -> None:
		ground_verifier.set_controls(verified_cancellation_grounds=",".join(grounds))

	def decision(self, user=fx.AO) -> dict:
		return open_period_read.get_tender_cancellation(tender=self.name, user=user)

	def cancel(self, ground="INADEQUATE_BUDGET", key=None, user=fx.AO):
		root = self._root()
		return cancellation.cancel_tender(tender=self.name, ground=ground, reason=REASON, expected_record_version=root.record_version, idempotency_key=key or fx.key(), user=user)

	def award_record(self, **values):
		frappe.db.set_value("Award Tender Authority", self.name, values)


class TestAllowed(PostCloseCase):
	def test_the_decision_is_offered_and_committed_with_a_verified_ground_and_award_not_issued(self):
		self.verify("INADEQUATE_BUDGET")
		shown = self.decision()
		decision = shown["decision"]
		self.assertEqual((decision["stage"], decision["allowed"], decision["blockers"], decision["heading"]), ("post_close", True, [], ""))
		self.assertEqual(decision["award"]["label"], "Award notification status: Not issued")
		self.assertTrue(decision["award"]["source"].startswith("Award Tender Authority"))
		self.assertEqual([g["key"] for g in shown["grounds"]], ["INADEQUATE_BUDGET"])
		self.assertEqual(shown["grounds"][0]["reference"], "GRD-INADEQUATE_BUDGET")
		self.assertIn("cancel_tender", shown["allowed_actions"])
		self.assertEqual(shown["postclose_warning_text"], "Cancellation is final for this tender. A replacement purchase requires a new requisition.")

		result = self.cancel()
		root = self._root()
		cancelled = frappe.get_doc("Tender Cancellation", result["cancellation"])
		self.assertEqual((root.overall_status, cancelled.previous_status), ("Cancelled", "Submission period ended"))
		self.assertEqual(json.loads(cancelled.ground_evidence_json)["reference"], "GRD-INADEQUATE_BUDGET")
		self.assertEqual(json.loads(cancelled.authority_evidence_json)["notification_status"], "Not issued")
		event = frappe.get_doc("Tender Event", {"tender": self.name, "event_type": "TenderCancelled"})
		payload = json.loads(event.payload)
		self.assertEqual((payload["previous_status"], payload["stage"], payload["resulting_status"]), ("Submission period ended", "post_close", "Cancelled"))
		# the Tender's authority record carries the cancellation, still Not issued; the funding recovery is registered with the decision
		self.assertEqual(frappe.db.get_value("Award Tender Authority", self.name, ["cancellation_ref", "notification_status"]), (cancelled.name, "Not issued"))
		self.assertEqual(frappe.db.get_value("Cancellation Resource Recovery", {"tender": self.name}, "status"), "Pending")
		# one delivery row per consumer, from this event, written with the decision
		rows = frappe.get_all("Tender Event Delivery", filters={"tender": self.name}, fields=["consumer", "status", "event_id", "attempts"])
		self.assertEqual([(r.consumer, r.status, r.event_id, r.attempts) for r in rows], [("bid-opening", "Pending", event.event_id, 0)])
		# no sealed content, count or name travels with the decision screen
		again = self.decision()
		self.assertNotIn("bid_count", json.dumps(again, default=str))

	def test_a_repeat_with_the_same_key_returns_the_original_decision_event_and_delivery(self):
		self.verify("INADEQUATE_BUDGET")
		key = fx.key()
		first = self.cancel(key=key)
		second = self.cancel(key=key)
		self.assertEqual((second["cancellation"], second.get("idempotent")), (first["cancellation"], True))
		self.assertEqual(frappe.db.count("Tender Event", {"tender": self.name, "event_type": "TenderCancelled"}), 1)
		self.assertEqual(frappe.db.count("Tender Event Delivery", {"tender": self.name}), 1)
		self.assertEqual(frappe.db.count("Tender Cancellation", {"tender": self.name}), 1)
		with self.assertRaises(TendersError) as ctx:  # a different key after the cancellation is committed
			self.cancel()
		self.assertEqual(ctx.exception.code, "TND_CANCELLED")

	def test_the_notice_reaches_the_candidates_registered_before_the_close(self):
		fake = fake_candidates.install(self)
		fake.register(tender=self.name, bidder_arrangement_id="ARR-PC-001", candidate_name="Afya Digital Supplies Limited", notice_address="tenders@afyadigital.example",
			registered_at=W("2027-05-20 09:00:00"))
		self.verify("INADEQUATE_BUDGET")
		result = self.cancel()
		self.assertEqual(frappe.db.count("Tender Candidate Notice", {"tender": self.name, "notice_type": "Tender cancelled"}), 1)
		doc = frappe.get_doc("Tender Cancellation", result["cancellation"])
		candidate = next(o for o in doc.obligations if o.obligation_type == "Candidate notice")
		self.assertNotEqual(candidate.evidence_reference, "No Tender-bound candidates were registered when the Tender was cancelled.")
		html = frappe.get_doc("Tender Document", {"cancellation": doc.name, "kind": "Cancellation notice"})
		self.assertIsNotNone(html)

	def test_the_post_close_notice_does_not_say_the_tender_will_not_be_opened(self):
		from kentender_procurement.tenders.services import documents

		self.verify("INADEQUATE_BUDGET")
		result = self.cancel()
		text = documents.html_of(frappe.db.get_value("Tender Document", {"cancellation": result["cancellation"], "kind": "Cancellation notice"}, "name"))
		self.assertIn("The submission period had ended when the proceedings were cancelled", text)
		self.assertNotIn("will not be opened", text)


class TestBlocked(PostCloseCase):
	def codes(self, shown=None) -> list[str]:
		return [b["code"] for b in (shown or self.decision())["decision"]["blockers"]]

	def test_no_verified_ground_blocks_with_the_documented_review_and_removes_the_action(self):
		shown = self.decision()
		decision = shown["decision"]
		self.assertEqual((decision["allowed"], self.codes(shown)), (False, ["TND_CANCEL_GROUND_UNVERIFIED"]))
		self.assertEqual((decision["heading"], decision["blocked_title"]), ("A tender decision is needed", "Cancellation cannot be decided here"))
		blocker = decision["blockers"][0]
		self.assertEqual(blocker["message"], "A verified cancellation basis is needed before this tender can be cancelled.")
		self.assertIn("Head of Procurement Function", blocker["holder"])
		self.assertIn("Accounting Officer keeps the decision", blocker["holder"])
		self.assertNotIn("cancel_tender", shown["allowed_actions"])
		self.assertIn("review_cancellation_decision", shown["allowed_actions"])
		self.assertEqual(shown["grounds"], [])

	def test_a_command_refused_by_the_guards_changes_nothing_and_lists_every_blocker(self):
		self.award_record(notification_status="Unknown")
		with self.assertRaises(TendersError) as ctx:
			self.cancel()
		self.assertEqual(ctx.exception.code, "TND_AWARD_STATUS_UNAVAILABLE")
		self.assertEqual(sorted(b["code"] for b in ctx.exception.detail["blockers"]), ["TND_AWARD_STATUS_UNAVAILABLE", "TND_CANCEL_GROUND_UNVERIFIED"])
		self.assertEqual(len(ctx.exception.detail["reasons"]), 2)
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Submission period ended")
		self.assertEqual(frappe.db.count("Tender Cancellation", {"tender": self.name}), 0)
		self.assertEqual(frappe.db.count("Tender Event Delivery", {"tender": self.name}), 0)
		self.assertFalse(frappe.db.get_value("Award Tender Authority", self.name, "cancellation_ref"))

	def test_a_ground_not_among_the_verified_ones_is_refused(self):
		self.verify("INADEQUATE_BUDGET")
		with self.assertRaises(TendersError) as ctx:
			self.cancel(ground="NEED_CEASED")
		self.assertEqual(ctx.exception.code, "TND_CANCEL_GROUND_UNVERIFIED")

	def test_the_award_status_blockers_name_their_code_holder_and_route(self):
		self.verify("INADEQUATE_BUDGET")
		cases = (
			({"notification_status": "Issued"}, "TND_CANCEL_TOO_LATE", "Award and legal process owner", "It is too late to cancel this Tender: the award has been notified."),
			({"notification_status": "Issue in progress"}, "TND_AWARD_STATUS_UNAVAILABLE", "Award service owner", "We cannot confirm that cancellation is permitted from the current award status."),
			({"notification_status": "Unknown"}, "TND_AWARD_STATUS_UNAVAILABLE", "Award service owner", "We cannot confirm that cancellation is permitted from the current award status."),
		)
		for values, code, holder, message in cases:
			self.award_record(**values)
			shown = self.decision()
			blocker = shown["decision"]["blockers"][0]
			self.assertEqual((blocker["code"], blocker["holder"], blocker["message"]), (code, holder, message), values)
			self.assertEqual(shown["decision"]["award"]["notification_status"], values["notification_status"])
			self.assertNotIn("cancel_tender", shown["allowed_actions"])
			self.assertIn("area", blocker["route"])

	def test_a_missing_or_tampered_authority_record_is_unavailable_never_not_issued(self):
		self.verify("INADEQUATE_BUDGET")
		self.award_record(source_event="tampered")
		self.assertEqual(self.codes(), ["TND_AWARD_STATUS_UNAVAILABLE"])
		frappe.db.delete("Award Tender Authority", {"tender": self.name})
		shown = self.decision()
		self.assertEqual(self.codes(shown), ["TND_AWARD_STATUS_UNAVAILABLE"])
		self.assertEqual(shown["decision"]["award"]["notification_status"], "Unknown")
		with self.assertRaises(TendersError) as ctx:
			self.cancel()
		self.assertEqual(ctx.exception.code, "TND_AWARD_STATUS_UNAVAILABLE")

	def test_an_unavailable_cancellation_consumer_goes_to_opening_access_support(self):
		self.verify("INADEQUATE_BUDGET")
		consumer = importlib.import_module(CONSUMER)
		with mock.patch.object(consumer, "available", return_value={"available": False, "reason": "The opening records are being restored."}):
			shown = self.decision()
			blocker = shown["decision"]["blockers"][0]
			self.assertEqual((blocker["code"], blocker["holder"]), ("TND_CANCELLATION_UNAVAILABLE", "Opening access support"))
			self.assertEqual(blocker["message"], "Cancellation is unavailable. Opening access support is checking the problem.")
			with self.assertRaises(TendersError) as ctx:
				self.cancel()
			self.assertEqual(ctx.exception.code, "TND_CANCELLATION_UNAVAILABLE")

	def test_every_current_blocker_is_returned_together_in_priority_order(self):
		self.award_record(notification_status="Issued")
		consumer = importlib.import_module(CONSUMER)
		with mock.patch.object(consumer, "available", return_value={"available": False, "reason": "down"}):
			self.assertEqual(self.codes(), ["TND_CANCEL_TOO_LATE", "TND_CANCEL_GROUND_UNVERIFIED", "TND_CANCELLATION_UNAVAILABLE"])

	def test_only_the_accounting_officer_is_offered_the_post_close_decision(self):
		self.verify("INADEQUATE_BUDGET")
		for user in (fx.HOPF, fx.OFFICER):
			actions = self.decision(user)["allowed_actions"]
			self.assertNotIn("cancel_tender", actions, user)
			self.assertNotIn("review_cancellation_decision", actions, user)
		with self.assertRaises(frappe.DoesNotExistError):  # the command is the Accounting Officer's alone; others get the masked answer
			self.cancel(user=fx.HOPF)
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Submission period ended")

	def test_a_technical_failure_alone_is_no_ground(self):
		"""Bid Opening's outcome is linked evidence for review: nothing in the verdict reads a fault, so a world full of failed services verifies nothing."""
		consumer = importlib.import_module(CONSUMER)
		self.assertEqual(self.codes(), ["TND_CANCEL_GROUND_UNVERIFIED"])
		self.assertTrue(consumer.available()["available"])


class TestDelivery(PostCloseCase):
	def test_a_failed_delivery_is_kept_and_retried_from_the_same_event_and_never_undoes_the_cancellation(self):
		self.verify("INADEQUATE_BUDGET")
		consumer = importlib.import_module(CONSUMER)
		with mock.patch.object(consumer, "deliver", side_effect=RuntimeError("Proceedings is down")):
			result = self.cancel()
			frappe.db.commit()  # the request's commit: delivery is attempted once, right after it, and fails
		event = frappe.get_doc("Tender Event", {"tender": self.name, "event_type": "TenderCancelled"})
		row = frappe.get_doc("Tender Event Delivery", {"tender": self.name})
		self.assertEqual((row.status, row.attempts, row.error_code, row.event_id), ("Failed", 1, "RuntimeError", event.event_id))
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Cancelled")  # terminal whatever a consumer does
		self.assertEqual(cancellation_delivery.status_for(self.name)[0]["status"], "Failed")
		self.assertEqual(self.decision()["delivery"][0]["label"], "Bid Opening")
		with mock.patch.object(consumer, "deliver", return_value={"receipt": "R-1"}) as deliver:
			self.assertEqual(cancellation_delivery.run(tender=self.name), {"delivered": 1, "failed": 0})
			args = deliver.call_args.kwargs
			self.assertEqual((args["cancellation"], args["event_id"], args["tender"]), (result["cancellation"], event.event_id, self.name))
			self.assertEqual(args["payload"]["resulting_status"], "Cancelled")  # the original event's payload, not a new one
		row.reload()
		self.assertEqual((row.status, row.attempts, row.receipt_ref), ("Delivered", 2, "R-1"))
		with mock.patch.object(consumer, "deliver", side_effect=AssertionError("a delivered row is never delivered again")):
			self.assertEqual(cancellation_delivery.run(tender=self.name), {"delivered": 0, "failed": 0})
		self.assertEqual(frappe.db.count("Tender Event", {"tender": self.name, "event_type": "TenderCancelled"}), 1)

	def test_a_consumer_that_returns_no_receipt_is_not_delivered(self):
		self.verify("INADEQUATE_BUDGET")
		consumer = importlib.import_module(CONSUMER)
		with mock.patch.object(consumer, "deliver", return_value={}):
			self.cancel()
			frappe.db.commit()
		self.assertEqual(frappe.db.get_value("Tender Event Delivery", {"tender": self.name}, "status"), "Failed")

	def test_the_cancelling_request_delivers_right_after_its_commit(self):
		self.verify("INADEQUATE_BUDGET")
		consumer = importlib.import_module(CONSUMER)
		with mock.patch.object(consumer, "deliver", return_value={"receipt": "R-AFTER-COMMIT"}) as deliver:
			self.cancel()
			deliver.assert_not_called()  # nothing is delivered while the decision is uncommitted
			frappe.db.commit()
			deliver.assert_called_once()
		self.assertEqual(frappe.db.get_value("Tender Event Delivery", {"tender": self.name}, "receipt_ref"), "R-AFTER-COMMIT")

	def test_a_tender_cancelled_before_the_ledger_existed_gets_its_rows_from_the_same_event(self):
		self.verify("INADEQUATE_BUDGET")
		self.cancel()
		frappe.db.delete("Tender Event Delivery", {"tender": self.name})
		self.assertEqual(cancellation_delivery.ensure_registered(self.name), 1)
		self.assertEqual(cancellation_delivery.ensure_registered(self.name), 0)


class TestContract(PostCloseCase):
	def test_the_four_codes_carry_the_words_of_the_error_contract(self):
		self.assertEqual(len(errors.ERROR_CODES), 39)
		self.assertEqual(errors.MESSAGES["TND_CANCEL_TOO_LATE"], "It is too late to cancel this Tender: the award has been notified.")
		self.assertEqual(errors.MESSAGES["TND_CANCELLATION_UNAVAILABLE"], "Cancellation is unavailable. Opening access support is checking the problem.")
		self.assertEqual(errors.MESSAGES["TND_AWARD_STATUS_UNAVAILABLE"], "We cannot confirm that cancellation is permitted from the current award status.")
		self.assertEqual(errors.MESSAGES["TND_CANCEL_GROUND_UNVERIFIED"], "A verified cancellation basis is needed before this tender can be cancelled.")

	def test_the_open_route_is_unchanged_and_needs_no_verified_ground(self):
		"""A Tender still open for submission is cancelled exactly as before: the ground catalogue, no verifier, the same Award fence."""
		frappe.db.set_value("Tender", self.name, {"overall_status": "Published — open"})  # the same Tender, before its period ended
		shown = self.decision()
		self.assertEqual((shown["decision"]["stage"], shown["decision"]["allowed"]), ("open", True))
		self.assertEqual(len(shown["grounds"]), len(cancellation.CANCELLATION_GROUNDS))
		self.assertIn("cancel_tender", shown["allowed_actions"])
