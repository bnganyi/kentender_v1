# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.7, 5.20, 7 and boards D13, D13-S, D13-C (plan Phase 8; tracker CM8-801): issues and the correspondence on them.

Units that did not meet open a delivery issue for the contract's owner to send to the supplier. A message is delivered only with evidence; a failed dispatch keeps the same message and retries it, sending
nothing twice. The supplier replies and may propose a remedy but never closes the issue; the owner closes it with a disposition, and replacement units that are accepted close it with the fact."""

from __future__ import annotations

import frappe

from kentender_contracts.services import errors, formation, issues, records, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class IssueCase(ContractCase):
	native = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: (setattr(frappe.flags, "kt_cm_dispatch_fault", None), self.env.__exit__(None, None, None)))
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24])
		self.case = self.t.active()
		self.t.appointed()
		frappe.db.set_value("Contract Case", self.case, "responsible_user", self.p["julia"])
		self.units = tw.fresh_serials(10)
		self.arrival = self.t.arrive(self.units)["arrival"]
		self.t.inspect(self.arrival, self.units, bad=tuple(self.units[8:]))
		self.t.accept(self.arrival)  # eight accepted, two do not meet

	def issue(self):
		return issues.get(self.case, 1)

	def send(self, text="Two laptops did not start. Please arrange replacement.", **kw):
		return issues.send_correspondence(self.case, issue=self.issue().name, text=text, expected_version=self.t.version(), idempotency_key=self.t.key("send"), actor=self.p["julia"], **kw)

	def reply(self, text="We will deliver two replacement laptops.", remedy="", who="david"):
		return issues.reply_correspondence(self.case, issue=self.issue().name, text=text, expected_version=self.t.version(), idempotency_key=self.t.key("reply"), actor=self.p[who], proposed_remedy=remedy)

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}


class TestOpening(IssueCase):
	def test_units_that_did_not_meet_open_a_delivery_issue_for_the_owner_to_send(self):
		row = self.issue()
		facts = records.loads(row.facts_json)
		self.assertEqual((row.kind, row.state, row.requested_remedy, row.owner_user), ("Delivery issue", "Open", "Replacement", self.p["julia"]))
		self.assertEqual((sorted(facts["units"]), facts["result"]), (sorted(self.units[8:]), "Does not meet"))
		self.assertIn("did not meet the requirements", records.loads(row.links_json)["draft"])
		self.assertIn(("SendContractCorrespondence", "Send the inspection findings to the supplier.", "actionable"), self.tasks("julia"))

	def test_the_supplier_or_the_owner_may_report_a_matter_and_a_stranger_may_not(self):
		out = issues.record_issue(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("r1"), actor=self.p["david"], kind="Other", title="Delivery note missing", description="The note for delivery 1 was not signed.")
		self.assertEqual(frappe.db.get_value("Contract Issue", out["issue"], ["kind", "state"], as_dict=True), {"kind": "Other", "state": "Open"})
		issues.record_issue(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("r2"), actor=self.p["julia"], kind="Other", title="Training room", description="The room is not ready.")
		self.assertEqual(refusal(issues.record_issue, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("r3"), actor=self.p["stranger"], kind="Other", title="x", description="y").code, "CM_AUTHORITY")
		self.assertIn("title", refusal(issues.record_issue, self.case, expected_version=self.t.version(), idempotency_key=self.t.key("r4"), actor=self.p["julia"], kind="Other", title=" ", description="y").fields)


class TestDispatch(IssueCase):
	def test_a_sent_message_is_delivered_with_evidence_and_the_supplier_is_asked_to_reply(self):
		self.send()
		row = self.issue()
		message = issues.thread(row)[0]
		self.assertEqual((row.state, message["dispatch"]["state"], message["dispatch"]["channel"]), ("Awaiting reply", "Delivered", "Supplier portal"))
		self.assertTrue(message["dispatch"]["evidence"].startswith("DLV-"))
		self.assertIn(("ReplyContractCorrespondence", "Reply to the replacement request.", "actionable"), self.tasks("david"))
		self.assertIn("ReplyContractCorrespondence", {c for c, _t, s in self.tasks("julia") if s == "waiting"})
		self.assertFalse([1 for c, _t, _s in self.tasks("julia") if c == "SendContractCorrespondence"])

	def test_a_failed_dispatch_keeps_the_same_message_unsent_and_never_claims_the_supplier_has_it(self):
		frappe.flags.kt_cm_dispatch_fault = "fail"
		self.send()
		row = self.issue()
		message = issues.thread(row)[0]
		self.assertEqual(message["dispatch"]["state"], "Unsent")
		self.assertFalse([1 for c, _t, _s in self.tasks("david") if c == "ReplyContractCorrespondence"], "the supplier is asked for nothing they have not received")
		self.assertIn(("RestoreContractOperation", "Restore the message dispatch", "actionable"), self.tasks("daniel"))
		self.assertTrue(frappe.db.exists("Contract Event", {"contract_case": self.case, "event_type": "Message not delivered"}))
		frappe.flags.kt_cm_dispatch_fault = None
		formation.restore_operations(self.case, actor=self.p["daniel"])
		again = issues.thread(self.issue())
		self.assertEqual((len(again), again[0]["dispatch"]["state"], again[0]["text"]), (1, "Delivered", message["text"]), "the same message, sent once")
		self.assertEqual(frappe.db.count("Contract Event", {"contract_case": self.case, "event_type": "Notice delivered"}), 1)
		self.assertIn(("ReplyContractCorrespondence", "Reply to the replacement request.", "actionable"), self.tasks("david"))
		formation.restore_operations(self.case, actor=self.p["daniel"])
		self.assertEqual(frappe.db.count("Contract Event", {"contract_case": self.case, "event_type": "Notice delivered"}), 1, "a second recovery sends nothing")

	def test_the_same_send_replayed_is_one_message(self):
		key = self.t.key("once")
		args = dict(issue=self.issue().name, text="Two laptops did not start.", expected_version=self.t.version(), idempotency_key=key, actor=self.p["julia"])
		issues.send_correspondence(self.case, **args)
		issues.send_correspondence(self.case, **args)  # a retried request with the same key
		self.assertEqual(len(issues.thread(self.issue())), 1)

	def test_only_the_owner_side_sends_and_a_message_needs_text(self):
		self.assertEqual(refusal(issues.send_correspondence, self.case, issue=self.issue().name, text="Hello", expected_version=self.t.version(), idempotency_key=self.t.key("a"), actor=self.p["david"]).code, "CM_AUTHORITY")
		self.assertIn("text", refusal(issues.send_correspondence, self.case, issue=self.issue().name, text=" ", expected_version=self.t.version(), idempotency_key=self.t.key("b"), actor=self.p["julia"]).fields)


class TestReplyAndClose(IssueCase):
	def test_the_supplier_replies_and_proposes_a_remedy_but_cannot_close_or_accept_it(self):
		self.send()
		self.reply(remedy="Deliver two replacement laptops on 27 July")
		row = self.issue()
		self.assertEqual((row.state, issues.thread(row)[1]["proposed_remedy"]), ("Remedy proposed", "Deliver two replacement laptops on 27 July"))
		self.assertIn(("ResolveContractIssue", "Review the supplier's reply.", "actionable"), self.tasks("julia"))
		self.assertEqual(refusal(issues.resolve_issue, self.case, issue=row.name, disposition="Agreed", expected_version=self.t.version(), idempotency_key=self.t.key("c"), actor=self.p["david"]).code, "CM_AUTHORITY")
		self.assertEqual(refusal(self.reply, who="julia").code, "CM_SEGREGATION", "the owner does not write the supplier's reply")

	def test_the_owner_closes_the_thread_with_a_disposition_and_nothing_is_left_waiting(self):
		self.send()
		self.reply()
		issues.resolve_issue(self.case, issue=self.issue().name, disposition="Replacement agreed for 27 July.", expected_version=self.t.version(), idempotency_key=self.t.key("res"), actor=self.p["julia"])
		row = self.issue()
		self.assertEqual((row.state, row.resolution, row.resolved_by), ("Closed", "Replacement agreed for 27 July.", self.p["julia"]))
		self.assertFalse([t for t in self.tasks("julia") | self.tasks("david") if t[0] in ("SendContractCorrespondence", "ReplyContractCorrespondence", "ResolveContractIssue")])
		self.assertEqual(refusal(self.send).code, "CM_CHANGED", "a closed thread takes no more messages; later evidence starts a linked issue")

	def test_a_warranty_claim_is_not_closed_by_a_note(self):
		out = issues.record_issue(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("w"), actor=self.p["julia"], kind="Warranty claim", title="Battery does not charge", description="Unit 4.")
		exc = refusal(issues.resolve_issue, self.case, issue=out["issue"], disposition="Fixed", expected_version=self.t.version(), idempotency_key=self.t.key("wr"), actor=self.p["julia"])
		self.assertEqual(exc.code, "CM_RECONCILE")

	def test_accepted_replacement_units_close_the_issue_that_asked_for_them_with_the_fact(self):
		self.send()
		self.reply()
		replacements = tw.fresh_serials(2)
		from kentender_contracts.services import delivery

		out = delivery.record_arrival(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("rep"), actor=self.p["grace"], received_at="2027-07-27 10:00:00", destination="Afya House store",
			items=[{"line_id": "L1", "quantity": 2, "units": replacements, "replaces": self.units[8:]}])
		self.t.inspect(out["arrival"], replacements)
		self.t.accept(out["arrival"])
		row = self.issue()
		self.assertEqual(row.state, "Closed")
		self.assertIn("Replacement units", row.resolution)
		self.assertTrue(all(u in row.resolution for u in replacements))


class TestCrashAndPartial(IssueCase):
	def test_a_delivery_made_before_the_crash_is_found_by_its_identity_and_not_made_again(self):
		from kentender_contracts.services import dispatch, intents

		self.send()
		row = self.issue()
		identity = intents.identity(self.case, "issue 1 message 1", 1, "Notice dispatch", "send")
		first = issues.thread(row)[0]["dispatch"]["evidence"]
		self.assertEqual(dispatch.find(identity), first, "the delivery is found by the operation that made it")
		# the crash: the message had gone out but the issue never recorded it
		messages = issues.thread(row)
		messages[0]["dispatch"] = {"state": "Unsent", "channel": "Supplier portal", "evidence": "", "at": ""}
		frappe.db.set_value("Contract Issue", row.name, "messages_json", records.dumps(messages))
		frappe.db.set_value("Contract Operation Intent", {"operation_identity": identity}, {"state": "Attempting", "result_reference": ""})
		frappe.db.set_value("Contract Operation Intent", {"operation_identity": identity}, "modified", "2000-01-01 00:00:00", update_modified=False)
		frappe.db.delete("Contract Transaction Link", {"operation_identity": identity})
		issues.dispatch_message(self.case, row.name, 1, self.p["daniel"])
		self.assertEqual(issues.thread(self.issue())[0]["dispatch"]["evidence"], first)
		self.assertEqual(frappe.db.count("Contract Event", {"contract_case": self.case, "event_type": "Notice delivered"}), 1, "found, not delivered a second time")

	def test_one_of_two_replacement_units_does_not_close_the_issue(self):
		from kentender_contracts.services import delivery

		self.send()
		one = tw.fresh_serials(1)
		out = delivery.record_arrival(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("rep"), actor=self.p["grace"], received_at="2027-07-27 10:00:00", destination="Afya House store",
			items=[{"line_id": "L1", "quantity": 1, "units": one, "replaces": [self.units[8]]}])
		self.t.inspect(out["arrival"], one)
		self.t.accept(out["arrival"])
		self.assertEqual(self.issue().state, "Awaiting reply", "the other rejected unit is still to be replaced")
