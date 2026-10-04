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

from kentender_procurement.bid_submission.services import price, reads, save, security_intake, start_bid
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
		self.assertEqual((priced["subtotal"], priced["tax"]), (f"KES {quantity * Decimal('160000'):,.2f}", "KES 6,400,000.00"))

	def test_the_worked_fixture_and_half_up_rounding(self):
		# The test world's line has quantity 1; the BDS-CHG-001 §10.1 fixture is
		# 250 laptops at 160,000 with 6,400,000 tax, a bid total of 46,400,000.
		def ctx(quantity, unit_price, tax):
			row = {"calculation": {"calculation_id": "CALC-LINE-TOTAL"}, "input_response_ids": {"unit_price": "u", "tax_amount": "t"}, "quantity": quantity, "currency": "KES", "line": "1"}
			return type("Ctx", (), {"model": type("Model", (), {"price_rows": [row]})(), "values": {"u": unit_price, "t": tax}})()

		fixture = price.summary(ctx("250", "160000", "6400000"))
		self.assertEqual((fixture["subtotal"], fixture["tax"], fixture["total"]), ("KES 40,000,000.00", "KES 6,400,000.00", "KES 46,400,000.00"))
		rounded = price.calculate(ctx("3", "100.125", "0.005"))
		self.assertEqual((rounded["subtotal"], rounded["tax"], rounded["total"]), (Decimal("300.39"), Decimal("0.01"), Decimal("300.40")))


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

	def test_an_intake_is_append_only_with_the_server_actor_and_time(self):
		self.at("2027-05-20 10:30:00")
		recorded = self.intake(received_at="2027-05-20 10:00:00")
		doc = frappe.get_doc("Tender Security Intake", {"intake_reference": recorded["intake_reference"]})
		self.assertEqual((doc.recorded_by, str(doc.recorded_at), doc.deadline_class), (tender_fx.HOPF, "2027-05-20 10:30:00", "Before deadline"))
		doc.issuer = "Another bank"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Tender Security Intake", doc.name, ignore_permissions=True)


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


class TestReceiptsDeskPage(SecurityCase):
	"""The Desk page's endpoints: a refusal is returned as data (the page shows
	it as a state, never a Frappe dialog); the lookup gives only the published
	Tender's own security facts; recording is POST only."""

	def call_as(self, user, fn, **kwargs):
		frappe.set_user(user)
		try:
			return fn(**kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_endpoints_refuse_as_data_and_the_lookup_is_public_facts_only(self):
		from kentender_procurement.bid_submission import api

		for fn, kwargs in ((api.list_my_tender_security_intakes, {}), (api.get_tender_security_requirement, {"tender_reference": self.reference})):
			self.assertEqual(self.call_as(tender_fx.OFFICER, fn, **kwargs), api.FORBIDDEN_INTAKE)
		lookup = self.call_as(tender_fx.HOPF, api.get_tender_security_requirement, tender_reference=self.reference)
		self.assertEqual(set(lookup), {"outcome", "found", "required", "tender_reference", "permitted_forms", "currency", "required_amount", "deadline"})
		self.assertEqual((lookup["outcome"], lookup["permitted_forms"]), ("OK", self.facts["permitted_forms"]))
		self.assertEqual(self.call_as(tender_fx.HOPF, api.list_my_tender_security_intakes, tender_reference=self.reference)["rows"], [])
		self.assertEqual(frappe.allowed_http_methods_for_whitelisted_func[api.record_physical_tender_security_receipt], ["POST"])
		for fn in (api.list_my_tender_security_intakes, api.get_tender_security_requirement):
			self.assertEqual(frappe.allowed_http_methods_for_whitelisted_func[fn], ["GET"])

	def test_the_page_is_installed_and_wired(self):
		self.assertEqual(frappe.db.get_value("Page", "tender-security-receipts", ["module", "title"]), ("Bid Submission", "Tender-security receipts"))
		self.assertEqual(frappe.get_hooks("page_js", app_name="kentender_procurement")["tender-security-receipts"], ["public/js/tender_security_receipts_page.js"])


class TestIntakeCorrection(SecurityCase):
	"""Owner decision 27 Sep 2026: a recorded original is corrected by a new,
	linked intake with a reason; the first stays in the record (append-only)
	and stops counting for the private match."""

	def test_a_correction_is_a_new_linked_intake_and_the_first_stops_counting(self):
		self.answer_security()
		wrong = self.intake(instrument_reference="KCB/TG/2027/8814")  # digits swapped
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Not recorded")
		missing = self.intake(corrects=wrong["intake_reference"], correction_reason="")
		self.assertEqual(missing["errors"], {"correction_reason": "Enter the reason for the correction (10–500 characters)."})
		fixed = self.intake(corrects=wrong["intake_reference"], correction_reason="The guarantee number was typed with two digits swapped.")
		self.assertEqual((fixed["ok"], fixed["corrects"]), (True, wrong["intake_reference"]))
		self.assertEqual(self.task("company")["security"]["physical_receipt_reference"], fixed["intake_reference"])
		rows = {r["intake_reference"]: r for r in security_intake.list_my_intakes(user=tender_fx.HOPF)["rows"]}
		self.assertEqual((rows[wrong["intake_reference"]]["status"], rows[wrong["intake_reference"]]["corrected_by"]), ("Corrected", fixed["intake_reference"]))
		self.assertEqual((rows[fixed["intake_reference"]]["status"], rows[fixed["intake_reference"]]["corrects"]), ("Current", wrong["intake_reference"]))
		again = self.intake(corrects=wrong["intake_reference"], correction_reason="Trying to correct the same receipt twice.")
		self.assertEqual(again["errors"], {"corrects": f"This receipt was already corrected by {fixed['intake_reference']}. Correct that one instead."})
		unknown = self.intake(corrects="TSI-0000000000", correction_reason="A receipt that does not exist at all.")
		self.assertEqual(unknown["errors"], {"corrects": "No tender-security receipt has this reference."})
		self.assertTrue(frappe.db.exists("Tender Security Intake", {"intake_reference": wrong["intake_reference"]}))  # nothing deleted

	def test_a_correction_to_an_unknown_tender_changes_nothing(self):
		from kentender_procurement.bid_submission.services import security_matching

		self.answer_security()
		first = self.intake()
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Recorded before deadline")
		self.assertIn(first["intake_reference"], [frappe.db.get_value("Tender Security Intake", r.name, "intake_reference") for r in security_matching.active_intakes(self.name)])
		# corrected to a Tender reference that exists but needs no security → refused; the first stays current
		self.assertEqual(self.intake(corrects=first["intake_reference"], correction_reason="Recorded against the wrong Tender reference.", tender_reference="TND-NOPE-0000-000")["errors"]["tender_reference"], "No published Tender has this reference.")
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Recorded before deadline")
