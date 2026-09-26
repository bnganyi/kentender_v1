# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §5.6 / §5.7 / §7.4 on a published Tender: addenda
(draft, stale prior value, materiality, deadline rule, return as a copied
Draft, issue with a frozen successor Published Bid Definition, channel
confirmation → Issued with the successor and deadline effective together),
the material-proposal cancellation review and discard, supplier
clarifications (candidate registration, producer identity, dedup, the
clarification deadline, direct vs anonymised broadcast, addendum-required,
failed delivery and retry), recommendation, cancellation (AO only, ground +
reason, immediate finality, obligations, notices, the attested evidence
defect), and the submission close with its Bid Submission handoff.
TPR09-AC-056..068, 097..100, TPR10-AC-001..011, TPR12-AC-012."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tenders.services import addenda, bid_definition, cancellation, candidate_gateway, candidate_notices, clarifications, configuration_gateway, draft_commands as cmd, events, lifecycle, open_period_read, publication, read, submission_close
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.tests import fixtures as fx, sample

CHANNELS = ("STATE_PORTAL", "MINISTRY_WEBSITE", "NOTICE_BOARD", "NATIONAL_NEWSPAPERS")


class OpenPeriodCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_all()
		self.addCleanup(frappe.set_user, "Administrator")
		frappe.flags.kt_tenders_clock = "2027-05-15 07:55:00"
		self.addCleanup(setattr, frappe.flags, "kt_tenders_clock", None)
		self.name = self._published()

	def _confirm(self, subject: str, channel: str, *, addendum: str = "", available_at="2027-05-15 08:00:00"):
		root = frappe.get_doc("Tender", self.name)
		online = channel in configuration_gateway.ONLINE_CHANNELS
		common = dict(available_at=available_at, evidence_reference=f"REF-{channel}", evidence_file=fx.evidence_file(f"{channel}.png"), public_url=f"https://portal.example.test/{channel}" if online else "", url_not_applicable_reason="" if online else "Physical channel", expected_record_version=root.record_version, idempotency_key=fx.key(), attestation_confirmed=True, user=fx.HOPF)
		if subject == "publication":
			return publication.confirm_publication_channel(tender=self.name, channel=channel, package_digest=frappe.db.get_value("Tender Publication", root.publication, "package_digest"), **common)
		return addenda.confirm_addendum_publication_channel(tender=self.name, addendum=addendum, channel=channel, addendum_digest=frappe.db.get_value("Tender Addendum", addendum, "addendum_digest"), **common)

	def _published(self) -> str:
		authorised = fx.authorised_handoff()
		started = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		root = frappe.get_doc("Tender", started["tender"])
		cmd.save_tender_draft(tender=root.name, values=sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE), expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		submitted = lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		approved = lifecycle.approve_tender_package(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, task=submitted["task"])
		root.reload()
		publication.authorise_tender_publication(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO, task=approved["task"])
		self.name = root.name
		for channel in CHANNELS:
			self._confirm("publication", channel)
		self.assertEqual(frappe.db.get_value("Tender", root.name, "overall_status"), "Published — open")
		return root.name

	def _root(self):
		return frappe.get_doc("Tender", self.name)

	def _addendum(self, *, values=None, user=fx.OFFICER) -> str:
		root = self._root()
		created = addenda.create_addendum_draft(tender=self.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=user)
		name = created["addendum"]["name"]
		if values is not None:
			root.reload()
			saved = addenda.update_addendum_draft(tender=self.name, addendum=name, values=values, expected_record_version=root.record_version, idempotency_key=fx.key(), user=user)
			self.assertTrue(saved["ok"], saved)
		return name

	FIXTURE_ADDENDUM = {
		"change_class": "Administrative clarification", "affected_area": "Goods/delivery schedule", "affected_reference_key": "delivery_location",
		"revised_value": "Test Delivery Location — Tenders, 3rd Floor Procurement Stores", "reason": "The published address omitted the internal delivery point",
		"materiality_statement": "Same site; no change to scope, quantity, value or evaluation basis.",
	}


class TestAddenda(OpenPeriodCase):
	def test_a_draft_records_before_after_and_is_stale_when_the_published_value_changed(self):
		frappe.flags.kt_tenders_clock = "2027-05-31 08:30:00"
		name = self._addendum(values=self.FIXTURE_ADDENDUM)
		doc = frappe.get_doc("Tender Addendum", name)
		self.assertEqual((doc.addendum_number, doc.addendum_reference.endswith("-001"), doc.previous_value, doc.status), (1, True, fx.LOCATION, "Draft"))
		self.assertTrue(doc.deadline_extension_required)  # 31 May → 5 Jun is inside the late-amendment window
		projection = open_period_read.get_tender_addendum(tender=self.name, addendum=name, user=fx.OFFICER)
		self.assertEqual((projection["material"], projection["deadline_rule"]["required"], projection["allowed_actions"]), (False, True, ["save_addendum_draft", "submit_addendum_for_issue", "discard_addendum_draft"]))
		self.assertEqual(projection["deadline_rule"]["explanation"], "This addendum is being issued within the governed late-amendment period.")
		root = self._root()
		with self.assertRaises(TendersError) as ctx:  # no revised deadline yet
			addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_ADDENDUM_DEADLINE_REQUIRED")
		refused = addenda.update_addendum_draft(tender=self.name, addendum=name, values={"revised_submission_deadline": "2027-06-04 11:00:00"}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertIn("revised_submission_deadline", refused["errors"])
		# a second created draft returns the open one
		again = addenda.create_addendum_draft(tender=self.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertEqual((again["action"], again["addendum"]["name"]), ("existing", name))
		# stale: the recorded prior value no longer matches (simulate a drifted baseline)
		frappe.db.set_value("Tender Addendum", name, "previous_value", "Somewhere else", update_modified=False)
		with self.assertRaises(TendersError) as ctx:
			addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_ADDENDUM_STALE")

	def test_a_material_change_cannot_be_issued_and_goes_to_a_cancellation_review(self):
		name = self._addendum(values={**self.FIXTURE_ADDENDUM, "affected_area": "Goods/delivery schedule", "affected_reference_key": "goods:1:quantity", "revised_value": "300 Each", "reason": "Additional deployment sites require 50 more laptops"})
		projection = open_period_read.get_tender_addendum(tender=self.name, addendum=name, user=fx.OFFICER)
		self.assertEqual((projection["material"], projection["material_text"]), (True, "This change cannot be made by addendum."))
		self.assertEqual(projection["allowed_actions"], ["save_addendum_draft", "request_cancellation_review", "discard_addendum_draft", "view_cancellation_requirements"])
		root = self._root()
		with self.assertRaises(TendersError) as ctx:
			addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_ADDENDUM_MATERIAL")
		self.assertEqual(frappe.db.get_value("Tender Addendum", name, "status"), "Draft")
		# TPR12-AC-012: one AO item and one sender waiting item; the Tender is unchanged
		reason = "Additional deployment sites require 50 more laptops; please consider cancellation."
		requested = addenda.request_tender_cancellation_review(tender=self.name, addendum=name, reason=reason, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		task = frappe.get_doc("Tender Task", requested["task"])
		self.assertEqual((task.task_type, task.business_role, task.sender, task.status), ("AO cancellation review", "Accounting Officer", fx.OFFICER, "Open"))
		self.assertIn("300 Each", task.comment)
		root.reload()
		again = addenda.request_tender_cancellation_review(tender=self.name, addendum=name, reason=reason, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual((again["action"], again["task"]), ("already_requested", requested["task"]))
		self.assertEqual(frappe.db.count("Tender Task", {"tender": self.name, "task_type": "AO cancellation review"}), 1)
		with self.assertRaises(TendersError):  # no edit or discard while the AO considers it
			addenda.discard_addendum_draft(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		from kentender_procurement.tenders.services import my_work_provider

		ao_rows = my_work_provider.my_work_rows(user=fx.AO)["assigned"]
		self.assertIn(f"Consider cancellation of {root.tender_reference}", [r["title"] for r in ao_rows])
		waiting = my_work_provider.my_work_rows(user=fx.OFFICER)["waiting"]
		self.assertTrue(any(r["title"].startswith("Waiting for ") and r["title"].endswith(f"to consider cancellation of {root.tender_reference}") for r in waiting), waiting)
		root.reload()
		with self.assertRaises(frappe.DoesNotExistError):  # only the AO closes it
			addenda.close_tender_cancellation_review(tender=self.name, addendum=name, reason="Budget covers only the original quantity.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		addenda.close_tender_cancellation_review(tender=self.name, addendum=name, reason="The original quantity stands; cancellation is not warranted.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO)
		self.assertEqual((frappe.db.get_value("Tender Addendum", name, "cancellation_review_status"), frappe.db.get_value("Tender Task", requested["task"], "status")), ("Closed", "Completed"))
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Published — open")
		self.assertEqual(my_work_provider.my_work_rows(user=fx.OFFICER)["waiting"], [])
		root.reload()
		with self.assertRaises(TendersError):  # the same proposal cannot request another review
			addenda.request_tender_cancellation_review(tender=self.name, addendum=name, reason=reason, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		discarded = addenda.discard_addendum_draft(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(discarded["addendum"]["status"], "Discarded")
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Published — open")
		self.assertEqual(read.get_tender(tender=self.name, user=fx.OFFICER)["open_period"]["addenda"], [])

	def test_issue_creates_channel_records_and_the_addendum_becomes_issued_with_the_revised_deadline(self):
		frappe.flags.kt_tenders_clock = "2027-05-31 08:30:00"
		name = self._addendum(values={**self.FIXTURE_ADDENDUM, "revised_submission_deadline": "2027-06-12 11:00:00"})
		root = self._root()
		submitted = addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(frappe.db.get_value("Tender Task", submitted["task"], "task_type"), "HOPF addendum issue")
		root.reload()
		with self.assertRaises(frappe.DoesNotExistError):  # only the HoPF issues
			addenda.issue_addendum(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		returned = addenda.return_addendum_for_correction(tender=self.name, addendum=name, reason="State the floor in the revised wording.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertEqual(returned["addendum"]["status"], "Returned")
		# plan W5: the returned row is kept as submitted; work continues on a copied Draft
		copy = returned["copied_draft"]["name"]
		self.assertEqual((frappe.db.get_value("Tender Addendum", copy, "predecessor_addendum"), returned["copied_draft"]["status"], returned["copied_draft"]["addendum_reference"]), (name, "Draft", returned["addendum"]["addendum_reference"]))
		correct = frappe.db.get_value("Tender Task", {"tender": self.name, "task_type": "Correct returned addendum", "subject_id": copy, "status": "Open"}, ["holder", "comment"], as_dict=True)
		self.assertEqual((correct.holder, correct.comment), (fx.OFFICER, "State the floor in the revised wording."))
		name = copy
		root.reload()
		addenda.update_addendum_draft(tender=self.name, addendum=name, values={"revised_value": self.FIXTURE_ADDENDUM["revised_value"]}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		frappe.flags.kt_tenders_clock = "2027-05-31 09:00:00"
		original = bid_definition.current(self.name)
		issued = addenda.issue_addendum(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertEqual(len(issued["confirmations"]), 4)
		doc = frappe.get_doc("Tender Addendum", name)
		self.assertEqual((doc.status, doc.issue_decided_by, len(doc.addendum_digest), doc.issued_at), ("Awaiting publication confirmation", fx.HOPF, 64, None))
		# TPR09-AC-097/098: the successor is frozen but the prior definition stays bidder-current
		self.assertEqual(frappe.db.get_value("Tender Bid Definition", doc.successor_bid_definition, ["status", "definition_version"]), ("Frozen", 2))
		self.assertEqual(bid_definition.current(self.name)["bid_definition_id"], original["bid_definition_id"])
		self.assertTrue(frappe.db.exists("Tender Document", {"addendum": name, "kind": "Addendum notice"}))
		self.assertEqual(frappe.db.get_value("Tender", self.name, "submission_deadline"), frappe.utils.get_datetime("2027-06-05 11:00:00"))  # unchanged until Issued
		record = read.get_tender(tender=self.name, user=fx.HOPF)
		self.assertEqual(record["open_period"]["effective_addenda_count"], 0)  # not yet effective
		for channel in CHANNELS[:3]:
			self._confirm("addendum", channel, addendum=name, available_at="2027-05-31 09:00:00")
		self.assertEqual(frappe.db.get_value("Tender Addendum", name, "status"), "Awaiting publication confirmation")
		final = self._confirm("addendum", CHANNELS[3], addendum=name, available_at="2027-05-31 09:00:00")
		self.assertTrue(final["all_confirmed"])
		doc.reload()
		self.assertEqual((doc.status, str(doc.issued_at)), ("Issued", "2027-05-31 09:00:00"))
		# TPR09-AC-099: the successor definition and revised deadline are effective together
		self.assertEqual(bid_definition.current(self.name)["bid_definition_id"], doc.successor_bid_definition_id)
		self.assertEqual(frappe.db.get_value("Tender Bid Definition", {"bid_definition_id": original["bid_definition_id"]}, "status"), "Superseded")
		self.assertEqual(str(frappe.db.get_value("Tender", self.name, "submission_deadline")), "2027-06-12 11:00:00")
		record = read.get_tender(tender=self.name, user=fx.HOPF)
		self.assertEqual((record["open_period"]["effective_addenda_count"], record["open_period"]["addenda"][0]["change_summary"]), (1, "Delivery point clarified"))
		ws = read.get_tenders_workspace(user=fx.OFFICER)
		self.assertEqual(next(r for r in ws["rows"] if r.get("tender") == self.name)["status_label"], "Published — open until 12 Jun 2027, 11:00 EAT")
		# the effective value now carries the revised wording, so a second addendum against the old wording is stale
		self.assertEqual(next(r for r in addenda.affected_references(self._root()) if r["key"] == "delivery_location")["value"], self.FIXTURE_ADDENDUM["revised_value"])
		self.assertEqual(sorted(e["event_type"] for e in events.list_for_tender(self.name) if e["event_type"].startswith("Addendum")), ["AddendumDraftCreated", "AddendumDraftSaved", "AddendumDraftSaved", "AddendumIssueDecided", "AddendumIssued", "AddendumReturned", "AddendumSubmittedForIssue", "AddendumSubmittedForIssue"])


class TestClarifications(OpenPeriodCase):
	CANDIDATE = {"bidder_arrangement_id": "ARR-TNDT-001", "candidate_name": "Afya Digital Supplies Limited", "notice_address": "tenders@afyadigital.example"}
	SECOND = {"bidder_arrangement_id": "ARR-TNDT-002", "candidate_name": "Second Supplier Limited", "notice_address": "bids@second.example"}
	QUESTION = "May the two comparable contracts be from different customers?"

	def setUp(self):
		super().setUp()
		frappe.flags.kt_tenders_clock = "2027-05-19 09:20:00"
		for candidate in (self.CANDIDATE, self.SECOND):
			candidate_gateway.register_stand_in_candidate(tender=self.name, user=fx.PRODUCER, **candidate)
		self.sent: list[str] = []
		frappe.flags.kt_tenders_notice_sync = True
		frappe.flags.kt_tenders_notice_transport = self._transport
		self.addCleanup(setattr, frappe.flags, "kt_tenders_notice_sync", False)
		self.addCleanup(setattr, frappe.flags, "kt_tenders_notice_transport", None)
		self.fail_to = ""

	def _transport(self, notice):
		self.sent.append(notice.destination_snapshot)
		if notice.destination_snapshot == self.fail_to:
			return {"result": "Failed", "provider_reference": "", "failure_reason": "Mailbox unavailable."}
		return {"result": "Delivered", "provider_reference": f"test:{notice.name}", "failure_reason": ""}

	def _receive(self, *, event="EVT-1", candidate="ARR-TNDT-001", at="2027-05-26 09:00:00", question=None, user=fx.PRODUCER):
		return clarifications.receive_tender_clarification(tender=self.name, candidate_registration_id=candidate, question=question or self.QUESTION, received_at=at, inbound_event_id=event, user=user)

	def test_only_a_registered_candidate_through_the_producer_asks_before_the_deadline(self):
		with self.assertRaises(TendersError) as ctx:  # TPR10-AC-002: no business user invents one
			self._receive(user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_RESPONSIBILITY_REQUIRED")
		with self.assertRaises(TendersError) as ctx:
			self._receive(candidate="ARR-UNKNOWN")
		self.assertEqual(ctx.exception.code, "TND_CLARIFICATION_CANDIDATE_REQUIRED")
		with self.assertRaises(TendersError) as ctx:  # TPR10-AC-003: at the deadline creates nothing
			self._receive(event="EVT-LATE", at="2027-05-27 17:00:00")
		self.assertEqual(ctx.exception.code, "TND_CLARIFICATION_LATE")
		self.assertEqual(frappe.db.count("Tender Clarification", {"tender": self.name}), 0)
		received = self._receive()  # TPR10-AC-001: no addendum needed
		self.assertEqual(received["status"], "Awaiting response")
		self.assertEqual((self._receive()["action"], frappe.db.count("Tender Clarification", {"tender": self.name})), ("duplicate", 1))
		task = frappe.db.get_value("Tender Task", {"tender": self.name, "task_type": "Clarification response", "subject_id": received["clarification"], "status": "Open"}, "name")
		self.assertTrue(task)
		projection = open_period_read.get_tender_clarification(tender=self.name, clarification=received["clarification"], user=fx.OFFICER)
		self.assertEqual((projection["clarification"]["candidate_label"], projection["clarification"]["related_addendum_reference"], projection["allowed_actions"]), ("Registered Tender candidate", "None", ["send_response", "prepare_addendum"]))

	def test_a_general_answer_reaches_every_candidate_without_naming_the_asker_and_a_direct_one_only_the_asker(self):
		first = self._receive()
		root = self._root()
		frappe.flags.kt_tenders_clock = "2027-05-26 11:00:00"
		with self.assertRaises(TendersError) as ctx:  # the audience is a deliberate choice
			clarifications.respond_to_tender_clarification(tender=self.name, clarification=first["clarification"], response="Yes, from different customers.", affects_published_tender=False, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_CONTROL_INVALID")
		answer = "Yes. The Tender requires two comparable contracts and does not require both contracts to be from the same customer."
		answered = clarifications.respond_to_tender_clarification(tender=self.name, clarification=first["clarification"], response=answer, affects_published_tender=False, response_audience="All registered candidates", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual((answered["status"], answered["notices"]), ("Answered", 2))
		self.assertEqual(sorted(self.sent), ["bids@second.example", "tenders@afyadigital.example"])
		self.assertEqual(candidate_notices.delivery_summary(first["clarification"], notice_type="Clarification response")["label"], "2 of 2 delivered")
		self.assertFalse(frappe.db.exists("Tender Task", {"subject_id": first["clarification"], "status": "Open"}))
		event = [e for e in events.list_for_tender(self.name) if e["event_type"] == "ClarificationAnswered"][0]
		self.assertNotIn("ARR-TNDT-001", json.dumps(event["payload"]))
		second = self._receive(event="EVT-2", candidate="ARR-TNDT-002", question="Is a certified copy of each contract acceptable?")
		root.reload()
		self.sent.clear()
		clarifications.respond_to_tender_clarification(tender=self.name, clarification=second["clarification"], response="Yes, certified copies are acceptable.", affects_published_tender=False, response_audience="Asker only", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertEqual(self.sent, ["bids@second.example"])

	def test_an_answer_that_changes_the_tender_waits_for_an_issued_addendum(self):
		received = self._receive()
		root = self._root()
		awaiting = clarifications.respond_to_tender_clarification(tender=self.name, clarification=received["clarification"], response="The delivery point is the 3rd Floor Procurement Stores.", affects_published_tender=True, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual((awaiting["status"], awaiting["reason_code"]), ("Awaiting addendum", "TND_CLARIFICATION_ADDENDUM_REQUIRED"))
		self.assertEqual(self.sent, [])  # TPR10-AC-005: nothing is sent
		self.assertEqual(frappe.db.get_value("Tender Clarification", received["clarification"], "response"), "The delivery point is the 3rd Floor Procurement Stores.")
		frappe.flags.kt_tenders_clock = "2027-05-26 12:00:00"
		name = self._addendum(values={**self.FIXTURE_ADDENDUM, "revised_submission_deadline": "2027-06-12 11:00:00"})
		root.reload()
		addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		addenda.issue_addendum(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		root.reload()
		still = clarifications.respond_to_tender_clarification(tender=self.name, clarification=received["clarification"], response="The delivery point is the 3rd Floor Procurement Stores.", affects_published_tender=True, required_addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(still["status"], "Awaiting addendum")  # TPR10-AC-006: issued AND effective
		for channel in CHANNELS:
			self._confirm("addendum", channel, addendum=name, available_at="2027-05-26 12:30:00")
		self.assertEqual(len([n for n in frappe.get_all("Tender Candidate Notice", filters={"subject_id": name}, pluck="status")]), 2)  # addendum notices (one per candidate)
		root.reload()
		self.sent.clear()
		sent = clarifications.respond_to_tender_clarification(tender=self.name, clarification=received["clarification"], response="The delivery point is the 3rd Floor Procurement Stores.", affects_published_tender=True, required_addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual((sent["status"], sent["response_audience"]), ("Answered", "All registered candidates"))
		self.assertEqual(len(self.sent), 2)

	def test_a_failed_notice_is_retried_without_changing_the_tender(self):
		received = self._receive()
		root = self._root()
		self.fail_to = "bids@second.example"
		clarifications.respond_to_tender_clarification(tender=self.name, clarification=received["clarification"], response="Yes, from different customers.", affects_published_tender=False, response_audience="All registered candidates", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		failed = frappe.db.get_value("Tender Candidate Notice", {"subject_id": received["clarification"], "status": "Failed"}, ["name", "attempt_count", "failure_reason"], as_dict=True)
		self.assertEqual((failed.attempt_count, failed.failure_reason), (1, "Mailbox unavailable."))
		self.assertEqual(candidate_notices.delivery_summary(received["clarification"])["label"], "1 candidate notice failed")
		self.assertEqual(frappe.db.get_value("Tender Clarification", received["clarification"], "status"), "Answered")  # the answer stands
		root.reload()
		with self.assertRaises(frappe.DoesNotExistError):
			candidate_notices.retry_failed_candidate_notice(tender=self.name, notice=failed.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO)
		self.fail_to = ""
		retried = candidate_notices.retry_failed_candidate_notice(tender=self.name, notice=failed.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(retried["status"], "Delivered")
		notice = frappe.get_doc("Tender Candidate Notice", failed.name)
		self.assertEqual(([a.result for a in notice.attempts], notice.destination_snapshot), (["Failed", "Delivered"], "bids@second.example"))
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Published — open")


class TestCancellationAndClose(OpenPeriodCase):
	def test_recommendation_is_optional_and_cancellation_is_final_with_obligations(self):
		root = self._root()
		frappe.flags.kt_tenders_clock = "2027-06-04 13:30:00"
		with self.assertRaises(TendersError) as ctx:
			cancellation.recommend_tender_cancellation(tender=self.name, ground="NOT_A_GROUND", reason="I recommend cancellation because the confirmed budget is insufficient.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertEqual(ctx.exception.code, "TND_CANCELLATION_GROUND_INVALID")
		recommended = cancellation.recommend_tender_cancellation(tender=self.name, ground="INADEQUATE_BUDGET", reason="I recommend cancellation because the confirmed budget is insufficient to complete this procurement.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Published — open")
		screen = open_period_read.get_tender_cancellation(tender=self.name, user=fx.AO)
		self.assertEqual((screen["recommendation"]["ground"], screen["allowed_actions"], screen["summary"]["channel_count"]), ("INADEQUATE_BUDGET", ["cancel_tender"], 4))
		self.assertEqual(screen["consequences"]["ppra_report_due_by"], "18 Jun 2027")
		self.assertEqual([g["label"] for g in screen["grounds"]][2], "Inadequate budgetary provision")
		root.reload()
		frappe.flags.kt_tenders_clock = "2027-06-04 14:00:00"
		for user in (fx.HOPF, fx.OFFICER):
			with self.assertRaises(frappe.DoesNotExistError):
				cancellation.cancel_tender(tender=self.name, ground="INADEQUATE_BUDGET", reason="The confirmed budget available for this procurement is insufficient to proceed.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=user)
		cancelled = cancellation.cancel_tender(tender=self.name, ground="INADEQUATE_BUDGET", reason="The confirmed budget available for this procurement is insufficient to proceed.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO)
		root.reload()
		doc = frappe.get_doc("Tender Cancellation", cancelled["cancellation"])
		self.assertEqual((root.overall_status, doc.ground_label, doc.decided_by, doc.recommendation), ("Cancelled", "Inadequate budgetary provision", fx.AO, recommended["decision"]))
		self.assertEqual((str(doc.ppra_report_due_by), str(doc.candidate_notice_due_by)), ("2027-06-18", "2027-06-18"))
		self.assertEqual([o.obligation_type for o in doc.obligations], ["Notice channel"] * 4 + ["PPRA report", "Candidate notice"])
		# §5.7: no candidate registered, so the absence is recorded from the registry
		self.assertEqual([o.status for o in doc.obligations], ["Due"] * 5 + ["Recorded"])
		self.assertEqual(doc.obligations[-1].evidence_reference, "No Tender-bound candidates were registered when the Tender was cancelled.")
		compliance = frappe.db.get_value("Tender Task", {"tender": self.name, "task_type": "Cancellation compliance", "status": "Open"}, ["holder", "sender"], as_dict=True)
		self.assertEqual((compliance.holder, compliance.sender), (fx.OFFICER, fx.AO))
		self.assertTrue(frappe.db.exists("Tender Document", {"cancellation": doc.name, "kind": "Cancellation notice"}))
		self.assertEqual(frappe.db.count("Tender Channel Confirmation", {"subject_type": "Cancellation notice", "subject_id": doc.name}), 4)
		self.assertEqual(frappe.db.get_value("Tender Publication", root.publication, "publication_status"), "Cancelled")
		# finality: no further business work, the Requisition is untouched
		for fn, kwargs in ((addenda.create_addendum_draft, {}), (cancellation.recommend_tender_cancellation, {"ground": "NEED_CEASED", "reason": "The procurement need has ceased entirely now."})):
			with self.assertRaises(TendersError) as ctx:
				fn(tender=self.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, **kwargs)
			self.assertEqual(ctx.exception.code, "TND_CANCELLED")
		self.assertEqual(frappe.db.get_value("Procurement Requisition", root.requisition, "current_state"), "Authorised")
		self.assertTrue(frappe.db.get_value("Authorised Requisition Handoff", root.requisition_handoff, "consumed_at"))
		self.assertEqual(len(fx.test_tenders()), 1)
		record = read.get_tender(tender=self.name, user=fx.OFFICER)
		self.assertEqual((record["screen"], record["allowed_actions"]), ("cancelled", ["record_cancellation_evidence", "view_history"]))
		# evidence: PPRA report recorded; a notice channel by the compliance
		# holder (§10.17 DES-12: the Procurement Officer) or the HOPF; an
		# auditor never; overdue derivation
		root.reload()
		recorded = cancellation.record_cancellation_compliance_evidence(tender=self.name, obligation_id="PPRA_REPORT", evidence_reference="PPRA-ACK-2027-0611", evidence_file=fx.evidence_file("ppra-ack.png"), expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(recorded["status"], "Recorded")
		root.reload()
		with self.assertRaises((TendersError, frappe.DoesNotExistError)):
			cancellation.record_cancellation_compliance_evidence(tender=self.name, obligation_id="NOTICE-NOTICE_BOARD", evidence_reference="NB-CANCEL-2027-034", evidence_file=fx.evidence_file("nb.png"), expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AUDITOR, available_at="2027-06-05 08:00:00", attestation_confirmed=True)
		# the attester's own attestation is required; it is never assumed (v0.8 defect)
		with self.assertRaises(TendersError) as ctx:
			cancellation.record_cancellation_compliance_evidence(tender=self.name, obligation_id="NOTICE-NOTICE_BOARD", evidence_reference="NB-CANCEL-2027-034", evidence_file=fx.evidence_file("nb.png"), expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER, available_at="2027-06-05 08:00:00")
		self.assertEqual((ctx.exception.code, set(ctx.exception.detail["fields"])), ("TND_PUBLICATION_CONFIRMATION_INCOMPLETE", {"attestation"}))
		root.reload()
		notice = cancellation.record_cancellation_compliance_evidence(tender=self.name, obligation_id="NOTICE-NOTICE_BOARD", evidence_reference="NB-CANCEL-2027-034", evidence_file=fx.evidence_file("nb.png"), expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER, available_at="2027-06-05 08:00:00", attestation_confirmed=True)
		self.assertEqual(notice["status"], "Recorded")
		self.assertEqual(frappe.db.get_value("Tender Channel Confirmation", {"subject_type": "Cancellation notice", "subject_id": doc.name, "channel": "NOTICE_BOARD"}, "attested_by"), fx.OFFICER)
		root.reload()
		hopf = cancellation.record_cancellation_compliance_evidence(tender=self.name, obligation_id="NOTICE-MINISTRY_WEBSITE", evidence_reference="MW-CANCEL-2027-034", evidence_file=fx.evidence_file("mw.png"), public_url="https://www.health.go.ke/tenders/cancel", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, available_at="2027-06-05 08:10:00", attestation_confirmed=True)
		self.assertEqual(hopf["status"], "Recorded")
		self.assertEqual(frappe.db.get_value("Tender Channel Confirmation", {"subject_type": "Cancellation notice", "subject_id": doc.name, "channel": "NOTICE_BOARD"}, "status"), "Confirmed")
		frappe.flags.kt_tenders_clock = "2027-06-20 09:00:00"
		screen = open_period_read.get_tender_cancellation(tender=self.name, user=fx.AUDITOR)
		statuses = {o["obligation_id"]: o["status"] for o in screen["cancellation"]["obligations"]}
		self.assertEqual((statuses["PPRA_REPORT"], statuses["NOTICE-NOTICE_BOARD"], statuses["CANDIDATE_NOTICE"], statuses["NOTICE-STATE_PORTAL"]), ("Recorded", "Recorded", "Recorded", "Overdue"))
		self.assertEqual(screen["cancellation"]["ppra_report_status"], "Recorded")
		self.assertEqual(frappe.db.get_value("Tender", self.name, "overall_status"), "Cancelled")

	def test_the_submission_period_closes_by_the_system_with_one_immutable_handoff(self):
		root = self._root()
		with self.assertRaises(TendersError):  # not yet due
			submission_close.close_tender_submission_period(tender=self.name, idempotency_key=fx.key(), user="Administrator")
		with self.assertRaises(TendersError) as ctx:  # never a business user
			submission_close.close_tender_submission_period(tender=self.name, idempotency_key=fx.key(), user=fx.HOPF, force=True)
		self.assertEqual(ctx.exception.code, "TND_RESPONSIBILITY_REQUIRED")
		frappe.flags.kt_tenders_clock = "2027-06-05 11:00:00"
		run = submission_close.close_due_submission_periods()
		self.assertEqual(run["closed"], [self.name])
		root.reload()
		self.assertEqual(root.overall_status, "Submission period ended")
		handoff = frappe.get_doc("Tender Submission Handoff", root.submission_handoff)
		payload = json.loads(handoff.payload_json)
		self.assertEqual((payload["handoff_version"], payload["tender_version"]["package_digest"], payload["publication"]["published_at"]), ("1.0", frappe.db.get_value("Tender Version", root.approved_version, "package_digest"), str(frappe.db.get_value("Tender Publication", root.publication, "published_at"))))
		self.assertEqual(payload["effective_submission_deadline"], "2027-06-05 11:00:00")
		self.assertEqual(len(payload["publication"]["required_channels"]), 4)
		self.assertEqual(frappe.db.get_value("Tender Event", {"tender": self.name, "event_type": "TenderSubmissionPeriodEnded"}, "status"), "Pending")
		again = submission_close.close_due_submission_periods()
		self.assertEqual(again["closed"], [])
		self.assertEqual(frappe.db.count("Tender Submission Handoff", {"tender": self.name}), 1)
		self.assertEqual(submission_close.get_submission_handoff(tender=self.name, user=fx.AUDITOR)["handoff_digest"], handoff.handoff_digest)
		record = read.get_tender(tender=self.name, user=fx.HOPF)
		self.assertEqual((record["screen"], record["tender"]["badge"]), ("published", "Submission period ended"))
		self.assertEqual([a for a in record["allowed_actions"] if a in ("prepare_addendum", "cancel_tender", "recommend_cancellation")], [])
		with self.assertRaises(TendersError) as ctx:
			addenda.create_addendum_draft(tender=self.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_STALE_VERSION")
