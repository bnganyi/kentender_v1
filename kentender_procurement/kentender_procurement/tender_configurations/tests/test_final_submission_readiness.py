# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Final Submission — readiness aggregation, submit, receipt (domain)."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_SEALED,
	_get_bid,
	_parse_json,
	create_or_get_draft,
)
from kentender_procurement.tender_configurations.services.final_submission import (
	STATE_NEEDS_ATTENTION,
	STATE_READY,
	STATE_SUBMITTED,
	get_bid_submission_readiness,
	get_final_bid_review,
	get_submission_receipt,
	get_submit_bid_page,
	portal_final_bid_review_url,
	portal_review_and_validate_url,
	portal_submission_receipt_url,
	portal_submit_bid_url,
	seed_ready_lean_bid_for_final_submission_tests,
	submit_bid,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	ACTION_REVIEW_VALIDATE_BID,
	ACTION_VIEW_RECEIPT,
	get_submission_checklist,
)


class TestFinalSubmissionReadiness(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_incomplete_lean_is_not_ready(self):
		from kentender_procurement.tender_configurations.seed.lean_price_schedule import (
			publish_lean_price_schedule_for_tests,
		)

		pub = publish_lean_price_schedule_for_tests(fixture="single_lot", clear=True)
		ref = pub["publication_ref"]
		ready = get_bid_submission_readiness(ref)
		self.assertNotEqual(ready["overall_state"], STATE_READY)
		self.assertEqual(ready["ready_to_submit"], 0)
		self.assertGreater(ready["blocking_issue_count"], 0)
		self.assertTrue(all("resolve_url" in i for i in ready["blocking_issues"]))
		keys = {s["section_key"] for s in ready["sections"]}
		self.assertNotIn("final_declaration_and_submit", keys)
		self.assertNotIn("sealed_submission", keys)

	def test_ready_seed_reaches_ready_to_submit(self):
		seed = seed_ready_lean_bid_for_final_submission_tests(clear=True)
		ref = seed["publication_ref"]
		ready = get_bid_submission_readiness(ref)
		self.assertEqual(ready["overall_state"], STATE_READY, ready)
		self.assertEqual(ready["ready_to_submit"], 1)
		self.assertEqual(ready["blocking_issue_count"], 0)
		self.assertEqual(ready["review_nav_enabled"], 1)
		self.assertEqual(ready["submit_nav_enabled"], 1)
		# Excluded (N/A) sections must not block
		na = [s for s in ready["sections"] if s["status"] == "Not applicable"]
		self.assertGreaterEqual(len(na), 1)
		# Totals separated by currency
		rows = ready["price_schedule_totals"].get("by_currency") or []
		self.assertTrue(rows)
		self.assertIn("KES", rows[0].get("currency") or "")
		self.assertIn(",", ready["price_schedule_totals"].get("grand_total_display") or "")

	def test_checklist_primary_review_when_ready(self):
		seed = seed_ready_lean_bid_for_final_submission_tests(clear=True)
		cl = get_submission_checklist(seed["publication_ref"])
		self.assertEqual(cl["primary_action"], ACTION_REVIEW_VALIDATE_BID)
		self.assertTrue(cl["primary_action_enabled"])
		self.assertEqual(
			cl["primary_action_url"],
			portal_review_and_validate_url(seed["publication_ref"]),
		)

	def test_final_review_uses_current_data_and_is_read_only(self):
		seed = seed_ready_lean_bid_for_final_submission_tests(clear=True)
		review = get_final_bid_review(seed["publication_ref"])
		self.assertEqual(review["read_only"], 1)
		self.assertEqual(review["status_chip"], "Ready to submit")
		self.assertTrue(review["sections"])
		self.assertEqual(
			review["form_of_tender_totals"]["grand_total_display"],
			review["price_schedule_totals"]["grand_total_display"],
		)

	def test_final_review_blocked_when_not_ready(self):
		from kentender_procurement.tender_configurations.seed.lean_price_schedule import (
			publish_lean_price_schedule_for_tests,
		)

		pub = publish_lean_price_schedule_for_tests(fixture="single_lot", clear=True)
		with self.assertRaises(frappe.ValidationError):
			get_final_bid_review(pub["publication_ref"])

	def test_submit_requires_declaration_and_locks(self):
		seed = seed_ready_lean_bid_for_final_submission_tests(clear=True)
		ref = seed["publication_ref"]
		with self.assertRaises(frappe.ValidationError):
			submit_bid(ref, declaration_confirmed=False)
		receipt = submit_bid(ref, declaration_confirmed=True)
		self.assertTrue(receipt.get("receipt_code"))
		self.assertEqual(receipt.get("submission_status"), "Submitted")
		self.assertNotIn("seal_hash", receipt)
		self.assertNotIn("bid_id", receipt)
		self.assertNotIn("schema", json.dumps(receipt).lower())

		ready = get_bid_submission_readiness(ref)
		self.assertEqual(ready["overall_state"], STATE_SUBMITTED)

		bid = _get_bid(seed["bid_id"])
		self.assertEqual(cstr_status(bid.status), STATUS_SEALED)
		# Immutable
		with self.assertRaises(frappe.ValidationError):
			from kentender_procurement.tender_configurations.services.electronic_bid import (
				save_section_responses,
			)

			save_section_responses(seed["bid_id"], "price_schedule", {"lines": {}})

		cl = get_submission_checklist(ref)
		self.assertEqual(cl["primary_action"], ACTION_VIEW_RECEIPT)
		self.assertEqual(cl["primary_action_url"], portal_submission_receipt_url(ref))

		# Idempotent resubmit returns receipt
		again = submit_bid(ref, declaration_confirmed=True)
		self.assertEqual(again["receipt_code"], receipt["receipt_code"])

	def test_receipt_get_matches_submit(self):
		seed = seed_ready_lean_bid_for_final_submission_tests(clear=True)
		ref = seed["publication_ref"]
		submitted = submit_bid(ref, declaration_confirmed=True)
		got = get_submission_receipt(ref)
		self.assertEqual(got["receipt_code"], submitted["receipt_code"])
		self.assertIn("Bid submitted", got.get("status_chip") or "")

	def test_deadline_blocks_submit(self):
		seed = seed_ready_lean_bid_for_final_submission_tests(clear=True)
		ref = seed["publication_ref"]
		pub_id = seed["publication_id"]
		frappe.db.set_value(
			"IT Tender Publication Record",
			pub_id,
			"submission_deadline",
			add_to_date(now_datetime(), days=-1),
		)
		frappe.db.commit()
		ready = get_bid_submission_readiness(ref)
		self.assertEqual(ready["deadline_open"], 0)
		self.assertEqual(ready["ready_to_submit"], 0)
		with self.assertRaises(frappe.ValidationError):
			submit_bid(ref, declaration_confirmed=True)

	def test_edit_after_ready_needs_attention(self):
		seed = seed_ready_lean_bid_for_final_submission_tests(clear=True)
		ref = seed["publication_ref"]
		self.assertEqual(get_bid_submission_readiness(ref)["overall_state"], STATE_READY)
		# Invalidate FoT by clearing certifications via price change path
		from kentender_procurement.tender_configurations.services.form_of_tender import (
			invalidate_fot_certifications,
		)

		doc = _get_bid(seed["bid_id"])
		invalidate_fot_certifications(doc, reason="price_schedule_changed")
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		ready = get_bid_submission_readiness(ref)
		self.assertEqual(ready["overall_state"], STATE_NEEDS_ATTENTION)
		self.assertGreater(ready["blocking_issue_count"], 0)

	def test_portal_urls(self):
		self.assertEqual(
			portal_review_and_validate_url("PUB-1"),
			"/tenders/PUB-1/review-and-validate",
		)
		self.assertEqual(portal_final_bid_review_url("PUB-1"), "/tenders/PUB-1/final-bid-review")
		self.assertEqual(portal_submit_bid_url("PUB-1"), "/tenders/PUB-1/submit-bid")
		self.assertEqual(
			portal_submission_receipt_url("PUB-1"),
			"/tenders/PUB-1/submission-receipt",
		)

	def test_submit_page_shows_identity_not_editable(self):
		seed = seed_ready_lean_bid_for_final_submission_tests(clear=True)
		page = get_submit_bid_page(seed["publication_ref"])
		self.assertIn("full_name", page["submitter"])
		self.assertIn("email", page["submitter"])
		self.assertTrue(page["declaration_text"])
		self.assertEqual(page["submission_permission"], 1)


def cstr_status(val) -> str:
	return str(val or "")


if __name__ == "__main__":
	unittest.main()
