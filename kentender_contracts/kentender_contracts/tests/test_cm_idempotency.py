# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.17, 5.18 and 7 (plan Phase 10; tracker CM8-1003; CM-AC-50): every command is safe to send twice.

A double-click, a lost response and a retry from a flaky connection all send a command again with the same key. The contract goes from receipt to a closed contract once, with a spy on the command journal that records
what each command was asked and what it answered; then every one of those commands is asked **again, exactly as it was**, and each must return what it returned the first time, never run its body, and leave the
contract and the native world exactly as they were. The same key with something else (another payload, another person, another command) is a conflict, never a quiet second run."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_contracts.services import closeout, errors, final_acceptance, records
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

NATIVE = ("Purchase Order", "Purchase Receipt", "Purchase Invoice", "Payment Entry", "Stock Ledger Entry", "GL Entry")


class TestEveryCommandIsSafeToSendTwice(ContractCase):
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

	def snapshot(self, case: str) -> dict[str, int]:
		mine = {d: frappe.db.count(d, {"contract_case": case}) for d in records.DOCTYPES if d != "Contract Case" and frappe.get_meta(d).has_field("contract_case")}
		mine.update({d: frappe.db.count(d) for d in NATIVE})
		mine["version"] = int(frappe.db.get_value("Contract Case", case, "record_version"))
		return mine

	def test_each_command_of_a_whole_contract_answers_the_same_when_asked_again_and_changes_nothing(self):
		asked: list[dict] = []
		real = records.command

		def spy(name, *, case, idempotency_key, actor, payload, body, authorise=None):
			result = real(name, case=case, idempotency_key=idempotency_key, actor=actor, payload=payload, body=body, authorise=authorise)
			asked.append({"name": name, "case": case, "key": idempotency_key, "actor": actor, "payload": payload, "authorise": authorise, "result": result})
			return result

		tag = self.id().rsplit(".", 1)[-1][:24]
		t = tw.Thread(self.p, tag=tag, item=world.ITEM_PLAIN, award_case=f"CM-TEST-{tag}-FIN")
		with mock.patch.object(records, "command", spy):
			case = t.active()
			t.appointed()
			frappe.db.set_value("Contract Case", case, "responsible_user", self.p["julia"])
			units = tw.fresh_serials(10)
			arrival = t.arrive(units, received_at="2027-07-12 10:00:00")["arrival"]
			t.inspect(arrival, units)
			frappe.flags.kt_cm_clock = "2027-07-20 10:00:00"
			t.accept(arrival)
			invoice = t.claim("IDEM-1", 10)["invoice"]
			t.certify_invoice(invoice)
			t.pay(invoice, "IDEM-BANK-1")
			frappe.flags.kt_cm_clock = "2028-07-28 08:30:00"
			final_acceptance.sign(case, expected_version=t.version(), idempotency_key=t.key("final"), actor=self.p["amina"])
			closeout.issue_completion_certificate(case, expected_version=t.version(), idempotency_key=t.key("completion"), actor=self.p["charles"])
			t.confirm_delivery()
			review = frappe.db.get_value("Contract Closeout", {"contract_case": case, "state": "Awaiting signature"}, "name")
			closeout.sign_closeout(case, closeout=review, expected_version=t.version(), idempotency_key=t.key("close"), actor=self.p["amina"])

		self.assertGreater(len(asked), 25, "the walk asked for most of the contract's commands")
		names = {a["name"] for a in asked}
		for expected in ("RequestContractSignatures", "SignContractVersion", "RecordContractArrival", "SignAcceptanceReport", "SignContractCertification", "RecordFinanceSettlement", "SignFinalContractAcceptance",
				"IssueCompletionCertificate", "ConfirmCertificateDelivery", "SignContractCloseout"):
			self.assertIn(expected, names, f"{expected} was not part of the walk")

		before = self.snapshot(case)

		def never_run() -> dict:
			raise AssertionError("a replayed command ran its body")

		for call in asked:
			again = real(call["name"], case=call["case"], idempotency_key=call["key"], actor=call["actor"], payload=call["payload"], body=never_run, authorise=call["authorise"])
			self.assertEqual(again, call["result"], f"{call['name']} answered differently the second time")
		self.assertEqual(self.snapshot(case), before, "asking again changed something")

		# the same key with something else is a conflict, never a quiet second run
		sample = next(a for a in asked if a["name"] == "SignContractCloseout")
		for change in ({"payload": {**sample["payload"], "extra": 1}}, {"name": "SignContractCertification"}):
			asked_with = {**sample, **change}
			with self.assertRaises(errors.ContractError) as caught:
				real(asked_with["name"], case=asked_with["case"], idempotency_key=asked_with["key"], actor=asked_with["actor"], payload=asked_with["payload"], body=never_run, authorise=asked_with["authorise"])
			self.assertEqual(caught.exception.code, "CM_CHANGED")
		self.assertEqual(self.snapshot(case), before)
