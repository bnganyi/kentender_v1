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
from unittest import mock

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import price, reads, save, security_intake, start_bid
from kentender_procurement.bid_submission.services import security_duty, security_matching, tender_security
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, KISIWA, PETER, BidCase, assign_intake_officer, key, opening_crossed, simulation_on
from kentender_procurement.tenders.services import bid_definition
from kentender_procurement.tenders.tests import fixtures as tender_fx

ISSUER, REFERENCE = "KCB Bank Kenya", "KCB/TG/2027/8841"
UPLOAD, ISSUER_SUPPLIED, PAPER = tender_security.UPLOAD, tender_security.ISSUER, tender_security.PAPER


class SecurityCase(BidCase):
	def setUp(self):
		super().setUp()
		simulation_on(self)
		assign_intake_officer(self)
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
		return security_intake.record_physical_tender_security_receipt(**values, idempotency_key=key(), user=user or tender_fx.OFFICER)


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
	def test_only_the_assigned_officer_records_and_bad_input_is_named(self):
		for user in (DAVID, tender_fx.HOPF, tender_fx.AO, tender_fx.NOBODY, "Administrator"):
			with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
				self.intake(user=user)
		refused = self.intake(received_at="2030-01-01 09:00:00", instrument_type="Cash", confirmed=False, tender_reference=self.reference)
		self.assertEqual((refused["ok"], sorted(refused["errors"])), (False, ["confirmed", "instrument_type", "received_at"]))
		# the duty is Tender-scoped: another Tender's reference, real or not, is the same refusal
		with self.assertRaises(frappe.PermissionError):
			self.intake(tender_reference="TND-NOPE-0000-000")

	def test_the_intake_answer_is_the_same_whether_or_not_a_bid_exists(self):
		"""An empty and a populated sealed box answer identically: the intake never looks at a bid."""
		empty = self.intake(instrument_reference="NO-SUCH-GUARANTEE")
		self.answer_security()
		populated = self.intake()
		self.assertEqual(set(empty), set(populated))
		self.assertEqual({k: type(v) for k, v in empty.items()}, {k: type(v) for k, v in populated.items()})
		self.assertRegex(populated["intake_reference"], r"^TSI-[0-9A-F]{10}$")
		self.assertEqual(populated["deadline_class"], "Before deadline")
		listed = security_intake.list_my_intakes(user=tender_fx.OFFICER)
		for payload in (empty, populated, listed):
			text = frappe.as_json(payload)
			for word in ("BID-", "ARR-", "Afya", "bid_workspace", "Matched", "Draft", "Submitted", "bid_count"):
				self.assertNotIn(word, text)
		self.assertEqual([r["intake_reference"] for r in listed["rows"]], [populated["intake_reference"], empty["intake_reference"]])

	def test_an_intake_without_any_bid_is_recorded(self):
		from kentender_procurement.bid_submission.services import tenders_gateway

		frappe.db.delete("Bid Workspace", {"tender": self.name})
		recorded = self.intake()
		self.assertTrue(recorded["ok"])
		self.assertEqual(frappe.db.count("Tender Security Intake", {"tender": self.name}), 1)

	def test_the_intake_code_never_reads_a_bid(self):
		"""The intake module imports no bid or match table and never matches."""
		import inspect

		source = inspect.getsource(security_intake)
		for forbidden in ("Bid Workspace", "Bid Submission Version", "Tender Box Envelope", "Bidder Arrangement", "match_tender(", "receipt_for("):
			self.assertNotIn(forbidden, source)

	def test_a_physical_original_and_an_issuer_confirmation_keep_their_times_apart(self):
		self.at("2027-05-20 10:30:00")
		physical = self.intake(received_at="2027-05-20 09:00:00")
		self.assertEqual((physical["intake_kind"], physical["issuer_confirmed_at"]), ("Physical original", ""))
		confirmation = self.intake(intake_kind="Issuer confirmation", received_at="2027-05-20 10:00:00", issuer_confirmed_at="2027-05-20 09:41:00", instrument_reference="KCB/TG/2027/9001")
		self.assertTrue(confirmation["ok"], confirmation)
		doc = frappe.get_doc("Tender Security Intake", {"intake_reference": confirmation["intake_reference"]})
		self.assertEqual((str(doc.received_at), str(doc.issuer_confirmed_at), str(doc.recorded_at), doc.recorded_by, doc.intake_kind),
			("2027-05-20 10:00:00", "2027-05-20 09:41:00", "2027-05-20 10:30:00", tender_fx.OFFICER, "Issuer confirmation"))
		missing = self.intake(intake_kind="Issuer confirmation", received_at="2027-05-20 10:00:00")
		self.assertEqual(missing["errors"], {"issuer_confirmed_at": "Enter the date and time the issuer confirmed the instrument."})
		later = self.intake(intake_kind="Issuer confirmation", received_at="2027-05-20 10:00:00", issuer_confirmed_at="2027-05-20 10:10:00")
		self.assertEqual(later["errors"], {"issuer_confirmed_at": "The issuer cannot have confirmed after you received the confirmation."})
		stray = self.intake(received_at="2027-05-20 10:00:00", issuer_confirmed_at="2027-05-20 09:41:00")
		self.assertEqual(stray["errors"], {"issuer_confirmed_at": "Only an issuer confirmation has an issuer confirmation time."})
		self.assertEqual(self.intake(intake_kind="Postal", received_at="2027-05-20 10:00:00")["errors"]["intake_kind"], "Choose what was received: physical original or issuer confirmation.")

	def test_the_deadline_class_is_decided_by_the_actual_receipt_time_and_the_recording_time_is_kept_apart(self):
		from datetime import timedelta

		from frappe.utils import get_datetime

		deadline = get_datetime(frappe.db.get_value("Tender", self.name, "submission_deadline"))
		self.at(str(deadline + timedelta(hours=3)))  # recorded well after the deadline ...
		late = self.intake(received_at=str(deadline + timedelta(hours=1)), instrument_reference="KCB/TG/LATE/1")
		early = self.intake(received_at=str(deadline - timedelta(hours=1)), instrument_reference="KCB/TG/EARLY/1")  # ... but received before it: never classed by the recording time
		self.assertEqual((late["deadline_class"], early["deadline_class"]), ("After deadline", "Before deadline"))
		doc = frappe.get_doc("Tender Security Intake", {"intake_reference": early["intake_reference"]})
		self.assertEqual((get_datetime(doc.received_at), get_datetime(doc.recorded_at)), (deadline - timedelta(hours=1), deadline + timedelta(hours=3)))

	def test_an_intake_is_append_only_with_the_server_actor_and_time(self):
		self.at("2027-05-20 10:30:00")
		recorded = self.intake(received_at="2027-05-20 10:00:00")
		doc = frappe.get_doc("Tender Security Intake", {"intake_reference": recorded["intake_reference"]})
		self.assertEqual((doc.recorded_by, str(doc.recorded_at), doc.deadline_class), (tender_fx.OFFICER, "2027-05-20 10:30:00", "Before deadline"))
		doc.issuer = "Another bank"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Tender Security Intake", doc.name, ignore_permissions=True)

	def test_recording_and_viewing_are_logged_as_exposure_and_a_revoked_officer_loses_access(self):
		recorded = self.intake()
		self.assertTrue(frappe.db.exists("Tender Security Exposure", {"tender": self.name, "user": tender_fx.OFFICER, "kind": security_duty.RECORDED, "intake_reference": recorded["intake_reference"]}))
		security_intake.list_my_intakes(user=tender_fx.OFFICER)
		self.assertTrue(frappe.db.exists("Tender Security Exposure", {"tender": self.name, "user": tender_fx.OFFICER, "kind": security_duty.VIEWED}))
		assignment = frappe.db.get_value("User Responsibility Assignment", {"business_role": security_duty.ROLE, "scope_reference": self.reference, "status": "Enabled"}, "name")
		security_duty.revoke_intake_officer(assignment=assignment, reason="The duty ended with the Tender's deadline.", user=tender_fx.HOPF)
		with self.assertRaises(frappe.PermissionError):
			security_intake.list_my_intakes(user=tender_fx.OFFICER)
		with self.assertRaises(frappe.PermissionError):
			self.intake()


class TestPrivateMatch(SecurityCase):
	"""The supplier reads its own actual security status at once (Project Owner, 10 October 2026); the stored match,
	which links an intake to a bid for the opening, exists only after the opening boundary is crossed."""

	NOTE = "This Tender requires the original tender security to be delivered before the deadline. Its receipt is not yet recorded; this does not block electronic submission. Security will be checked against your bid after opening."

	def test_before_the_opening_the_supplier_sees_the_actual_status_and_nothing_is_stored(self):
		self.answer_security()
		before = self.task("company")["security"]
		self.assertEqual((before["required"], before["physical_receipt_status"], before["physical_receipt_reference"]), (True, "Original receipt not yet recorded", ""))
		self.assertEqual(frappe.db.count("Tender Security Intake Match", {"tender": self.name}), 0)
		self.assertIn(self.NOTE, [n["text"] for n in reads.get_bid_review(bid_reference=self.bid, user=DAVID)["review_notes"]])
		recorded = self.intake()
		after = self.task("company")["security"]
		self.assertEqual((after["physical_receipt_status"], after["physical_receipt_reference"], after["physical_received_at"]), ("Original received", recorded["intake_reference"], "19 May 2027, 09:00 EAT"))
		self.assertEqual(frappe.db.count("Tender Security Intake Match", {"tender": self.name}), 0)  # still no stored link before the boundary
		self.assertNotIn(self.NOTE, [n["text"] for n in reads.get_bid_review(bid_reference=self.bid, user=DAVID)["review_notes"]])
		for word in ("not yet matched", "Not yet matched"):
			self.assertNotIn(word, frappe.as_json(self.task("company")))

	def test_an_exact_match_is_ignored_for_case_and_spacing_and_stored_only_after_the_opening_starts(self):
		recorded = self.intake(issuer="kcb bank  kenya", instrument_reference="kcb/tg/2027/8841")  # case and spacing do not matter
		self.answer_security()  # the supplier's save runs the (guarded) match too
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Original received")
		self.assertEqual(frappe.db.count("Tender Security Intake Match", {"tender": self.name}), 0)
		opening_crossed(self)
		security_matching.match_tender(self.name)
		after = self.task("company")["security"]
		self.assertEqual((after["physical_receipt_status"], after["physical_receipt_reference"]), ("Original received", recorded["intake_reference"]))
		self.assertEqual(frappe.db.count("Tender Security Intake Match", {"tender": self.name, "status": "Matched"}), 1)

	def test_a_different_amount_or_two_identical_bids_is_not_shown_as_received(self):
		self.answer_security()
		self.intake(amount=str(Decimal(self.facts["amount"]) * 2))
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Original receipt not yet recorded")
		other = self.start(PETER, KISIWA)
		self.answer_security(bid=other, user=PETER)
		self.intake()
		# two bids carry the same instrument: neither is told it was received, so nobody learns of another's instrument
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Original receipt not yet recorded")
		self.assertEqual(self.task("company", other, PETER)["security"]["physical_receipt_status"], "Original receipt not yet recorded")
		opening_crossed(self)
		security_matching.match_tender(self.name)
		self.assertTrue(frappe.db.exists("Tender Security Intake Match", {"tender": self.name, "status": "Ambiguous"}))

	def test_a_bid_without_a_physical_original_is_unaffected(self):
		"""Electronic submission and its receipt never depend on the original."""
		self.answer_security()
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Original receipt not yet recorded")
		review = reads.get_bid_review(bid_reference=self.bid, user=DAVID)
		self.assertTrue([n for n in review["review_notes"] if "not yet recorded" in n["text"]])  # a Review note, not a Must fix
		self.assertFalse([i for i in review.get("must_fix", []) if "tender-security" in cstr(i).lower()])

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

		for user in (tender_fx.HOPF, tender_fx.AO, tender_fx.NOBODY, "Administrator"):
			for fn, kwargs in ((api.list_my_tender_security_intakes, {}), (api.get_tender_security_requirement, {"tender_reference": self.reference}), (api.get_my_tender_security_tenders, {})):
				with self.subTest(user=user, fn=fn.__name__):
					self.assertEqual(self.call_as(user, fn, **kwargs), api.FORBIDDEN_INTAKE)
		lookup = self.call_as(tender_fx.OFFICER, api.get_tender_security_requirement, tender_reference=self.reference)
		self.assertEqual(set(lookup), {"outcome", "found", "required", "tender_reference", "permitted_forms", "currency", "required_amount", "deadline", "requirement"})
		self.assertIn("An original must be delivered", lookup["requirement"])
		self.assertEqual((lookup["outcome"], lookup["permitted_forms"]), ("OK", self.facts["permitted_forms"]))
		self.assertEqual(self.call_as(tender_fx.OFFICER, api.list_my_tender_security_intakes, tender_reference=self.reference)["rows"], [])
		mine = self.call_as(tender_fx.OFFICER, api.get_my_tender_security_tenders)
		self.assertEqual([t["tender_reference"] for t in mine["tenders"]], [self.reference])
		self.assertEqual(frappe.allowed_http_methods_for_whitelisted_func[api.record_physical_tender_security_receipt], ["POST"])
		self.assertEqual(frappe.allowed_http_methods_for_whitelisted_func[api.list_my_tender_security_intakes], ["POST"])  # viewing is logged
		self.assertEqual(frappe.allowed_http_methods_for_whitelisted_func[api.get_tender_security_requirement], ["GET"])

	def test_the_head_assigns_through_the_api_and_sees_no_intake(self):
		from kentender_procurement.bid_submission import api

		self.assertEqual(self.call_as(tender_fx.OFFICER, api.assign_tender_security_intake_officer, tender_reference=self.reference, officer=tender_fx.NOBODY), api.FORBIDDEN_DUTY)
		view = self.call_as(tender_fx.HOPF, api.get_tender_security_duty, tender_reference=self.reference)
		self.assertEqual(view["outcome"], "OK")
		self.assertEqual([r["user"] for r in view["assignments"]["rows"]], [tender_fx.OFFICER])
		self.assertNotIn("intake_reference", frappe.as_json(view))
		self.assertEqual(self.call_as(tender_fx.HOPF, api.list_my_tender_security_intakes), api.FORBIDDEN_INTAKE)  # no intake access by office

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
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Original receipt not yet recorded")
		missing = self.intake(corrects=wrong["intake_reference"], correction_reason="")
		self.assertEqual(missing["errors"], {"correction_reason": "Enter the reason for the correction (10–500 characters)."})
		fixed = self.intake(corrects=wrong["intake_reference"], correction_reason="The guarantee number was typed with two digits swapped.")
		self.assertEqual((fixed["ok"], fixed["corrects"]), (True, wrong["intake_reference"]))
		self.assertEqual(self.task("company")["security"]["physical_receipt_reference"], fixed["intake_reference"])
		rows = {r["intake_reference"]: r for r in security_intake.list_my_intakes(user=tender_fx.OFFICER)["rows"]}
		self.assertEqual((rows[wrong["intake_reference"]]["status"], rows[wrong["intake_reference"]]["corrected_by"]), ("Corrected", fixed["intake_reference"]))
		self.assertEqual((rows[fixed["intake_reference"]]["status"], rows[fixed["intake_reference"]]["corrects"]), ("Current", wrong["intake_reference"]))
		again = self.intake(corrects=wrong["intake_reference"], correction_reason="Trying to correct the same receipt twice.")
		self.assertEqual(again["errors"], {"corrects": f"This receipt was already corrected by {fixed['intake_reference']}. Correct that one instead."})
		unknown = self.intake(corrects="TSI-0000000000", correction_reason="A receipt that does not exist at all.")
		self.assertEqual(unknown["errors"], {"corrects": "No tender-security receipt has this reference."})
		self.assertTrue(frappe.db.exists("Tender Security Intake", {"intake_reference": wrong["intake_reference"]}))  # nothing deleted

	def test_a_correction_to_an_unknown_tender_changes_nothing(self):
		opening_crossed(self)
		self.answer_security()
		first = self.intake()
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Original received")
		self.assertIn(first["intake_reference"], [frappe.db.get_value("Tender Security Intake", r.name, "intake_reference") for r in security_matching.active_intakes(self.name)])
		# corrected to a Tender reference the officer has no duty for → refused before anything is read; the first stays current
		with self.assertRaises(frappe.PermissionError):
			self.intake(corrects=first["intake_reference"], correction_reason="Recorded against the wrong Tender reference.", tender_reference="TND-NOPE-0000-000")
		self.assertEqual(self.task("company")["security"]["physical_receipt_status"], "Original received")


class TestTenderStatesTheOriginal(SecurityCase):
	"""Project Owner, 10 October 2026: "security required" never means "physical original required" by itself. The Tender
	states how its security is submitted and whether an original is delivered; the supplier's screens follow those
	statements, and a Tender that states neither has no original invented for it."""

	def stated(self, method, original):
		return mock.patch.object(tender_security, "requirement", return_value=tender_security.requirement({"submission_method": method, "original_delivery": original}))

	def test_the_published_facts_carry_the_tenders_own_statements(self):
		self.assertEqual((self.facts["submission_method"], self.facts["original_delivery"]), (UPLOAD, "Required"))
		view = self.task("company")["tender_security"]
		self.assertEqual(view["requirement"], "Upload your tender security, the electronic instrument, here. An original must be delivered before the submission deadline.")

	def test_the_wording_for_every_combination(self):
		cases = {
			(UPLOAD, "Required"): "Upload your tender security, the electronic instrument, here. An original must be delivered before the submission deadline.",
			(UPLOAD, "Not required"): "Upload your tender security, the electronic instrument, here. No original is required.",
			(ISSUER_SUPPLIED, "Not required"): "Your issuer supplies your tender security directly to the procuring entity. Enter the instrument's details here; you do not upload it. No original is required.",
			(PAPER, "Required"): "Upload the prescribed electronic copy of your paper tender security here. The original must be delivered before the submission deadline.",
		}
		for (method, original), text in cases.items():
			with self.subTest(method=method, original=original):
				self.assertEqual(tender_security.requirement_text(method, original), text)
		self.assertEqual(tender_security.requirement_text("", ""), "")
		self.assertEqual(tender_security.requirement_text(UPLOAD, ""), "")  # half a statement is no statement
		self.assertEqual(tender_security.requirement_text("Electronic", "Required"), "")  # a retired value states nothing

	def test_no_original_required_means_no_advisory_and_no_status_about_one(self):
		self.answer_security()
		with self.stated(UPLOAD, "Not required"):
			view = self.task("company")["security"]
			self.assertEqual((view["physical_original_required"], view["physical_receipt_status"]), (False, "No original required"))
			notes = [n["text"] for n in reads.get_bid_review(bid_reference=self.bid, user=DAVID)["review_notes"]]
			self.assertFalse([n for n in notes if "original" in n.lower()])

	def test_a_tender_that_states_nothing_gets_no_invented_original(self):
		self.answer_security()
		with self.stated("", ""):
			view = self.task("company")["security"]
			self.assertEqual((view["requirement_stated"], view["physical_original_required"], view["physical_receipt_status"]), (False, False, "Original delivery not stated"))
			self.assertEqual(view["requirement_text"], "")
			notes = [n["text"] for n in reads.get_bid_review(bid_reference=self.bid, user=DAVID)["review_notes"]]
			self.assertFalse([n for n in notes if "original" in n.lower()])
			shown = self.task("company")["tender_security"]["physical"]
			self.assertEqual(shown["title"], "Original delivery not stated")

	def test_a_paper_instrument_takes_the_electronic_copy_but_no_electronic_submission(self):
		from kentender_procurement.bid_submission.services import security_verification

		self.answer_security()
		with self.stated(PAPER, "Required"):
			self.assertIsNone(self.task("company")["tender_security"]["electronic"])
			refused = None
			try:
				security_verification.submit_tender_security(bid_reference=self.bid, expected_record_version=frappe.db.get_value("Bid Workspace", self.bid, "record_version"), idempotency_key=key(), user=DAVID)
			except Exception as caught:  # BidSubmissionError
				refused = str(caught)
			self.assertIn("does not accept tender security submitted electronically", refused or "")
			self.assertTrue(self.task("company")["security"]["physical_original_required"])
		self.assertIsNotNone(self.task("company")["tender_security"]["electronic"])  # the Tender that permits it still shows it

	def test_an_issuer_supplied_tender_has_no_upload_and_a_pending_issuer_blocks_nothing(self):
		"""Release 1.5 gives the issuer-supplied method its own group (no attachment). The fixture Tender is bound to the upload
		group, so the issuer group is stood in for by the facts the group would carry: nothing to upload, nothing missing."""
		from kentender_procurement.bid_submission.services import security_verification as sv

		facts = {"security_type": "Demand Bank Guarantee", "issuer": ISSUER, "reference": REFERENCE, "amount": "500000.00", "valid_until": "2027-11-15", "proof": [], "proof_expected": False}
		self.assertEqual(sv.missing(facts), {})  # no proof is required where the group has no attachment
		self.assertEqual(sv.missing({**facts, "proof_expected": True}), {"proof": "Add the instrument's proof."})
		with self.stated(ISSUER_SUPPLIED, "Not required"):
			view = self.task("company")["security"]
			self.assertTrue(view["issuer_supplied"])
			self.assertTrue(view["electronic_permitted"])
		# a pending issuer answer never blocks submitting the bid: it is no Must fix
		self.answer_security()
		review = reads.get_bid_review(bid_reference=self.bid, user=DAVID)
		self.assertFalse([i for i in review.get("must_fix", []) if "issuer" in cstr(i).lower() or "verif" in cstr(i).lower()])

	def test_a_correction_states_what_a_tender_published_without_statements_already_says(self):
		with mock.patch.object(tender_security.tenders_gateway, "security_statement_correction", return_value={"submission_method": PAPER, "original_delivery": "Required"}):
			self.assertEqual(tender_security.statements({}, self.name), {"submission_method": PAPER, "original_delivery": "Required"})
			# a published statement is never replaced by a correction
			published = {"submission_method": UPLOAD, "original_delivery": "Not required"}
			self.assertEqual(tender_security.statements(published, self.name), published)
