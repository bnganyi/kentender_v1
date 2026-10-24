# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.20, 7, 19.3 (CM-R-09, LQ-03) and boards D16, D37, D37-A, D37-P, D37-X (plan Phase 8; tracker CM8-805): actions on a verified security.

A claim's four facts are never one: the request, the Accounting Officer's decision, the communication actually delivered and the issuer's outcome. A replacement is verified before it supersedes the instrument in
force, and only when the two overlap. A return needs the evidenced final acceptance and no open claim; expiry releases nothing."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D, short_date  # noqa: F401
import frappe

from kentender_contracts.services import errors, records, security, security_actions, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


EVIDENCE = [{"label": "Default notice", "file": "/private/files/default.pdf"}]
AUGUST_12 = D("2027-08-12 09:00:00")


class SecurityActionCase(ContractCase):
	native = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: self.env.__exit__(None, None, None))
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24], security=True)
		self.case = self.t.active()
		frappe.flags.kt_cm_clock = AUGUST_12

	def ask(self, who="charles", **kw):
		return security_actions.request_claim(self.case, grounds=kw.pop("grounds", "Failure to perform the unfulfilled obligation"), amount=kw.pop("amount", 40_000), recipient=kw.pop("recipient", "Test Bank"),
			mandate=kw.pop("mandate", "Reviewed test mandate 1"), evidence=kw.pop("evidence", EVIDENCE), expected_version=self.t.version(), idempotency_key=self.t.key("ask"), actor=self.p[who], **kw)

	def decide(self, decision="Approve", who="amina", reason="The exact claim is supported.", number=1):
		return security_actions.decide_claim(self.case, claim=number, decision=decision, reason=reason, expected_version=self.t.version(), idempotency_key=self.t.key("dec"), actor=self.p[who])

	def communicate(self, number=1, **kw):
		return security_actions.record_communication(self.case, claim=number, sent_on=kw.pop("sent_on", D("2027-08-12")), channel=kw.pop("channel", "Courier"), reference=kw.pop("reference", "CR-0042"),
			evidence=kw.pop("evidence", [{"label": "Proof of delivery", "file": "/private/files/pod.pdf"}]), expected_version=self.t.version(), idempotency_key=self.t.key("comm"), actor=self.p[kw.pop("who", "charles")])

	def outcome(self, number=1, **kw):
		return security_actions.record_outcome(self.case, claim=number, issuer_reference=kw.pop("reference", "TEST-SG-OUT-01"), outcome_on=kw.pop("on", D("2027-08-13")), evidence=kw.pop("evidence", [{"label": "Test issuer outcome 1", "file": "/private/files/out.pdf"}]),
			proceeds=kw.pop("proceeds", 40_000), expected_version=self.t.version(), idempotency_key=self.t.key("out"), actor=self.p["charles"])

	def row(self, number=1):
		return security_actions.get_claim(self.case, number)

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}


class TestClaim(SecurityActionCase):
	def test_a_claim_records_the_grounds_the_amount_the_recipient_and_the_mandate_and_asks_the_accounting_officer(self):
		out = self.ask()
		row = self.row()
		self.assertEqual((row.state, row.amount, row.recipient, row.mandate, out["claim_no"]), ("Requested", 40_000, "Test Bank", "Reviewed test mandate 1", 1))
		self.assertEqual(row.security, security_actions.operative(self.case).name)
		self.assertIn(("DecideSecurityClaim", "Decide the security claim.", "actionable"), self.tasks("amina"))

	def test_the_claim_is_corrected_not_recorded_when_it_is_incomplete_above_the_instrument_or_on_an_expired_one(self):
		self.assertEqual(refusal(self.ask, who="stranger").code, "CM_AUTHORITY")
		self.assertIn("grounds", refusal(self.ask, grounds=" ").fields)
		self.assertIn("mandate", refusal(self.ask, mandate="").fields)
		self.assertIn("evidence", refusal(self.ask, evidence=[]).fields)
		self.assertIn("amount", refusal(self.ask, amount=0).fields)
		self.assertIn("amount", refusal(self.ask, amount=100_001).fields)
		frappe.flags.kt_cm_clock = D("2027-09-01 09:00:00")  # the day after the instrument expired
		out = refusal(self.ask)
		self.assertEqual((out.code, out.detail["hold"]), ("CM_HOLD", "security expired"))
		self.assertFalse(frappe.db.count("Contract Security Claim", {"contract_case": self.case}))

	def test_one_claim_at_a_time_and_a_contract_with_no_verified_security_has_none_to_claim_on(self):
		self.ask()
		self.assertEqual(refusal(self.ask).code, "CM_CHANGED")

	def test_only_the_accounting_officer_decides_and_never_the_person_who_prepared_it(self):
		self.ask()
		self.assertEqual(refusal(self.decide, who="charles").code, "CM_AUTHORITY")
		frappe.db.set_value("Contract Security Claim", self.row().name, "prepared_by", self.p["amina"])
		self.assertEqual(refusal(self.decide).code, "CM_SEGREGATION")
		frappe.db.set_value("Contract Security Claim", self.row().name, "prepared_by", self.p["charles"])
		self.assertIn("reason", refusal(self.decide, reason=" ").fields)

	def test_a_decision_gives_no_cash_status_and_a_returned_claim_is_corrected_and_decided_again(self):
		self.ask()
		self.decide("Return", reason="Attach the termination notice.")
		self.assertEqual(self.row().state, "Returned")
		self.assertIn(("RequestSecurityClaim", "Correct the security claim.", "actionable"), self.tasks("charles"))
		self.ask(correcting=1, evidence=EVIDENCE + [{"label": "Termination notice", "file": "/private/files/term.pdf"}])
		self.assertEqual((self.row().state, len(records.loads(self.row().evidence_json)), frappe.db.count("Contract Security Claim", {"contract_case": self.case})), ("Requested", 2, 1))
		self.decide()
		self.assertEqual((self.row().state, self.row().amount, records.loads(self.row().outcome_json)), ("Approved", 40_000, {}))
		self.assertIn(("RecordSecurityClaimCommunication", "Send the approved claim to the issuer.", "actionable"), self.tasks("charles"))

	def test_a_declined_claim_ends_there_and_a_later_one_may_be_made(self):
		self.ask()
		self.decide("Decline", reason="The loss is not shown.")
		self.assertEqual(self.row().state, "Declined")
		self.ask(grounds="Failure to perform, with the loss review attached")
		self.assertEqual(self.row(2).state, "Requested")

	def test_the_communication_and_then_the_outcome_are_each_their_own_recorded_fact(self):
		self.ask()
		self.decide()
		self.assertEqual(refusal(self.outcome).code, "CM_CHANGED")  # nothing was delivered yet, so there is nothing to answer
		self.assertIn("channel", refusal(self.communicate, channel=" ").fields)
		self.assertIn("evidence", refusal(self.communicate, evidence=[]).fields)
		self.communicate()
		self.assertEqual(self.row().state, "Communicated")
		self.assertIn(("RecordSecurityClaimOutcome", "Test Bank must respond to the approved claim; communication delivered " + short_date("2027-08-12") + ".", "waiting"), self.tasks("charles"))
		self.assertIn("proceeds", refusal(self.outcome, proceeds=40_001).fields)
		self.assertIn("issuer_reference", refusal(self.outcome, reference=" ").fields)
		out = self.outcome()
		self.assertEqual((out["state"], out["proceeds"], self.row().state), ("Outcome recorded", 40_000, "Outcome recorded"))
		self.assertFalse({t for t in self.tasks("charles") if t[0] == "RecordSecurityClaimOutcome"})
		self.assertIn("separately", [e["summary"] for e in __import__("kentender_contracts.services.events", fromlist=["history"]).history(self.case) if e["type"] == "Security claim outcome recorded"][0])


class TestReplacement(SecurityActionCase):
	def setUp(self):
		super().setUp()
		self.new = self.t.record_security(reference="TEST-SG-02", issued_on=D("2027-08-15"), expires_on=D("2027-09-30"), verify=False)

	def verify_new(self):
		return security.verify_security(self.case, security=self.new, expected_version=self.t.version(), idempotency_key=self.t.key("v"), actor=self.p["charles"], confirmation_reference="TEST-SG-CONF-02", received_on=D("2027-08-15"), basis="Issuer confirmation")

	def replace(self):
		return security_actions.replace(self.case, security_name=self.new, expected_version=self.t.version(), idempotency_key=self.t.key("rep"), actor=self.p["charles"])

	def test_the_old_instrument_stays_operative_until_the_replacement_is_verified_and_recorded(self):
		old = security_actions.operative(self.case).name
		self.assertNotEqual(old, self.new)
		self.assertEqual(refusal(self.replace).code, "CM_CHANGED")  # not verified
		self.verify_new()
		self.assertEqual(security_actions.operative(self.case).name, old)  # both are verified; the old one stays the instrument in force until the replacement is recorded
		self.assertEqual(frappe.db.get_value("Contract Security", old, "state"), "Verified")
		self.assertIn(("RecordSecurityAction", "Record the replacement security.", "actionable"), self.tasks("charles"))

	def test_a_verified_replacement_that_overlaps_supersedes_the_old_one(self):
		old = frappe.db.get_value("Contract Security", {"contract_case": self.case, "version_no": 1}, "name")
		self.verify_new()
		out = self.replace()
		self.assertEqual((out["replaced"], frappe.db.get_value("Contract Security", old, "state"), security_actions.operative(self.case).name), (old, "Superseded", self.new))
		self.assertFalse({t for t in self.tasks("charles") if t[0] == "RecordSecurityAction"})

	def test_a_replacement_that_leaves_a_gap_is_a_held_issue_and_the_old_instrument_stays(self):
		gap = self.t.record_security(reference="TEST-SG-03", issued_on=D("2027-09-05"), expires_on=D("2027-10-31"), verify=True)
		old = frappe.db.get_value("Contract Security", {"contract_case": self.case, "version_no": 1}, "name")
		out = refusal(security_actions.replace, self.case, security_name=gap, expected_version=self.t.version(), idempotency_key=self.t.key("gap"), actor=self.p["charles"])
		self.assertEqual((out.code, out.detail["hold"]), ("CM_HOLD", "security coverage gap"))
		self.assertEqual(frappe.db.get_value("Contract Security", old, "state"), "Verified")

	def test_a_replacement_for_less_than_the_instrument_is_refused(self):
		small = self.t.record_security(reference="TEST-SG-04", amount=100_000, issued_on=D("2027-08-15"), expires_on=D("2027-09-30"), verify=False)
		frappe.db.set_value("Contract Security", small, {"state": "Verified", "amount": 50_000})
		self.assertIn("amount", refusal(security_actions.replace, self.case, security_name=small, expected_version=self.t.version(), idempotency_key=self.t.key("small"), actor=self.p["charles"]).fields)


class TestReturn(SecurityActionCase):
	def final_acceptance(self, signed=D("2027-07-27 10:00:00")):
		records.new("Contract Certificate", contract_case=self.case, kind="Final acceptance", subject="final acceptance", subject_version=1, state="Signed", signer=self.p["amina"], proof_reference="TEST-PROOF",
			signed_at=signed, content_json="{}", record_version=1)

	def give_back(self, on=D("2027-08-01"), **kw):
		return security_actions.record_return(self.case, returned_on=on, evidence=kw.pop("evidence", [{"label": "Bank discharge TEST-SG-01", "file": "/private/files/discharge.pdf"}]), expected_version=self.t.version(),
			idempotency_key=self.t.key("ret"), actor=self.p[kw.pop("who", "charles")])

	def test_nothing_is_returned_without_the_evidenced_final_acceptance_even_after_expiry(self):
		frappe.flags.kt_cm_clock = D("2027-09-15 09:00:00")  # the instrument expired on 31 August
		out = refusal(self.give_back, on=D("2027-09-15"))
		self.assertEqual((out.code, out.detail["hold"]), ("CM_HOLD", "FINAL_ACCEPTANCE_NOT_EVIDENCED"))
		self.assertEqual(security_actions.operative(self.case).state, "Verified")  # expiry released nothing

	def test_the_return_is_due_thirty_days_after_the_final_acceptance_and_may_be_made_before_that(self):
		self.assertIsNone(security_actions.return_due(self.case))
		self.final_acceptance()
		self.assertEqual(str(security_actions.return_due(self.case)), D("2027-08-26"))
		instrument = security_actions.operative(self.case).name
		out = self.give_back(on=D("2027-08-01"))
		self.assertEqual((out["state"], frappe.db.get_value("Contract Security", instrument, "state")), ("Returned", "Returned"))
		detail = records.loads(frappe.db.get_value("Contract Security", instrument, "return_json"))
		self.assertEqual((detail["on"], detail["due"], detail["final_acceptance"]), (D("2027-08-01"), D("2027-08-26"), D("2027-07-27")))
		self.assertIsNone(security_actions.operative(self.case))

	def test_the_return_needs_its_evidence_a_date_after_the_final_acceptance_and_no_open_claim(self):
		self.final_acceptance()
		self.assertIn("evidence", refusal(self.give_back, evidence=[]).fields)
		self.assertIn("returned_on", refusal(self.give_back, on=D("2027-07-20")).fields)
		self.assertEqual(refusal(self.give_back, who="stranger").code, "CM_AUTHORITY")
		self.ask()
		blocked = refusal(self.give_back)
		self.assertEqual((blocked.code, blocked.detail["hold"]), ("CM_HOLD", "security claim open"))
		self.decide("Decline", reason="The loss is not shown.")
		self.give_back()
		self.assertEqual(frappe.db.get_value("Contract Security", {"contract_case": self.case, "version_no": 1}, "state"), "Returned")

	def ask(self):
		return security_actions.request_claim(self.case, grounds="Failure to perform", amount=40_000, recipient="Test Bank", mandate="Reviewed test mandate 1", evidence=EVIDENCE, expected_version=self.t.version(),
			idempotency_key=self.t.key("ask"), actor=self.p["charles"])

	def decide(self, decision, reason):
		return security_actions.decide_claim(self.case, claim=1, decision=decision, reason=reason, expected_version=self.t.version(), idempotency_key=self.t.key("dec"), actor=self.p["amina"])

	def test_the_production_profile_waits_for_the_legal_owner_before_any_return(self):
		self.final_acceptance()
		frappe.db.set_value("Contract Case", self.case, "legal_profile", "KE-PPADA-2015")
		out = refusal(self.give_back)
		self.assertEqual((out.code, out.reasons[0]["detail"]["rule"]), ("CM_RULE", "CM-R-09"))
