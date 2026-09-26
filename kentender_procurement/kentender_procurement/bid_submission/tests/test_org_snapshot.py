# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.4.8, §4.5 and §7.2 `RefreshBidOrganisationSnapshot`
(plan Phase 5, BDS8-502; BDS06-IMP-016): an Account change reaches a Draft
only through an explicit comparison and confirmation, as a new snapshot."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.bid_submission.services import errors, snapshot, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, PETER, BidCase, key


class TestOrganisationSnapshot(BidCase):
	def test_an_account_change_reaches_the_draft_only_when_confirmed(self):
		bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]
		first = frappe.db.get_value("Bid Workspace", bid, "organisation_snapshot")
		self.accounts.orgs[AFYA]["registered_address"] = "Afya Plaza, Upper Hill, Nairobi"
		version = frappe.db.get_value("Bid Workspace", bid, "record_version")
		preview = snapshot.refresh_bid_organisation_snapshot(bid_reference=bid, confirm=False, expected_record_version=version, idempotency_key=key(), user=DAVID)
		self.assertEqual((preview["refreshed"], preview["changed"], preview["snapshot_version"]), (False, ["registered_address"], 1))
		done = snapshot.refresh_bid_organisation_snapshot(bid_reference=bid, confirm=True, expected_record_version=version, idempotency_key=key(), user=DAVID)
		self.assertEqual((done["refreshed"], done["snapshot_version"]), (True, 2))
		workspace = frappe.get_doc("Bid Workspace", bid)
		self.assertNotEqual(workspace.organisation_snapshot, first)
		self.assertEqual(json.loads(frappe.db.get_value("Bid Organisation Snapshot", workspace.organisation_snapshot, "facts_json"))["organisation"]["registered_address"], "Afya Plaza, Upper Hill, Nairobi")
		self.assertEqual(json.loads(frappe.db.get_value("Bid Organisation Snapshot", first, "facts_json"))["organisation"]["registered_address"], "Afya Digital Supplies Limited, Nairobi")
		with self.assertRaises(errors.BidSubmissionError) as masked:
			snapshot.refresh_bid_organisation_snapshot(bid_reference=bid, confirm=True, expected_record_version=workspace.record_version, idempotency_key=key(), user=PETER)
		self.assertEqual(masked.exception.code, "BDS_TENDER_NOT_FOUND")
