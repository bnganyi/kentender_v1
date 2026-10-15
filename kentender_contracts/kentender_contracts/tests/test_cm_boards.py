# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 6.3, 9.0, 10 (plan Phase 4; tracker CM8-414): the screens the thread draws, built by the server for each person at each step.

The test walks the ordinary thread as the people of the boards and, at each step, asks the router for that person's screen: which board it is, what the next step says, which action is the
primary one, what the viewer must not see. With `CM_CAPTURE_BOARDS=1` it also writes each board as a JSON fixture (`public/js/contracts/fixtures/`), which the component test draws and compares
with the design's board (the structural fidelity gate)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import frappe

from kentender_contracts.boards import listing, router
from kentender_contracts.services import delivery, errors, formation, payment, records, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

FIXTURES = Path(frappe.get_app_path("kentender_contracts")) / "public/js/contracts/fixtures"
CAPTURE = bool(os.environ.get("CM_CAPTURE_BOARDS"))
CONTROLS = "Contract Test Environment Controls"


class TestBoards(ContractCase):
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
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "")
		self.p = self.people
		self.seen: dict[str, dict] = {}

	def screen(self, who: str, expected: str, *, tab: str | None = None, subject: tuple[str, ...] = (), capture_as: str | None = None) -> dict:
		board = router.board_for(self.case, self.p[who], tab=tab, subject=subject)
		self.assertEqual(board["id"], expected, f"{who} on {tab or 'the default tab'}")
		self.seen[capture_as or expected] = board
		return board

	def tearDown(self):
		if CAPTURE:
			FIXTURES.mkdir(parents=True, exist_ok=True)
			for name, board in self.seen.items():
				(FIXTURES / f"{name.replace(' · ', '_')}.json").write_text(json.dumps(board, indent=1, sort_keys=True, default=str) + "\n")

	def primary(self, board: dict) -> str:
		return board.get("p", "")

	def test_the_screens_of_the_thread_for_the_people_who_walk_it(self):
		t = tw.Thread(self.p, tag="BOARDS")
		out = tw.receive(self.p, contract_id=t.contract_id)
		self.case = t.case = out["contract"]

		# the list: My work for the head of procurement, the supplier's own list, an empty My work and a search that finds nothing
		mine = listing.workspace(self.p["charles"], view="My work")["board"]
		self.assertEqual((mine["id"], mine["title"], [c for c in mine["cols"]], mine["rows"][0][0], mine["rows"][0][2]), ("D01", "Contracts", listing.COLS, "@" + t.contract_id, "!Preparing"))
		self.seen["D01"] = mine
		self.seen["D01-S"] = listing.workspace(self.p["mary"])["board"]
		self.assertEqual((self.seen["D01-S"]["title"], self.seen["D01-S"]["cols"], self.seen["D01-S"]["views"]), ("My contracts", listing.COLS_SUPPLIER, []))
		empty = listing.workspace(self.p["grace"], view="My work")["board"]
		self.assertEqual((empty["rows"], empty["empty"]), ([], "No contracts are available."))
		self.seen["D01-E"] = empty
		nothing = listing.workspace(self.p["charles"], view="All contracts", search="no such contract")["board"]
		self.assertEqual((nothing["rows"], nothing["empty"], nothing["emptyAct"]), ([], "No contracts match your search.", "Clear search"))
		self.seen["D01-F"] = nothing

		# preparation: the particulars still to complete, then the agreement ready to send
		blank = self.screen("charles", "D02", capture_as="D02-missing")
		self.assertEqual(self.primary(blank), "Save particulars")
		self.assertEqual(blank["next"]["k"], "turn")
		formation.save_particulars(self.case, expected_version=t.version(), idempotency_key=t.key("p"), actor=self.p["brian"], values=tw.package_particulars(self.p))
		ready = self.screen("charles", "D02")
		self.assertEqual((self.primary(ready), ready["st"], ready["tab"], ready["back"]), ("Send for signature", "Preparing", "Agreement", "Back to contracts"))
		self.assertEqual([r["t"] for r in ready["regions"]], ["Summary", "Agreement summary"])
		self.assertEqual(self.screen("mary", "D02-S", capture_as="D02-S-before").get("next"), None, "the supplier has nothing to do before the agreement is sent")
		view = self.screen("charles", "D02-V", tab="Agreement", subject=("1",))  # the route /<contract>/agreement/1
		self.assertEqual(router.board_for(self.case, self.p["charles"], tab="Agreement", subject=("agreement", "1"))["id"], "D02-V", "a leading tab name is tolerated")
		self.assertIn("Form No. 4 particulars", [r["t"] for r in view["regions"]])

		# signing
		formation.request_signatures(self.case, expected_version=t.version(), idempotency_key=t.key("send"), actor=self.p["charles"])
		mary = self.screen("mary", "D03")
		self.assertEqual((self.primary(mary), mary["st"], mary["next"]["k"]), ("Sign contract", "Awaiting signatures", "turn"))
		self.assertEqual(self.screen("charles", "D03-S")["next"]["k"], "wait")
		formation.sign_contract(self.case, party="Supplier", expected_version=t.version(), idempotency_key=t.key("s1"), actor=self.p["mary"])
		self.assertEqual(self.screen("mary", "D03-S", capture_as="D03-W")["next"]["k"], "wait")
		amina = self.screen("amina", "D03-A")
		self.assertEqual((self.primary(amina), amina["regions"][-1]["t"]), ("Sign contract", "Signatures"))
		formation.sign_contract(self.case, party="Entity", expected_version=t.version(), idempotency_key=t.key("s2"), actor=self.p["amina"])
		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Active")

		# appointment and declarations
		rec = self.screen("charles", "D23-R")
		self.assertEqual(self.primary(rec), "Recommend inspectors")
		members = [{"user": self.p["julia"], "capacity": "Chair", "role_label": "User department"}, {"user": self.p["peter"], "capacity": "Member", "certifier": True, "role_label": "Technical"},
			{"user": self.p["brian"], "capacity": "Member", "role_label": "Procurement"}]
		proposal = delivery.recommend_inspectors(self.case, expected_version=t.version(), idempotency_key=t.key("r"), actor=self.p["charles"], members=members)
		ao = self.screen("amina", "D23")
		self.assertEqual((self.primary(ao), sorted(ao["actions"]), sorted(ao["dialogs"])), ("Appoint inspectors", ["Appoint inspectors", "Return for correction"], ["appoint", "return"]))
		delivery.appoint_inspectors(self.case, appointment=proposal["appointment"], expected_version=t.version(), idempotency_key=t.key("a"), actor=self.p["amina"])
		peter = self.screen("peter", "D24")
		self.assertEqual((self.primary(peter), peter["regions"][1]["b"][0]["items"][0]["t"]), ("Save declaration", "rad"))
		self.assertEqual(self.screen("charles", "D23-P")["next"]["k"], "wait")
		for who in ("julia", "peter", "brian"):
			delivery.declare_interest(self.case, expected_version=t.version(), idempotency_key=t.key("d"), actor=self.p[who])

		# arrival, inspection, technical confirmation, acceptance
		receive = self.screen("grace", "D04", tab="Deliveries", subject=("record-delivery",))
		self.assertEqual((self.primary(receive), receive["dialogs"]["units"]["local"]), ("Record delivery", True))
		units = tw.fresh_serials(10)
		arrival = t.arrive(units)["arrival"]
		inspect = self.screen("peter", "D05")
		self.assertEqual((self.primary(inspect), inspect["tab"]), ("Record observations", "Deliveries"))
		t.inspect(arrival, units, bad=tuple(units[8:]))
		self.assertEqual(self.screen("peter", "D19")["regions"][0]["b"][0]["items"][2], ["Conforms", "8"])
		delivery.sign_technical_certificate(self.case, arrival=arrival, expected_version=t.version(), idempotency_key=t.key("c"), actor=self.p["peter"])
		chair = self.screen("julia", "D06")
		self.assertEqual(self.primary(chair), "Prepare report for signing")
		report = delivery.prepare_acceptance_report(self.case, arrivals=[arrival], expected_version=t.version(), idempotency_key=t.key("p"), actor=self.p["julia"])
		self.assertEqual(self.screen("brian", "D07")["regions"][3]["t"], "Signatures")
		for who in ("julia", "peter", "brian"):
			delivery.sign_acceptance_report(self.case, acceptance=report["acceptance"], expected_version=t.version(), idempotency_key=t.key("s"), actor=self.p[who])
		delivery.record_custody_return(self.case, expected_version=t.version(), idempotency_key=t.key("x"), actor=self.p["grace"], units=units[8:], evidence="Gate pass 1")

		# invoice, certification, Finance
		supplier = self.screen("david", "D09", tab="Invoices")
		self.assertEqual(self.primary(supplier), "Submit invoice")
		form = self.screen("david", "D18", tab="Invoices", subject=("submit-invoice",))
		self.assertEqual(self.primary(form), "Submit invoice")
		held = t.claim("AFYA-1", 9)
		self.assertEqual(self.screen("charles", "D08")["next"]["k"], "turn")
		self.assertEqual(self.screen("david", "D18-R", tab="Invoices")["next"]["k"], "wait")
		payment.request_invoice_correction(self.case, invoice=held["invoice"], expected_version=t.version(), idempotency_key=t.key("rc"), actor=self.p["charles"], reason="Claim the eight accepted units.")
		self.assertEqual(self.screen("david", "D18-C")["title"], "Correct invoice")
		corrected = payment.submit_invoice(self.case, expected_version=t.version(), idempotency_key=t.key("c"), actor=self.p["david"], claim_reference="AFYA-1-R1", invoice_date=frappe.utils.today(),
			lines=[{"line_id": "L1", "quantity": 8}], successor_of=held["invoice"])
		self.assertEqual(self.screen("charles", "D08-C")["p"], "Sign certification")
		t.certify_invoice(corrected["invoice"])
		self.assertEqual(self.screen("josphat", "D33")["p"], "Submit invoice for approval")
		native = frappe.db.get_value("Contract Invoice", corrected["invoice"], "native_invoice")
		payment.save_accounting_invoice(self.case, invoice=corrected["invoice"], expected_version=t.version(), idempotency_key=t.key("ai"), actor=self.p["josphat"], posting_date=frappe.utils.today(),
			payable_account=frappe.db.get_value("Company", world.COMPANY, "default_payable_account"), cost_centre=frappe.db.get_value("Company", world.COMPANY, "cost_center"),
			expense_account=frappe.db.get_value("Purchase Invoice Item", {"parent": native}, "expense_account"))
		payment.submit_accounting_invoice(self.case, invoice=corrected["invoice"], expected_version=t.version(), idempotency_key=t.key("as"), actor=self.p["josphat"])
		self.assertEqual(self.screen("beatrice", "D33-A")["p"], "Approve accounting invoice")
		payment.approve_accounting_invoice(self.case, invoice=corrected["invoice"], expected_version=t.version(), idempotency_key=t.key("aa"), actor=self.p["beatrice"])
		self.assertEqual(self.screen("josphat", "D09-F")["p"], "Submit payment for approval")
		draft = payment.save_finance_draft(self.case, invoice=corrected["invoice"], expected_version=t.version(), idempotency_key=t.key("d"), actor=self.p["josphat"], mode_of_payment=world.MODE, paid_from=world.BANK_ACCOUNT, reference_no="B-1")
		payment.submit_finance_for_approval(self.case, payment=draft["payment"], expected_version=t.version(), idempotency_key=t.key("sp"), actor=self.p["josphat"])
		self.assertEqual(self.screen("beatrice", "D17")["p"], "Approve payment")
		payment.approve_finance_record(self.case, payment=draft["payment"], expected_version=t.version(), idempotency_key=t.key("ap"), actor=self.p["beatrice"])
		self.assertEqual(self.screen("beatrice", "D17-S")["p"], "Confirm payment")
		payment.record_finance_settlement(self.case, payment=draft["payment"], expected_version=t.version(), idempotency_key=t.key("st"), actor=self.p["beatrice"], effective_date=frappe.utils.today(), evidence="Bank line 1")

		# replacement units, to completion
		units2 = tw.fresh_serials(2)
		arrival2 = t.arrive(units2, received_at="2027-07-16 09:00:00")["arrival"]
		t.inspect(arrival2, units2)
		t.accept(arrival2)
		inv2 = t.claim("AFYA-2", 2)
		t.certify_invoice(inv2["invoice"])
		t.pay(inv2["invoice"], "B-2")
		completion = self.screen("charles", "D22")
		self.assertEqual(self.primary(completion), "Sign and issue certificate")
		from kentender_contracts.services import closeout

		closeout.issue_completion_certificate(self.case, expected_version=t.version(), idempotency_key=t.key("ic"), actor=self.p["charles"])
		close = self.screen("amina", "D11")
		self.assertEqual(self.primary(close), "Sign close-out")
		closeout.sign_closeout(self.case, closeout=frappe.db.get_value("Contract Closeout", {"contract_case": self.case, "state": "Awaiting signature"}, "name"), expected_version=t.version(), idempotency_key=t.key("cl"), actor=self.p["amina"])
		self.assertEqual(self.screen("amina", "D10", tab="Obligations")["st"], "Closed")
		self.assertEqual(self.screen("daniel", "D10", tab="Obligations", capture_as="D40-T")["next"], None, "a technical reader has no personal work")
		self.assertEqual(self.screen("charles", "D41", tab="History")["tab"], "History")

	def test_a_stranger_gets_the_denial_and_the_supplier_never_sees_internal_work(self):
		t = tw.Thread(self.p, tag="DENY")
		self.case = t.active()
		self.assertEqual(refusal_code(lambda: router.board_for(self.case, self.p["stranger"])), "CM_AUTHORITY")
		self.assertEqual(refusal_code(lambda: router.board_for("CM-NOPE", self.p["charles"])), "CM_AUTHORITY")
		board = router.board_for(self.case, self.p["mary"], tab="Obligations")
		text = json.dumps(board)
		for internal in ("Finance preparation", "Head of Procurement", "Contract inspection", "deliberation"):
			self.assertNotIn(internal, text, "a supplier never sees internal work")
		self.assertEqual(board["audiences"], ["supplier"])


	def test_a_hold_makes_the_step_blocked_with_its_reason_and_its_holder_and_never_a_button_that_will_be_refused(self):
		from kentender_contracts.services import holds, work

		t = tw.Thread(self.p, tag="HELD")
		out = tw.receive(self.p, contract_id=t.contract_id)
		self.case = t.case = out["contract"]
		formation.save_particulars(self.case, expected_version=t.version(), idempotency_key=t.key("p"), actor=self.p["brian"], values=tw.package_particulars(self.p))
		before = self.screen("charles", "D02")
		self.assertEqual((before["next"]["k"], before["p"]), ("turn", "Send for signature"))
		held = holds.Hold(key="restriction:R-1", kind="Restriction", reason="An award restriction requires review.", blocks=frozenset({"new_signing_attempt"}), owner="Head of procurement function",
			clearing="The restriction is resolved by its owner")
		holds.PROVIDERS["test-restriction"] = lambda case: [held] if case == self.case else []
		self.addCleanup(holds.PROVIDERS.pop, "test-restriction", None)
		live = [x for x in work.live(self.case) if x["holder"] == self.p["charles"]]
		self.assertEqual((live[0]["state"], live[0]["blocker"]["message"], live[0]["blocker"]["responsibility"]), ("blocked", "An award restriction requires review.", "Head of procurement function"))
		after = router.board_for(self.case, self.p["charles"])
		self.assertEqual((after["next"]["k"], after["next"]["h"].startswith("Review the contract")), ("blk", True))
		self.assertEqual(after["next"]["fixes"], ["View issue"])
		self.assertEqual(after["actions"]["View issue"], {"do": "tab", "tab": "Obligations"})
		obligations = router.board_for(self.case, self.p["charles"], tab="Obligations")
		self.assertIn("An award restriction requires review.", json.dumps(obligations), "the hold is listed with the remaining work")


def refusal_code(fn):
	try:
		fn()
	except errors.ContractError as exc:
		return exc.code
	return ""
