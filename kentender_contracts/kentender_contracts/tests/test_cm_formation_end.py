# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 5.14 (plan Phase 5; tracker CM8-505; FU-CM-42): a contract that does not come into being.

A refusal or an expired signing window never substitutes another supplier or ends the contract by itself. It raises one follow-up for the head of procurement, who records a reasoned outcome; only
live work ends and every record stays."""

from __future__ import annotations

import frappe

from kentender_contracts.boards import router
from kentender_contracts.services import errors, formation, formation_end, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

CONTROLS = "Contract Test Environment Controls"
WHY = "The supplier declined to sign"


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class TestFormationEnd(ContractCase):
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
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "")
		self.p, self.n = self.people, 0

	def k(self):
		self.n += 1
		return f"end-{self.id().rsplit('.', 1)[-1]}-{self.n}"

	def version(self, case):
		return frappe.db.get_value("Contract Case", case, "record_version")

	def prepared(self):
		out = tw.receive(self.p)
		saved = formation.save_particulars(out["contract"], expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["brian"], values=tw.package_particulars(self.p))
		return out["contract"]

	def sent(self):
		case = self.prepared()
		formation.request_signatures(case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["charles"])
		return case

	def end(self, case, *, who="charles", kind=WHY, reason="Mary Wanjiku told us the supplier will not sign."):
		return formation_end.record_not_proceeding(case, kind=kind, reason=reason, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p[who])

	def mine(self, case):
		ours = set(self.p.values())
		return {(t["command"], t["holder"], t["state"]) for t in work.live(case) if t["holder"] in ours}

	def test_a_reasoned_outcome_before_the_agreement_is_in_force_ends_the_live_work_and_keeps_every_record(self):
		case = self.sent()
		formation.sign_contract(case, party="Supplier", expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["mary"])
		self.end(case)
		doc = frappe.get_doc("Contract Case", case)
		self.assertEqual((doc.lifecycle, doc.outcome_reason), ("Did not proceed", f"{WHY}: Mary Wanjiku told us the supplier will not sign."))
		self.assertEqual(self.mine(case), set(), "no live work is left")
		self.assertEqual(frappe.db.get_value("Contract Agreement Version", {"contract_case": case}, "state"), "Ended")
		states = {s.party: s.state for s in frappe.get_all("Contract Signature", filters={"contract_case": case}, fields=["party", "state"])}
		self.assertEqual(states, {"Supplier": "Signed", "Entity": "Superseded"}, "a signature that was made stays as it was")
		self.assertEqual(frappe.db.count("Contract Event", {"contract_case": case, "event_type": "Did not proceed"}), 1)
		self.assertEqual(frappe.db.count("Contract Operation Intent", {"contract_case": case, "operation_kind": "Purchase order"}), 0, "no order was made")

	def test_it_is_reasoned_attributed_and_only_for_a_preparer(self):
		case = self.sent()
		self.assertEqual(refusal(self.end, case, reason=" ").fields["reason"], "Enter the reason.")
		self.assertEqual(refusal(self.end, case, kind="Because").fields["kind"], "Choose why the contract did not proceed.")
		for who in ("julia", "mary", "grace"):
			self.assertEqual(refusal(self.end, case, who=who).code, "CM_AUTHORITY", who)
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Awaiting signatures")

	def test_before_the_agreement_is_sent_it_can_be_recorded_too(self):
		case = self.prepared()
		self.end(case, kind="The award was withdrawn or changed", reason="Award withdrew the award.")
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Did not proceed")

	def test_it_is_terminal_and_nothing_else_can_be_done_on_the_contract(self):
		case = self.sent()
		self.end(case)
		self.assertEqual(refusal(self.end, case).code, "CM_CHANGED")
		self.assertEqual(refusal(formation.sign_contract, case, party="Supplier", expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["mary"]).code, "CM_CHANGED")
		self.assertEqual(refusal(formation.request_signatures, case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["charles"]).code, "CM_CHANGED")

	def test_an_agreement_in_force_cannot_be_ended_this_way(self):
		case = self.sent()
		first = formation.sign_contract(case, party="Supplier", expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["mary"])
		formation.sign_contract(case, party="Entity", expected_version=first["record_version"], idempotency_key=self.k(), actor=self.p["amina"])
		self.assertEqual(refusal(self.end, case).code, "CM_CHANGED")
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Active")

	def test_an_unconfirmed_signing_attempt_must_be_recovered_first(self):
		case = self.sent()
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "Indeterminate")
		refusal(formation.sign_contract, case, party="Supplier", expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["mary"])
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "")
		self.assertEqual(refusal(self.end, case).code, "CM_HOLD")
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Awaiting signatures")

	def test_an_expired_window_raises_one_follow_up_and_decides_nothing(self):
		case = self.sent()
		self.assertEqual(formation_end.sweep_signing_windows(), 0, "inside the window nothing is raised")
		frappe.flags.kt_cm_clock = "2027-07-15 09:00:00"
		raised = formation_end.sweep_signing_windows()
		again = formation_end.sweep_signing_windows()
		self.assertEqual((raised >= 1, again), (True, 0), "one follow-up, not one per sweep")
		self.assertIn(("RecordContractNotProceeding", self.p["charles"], "actionable"), self.mine(case))
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Awaiting signatures", "an expired window ends nothing by itself")
		board = router.board_for(case, self.p["charles"])
		self.assertEqual(board["p"], "Record that the contract did not proceed")
		self.assertEqual(board["dialogs"]["notproceeding"]["command"], "RecordContractNotProceeding")
		self.assertEqual(self.end(case, kind="The signing window ended", reason="No extension was granted.")["lifecycle"], "Did not proceed")
		self.assertEqual(self.mine(case), set())

	def test_the_link_is_offered_to_the_preparer_and_not_to_the_supplier(self):
		case = self.sent()
		self.assertIn("Record that the contract did not proceed", router.board_for(case, self.p["charles"], tab="Agreement")["actions"])
		self.assertNotIn("Record that the contract did not proceed", router.board_for(case, self.p["mary"], tab="Agreement")["actions"])
