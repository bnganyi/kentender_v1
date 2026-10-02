# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Release 1.4, joint venture: each member (the lead is the first) shows its own business profile, copied
from that member's own Account when the bid was started. A member whose Account has no profile is a Must
fix that names that member and says it must complete its profile itself: the lead's preparer cannot."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import reads, start_bid
from kentender_procurement.bid_submission.tests.support import JUA, KISIWA, PETER, BidCase, key


class TestJointVentureProfiles(BidCase):
	def start_joint(self) -> str:
		out = start_bid.start_bid(tender_reference=self.reference, organisation=KISIWA, arrangement=self.joint_venture(), notice_contact_id=f"{KISIWA}-C1", idempotency_key=key(), user=PETER)
		self.assertTrue(out["ok"], out)
		return out["bid_reference"]

	def company(self, bid):
		return reads.get_bid_task(bid_reference=bid, task="company", user=PETER)

	def profile_rows(self, view):
		return [r for r in view["declarations"] if r["label"].startswith("Business profile")]

	def test_each_member_has_its_own_profile_row_read_from_its_own_account(self):
		bid = self.start_joint()
		rows = self.profile_rows(self.company(bid))
		self.assertEqual([r["label"] for r in rows], ["Business profile — Kisiwa Digital Limited", "Business profile — Jua Technology Limited"])
		self.assertEqual([r["status"] for r in rows], ["Complete", "Complete"])
		snapshot = frappe.db.get_value("Bid Organisation Snapshot", frappe.db.get_value("Bid Workspace", bid, "organisation_snapshot"), "facts_json")
		self.assertEqual(sorted(frappe.parse_json(snapshot)["profiles"]), sorted([KISIWA, JUA]))
		# every field is read-only and shows that member's own director
		fields = [f for r in rows for f in r["fields"] if f["label"].startswith("Directors")]
		self.assertEqual(len(fields), 2)
		self.assertEqual({f["editable"] for f in fields}, {False})
		self.assertEqual({f["value"][0]["name"] for f in fields}, {"Grace Njeri", "John Kamau"})

	def test_a_member_without_a_profile_is_a_must_fix_that_names_the_member(self):
		self.accounts.profiles.pop(JUA)
		bid = self.start_joint()
		view = self.company(bid)
		rows = {r["label"]: r for r in self.profile_rows(view)}
		member = rows["Business profile — Jua Technology Limited"]
		self.assertEqual((member["status"], member["account_href"]), ("Needs attention", ""))  # not Kisiwa's to fix from Kisiwa's Account
		text = next(f["issue"]["text"] for f in member["fields"] if f["issue"])
		self.assertEqual(text, "Jua Technology Limited must complete its business profile in its own Account.")
		self.assertEqual(rows["Business profile — Kisiwa Digital Limited"]["status"], "Complete")
