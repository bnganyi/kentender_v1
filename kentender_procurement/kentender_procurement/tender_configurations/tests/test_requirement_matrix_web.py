# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A4 Website Requirement Matrix — /tenders/<publication_ref>/sections/<section_key>."""

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
from kentender_procurement.tender_configurations.services.electronic_bid import (
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender,
	save_publication_setup,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	get_published_tender_overview,
)
from kentender_procurement.tender_configurations.tests.test_requirement_matrix_api import (
	MATRIX_SCHEMA,
)


class TestRequirementMatrixWeb(IntegrationTestCase):
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
				"bidder_submission_schema": json.dumps(MATRIX_SCHEMA),
				"short_scope_summary": "A4W matrix web scope.",
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
				"tender_notice": "A4W matrix notice.",
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

	def _ensure_matrix_schema(self, ref: str) -> None:
		from kentender_procurement.tender_configurations.services.published_tender_overview import (
			resolve_published_tender_backend,
		)

		backend = resolve_published_tender_backend(ref)
		draft = create_or_get_draft(backend.get("configuration_id") or self.cfg_id)
		bid = frappe.get_doc("Electronic Bid Submission", draft["bid_id"])
		bid.db_set("schema_snapshot", json.dumps(MATRIX_SCHEMA), update_modified=False)
		frappe.db.set_value(
			"Tender Configuration",
			self.cfg_id,
			"bidder_submission_schema",
			json.dumps(MATRIX_SCHEMA),
		)
		frappe.db.commit()

	def _get(self, path: str):
		set_request(method="GET", path=path)
		return get_response()

	def test_guest_redirects_to_login(self):
		ref = self._publish()
		self._ensure_matrix_schema(ref)
		frappe.set_user("Guest")
		resp = self._get(f"/tenders/{ref}/sections/alpha_compliance_matrix")
		self.assertIn(resp.status_code, (301, 302))
		loc = resp.headers.get("Location") or ""
		self.assertIn("/login", loc)
		self.assertIn("sections", loc)

	def test_admin_matrix_renders(self):
		ref = self._publish()
		self._ensure_matrix_schema(ref)
		frappe.set_user("Administrator")
		resp = self._get(f"/tenders/{ref}/sections/alpha_compliance_matrix")
		self.assertEqual(resp.status_code, 200, frappe.safe_decode(resp.get_data())[:800])
		body = frappe.safe_decode(resp.get_data())
		self.assertIn('data-testid="kt-a4-matrix-root"', body)
		self.assertIn('data-testid="kt-a4-title"', body)
		self.assertIn("Technical Compliance Matrix", body)
		self.assertIn('data-testid="kt-a4-group-rail"', body)
		self.assertIn("System Capacity", body)
		self.assertIn("Security Controls", body)
		self.assertIn("requirements complete", body)
		self.assertIn('data-testid="kt-a4-drawer"', body)
		self.assertIn("Requirement Details", body)
		self.assertIn("Back to Workspace", body)
		self.assertIn("Save & Continue", body)
		self.assertIn("requirement_matrix_web.js", body)
		# Sidebar: short workspace label only — tender ref/title live in page context (e.g. CBQ aside).
		self.assertIn('data-testid="kt-a2-sidebar-title"', body)
		self.assertIn("Bidder Workspace", body)
		self.assertNotIn('data-testid="kt-a2-sidebar-tender"', body)
		self.assertNotIn('data-testid="kt-a2-sidebar-ref"', body)
		# List rows render title once (no secondary statement mirror in markup).
		self.assertNotIn("kt-a4-row-desc", body)
		self.assertNotIn("Tender Configurations", body)
		self.assertNotIn("Evaluation and Award", body)
		self.assertNotIn("NSSF", body)


if __name__ == "__main__":
	unittest.main()
