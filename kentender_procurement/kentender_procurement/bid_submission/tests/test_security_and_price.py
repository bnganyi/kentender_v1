# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.8, §5.5 items 6–7, §5.6, §7.3 and owner decisions
OD-G/OD-H (plan Phase 7, BDS8-701): price totals are calculated exactly on
the server; the physical security original is a Review note until recorded;
the Head of Procurement Function records a blind intake and learns nothing
about bids; only an exact, unique match shows "recorded", and only to that
supplier."""

from __future__ import annotations

from decimal import Decimal

import frappe

from kentender_procurement.bid_submission.services import reads, save, security_intake, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, KISIWA, PETER, BidCase, key, simulation_on
from kentender_procurement.tenders.services import bid_definition
from kentender_procurement.tenders.tests import fixtures as tender_fx

ISSUER, REFERENCE = "KCB Bank Kenya", "KCB/TG/2027/8841"


class SecurityCase(BidCase):
	def setUp(self):
		super().setUp()
		simulation_on(self)
		self.bid = self.start(DAVID, AFYA)
		self.facts = next(g["published_facts"] for s in bid_definition.current(self.name)["definition"]["sections"] for g in s["groups"] if g["rule_id"] == "RR-TENDER-SECURITY")

	def start(self, user, organisation):
		return start_bid.start_bid(tender_reference=self.reference, organisation=organisation, arrangement=self.single(), notice_contact_id=f"{organisation}-C1", idempotency_key=key(), user=user)["bid_reference"]

	def task(self, name, bid=None, user=DAVID):
		return reads.get_bid_task(bid_reference=bid or self.bid, task=name, user=user)

	def handle(self, view, label, **match):
		return next(f["handle"] for g in view["groups"] for f in g["fields"] if f["label"] == label and all(f.get(k) == v for k, v in match.items()))

	def save(self, task, values, bid=None, user=DAVID):
		bid = bid or self.bid
		result = save.save_bid_task(bid_reference=bid, task=task, values=values, expected_record_version=frappe.db.get_value("Bid Workspace", bid, "record_version"), idempotency_key=key(), user=user)
		self.assertTrue(result["ok"], result)
		return result

	def answer_security(self, bid=None, user=DAVID, issuer=ISSUER, reference=REFERENCE, amount=None):
		view = self.task("company", bid, user)
		form = self.handle(view, "Form of Tender Security")
		self.save("company", {form: "Demand Bank Guarantee"}, bid, user)
		view = self.task("company", bid, user)
		values = {
			self.handle(view, "Issuing bank or insurer"): issuer, self.handle(view, "Guarantee number"): reference,
			self.handle(view, "Amount of the instrument"): amount or self.facts["amount"], self.handle(view, "Guarantee valid until", visible=True): self.facts["bank_guarantee_expiry_date"],
		}
		self.save("company", values, bid, user)

	def intake(self, user=None, **overrides):
		values = {
			"tender_reference": self.reference, "instrument_type": "Demand Bank Guarantee", "issuer": ISSUER, "instrument_reference": REFERENCE,
			"amount": self.facts["amount"], "currency": self.facts["currency"], "received_at": "2027-05-19 09:00:00", "notes": "", "confirmed": True, **overrides,
		}
		return security_intake.record_physical_tender_security_receipt(**values, idempotency_key=key(), user=user or tender_fx.HOPF)


class TestPrice(SecurityCase):
	def test_totals_are_calculated_exactly_and_only_when_every_line_is_priced(self):
		view = self.task("price")
		unit, tax = self.handle(view, "Unit price"), self.handle(view, "Taxes payable on this line")
		self.save("price", {unit: "160000"})
		partial = self.task("price")["price"]
		self.assertEqual((partial["complete"], partial["total"]), (False, ""))
		self.save("price", {tax: "6400000"})
		priced = self.task("price")["price"]
		quantity = Decimal(priced["lines"][0]["quantity"])
		expected = quantity * Decimal("160000") + Decimal("6400000")
		self.assertEqual((priced["complete"], priced["total"]), (True, f"KES {expected:,.2f}"))
		self.assertEqual(priced["lines"][0]["amount_before_tax"], f"KES {quantity * Decimal('160000'):,.2f}")
		if quantity == 250:
			self.assertEqual(priced["total"], "KES 46,400,000.00")  # the BDS-CHG-001 §10.1 fixture


class TestBlindIntake(SecurityCase):
	def test_only_the_head_of_procurement_records_and_bad_input_is_named(self):
		for user in (DAVID, tender_fx.OFFICER):
			with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
				self.intake(user=user)
		refused = self.intake(received_at="2030-01-01 09:00:00", instrument_type="Cash", confirmed=False, tender_reference=self.reference)
		self.assertEqual((refused["ok"], sorted(refused["errors"])), (False, ["confirmed", "instrument_type", "received_at"]))
		self.assertEqual(self.intake(tender_reference="TND-NOPE-0000-000")["errors"]["tender_reference"], "No published Tender has this reference.")

	def test_the_intake_answer_is_the_same_whether_or_not_a_bid_matches(self):
		unmatched = self.intake(instrument_reference="NO-SUCH-GUARANTEE")
		self.answer_security()
		matched = self.intake()
		self.assertEqual(set(unmatched), set(matched))
		self.assertEqual({k: type(v) for k, v in unmatched.items()}, {k: type(v) for k, v in matched.items()})
		self.assertRegex(matched["intake_reference"], r"^TSI-[0-9A-F]{10}$")
		self.assertEqual(matched["deadline_class"], "Before deadline")
		for payload in (unmatched, matched, security_intake.list_my_intakes(user=tender_fx.HOPF)):
			text = frappe.as_json(payload)
			for word in ("BID-", "ARR-", "Afya", "bid_workspace", "Matched", "Draft"):
				self.assertNotIn(word, text)
		self.assertEqual([r["intake_reference"] for r in security_intake.list_my_intakes(user=tender_fx.HOPF)["rows"]], [matched["intake_reference"], unmatched["intake_reference"]])


class TestPrivateMatch(SecurityCase):
	def test_an_exact_match_shows_recorded_to_that_supplier_only(self):
		before = self.task("company")["security"]
		self.assertEqual((before["required"], before["physical_receipt_status"]), (True, "Not recorded"))
		notes = reads.get_bid_review(bid_reference=self.bid, user=DAVID)["review_notes"]
		self.assertIn("The physical tender-security original has not been recorded as received.", [n["text"] for n in notes])
		recorded = self.intake(issuer="kcb bank  kenya", instrument_reference="kcb/tg/2027/8841")  # case and spacing do not matter
		self.answer_security()  # the supplier's save runs the match too
		after = self.task("company")["security"]
		self.assertEqual((after["physical_receipt_status"], after["physical_receipt_reference"], after["physical_received_at"]), ("Recorded before deadline", recorded["intake_reference"], "19 May 2027, 09:00 EAT"))
		self.assertNotIn("The physical tender-security original has not been recorded as received.", [n["text"] for n in reads.get_bid_review(bid_reference=self.bid, user=DAVID)["review_notes"]])

	def test_a_different_amount_or_two_identical_bids_is_no_match(self):
		self.answer_security()
		self.intake(amount=str(Decimal(self.facts["amount"]) * 2))
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Not recorded")
		other = self.start(PETER, KISIWA)
		self.answer_security(bid=other, user=PETER)
		self.intake()
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Not recorded")
		self.assertEqual(self.task("company", other, PETER)["security"]["physical_receipt_status"], "Not recorded")
		self.assertTrue(frappe.db.exists("Tender Security Intake Match", {"tender": self.name, "status": "Ambiguous"}))

	def test_no_role_can_read_a_match(self):
		self.assertEqual(frappe.get_meta("Tender Security Intake Match").permissions, [])
