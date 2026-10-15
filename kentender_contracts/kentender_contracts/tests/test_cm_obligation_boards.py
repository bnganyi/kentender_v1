# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 10 boards D13 (S, C), D15 (L), D16 (W, P), D20 (P, T), D35 (V, C, H), D36 (A, E, S, H), D37 (A, P, X), D39 (P, C, H) (plan Phase 8; tracker CM8-803..807): the screen each person gets at each step of
an issue, a warranty claim, a delay adjustment, a security action, a termination and a report.

The server builds each board for the viewer at their step; with `CM_CAPTURE_BOARDS=1` each is written as a fixture for the structural fidelity gate."""

from __future__ import annotations

import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import adjustment, delivery, issues, records, reporting, security, security_actions, termination, warranty
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

EVIDENCE = [{"label": "Default notice and delivery proof", "file": "/private/files/default-notice.pdf"}]


class OpsBoards(ContractCase):
	native = True
	item = ""
	security = False

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)
		world.ensure_workflow()
		cls.addClassCleanup(world.drop_workflow)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: (setattr(frappe.flags, "kt_cm_dispatch_fault", None), setattr(frappe.flags, "kt_cm_funding_fault", None), setattr(frappe.conf, adjustment.MAPPING_FLAG, None), self.env.__exit__(None, None, None)))
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24], item=self.item, security=self.security)
		self.case = self.t.active()
		self.t.appointed()
		frappe.db.set_value("Contract Case", self.case, "responsible_user", self.p["carol"])

	def screen(self, who, expected, capture=True, **kw):
		board = router.board_for(self.case, self.p[who], **kw)
		self.assertEqual(board["id"], expected, f"{who}: {board.get('title')} / {(board.get('next') or {}).get('h')}")
		return tw.capture(board) if capture else board

	def accepted(self, count=10, bad=(), on="2027-07-25 10:00:00", received="2027-07-12 10:00:00"):
		units = tw.fresh_serials(count)
		arrival = self.t.arrive(units, received_at=received)["arrival"]
		self.t.inspect(arrival, units, bad=tuple(units[i] for i in bad))
		frappe.flags.kt_cm_clock = on
		self.t.accept(arrival)
		return units


class TestIssues(OpsBoards):
	def test_a_delivery_issue_from_the_findings_to_the_closed_thread(self):
		units = self.accepted(10, bad=(8, 9), on="2027-07-20 15:00:00")
		owner = self.screen("carol", "D13", tab="Obligations")
		self.assertEqual((owner["title"], owner["p"], owner["next"]["h"], owner["s2"]), ("2 laptop computers need replacement", "Send message", "Send the inspection findings to the supplier.", ["View acceptance report"]))
		facts = owner["regions"][0]["b"][0]["items"]
		self.assertEqual([f[0] for f in facts], ["Units", "Result", "Observed", "Requested remedy", "Requested reply date"])
		self.assertEqual(facts[1], ["Result", "Does not meet"])
		row = issues.get(self.case, 1)
		issues.send_correspondence(self.case, issue=row.name, text="Two laptops did not start during inspection. Please arrange replacement and confirm the delivery date.", expected_version=self.t.version(), idempotency_key=self.t.key("s"), actor=self.p["carol"])
		supplier = self.screen("david", "D13-S")
		self.assertEqual((supplier["p"], supplier["back"], supplier["next"]["h"]), ("Send reply", "Back to my contracts", "Reply to the replacement request."))
		self.assertEqual(supplier["regions"][1]["t"], "Message from Ministry of Health")
		issues.reply_correspondence(self.case, issue=row.name, text="We will deliver two replacement laptops on 27 July 2027.", expected_version=self.t.version(), idempotency_key=self.t.key("r"), actor=self.p["david"])
		new = tw.fresh_serials(2)
		again = delivery.record_arrival(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("ra"), actor=self.p["grace"], received_at="2027-07-26 10:00:00", destination="Afya House store",
			items=[{"line_id": "L1", "quantity": 2, "units": new, "replaces": units[8:]}])["arrival"]
		self.t.inspect(again, new)
		frappe.flags.kt_cm_clock = "2027-07-27 16:00:00"
		self.t.accept(again)
		closed = self.screen("carol", "D13-C", tab="Obligations", subject=("issue", "1"))
		self.assertEqual((closed["next"]["k"], closed["p"], closed["s2"]), ("done", "", ["Report a new issue", "View replacement acceptance"]))
		self.assertIn("Replacement units", closed["regions"][1]["b"][0]["v"])


class TestWarranty(OpsBoards):
	item = world.ITEM_PLAIN

	def setUp(self):
		super().setUp()
		self.units = self.accepted(10, on="2027-07-20 10:00:00")
		frappe.flags.kt_cm_clock = "2028-07-10 09:00:00"

	def claim(self, remedy, unit):
		return warranty.record_claim(self.case, unit=unit, fault="Battery does not charge", notice_date="2028-07-10", remedy=remedy, expected_version=self.t.version(), idempotency_key=self.t.key("claim"), actor=self.p["carol"])

	def row(self):
		return issues.get(self.case, 1)

	def test_a_warranty_claim_from_the_defect_notice_to_the_closed_claim(self):
		self.claim("Like-for-like replacement", self.units[3])
		notice = self.screen("carol", "D16-W", tab="Obligations")
		self.assertEqual((notice["title"], notice["p"], notice["next"]["h"], notice["s2"]), ("Warranty claim", "Send notice", "Send the defect notice.", ["View warranty"]))
		self.assertEqual([r[0] for r in notice["regions"][0]["b"][0]["items"]], ["Unit", "Accepted", "Source terms", "Fault", "Warranty", "Evidence"])
		issues.send_correspondence(self.case, issue=self.row().name, text="The battery does not charge. Please arrange a replacement.", expected_version=self.t.version(), idempotency_key=self.t.key("n"), actor=self.p["carol"])
		frappe.flags.kt_cm_clock = "2028-07-10 09:30:00"
		arrange = self.screen("carol", "D35", tab="Obligations")
		self.assertEqual((arrange["p"], arrange["next"]["h"]), ("Record return", "Arrange return of the faulty laptop computer."))
		self.assertEqual(arrange["regions"][1]["b"][0]["items"], [["Returned", "No"], ["Replacement", "Not received"], ["Finance correction", "Pending — Josphat Mwangi"]])
		self.assertEqual(arrange["dialogs"]["return"]["p"], "Record return")
		warranty.record_return(self.case, issue=self.row().name, collected_on="2028-07-12", evidence="Test collection WAR-01", expected_version=self.t.version(), idempotency_key=self.t.key("ret"), actor=self.p["carol"])
		new = tw.fresh_serials(1)
		out = delivery.record_arrival(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("ra"), actor=self.p["grace"], received_at="2028-07-14 10:00:00", destination="Afya House store",
			items=[{"line_id": "L1", "quantity": 1, "units": new, "replaces": [self.units[3]]}])
		self.t.inspect(out["arrival"], new)
		frappe.flags.kt_cm_clock = "2028-07-15 09:00:00"
		self.t.accept(out["arrival"])
		blocked = self.screen("peter", "D35-H", tab="Obligations")
		self.assertEqual((blocked["next"]["k"], blocked["next"]["h"], blocked["p"]), ("blk", "Finance must reconcile the replacement.", ""))
		self.assertEqual(blocked["next"]["fixes"], ["View affected records", "View claim"])
		from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_return

		ret = make_purchase_return(delivery.posted_receipts(self.case)[0])
		ret.items[0].qty = ret.items[0].received_qty = -1
		ret.insert(ignore_permissions=True)
		ret.submit()
		warranty.reconcile_return(self.case, issue=self.row().name, return_document=ret.name, expected_version=self.t.version(), idempotency_key=self.t.key("rec"), actor=self.p["josphat"])
		verify = self.screen("peter", "D35-V", tab="Obligations")
		self.assertEqual((verify["p"], verify["s2"], verify["next"]["h"]), ("Verify remedy", ["Request correction"], "Confirm the remedy evidence."))
		self.assertEqual(verify["regions"][0]["b"][0]["items"][2], ["Return/credit and replacement receipt", "Reconciled"])
		warranty.verify_remedy(self.case, issue=self.row().name, expected_version=self.t.version(), idempotency_key=self.t.key("v"), actor=self.p["peter"])
		done = self.screen("carol", "D35-C", tab="Obligations", subject=("issue", "1"))
		self.assertEqual((done["next"]["k"], done["s2"]), ("done", ["View remedy", "View history"]))
		self.assertEqual(done["regions"][0]["b"][0]["items"][1], ["Additional invoice entitlement", "None"])


	def test_a_repair_claim_waits_on_the_supplier_after_the_warranty_has_ended(self):
		self.claim("Repair", self.units[4])
		issues.send_correspondence(self.case, issue=self.row().name, text="Battery does not charge.", expected_version=self.t.version(), idempotency_key=self.t.key("n2"), actor=self.p["carol"])
		frappe.flags.kt_cm_clock = "2028-07-21 09:00:00"
		board = self.screen("carol", "D16-P", tab="Obligations")
		self.assertEqual((board["next"]["k"], board["p"], board["s2"]), ("wait", "", ["View notice", "View claim history"]))
		self.assertIn("Expired", dict(board["regions"][0]["b"][0]["items"])["Warranty"])


class TestAdjustment(OpsBoards):
	def test_a_delay_adjustment_from_the_proposal_to_the_certification_and_the_held_payment(self):
		self.accepted(10, on="2027-07-25 10:00:00")
		hop = self.screen("charles", "D36", tab="Obligations")
		self.assertEqual((hop["title"], hop["p"], hop["next"]["h"]), ("Review delivery delay", "Submit adjustment for decision", "Review the proposed adjustment."))
		calc = hop["regions"][0]["b"]
		self.assertEqual([r[0] for r in calc[0]["items"]], ["Due date", "Delivered", "Days late", "Eligible principal", "Rate", "Cap", "Effective extension"])
		self.assertEqual(calc[0]["items"][2], ["Days late", "5 calendar days (21–25 Jul inclusive)"])
		self.assertEqual(calc[1]["items"], [["Calculation", "KES 1,000 per day × 5"], ["Proposed adjustment", "KES 5,000"]])
		self.assertEqual(hop["dialogs"]["submit"]["p"], "Submit")
		adjustment.prepare(self.case, causation="Supplier shipment delay", clause="TEST-DELAY-01", supplier_response="Requests exclusion of two days", recommendation="No supported exclusion", expected_version=self.t.version(),
			idempotency_key=self.t.key("p"), actor=self.p["charles"])
		ao = self.screen("amina", "D36-A", tab="Obligations")
		self.assertEqual((ao["p"], ao["s2"], ao["next"]["h"]), ("Approve adjustment", ["Decline", "Return for correction"], "Decide the proposed delay adjustment."))
		self.assertEqual(ao["regions"][2]["b"][0]["items"], [["Technical/legal recommendation", "No supported exclusion"]])
		adjustment.decide(self.case, adjustment=adjustment.get(self.case, 1).name, decision="Approve", reason="Supplier-responsible five-day delay established.", expected_version=self.t.version(), idempotency_key=self.t.key("d"), actor=self.p["amina"])
		invoice = self.t.claim("INV-ADJ-1", 10)["invoice"]
		cert = self.screen("charles", "D36-S", tab="Invoices")
		self.assertEqual((cert["p"], cert["next"]["h"], cert["regions"][0]["b"][0]["rows"][0]), ("Sign certification", "Review the invoice and sign the certification.", ["KES 1,000,000", "KES 5,000", "KES 995,000"]))
		self.t.certify_invoice(invoice)
		self.t.post_accounting(invoice)  # the liability is Finance's own step; it is the payment that waits for the unverified mapping
		held = self.screen("josphat", "D36-H")
		self.assertEqual((held["next"]["k"], held["next"]["h"], held["p"]), ("blk", "This action is on hold.", ""))
		self.assertEqual(held["next"]["fixes"], ["View calculation", "View issue"])

	def test_an_extension_that_took_effect_shows_the_retained_earlier_computation(self):
		self.accepted(10, on="2027-07-25 10:00:00")
		adjustment.prepare(self.case, causation="Supplier shipment delay", clause="TEST-DELAY-01", supplier_response="", recommendation="", expected_version=self.t.version(), idempotency_key=self.t.key("p"), actor=self.p["charles"])
		adjustment.decide(self.case, adjustment=adjustment.get(self.case, 1).name, decision="Return", reason="Re-read the extension.", expected_version=self.t.version(), idempotency_key=self.t.key("d"), actor=self.p["amina"])
		self.t.change_through("Extension", {"proposed_date": "2027-07-22"})
		board = self.screen("charles", "D36-E", tab="Obligations")
		calc = board["regions"][0]["b"]
		self.assertEqual((calc[0]["items"][0], calc[0]["items"][2]), (["Due date", "22 Jul 2027 (effective extension)"], ["Days late", "3 calendar days (23–25 Jul inclusive)"]))
		self.assertEqual(calc[1]["items"][1], ["Proposed adjustment", "KES 3,000"])


class TestSecurity(OpsBoards):
	security = True

	def setUp(self):
		super().setUp()
		frappe.flags.kt_cm_clock = "2027-08-12 09:00:00"

	def claim(self):
		return security_actions.request_claim(self.case, grounds="Failure to perform the unfulfilled obligation", amount=40_000, recipient="Test Bank", mandate="Reviewed test mandate 1", evidence=EVIDENCE,
			expected_version=self.t.version(), idempotency_key=self.t.key("c"), actor=self.p["charles"])

	def test_a_security_claim_from_the_request_to_the_issuers_outcome(self):
		prepare = self.screen("charles", "D37", tab="Obligations", subject=("request-security-claim",))
		self.assertEqual((prepare["p"], prepare["s2"], prepare["next"]["h"]), ("Request claim", ["View instrument", "Cancel"], "Prepare the supported claim."))
		self.claim()
		ao = self.screen("amina", "D37-A")
		self.assertEqual((ao["p"], ao["s2"], ao["next"]["h"]), ("Approve claim", ["Decline", "Return for correction"], "Decide the security claim."))
		self.assertEqual(ao["regions"][1]["b"][0]["items"][0], ["Amount", "KES 40,000"])
		security_actions.decide_claim(self.case, claim=1, decision="Approve", reason="The exact claim is supported.", expected_version=self.t.version(), idempotency_key=self.t.key("d"), actor=self.p["amina"])
		self.assertEqual(self.screen("charles", "D37-C", capture=False)["p"], "Record delivery")
		security_actions.record_communication(self.case, claim=1, sent_on="2027-08-12", channel="Courier", reference="CR-1", evidence=[{"label": "Proof", "file": "/private/files/p.pdf"}], expected_version=self.t.version(),
			idempotency_key=self.t.key("m"), actor=self.p["charles"])
		waiting = self.screen("charles", "D37-P", tab="Obligations")
		self.assertEqual((waiting["next"]["k"], waiting["p"], waiting["s2"]), ("wait", "", ["Record claim outcome"]))
		self.assertEqual(waiting["dialogs"]["outcome"]["p"], "Save outcome")
		self.assertEqual(waiting["regions"][1]["b"][0]["items"][2], ["Outcome", "Not recorded"])

	def test_a_replacement_instrument_is_verified_while_the_old_one_stays_operative(self):
		new = self.t.record_security(reference="TEST-SG-02", issued_on="2027-08-15", expires_on="2027-09-30", verify=False)
		board = self.screen("charles", "D37-X", tab="Obligations")
		self.assertEqual((board["p"], board["s2"], board["next"]["h"]), ("Verify replacement", ["Reject replacement"], "Check the issuer's confirmation."))
		table = board["regions"][0]["b"][0]
		self.assertEqual([[r[0], r[3]] for r in table["rows"]], [["TEST-SG-01", "!Operative"], ["TEST-SG-02", "!Not verified"]])
		security.verify_security(self.case, security=new, expected_version=self.t.version(), idempotency_key=self.t.key("v"), actor=self.p["charles"], confirmation_reference="TEST-SG-CONF-02", received_on="2027-08-15")
		self.assertEqual(self.screen("charles", "D37-R", capture=False)["p"], "Record replacement")

	def test_the_return_is_due_after_the_final_acceptance(self):
		records.new("Contract Certificate", contract_case=self.case, kind="Final acceptance", subject="final acceptance", subject_version=1, state="Signed", signer=self.p["amina"], proof_reference="TEST",
			signed_at="2027-07-27 10:00:00", content_json="{}", record_version=1)
		security_actions.on_final_acceptance(self.case)
		frappe.flags.kt_cm_clock = "2027-08-01 09:30:00"
		board = self.screen("charles", "D16", tab="Obligations")
		self.assertEqual((board["title"], board["p"], board["next"]["h"], board["s2"]), ("Performance security", "Record return", "Record the security return.", ["View guarantee"]))
		self.assertEqual(board["regions"][0]["b"][0]["items"][2:], [["AO final acceptance", "27 July 2027"], ["Return due", "26 August 2027 — 30 days from AO final acceptance"], ["Status", "Return due"]])


class TestTermination(OpsBoards):
	def setUp(self):
		super().setUp()
		self.accepted(8, on="2027-07-25 10:00:00")
		self.paid = self.t.claim("INV-T-1", 6)["invoice"]
		self.t.certify_invoice(self.paid)
		self.t.pay(self.paid, "TERM-BANK-1")
		self.unpaid = self.t.claim("INV-T-2", 2)["invoice"]
		self.t.certify_invoice(self.unpaid)

	def ask(self):
		return termination.request(self.case, grounds="Material non-delivery", clause="Contract clause 8", recommendation="Terminate unperformed balance", evidence=EVIDENCE + [{"label": "Legal advice 1", "file": "/private/files/l.pdf"}],
			expected_version=self.t.version(), idempotency_key=self.t.key("ask"), actor=self.p["charles"])

	def test_a_termination_from_the_decision_to_the_completed_settlement(self):
		request = self.screen("charles", "D20-N", capture=False, tab="Obligations", subject=("request-termination",))
		self.assertEqual(request["p"], "Request termination")
		self.ask()
		ao = self.screen("amina", "D20")
		self.assertEqual((ao["title"], ao["p"], ao["s2"], ao["next"]["h"]), ("Review contract termination", "Approve termination", ["Decline", "Return for correction"], "Decide the termination request."))
		self.assertEqual(ao["regions"][1]["b"][0]["items"], [["Accepted value", "KES 800,000"], ["Cash paid", "KES 600,000"], ["Supported unpaid", "KES 200,000"], ["Advance balance", "KES 0"], ["Disputed claim", "KES 0"]])
		termination.decide(self.case, termination=1, decision="Approve", reason="The grounds are established.", expected_version=self.t.version(), idempotency_key=self.t.key("dec"), actor=self.p["amina"])
		self.assertEqual(self.screen("charles", "D20-R", capture=False)["p"], "Record delivery")
		waiting = self.screen("amina", "D20-P", tab="Obligations")
		self.assertEqual((waiting["next"]["k"], waiting["p"], waiting["s2"]), ("wait", "", ["View notice", "View delivery status"]))
		termination.record_notice(self.case, termination=1, delivered_on="2027-07-02", method="Registered post", reference="RP-1", effective_on="2027-07-02", evidence=[{"label": "Proof", "file": "/private/files/p.pdf"}],
			expected_version=self.t.version(), idempotency_key=self.t.key("not"), actor=self.p["charles"])
		effective = self.screen("amina", "D20-T", tab="Obligations")
		self.assertEqual((effective["st"], effective["next"]["k"], effective["p"], effective["s2"]), ("Terminated", "wait", "", ["View termination record", "View settlement"]))
		self.t.pay(self.unpaid, "TERM-BANK-2")
		prepare = self.screen("charles", "D39-P", tab="Obligations")
		self.assertEqual((prepare["p"], prepare["s2"], prepare["next"]["h"]), ("Submit settlement for completion", ["Return for correction", "View reconciliation"], "Review the reconciled settlement."))
		self.assertEqual(prepare["regions"][0]["b"][0]["items"][5], ["Budget decrease", "Acknowledged"])
		termination.prepare_settlement(self.case, termination=1, finance_reference="TERM-01", expected_version=self.t.version(), idempotency_key=self.t.key("prep"), actor=self.p["charles"])
		complete = self.screen("amina", "D39", tab="Obligations")
		self.assertEqual((complete["p"], complete["s2"], complete["dialogs"]["complete"]["p"]), ("Complete settlement", ["Return for correction", "View termination"], "Confirm completion"))
		termination.complete_settlement(self.case, termination=1, reason="All required settlement facts reconciled.", expected_version=self.t.version(), idempotency_key=self.t.key("done"), actor=self.p["amina"])
		done = self.screen("charles", "D39-C", tab="Obligations")
		self.assertEqual((done["st"], done["next"]["k"], done["s2"]), ("Terminated", "done", ["View settlement", "View funding update"]))

	def test_an_advance_that_is_not_recovered_blocks_the_settlement(self):
		self.ask()
		termination.decide(self.case, termination=1, decision="Approve", reason="Established.", expected_version=self.t.version(), idempotency_key=self.t.key("dec"), actor=self.p["amina"])
		termination.record_notice(self.case, termination=1, delivered_on="2027-07-02", method="Post", reference="RP-1", effective_on="2027-07-02", evidence=[{"label": "Proof", "file": "/private/files/p.pdf"}],
			expected_version=self.t.version(), idempotency_key=self.t.key("not"), actor=self.p["charles"])
		self.t.pay(self.unpaid, "TERM-BANK-2")
		from unittest import mock

		from kentender_contracts.services import advance

		with mock.patch.object(advance, "position", return_value={"advance": "A", "certified": 20000.0, "paid": 20000.0, "recovered": 0.0, "outstanding": 20000.0}):
			board = self.screen("charles", "D39-H", tab="Obligations")
		self.assertEqual((board["next"]["k"], board["next"]["h"], board["p"]), ("blk", "The advance recovery needs resolution.", ""))
		self.assertEqual(board["regions"][0]["b"][0]["items"][1], ["Outstanding advance", "KES 20,000"])


class TestReports(OpsBoards):
	def test_the_monthly_report_and_the_publication_requirement(self):
		publication = self.screen("charles", "D15-L", tab="Obligations", subject=("publication",))
		self.assertEqual((publication["st"], publication["next"]["k"], publication["next"]["h"]), ("Needs review", "blk", "The applicable publication deadline needs confirmation."))
		self.assertEqual(publication["next"]["fixes"], ["Record source evidence", "View source event", "View signing record"])
		items = publication["regions"][0]["b"][0]["items"]
		self.assertEqual(items[0], ["Trigger", "Award decision recorded 17 Jun 2027, 10:00 EAT"])
		self.assertEqual(items[3], ["Deadline", "Not confirmed — set by current directions"])
		self.assertEqual(publication["dialogs"]["evidence"]["p"], "Save evidence")
		self.accepted(10, on="2027-07-19 10:00:00")
		invoice = self.t.claim("INV-R-1", 8)["invoice"]
		self.t.certify_invoice(invoice)
		self.t.pay(invoice, "RPT-BANK-1")
		frappe.flags.kt_cm_clock = "2027-08-01 09:00:00"
		reporting.generate("Progress", period_start="2027-07-01", idempotency_key=self.t.key("g"), actor=self.p["charles"])
		report = self.screen("charles", "D15", tab="Obligations", subject=("report", frappe.db.get_value("Contract Report", {"report_type": "Progress", "contract_case": ["is", "not set"]}, "name", order_by="creation desc")))
		self.assertEqual((report["title"], report["p"], report["s2"][0]), ("Monthly contract progress", "Submit report", "View contract"))
		table = report["regions"][1]["b"][0]
		self.assertEqual(table["cols"], ["Contract", "Title", "Contract value", "Commenced", "Status", "Cash confirmed", "Expected completion"])
		self.assertEqual(report["regions"][1]["b"][1]["v"], "10 laptop computers accepted. Unpaid KES 200,000; no noncash adjustment. No open delivery issue.")
