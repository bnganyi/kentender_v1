# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Officer Bid Submissions — sealed confidentiality, opening, register (docs/bids §8/§24)."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.seed.bid_submissions_officer_fixtures import (
	ensure_pub_with_deadlines,
)
from kentender_procurement.tender_configurations.services.bid_submissions import (
	STAGE_OPENED,
	STAGE_SEALED,
	derive_submission_stage,
	get_bid_submission_sealed_status,
	get_opening_register,
	get_submitted_bid_overview,
	list_bid_submission_tenders,
	officer_link_supersession,
	officer_withdraw_sealed_bid,
	open_submitted_bids,
	resolve_active_submissions,
)


class TestBidSubmissionsSealedAndOpen(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		cls.fx = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)

	def setUp(self):
		frappe.set_user("Administrator")

	def test_list_has_no_pre_open_counts(self):
		listed = list_bid_submission_tenders()
		row = next(
			(r for r in listed["rows"] if r["publication_id"] == self.fx["publication_id"]),
			None,
		)
		self.assertIsNotNone(row)
		self.assertEqual(row["submission_stage"], STAGE_SEALED)
		self.assertNotIn("active_bids_opened", row)
		self.assertNotIn("bidder", json.dumps(row).lower())

	def test_sealed_status_hides_submission_metadata(self):
		status = get_bid_submission_sealed_status(self.fx["publication_id"])
		blob = json.dumps(status)
		self.assertNotIn("Alpha", blob)
		self.assertNotIn("receipt", blob.lower())
		self.assertNotIn("bid_id", blob)
		self.assertEqual(status.get("can_open_submitted_bids"), 1)

	def test_register_blocked_before_open(self):
		fx = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
		with self.assertRaises(frappe.ValidationError) as ctx:
			get_opening_register(fx["publication_id"])
		self.assertIn("sealed", cstr(ctx.exception).lower())

	def test_overview_blocked_before_open(self):
		fx = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
		with self.assertRaises(frappe.ValidationError) as ctx:
			get_submitted_bid_overview(fx["publication_id"], fx["bid_ids"][0])
		self.assertIn("sealed", cstr(ctx.exception).lower())

	def test_open_creates_register_and_exposes_bids(self):
		fx = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
		reg = open_submitted_bids(fx["publication_id"])
		self.assertEqual(reg["submission_stage"], STAGE_OPENED)
		self.assertGreaterEqual(reg["active_bids_opened"], 3)
		self.assertFalse(reg.get("empty"))
		names = {r["tenderer"] for r in reg["rows"]}
		self.assertIn("Alpha Systems Ltd", names)

	def test_duplicate_open_blocked(self):
		fx = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
		open_submitted_bids(fx["publication_id"])
		with self.assertRaises(frappe.ValidationError) as ctx:
			open_submitted_bids(fx["publication_id"])
		self.assertIn("already", cstr(ctx.exception).lower())

	def test_active_selection_excludes_withdrawn_and_superseded(self):
		fx = ensure_pub_with_deadlines(past_deadline=True, past_opening=True)
		old_id, new_id = fx["bid_ids"][0], fx["bid_ids"][1]
		officer_link_supersession(old_id, new_id)
		officer_withdraw_sealed_bid(fx["bid_ids"][2])
		active = resolve_active_submissions(fx["publication_id"])
		ids = {a["bid_id"] for a in active}
		self.assertNotIn(old_id, ids)
		self.assertNotIn(fx["bid_ids"][2], ids)
		self.assertIn(new_id, ids)

	def test_stage_derivation(self):
		pub = frappe.get_doc("IT Tender Publication Record", self.fx["publication_id"])
		self.assertEqual(derive_submission_stage(pub), STAGE_SEALED)
