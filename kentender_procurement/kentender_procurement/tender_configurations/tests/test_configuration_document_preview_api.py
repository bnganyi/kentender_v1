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
	STATUS_AWAITING_PUBLICATION_SETUP,
	STATUS_RETURNED_FOR_CORRECTION,
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


from kentender_procurement.tender_configurations.seed.preview_fixtures import (
	_approve,
	_seed_bidder_facing_config,
)


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

	def test_generate_confirm_auto_opens_publication_setup(self):
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen["preview_status"], "Generated", gen.get("render_exception"))

		conf = confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
		self.assertEqual(conf["preview_status"], "Confirmed")
		self.assertEqual(conf["preview_status_label"], "Preview Confirmed")
		self.assertTrue(conf["show_publication_package"])
		self.assertFalse(conf["can_regenerate_preview"])
		self.assertEqual(conf.get("download_pdf_label"), "Download Confirmed PDF")
		self.assertTrue(conf.get("document_hash"))
		self.assertTrue(conf.get("publication_id"))
		self.assertIn("publication-setup/", conf.get("publication_setup_route") or "")
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_AWAITING_PUBLICATION_SETUP)
		self.assertTrue(doc.confirmed_document_package)
		self.assertTrue(doc.it_publication_record)
		pkg_doc = frappe.get_doc(PACKAGE_DOCTYPE, doc.confirmed_document_package)
		self.assertEqual(pkg_doc.document_hash, conf.get("document_hash"))
		self.assertTrue(
			cstr(pkg_doc.bidder_submission_schema or "").strip(),
			"Confirm must compile bidder_submission_schema onto the package (F1 §3).",
		)
		self.assertTrue(cstr(pkg_doc.evaluation_schema or "").strip())
		self.assertTrue(pkg_doc.contract_carry_forward)
		self.assertTrue(pkg_doc.preview_confirmation)
		pkg = json.loads(doc.publication_package)
		self.assertTrue(pkg.get("sent_at"))
		self.assertTrue(pkg.get("document_hash"))
		pub = frappe.get_doc(PUBLICATION_DOCTYPE, doc.it_publication_record)
		self.assertEqual(pub.status, "Awaiting Publication Setup")
		self.assertEqual(pub.confirmed_package, doc.confirmed_document_package)
		pkg_doc.reload()
		self.assertEqual(pkg_doc.package_status, PACKAGE_STATUS_AWAITING)

		# Legacy send shim is idempotent after confirm.
		sent = send_to_publication_workflow(self.cfg_id)
		self.assertTrue(sent.get("sent") or sent.get("package_confirmed"))
		doc.reload()
		self.assertEqual(doc.status, STATUS_AWAITING_PUBLICATION_SETUP)
		self.assertEqual(doc.it_publication_record, pub.name)

	def test_confirm_requires_flag(self):
		generate_document_preview(self.cfg_id)
		with self.assertRaises(Exception):
			confirm_document_preview(self.cfg_id, {})

	def test_regenerate_blocked_after_confirm(self):
		generate_document_preview(self.cfg_id)
		confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		self.assertEqual(doc.status, STATUS_AWAITING_PUBLICATION_SETUP)
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

	def test_return_after_confirm_invalidates_package_and_publication(self):
		generate_document_preview(self.cfg_id)
		confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
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
