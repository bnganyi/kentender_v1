# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A1 Website Published Tender Overview — /tenders/<publication_ref>."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime, set_request
from frappe.website.serve import get_response
from frappe.website.utils import clear_website_cache

from kentender_procurement.tender_configurations.constants import CANONICAL_PACKAGE_ID
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


class TestPublishedTenderOverviewWeb(IntegrationTestCase):
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
					{"version": 1, "sections": [{"title": "Eligibility", "required": True}]}
				),
				"short_scope_summary": "A1W portal overview scope summary.",
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
				"tender_notice": "A1W available tenders notice.",
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

	def test_guest_overview_route_renders_portal_chrome(self):
		ref = self._publish()
		frappe.set_user("Guest")
		resp = self._get(f"/tenders/{ref}")
		self.assertEqual(resp.status_code, 200, frappe.safe_decode(resp.get_data())[:800])
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="kt-a1w-overview-root"', body)
		self.assertIn('data-testid="kt-a0-topnav"', body)
		self.assertIn('data-testid="kt-a1w-primary-cta"', body)
		self.assertIn('data-testid="kt-a1w-ask-question"', body)
		self.assertIn("kt-a1w-timeline", body)
		self.assertIn("What you will submit", body)
		self.assertIn("kt-a1w-footer", body)
		self.assertNotIn("Tender Configurations", body)
		self.assertNotIn("Evaluation and Award", body)
		# Dates must be formatted (no raw microsecond DB noise in Key Dates).
		self.assertNotRegex(body, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3,}")

	def test_unknown_ref_is_not_found(self):
		frappe.set_user("Guest")
		resp = self._get("/tenders/PUB-DOES-NOT-EXIST-XYZ")
		self.assertIn(resp.status_code, (404, 410))


if __name__ == "__main__":
	unittest.main()
