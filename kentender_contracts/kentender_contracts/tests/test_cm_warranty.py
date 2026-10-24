# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.18, 5.20, 7 and boards D16-W, D16-P, D35, D35-V, D35-C, D35-H (plan Phase 8; tracker CM8-804): warranty claims on accepted goods.

A unit accepted and paid for is history: its warranty claim returns it, Finance reconciles the native return and credit, the replacement is accepted by the ordinary route and the technical capacity verifies
the remedy, which closes the claim in the same act. The replacement fulfils the existing obligation: no second payable, no invoice entitlement, no universal new warranty. While the returned unit's credit
is not reconciled, new certification and payment wait."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D, after_months  # noqa: F401
import frappe

from kentender_contracts.services import change, delivery, errors, holds, issues, position, records, warranty, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


ACCEPTED_ON = D("2027-07-20 10:00:00")
NOTICE_ON = D("2028-07-10 09:00:00")


class WarrantyCase(ContractCase):
	native = True

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
		self.addCleanup(lambda: (setattr(frappe.flags, "kt_cm_dispatch_fault", None), self.env.__exit__(None, None, None)))
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24], item=world.ITEM_PLAIN)
		self.case = self.t.active()
		self.t.appointed()
		frappe.db.set_value("Contract Case", self.case, "responsible_user", self.p["julia"])
		self.units = tw.fresh_serials(10)
		arrival = self.t.arrive(self.units, received_at=D("2027-07-12 10:00:00"))["arrival"]
		self.t.inspect(arrival, self.units)
		frappe.flags.kt_cm_clock = ACCEPTED_ON
		self.t.accept(arrival)
		frappe.flags.kt_cm_clock = NOTICE_ON

	def claim(self, unit=None, remedy="Like-for-like replacement", notice=D("2028-07-10"), fault="Battery does not charge", who="julia"):
		return warranty.record_claim(self.case, unit=unit or self.units[3], fault=fault, notice_date=notice, remedy=remedy, expected_version=self.t.version(), idempotency_key=self.t.key("claim"), actor=self.p[who])

	def row(self, number=1):
		return issues.get(self.case, number)

	def notice(self, number=1):
		return issues.send_correspondence(self.case, issue=self.row(number).name, text="The battery does not charge. Please arrange a replacement.", expected_version=self.t.version(), idempotency_key=self.t.key("notice"), actor=self.p["julia"])

	def collected(self, number=1):
		return warranty.record_return(self.case, issue=self.row(number).name, collected_on=D("2028-07-12"), evidence="Collection note WAR-01", expected_version=self.t.version(), idempotency_key=self.t.key("ret"), actor=self.p["julia"])

	def native_return(self):
		"""Finance's native return of one unit against the contract's receipt."""
		from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_return

		receipt = delivery.posted_receipts(self.case)[0]
		ret = make_purchase_return(receipt)
		ret.items[0].qty = ret.items[0].received_qty = -1
		ret.insert(ignore_permissions=True)
		ret.submit()
		return ret.name

	def reconcile(self, number=1, **kw):
		kw.setdefault("return_document", self.native_return())
		return warranty.reconcile_return(self.case, issue=self.row(number).name, expected_version=self.t.version(), idempotency_key=self.t.key("rec"), actor=self.p["josphat"], **kw)

	def replacement(self, old=None):
		new = tw.fresh_serials(1)
		out = delivery.record_arrival(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("rarrive"), actor=self.p["grace"], received_at=D("2028-07-14 10:00:00"), destination="Afya House store",
			items=[{"line_id": "L1", "quantity": 1, "units": new, "replaces": [old or self.units[3]]}])
		self.t.inspect(out["arrival"], new)
		frappe.flags.kt_cm_clock = D("2028-07-15 09:00:00")
		self.t.accept(out["arrival"])
		return new[0]

	def verify(self, number=1, who="peter", **kw):
		return warranty.verify_remedy(self.case, issue=self.row(number).name, expected_version=self.t.version(), idempotency_key=self.t.key("verify"), actor=self.p[who], **kw)

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}


class TestClaim(WarrantyCase):
	def test_a_blank_notice_date_is_refused_and_not_read_as_today(self):
		for blank in ("", "  "):
			exc = refusal(self.claim, notice=blank)
			self.assertIn("notice_date", exc.detail["fields"], repr(blank))
		self.assertEqual(frappe.db.count("Contract Issue", {"contract_case": self.case}), 0)

	def test_a_claim_records_the_unit_the_fault_and_the_end_of_its_warranty_and_asks_for_the_defect_notice(self):
		out = self.claim()
		row = self.row()
		found = warranty.facts(row)
		self.assertEqual((row.kind, row.state, row.requested_remedy, out["issue_no"]), ("Warranty claim", "Open", "Like-for-like replacement", 1))
		self.assertEqual((found["unit"], found["fault"], found["notice_date"], found["warranty_ends"]), (self.units[3], "Battery does not charge", D("2028-07-10"), after_months("2027-07-20", 12)))
		self.assertEqual(warranty.stage(row), "notice")
		self.assertIn(("SendContractCorrespondence", "Send the defect notice.", "actionable"), self.tasks("julia"))

	def test_only_an_accepted_unit_inside_its_warranty_and_not_already_claimed_can_be_claimed(self):
		self.assertIn("unit", refusal(self.claim, unit="NO-SUCH-UNIT").fields)
		self.assertIn("notice_date", refusal(self.claim, notice=D("2028-07-21")).fields)  # the day after the warranty ended
		self.assertIn("fault", refusal(self.claim, fault=" ").fields)
		self.assertIn("remedy", refusal(self.claim, remedy="Refund").fields)
		self.claim()
		self.assertEqual(refusal(self.claim).code, "CM_CHANGED")
		self.claim(unit=self.units[4])  # another unit is its own claim
		self.assertEqual(frappe.db.count("Contract Issue", {"contract_case": self.case, "kind": "Warranty claim"}), 2)

	def test_the_owner_or_a_preparer_records_it_and_a_stranger_does_not(self):
		self.assertEqual(refusal(self.claim, who="stranger").code, "CM_AUTHORITY")

	def test_a_warranty_claim_is_closed_by_its_verified_remedy_not_by_a_note(self):
		self.claim()
		self.assertEqual(refusal(issues.resolve_issue, self.case, issue=self.row().name, disposition="Done", expected_version=self.t.version(), idempotency_key=self.t.key("res"), actor=self.p["julia"]).code, "CM_RECONCILE")


class TestReplacement(WarrantyCase):
	def setUp(self):
		super().setUp()
		self.claim()
		self.notice()

	def test_the_delivered_notice_asks_the_owner_to_arrange_the_return(self):
		self.assertEqual(warranty.stage(self.row()), "return")
		self.assertIn(("RecordWarrantyReturn", "Arrange return of the faulty laptop computer.", "actionable"), self.tasks("julia"))
		self.assertEqual(refusal(self.verify).code, "CM_CHANGED")  # not ready to be verified yet

	def test_the_return_removes_the_unit_from_the_accepted_ones_asks_finance_and_holds_new_certification_and_payment(self):
		self.assertIn("evidence", refusal(warranty.record_return, self.case, issue=self.row().name, collected_on=D("2028-07-12"), evidence=" ", expected_version=self.t.version(), idempotency_key=self.t.key("r0"), actor=self.p["julia"]).fields)
		self.collected()
		now = position.position(self.case)
		self.assertEqual((now["units"][self.units[3]]["status"], now["lines"]["L1"]["accepted"], now["lines"]["L1"]["remaining"], now["lines"]["L1"]["ordered"]), ("Returned", 9, 1, 10))
		self.assertEqual(warranty.stage(self.row()), "reconcile")
		self.assertIn(("ReconcileWarrantyReturn", "Reconcile the return and credit for the faulty laptop computer.", "actionable"), self.tasks("josphat"))
		held = [h for h in holds.open_holds(self.case) if h.key.startswith("warranty return:")]
		self.assertEqual((len(held), held[0].reason, held[0].owner), (1, "Finance must reconcile the replacement.", self.p["josphat"]))
		self.assertTrue(holds.blocking(self.case, "certify_invoice") and holds.blocking(self.case, "pay") and holds.blocking(self.case, "close_claim"))
		self.assertFalse(holds.blocking(self.case, "new_spending"))  # independent work is not held
		self.assertEqual(refusal(self.collected).code, "CM_CHANGED")  # recorded once

	def test_finance_names_the_native_return_and_a_document_that_is_not_one_is_refused(self):
		self.collected()
		self.assertEqual(refusal(warranty.reconcile_return, self.case, issue=self.row().name, expected_version=self.t.version(), idempotency_key=self.t.key("x"), actor=self.p["stranger"]).code, "CM_AUTHORITY")
		self.assertIn("return_document", refusal(warranty.reconcile_return, self.case, issue=self.row().name, expected_version=self.t.version(), idempotency_key=self.t.key("x1"), actor=self.p["josphat"]).fields)
		self.assertIn("return_document", refusal(warranty.reconcile_return, self.case, issue=self.row().name, return_document=delivery.posted_receipts(self.case)[0], expected_version=self.t.version(),
			idempotency_key=self.t.key("x2"), actor=self.p["josphat"]).fields)  # the receipt itself, not a return of it
		self.assertIn("credit_document", refusal(warranty.reconcile_return, self.case, issue=self.row().name, credit_document="ACC-PINV-NONE", expected_version=self.t.version(), idempotency_key=self.t.key("x3"), actor=self.p["josphat"]).fields)
		self.reconcile()
		self.assertEqual(warranty.stage(self.row()), "replacement")
		self.assertFalse([h for h in holds.open_holds(self.case) if h.key.startswith("warranty return:")])
		self.assertTrue(records.loads(self.row().links_json)["reconciliation"]["return_document"])

	def test_a_replacement_accepted_after_the_reconciliation_is_ready_to_verify_and_closes_the_claim_in_one_act(self):
		self.collected()
		self.reconcile()
		new = self.replacement()
		self.assertEqual(warranty.stage(self.row()), "verify")
		self.assertEqual(warranty.replacement_of(self.case, self.units[3]), new)
		self.assertIn(("VerifyContractRemedy", "Confirm the remedy evidence.", "actionable"), self.tasks("peter"))
		self.assertEqual(refusal(self.verify, who="faith").code, "CM_AUTHORITY")  # not the appointed technical capacity
		out = self.verify()
		row = self.row()
		self.assertEqual((out["state"], row.state, warranty.stage(row)), ("Closed", "Closed", "closed"))
		self.assertIn(f"replacement unit {new} accepted for unit {self.units[3]}", row.resolution)
		self.assertIn("no additional payment", row.resolution)
		self.assertFalse({t for t in self.tasks("peter") if t[0] == "VerifyContractRemedy"})
		now = position.position(self.case)
		self.assertEqual((now["lines"]["L1"]["accepted"], now["lines"]["L1"]["ordered"], now["lines"]["L1"]["remaining"]), (10, 10, 0))  # the existing obligation is fulfilled, nothing is added

	def test_the_reconciliation_made_after_the_replacement_was_accepted_asks_for_the_verification_then(self):
		self.collected()
		self.replacement()
		self.assertEqual(warranty.stage(self.row()), "reconcile")  # the replacement is in, Finance has not reconciled the return
		out = refusal(self.verify)
		self.assertEqual((out.code, out.detail["holder"]), ("CM_RECONCILE", self.p["josphat"]))
		self.assertEqual(out.detail["missing"][0]["what"], "Finance has not reconciled the return and credit of the faulty unit.")
		self.reconcile()
		self.assertEqual(warranty.stage(self.row()), "verify")
		self.verify()
		self.assertEqual(self.row().state, "Closed")

	def test_a_remedy_with_missing_evidence_names_what_is_missing_and_who_holds_it(self):
		self.collected()
		self.reconcile()
		out = refusal(self.verify)  # reconciled, but no replacement has been accepted yet
		self.assertEqual((out.code, out.detail["holder"]), ("CM_RECONCILE", self.p["julia"]))
		self.assertIn("No replacement for unit", out.detail["missing"][0]["what"])
		self.assertNotEqual(self.row().state, "Closed")  # the claim stays open with the specific missing evidence

	def test_a_paid_unit_returned_adds_no_second_payable_and_no_entitlement(self):
		invoice = self.t.claim("INV-WAR-1", 10)["invoice"]
		self.t.certify_invoice(invoice)
		self.t.pay(invoice, "WAR-BANK-1")
		self.assertEqual(frappe.db.get_value("Contract Invoice", invoice, "state"), "Paid")
		self.collected()
		self.reconcile()
		self.replacement()
		self.verify()
		self.assertEqual(frappe.db.get_value("Contract Invoice", invoice, "state"), "Paid")  # the payment stays a historical cash fact
		extra = self.t.claim("INV-WAR-2", 1)["invoice"]
		self.assertEqual(frappe.db.get_value("Contract Invoice", extra, "state"), "Held")  # all ten are accepted and claimed: a like-for-like replacement earns no second payable


class TestRepair(WarrantyCase):
	def test_a_repair_goes_straight_to_verification_with_the_measured_evidence_and_no_documents(self):
		self.claim(remedy="Repair")
		self.notice()
		self.assertEqual(warranty.stage(self.row()), "verify")
		self.assertIn(("VerifyContractRemedy", "Confirm the repair evidence.", "actionable"), self.tasks("peter"))
		self.assertIn("evidence", refusal(self.verify).fields)
		self.verify(evidence="Battery replaced; charges to 100% in the log WAR-LOG-1")
		self.assertEqual(self.row().state, "Closed")
		self.assertIn("repaired", self.row().resolution)
		self.assertEqual(position.position(self.case)["lines"]["L1"]["accepted"], 10)  # no receipt or return was invented for a repair
