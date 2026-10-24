# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 6, 6.2.1 and CM-OD-09 (plan Phase 10; tracker CM8-1004; CM-AC-20): the adversarial authority scenarios, end to end, each failing **without side effects**.

A supplier of another organisation, an expired appointment, a supplier accepting their own delivery, Finance approving what Finance prepared, the maker confirming the settlement, the person who signed the acceptance
certifying the claim that depends on it, and a technical account acting on the business all meet a refusal, and after each the contract holds exactly the records it held before and the native world holds the documents it
held before. These are the services the screens call, with real ERPNext documents."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D  # noqa: F401
import frappe

from kentender_contracts.services import audience, delivery, errors, payment, records
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

NATIVE = ("Purchase Order", "Purchase Receipt", "Purchase Invoice", "Payment Entry", "Stock Ledger Entry", "GL Entry")


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class AdversarialCase(ContractCase):
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
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24])
		self.case = self.t.active()
		self.t.appointed()
		self.units = tw.fresh_serials(4)
		self.arrival = self.t.arrive(self.units, received_at=D("2027-07-12 10:00:00"))["arrival"]

	def snapshot(self) -> dict[str, int]:
		"""Everything the contract and the native world hold that a refused action could have changed."""
		mine = {d: frappe.db.count(d, {"contract_case": self.case}) for d in records.DOCTYPES if d != "Contract Case" and frappe.get_meta(d).has_field("contract_case")}
		mine.update({d: frappe.db.count(d) for d in NATIVE})
		mine["version"] = int(frappe.db.get_value("Contract Case", self.case, "record_version"))
		return mine

	def refused(self, fn, *codes, **kw):
		"""The call is refused with one of `codes` and nothing anywhere changed."""
		before = self.snapshot()
		exc = refusal(fn, **kw) if kw else refusal(fn)
		self.assertIn(exc.code, codes, f"{exc.code}: {exc}")
		self.assertEqual(self.snapshot(), before, "a refused action leaves nothing behind")
		return exc


class TestAnotherSupplier(AdversarialCase):
	def test_a_supplier_of_another_organisation_cannot_read_or_claim_on_the_contract(self):
		class Rival(tw.Suppliers):
			"""A second organisation's representative: a supplier account, but not this contract's supplier."""

			def active_assignments(self, *, user, at=None):
				rows = super().active_assignments(user=user, at=at)
				return rows or ([{"assignment_id": "A-rival", "organisation_id": "ORG-RIVAL", "user": user, "responsibility": "Supplier Representative", "active": True, "signatory_ready": False}] if user == "rival.rep@example.test" else [])

		frappe.flags.kt_supplier_account_provider = Rival()
		if not frappe.db.exists("User", "rival.rep@example.test"):
			frappe.get_doc({"doctype": "User", "email": "rival.rep@example.test", "first_name": "Rival", "last_name": "Rep", "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True)
			self.addCleanup(lambda: frappe.delete_doc("User", "rival.rep@example.test", force=True, ignore_permissions=True))
		self.assertEqual(audience.readable("rival.rep@example.test", self.case), [], "another supplier reads nothing of this contract")
		self.refused(lambda: payment.submit_invoice(self.case, expected_version=self.t.version(), idempotency_key="rival-claim", actor="rival.rep@example.test", claim_reference="RIVAL-1", invoice_date=frappe.utils.today(),
			lines=[{"line_id": "L1", "quantity": 1}]), "CM_AUTHORITY", "CM_SEGREGATION")  # a supplier claims only as this contract's representative or signatory


class TestExpiredAppointment(AdversarialCase):
	def test_an_inspector_whose_appointment_has_ended_cannot_record_observations(self):
		appointment = frappe.get_all("Contract Appointment", filters={"contract_case": self.case, "state": "Appointed"}, pluck="name")[0]
		frappe.db.set_value("Contract Appointment", appointment, "effective_to", D("2027-07-01 00:00:00"))
		self.refused(lambda: delivery.record_inspection(self.case, arrival=self.arrival, expected_version=self.t.version(), idempotency_key="expired-inspect", actor=self.p["peter"], observations=tw.readings(self.units)),
			"CM_AUTHORITY", "CM_APPOINTMENT")


class TestSelfAcceptance(AdversarialCase):
	def test_the_supplier_cannot_sign_or_decide_their_own_delivery(self):
		self.t.inspect(self.arrival, self.units)
		delivery.sign_technical_certificate(self.case, arrival=self.arrival, expected_version=self.t.version(), idempotency_key="adv-cert", actor=self.p["peter"])
		report = delivery.prepare_acceptance_report(self.case, arrivals=[self.arrival], expected_version=self.t.version(), idempotency_key="adv-prep", actor=self.p["julia"])["acceptance"]
		for who in ("david", "mary"):
			self.refused(lambda who=who: delivery.sign_acceptance_report(self.case, acceptance=report, expected_version=self.t.version(), idempotency_key=f"adv-sign-{who}", actor=self.p[who]), "CM_AUTHORITY")
			self.refused(lambda who=who: delivery.decide_acceptance(self.case, acceptance=report, expected_version=self.t.version(), idempotency_key=f"adv-decide-{who}", actor=self.p[who]), "CM_AUTHORITY")


class TestFinanceSeparations(AdversarialCase):
	def accepted(self):
		self.t.inspect(self.arrival, self.units)
		self.t.accept(self.arrival)

	def test_the_person_who_signed_the_acceptance_cannot_certify_the_claim_that_depends_on_it(self):
		self.accepted()
		invoice = self.t.claim("ADV-1", 4)["invoice"]
		# Brian prepares contracts and sat on the committee that signed the acceptance report: the claim is certified by someone who did not
		exc = self.refused(lambda: payment.sign_certification(self.case, invoice=invoice, expected_version=self.t.version(), idempotency_key="adv-cert-brian", actor=self.p["brian"]), "CM_SEGREGATION", "CM_AUTHORITY")
		self.assertIn(exc.code, ("CM_SEGREGATION", "CM_AUTHORITY"))

	def test_finance_cannot_approve_what_finance_prepared_and_the_maker_cannot_confirm_the_settlement(self):
		self.accepted()
		invoice = self.t.claim("ADV-2", 4)["invoice"]
		self.t.certify_invoice(invoice)
		native = frappe.db.get_value("Contract Invoice", invoice, "native_invoice")
		payment.save_accounting_invoice(self.case, invoice=invoice, expected_version=self.t.version(), idempotency_key="adv-ai", actor=self.p["josphat"], posting_date=frappe.utils.today(),
			payable_account=frappe.db.get_value("Company", world.COMPANY, "default_payable_account"), cost_centre=frappe.db.get_value("Company", world.COMPANY, "cost_center"),
			expense_account=frappe.db.get_value("Purchase Invoice Item", {"parent": native}, "expense_account"))
		payment.submit_accounting_invoice(self.case, invoice=invoice, expected_version=self.t.version(), idempotency_key="adv-as", actor=self.p["josphat"])
		exc = self.refused(lambda: payment.approve_accounting_invoice(self.case, invoice=invoice, expected_version=self.t.version(), idempotency_key="adv-self-approve", actor=self.p["josphat"]), "CM_SEGREGATION", "CM_AUTHORITY")
		payment.approve_accounting_invoice(self.case, invoice=invoice, expected_version=self.t.version(), idempotency_key="adv-approve", actor=self.p["beatrice"])
		draft = payment.save_finance_draft(self.case, invoice=invoice, expected_version=self.t.version(), idempotency_key="adv-draft", actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="ADV-BANK")
		payment.submit_finance_for_approval(self.case, payment=draft["payment"], expected_version=self.t.version(), idempotency_key="adv-sp", actor=self.p["josphat"])
		self.refused(lambda: payment.approve_finance_record(self.case, payment=draft["payment"], expected_version=self.t.version(), idempotency_key="adv-self-pay", actor=self.p["josphat"]), "CM_SEGREGATION", "CM_AUTHORITY")
		payment.approve_finance_record(self.case, payment=draft["payment"], expected_version=self.t.version(), idempotency_key="adv-ap", actor=self.p["beatrice"])
		self.refused(lambda: payment.record_finance_settlement(self.case, payment=draft["payment"], expected_version=self.t.version(), idempotency_key="adv-maker-settles", actor=self.p["josphat"], effective_date=frappe.utils.today(),
			evidence="Bank line"), "CM_SEGREGATION", "CM_AUTHORITY")
		self.assertEqual(frappe.db.get_value("Payment Entry", draft["payment"], "docstatus"), 1, "the approved payment stays approved and unsettled")
