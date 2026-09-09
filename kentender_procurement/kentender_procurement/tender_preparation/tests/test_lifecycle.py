# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §10.2 — submit, return, reopen and the immutability of
every non-Draft Version (TPR-AC-024/025/027/029, SMOKE-09/12)."""

from __future__ import annotations

import frappe

from kentender_procurement.tender_preparation.services import lifecycle, publication
from kentender_procurement.tender_preparation.services.errors import TenderPreparationError
from kentender_procurement.tender_preparation.tests import fixtures as fx
from kentender_procurement.tender_preparation.tests.base import TenderCase


class TestSubmit(TenderCase):
	def test_submit_locks_the_version_and_opens_one_hopf_task(self):
		sub = fx.submitted()
		version = frappe.get_doc("Tender Preparation Version", sub["tender_version"])
		self.assertEqual(version.version_status, "Submitted")
		self.assertEqual(version.submitted_by, fx.OFFICER)
		self.assertTrue(version.content_digest)
		root = frappe.get_doc("Prepared Tender", sub["tender"])
		self.assertEqual(root.current_state, "Submitted for approval")
		tasks = frappe.get_all("Tender Preparation Task", filters={"tender": root.name, "status": "Open"}, fields=["business_role"])
		self.assertEqual([t.business_role for t in tasks], ["Head of Procurement Function"])

	def test_submit_with_blocking_findings_is_refused(self):
		prep = fx.prepared()
		frappe.set_user(fx.OFFICER)
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		with self.assertRaises(TenderPreparationError) as ctx:
			lifecycle.submit_tender_for_approval(tender=prep["tender"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_BLOCKING_FINDINGS")
		self.assertTrue(ctx.exception.detail["findings"])
		self.assertEqual(frappe.db.get_value("Prepared Tender", prep["tender"], "current_state"), "Draft")

	def test_a_submitted_version_is_immutable_in_place(self):
		"""TPR-AC-029 — no lifecycle flag, no edit."""
		sub = fx.submitted()
		version = frappe.get_doc("Tender Preparation Version", sub["tender_version"])
		version.tender_title = "Edited after submission"
		with self.assertRaises(frappe.ValidationError):
			version.save(ignore_permissions=True)
		version.reload()
		version.snapshot_json = "{}"
		with self.assertRaises(frappe.ValidationError):
			version.save(ignore_permissions=True)


class TestReturn(TenderCase):
	def test_return_preserves_the_submitted_version_and_opens_draft_version_2(self):
		"""SMOKE-09 / TPR-AC-025."""
		sub = fx.submitted()
		before = frappe.get_doc("Tender Preparation Version", sub["tender_version"])
		digest_before = before.content_digest
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Prepared Tender", sub["tender"])
		result = lifecycle.return_tender_for_correction(task=sub["task"], reason="Confirm whether manufacturer authorisation is necessary and update the evidence requirement.", expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "returned")
		returned = frappe.get_doc("Tender Preparation Version", sub["tender_version"])
		self.assertEqual(returned.version_status, "Returned")
		self.assertEqual(returned.content_digest, digest_before)
		self.assertEqual(returned.tender_title, fx.TASK1["tender_title"])
		successor = frappe.get_doc("Tender Preparation Version", result["tender_version"])
		self.assertEqual(successor.version_number, 2)
		self.assertEqual(successor.version_status, "Draft")
		self.assertEqual(successor.based_on_version, returned.name)
		self.assertEqual(successor.snapshot_digest, returned.snapshot_digest)
		self.assertEqual(successor.tender_title, returned.tender_title)
		root.reload()
		self.assertEqual((root.current_state, root.current_version), ("Draft", successor.name))
		self.assertEqual(frappe.db.get_value("Tender Preparation Task", sub["task"], "status"), "Completed")
		decision = frappe.get_doc("Tender Preparation Decision", result["decision"])
		self.assertEqual((decision.decision, decision.actor), ("Return for correction", fx.HOPF))

	def test_return_requires_a_reason_and_the_head_of_procurement_function(self):
		sub = fx.submitted()
		root = frappe.get_doc("Prepared Tender", sub["tender"])
		frappe.set_user(fx.HOPF)
		with self.assertRaises(TenderPreparationError) as ctx:
			lifecycle.return_tender_for_correction(task=sub["task"], reason="short", expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_CONTROL_INVALID")
		frappe.set_user(fx.OFFICER)
		with self.assertRaises(frappe.DoesNotExistError):
			lifecycle.return_tender_for_correction(task=sub["task"], reason="The officer may not return a Tender.", expected_record_version=root.record_version, idempotency_key=fx.key())

	def test_the_corrected_successor_can_be_resubmitted_and_approved(self):
		sub = fx.submitted()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Prepared Tender", sub["tender"])
		returned = lifecycle.return_tender_for_correction(task=sub["task"], reason="Please confirm the submission deadline before approval.", expected_record_version=root.record_version, idempotency_key=fx.key())
		fx.complete_draft(sub["tender"], overrides={"tender_title": "Supply and delivery of business laptops (corrected)"})
		frappe.set_user(fx.OFFICER)
		root.reload()
		resubmitted = lifecycle.submit_tender_for_approval(tender=sub["tender"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOPF)
		root.reload()
		approved = lifecycle.approve_tender_for_publication(task=resubmitted["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(approved["tender_version"], returned["tender_version"])
		self.assertEqual(frappe.db.get_value("Tender Preparation Version", approved["tender_version"], "version_number"), 2)


class TestReopen(TenderCase):
	def test_reopen_is_allowed_before_consumption_and_refused_after(self):
		"""SMOKE-12 / TPR-AC-027."""
		app = fx.approved()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Prepared Tender", app["tender"])
		result = lifecycle.reopen_approved_tender(tender=app["tender"], reason="The submission deadline must be corrected before publication.", expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "reopened")
		self.assertEqual(frappe.db.get_value("Tender Preparation Version", app["tender_version"], "version_status"), "Reopened")
		self.assertEqual(frappe.db.get_value("Tender Publication Handoff", app["publication_handoff"], "status"), "Cancelled")
		root.reload()
		self.assertEqual(root.current_state, "Draft")
		self.assertFalse(root.approved_version)
		successor = frappe.get_doc("Tender Preparation Version", result["tender_version"])
		self.assertEqual(successor.version_number, 2)
		# approve again, then consume, then reopen must be refused
		fx.complete_draft(app["tender"])
		frappe.set_user(fx.OFFICER)
		root.reload()
		resub = lifecycle.submit_tender_for_approval(tender=app["tender"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOPF)
		root.reload()
		lifecycle.approve_tender_for_publication(task=resub["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user("Administrator")
		publication.acknowledge_publication_consumed(tender=app["tender"], correlation_id=fx.key(), published_on="2102-02-01")
		frappe.set_user(fx.HOPF)
		root.reload()
		with self.assertRaises(TenderPreparationError) as ctx:
			lifecycle.reopen_approved_tender(tender=app["tender"], reason="Too late to reopen this Tender.", expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_PUBLICATION_CONSUMED")

	def test_reopen_never_edits_the_approved_version(self):
		app = fx.approved()
		before = frappe.get_doc("Tender Preparation Version", app["tender_version"])
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Prepared Tender", app["tender"])
		lifecycle.reopen_approved_tender(tender=app["tender"], reason="Reopened to prove the approved Version is untouched.", expected_record_version=root.record_version, idempotency_key=fx.key())
		after = frappe.get_doc("Tender Preparation Version", app["tender_version"])
		self.assertEqual(after.content_digest, before.content_digest)
		self.assertEqual(after.tender_title, before.tender_title)
		self.assertEqual(after.snapshot_json, before.snapshot_json)
