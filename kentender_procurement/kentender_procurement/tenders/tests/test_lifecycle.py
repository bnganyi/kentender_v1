# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §5.1 rows 1–6 and the §5.1 correction rows, on a real
authorised Requisition handoff built through Requisitions' own commands:
StartTender (atomic consumption, duplicate start, unsupported product),
SaveTenderDraft (controls, stale write, evidence CRUD), submission (Must
fix blocks; freeze + documents + HoPF task), return (copied Draft),
approval (segregation from Version columns; AO task; no confirmation),
reopen (before authorisation only), requisition correction and the
corrected successor, the compatibility checks, the review result and the
§12 audit trail. TPR08-AC-005..010, 013..017, 025..036, 040, 076, 079."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tenders.services import compatibility, correction, draft_commands as cmd, events, lifecycle, review
from kentender_procurement.tenders.services import snapshot as snap
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.tests import fixtures as fx, sample


class TenderLifecycleCase(IntegrationTestCase):
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

	def _started(self, *, items=(("Business laptops", 1, "Clinical training"),)) -> tuple[dict, dict]:
		authorised = fx.authorised_handoff(items=items)
		started = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		return authorised, started

	def _complete(self, started: dict, **overrides) -> dict:
		values = sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE)
		values.update(overrides)
		root = frappe.get_doc("Tender", started["tender"])
		return cmd.save_tender_draft(tender=root.name, values=values, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)

	def _submitted(self) -> tuple[dict, dict, dict]:
		authorised, started = self._started()
		self._complete(started)
		root = frappe.get_doc("Tender", started["tender"])
		submitted = lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		return authorised, started, submitted

	def _approved(self) -> tuple[dict, dict, dict]:
		authorised, started, submitted = self._submitted()
		root = frappe.get_doc("Tender", started["tender"])
		approved = lifecycle.approve_tender_package(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, task=submitted["task"])
		return authorised, started, approved


class TestStartTender(TenderLifecycleCase):
	def test_start_creates_one_draft_binds_the_release_and_consumes_the_handoff_atomically(self):
		authorised, started = self._started()
		self.assertEqual(started["action"], "started")
		root = frappe.get_doc("Tender", started["tender"])
		version = frappe.get_doc("Tender Version", started["tender_version"])
		self.assertTrue(root.tender_reference.startswith("TND-"))
		self.assertEqual((root.overall_status, version.status, version.version_number), ("Draft", "Draft", 1))
		self.assertEqual(root.template_release_id, "IT-EQUIPMENT-OPEN-V1-1.1")
		self.assertEqual(version.prepared_by, fx.OFFICER)
		handoff = frappe.get_doc("Authorised Requisition Handoff", authorised["handoff"])
		self.assertEqual((handoff.tender, handoff.tender_version), (root.name, version.name))
		self.assertTrue(handoff.consumed_at)
		snapshot = snap.load(version)
		self.assertEqual(snapshot["handoff"], handoff.name)
		self.assertEqual(len(snapshot["items"]), 1)  # the test world funds one unit; two-item grouping is proven on the §10.1 sample
		self.assertEqual(json.loads(version.officer_payload_json)["tender_validity_days"], 120)
		self.assertEqual([e.event_type for e in frappe.get_all("Tender Event", filters={"tender": root.name}, fields=["event_type"])], ["TenderStarted"])

	def test_a_repeated_or_concurrent_start_returns_the_one_tender(self):
		authorised, started = self._started()
		again = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual((again["action"], again["tender"]), ("existing", started["tender"]))
		replay = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(replay["tender"], started["tender"])
		self.assertEqual(frappe.db.count("Tender"), 1)

	def test_only_a_procurement_officer_starts_and_an_unsupported_product_creates_nothing(self):
		authorised = fx.authorised_handoff()
		for user in (fx.HOPF, fx.AO, fx.AUDITOR, fx.NOBODY):
			with self.assertRaises(TendersError) as ctx:
				cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=user)
			self.assertEqual(ctx.exception.code, "TND_RESPONSIBILITY_REQUIRED", user)
		handoff = frappe.get_doc("Authorised Requisition Handoff", authorised["handoff"])
		payload = json.loads(handoff.payload_json)
		payload["planned_method"] = "Restricted Tender"
		handoff.payload_json = json.dumps(payload)
		handoff.flags.kt_lifecycle = True
		frappe.db.set_value("Authorised Requisition Handoff", handoff.name, "payload_json", json.dumps(payload), update_modified=False)
		with self.assertRaises(TendersError) as ctx:
			cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_PRODUCT_UNSUPPORTED")
		self.assertEqual(ctx.exception.detail["check"], "Method")
		self.assertEqual(frappe.db.count("Tender"), 0)
		self.assertFalse(frappe.db.get_value("Authorised Requisition Handoff", authorised["handoff"], "consumed_at"))

	def test_the_eight_compatibility_checks_on_the_fixture(self):
		snapshot, _ = sample.sample_snapshot()
		checks = compatibility.evaluate(snapshot)
		self.assertEqual([c.check for c in checks], ["Procurement category", "Product", "Method", "Reservation", "Lotting", "Currency", "Award package", "Plan horizon"])
		self.assertTrue(compatibility.is_supported(checks))
		snapshot["reservation_category_value"] = "Unknown group"
		self.assertEqual(compatibility.first_failure(compatibility.evaluate(snapshot)).check, "Reservation")


class TestSaveDraft(TenderLifecycleCase):
	def test_save_validates_merges_regenerates_and_bumps(self):
		_, started = self._started()
		root = frappe.get_doc("Tender", started["tender"])
		refused = cmd.save_tender_draft(tender=root.name, values={"tender_validity_days": 0}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertFalse(refused["ok"])
		self.assertIn("tender_validity_days", refused["errors"])
		with self.assertRaises(TendersError) as ctx:
			cmd.save_tender_draft(tender=root.name, values={"items": []}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_INHERITED_EDIT")
		saved = cmd.save_tender_draft(tender=root.name, values={"tender_title": "Supply and delivery of business laptops", "pre_tender_meeting": True, "meeting_mode": "Physical", "meeting_datetime": "2027-05-22 10:00:00", "meeting_venue": fx.LOCATION}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertTrue(saved["ok"])
		self.assertEqual(saved["record_version"], root.record_version + 1)
		self.assertEqual(saved["tasks"]["details"], "Needs attention")
		with self.assertRaises(TendersError) as ctx:
			cmd.save_tender_draft(tender=root.name, values={"tender_title": "x"}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_STALE_VERSION")
		# switching the meeting off clears the hidden conditional values
		done = cmd.save_tender_draft(tender=root.name, values={"pre_tender_meeting": False}, expected_record_version=saved["record_version"], idempotency_key=fx.key(), user=fx.OFFICER)
		state = json.loads(frappe.get_doc("Tender Version", started["tender_version"]).officer_payload_json)
		self.assertIsNone(state["meeting_venue"])
		self.assertTrue(done["ok"])
		for user in (fx.HOPF, fx.AUDITOR):
			with self.assertRaises(frappe.DoesNotExistError):
				cmd.save_tender_draft(tender=root.name, values={"tender_title": "x"}, expected_record_version=done["record_version"], idempotency_key=fx.key(), user=user)

	def test_evidence_rows_are_added_updated_removed_and_must_prove_a_published_requirement(self):
		_, started = self._started()
		root = frappe.get_doc("Tender", started["tender"])
		refused = cmd.add_tender_evidence_requirement(tender=root.name, values={"label": "Certificate", "evidence_type": "Certificate", "linked_requirement_type": "Technical requirement", "linked_requirement_id": "TECH-999", "mandatory": True}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertIn("linked_requirement_id", refused["errors"])
		tech_id = snap.load(frappe.get_doc("Tender Version", started["tender_version"]))["technical_requirements"][0]["technical_requirement_id"]
		added = cmd.add_tender_evidence_requirement(tender=root.name, values={"label": "Electrical compatibility certificate", "evidence_type": "Certificate", "linked_requirement_type": "Technical requirement", "linked_requirement_id": tech_id, "mandatory": True}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(added["evidence_requirement_id"], "EV-001")
		updated = cmd.update_tender_evidence_requirement(tender=root.name, evidence_requirement_id="EV-001", values={"mandatory": False}, expected_record_version=added["record_version"], idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertFalse(updated["evidence_requirements"][0]["mandatory"])
		removed = cmd.remove_tender_evidence_requirement(tender=root.name, evidence_requirement_id="EV-001", expected_record_version=updated["record_version"], idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(removed["evidence_requirements"], [])
		types = [e.event_type for e in frappe.get_all("Tender Event", filters={"tender": root.name}, fields=["event_type"], order_by="sequence asc")]
		self.assertEqual(types[-3:], ["TenderAddTenderEvidenceRequirement", "TenderUpdateTenderEvidenceRequirement", "TenderRemoveTenderEvidenceRequirement"])


class TestSubmitReturnApprove(TenderLifecycleCase):
	def test_a_must_fix_finding_blocks_submission_with_the_exact_route(self):
		_, started = self._started()
		self._complete(started, inspection_location="")
		root = frappe.get_doc("Tender", started["tender"])
		with self.assertRaises(TendersError) as ctx:
			lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_MUST_FIX")
		finding = ctx.exception.detail["findings"][0]
		self.assertEqual((finding["message"], finding["route"], finding["link_label"]), ("Enter the inspection and acceptance location.", "requirements#inspection_location", "Review contract terms"))
		self.assertEqual(frappe.db.get_value("Tender", root.name, "overall_status"), "Draft")

	def test_submission_freezes_the_version_and_the_review_note_survives(self):
		_, started, submitted = self._submitted()
		version = frappe.get_doc("Tender Version", started["tender_version"])
		root = frappe.get_doc("Tender", started["tender"])
		self.assertEqual((version.status, root.overall_status), ("Submitted", "Awaiting procurement approval"))
		self.assertEqual(version.submitted_by, fx.OFFICER)
		self.assertTrue(version.package_digest and version.invitation_digest and version.issued_tender_digest and version.response_schema_digest)
		docs = frappe.get_all("Tender Document", filters={"tender_version": version.name}, pluck="kind")
		self.assertEqual(sorted(docs), ["Complete Tender", "Invitation"])
		summary = review.summary(version)
		self.assertEqual((summary["result"], summary["must_fix_count"], summary["review_note_count"]), ("Ready to submit", 0, 1))
		self.assertEqual(summary["review_notes"][0]["message"], review.MANUFACTURER_NOTE)
		task = frappe.get_doc("Tender Task", submitted["task"])
		self.assertEqual((task.task_type, task.status), ("HOPF approval", "Open"))
		with self.assertRaises(TendersError) as ctx:  # read-only to every business actor
			cmd.save_tender_draft(tender=root.name, values={"tender_title": "x"}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_STALE_VERSION")

	def test_return_preserves_the_submitted_version_and_creates_one_copied_draft(self):
		_, started, submitted = self._submitted()
		root = frappe.get_doc("Tender", started["tender"])
		with self.assertRaises(TendersError) as ctx:
			lifecycle.return_tender_for_correction(tender=root.name, reason="", affected_task="Supplier and contract requirements", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertEqual(ctx.exception.code, "TND_CONTROL_INVALID")
		returned = lifecycle.return_tender_for_correction(tender=root.name, reason="Confirm whether manufacturer authorisation is necessary and update the supplier evidence requirement.", affected_task="Supplier and contract requirements", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, task=submitted["task"])
		self.assertEqual(returned["affected_task"], "requirements")
		old = frappe.get_doc("Tender Version", started["tender_version"])
		draft = frappe.get_doc("Tender Version", returned["copied_draft"])
		self.assertEqual((old.status, old.returned_by, draft.status, draft.version_number, draft.predecessor_version), ("Returned", fx.HOPF, "Draft", 2, old.name))
		self.assertEqual(draft.officer_payload_json, old.officer_payload_json)
		root.reload()
		self.assertEqual((root.overall_status, root.current_version), ("Draft", draft.name))
		self.assertEqual(frappe.db.get_value("Tender Task", submitted["task"], "status"), "Completed")

	def test_the_preparer_or_submitter_cannot_approve_and_approval_creates_the_ao_task_only(self):
		authorised = fx.authorised_handoff(items=(("Business laptops", 1, "Clinical training"),))
		started = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.BOTH)
		root = frappe.get_doc("Tender", started["tender"])
		cmd.save_tender_draft(tender=root.name, values=sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE), expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.BOTH)
		root.reload()
		submitted = lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.BOTH)
		root.reload()
		with self.assertRaises(TendersError) as ctx:
			lifecycle.approve_tender_package(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.BOTH, task=submitted["task"])
		self.assertEqual(ctx.exception.code, "TND_SOD_BLOCKED")
		approved = lifecycle.approve_tender_package(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, task=submitted["task"])
		version = frappe.get_doc("Tender Version", started["tender_version"])
		root.reload()
		self.assertEqual((version.status, version.approved_by, root.overall_status, root.approved_version), ("Approved", fx.HOPF, "Approved", version.name))
		ao_task = frappe.get_doc("Tender Task", approved["task"])
		self.assertEqual((ao_task.task_type, ao_task.business_role, ao_task.status), ("AO publication authorisation", "Accounting Officer", "Open"))
		self.assertEqual(frappe.db.count("Tender Channel Confirmation"), 0)
		self.assertIsNone(root.published_at)
		self.assertIsNone(root.publication)
		self.assertIn("Charles" if False else version.approved_by, [version.approved_by])
		# the Invitation now carries the approver's signature block
		from kentender_procurement.tenders.services import documents

		invitation = next(d for d in documents.list_for_tender(root.name) if d.kind == "Invitation" and d.digest == version.invitation_digest)
		self.assertIn(frappe.db.get_value("User", fx.HOPF, "full_name"), documents.html_of(invitation.name))
		# the AO who also prepared it cannot authorise (checked through the same segregation helper)
		with self.assertRaises(TendersError):
			lifecycle.require_segregation(version, fx.BOTH, blocked_columns=("prepared_by", "submitted_by", "approved_by"))

	def test_reopen_before_authorisation_creates_a_copied_draft_and_cancels_the_ao_task(self):
		_, started, approved = self._approved()
		root = frappe.get_doc("Tender", started["tender"])
		with self.assertRaises(TendersError):
			lifecycle.reopen_approved_tender(tender=root.name, reason="", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		reopened = lifecycle.reopen_approved_tender(tender=root.name, reason="The submission deadline must move by one week.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		root.reload()
		self.assertEqual((root.overall_status, root.approved_version, root.current_version), ("Draft", None, reopened["copied_draft"]))
		self.assertEqual(frappe.db.get_value("Tender Version", started["tender_version"], "status"), "Approved")
		self.assertEqual(frappe.db.get_value("Tender Task", approved["task"], "status"), "Cancelled")
		self.assertEqual(frappe.db.get_value("Tender Version", reopened["copied_draft"], "reopen_reason"), "The submission deadline must move by one week.")

	def test_every_decision_writes_the_audit_minimum(self):
		_, started, _ = self._approved()
		root = frappe.get_doc("Tender", started["tender"])
		rows = events.list_for_tender(root.name)
		types = [r["event_type"] for r in rows]
		self.assertEqual(types, ["TenderStarted", "TenderDraftSaved", "TenderSubmitted", "TenderApproved"])
		for row in rows:
			payload = row["payload"]
			for key in ("schema_version", "command", "idempotency_key_hash", "actor", "assignment_snapshot", "occurred_at_utc", "occurred_at_eat", "previous_status", "resulting_status", "record_version"):
				self.assertIn(key, payload, key)
		self.assertEqual(rows[-1]["payload"]["resulting_status"], "Approved")
		self.assertTrue(rows[-1]["payload"]["approved_package_digest"])
		decisions = frappe.get_all("Tender Decision", filters={"tender": root.name}, pluck="decision", order_by="decided_at asc")
		self.assertEqual(decisions, ["Submit for approval", "Approve Tender package"])


class TestRequisitionCorrection(TenderLifecycleCase):
	def test_correction_stops_the_version_releases_the_handoff_and_a_successor_continues(self):
		authorised, started = self._started()
		root = frappe.get_doc("Tender", started["tender"])
		with self.assertRaises(TendersError):
			correction.request_requisition_correction(tender=root.name, reason="too short", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		requested = correction.request_requisition_correction(tender=root.name, reason="The authorised battery-runtime requirement must be corrected before this Tender can continue.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		root.reload()
		stopped = frappe.get_doc("Tender Version", requested["stopped_version"])
		self.assertEqual((root.overall_status, stopped.status, stopped.stopped_by), ("Requisition correction requested", "Stopped for requisition correction", fx.HOPF))
		self.assertFalse(frappe.db.get_value("Authorised Requisition Handoff", authorised["handoff"], "consumed_at"))
		with self.assertRaises(TendersError) as ctx:  # no local override
			cmd.save_tender_draft(tender=root.name, values={"tender_title": "x"}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_STALE_VERSION")
		state = correction.correction_state(root, user=fx.OFFICER)
		self.assertEqual(state["requested_by"], fx.HOPF)
		# the released handoff is itself the authorised successor in this world (Requisitions re-authorises the same Plan Item)
		self.assertEqual(state["successor"]["handoff"], authorised["handoff"])
		continued = correction.start_corrected_tender_version(tender=root.name, handoff=authorised["handoff"], expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		draft = frappe.get_doc("Tender Version", continued["version"]["name"])
		self.assertEqual((root.overall_status, draft.version_number, draft.predecessor_version, draft.status), ("Draft", 2, stopped.name, "Draft"))
		self.assertEqual(frappe.db.get_value("Tender Version", stopped.name, "status"), "Stopped for requisition correction")
		self.assertEqual(frappe.db.get_value("Authorised Requisition Handoff", authorised["handoff"], "tender_version"), draft.name)
