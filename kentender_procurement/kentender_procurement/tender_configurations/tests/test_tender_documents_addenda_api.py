# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A3 Tender Documents & Addenda — domain API contract tests."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.tender_configurations.seed.preview_fixtures import (
	_approve,
	_seed_bidder_facing_config,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.document_preview import (
	confirm_document_preview,
	generate_document_preview,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender_for_development_preview,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	resolve_published_tender_backend,
)
from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
	ACK_STATUS_ACTION_REQUIRED,
	ACK_STATUS_COMPLETE,
	EMPTY_ADDENDA_MESSAGE,
	READINESS_NO_ADDENDA,
	acknowledge_tender_documents,
	extract_package_addenda,
	get_tender_documents_addenda,
	is_documents_acknowledged,
	portal_documents_url,
	required_addenda_block_submission,
	resolve_document_acknowledgement_section,
)


class TestTenderDocumentsAddendaHelpers(unittest.TestCase):
	def test_portal_documents_url(self):
		self.assertEqual(portal_documents_url("PUB-TEST-1"), "/tenders/PUB-TEST-1/documents")

	def test_resolve_document_acknowledgement_section(self):
		schema = {
			"sections": [
				{
					"key": "tender_document_acknowledgement",
					"title": "Tender Documents & Addenda",
					"required": True,
				},
				{"key": "form_of_tender", "title": "Form of Tender", "required": True},
			]
		}
		sec = resolve_document_acknowledgement_section(schema)
		self.assertIsNotNone(sec)
		self.assertEqual(sec["key"], "tender_document_acknowledgement")
		self.assertEqual(sec["index"], 0)

		by_type = resolve_document_acknowledgement_section(
			{"sections": [{"section_key": "docs", "section_type": "document_acknowledgement", "title": "Docs"}]}
		)
		self.assertEqual(by_type["key"], "docs")

	def test_extract_package_addenda_empty_by_default(self):
		self.assertEqual(extract_package_addenda({}), [])
		self.assertEqual(extract_package_addenda({"items": ["Generated Tender PDF"]}), [])

	def test_extract_package_addenda_real_rows_only(self):
		rows = extract_package_addenda(
			{
				"addenda": [
					{
						"id": "ADD-1",
						"title": "Schedule change",
						"requires_acknowledgement": True,
					}
				]
			}
		)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["id"], "ADD-1")

	def test_blocker_false_when_no_addenda(self):
		self.assertFalse(required_addenda_block_submission([], {}))
		self.assertFalse(required_addenda_block_submission(None, {"acknowledged": True}))

	def test_blocker_true_when_required_unacked(self):
		addenda = [{"id": "ADD-1", "requires_acknowledgement": 1}]
		self.assertTrue(required_addenda_block_submission(addenda, {"acknowledged": True}))
		self.assertFalse(
			required_addenda_block_submission(
				addenda, {"acknowledged": True, "addenda_acknowledged": ["ADD-1"]}
			)
		)

	def test_is_documents_acknowledged(self):
		self.assertTrue(is_documents_acknowledged({"acknowledged": True}))
		self.assertTrue(is_documents_acknowledged({"acknowledge_itt_gcc_tds": True}))
		self.assertFalse(is_documents_acknowledged({}))


class TestTenderDocumentsAddendaApi(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			{
				"std_version": CANONICAL_PACKAGE_ID,
				"bidder_submission_schema": json.dumps(
					{
						"version": 1,
						"sections": [
							{
								"key": "tender_document_acknowledgement",
								"section_type": "document_acknowledgement",
								"title": "Tender Documents & Addenda",
								"required": True,
							},
							{"key": "form_of_tender", "title": "Form of Tender", "required": True},
						],
					}
				),
				"short_scope_summary": "A3 documents scope.",
			},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		for name in frappe.get_all(
			"Electronic Bid Submission",
			filters={"configuration": self.cfg_id},
			pluck="name",
		):
			frappe.delete_doc("Electronic Bid Submission", name, force=1, ignore_permissions=True)
		frappe.db.commit()

	def _publish(self):
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen.get("preview_status"), "Generated", gen.get("render_exception"))
		conf = confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
		pub_id = conf["publication_id"]
		now = now_datetime()
		save_publication_setup(
			pub_id,
			{
				"publication_mode": "immediate",
				"publication_datetime": str(now),
				"tender_notice": "A3 documents notice.",
				"clarification_deadline": str(add_to_date(now, days=2)),
				"submission_deadline": str(add_to_date(now, days=14)),
				"opening_datetime": str(add_to_date(now, days=15, hours=1)),
				"bidder_visibility": "All Registered Bidders",
				"activate_bidder_workspace": 1,
				"acknowledgement_confirmed": 1,
			},
		)
		published = publish_tender_for_development_preview(pub_id)
		ref = cstr(published.get("publication_ref") or "") or cstr(
			frappe.db.get_value("IT Tender Publication Record", pub_id, "publication_ref") or ""
		)
		self.assertTrue(ref.startswith("PUB-"), ref)
		return ref

	def test_guest_denied(self):
		ref = self._publish()
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_tender_documents_addenda(ref)

	def test_empty_addenda_and_package_documents(self):
		ref = self._publish()
		out = get_tender_documents_addenda(ref)
		self.assertEqual(out["published_tender_ref"], ref)
		self.assertTrue(out["documents_url"].endswith("/documents"))
		self.assertEqual(out["addenda"], [])
		self.assertEqual(out["addenda_empty"], 1)
		self.assertEqual(out["addenda_empty_message"], EMPTY_ADDENDA_MESSAGE)
		self.assertEqual(out["addenda_block_submission"], 0)
		self.assertEqual(out["acknowledgement_status"], ACK_STATUS_ACTION_REQUIRED)
		self.assertEqual(out["readiness"]["addenda_label"], READINESS_NO_ADDENDA)
		# Package-driven docs only — no invented mock BoQ/DOCX rows.
		for doc in out["documents"]:
			self.assertNotIn(cstr(doc.get("type")).upper(), {"DOCX", "XLSX"})
			self.assertNotRegex(cstr(doc.get("name")), r"(?i)bill of quantities|technical specifications")
		self.assertEqual(out["acknowledge_label"], "Acknowledge Tender Documents")
		self.assertEqual(out["acknowledge_enabled"], 1)
		self.assertEqual(out["continue_enabled"], 0)

	def test_acknowledge_completes_section_enables_continue(self):
		ref = self._publish()
		out = acknowledge_tender_documents(ref)
		self.assertEqual(out["documents_acknowledged"], 1)
		self.assertEqual(out["acknowledgement_status"], ACK_STATUS_COMPLETE)
		self.assertEqual(out["addenda_block_submission"], 0)
		self.assertEqual(out["acknowledge_enabled"], 0)
		self.assertEqual(out["continue_enabled"], 1)
		self.assertEqual(out["continue_label"], "Continue to Next Section")
		# Response persisted on electronic bid (binding hashes stay server-side).
		backend = resolve_published_tender_backend(ref)
		bid = frappe.get_doc("Electronic Bid Submission", backend["bid_id"])
		responses = json.loads(bid.responses or "{}")
		payload = responses.get(out["section_key"]) or {}
		self.assertTrue(is_documents_acknowledged(payload))
		self.assertTrue(payload.get("package_document_hash"))
		self.assertNotIn("package_context", out)
		self.assertNotIn("bid_id", out)


if __name__ == "__main__":
	unittest.main()
