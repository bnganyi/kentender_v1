# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §10.2/§10.3/§10.5 — approval: segregation from the
Version's own audit event against a user holding both responsibilities
(TPR-AC-023, SMOKE-10), one atomic commit of decision, Version, package,
files and handoff (TPR-AC-026), idempotent retry (SMOKE-11), the handoff
contents (TPR-AC-035/038) and the single approval level (TPR-AC-024)."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.tender_preparation.services import lifecycle
from kentender_procurement.tender_preparation.services.errors import TenderPreparationError
from kentender_procurement.tender_preparation.tests import fixtures as fx
from kentender_procurement.tender_preparation.tests.base import TenderCase


class TestApprove(TenderCase):
	def test_the_preparer_cannot_approve_even_when_holding_both_responsibilities(self):
		"""SMOKE-10 / TPR-AC-023."""
		sub = fx.submitted(user=fx.BOTH)
		frappe.set_user(fx.BOTH)
		root = frappe.get_doc("Prepared Tender", sub["tender"])
		with self.assertRaises(TenderPreparationError) as ctx:
			lifecycle.approve_tender_for_publication(task=sub["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_SOD_BLOCKED")
		frappe.set_user(fx.HOPF)
		result = lifecycle.approve_tender_for_publication(task=sub["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "approved")

	def test_approval_commits_decision_version_package_files_and_handoff(self):
		app = fx.approved()
		root = frappe.get_doc("Prepared Tender", app["tender"])
		self.assertEqual(root.current_state, "Approved for publication")
		self.assertEqual(root.approved_version, app["tender_version"])
		version = frappe.get_doc("Tender Preparation Version", app["tender_version"])
		self.assertEqual(version.version_status, "Approved")
		self.assertEqual(version.decided_by, fx.HOPF)
		handoff = frappe.get_doc("Tender Publication Handoff", app["publication_handoff"])
		self.assertEqual((handoff.status, handoff.handoff_version), ("Ready", "1.1"))
		package = json.loads(handoff.package_json)
		for key in ("binding", "inherited_snapshot", "officer_values", "evidence_requirements", "generated", "renders", "readiness", "approval"):
			self.assertIn(key, package)
		for key in ("supplier_response_schema", "evaluation_contract", "contract_obligations", "price_schedule", "goods"):
			self.assertIn(key, package["generated"])
		self.assertNotEqual(handoff.invitation_digest, handoff.issued_tender_digest)
		self.assertEqual(package["renders"]["invitation_digest"], handoff.invitation_digest)
		for field in ("invitation_html_file", "issued_tender_html_file", "invitation_pdf_file", "issued_tender_pdf_file"):
			name = handoff.get(field)
			self.assertTrue(name, field)
			self.assertEqual(frappe.db.get_value("File", name, "is_private"), 1)
		self.assertEqual(frappe.db.get_value("Tender Preparation Task", app["task"], "status"), "Completed")
		self.assertEqual(frappe.db.count("Tender Preparation Decision", {"tender": root.name, "decision": "Approve for publication"}), 1)
		self.assertEqual(frappe.db.count("Tender Preparation Event", {"tender": root.name, "event_type": "TenderPublicationHandoffReady.v1"}), 1)
		# the approval block reached the rendered Invitation, the internal context did not
		html = frappe.get_doc("File", handoff.invitation_html_file).get_content()
		self.assertIn("Head of Procurement Function", html)
		self.assertNotIn("strategic", html.lower())

	def test_a_retry_with_the_same_key_creates_no_duplicate(self):
		"""SMOKE-11."""
		sub = fx.submitted()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Prepared Tender", sub["tender"])
		k = fx.key()
		first = lifecycle.approve_tender_for_publication(task=sub["task"], expected_record_version=root.record_version, idempotency_key=k)
		second = lifecycle.approve_tender_for_publication(task=sub["task"], expected_record_version=root.record_version, idempotency_key=k)
		self.assertTrue(second["idempotent"])
		self.assertEqual(first["publication_handoff"], second["publication_handoff"])
		self.assertEqual(frappe.db.count("Tender Publication Handoff", {"tender": sub["tender"]}), 1)
		self.assertEqual(frappe.db.count("File", {"attached_to_name": first["publication_handoff"]}), 4)

	def test_a_failure_after_the_decision_leaves_nothing_behind(self):
		"""TPR-AC-026 — forced failure inside the savepoint."""
		sub = fx.submitted()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Prepared Tender", sub["tender"])

		def boom():
			raise RuntimeError("forced failure after the decision insert")

		lifecycle._after_decision_hook = boom
		self.addCleanup(setattr, lifecycle, "_after_decision_hook", None)
		with self.assertRaises(RuntimeError):
			lifecycle.approve_tender_for_publication(task=sub["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(frappe.db.count("Tender Preparation Decision", {"tender": sub["tender"]}), 0)
		self.assertEqual(frappe.db.count("Tender Publication Handoff", {"tender": sub["tender"]}), 0)
		self.assertEqual(frappe.db.count("Tender Preparation Event", {"tender": sub["tender"]}), 0)
		self.assertEqual(frappe.db.get_value("Prepared Tender", sub["tender"], "current_state"), "Submitted for approval")
		self.assertEqual(frappe.db.get_value("Tender Preparation Version", sub["tender_version"], "version_status"), "Submitted")
		self.assertEqual(frappe.db.get_value("Tender Preparation Task", sub["task"], "status"), "Open")

	def test_only_the_head_of_procurement_function_approves(self):
		"""TPR-AC-024 — no second approver, no auditor, no officer."""
		sub = fx.submitted()
		root = frappe.get_doc("Prepared Tender", sub["tender"])
		for user in (fx.OFFICER, fx.AUDITOR, fx.OUTSIDER):
			frappe.set_user(user)
			with self.assertRaises(frappe.DoesNotExistError, msg=user):
				lifecycle.approve_tender_for_publication(task=sub["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		roles = {r.business_role for r in frappe.get_all("Tender Preparation Task", fields=["business_role"])}
		self.assertEqual(roles, {"Head of Procurement Function"})
