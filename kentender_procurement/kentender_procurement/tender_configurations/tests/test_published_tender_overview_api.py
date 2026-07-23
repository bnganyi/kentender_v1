# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bidder A1 — published tender overview domain API contract tests."""

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
	publish_tender,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	ACTION_CLOSED,
	ACTION_CONTINUE,
	ACTION_START,
	ACTION_UNAVAILABLE,
	ACTION_VIEW_SUBMITTED,
	get_published_tender_overview,
	start_or_get_bid_workspace,
)


class TestPublishedTenderOverviewApi(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
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
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			{
				"bidder_submission_schema": json.dumps(
					{
						"version": 1,
						"sections": [
							{
								"section_key": "eligibility_declarations",
								"title": "Eligibility & Declarations",
								"required": True,
							},
							{
								"section_key": "price_schedule",
								"title": "Price Schedule",
								"required": True,
							},
							{
								"section_key": "optional_notes",
								"title": "Optional Notes",
								"required": False,
							},
						],
					}
				),
				"short_scope_summary": (
					"Provision of ICT equipment and related services for the seeded tender configuration."
				),
			},
		)
		# Isolate overview primary-action tests from leftover Electronic Bid rows.
		for name in frappe.get_all(
			"Electronic Bid Submission",
			filters={"configuration": self.cfg_id},
			pluck="name",
		):
			frappe.delete_doc("Electronic Bid Submission", name, force=1, ignore_permissions=True)
		frappe.db.commit()

	def _insert_sealed_bid(self, bidder_label: str = "A1 Sealed Bidder") -> str:
		doc = frappe.get_doc(
			{
				"doctype": "Electronic Bid Submission",
				"configuration": self.cfg_id,
				"configuration_ref": self.cfg_id,
				"std_version": CANONICAL_PACKAGE_ID,
				"bidder_label": bidder_label,
				"status": "Sealed",
				"schema_hash": "test-hash",
				"schema_snapshot": json.dumps({"sections": []}),
				"responses": json.dumps({}),
				"sealed_at": now_datetime(),
				"sealed_by": "Administrator",
				"seal_hash": "seal-test-hash",
				"receipt_code": f"EBD-A1-{frappe.generate_hash(length=6).upper()}",
				"receipt_issued_at": now_datetime(),
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		return doc.name

	def _confirm_and_publish(self, *, submission_days: int = 14, activate: int = 1):
		gen = generate_document_preview(self.cfg_id)
		self.assertEqual(gen.get("preview_status"), "Generated", gen.get("render_exception"))
		conf = confirm_document_preview(self.cfg_id, {"confirm_ready_for_handoff": 1})
		pub_id = conf["publication_id"]
		now = now_datetime()
		payload = {
			"publication_mode": "immediate",
			"publication_datetime": str(now),
			"tender_notice": "Public notice for bidder overview test.",
			"clarification_deadline": str(add_to_date(now, days=2)),
			"submission_deadline": str(add_to_date(now, days=submission_days)),
			"opening_datetime": str(add_to_date(now, days=max(submission_days, 1), hours=1)),
			"bidder_visibility": "All Registered Bidders",
			"activate_bidder_workspace": activate,
			"acknowledgement_confirmed": 1,
		}
		save_publication_setup(pub_id, payload)
		published = publish_tender(pub_id)
		self.assertTrue(published.get("published"))
		ref = cstr(published.get("publication_ref") or "")
		if not ref:
			ref = cstr(
				frappe.db.get_value("IT Tender Publication Record", pub_id, "publication_ref") or ""
			)
		self.assertTrue(ref.startswith("PUB-"), ref)
		return pub_id, ref

	def test_overview_start_bid_when_open(self):
		_pub_id, ref = self._confirm_and_publish(submission_days=14)
		ov = get_published_tender_overview(ref)
		self.assertEqual(ov["published_tender_ref"], ref)
		self.assertEqual(ov["primary_action"], ACTION_START)
		self.assertEqual(ov["primary_action_enabled"], 1)
		self.assertEqual(ov["status_chip"], "Open")
		self.assertEqual(ov["workspace_status"], "Not Started")
		self.assertTrue(ov["tender_title"])
		self.assertTrue(ov["scope_summary"])

	def test_documents_are_package_driven(self):
		_pub_id, ref = self._confirm_and_publish()
		ov = get_published_tender_overview(ref)
		docs = ov.get("documents") or []
		self.assertTrue(docs, "expected package-driven document rows")
		names = " ".join(cstr(d.get("name") or "") for d in docs).lower()
		self.assertNotIn("bill of quantities (boq)", names)
		self.assertNotIn("technical specifications", names)
		# Must include real package artifacts or confirmed PDF — not mock DOCX/XLSX samples.
		types = {cstr(d.get("type") or "") for d in docs}
		self.assertTrue(types & {"PDF", "Package Artifact"}, types)

	def test_submission_sections_from_schema(self):
		_pub_id, ref = self._confirm_and_publish()
		ov = get_published_tender_overview(ref)
		sections = ov.get("submission_sections") or []
		titles = [cstr(s.get("title") or "") for s in sections]
		self.assertIn("Eligibility & Declarations", titles)
		self.assertIn("Price Schedule", titles)
		self.assertIn("Optional Notes", titles)
		optional = next(s for s in sections if s["title"] == "Optional Notes")
		self.assertFalse(optional["required"])
		self.assertEqual(optional["required_label"], "Optional")

	def test_tender_info_omits_blank_and_uses_config(self):
		_pub_id, ref = self._confirm_and_publish()
		ov = get_published_tender_overview(ref)
		info = ov.get("tender_info") or []
		self.assertTrue(info)
		for row in info:
			self.assertTrue(cstr(row.get("value") or "").strip())
			self.assertTrue(cstr(row.get("label") or "").strip())
		keys = {cstr(r.get("key") or "") for r in info}
		# Seeded TDS includes tender security — must surface when present.
		self.assertIn("bid_security", keys)
		# Never surface raw publication hash as a tender-info value.
		for row in info:
			self.assertNotRegex(cstr(row.get("value") or ""), r"^[a-f0-9]{10,}$")

	def test_continue_bid_after_start(self):
		_pub_id, ref = self._confirm_and_publish()
		started = start_or_get_bid_workspace(ref, bidder_label="A1 Test Bidder")
		self.assertTrue(started.get("bid_id"))
		ov = get_published_tender_overview(ref)
		self.assertEqual(ov["primary_action"], ACTION_CONTINUE)
		self.assertEqual(ov["primary_action_enabled"], 1)
		self.assertEqual(ov["workspace_status"], "Draft")

	def test_view_submitted_bid_when_sealed(self):
		_pub_id, ref = self._confirm_and_publish()
		self._insert_sealed_bid()
		ov = get_published_tender_overview(ref)
		self.assertEqual(ov["primary_action"], ACTION_VIEW_SUBMITTED)
		self.assertEqual(ov["primary_action_enabled"], 1)
		self.assertEqual(ov["workspace_status"], "Submitted")
		self.assertTrue(ov.get("receipt_code"))

	def test_closed_after_submission_deadline_blocks_start(self):
		pub_id, ref = self._confirm_and_publish(submission_days=14)
		frappe.db.set_value(
			"IT Tender Publication Record",
			pub_id,
			"submission_deadline",
			add_to_date(now_datetime(), days=-1),
		)
		frappe.db.commit()
		ov = get_published_tender_overview(ref)
		self.assertEqual(ov["primary_action"], ACTION_CLOSED)
		self.assertEqual(ov["primary_action_enabled"], 0)
		self.assertEqual(ov["status_chip"], "Closed")
		self.assertEqual(ov["past_submission_deadline"], 1)
		with self.assertRaises(Exception):
			start_or_get_bid_workspace(ref)

	def test_unavailable_when_workspace_not_activated(self):
		# Publish with activate=0 is blocked by publish_tender validation — force flag after publish.
		pub_id, ref = self._confirm_and_publish(activate=1)
		frappe.db.set_value(
			"IT Tender Publication Record",
			pub_id,
			{"activate_bidder_workspace": 0, "bidder_workspace_activation": 0},
		)
		frappe.db.commit()
		ov = get_published_tender_overview(ref)
		self.assertEqual(ov["primary_action"], ACTION_UNAVAILABLE)
		self.assertEqual(ov["primary_action_enabled"], 0)
		with self.assertRaises(Exception):
			start_or_get_bid_workspace(ref)

	def test_closed_with_sealed_shows_view_submitted(self):
		_pub_id, ref = self._confirm_and_publish(submission_days=14)
		self._insert_sealed_bid(bidder_label="A1 Late View")
		frappe.db.set_value(
			"IT Tender Publication Record",
			_pub_id,
			"submission_deadline",
			add_to_date(now_datetime(), days=-1),
		)
		frappe.db.commit()
		ov = get_published_tender_overview(ref)
		self.assertEqual(ov["primary_action"], ACTION_VIEW_SUBMITTED)
		self.assertEqual(ov["primary_action_enabled"], 1)


if __name__ == "__main__":
	unittest.main()
