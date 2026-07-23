# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A3 Website Tender Documents & Addenda — /tenders/<publication_ref>/documents."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime, set_request
from frappe.website.serve import get_response
from frappe.website.utils import clear_website_cache

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
from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
	EMPTY_ADDENDA_MESSAGE,
)


class TestTenderDocumentsAddendaWeb(IntegrationTestCase):
	def setUp(self):
		clear_website_cache()
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
							}
						],
					}
				),
				"short_scope_summary": "A3W documents web scope.",
			},
		)
		_approve(self.cfg_id)
		_seed_bidder_facing_config(self.cfg_id)
		frappe.db.commit()

	def tearDown(self):
		if hasattr(frappe.local, "request"):
			delattr(frappe.local, "request")
		frappe.set_user("Administrator")

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
				"tender_notice": "A3W documents notice.",
				"clarification_deadline": str(add_to_date(now, days=2)),
				"submission_deadline": str(add_to_date(now, days=14)),
				"opening_datetime": str(add_to_date(now, days=15, hours=1)),
				"bidder_visibility": "All Registered Bidders",
				"activate_bidder_workspace": 1,
				"acknowledgement_confirmed": 1,
			},
		)
		published = publish_tender(pub_id)
		ref = published.get("publication_ref") or frappe.db.get_value(
			"IT Tender Publication Record", pub_id, "publication_ref"
		)
		return ref

	def _get(self, path: str):
		set_request(method="GET", path=path)
		return get_response()

	def test_guest_redirects_to_login(self):
		ref = self._publish()
		frappe.set_user("Guest")
		resp = self._get(f"/tenders/{ref}/documents")
		self.assertIn(resp.status_code, (301, 302))
		loc = resp.headers.get("Location") or ""
		self.assertIn("/login", loc)
		self.assertIn("documents", loc)

	def test_admin_documents_renders(self):
		ref = self._publish()
		frappe.set_user("Administrator")
		resp = self._get(f"/tenders/{ref}/documents")
		self.assertEqual(resp.status_code, 200, frappe.safe_decode(resp.get_data())[:800])
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="kt-a3-documents-root"', body)
		self.assertIn('data-testid="kt-a3-official-documents"', body)
		self.assertIn('data-testid="kt-a3-official-addenda"', body)
		self.assertIn("data-kt-countdown", body)
		self.assertIn("kt_bidder_countdown.js", body)
		self.assertIn("Official Tender Documents", body)
		self.assertIn("Official Addenda", body)
		self.assertIn(EMPTY_ADDENDA_MESSAGE, body)
		self.assertIn("Acknowledge Tender Documents", body)
		self.assertIn("Back to Checklist", body)
		self.assertIn("Continue to Next Section", body)
		self.assertIn('data-testid="kt-a2-nav-prepare"', body)
		self.assertNotIn("Tender Configurations", body)
		self.assertNotIn("Evaluation and Award", body)


if __name__ == "__main__":
	unittest.main()
