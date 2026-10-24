# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.7, 5.11, 5.19, 7 (CM-R-12, LQ-04) and boards D36, D36-A, D36-S, D36-H, D36-E (plan Phase 8; tracker CM8-803): the contractual delay adjustment.

The system proposes the calculation from the operative due date, the day the last unit was accepted, the rate and the cap; nobody types the figure. An effective extension moves the due date and the earlier
computation is kept; an unsigned request moves nothing. The Accounting Officer (never the person who prepared it) approves, declines or returns it. An approved adjustment becomes a native deduction on the next
invoice through a Finance-verified mapping and is noncash: cash 995,000 and the adjustment 5,000 settle the 1,000,000. With no verified mapping the affected payment is held with a named owner."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D  # noqa: F401
from unittest import mock

import frappe

from kentender_contracts.rules import profile as profiles
from kentender_contracts.services import adjustment, change, errors, holds, payment, records, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class DelayCase(ContractCase):
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
		self.addCleanup(lambda: (setattr(frappe.conf, adjustment.MAPPING_FLAG, None), self.env.__exit__(None, None, None)))
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24])
		self.case = self.t.active()
		self.t.appointed()

	def delivered(self, on=D("2027-07-25 10:00:00")):
		"""All ten laptops arrive and are accepted on `on` (the actual delivery event)."""
		units = tw.fresh_serials(10)
		arrival = self.t.arrive(units, received_at=D("2027-07-12 10:00:00"))["arrival"]
		self.t.inspect(arrival, units)
		frappe.flags.kt_cm_clock = on
		return self.t.accept(arrival)

	def prepare(self, who="charles", **kw):
		return adjustment.prepare(self.case, causation=kw.pop("causation", "Supplier shipment delay"), clause=kw.pop("clause", "TEST-DELAY-01"), supplier_response=kw.pop("supplier_response", "Requests exclusion of two days."),
			expected_version=self.t.version(), idempotency_key=self.t.key("prep"), actor=self.p[who], **kw)

	def decide(self, decision="Approve", number=1, who="amina", reason="Supplier-responsible five-day delay established."):
		return adjustment.decide(self.case, adjustment=adjustment.get(self.case, number).name, decision=decision, reason=reason, expected_version=self.t.version(), idempotency_key=self.t.key("dec"), actor=self.p[who])

	def row(self, number=1):
		return adjustment.get(self.case, number)

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}


class TestCalculation(DelayCase):
	def test_five_days_late_is_one_thousand_a_day_for_five_thousand_and_the_inputs_are_shown_with_it(self):
		self.delivered()
		out = self.prepare()
		figures = adjustment.calculation(self.row())
		self.assertEqual((out["days"], out["amount"]), (5, 5000))
		self.assertEqual((figures["due"], figures["event"], figures["days"]), (D("2027-07-20"), D("2027-07-25"), 5))
		self.assertEqual((figures["principal"], figures["rate_percent"], figures["daily"], figures["gross"], figures["cap"], figures["amount"]), (1_000_000, 0.1, 1000, 5000, 100_000, 5000))
		self.assertEqual((figures["clause"], figures["exclusions"], figures["extensions"]), ("TEST-DELAY-01", [], []))
		self.assertIn("up to and including", figures["count_basis"])
		self.assertEqual((self.row().state, self.row().causation), ("Submitted", "Supplier shipment delay"))
		self.assertIn(("DecideContractAdjustment", "Decide the proposed delay adjustment.", "actionable"), self.tasks("amina"))

	def test_the_form_s_recommendation_reaches_the_decision(self):
		"""The dialog's values travel through the command table, as the browser sends them; a value the table drops is lost to the person who decides."""
		from kentender_contracts.api import commands

		self.delivered()
		commands.COMMANDS["PrepareContractAdjustment"](self.case, {}, {"causation": "Supplier shipment delay", "clause": "TEST-DELAY-01", "supplier_response": "Requests exclusion of two days.", "recommendation": "No supported exclusion"},
			self.t.version(), self.t.key("form"), self.p["charles"])
		self.assertEqual(adjustment.calculation(self.row())["recommendation"], "No supported exclusion")

	def test_the_cap_limits_a_long_delay(self):
		self.delivered(on=D("2028-02-20 10:00:00"))  # 215 days late: 215,000 before the cap
		self.prepare()
		figures = adjustment.calculation(self.row())
		self.assertEqual((figures["gross"], figures["cap"], figures["amount"]), (215_000, 100_000, 100_000))

	def test_there_is_nothing_to_adjust_until_every_unit_is_accepted_or_when_delivery_was_on_time(self):
		self.assertIn("delivery", refusal(self.prepare).fields)  # nothing delivered yet
		self.delivered(on=D("2027-07-20 10:00:00"))  # on the due date itself
		self.assertIn("delivery", refusal(self.prepare).fields)

	def test_a_missing_cause_or_clause_is_corrected(self):
		self.delivered()
		self.assertIn("causation", refusal(self.prepare, causation=" ").fields)
		self.assertIn("clause", refusal(self.prepare, clause="").fields)

	def test_only_a_preparer_prepares_and_the_production_profile_refuses_until_it_is_verified(self):
		self.delivered()
		self.assertEqual(refusal(self.prepare, who="stranger").code, "CM_AUTHORITY")
		frappe.db.set_value("Contract Case", self.case, "legal_profile", "KE-PPADA-2015")
		out = refusal(self.prepare)
		self.assertEqual((out.code, out.reasons[0]["detail"]["rule"]), ("CM_RULE", "CM-R-12"))
		self.assertFalse(frappe.db.count("Contract Adjustment", {"contract_case": self.case}))

	def test_an_effective_extension_moves_the_due_date_and_the_earlier_computation_is_kept(self):
		self.delivered()
		self.prepare()
		self.decide("Return", reason="An extension may apply; re-read it.")
		self.t.change_through("Extension", {"proposed_date": D("2027-07-22")})  # signed by both: the operative due date is now 22 July
		self.prepare()
		figures = adjustment.calculation(self.row(2))
		self.assertEqual((figures["due"], figures["original_due"], figures["days"], figures["amount"]), (D("2027-07-22"), D("2027-07-20"), 3, 3000))
		self.assertEqual(figures["extensions"][0]["to"], D("2027-07-22"))
		self.assertEqual((figures["prior"]["amount"], figures["prior"]["days"], figures["prior"]["due"]), (5000, 5, D("2027-07-20")))
		self.assertEqual((self.row(1).state, self.row(2).supersedes), ("Superseded", self.row(1).name))

	def test_a_request_that_is_not_signed_changes_no_date(self):
		self.delivered()
		change.request_change(self.case, kind="Extension", request={"proposed_date": D("2027-07-22")}, reason="Delay.", evidence=[{"label": "Supplier request 1", "file": "/private/files/r.pdf"}], expected_version=self.t.version(),
			idempotency_key=self.t.key("ask"), actor=self.p["david"])
		self.prepare()
		self.assertEqual(adjustment.calculation(self.row())["days"], 5)


class TestDecision(DelayCase):
	def setUp(self):
		super().setUp()
		self.delivered()
		self.prepare()

	def test_only_the_accounting_officer_decides_and_never_the_person_who_prepared_it(self):
		self.assertEqual(refusal(self.decide, who="charles").code, "CM_AUTHORITY")
		frappe.db.set_value("Contract Adjustment", self.row().name, "prepared_by", self.p["amina"])
		self.assertEqual(refusal(self.decide).code, "CM_SEGREGATION")
		self.assertEqual(self.row().state, "Submitted")

	def test_a_decision_needs_a_reason_and_a_decline_or_return_is_recorded_with_it(self):
		self.assertIn("reason", refusal(self.decide, reason=" ").fields)
		self.decide("Decline", reason="The supplier's exclusion is supported.")
		self.assertEqual((self.row().state, records.loads(self.row().decision_json)["reason"]), ("Declined", "The supplier's exclusion is supported."))
		self.assertEqual(adjustment.applied_to("none"), 0)
		self.assertFalse(adjustment.pending_application(self.case))

	def test_a_returned_proposal_goes_back_to_the_head_of_procurement(self):
		self.decide("Return", reason="Re-read the extension.")
		self.assertEqual(self.row().state, "Returned")
		self.assertIn(("PrepareContractAdjustment", "Correct the delay adjustment.", "actionable"), self.tasks("charles"))

	def test_an_automatic_deduction_is_held_for_the_legal_question_unless_the_profile_answers_it(self):
		verified = profiles.Profile("VERIFIED-NO-ANSWER", "A verified profile that has not answered LQ-04", profiles.VERIFIED, False, profiles.STATUTORY + profiles.SYNTHETIC_ONLY)
		with mock.patch.dict(profiles.PROFILES, {verified.id: verified}):
			frappe.db.set_value("Contract Case", self.case, "legal_profile", verified.id)
			out = refusal(self.decide)
			self.assertEqual((out.code, out.reasons[0]["detail"]["question"], out.reasons[0]["detail"]["branch"]), ("CM_HOLD", "LQ-04", "automatic_deduction"))
			self.assertEqual(self.row().state, "Submitted")
			self.decide("Return", reason="Held for the legal question.")  # a return is not a deduction

	def test_an_approved_adjustment_waits_to_be_applied_and_a_second_proposal_is_refused_meanwhile(self):
		self.decide()
		self.assertEqual(self.row().state, "Approved")
		self.assertEqual([r.name for r in adjustment.pending_application(self.case)], [self.row().name])
		self.assertEqual(refusal(self.prepare).code, "CM_CHANGED")


class TestApplication(DelayCase):
	def setUp(self):
		super().setUp()
		self.delivered()
		self.prepare()
		self.decide()
		self.claim_and_certify()

	def claim_and_certify(self):
		self.invoice = self.t.claim("INV-ADJ-1", 10)["invoice"]
		self.t.certify_invoice(self.invoice)

	def account(self):
		return frappe.db.get_value("Account", {"company": world.COMPANY, "is_group": 0, "root_type": "Expense", "disabled": 0}, "name")

	def native(self):
		return frappe.db.get_value("Contract Invoice", self.invoice, "native_invoice")

	def test_with_no_verified_mapping_the_payment_is_held_with_a_named_owner_and_nothing_else_is(self):
		held = [h for h in holds.open_holds(self.case) if h.key == "adjustment mapping"]
		self.assertEqual(len(held), 1)
		self.assertEqual((held[0].reason, held[0].owner), ("The native deduction mapping is unverified.", self.p["josphat"]))
		self.assertTrue(holds.blocking(self.case, "pay"))
		self.assertFalse(holds.blocking(self.case, "certify_invoice"))
		self.assertFalse(holds.blocking(self.case, "new_spending"))
		self.assertEqual(adjustment.mapping_problems(), ["Finance has not named the account for contractual deductions."])

	def test_a_mapping_that_is_not_a_ledger_account_is_not_verified(self):
		frappe.conf[adjustment.MAPPING_FLAG] = "No such account"
		self.assertIn("does not exist", adjustment.mapping_problems()[0])
		group = frappe.db.get_value("Account", {"company": world.COMPANY, "is_group": 1}, "name")
		frappe.conf[adjustment.MAPPING_FLAG] = group
		self.assertIn("cannot be posted to", adjustment.mapping_problems()[0])

	def test_the_adjustment_is_a_native_deduction_and_noncash_so_cash_and_adjustment_settle_the_invoice(self):
		frappe.conf[adjustment.MAPPING_FLAG] = self.account()
		self.t.post_accounting(self.invoice)
		pi = frappe.get_doc("Purchase Invoice", self.native())
		deduction = [t for t in pi.taxes if t.description.startswith(adjustment.MARKER)]
		self.assertEqual((len(deduction), deduction[0].add_deduct_tax, float(deduction[0].tax_amount)), (1, "Deduct", 5000))
		self.assertEqual(float(pi.grand_total), 995_000)
		self.assertEqual((self.row().state, self.row().invoice), ("Applied", self.invoice))
		now = payment.invoice_position(self.case, self.invoice)
		self.assertEqual((now["certified"], now["adjustment"], now["noncash"], now["outstanding"], now["cash_confirmed"]), (1_000_000, 5000, 5000, 995_000, 0))
		self.assertFalse(holds.blocking(self.case, "pay"))  # applied: nothing is waiting for a mapping
		self.t.pay(self.invoice, "ADJ-BANK-1")
		done = payment.invoice_position(self.case, self.invoice)
		self.assertEqual((done["cash_confirmed"], done["noncash"], done["outstanding"]), (995_000, 5000, 0))
		self.assertEqual(frappe.db.get_value("Contract Invoice", self.invoice, "state"), "Paid")

	def test_applying_twice_adds_one_deduction(self):
		frappe.conf[adjustment.MAPPING_FLAG] = self.account()
		self.t.post_accounting(self.invoice)
		self.assertEqual(adjustment.apply_to_native(self.case, self.invoice, self.native()), [])
		pi = frappe.get_doc("Purchase Invoice", self.native())
		self.assertEqual(len([t for t in pi.taxes if t.description.startswith(adjustment.MARKER)]), 1)
