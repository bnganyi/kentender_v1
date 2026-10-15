# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.10, 6.3, 10.1A and 10.3 (plan Phase 10; tracker CM8-1002; CM-AC-19 and CM-AC-62): no screen leaves its reader at a dead end.

Two halves. The **static half** reads the code: every command a task can ask a person to take is a command the API can run, and has a tab to land on, so a task never names an action that cannot be taken. The **walk** takes
one contract from receipt to a reopened close-out and, at each stage, opens it as every person of the test world on the first screen and on the Obligations tab: a reader who may read it gets a screen (never an error), a
"your turn" has a primary action that does something, a blocked step has a fix that goes somewhere and a named holder, a wait names who, and every action a screen draws does something. A reader who may not read it gets
the one shared denial and nothing else."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import frappe

from kentender_contracts.boards import chrome, router
from kentender_contracts.services import audience, closeout, closure_correction, errors, final_acceptance, formation, work
from kentender_contracts.tests import dead_end
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

APP = Path(frappe.get_app_path("kentender_contracts"))

#: a task whose command is not a button of its own: it is taken by another screen, or it is a scheduled reminder that opens the form its owner already has.
#: command -> why that is not a dead end
NOT_A_COMMAND_OF_ITS_OWN = {
	"RecordWarrantyClaim": "a scheduled reminder for the day the warranty ends; the owner records a claim from the Obligations tab's own entry",
	"RecordContractReportSubmission": "a scheduled reminder; the submission is recorded from the report's own screen (D15)",
}


def _assigned_commands() -> dict[str, set[str]]:
	found: dict[str, set[str]] = {}
	for path in sorted((APP / "services").glob("*.py")):
		for node in ast.walk(ast.parse(path.read_text())):
			if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("assign", "incident") and isinstance(node.func.value, ast.Name) and node.func.value.id == "work"
					and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str)):
				found.setdefault(node.args[1].value, set()).add(path.name)
	return found


class TestEveryTaskNamesSomethingTheServerCanRun(ContractCase):
	def test_every_command_a_task_asks_for_is_a_command_the_api_can_run(self):
		from kentender_contracts.api import commands

		missing = sorted(c for c in _assigned_commands() if c not in commands.COMMANDS and c not in NOT_A_COMMAND_OF_ITS_OWN)
		self.assertEqual(missing, [], "a task asks a person for an action the server cannot run")

	def test_every_command_a_task_asks_for_lands_on_a_tab_that_exists(self):
		unknown = sorted(c for c in _assigned_commands() if chrome.tab_of(c) not in chrome.TABS)
		self.assertEqual(unknown, [])

	def test_every_explained_exception_is_still_an_exception(self):
		stale = sorted(c for c in NOT_A_COMMAND_OF_ITS_OWN if c not in _assigned_commands())
		self.assertEqual(stale, [], "remove an exception once the task it excuses is gone")

	def test_every_command_with_a_screen_of_its_own_is_routed_to_it(self):
		"""A task for the head, the owner or a signer opens on the screen that takes it: the router names the command, directly or through the sets it dispatches on."""
		source = (APP / "boards/router.py").read_text()
		routed = set(re.findall(r'"([A-Z][A-Za-z]+)"', source))
		from kentender_contracts.services import change

		routed |= set(change.COMMANDS)
		unrouted = sorted(c for c in _assigned_commands() if c not in routed and c not in NOT_A_COMMAND_OF_ITS_OWN)
		# commands the design draws no screen for are taken from the Obligations tab's primary action (see `obligations.obligations`) or by the summary tab's own button
		by_summary = {"PrepareContractCloseout", "ReconcileInvoiceLiability"}
		self.assertEqual(sorted(set(unrouted) - by_summary), [], "a task whose holder lands on a screen with no way to take it")


class SweepCase(ContractCase):
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
		self.visited = 0
		self.stranded: list[str] = []

	def sweep(self, stage: str) -> None:
		"""Every person of the world opens the contract on its first screen and on the Obligations tab."""
		for persona, user in self.p.items():
			readable = bool(audience.readable(user, self.case))
			for tab in (None, "Obligations"):
				kw = {"tab": tab} if tab else {}
				try:
					board = router.board_for(self.case, user, **kw)
				except errors.ContractError as exc:
					self.assertFalse(readable, f"{stage}: {persona} may read the contract and was refused ({exc.code})")
					self.assertEqual(exc.code, "CM_AUTHORITY", f"{stage}: {persona}")
					continue
				self.assertTrue(readable, f"{stage}: {persona} may not read the contract and was shown a screen")
				self.stranded += [f"{stage}: {persona} ({tab or 'first screen'}): {why}" for why in dead_end.problems(board)]
				self.visited += 1



class TestTheLiabilityGap(SweepCase):
	def test_finance_asked_for_a_native_credit_is_not_left_without_a_way_to_act(self):
		"""A posted invoice is corrected down: Finance is asked to bring the liability to the supported amount with a native credit, and the head's certification waits for it."""
		from frappe.utils import today

		from kentender_contracts.services import payment

		t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24], item=world.ITEM_PLAIN)
		self.case = t.active()
		t.appointed()
		units = tw.fresh_serials(10)
		arrival = t.arrive(units)["arrival"]
		t.inspect(arrival, units, bad=tuple(units[8:]))
		t.accept(arrival)
		first = payment.submit_invoice(self.case, expected_version=t.version(), idempotency_key=t.key("claim"), actor=self.p["david"], claim_reference="DE-LIAB-1", invoice_date=today(), lines=[{"line_id": "L1", "quantity": 10}])
		t.post_accounting(first["invoice"])
		payment.request_invoice_correction(self.case, invoice=first["invoice"], expected_version=t.version(), idempotency_key=t.key("ask"), actor=self.p["charles"], reason="Please correct the invoice to match the eight accepted laptops.")
		payment.submit_invoice(self.case, expected_version=t.version(), idempotency_key=t.key("claim2"), actor=self.p["david"], claim_reference="DE-LIAB-1-C", invoice_date=today(), lines=[{"line_id": "L1", "quantity": 8}],
			successor_of=first["invoice"], reason="Corrected to the eight accepted laptops.")
		self.assertIn("ReconcileInvoiceLiability", {x["command"] for x in work.live(self.case) if x["holder"] == self.p["josphat"]}, "Finance is asked for the credit")
		self.sweep("a liability waits for its credit")
		self.assertEqual(self.stranded, [], "readers left on a screen with no way forward")


class TestTheWalk(SweepCase):
	def test_one_contract_from_receipt_to_a_reopened_close_out_strands_nobody(self):
		tag = self.id().rsplit(".", 1)[-1][:24]
		t = tw.Thread(self.p, tag=tag, item=world.ITEM_PLAIN, award_case=f"CM-TEST-{tag}-FIN")
		out = tw.receive(self.p, contract_id=t.contract_id, award_case=t.award_case)
		self.case = t.case = out["contract"]
		self.sweep("received")
		formation.save_particulars(self.case, expected_version=t.version(), idempotency_key=t.key("particulars"), actor=self.p["brian"], values=tw.package_particulars(self.p, False, t.item))
		self.sweep("particulars saved")
		formation.request_signatures(self.case, expected_version=t.version(), idempotency_key=t.key("send"), actor=self.p["charles"])
		self.sweep("sent for signature")
		formation.sign_contract(self.case, party="Supplier", expected_version=t.version(), idempotency_key=t.key("sign-s"), actor=self.p["mary"])
		self.sweep("signed by the supplier")
		formation.sign_contract(self.case, party="Entity", expected_version=t.version(), idempotency_key=t.key("sign-e"), actor=self.p["amina"])
		self.sweep("in force")
		t.appointed()
		frappe.db.set_value("Contract Case", self.case, "responsible_user", self.p["julia"])
		self.sweep("inspectors appointed")
		units = tw.fresh_serials(10)
		arrival = t.arrive(units, received_at="2027-07-12 10:00:00")["arrival"]
		self.sweep("goods arrived")
		t.inspect(arrival, units, bad=tuple(units[8:]))
		self.sweep("inspected, two units do not conform")
		frappe.flags.kt_cm_clock = "2027-07-20 10:00:00"
		t.accept(arrival)
		self.sweep("accepted, two rejected")
		first_claim = t.claim("DE-1", 8)["invoice"]
		self.sweep("a claim for the eight accepted")
		t.certify_invoice(first_claim)
		t.pay(first_claim, "DE-BANK-1")
		self.sweep("the eight paid")
		from kentender_contracts.services import delivery

		delivery.record_custody_return(self.case, expected_version=t.version(), idempotency_key=t.key("collect"), actor=self.p["grace"], units=units[8:], evidence="Supplier gate pass GP-77")
		self.sweep("the rejected units collected")
		replacement = tw.fresh_serials(2)

		second = delivery.record_arrival(self.case, expected_version=t.version(), idempotency_key=t.key("arrive2"), actor=self.p["grace"], received_at="2027-07-22 10:00:00", destination="Afya House store",
			items=[{"line_id": "L1", "quantity": 2, "units": replacement, "replaces": units[8:]}])["arrival"]
		t.inspect(second, replacement)
		frappe.flags.kt_cm_clock = "2027-07-23 10:00:00"
		t.accept(second)
		self.sweep("everything accepted")
		second_claim = t.claim("DE-2", 2)["invoice"]
		self.sweep("a claim for the two replacements")
		t.certify_invoice(second_claim)
		self.sweep("the claim certified")
		t.pay(second_claim, "DE-BANK-2")
		self.sweep("paid")
		frappe.flags.kt_cm_clock = "2028-07-28 08:30:00"
		self.sweep("the final acceptance is the Accounting Officer's")
		final_acceptance.sign(self.case, expected_version=t.version(), idempotency_key=t.key("final"), actor=self.p["amina"])
		self.sweep("final acceptance recorded")
		closeout.issue_completion_certificate(self.case, expected_version=t.version(), idempotency_key=t.key("completion"), actor=self.p["charles"])
		self.sweep("the certificate signed, its delivery not yet confirmed")
		t.confirm_delivery()
		self.sweep("the review is the Accounting Officer's")
		review = frappe.db.get_value("Contract Closeout", {"contract_case": self.case, "state": "Awaiting signature"}, "name")
		closeout.sign_closeout(self.case, closeout=review, expected_version=t.version(), idempotency_key=t.key("close"), actor=self.p["amina"])
		self.sweep("closed")
		closure_correction.prepare(self.case, fact="Certificate delivery", reason="Delivery was recorded without proof.", evidence_files=[{"label": "Incident", "file": "x"}], submit=True, expected_version=t.version(),
			idempotency_key=t.key("corr"), actor=self.p["charles"])
		self.sweep("a correction is asked for")
		closure_correction.decide(self.case, correction=1, decision="Reopen", reason="Evidence was not established.", expected_version=t.version(), idempotency_key=t.key("reopen"), actor=self.p["amina"])
		self.sweep("reopened")
		self.assertEqual(self.stranded, [], "readers left on a screen with no way forward")
		self.assertGreater(self.visited, 300, "the walk looked at every person at every stage")
		self.assertTrue(work.live(self.case), "a reopened contract has work for someone")
