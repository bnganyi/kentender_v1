# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WG-03 Document Preview + Publication Handoff API contract tests."""

from __future__ import annotations

import json

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import cstr

from kentender_procurement.tender_configurations.constants import (
	STATUS_APPROVED_FOR_PREVIEW,
	STATUS_COMPLETED,
	STATUS_READY_FOR_PUBLICATION,
	STATUS_RETURNED_FOR_CORRECTION,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.document_preview import (
	confirm_document_preview,
	download_document_preview_pdf,
	generate_document_preview,
	get_document_preview,
	return_preview_for_correction,
	send_to_publication_workflow,
)
from kentender_procurement.tender_configurations.services.eligibility import (
	ensure_fixture_std_version,
)


def _approve(cfg_id: str):
	doc = frappe.get_doc("Tender Configuration", cfg_id)
	doc.status = STATUS_APPROVED_FOR_PREVIEW
	doc.review_workspace = json.dumps(
		{"approved_at": "2026-07-19 11:00:00", "approved_by": "Administrator", "checklist": []}
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()


def _seed_bidder_facing_config(cfg_id: str):
	"""Populate CFG blobs so required preview sections can render legally."""
	doc = frappe.get_doc("Tender Configuration", cfg_id)
	doc.tds_values = json.dumps(
		{
			"contact_officer": "Jane Doe",
			"contact_email": "procurement@example.go.ke",
			"clarification_submission_method": "E-Procurement Portal",
			"clarification_deadline": "2026-08-30T15:30",
			"pre_tender_meeting": "No",
			"tender_submission_deadline": "2026-09-15T17:00",
			"tender_opening_datetime": "2026-09-15T17:30",
			"bid_validity_period": "120",
			"bid_validity_unit": "days",
			"submission_channel": "E-Procurement Portal",
			"submission_language": "English",
			"tender_currency": "KES",
			"tender_security_required": "Yes",
			"tender_security_amount": "50000",
			"tender_security_currency": "KES",
			"tender_security_validity_period": "14",
			"tender_security_validity_unit": "days",
			"margin_of_preference_applies": "No",
			"opening_method": "Electronic Opening",
			"opening_location": "KenTender portal",
			"opening_attendance_allowed": "Yes",
		}
	)
	doc.it_requirements = json.dumps(
		[
			{
				"requirement_id": "REQ-001",
				"title": "Helpdesk Service Continuity",
				"description": "Support continuous helpdesk operations with defined SLAs.",
				"category_label": "Business Objective",
				"treatment_label": "Mandatory",
			},
			{
				"requirement_id": "REQ-002",
				"title": "Compute Node Performance",
				"description": "Compute nodes must meet the stated processor and memory requirements.",
				"category_label": "Technical Requirement",
				"treatment_label": "Mandatory",
			},
		]
	)
	doc.evaluation_setup = json.dumps(
		{
			"criteria": [
				{
					"criterion_name": "Tender security submitted",
					"stage": "Preliminary",
					"evaluation_basis": "Pass/Fail",
					"pass_fail_rule": "Must be submitted in required form and amount",
					"bidder_evidence": "Required",
				},
				{
					"criterion_name": "Technical compliance for: REQ-002",
					"stage": "Technical",
					"evaluation_basis": "Scored",
					"marks": "50",
					"related_requirement_id": "REQ-002",
					"bidder_evidence": "Required",
				},
			]
		}
	)
	doc.price_schedule = json.dumps(
		{
			"items": [
				{
					"item_name": "Price for requirement: REQ-002",
					"related_requirement_id": "REQ-002",
					"bidder_facing_description": (
						"Supply, install, and commission compute nodes meeting the "
						"specified performance requirement."
					),
					"unit": "Lot",
					"quantity": "1",
					"currency": "KES",
				}
			]
		}
	)
	doc.system_inventory = json.dumps({"not_applicable": 1, "items": []})
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()


class TestConfigurationDocumentPreviewApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_fixture_std_version()
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)

	def test_get_before_generate(self):
		out = get_document_preview(self.cfg_id)
		self.assertEqual(out["preview_status"], "Not generated")
		self.assertFalse(out["show_publication_package"])

	def test_generate_includes_std_locked_content(self):
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen["preview_status"], "Generated", gen.get("render_exception"))
		self.assertIn("PREVIEW", gen["preview_html"])
		self.assertEqual(len(gen["outline"]), 13)
		self.assertNotIn("Standard ITT text.", gen["preview_html"])
		self.assertNotIn("Standard GCC text.", gen["preview_html"])
		self.assertNotIn("Fixture locked", gen["preview_html"])
		self.assertNotIn("No configured rows.", gen["preview_html"])
		self.assertNotIn("Locked standard text from bound STD version.", gen["preview_html"])
		self.assertNotIn("contact_officer", gen["preview_html"])
		self.assertNotIn("No additional requirements are specified under this section.", gen["preview_html"])
		self.assertIn("Contact officer", gen["preview_html"])
		self.assertIn("KES 50,000", gen["preview_html"])
		self.assertIn("30 August 2026", gen["preview_html"])
		self.assertIn("Compute Node Performance technical compliance", gen["preview_html"])
		self.assertIn("Scored out of 50 marks", gen["preview_html"])
		self.assertIn("[Bidder to complete]", gen["preview_html"])
		self.assertIn("Helpdesk Service Continuity", gen["preview_html"])
		# Requirements split: business in IS section, technical in Technical section — not duplicated titles across both as same table dump
		self.assertNotIn("Technical compliance for:", gen["preview_html"])
		self.assertNotIn("Price for requirement:", gen["preview_html"])
		self.assertNotIn(">REQ-002<", gen["preview_html"])
		self.assertIn("not applicable", gen["preview_html"].lower())
		self.assertIn("Instructions to Tenderers", gen["preview_html"])
		self.assertIn("tenderer shall prepare", gen["preview_html"].lower())
		self.assertIn('id="sec-itt"', gen["preview_html"])
		self.assertIn('id="sec-gcc"', gen["preview_html"])
		self.assertTrue(gen.get("render_hashes", {}).get("itt"))
		self.assertTrue(gen.get("render_hashes", {}).get("gcc"))
		self.assertFalse(gen.get("render_exception"))

	def test_exception_when_required_tds_empty(self):
		frappe.db.set_value("Tender Configuration", self.cfg_id, "tds_values", "{}")
		frappe.db.commit()
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen["preview_status"], "Exception found")
		self.assertIn("Readiness issue", gen.get("render_exception") or "")

	def test_exception_when_std_version_missing(self):
		frappe.db.set_value("Tender Configuration", self.cfg_id, "std_version", None)
		frappe.db.commit()
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen["preview_status"], "Exception found")
		self.assertTrue(gen.get("render_exception"))

	def test_generate_confirm_send(self):
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen["preview_status"], "Generated", gen.get("render_exception"))

		conf = confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
		self.assertEqual(conf["preview_status"], "Confirmed")
		self.assertTrue(conf["show_publication_package"])
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_READY_FOR_PUBLICATION)

		sent = send_to_publication_workflow(self.cfg_id)
		self.assertTrue(sent.get("sent"))
		doc.reload()
		self.assertEqual(doc.status, STATUS_COMPLETED)
		pkg = json.loads(doc.publication_package)
		self.assertTrue(pkg.get("sent_at"))

	def test_confirm_requires_flag(self):
		generate_document_preview(self.cfg_id)
		with self.assertRaises(Exception):
			confirm_document_preview(self.cfg_id, {})

	def test_regenerate_invalidates_confirmed(self):
		generate_document_preview(self.cfg_id)
		confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_READY_FOR_PUBLICATION)

		regen = generate_document_preview(self.cfg_id)
		self.assertEqual(regen["preview_status"], "Generated")
		self.assertEqual(regen["user_confirmed"], 0)
		doc.reload()
		self.assertEqual(doc.status, STATUS_APPROVED_FOR_PREVIEW)
		self.assertFalse(doc.publication_package)

	def test_return_for_correction_requires_fields_and_clears_preview(self):
		generate_document_preview(self.cfg_id)
		with self.assertRaises(Exception):
			return_preview_for_correction(self.cfg_id, {"affected_section": "ITT"})
		out = return_preview_for_correction(
			self.cfg_id,
			{
				"affected_section": "Instructions to Tenderers",
				"reason": "ITT clause wording incorrect",
				"severity": "High",
				"owning_cfg_step": "CFG-02",
			},
		)
		self.assertTrue(out.get("returned"))
		self.assertEqual(out["preview_status"], "Not generated")
		self.assertFalse(out.get("preview_html"))
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_RETURNED_FOR_CORRECTION)
		blob = json.loads(doc.document_preview)
		self.assertEqual(blob["return"]["severity"], "High")
		self.assertEqual(blob["return"]["owning_cfg_step"], "CFG-02")

	def test_download_preview_pdf(self):
		generate_document_preview(self.cfg_id)
		download_document_preview_pdf(self.cfg_id)
		content = frappe.local.response.filecontent
		self.assertTrue(content)
		self.assertTrue(bytes(content).startswith(b"%PDF"))
		self.assertIn(".pdf", cstr(frappe.local.response.filename))
