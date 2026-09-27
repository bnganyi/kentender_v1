# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.11, §5.8, §5.9, §7.3 and plan D9 (plan Phase 9,
BDS8-901): a replacement becomes current only when the tender box accepts it,
and the former Version is superseded in that same outcome; a withdrawal needs
the signatory, the current receipt, a 10–500 character reason and the time
before the deadline, and deletes nothing; a withdrawn bid can start again; at
the deadline the box closes, unsent Drafts close without submission, an
unsent replacement leaves its Version current, and one sealed hand-off holds
only identities, lineage, custody proofs and the physical-security intake
inventory."""

from __future__ import annotations

import hashlib
import json

import frappe

from kentender_procurement.bid_submission.services import close, receipts, reads, replacement, save, security_intake, simulation, start_bid, withdrawal
from kentender_procurement.bid_submission.test_services import tender_box
from kentender_procurement.bid_submission.tests.support import DAVID, KISIWA, MARY, PETER, key
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase
from kentender_procurement.tenders.services import bid_definition, submission_close
from kentender_procurement.tenders.tests import fixtures as tender_fx

REASON = "Our pricing changed after the addendum was issued."


class ChangeCase(SubmissionCase):
	def submitted(self, **kw) -> str:
		result = self.submit(self.signed(), **kw)
		self.assertTrue(result["ok"], result)
		return result["receipt_reference"]

	def replace(self, user=MARY):
		return replacement.prepare_replacement_bid(bid_reference=self.bid, expected_record_version=self.version(), idempotency_key=key(), user=user)

	def withdraw(self, reason=REASON, receipt="", user=MARY, confirmed=True):
		return withdrawal.withdraw_bid(bid_reference=self.bid, receipt_reference=receipt, reason=reason, confirmed=confirmed, expected_record_version=self.version(), idempotency_key=key(), user=user)

	def current(self):
		return tuple(frappe.db.get_value("Bid Workspace", self.bid, ["status", "current_submission_version"]))

	def version_status(self, name):
		return frappe.db.get_value("Bid Submission Version", name, "status")

	def edit(self, value, at):
		field = next(f for g in reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)["groups"] for f in g["fields"] if f["label"] == "Offered make and model")
		self.at(at)
		self.assertTrue(save.save_bid_task(bid_reference=self.bid, task="requirements", values={field["handle"]: value}, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)["ok"])


class TestReplacement(ChangeCase):
	def test_a_replacement_becomes_current_only_when_the_tender_box_accepts_it(self):
		first = self.submitted()
		_status, v1 = self.current()
		self.assertEqual(self.code(self.replace, user=DAVID), "BDS_SIGNATORY_REQUIRED")
		self.at("2027-05-31 08:30:00")
		prepared = self.replace()
		self.assertEqual((prepared["ok"], prepared["status"], prepared["started_from"]), (True, "Ready to submit", "Submitted"))
		self.assertEqual((self.current(), self.version_status(v1)), (("Ready to submit", v1), "Submitted"))  # Version 1 stays current
		self.assertEqual(receipts.get_bid_receipt(receipt_reference=first, user=MARY)["status"], "Submitted")
		header = reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)["bid"]
		self.assertEqual(header["current_submission"], {"version_label": "Submitted bid Version 1", "receipt_reference": first})
		self.assertEqual(self.code(self.replace), "BDS_STALE_VERSION")  # already open
		self.edit("ApexBook Pro 15", "2027-05-31 08:45:00")  # the representative works on the replacement Draft
		self.at("2027-05-31 09:15:00")
		# a definite rejection leaves Version 1 current
		simulation.set_controls(deposit_outcome="Reject")
		self.assertEqual(self.submit(self.signed())["code"], "BDS_CUSTODY_REJECTED")
		self.assertEqual((self.current(), self.version_status(v1)), (("Ready to submit", v1), "Submitted"))
		simulation.set_controls(deposit_outcome="Accept")
		# a replacement against a receipt that is no longer current changes nothing
		self.assertEqual(self.code(self.submit, self.signed(), replaces="RCPT-NOT-CURRENT"), "BDS_REPLACEMENT_CONFLICT")
		second = self.submitted(replaces=first)
		_status, v2 = self.current()
		self.assertEqual((self.current(), self.version_status(v1), self.version_status(v2)), (("Submitted", v2), "Superseded", "Submitted"))
		self.assertEqual(frappe.db.get_value("Bid Submission Version", v2, ["version_number", "predecessor_submission_version"]), (2, v1))
		facts = receipts.get_bid_receipt(receipt_reference=second, user=MARY)
		self.assertEqual((facts["submitted_version"], facts["replaces_receipt"], facts["accepted_at"]), ("Submitted bid Version 2", first, "31 May 2027, 09:15:00 EAT"))
		self.assertEqual(receipts.get_bid_receipt(receipt_reference=first, user=MARY)["status"], "Superseded")
		change = frappe.get_all("Bid Submission Change", filters={"bid_workspace": self.bid}, fields=["change_type", "affected_submission_version", "new_submission_version", "acknowledgement_ref"])
		self.assertEqual([dict(c) for c in change], [{"change_type": "Replacement submitted", "affected_submission_version": v1, "new_submission_version": v2, "acknowledgement_ref": second}])


class TestWithdrawal(ChangeCase):
	def test_a_withdrawal_is_deliberate_acknowledged_and_deletes_nothing(self):
		first = self.submitted()
		_status, v1 = self.current()
		self.assertEqual(self.code(self.withdraw, user=DAVID), "BDS_SIGNATORY_REQUIRED")
		for reason in ("x" * 9, "x" * 501):
			self.assertEqual(self.withdraw(reason=reason)["errors"], {"reason": "Enter 10–500 characters."})
		self.assertEqual(self.withdraw(confirmed=False)["errors"], {"confirmed": withdrawal.CONFIRM_TEXT})
		self.assertEqual(self.code(self.withdraw, receipt="RCPT-SOMETHING-ELSE"), "BDS_REPLACEMENT_CONFLICT")
		self.at("2027-05-30 15:00:00")
		ack = self.withdraw(reason="x" * 10, receipt=first)
		self.assertRegex(ack["acknowledgement_reference"], r"^WD-MOH-\d{4}-\d{3}-001$")
		self.assertEqual((ack["withdrawn_by"], ack["withdrawn_at"], ack["status"], ack["withdrawn_receipt"]), ("Mary Wanjiku", "30 May 2027, 15:00:00 EAT", "Withdrawn", first))
		self.assertEqual((self.current(), self.version_status(v1)), (("Withdrawn", None), "Withdrawn"))
		self.assertTrue(frappe.db.exists("Tender Box Envelope", frappe.db.get_value("Bid Submission Version", v1, "tender_box_envelope")))
		self.assertEqual(receipts.get_bid_receipt(receipt_reference=first, user=DAVID)["status"], "Withdrawn")
		self.assertEqual(withdrawal.get_withdrawal_acknowledgement(acknowledgement_reference=ack["acknowledgement_reference"], user=DAVID)["bid_reference"], self.bid)
		with self.assertRaises(frappe.DoesNotExistError):
			withdrawal.get_withdrawal_acknowledgement(acknowledgement_reference=ack["acknowledgement_reference"], user=PETER)
		self.assertEqual(self.code(self.withdraw), "BDS_STALE_VERSION")  # nothing current to withdraw
		# Start replacement: a new Draft, then a new Version and receipt; Version 1 stays Withdrawn
		self.at("2027-05-31 10:00:00")
		self.assertEqual(self.replace()["started_from"], "Withdrawn")
		self.assertEqual(self.current(), ("Ready to submit", None))
		second = self.submitted()
		_status, v2 = self.current()
		self.assertEqual((self.version_status(v1), self.version_status(v2), frappe.db.get_value("Bid Submission Version", v2, "predecessor_submission_version")), ("Withdrawn", "Submitted", v1))
		self.assertNotEqual(second, first)

	def test_after_the_deadline_nothing_can_change(self):
		self.submitted()
		before = self.current()
		self.at(str(self.deadline()))
		self.assertEqual(self.code(self.withdraw), "BDS_WITHDRAWAL_BLOCKED")
		self.assertEqual(self.code(self.replace), "BDS_DEADLINE_PASSED")
		self.assertEqual(self.current(), before)


class TestClose(ChangeCase):
	def test_the_box_closes_drafts_close_and_the_hand_off_is_sealed(self):
		first = self.submitted()
		_status, v1 = self.current()
		self.at("2027-05-31 09:00:00")
		self.replace()  # never submitted
		other = start_bid.start_bid(tender_reference=self.reference, organisation=KISIWA, arrangement=self.single(), notice_contact_id=f"{KISIWA}-C1", idempotency_key=key(), user=PETER)["bid_reference"]
		facts = next(g["published_facts"] for s in bid_definition.current(self.name)["definition"]["sections"] for g in s["groups"] if g["rule_id"] == "RR-TENDER-SECURITY")
		intake = security_intake.record_physical_tender_security_receipt(
			tender_reference=self.reference, instrument_type=facts["permitted_forms"][0], issuer="KCB Bank Kenya", instrument_reference="KCB/TG/HANDOFF/1", amount=facts["amount"],
			currency=facts["currency"], received_at="2027-05-31 08:00:00", confirmed=True, idempotency_key=key(), user=tender_fx.HOPF,
		)["intake_reference"]
		self.at(str(self.deadline()))
		submission_close.close_tender_submission_period(tender=self.name, idempotency_key=key(), user="Administrator")
		self.assertEqual(close.consume_tender_events(tender=self.name)["closed"], 1)
		self.assertEqual(self.current(), ("Submitted", v1))  # the unsent replacement closed; Version 1 stays current
		self.assertEqual(frappe.db.get_value("Bid Workspace", other, ["status", "current_submission_version"]), ("Closed without submission", None))
		self.assertEqual(set(frappe.get_all("Bidder Arrangement", filters={"tender": self.name}, pluck="status")), {"Closed"})
		self.assertEqual(frappe.db.get_value("Tender Event", {"tender": self.name, "event_type": "TenderSubmissionPeriodEnded"}, "status"), "Delivered")
		row = frappe.get_doc("Bid Opening Handoff", {"tender": self.name})
		body = json.loads(row.payload_json)
		self.assertEqual((row.consumer, row.delivery_status, row.handoff_digest), ("bid-opening", "Pending", hashlib.sha256(row.payload_json.encode()).hexdigest()))
		self.assertEqual([(e["bid_reference"], e["receipt_reference"], e["status"]) for e in body["envelopes"]], [(self.bid, first, "Submitted")])  # no Draft in the inventory
		self.assertEqual(body["closed_box"]["custody_inventory"], [body["envelopes"][0]["envelope_id"]])
		self.assertEqual([i["intake_reference"] for i in body["physical_tender_security"]["intakes"]], [intake])
		self.assertEqual(body["unresolved_attempts"], [])
		text = row.payload_json
		for content in ("content_base64", "ApexBook", "Afya Digital Supplies Limited", other):
			self.assertNotIn(content, text)
		self.assertEqual(frappe.db.get_value("Tender Box Envelope", {"tender": self.name}, "box_state"), "Handed to Bid Opening")
		# closed for good: the same close again changes nothing, every command is refused, the box takes nothing
		self.assertTrue(close.close_bid_submission(tender=self.name)["idempotent"])
		self.assertEqual(frappe.db.count("Bid Opening Handoff", {"tender": self.name}), 1)
		self.assertEqual(self.code(self.withdraw), "BDS_WITHDRAWAL_BLOCKED")
		self.assertEqual(self.code(self.replace), "BDS_DEADLINE_PASSED")
		late = tender_box.TestTenderBox().deposit(correlation_id="COR-LATE-TEST", tender=self.name, package=b"{}", package_digest=hashlib.sha256(b"{}").hexdigest(), deadline="2999-01-01 00:00:00", at=self.deadline())
		self.assertEqual(late["result"], "Rejected")
		tender_box.remove(["COR-LATE-TEST"])
		from kentender_procurement.bid_submission import api

		self.assertFalse([n for n in dir(api) if any(w in n.lower() for w in ("reopen", "extend", "backdate", "open_bid", "decrypt"))])
