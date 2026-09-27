# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §5.14 and plan D15 (plan Phase 10, BDS8-1001): a ready bid
gives the Authorised Signatory "Review and submit BID-…" and the
representative the waiting line; a blocking operational condition replaces
that item with the matching waiting line and an incident for the current
Release or Technical Operator; an unconfirmed attempt is the Technical
Operator's; each clears from the event that ends it — never from a read."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.bid_submission.services import handoffs, reads, save, simulation, submission
from kentender_procurement.bid_submission.tests.support import DAVID, MARY, key
from kentender_procurement.bid_submission.tests.test_guidance import DANIEL, NADIA, GuidanceCase


class HandoffCase(GuidanceCase):
	def open_rows(self):
		return {r.kind: r for r in frappe.get_all("Bid Hand-off", filters={"bid_workspace": self.bid, "status": "Open"}, fields=["kind", "holder_users", "sender_users", "item_title", "waiting_title", "notification_result"])}

	def incident(self, key_):
		return frappe.db.get_value("Bid Submission Incident", {"incident_key": key_}, ["status", "holder_users", "reference"], as_dict=True)


class TestReadyHandoff(HandoffCase):
	def test_ready_gives_mary_the_item_and_david_the_waiting_line_until_submitted(self):
		rows = self.open_rows()
		self.assertEqual(list(rows), ["Review and submit"])
		ready = rows["Review and submit"]
		self.assertEqual((json.loads(ready.holder_users), json.loads(ready.sender_users), ready.item_title), ([MARY], [DAVID], f"Review and submit {self.bid}"))
		self.assertEqual(reads.get_my_bids(user=MARY)["work"], [{"bid_reference": self.bid, "kind": "item", "title": f"Review and submit {self.bid}"}])
		self.assertEqual(reads.get_my_bids(user=DAVID)["work"], [{"bid_reference": self.bid, "kind": "waiting", "title": f"Waiting for Mary Wanjiku to submit {self.bid}"}])
		# reads never open or clear anything
		before = frappe.db.count("Bid Hand-off")
		reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)
		reads.get_bid_review(bid_reference=self.bid, user=MARY)
		self.assertEqual(frappe.db.count("Bid Hand-off"), before)
		# back to Draft clears it; ready again reopens it and messages Mary
		field = next(f for g in reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)["groups"] for f in g["fields"] if f["label"] == "Offered make and model")
		self.assertTrue(save.save_bid_task(bid_reference=self.bid, task="requirements", values={field["handle"]: None}, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)["ok"])
		self.assertEqual(self.open_rows(), {})
		sent = []
		self._flag("kt_bds_message_transport", lambda message: sent.append(message) or {"result": "Sent"})
		self.assertTrue(save.save_bid_task(bid_reference=self.bid, task="requirements", values={field["handle"]: "ApexBook Pro 14"}, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)["ok"])
		self.assertEqual([(m["to"], m["subject"]) for m in sent], [(MARY, f"Review and submit {self.bid}")])
		self.assertEqual(self.open_rows()["Review and submit"].notification_result, "Sent")
		self.assertTrue(self.submit(self.signed())["ok"])
		self.assertEqual(self.open_rows(), {})
		self.assertEqual(frappe.db.get_value("Bid Hand-off", {"bid_workspace": self.bid}, "clear_reason"), "Bid is now Submitted")


class TestOperationalHandoffs(HandoffCase):
	def test_a_closed_gate_is_the_release_operators_and_clears_when_it_opens(self):
		simulation.set_controls(gate_closed=1)
		handoffs.sweep()
		rows = self.open_rows()
		self.assertEqual(list(rows), ["Waiting for production submission availability"])
		self.assertEqual(json.loads(rows["Waiting for production submission availability"].sender_users), [MARY])
		gate = self.incident("production-gate")
		self.assertEqual((gate.status, json.loads(gate.holder_users)), ("Open", [NADIA]))
		self.assertTrue(frappe.db.exists("Notification Log", {"for_user": NADIA, "document_type": "Bid Submission Incident"}))
		simulation.set_controls(gate_closed=0)
		handoffs.sweep()
		self.assertEqual((self.incident("production-gate").status, list(self.open_rows())), ("Resolved", ["Review and submit"]))

	def test_an_unconfirmed_attempt_is_the_technical_operators_until_reconciled(self):
		simulation.set_controls(deposit_outcome="Uncertain")
		pending = self.submit(self.signed())
		self.assertEqual(list(self.open_rows()), ["Waiting for the result of this submission attempt"])
		attempt = self.incident(f"attempt:{pending['correlation_id']}")
		self.assertEqual((attempt.status, json.loads(attempt.holder_users), attempt.reference), ("Open", [DANIEL], pending["correlation_id"]))
		simulation.set_controls(uncertain_resolution="Accept")
		submission.reconcile_uncertain_attempts()
		self.assertEqual((self.incident(f"attempt:{pending['correlation_id']}").status, self.open_rows()), ("Resolved", {}))

	def test_the_deadline_clears_every_hand_off(self):
		self.assertTrue(self.open_rows())
		self.at(str(self.deadline()))
		handoffs.sweep()
		self.assertEqual(self.open_rows(), {})


from kentender_procurement.bid_submission.tests.test_addendum_refresh import AddendumCase  # noqa: E402


class TestAddendumHandoff(AddendumCase):
	def test_an_effective_addendum_gives_the_preparer_a_named_review_item(self):
		name = self.issue_addendum()
		reference = frappe.db.get_value("Tender Addendum", name, "addendum_reference")
		self.at("2027-06-01 12:05:00")
		handoffs.sweep()
		row = frappe.get_all("Bid Hand-off", filters={"bid_workspace": self.bid, "status": "Open"}, fields=["kind", "holder_users", "item_title", "sender_users"])
		self.assertEqual([(r.kind, json.loads(r.holder_users), r.item_title, json.loads(r.sender_users)) for r in row], [("Review addendum", [DAVID], f"Review {reference} for {self.bid}", [])])
