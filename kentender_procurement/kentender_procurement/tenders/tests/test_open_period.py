# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §5.6 / §5.7 / §7.4 on a published Tender: addenda
(draft, stale prior value, materiality, deadline rule, issue, channel
confirmation → Issued, deadline revised), inquiries (producer identity,
dedup, late, direct vs anonymised broadcast), recommendation, cancellation
(AO only, ground + reason, immediate finality, obligations, notice), evidence
recording, and the submission close with its Bid Submission handoff.
TPR08-AC-056..068, TPR-IMP-055."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tenders.services import addenda, cancellation, configuration_gateway, draft_commands as cmd, events, inquiries, lifecycle, open_period_read, publication, read, submission_close
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
		self.assertEqual((projection["material"], projection["deadline_rule"]["required"], projection["allowed_actions"]), (False, True, ["save_addendum_draft", "submit_addendum_for_issue"]))
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

	def test_a_material_change_cannot_be_submitted_or_issued(self):
		name = self._addendum(values={**self.FIXTURE_ADDENDUM, "affected_area": "Goods/delivery schedule", "affected_reference_key": "goods:1:quantity", "revised_value": "300 Each", "reason": "Additional deployment sites require 50 more laptops"})
		projection = open_period_read.get_tender_addendum(tender=self.name, addendum=name, user=fx.OFFICER)
		self.assertEqual((projection["material"], projection["material_text"], projection["allowed_actions"]), (True, "This change cannot be made by addendum.", ["save_addendum_draft"]))
		root = self._root()
		with self.assertRaises(TendersError) as ctx:
			addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_ADDENDUM_MATERIAL")
		self.assertEqual(frappe.db.get_value("Tender Addendum", name, "status"), "Draft")

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
		root.reload()
		addenda.update_addendum_draft(tender=self.name, addendum=name, values={"revised_value": self.FIXTURE_ADDENDUM["revised_value"]}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		frappe.flags.kt_tenders_clock = "2027-05-31 09:00:00"
		issued = addenda.issue_addendum(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertEqual(len(issued["confirmations"]), 4)
		doc = frappe.get_doc("Tender Addendum", name)
		self.assertEqual((doc.status, doc.issued_by, len(doc.addendum_digest)), ("Awaiting publication confirmation", fx.HOPF, 64))
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
		self.assertEqual((doc.status, str(doc.effective_at)), ("Issued", "2027-05-31 09:00:00"))
		self.assertEqual(str(frappe.db.get_value("Tender", self.name, "submission_deadline")), "2027-06-12 11:00:00")
		record = read.get_tender(tender=self.name, user=fx.HOPF)
		self.assertEqual((record["open_period"]["effective_addenda_count"], record["open_period"]["addenda"][0]["change_summary"]), (1, "Delivery point clarified"))
		ws = read.get_tenders_workspace(user=fx.OFFICER)
		self.assertEqual(next(r for r in ws["rows"] if r.get("tender") == self.name)["status_label"], "Published — open until 12 Jun 2027, 11:00 EAT")
		# the effective value now carries the revised wording, so a second addendum against the old wording is stale
		self.assertEqual(next(r for r in addenda.affected_references(self._root()) if r["key"] == "delivery_location")["value"], self.FIXTURE_ADDENDUM["revised_value"])
		self.assertEqual(sorted(e["event_type"] for e in events.list_for_tender(self.name) if e["event_type"].startswith("Addendum")), ["AddendumDraftCreated", "AddendumDraftSaved", "AddendumDraftSaved", "AddendumIssueDecided", "AddendumIssued", "AddendumReturned", "AddendumSubmittedForIssue", "AddendumSubmittedForIssue"])


class TestInquiries(OpenPeriodCase):
	def _issued_addendum(self) -> str:
		frappe.flags.kt_tenders_clock = "2027-05-31 08:30:00"
		name = self._addendum(values={**self.FIXTURE_ADDENDUM, "revised_submission_deadline": "2027-06-12 11:00:00"})
		root = self._root()
		addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		addenda.issue_addendum(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		for channel in CHANNELS:
			self._confirm("addendum", channel, addendum=name, available_at="2027-05-31 09:00:00")
		return name

	def test_only_the_registered_producer_delivers_and_responses_are_classified(self):
		addendum = self._issued_addendum()
		question = "Do suppliers who downloaded the original Tender need to change the offered delivery price?"
		with self.assertRaises(TendersError) as ctx:  # AC-063: no manually invented inquiry
			inquiries.receive_addendum_inquiry(tender=self.name, addendum=addendum, candidate_identity="SUP-0001", question=question, received_at="2027-06-01 09:00:00", inbound_event_id="EVT-1", user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_RESPONSIBILITY_REQUIRED")
		received = inquiries.receive_addendum_inquiry(tender=self.name, addendum=addendum, candidate_identity="SUP-0001", question=question, received_at="2027-06-01 09:00:00", inbound_event_id="EVT-1", user=fx.PRODUCER)
		self.assertEqual(received["status"], "Awaiting response")
		duplicate = inquiries.receive_addendum_inquiry(tender=self.name, addendum=addendum, candidate_identity="SUP-0001", question=question, received_at="2027-06-01 09:00:00", inbound_event_id="EVT-1", user=fx.PRODUCER)
		self.assertEqual((duplicate["action"], duplicate["inquiry"]), ("duplicate", received["inquiry"]))
		late = inquiries.receive_addendum_inquiry(tender=self.name, addendum=addendum, candidate_identity="SUP-0002", question="Is the deadline moving again?", received_at="2027-06-10 09:00:00", inbound_event_id="EVT-2", user=fx.PRODUCER)
		self.assertEqual(late["status"], "Late")
		root = self._root()
		with self.assertRaises(TendersError) as ctx:
			inquiries.respond_to_addendum_inquiry(tender=self.name, inquiry=late["inquiry"], response="No.", affects_requirements=False, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_INQUIRY_LATE")
		projection = open_period_read.get_addendum_inquiry(tender=self.name, inquiry=received["inquiry"], user=fx.OFFICER)
		self.assertEqual((projection["inquiry"]["candidate_label"], projection["inquiry"]["candidate_identity"], projection["allowed_actions"]), ("Verified supplier account", "", ["send_response"]))
		self.assertEqual(open_period_read.get_addendum_inquiry(tender=self.name, inquiry=received["inquiry"], user=fx.AUDITOR)["inquiry"]["candidate_identity"], "SUP-0001")
		frappe.flags.kt_tenders_clock = "2027-06-01 11:00:00"
		answered = inquiries.respond_to_addendum_inquiry(tender=self.name, inquiry=received["inquiry"], response="No. The addendum clarifies the internal delivery point within Afya House and does not change the delivery city, quantity or pricing basis.", affects_requirements=False, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual((answered["broadcast_status"], answered["broadcast_digest"]), ("Not required", ""))
		direct = [e for e in events.list_for_tender(self.name) if e["event_type"] == "AddendumInquiryAnswered"][0]
		self.assertEqual(direct["payload"]["audience"], "the asking candidate")
		# a requirement-affecting response is broadcast without the asker
		third = inquiries.receive_addendum_inquiry(tender=self.name, addendum=addendum, candidate_identity="SUP-0003", question="Does the revised delivery point change the delivery date?", received_at="2027-06-01 10:00:00", inbound_event_id="EVT-3", user=fx.PRODUCER)
		root.reload()
		broadcast = inquiries.respond_to_addendum_inquiry(tender=self.name, inquiry=third["inquiry"], response="Delivery remains due on 30 September 2027 at the revised delivery point.", affects_requirements=True, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertEqual(broadcast["broadcast_status"], "Broadcast")
		event = [e for e in events.list_for_tender(self.name) if e["event_type"] == "AddendumInquiryBroadcast"][0]
		self.assertNotIn("SUP-0003", json.dumps(event["payload"]))
		self.assertEqual((event["status"], event["payload"]["source_identity_included"], event["payload"]["broadcast_digest"]), ("Pending", False, broadcast["broadcast_digest"]))
		record = read.get_tender(tender=self.name, user=fx.OFFICER)
		self.assertEqual([i["response_status"] for i in record["open_period"]["inquiries"]], ["Answered", "Answered", "Late"])


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
		self.assertTrue(all(o.status == "Due" for o in doc.obligations))
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
		self.assertEqual(frappe.db.count("Tender"), 1)
		record = read.get_tender(tender=self.name, user=fx.OFFICER)
		self.assertEqual((record["screen"], record["allowed_actions"]), ("cancelled", ["record_cancellation_evidence", "view_history"]))
		# evidence: PPRA report recorded; a notice channel needs the HoPF; overdue derivation
		root.reload()
		recorded = cancellation.record_cancellation_compliance_evidence(tender=self.name, obligation_id="PPRA_REPORT", evidence_reference="PPRA-ACK-2027-0611", evidence_file=fx.evidence_file("ppra-ack.png"), expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(recorded["status"], "Recorded")
		root.reload()
		with self.assertRaises(TendersError) as ctx:
			cancellation.record_cancellation_compliance_evidence(tender=self.name, obligation_id="NOTICE-NOTICE_BOARD", evidence_reference="NB-CANCEL-2027-034", evidence_file=fx.evidence_file("nb.png"), expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_RESPONSIBILITY_REQUIRED")
		notice = cancellation.record_cancellation_compliance_evidence(tender=self.name, obligation_id="NOTICE-NOTICE_BOARD", evidence_reference="NB-CANCEL-2027-034", evidence_file=fx.evidence_file("nb.png"), expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, available_at="2027-06-05 08:00:00")
		self.assertEqual(notice["status"], "Recorded")
		self.assertEqual(frappe.db.get_value("Tender Channel Confirmation", {"subject_type": "Cancellation notice", "subject_id": doc.name, "channel": "NOTICE_BOARD"}, "status"), "Confirmed")
		frappe.flags.kt_tenders_clock = "2027-06-20 09:00:00"
		screen = open_period_read.get_tender_cancellation(tender=self.name, user=fx.AUDITOR)
		statuses = {o["obligation_id"]: o["status"] for o in screen["cancellation"]["obligations"]}
		self.assertEqual((statuses["PPRA_REPORT"], statuses["NOTICE-NOTICE_BOARD"], statuses["CANDIDATE_NOTICE"], statuses["NOTICE-STATE_PORTAL"]), ("Recorded", "Recorded", "Overdue", "Overdue"))
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
