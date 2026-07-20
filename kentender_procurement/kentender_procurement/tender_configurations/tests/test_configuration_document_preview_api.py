# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WG-03 Document Preview + Publication Handoff API contract tests."""

from __future__ import annotations

import json

import unittest

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.constants import (
	STATUS_APPROVED_FOR_PREVIEW,
	STATUS_READY_FOR_PUBLICATION,
	STATUS_RETURNED_FOR_CORRECTION,
	STATUS_SENT_TO_PUBLICATION,
)
from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
	PACKAGE_DOCTYPE,
	PUBLICATION_DOCTYPE,
	PACKAGE_STATUS_AWAITING,
	PACKAGE_STATUS_INVALIDATED,
	PUBLICATION_STATUS_RETURNED,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.document_preview import (
	confirm_document_preview,
	download_document_preview_pdf,
	generate_document_preview,
	get_document_preview,
	return_preview_for_correction,
	send_to_publication_workflow,
)  # get_document_preview used by F1 lock assertions
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.services.ensure_active_canonical_std import (
	ensure_active_canonical_ppra_it_std,
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
	doc.contract_values = json.dumps(
		{
			"contract_values": [
				{
					"contract_value_id": "SCC-01",
					"item_label": "Governing law",
					"value_or_obligation": "Governing law: Laws of Kenya",
				},
				{
					"contract_value_id": "SCC-02",
					"item_label": "Scope",
					"value_or_obligation": "Scope: All modules in Part 2",
				},
				{
					"contract_value_id": "SCC-03",
					"item_label": "Commencement",
					"value_or_obligation": (
						"Commencement within 14 days; 24 month implementation period"
					),
				},
				{
					"contract_value_id": "SCC-04",
					"item_label": "Payment",
					"value_or_obligation": "Milestone payment schedule as agreed",
				},
				{
					"contract_value_id": "SCC-05",
					"item_label": "Source code / escrow",
					"value_or_obligation": "Source code escrow within 30 days",
				},
				{
					"contract_value_id": "SCC-06",
					"item_label": "Subcontracting",
					"value_or_obligation": "Subcontracting requires prior written approval",
				},
				{
					"contract_value_id": "SCC-07",
					"item_label": "SLA",
					"value_or_obligation": "P1 response 4 hours / resolution 24 hours",
				},
				{
					"contract_value_id": "SCC-08",
					"item_label": "Performance security",
					"value_or_obligation": "10% performance security of Contract Price",
				},
				{
					"contract_value_id": "SCC-09",
					"item_label": "Warranty",
					"value_or_obligation": "Twelve-month warranty after go-live",
				},
			]
		}
	)
	doc.system_inventory = json.dumps({"not_applicable": 1, "items": []})
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()


class TestConfigurationDocumentPreviewApi(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		ensure_active_canonical_ppra_it_std(force_reimport=False)
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			"std_version",
			CANONICAL_PACKAGE_ID,
		)
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
		self.assertIn("Electronic price entry", gen["preview_html"])
		self.assertIn("Helpdesk Service Continuity", gen["preview_html"])
		# Requirements split: business in IS section, technical in Technical section — not duplicated titles across both as same table dump
		self.assertNotIn("Technical compliance for:", gen["preview_html"])
		self.assertNotIn("Price for requirement:", gen["preview_html"])
		# REQ-* may appear only in Requirement ID matrix cells, not as headings/titles.
		self.assertNotIn("<h3>REQ-002</h3>", gen["preview_html"])
		self.assertNotIn("<td>REQ-002</td>", gen["preview_html"])
		self.assertIn('data-col="requirement-id">REQ-002<', gen["preview_html"])
		self.assertIn("not applicable", gen["preview_html"].lower())
		self.assertIn("Instructions to Tenderers", gen["preview_html"])
		self.assertIn("scope of tender", gen["preview_html"].lower())
		self.assertNotIn("tenderer shall prepare the tender in accordance", gen["preview_html"].lower())
		self.assertIn('id="sec-itt"', gen["preview_html"])
		self.assertIn('id="sec-gcc"', gen["preview_html"])
		self.assertIn('id="sec-forms"', gen["preview_html"])
		self.assertTrue(gen.get("render_hashes", {}).get("itt"))
		self.assertTrue(gen.get("render_hashes", {}).get("gcc"))
		self.assertTrue(gen.get("render_hashes", {}).get("forms"))
		self.assertFalse(gen.get("render_exception"))

	def test_exception_when_required_tds_empty(self):
		frappe.db.set_value("Tender Configuration", self.cfg_id, "tds_values", "{}")
		frappe.db.commit()
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen["preview_status"], "Exception found")
		self.assertFalse(gen.get("preview_html"))
		self.assertFalse(gen.get("can_download_preview_pdf"))
		block = gen.get("generation_block") or {}
		self.assertEqual(block.get("status"), "generation_blocked")
		self.assertIn("CFG-02", block.get("blocking_area") or "")
		self.assertNotIn("Readiness issue:", gen.get("preview_html") or "")

	def test_exception_does_not_embed_diagnostics_in_html(self):
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			"system_inventory",
			json.dumps({"items": []}),
		)
		frappe.db.commit()
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen["preview_status"], "Exception found")
		self.assertEqual(gen.get("preview_html") or "", "")
		block = gen.get("generation_block") or {}
		self.assertIn("CFG-05", block.get("blocking_area") or "")
		self.assertEqual(block.get("owner_step"), "CFG-05")
		self.assertEqual(
			block.get("owner_route"),
			"it-tender-configuration-system-inventory",
		)
		self.assertIn("CFG-05", block.get("cta_label") or "")
		self.assertIn("no bidder-facing content", (block.get("message") or "").lower())
		ctx = gen.get("context") or {}
		self.assertIn("Preview blocked", ctx.get("issues_label") or "")
		self.assertEqual(ctx.get("issues_alert"), 1)
		with self.assertRaises(Exception):
			download_document_preview_pdf(self.cfg_id)

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
		self.assertEqual(conf["preview_status_label"], "Preview Confirmed")
		self.assertTrue(conf["show_publication_package"])
		self.assertFalse(conf["can_regenerate_preview"])
		self.assertEqual(conf.get("download_pdf_label"), "Download Confirmed PDF")
		self.assertTrue(conf.get("document_hash"))
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_READY_FOR_PUBLICATION)
		self.assertTrue(doc.confirmed_document_package)
		pkg_doc = frappe.get_doc(PACKAGE_DOCTYPE, doc.confirmed_document_package)
		self.assertEqual(pkg_doc.document_hash, conf.get("document_hash"))
		self.assertTrue(pkg_doc.bidder_submission_schema or pkg_doc.evaluation_schema)
		self.assertTrue(pkg_doc.contract_carry_forward)
		self.assertTrue(pkg_doc.preview_confirmation)

		sent = send_to_publication_workflow(self.cfg_id)
		self.assertTrue(sent.get("sent"))
		doc.reload()
		self.assertEqual(doc.status, STATUS_SENT_TO_PUBLICATION)
		pkg = json.loads(doc.publication_package)
		self.assertTrue(pkg.get("sent_at"))
		self.assertTrue(pkg.get("document_hash"))
		self.assertTrue(doc.it_publication_record)
		pub = frappe.get_doc(PUBLICATION_DOCTYPE, doc.it_publication_record)
		self.assertEqual(pub.status, "Awaiting Publication Setup")
		self.assertEqual(pub.confirmed_package, doc.confirmed_document_package)
		pkg_doc.reload()
		self.assertEqual(pkg_doc.package_status, PACKAGE_STATUS_AWAITING)

	def test_confirm_requires_flag(self):
		generate_document_preview(self.cfg_id)
		with self.assertRaises(Exception):
			confirm_document_preview(self.cfg_id, {})

	def test_regenerate_blocked_after_confirm(self):
		generate_document_preview(self.cfg_id)
		confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_READY_FOR_PUBLICATION)
		with self.assertRaises(Exception):
			generate_document_preview(self.cfg_id)
		dto = get_document_preview(self.cfg_id)
		self.assertFalse(dto["can_regenerate_preview"])
		self.assertEqual(dto["preview_status"], "Confirmed")

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

	def test_return_after_send_invalidates_package_and_publication(self):
		generate_document_preview(self.cfg_id)
		confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
		send_to_publication_workflow(self.cfg_id)
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		pkg_name = doc.confirmed_document_package
		pub_name = doc.it_publication_record
		self.assertTrue(pkg_name and pub_name)

		out = return_preview_for_correction(
			self.cfg_id,
			{
				"affected_section": "Special Conditions of Contract",
				"reason": "SCC payment milestone incorrect",
				"severity": "High",
				"owning_cfg_step": "CFG-09",
			},
		)
		self.assertTrue(out.get("returned"))
		doc.reload()
		self.assertEqual(doc.status, STATUS_RETURNED_FOR_CORRECTION)
		self.assertFalse(doc.confirmed_document_package)
		self.assertFalse(doc.it_publication_record)
		self.assertFalse(doc.readiness_report)
		self.assertFalse(doc.review_workspace)
		pkg = frappe.get_doc(PACKAGE_DOCTYPE, pkg_name)
		self.assertEqual(pkg.package_status, PACKAGE_STATUS_INVALIDATED)
		pub = frappe.get_doc(PUBLICATION_DOCTYPE, pub_name)
		self.assertEqual(pub.status, PUBLICATION_STATUS_RETURNED)

	def test_locked_configuration_rejects_tds_edit(self):
		from kentender_procurement.tender_configurations.services.tds import (
			save_configuration_tds,
		)

		generate_document_preview(self.cfg_id)
		confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
		with self.assertRaises(Exception):
			save_configuration_tds(
				self.cfg_id,
				{"contact_officer": "Should Not Persist"},
			)

	def test_download_preview_pdf(self):
		generate_document_preview(self.cfg_id)
		download_document_preview_pdf(self.cfg_id)
		content = frappe.local.response.filecontent
		self.assertTrue(content)
		self.assertTrue(bytes(content).startswith(b"%PDF"))
		self.assertIn(".pdf", cstr(frappe.local.response.filename))
