# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 14 and plan Phase 12 (tracker CM8-1202): the whole-chain scenarios, each from its start to its end through the services the screens call, with real ERPNext documents.

The plan names eight. Six are walked end to end by the modules that own them (the table is in the tracker): normal goods (`test_cm_completion`), mixed acceptance and replacement (`test_cm_thread`), multiple deliveries,
invoices and instalments (`test_cm_settlement`, `test_cm_thread`), a quantity variation (`test_cm_change`), a disputed delay (`test_cm_adjustment`) and a paid-unit warranty (`test_cm_warranty`). The two that no
other module walks all the way are here: a termination while an advance is outstanding, and a contract that arrives with activity already behind it and is carried to its close."""

from __future__ import annotations

import frappe
from frappe.utils import flt

from kentender_contracts.services import advance, closeout, errors, existing, formation, position, records, termination, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

EVIDENCE = [{"label": "Default notice and delivery proof", "file": "/private/files/default-notice.pdf"}]


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class WholeChain(ContractCase):
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
		self.addCleanup(lambda: self.env.__exit__(None, None, None))
		self.p = self.people

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}


class TestTerminationWithAnAdvance(WholeChain):
	"""An advance of KES 100,000 is paid; eight laptops are accepted and invoiced with KES 10,000 recovered on each; the Accounting Officer terminates. The advance that was not recovered is a debt of the supplier,
	and a settlement cannot be completed while it is neither settled nor classified with the term that lets it survive."""

	def setUp(self):
		super().setUp()
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24], advance=True)
		self.case = self.t.case = self.t.active()
		self.t.appointed()
		row = advance.prepare_advance(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("adv"), actor=self.p["david"], claim_reference="WC-ADV-1", amount=100_000)["advance"]
		sec = advance.record_guarantee(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("g"), actor=self.p["josphat"], issuer="Test Bank", beneficiary="Ministry of Health", reference="WC-AG-01",
			amount=100_000, issued_on="2027-06-01", expires_on="2027-08-31")["security"]
		advance.verify_guarantee(self.case, security=sec, expected_version=self.t.version(), idempotency_key=self.t.key("v"), actor=self.p["charles"], confirmation_reference="WC-AG-CONF", received_on="2027-07-02")
		advance.sign_advance_certification(self.case, advance=row, expected_version=self.t.version(), idempotency_key=self.t.key("cert"), actor=self.p["charles"])
		from kentender_contracts.services import payment

		entry = payment.save_advance_payment(self.case, advance=row, expected_version=self.t.version(), idempotency_key=self.t.key("pay"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT,
			reference_no="WC-ADV-BANK")["payment"]
		payment.submit_finance_for_approval(self.case, payment=entry, expected_version=self.t.version(), idempotency_key=self.t.key("sub"), actor=self.p["josphat"])
		payment.approve_finance_record(self.case, payment=entry, expected_version=self.t.version(), idempotency_key=self.t.key("app"), actor=self.p["beatrice"])
		payment.record_finance_settlement(self.case, payment=entry, expected_version=self.t.version(), idempotency_key=self.t.key("settle"), actor=self.p["beatrice"], effective_date="2027-07-05", evidence="Bank line WC-ADV")
		units = tw.fresh_serials(8)
		arrival = self.t.arrive(units)["arrival"]
		self.t.inspect(arrival, units)
		self.t.accept(arrival)
		self.invoice = self.t.claim("WC-INV-1", 8)["invoice"]
		self.t.certify_invoice(self.invoice)
		self.t.pay(self.invoice, "WC-BANK-1")

	def terminate(self):
		termination.request(self.case, grounds="Material non-delivery", clause="Contract clause 8", recommendation="Terminate the unperformed balance", evidence=EVIDENCE, expected_version=self.t.version(),
			idempotency_key=self.t.key("ask"), actor=self.p["charles"])
		termination.decide(self.case, termination=1, decision="Approve", reason="The grounds are established.", expected_version=self.t.version(), idempotency_key=self.t.key("dec"), actor=self.p["amina"])
		return termination.record_notice(self.case, termination=1, delivered_on="2027-07-02", method="Registered post", reference="RP-0042", effective_on="2027-07-02", evidence=[{"label": "Proof of delivery", "file": "/private/files/pod.pdf"}],
			expected_version=self.t.version(), idempotency_key=self.t.key("notice"), actor=self.p["charles"])

	def test_the_advance_still_owed_is_in_the_position_the_settlement_and_the_close_of_the_contract(self):
		position_ = advance.position(self.case)
		self.assertEqual((position_["paid"], position_["recovered"], position_["outstanding"]), (100_000, 80_000, 20_000), "ten thousand was recovered on each of the eight laptops invoiced")
		self.terminate()
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Terminated")
		found = records.loads(termination.get(self.case, 1).financial_json)
		self.assertEqual((found["accepted_value"], found["advance_balance"]), (800_000, 20_000), "the financial position of the request was generated from the records, advance included")
		recon = termination.reconciliation(self.case, termination.get(self.case, 1))
		self.assertEqual(recon["advance_balance"], 20_000)
		self.assertEqual([(r["kind"], r["ref"]) for r in recon["remaining"]], [("Advance recovery", "advance")], "the advance owed is the one thing left between the termination and its settlement")
		# nothing is settled by saying so: with the advance neither settled nor named as surviving, the settlement can be prepared but not completed
		prepared = termination.prepare_settlement(self.case, termination=1, finance_reference="WC-TERM-01", classified=[], expected_version=self.t.version(), idempotency_key=self.t.key("prep0"), actor=self.p["charles"])
		self.assertEqual(prepared["remaining"], 1)
		stopped = refusal(termination.complete_settlement, self.case, termination=1, reason="Every settlement fact is reconciled or classified.", expected_version=self.t.version(), idempotency_key=self.t.key("done0"), actor=self.p["amina"])
		self.assertEqual((stopped.code, stopped.detail["remaining"][0]["kind"]), ("CM_CLOSURE", "Advance recovery"))
		termination.prepare_settlement(self.case, termination=1, finance_reference="WC-TERM-01", classified=[{"kind": "Advance recovery", "ref": "advance", "basis": "Advance guarantee WC-AG-01 stands until the advance is recovered"}],
			expected_version=self.t.version(), idempotency_key=self.t.key("prep"), actor=self.p["charles"])
		termination.complete_settlement(self.case, termination=1, reason="Every settlement fact is reconciled or classified.", expected_version=self.t.version(), idempotency_key=self.t.key("done"), actor=self.p["amina"])
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Terminated", "the settlement is its own fact: the contract is never shown as completed")
		self.assertEqual(advance.position(self.case)["outstanding"], 20_000, "completing a settlement erases no debt")


class TestImportedActivityIsCarriedToTheClose(WholeChain):
	"""A contract signed before KenTender with four of ten laptops accepted and invoiced, two in custody and four to come: registered, confirmed by Finance, started, and then carried to its end without being asked to
	sign again or to invoice what was invoiced before."""

	def setUp(self):
		super().setUp()
		self.n = 0
		receipt = world.fixed_asset_receipt("WCEXT", 4)
		from kentender_contracts.native import adapter

		invoice = adapter.invoice_receipt(receipt, world.identity("invoice wcext", "Native invoice"), bill_no="WC-EXT-INV", qty=4)
		frappe.db.commit()
		values = {"source": "External records", "reference": "MOH/ICT/2027/WC-EXT", "supplier_country": tw.REGISTRATION[0], "supplier_registration": tw.REGISTRATION[1], "agreement_file": tw.evidence_file(self.p["brian"], "wc-agreement"),
			"amendments": "None", "signed_on": "2027-07-02", "effective_on": "2027-07-02", "cutover": "2027-08-03 00:00:00", "original_value": 1_000_000, "current_value": 1_000_000,
			"items": "Laptop computer | 10 | Each | 100000 | Included | 4 | 2 | 4", "delivery_due": "2027-07-20", "payment_days": 30, "warranty_months": 12,
			"acceptance": "RAM | >= | 16 | GB\nStorage | >= | 512 | GB\nStarts successfully | = | Yes | ", "security_required": "No", "advance_allowed": "No", "restrictions": "None", "clauses": "Agreement WC-EXT §§2-8",
			"owner": self.p["julia"], "managing_unit": tw.unit(), "entity_signatory": self.p["amina"], "native_supplier": world.SUPPLIER, "asset_location": world.LOCATION, "item_mapping": {"L1": world.ITEM_FA},
			"prior_activity": "Some", "opening_invoiced": 400_000, "opening_credits": 0, "opening_cash_paid": 0, "opening_outstanding": 400_000, "opening_advance": 0, "units_in_custody": "WC-EXT-009\nWC-EXT-010",
			"link_purchase_receipt": receipt, "link_purchase_invoice": invoice}
		self.case = existing.register_existing_contract(idempotency_key=self.key(), actor=self.p["brian"], values=values)["open"]
		existing.confirm_opening_position(self.case, expected_version=self.version(), idempotency_key=self.key(), actor=self.p["beatrice"])
		existing.start_management(self.case, expected_version=self.version(), idempotency_key=self.key(), actor=self.p["charles"])
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24])
		self.t.case = self.case

	def key(self):
		self.n += 1
		return f"wc-{self.id().rsplit('.', 1)[-1][:20]}-{self.n}"

	def version(self):
		return frappe.db.get_value("Contract Case", self.case, "record_version")

	def test_the_contract_is_finished_from_the_opening_position_with_nothing_signed_or_invoiced_twice(self):
		self.assertEqual(frappe.db.count("Contract Signature", {"contract_case": self.case}), 0, "nobody was asked to sign")
		self.t.appointed()
		opening = frappe.get_doc("Contract Arrival", {"contract_case": self.case})
		self.assertEqual(opening.delivery_reference, "Opening position")
		self.t.inspect(opening.name, ["WC-EXT-009", "WC-EXT-010"])
		self.t.accept(opening.name)
		units = tw.fresh_serials(4)
		arrival = self.t.arrive(units, received_at="2027-07-16 10:00:00")["arrival"]
		self.t.inspect(arrival, units)
		self.t.accept(arrival)
		now = position.position(self.case)["lines"]["L1"]
		self.assertEqual((now["ordered"], now["accepted"], now["remaining"], now["in_custody"]), (10, 10, 0, 0))
		# only what was not invoiced before can be claimed: the four accepted at the opening were invoiced already, so a claim for all ten is matched against six and is sent for review, never paid on trust
		from kentender_contracts.services import payment

		match = payment.match_claim(self.case, payment._claim_lines([{"line_id": "L1", "quantity": 10}]))
		self.assertEqual(match["outcome"], "Needs review")
		self.assertIn("only 6 accepted and unclaimed", " ".join(f["reason"] for f in match["findings"]), "ten is more than the six not yet invoiced")
		# the six left are on two receipts (the two held in custody at the opening, the four that arrived since), and a claim is matched against one receipt, so they are claimed as two invoices; the smaller claim takes the smaller receipt, so the larger still fits
		first, second = self.t.claim("WC-CLAIM-1", 2), self.t.claim("WC-CLAIM-2", 4)
		self.assertEqual((first["state"], second["state"]), ("Submitted", "Submitted"))
		for claim, bank in ((first, "WC-EXT-BANK-1"), (second, "WC-EXT-BANK-2")):
			self.t.certify_invoice(claim["invoice"])
			self.t.pay(claim["invoice"], bank)
			self.assertEqual(frappe.db.get_value("Contract Invoice", claim["invoice"], "state"), "Paid")
		self.assertIn(("IssueCompletionCertificate", "Issue the completion certificate.", "actionable"), self.tasks("charles"), "the head is asked to issue the certificate once everything is accepted and settled")
		closeout.issue_completion_certificate(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("completion"), actor=self.p["charles"])
		self.t.confirm_delivery()
		review = frappe.db.get_value("Contract Closeout", {"contract_case": self.case, "state": "Awaiting signature"}, "name")
		closeout.sign_closeout(self.case, closeout=review, expected_version=self.t.version(), idempotency_key=self.t.key("close"), actor=self.p["amina"])
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Closed")
		self.assertEqual(frappe.db.count("Contract Signature", {"contract_case": self.case}), 0, "still nobody was asked to sign the agreement")
		self.assertEqual(flt(frappe.db.get_value("Contract Case", self.case, "record_version")) > 0, True)
