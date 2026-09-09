# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §10.4 — an inherited requirement is never edited here;
the correction route stops the Version, releases the handoff, and a new
authorised handoff is required (TPR-AC-028, SMOKE-13; plan D20)."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.tender_preparation.services import draft_commands as cmd
from kentender_procurement.tender_preparation.services import lifecycle
from kentender_procurement.tender_preparation.services.errors import TenderPreparationError
from kentender_procurement.tender_preparation.tests import fixtures as fx
from kentender_procurement.tender_preparation.tests.base import TenderCase


class TestUpstreamCorrection(TenderCase):
	def test_the_stopped_version_is_preserved_and_the_handoff_released(self):
		prep = fx.prepared()
		fx.complete_draft(prep["tender"])
		version_before = frappe.get_doc("Tender Preparation Version", prep["tender_version"])
		snapshot_before = version_before.snapshot_json
		frappe.set_user(fx.OFFICER)
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		result = lifecycle.request_tender_upstream_correction(tender=prep["tender"], reason="The authorised technical requirement for this item's battery specification must be corrected in the Requisition.", expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "upstream_correction_required")
		self.assertEqual(result["handoff_release"], "released")
		version = frappe.get_doc("Tender Preparation Version", prep["tender_version"])
		self.assertEqual(version.version_status, "Upstream correction required")
		self.assertEqual(version.snapshot_json, snapshot_before)
		root.reload()
		self.assertEqual(root.current_state, "Upstream correction required")
		handoff = frappe.get_doc("Authorised Requisition Handoff", root.requisition_handoff)
		self.assertFalse(handoff.consumed_at)
		self.assertEqual(handoff.tender, "")
		# the stopped Tender accepts no further edits
		with self.assertRaises(TenderPreparationError) as ctx:
			cmd.save_tender_draft(tender=prep["tender"], values={"tender_title": "after stop"}, expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_STALE_VERSION")

	def test_a_new_tender_is_required_from_a_new_handoff_and_links_its_predecessor_by_reference(self):
		prep = fx.prepared()
		frappe.set_user(fx.OFFICER)
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		lifecycle.request_tender_upstream_correction(tender=prep["tender"], reason="Correct the memory requirement upstream in the Requisition.", expected_record_version=root.record_version, idempotency_key=fx.key())
		# the released handoff is eligible again and a fresh Tender starts from it as a new record (D20)
		frappe.set_user(fx.OFFICER)
		again = cmd.prepare_tender(handoff=root.requisition_handoff, idempotency_key=fx.key())
		self.assertEqual(again["action"], "created")
		self.assertNotEqual(again["tender"], prep["tender"])
		new_root = frappe.get_doc("Prepared Tender", again["tender"])
		self.assertTrue(new_root.tender_reference.endswith("-2"))
		self.assertEqual(json.loads(frappe.get_doc("Tender Preparation Version", again["tender_version"]).snapshot_json)["handoff"], root.requisition_handoff)

	def test_a_submitted_version_can_also_be_stopped_and_its_task_cancelled(self):
		sub = fx.submitted()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Prepared Tender", sub["tender"])
		result = lifecycle.request_tender_upstream_correction(tender=sub["tender"], reason="The Requisition's delivery date must be corrected before this Tender can proceed.", expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "upstream_correction_required")
		self.assertEqual(frappe.db.get_value("Tender Preparation Task", sub["task"], "status"), "Cancelled")
		self.assertEqual(frappe.db.get_value("Tender Preparation Decision", result["decision"], "legal_capacity"), "Head of Procurement Function")

	def test_an_auditor_cannot_request_it_and_a_reason_is_required(self):
		prep = fx.prepared()
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		frappe.set_user(fx.AUDITOR)
		with self.assertRaises(frappe.DoesNotExistError):
			lifecycle.request_tender_upstream_correction(tender=prep["tender"], reason="An auditor has no business transition here.", expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.OFFICER)
		with self.assertRaises(TenderPreparationError) as ctx:
			lifecycle.request_tender_upstream_correction(tender=prep["tender"], reason="short", expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_CONTROL_INVALID")
