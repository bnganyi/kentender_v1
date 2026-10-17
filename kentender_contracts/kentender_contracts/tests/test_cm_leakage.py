# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 6.2 (plan Phase 10; tracker CM8-1001; CM-AC-43 and CM-AC-48): what each reader of a contract is never shown, and what a read-only reader can never do.

The contract carries a few facts that belong to some readers only: the reviewers' recommendation on a requested change (internal deliberation), the funding allocation (reservation, source allocation, budget line),
and the bank account a payment was made from (Finance's). Each is a sentinel string: the test opens the contract as every kind of reader, on its first screen and on all five tabs, and the text of what the server sent
must not contain a sentinel its reader may not see. A reader who may not read the contract is refused with the one shared denial, and the technical and audit readers, who read without commands, are offered no
business action on any screen and are refused every business command."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D  # noqa: F401
import json

import frappe

from kentender_contracts.api import commands
from kentender_contracts.boards import chrome, router
from kentender_contracts.services import audience, change, errors, payment
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

RECOMMENDATION = "LEAK-RECO-9f1c Approve only if the supplier waives interest."
FUNDING = ("RSV-DEMO-1", "PSA-DEMO-1", "BL-DEMO-1")
#: who must never see the sentinels. The supplier and the receiver see none of the internal deliberation, the funding allocation or Finance's accounts (section 6.2); an inspector who is not a reviewer reads the contract and
#: its deliveries but not the reviewers' deliberation, the funding allocation or the accounts.
NEVER_SEEN_BY = ("mary", "david", "grace", "julia")
#: the readers who may read without a business command (section 6.2: "No business mutations")
READ_ONLY = ("daniel", "naomi")


class LeakageCase(ContractCase):
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
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24], item=world.ITEM_PLAIN)
		self.case = self.t.active()
		self.t.appointed()
		frappe.db.set_value("Contract Case", self.case, "responsible_user", self.p["carol"])
		units = tw.fresh_serials(10)
		arrival = self.t.arrive(units, received_at=D("2027-07-12 10:00:00"))["arrival"]
		self.t.inspect(arrival, units)
		self.t.accept(arrival)
		invoice = self.t.claim("LK-1", 10)["invoice"]  # a claim, certified; Finance has saved the accounting invoice with its accounts and not yet posted it
		self.t.certify_invoice(invoice)
		native = frappe.db.get_value("Contract Invoice", invoice, "native_invoice")
		payable = frappe.db.get_value("Company", world.COMPANY, "default_payable_account")
		payment.save_accounting_invoice(self.case, invoice=invoice, expected_version=self.t.version(), idempotency_key=self.t.key("acct"), actor=self.p["josphat"], posting_date=frappe.utils.today(), payable_account=payable,
			cost_centre=frappe.db.get_value("Company", world.COMPANY, "cost_center"), expense_account=frappe.db.get_value("Purchase Invoice Item", {"parent": native}, "expense_account"))
		self.payable = payable  # Finance's account: drawn only while Finance prepares the accounting invoice
		change.request_change(self.case, kind="Extension", request={"proposed_date": D("2027-07-27")}, reason="Supplier reports a shipment delay.", evidence=[{"label": "Supplier request", "file": "/private/files/r.pdf"}],
			expected_version=self.t.version(), idempotency_key=self.t.key("ask"), actor=self.p["david"])
		roster = dict(zip(change.REVIEW_KINDS["Extension"], (self.p["peter"], self.p["faith"], self.p["brian"]), strict=True))
		change.appoint_reviewers(self.case, change=1, reference="AO/VAR/2027/001", reviewers=roster, expected_version=self.t.version(), idempotency_key=self.t.key("appoint"), actor=self.p["charles"])
		change.record_review(self.case, change=1, kind="Technical review", recommendation=RECOMMENDATION, declaration=change.NO_CONFLICT, expected_version=self.t.version(), idempotency_key=self.t.key("rec"), actor=self.p["peter"])

	def everything_sent_to(self, persona: str) -> str:
		"""All the text the server sends this reader: the first screen and every tab."""
		out = []
		for tab in (None, *chrome.TABS):
			kw = {"tab": tab} if tab else {}
			try:
				out.append(json.dumps(router.board_for(self.case, self.p[persona], **kw), default=str))
			except errors.ContractError:
				out.append("")
		return "\n".join(out)


class TestWhatAReaderIsNeverShown(LeakageCase):
	def test_the_readers_who_may_not_see_a_sentinel_never_receive_it_on_any_tab(self):
		for persona in NEVER_SEEN_BY:
			text = self.everything_sent_to(persona)
			self.assertTrue(text.strip(), f"{persona} reads the contract")
			for sentinel in (RECOMMENDATION, *FUNDING, self.payable):
				self.assertFalse(sentinel in text, f"{persona} was sent {sentinel!r}")

	def test_the_sentinels_are_there_for_the_readers_who_may_see_them(self):
		"""Without this the test above would pass for a world that simply did not hold the facts: the reviewer reads back their own recommendation, and Finance sees the account it paid from."""
		self.assertTrue(RECOMMENDATION in self.everything_sent_to("peter"), "the reviewer reads back their own recommendation")
		self.assertTrue(self.payable in self.everything_sent_to("josphat"), "Finance sees the account it chose")

	def test_every_reader_finds_the_contract_in_their_list_without_a_task_and_a_stranger_never_does(self):
		"""Reading is not a task: each reader's list, filtered before it is counted, holds the contract whether or not they have anything to do on it (CM-AC-48)."""
		from kentender_contracts.boards import listing

		contract_id = frappe.db.get_value("Contract Case", self.case, "contract_id")
		for persona in ("charles", "amina", "brian", "carol", "julia", "peter", "faith", "grace", "josphat", "beatrice", "naomi", "daniel", "mary", "david"):
			found = listing.workspace(self.p[persona], view="All contracts", search=contract_id)
			self.assertEqual(found.get("screen"), "workspace", f"{persona} opens the workspace")
			self.assertEqual([r["case"] for r in found["rows"]], [self.case], f"{persona} finds the contract")
			self.assertEqual(found["total"], 1, f"{persona}: the count is of what they may read")
		stranger = listing.workspace(self.p["stranger"], view="All contracts", search=contract_id)
		self.assertEqual(stranger.get("screen"), "workspace-forbidden")

	def test_a_person_who_is_not_a_reader_gets_the_shared_denial_and_nothing_else(self):
		with self.assertRaises(errors.ContractError) as caught:
			router.board_for(self.case, self.p["stranger"])
		self.assertEqual((caught.exception.code, caught.exception.detail.get("denied")), ("CM_AUTHORITY", True))
		self.assertNotIn(self.case, str(caught.exception.detail.get("reason", "")))

	def test_the_reviewer_reads_only_while_the_change_is_open(self):
		self.assertTrue(audience.readable(self.p["faith"], self.case), "named to review: reads")
		frappe.db.set_value("Contract Change", change.get(self.case, 1).name, "state", "Declined")
		self.assertEqual(audience.readable(self.p["faith"], self.case), [], "the access ends with the change")


class TestReadWithoutMutation(LeakageCase):
	def test_the_technical_and_audit_readers_are_offered_no_business_action_on_any_screen(self):
		for persona in READ_ONLY:
			for tab in (None, *chrome.TABS):
				kw = {"tab": tab} if tab else {}
				board = router.board_for(self.case, self.p[persona], **kw)
				doing = sorted({a["command"] for a in board["actions"].values() if a.get("do") == "command"} - {"RestoreContractOperation"})
				self.assertEqual(doing, [], f"{persona} on {tab or 'the first screen'} is offered a business action")
				self.assertEqual(board["p"] if persona == "naomi" else "", "", f"{persona} has no primary action")
				for dialog in board.get("dialogs", {}).values():
					self.assertNotIn(dialog.get("command"), {c for c in commands.COMMANDS if c != "RestoreContractOperation"}, f"{persona} is offered a dialog that runs a command")

	def test_the_read_only_readers_are_refused_every_business_command_without_a_trace(self):
		class Anything(dict):
			"""Arguments any command may ask for, so the refusal comes from the service's own authority check and not from a missing argument."""

			def __missing__(self, key):
				return "1"

		before = self.counts()
		for persona in READ_ONLY:
			user = self.p[persona]
			for name, handler in commands.COMMANDS.items():
				if name == "RestoreContractOperation":  # technical recovery is the technical reader's own, separately scoped
					continue
				try:
					handler(self.case, Anything(), {}, self.t.version(), f"{persona}-{name}", user)
				except (errors.ContractError, errors.InputError, frappe.DoesNotExistError, frappe.PermissionError):
					continue
				except (KeyError, TypeError, ValueError):
					continue  # the command could not even read its arguments: nothing was done
				self.fail(f"{persona} was allowed to run {name}")
		self.assertEqual(self.counts(), before, "a refused command leaves no record behind")

	def counts(self) -> dict[str, int]:
		from kentender_contracts.services import records

		return {doctype: frappe.db.count(doctype, {"contract_case": self.case}) for doctype in records.DOCTYPES if doctype != "Contract Case" and frappe.get_meta(doctype).has_field("contract_case")
			and doctype not in ("Contract Command Journal",)}
