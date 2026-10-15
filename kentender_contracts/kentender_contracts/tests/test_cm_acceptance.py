# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.6 and boards D06, D07 (plan Phase 6; tracker CM8-605; CM-AC-06, 07, 10): what a member can do with a frozen acceptance report besides sign it.

A member can sign with a recorded dissent, which cannot be outvoted: the units named become needs-review and are read again. A member can send the report back to the chair for correction, before it is
effective, keeping every signature it has. Where the appointment leaves acceptance to the Accounting Officer, the committee's signed report is a recommendation and the Accounting Officer's own
signature on that exact report makes it effective; no such extra decision exists where the committee decides."""

from __future__ import annotations

import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import delivery, errors, position, records, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class AcceptanceCase(ContractCase):
	native = True
	authority = "Committee accepts"

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
		self.t = tw.Thread(self.p, tag="ACC")
		self.case = self.t.active()
		self.t.appointed(self.authority)
		self.units = tw.fresh_serials(4)
		self.arrival = self.t.arrive(self.units)["arrival"]
		self.t.inspect(self.arrival, self.units)

	def prepare(self):
		delivery.sign_technical_certificate(self.case, arrival=self.arrival, expected_version=self.t.version(), idempotency_key=self.t.key("cert"), actor=self.p["peter"])
		return delivery.prepare_acceptance_report(self.case, arrivals=[self.arrival], expected_version=self.t.version(), idempotency_key=self.t.key("prepare"), actor=self.p["julia"])["acceptance"]

	def sign(self, who, report, **kw):
		return delivery.sign_acceptance_report(self.case, acceptance=report, expected_version=self.t.version(), idempotency_key=self.t.key(f"sign-{who}"), actor=self.p[who], **kw)

	def sign_all(self, report, **dissent):
		out = {}
		for who in ("julia", "peter", "brian"):
			out = self.sign(who, report, **(dissent if who == "brian" else {}))
		return out

	def report(self, name):
		return frappe.get_doc("Contract Acceptance", name)

	def mine(self, *who):
		users = {self.p[w] for w in who}
		return {(x["command"].split(":")[0], x["holder"], x["state"], x["title"]) for x in work.live(self.case) if x["holder"] in users}


class TestDissent(AcceptanceCase):
	def test_a_dissent_cannot_be_outvoted_the_named_unit_becomes_needs_review_and_only_the_rest_is_received(self):
		report = self.prepare()
		self.sign("julia", report)
		self.sign("peter", report)
		out = self.sign("brian", report, dissent_units=[self.units[2]], dissent_reason="The case is cracked.")
		self.assertTrue(out["effective"], "the member still signed: the report is decided by the rest")
		decided = position.decisions(self.case)
		self.assertEqual({u: d["disposition"] for u, d in decided.items()}, {self.units[0]: "accepted", self.units[1]: "accepted", self.units[3]: "accepted", self.units[2]: "deferred"})
		self.assertIn("Dissent recorded by Brian Wafula: The case is cracked.", decided[self.units[2]]["reason"])
		receipt = frappe.get_doc("Purchase Receipt", delivery.posted_receipts(self.case)[0])
		self.assertEqual(sum(r.qty for r in receipt.items), 3, "the dissented unit is not received")
		self.assertEqual(self.report(report).state, "Effective")
		proposed = records.loads(self.report(report).lines_json)[0]["units"]
		self.assertIn(self.units[2], proposed["accepted"], "the chair's report is kept as it was frozen")

	def test_the_dissent_is_attributed_in_the_signature_and_history(self):
		report = self.prepare()
		self.sign_all(report, dissent_units=[self.units[1]], dissent_reason="Wrong keyboard layout.")
		signers = records.loads(self.report(report).signers_json)
		by = {s["name"]: s for s in signers}
		self.assertEqual(by["Brian Wafula"]["dissent"], {"units": [self.units[1]], "reason": "Wrong keyboard layout."})
		self.assertIsNone(by["Julia Njeri"]["dissent"])
		events = frappe.get_all("Contract Event", filters={"contract_case": self.case, "event_type": "Acceptance report signed with dissent"}, pluck="actor")
		self.assertEqual(events, [self.p["brian"]])

	def test_a_dissent_needs_units_of_this_report_and_a_reason(self):
		report = self.prepare()
		self.assertEqual(refusal(self.sign, "brian", report, dissent_units=[self.units[0]]).fields["dissent_reason"], "Give the reason for your dissent.")
		self.assertIn("dissent_units", refusal(self.sign, "brian", report, dissent_reason="No.").fields)
		self.assertIn("dissent_units", refusal(self.sign, "brian", report, dissent_units=["NOT-A-UNIT"], dissent_reason="No.").fields)
		self.assertEqual(self.report(report).state, "Awaiting signatures", "nothing was signed by the refused attempts")

	def test_the_dissented_unit_is_read_again_confirmed_again_and_only_then_accepted(self):
		report = self.prepare()
		self.sign_all(report, dissent_units=[self.units[2]], dissent_reason="Cracked case.")
		self.assertEqual(delivery.certified_units(self.case, 1), {self.units[0], self.units[1], self.units[3]}, "the earlier confirmation no longer stands for the dissented unit")
		live = self.mine("peter", "julia", "brian")
		self.assertIn(("RecordInspectionObservations", self.p["peter"], "actionable", "A member's dissent needs a repeated reading."), live)
		second = delivery.prepare_acceptance_report
		stuck = refusal(second, self.case, arrivals=[self.arrival], expected_version=self.t.version(), idempotency_key=self.t.key("again"), actor=self.p["julia"])
		self.assertEqual((stuck.code, stuck.detail["units"]), ("CM_INCOMPLETE", [self.units[2]]), "the confirmation is already signed, but there is no new reading: a report would decide nothing")
		delivery.record_inspection(self.case, arrival=self.arrival, expected_version=self.t.version(), idempotency_key=self.t.key("reread"), actor=self.p["peter"], observations=tw.readings([self.units[2]]))
		delivery.sign_technical_certificate(self.case, arrival=self.arrival, expected_version=self.t.version(), idempotency_key=self.t.key("cert2"), actor=self.p["peter"])
		again = delivery.prepare_acceptance_report(self.case, arrivals=[self.arrival], expected_version=self.t.version(), idempotency_key=self.t.key("prepare2"), actor=self.p["julia"])["acceptance"]
		line = records.loads(self.report(again).lines_json)[0]
		self.assertEqual((line["units"]["accepted"], line["accepted"] + line["rejected"] + line["deferred"]), ([self.units[2]], 1), "only the unit that was re-read is in the new report")
		self.sign_all(again)
		self.assertEqual(position.decisions(self.case)[self.units[2]]["disposition"], "accepted")
		self.assertEqual(len(delivery.posted_receipts(self.case)), 2)
		self.assertEqual(position.dissents(self.case), {}, "a later decision closes the dissent")


class TestCorrection(AcceptanceCase):
	def test_a_member_sends_the_report_back_it_keeps_its_signatures_and_the_chair_prepares_again(self):
		report = self.prepare()
		self.sign("julia", report)
		delivery.request_acceptance_correction(self.case, acceptance=report, reason="Unit CMT-3 is listed twice.", expected_version=self.t.version(), idempotency_key=self.t.key("correct"), actor=self.p["peter"])
		old = self.report(report)
		self.assertEqual((old.state, old.correction_reason), ("Superseded", "Unit CMT-3 is listed twice."))
		self.assertEqual([s["state"] for s in records.loads(old.signers_json)], ["Signed", "Awaiting", "Awaiting"], "the signatures it had are kept as history")
		self.assertFalse([1 for c, h, s, _t in self.mine("brian", "peter") if c == "SignAcceptanceReport" and s in ("actionable", "waiting")], "no one is asked to sign a report that was sent back")
		self.assertIn(("PrepareAcceptanceReport", self.p["julia"], "actionable", "Correct the acceptance report."), self.mine("julia"))
		again = delivery.prepare_acceptance_report(self.case, arrivals=[self.arrival], expected_version=self.t.version(), idempotency_key=self.t.key("prepare2"), actor=self.p["julia"])
		self.assertEqual(self.report(again["acceptance"]).version_no, 2)
		self.assertEqual({s["state"] for s in records.loads(self.report(again["acceptance"]).signers_json)}, {"Awaiting"}, "everyone signs the new report for themselves")
		self.assertEqual(delivery.posted_receipts(self.case), [])

	def test_a_correction_needs_a_reason_a_signer_and_a_report_that_is_not_yet_effective(self):
		report = self.prepare()
		self.assertIn("reason", refusal(delivery.request_acceptance_correction, self.case, acceptance=report, reason=" ", expected_version=self.t.version(), idempotency_key=self.t.key("c1"), actor=self.p["peter"]).fields)
		self.assertEqual(refusal(delivery.request_acceptance_correction, self.case, acceptance=report, reason="Why", expected_version=self.t.version(), idempotency_key=self.t.key("c2"), actor=self.p["grace"]).code, "CM_AUTHORITY")
		self.sign_all(report)
		late = refusal(delivery.request_acceptance_correction, self.case, acceptance=report, reason="Too late", expected_version=self.t.version(), idempotency_key=self.t.key("c3"), actor=self.p["peter"])
		self.assertEqual(late.code, "CM_CHANGED")
		self.assertIn("reversal", late.detail["reason"])

	def test_the_chair_sees_why_the_report_came_back(self):
		report = self.prepare()
		delivery.request_acceptance_correction(self.case, acceptance=report, reason="Unit CMT-3 is listed twice.", expected_version=self.t.version(), idempotency_key=self.t.key("correct"), actor=self.p["brian"])
		board = router.board_for(self.case, self.p["julia"])
		regions = {r["t"]: r for r in board["regions"]}
		self.assertIn("Correction requested", regions)
		self.assertIn("Unit CMT-3 is listed twice.", frappe.as_json(regions["Correction requested"]))


class TestAccountingOfficerDecides(AcceptanceCase):
	authority = "Accounting Officer decides"

	def test_the_signed_report_is_a_recommendation_and_nothing_is_received_until_the_accounting_officer_decides(self):
		report = self.prepare()
		out = self.sign_all(report)
		self.assertEqual((out.get("effective"), out.get("recommended")), (False, True))
		self.assertEqual(self.report(report).state, "Recommended")
		self.assertEqual(delivery.posted_receipts(self.case), [])
		self.assertEqual(position.decisions(self.case), {}, "a recommendation decides no unit")
		self.assertIn(("DecideContractAcceptance", self.p["amina"], "actionable", "Decide on the acceptance report."), self.mine("amina"))
		self.assertIn(("DecideContractAcceptance", self.p["julia"], "waiting", "Waiting for the Accounting Officer's decision."), self.mine("julia"))

	def test_the_accounting_officers_signature_on_that_report_makes_it_effective_and_posts_once(self):
		report = self.prepare()
		self.sign_all(report)
		out = delivery.decide_acceptance(self.case, acceptance=report, expected_version=self.t.version(), idempotency_key=self.t.key("decide"), actor=self.p["amina"])
		self.assertTrue(out["effective"])
		doc = self.report(report)
		self.assertEqual(doc.state, "Effective")
		self.assertEqual(records.loads(doc.decision_json)["decided_by"], self.p["amina"])
		self.assertEqual(len(delivery.posted_receipts(self.case)), 1)
		self.assertFalse([1 for c, *_ in self.mine("amina") if c == "DecideContractAcceptance"], "her task is done")

	def test_only_the_accounting_officer_decides_and_only_a_recommended_report(self):
		report = self.prepare()
		self.assertEqual(refusal(delivery.decide_acceptance, self.case, acceptance=report, expected_version=self.t.version(), idempotency_key=self.t.key("d0"), actor=self.p["amina"]).code, "CM_CHANGED", "not recommended yet")
		self.sign_all(report)
		self.assertEqual(refusal(delivery.decide_acceptance, self.case, acceptance=report, expected_version=self.t.version(), idempotency_key=self.t.key("d1"), actor=self.p["julia"]).code, "CM_AUTHORITY")

	def test_the_accounting_officer_can_send_a_recommendation_back(self):
		report = self.prepare()
		self.sign_all(report)
		delivery.request_acceptance_correction(self.case, acceptance=report, reason="Show the rejected units separately.", expected_version=self.t.version(), idempotency_key=self.t.key("back"), actor=self.p["amina"])
		self.assertEqual(self.report(report).state, "Superseded")
		self.assertIn(("PrepareAcceptanceReport", self.p["julia"], "actionable", "Correct the acceptance report."), self.mine("julia"))

	def test_the_accounting_officer_sees_the_report_with_any_dissent_applied(self):
		report = self.prepare()
		self.sign_all(report, dissent_units=[self.units[1]], dissent_reason="Cracked case.")
		board = router.board_for(self.case, self.p["amina"])
		self.assertEqual((board["id"], board["p"]), ("D07-A", "Accept as recommended"))
		self.assertIn("Cracked case.", frappe.as_json(board["regions"]))
		out = delivery.decide_acceptance(self.case, acceptance=report, expected_version=self.t.version(), idempotency_key=self.t.key("decide"), actor=self.p["amina"])
		self.assertEqual(position.decisions(self.case)[self.units[1]]["disposition"], "deferred")


class TestWhoAccepts(AcceptanceCase):
	def test_the_appointment_records_who_accepts_and_refuses_anything_else(self):
		self.assertEqual(frappe.db.get_value("Contract Appointment", {"contract_case": self.case, "state": "Appointed"}, "acceptance"), "Committee accepts")
		exc = refusal(delivery.recommend_inspectors, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("rec"), actor=self.p["charles"],
			members=[{"user": self.p["julia"], "capacity": "Chair"}, {"user": self.p["peter"], "certifier": True}, {"user": self.p["brian"]}], acceptance="Whoever is free")
		self.assertIn("acceptance", exc.fields)
