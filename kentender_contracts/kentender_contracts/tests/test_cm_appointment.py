# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.6, 6.1, boards D23, D24 and their variants (plan Phase 6; tracker CM8-601; CM-AC-38): a declaration, a conflict, a replacement and a report that has to be reconstituted.

The appointment is the written authority to inspect. A member who stays keeps the declaration they made; one who comes in declares for themselves; a conflict suspends the member's own work and
the whole appointment until it is replaced; a replacement applies from then on and nothing earlier is rewritten; and a report that is still waiting for signatures is superseded by a reviewed
successor, its signatures kept as history on it, so no earlier signature is ever read as a new member's."""

from __future__ import annotations

import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import bindings, delivery, errors, records, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class TestAppointment(ContractCase):
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
		self.t = tw.Thread(self.p, tag="APT")
		self.case = self.t.active()
		self.t.appointed()

	def mine(self, *who):
		users = {self.p[w] for w in who} if who else set(self.p.values())
		return {(x["command"].split(":")[0], x["holder"], x["state"]) for x in work.live(self.case) if x["holder"] in users}

	def conflict(self, who="peter", reason="A close family member works for the supplier."):
		return delivery.declare_interest(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("conflict"), actor=self.p[who], conflict=reason)

	def replace(self, *, leaving="peter", coming="faith", technical=True):
		members = [{"user": self.p["julia"], "capacity": "Chair", "role_label": "User department"}, {"user": self.p[coming if technical else "peter"], "capacity": "Member", "certifier": True, "role_label": "Technical"},
			{"user": self.p["brian"], "capacity": "Member", "role_label": "Procurement"}]
		if not technical:
			members[1] = {"user": self.p["faith"], "capacity": "Member", "role_label": "Technical", "certifier": False}
		rec = delivery.recommend_inspectors(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("re-recommend"), actor=self.p["charles"], members=members)
		return delivery.appoint_inspectors(self.case, appointment=rec["appointment"], expected_version=self.t.version(), idempotency_key=self.t.key("re-appoint"), actor=self.p["amina"])

	def declared(self, who):
		return frappe.get_doc("Contract Appointment", bindings.effective_appointment(self.case)["appointment"]).members_json and next(
			(m for m in records.loads(frappe.get_doc("Contract Appointment", bindings.effective_appointment(self.case)["appointment"]).members_json) if m["user"] == self.p[who]), None)

	# -- a replacement ---------------------------------------------------------------------------------------------------------------
	def test_a_member_who_stays_keeps_the_declaration_and_a_new_member_declares_for_themselves(self):
		self.t.arrive(tw.fresh_serials(1))
		first = bindings.effective_appointment(self.case)
		self.replace(leaving="peter", coming="faith")
		now = bindings.effective_appointment(self.case)
		self.assertEqual(now["version"], first["version"] + 1)
		self.assertTrue(self.declared("julia")["declared_at"] and self.declared("brian")["declared_at"], "the members who stay keep what they declared")
		self.assertIsNone(self.declared("faith")["declared_at"], "a new member declares for themselves")
		self.assertIn(("DeclareContractInterest", self.p["faith"], "actionable"), self.mine("faith"))
		self.assertFalse([1 for c, _h, _s in self.mine("julia", "brian") if c == "DeclareContractInterest"])
		self.assertFalse(delivery.appointment_state(self.case)["ready"], "the inspectors are not ready until the new member declares")
		self.assertEqual(refusal(delivery.record_inspection, self.case, arrival=frappe.get_all("Contract Arrival", filters={"contract_case": self.case}, pluck="name")[0], expected_version=self.t.version(),
			idempotency_key=self.t.key("early"), actor=self.p["julia"], observations=[]).code, "CM_APPOINTMENT")
		delivery.declare_interest(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("declare-faith"), actor=self.p["faith"])
		self.assertTrue(delivery.appointment_state(self.case)["ready"])
		self.assertEqual(frappe.db.get_value("Contract Appointment", first["appointment"], "state"), "Replaced", "the earlier appointment stays as history")

	def test_the_replaced_member_loses_authority_and_their_work_passes_to_the_people_now_appointed(self):
		out = self.t.arrive(tw.fresh_serials(2))
		self.assertIn(("RecordInspectionObservations", self.p["peter"], "actionable"), self.mine("peter"))
		self.replace(leaving="peter", coming="faith")
		self.assertIsNone(bindings.member(self.case, self.p["peter"]), "the removed member no longer has authority")
		self.assertFalse([1 for c, _h, s in self.mine("peter") if c == "RecordInspectionObservations" and s == "actionable"])
		self.assertIn(("RecordInspectionObservations", self.p["faith"], "actionable"), self.mine("faith"), "the inspection is now theirs to do")
		self.assertEqual(refusal(delivery.record_inspection, self.case, arrival=out["arrival"], expected_version=self.t.version(), idempotency_key=self.t.key("stale"), actor=self.p["peter"], observations=[]).code, "CM_AUTHORITY")

	# -- a conflict ------------------------------------------------------------------------------------------------------------------
	def test_a_declared_conflict_suspends_the_members_own_work_and_the_whole_appointment_until_it_is_replaced(self):
		out = self.t.arrive(tw.fresh_serials(2))
		self.conflict("peter")
		self.assertFalse([1 for c, _h, s in self.mine("peter") if c == "RecordInspectionObservations" and s in ("actionable", "blocked")], "the conflicted member's own inspection work is closed")
		self.assertIn(("RecommendContractInspectors", self.p["charles"], "actionable"), self.mine("charles"), "replacement work opens for HOP")
		self.assertFalse(delivery.appointment_state(self.case)["ready"])
		for who in ("julia", "brian"):
			self.assertEqual(refusal(delivery.record_inspection, self.case, arrival=out["arrival"], expected_version=self.t.version(), idempotency_key=self.t.key("blocked"), actor=self.p[who],
				observations=[]).code, "CM_APPOINTMENT", "nobody inspects while a member is in conflict")
		self.replace(leaving="peter", coming="faith")
		delivery.declare_interest(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("declare-faith"), actor=self.p["faith"])
		self.assertTrue(delivery.appointment_state(self.case)["ready"])
		self.assertTrue(delivery.record_inspection(self.case, arrival=out["arrival"], expected_version=self.t.version(), idempotency_key=self.t.key("ok"), actor=self.p["faith"],
			observations=tw.readings(frappe.get_all("Contract Arrival", filters={"name": out["arrival"]}, pluck="items_json") and [u for i in records.loads(frappe.db.get_value("Contract Arrival", out["arrival"], "items_json")) for u in i["units"]]))["ok"])

	# -- a report waiting for signatures ---------------------------------------------------------------------------------------------
	def test_a_report_waiting_for_signatures_is_superseded_by_a_successor_and_its_signatures_stay_with_it(self):
		units = tw.fresh_serials(2)
		out = self.t.arrive(units)
		self.t.inspect(out["arrival"], units)
		delivery.sign_technical_certificate(self.case, arrival=out["arrival"], expected_version=self.t.version(), idempotency_key=self.t.key("cert"), actor=self.p["peter"])
		prepared = delivery.prepare_acceptance_report(self.case, arrivals=[out["arrival"]], expected_version=self.t.version(), idempotency_key=self.t.key("prepare"), actor=self.p["julia"])
		delivery.sign_acceptance_report(self.case, acceptance=prepared["acceptance"], expected_version=self.t.version(), idempotency_key=self.t.key("sign-julia"), actor=self.p["julia"])
		self.conflict("peter")
		self.replace(leaving="peter", coming="faith")
		old = frappe.get_doc("Contract Acceptance", prepared["acceptance"])
		self.assertEqual(old.state, "Superseded")
		signed = {s["user"]: s["state"] for s in records.loads(old.signers_json)}
		self.assertEqual(signed[self.p["julia"]], "Signed", "the signature that was made stays on the superseded report")
		self.assertIn(("PrepareAcceptanceReport", self.p["julia"], "actionable"), self.mine("julia"), "the chair prepares the successor")
		self.assertFalse([1 for c, _h, _s in self.mine("peter", "brian") if c == "SignAcceptanceReport"], "no signing task for the old report survives")
		self.assertEqual(frappe.db.count("Contract Event", {"contract_case": self.case, "event_type": "Acceptance report reconstituted"}), 1)

	# -- the screens -----------------------------------------------------------------------------------------------------------------
	def test_the_declaration_receipt_and_the_blocked_replacement_screens(self):
		self.conflict("peter")
		hop = tw.capture(router.board_for(self.case, self.p["charles"]))
		self.assertEqual((hop["id"], hop["next"]["k"], hop["p"]), ("D24-X", "blk", ""))
		self.assertIn("Peter Mugo must be replaced before the affected inspection can proceed.", hop["next"]["h"])
		self.assertEqual(sorted(hop["next"]["fixes"]), ["Revise appointment recommendation", "View declaration"])
		self.assertEqual(hop["actions"]["Revise appointment recommendation"]["route"][1:], ["agreement", "recommend"])
		form = router.board_for(self.case, self.p["charles"], tab="Agreement", subject=("recommend",))
		self.assertEqual(form["id"], "D23-R")
		julia = tw.capture(router.board_for(self.case, self.p["julia"], tab="Agreement"))
		self.assertEqual(julia["id"], "D24-S")
		self.assertEqual((julia["p"], julia["next"]["k"], julia["regions"][1]["b"][0]["items"][0]), ("", "done", ["Declaration", "I have no conflict of interest"]))
		self.assertEqual(router.board_for(self.case, self.p["julia"], tab="Agreement", subject=("appointment",))["id"] not in ("D24-S",), True)
