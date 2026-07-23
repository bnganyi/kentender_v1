# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A0 Available Tenders — public list + status mapping tests."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.tender_configurations.seed.preview_fixtures import (
	_approve,
	_seed_bidder_facing_config,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.available_tenders import (
	ACTION_CONTINUE,
	ACTION_VIEW_NOTICE,
	ACTION_VIEW_SUBMITTED,
	ACTION_VIEW_TENDER,
	STATUS_CANCELLED,
	STATUS_CLOSED,
	STATUS_CLOSING_SOON,
	STATUS_OPEN,
	_overview_url,
	compute_public_status,
	list_available_tenders,
	resolve_primary_action,
)
from kentender_procurement.tender_configurations.services.document_preview import (
	confirm_document_preview,
	generate_document_preview,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	publish_tender,
	save_publication_setup,
)


class TestAvailableTendersStatus(unittest.TestCase):
	def test_open_when_published_and_deadline_far(self):
		now = now_datetime()
		st = compute_public_status(
			publication_status="Published",
			submission_deadline=add_to_date(now, days=10),
			clarification_deadline=add_to_date(now, days=5),
			now=now,
		)
		self.assertEqual(st, STATUS_OPEN)

	def test_closing_soon_within_72h(self):
		now = now_datetime()
		st = compute_public_status(
			publication_status="Published",
			submission_deadline=add_to_date(now, hours=48),
			clarification_deadline=add_to_date(now, hours=1),
			now=now,
		)
		self.assertEqual(st, STATUS_CLOSING_SOON)

	def test_closed_after_deadline(self):
		now = now_datetime()
		st = compute_public_status(
			publication_status="Published",
			submission_deadline=add_to_date(now, days=-1),
			clarification_deadline=add_to_date(now, days=-2),
			now=now,
		)
		self.assertEqual(st, STATUS_CLOSED)

	def test_cancelled_internal_status(self):
		st = compute_public_status(
			publication_status="Cancelled",
			submission_deadline=None,
			clarification_deadline=None,
		)
		self.assertEqual(st, STATUS_CANCELLED)

	def test_primary_actions(self):
		self.assertEqual(
			resolve_primary_action(
				public_status=STATUS_OPEN, is_guest=True, has_draft=False, has_sealed=False
			),
			ACTION_VIEW_TENDER,
		)
		self.assertEqual(
			resolve_primary_action(
				public_status=STATUS_OPEN, is_guest=False, has_draft=True, has_sealed=False
			),
			ACTION_CONTINUE,
		)
		self.assertEqual(
			resolve_primary_action(
				public_status=STATUS_OPEN, is_guest=False, has_draft=False, has_sealed=True
			),
			ACTION_VIEW_SUBMITTED,
		)
		self.assertEqual(
			resolve_primary_action(
				public_status=STATUS_CANCELLED, is_guest=False, has_draft=False, has_sealed=False
			),
			ACTION_VIEW_NOTICE,
		)
		# Never Start Bid on landing
		self.assertNotEqual(
			resolve_primary_action(
				public_status=STATUS_OPEN, is_guest=False, has_draft=False, has_sealed=False
			),
			"Start Bid",
		)


class TestAvailableTendersList(unittest.TestCase):
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
					{"version": 1, "sections": [{"title": "Eligibility", "required": True}]}
				),
				"short_scope_summary": "A0 list scope summary for published tender discovery.",
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

	def _publish(self, *, submission_days: int = 14):
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
				"tender_notice": "A0 available tenders notice.",
				"clarification_deadline": str(add_to_date(now, days=2)),
				"submission_deadline": str(add_to_date(now, days=submission_days)),
				"opening_datetime": str(add_to_date(now, days=max(submission_days, 1), hours=1)),
				"bidder_visibility": "All Registered Bidders",
				"activate_bidder_workspace": 1,
				"acknowledgement_confirmed": 1,
			},
		)
		published = publish_tender(pub_id)
		ref = published.get("publication_ref") or frappe.db.get_value(
			"IT Tender Publication Record", pub_id, "publication_ref"
		)
		return pub_id, ref

	def test_lists_published_open_tender(self):
		_pub_id, ref = self._publish(submission_days=14)
		out = list_available_tenders({"q": "A0 list scope summary"}, user="Guest", page_size=50)
		refs = {t["tender_reference"] for t in out["tenders"]}
		self.assertIn(ref, refs)
		row = next(t for t in out["tenders"] if t["tender_reference"] == ref)
		self.assertEqual(row["public_status"], STATUS_OPEN)
		self.assertEqual(row["primary_action_label"], ACTION_VIEW_TENDER)
		self.assertIn("/tenders/", row["primary_action_url"])
		self.assertNotIn("/app/published-tender-overview", row["primary_action_url"])
		self.assertTrue(row["primary_action_url"].startswith("/tenders/"))
		self.assertNotIn("Start Bid", row["primary_action_label"])
		self.assertTrue(out["is_guest"])

	def test_default_excludes_closed(self):
		pub_id, ref = self._publish(submission_days=14)
		frappe.db.set_value(
			"IT Tender Publication Record",
			pub_id,
			"submission_deadline",
			add_to_date(now_datetime(), days=-1),
		)
		frappe.db.commit()
		out = list_available_tenders({}, user="Guest")
		refs = {t["tender_reference"] for t in out["tenders"]}
		self.assertNotIn(ref, refs)
		closed = list_available_tenders({"status": STATUS_CLOSED}, user="Guest")
		closed_refs = {t["tender_reference"] for t in closed["tenders"]}
		self.assertIn(ref, closed_refs)

	def test_guest_counts_zero_private_bids(self):
		self._publish()
		out = list_available_tenders({}, user="Guest")
		self.assertEqual(out["counts"]["draft_bids"], 0)
		self.assertEqual(out["counts"]["submitted_bids"], 0)

	def test_overview_url_is_website_portal(self):
		self.assertEqual(_overview_url("PUB-TEST-001"), "/tenders/PUB-TEST-001")
		self.assertTrue(_overview_url("PUB/A").startswith("/tenders/"))


if __name__ == "__main__":
	unittest.main()

