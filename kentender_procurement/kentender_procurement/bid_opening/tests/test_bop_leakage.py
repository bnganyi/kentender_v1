# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The leakage gate (BOP-CHG-001 v0.10 BOP-N01, BOP-N13, BOP-A13; plan BOP10-703).

Before Start, nothing a PE, public or technical reader can reach says or
implies how many bids there are or who submitted: not the opening read, My
Work, nor a refused command's code and wording. (Bid Opening's Technical record
search entries are status records only: test_bop_api.)
The same calls on an empty box give the same answers (see also the exact
count-neutral views in test_bop_pre_session)."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.bid_opening import api
from kentender_procurement.bid_opening.services import my_work_provider
from kentender_procurement.bid_opening.tests.support import AO, AUDITOR, CHAIR, INDEPENDENT, MEMBER
from kentender_procurement.bid_opening.tests.test_bop_api import ApiCase
from kentender_procurement.bid_submission.tests.support import key

READERS = (AO, CHAIR, MEMBER, INDEPENDENT, AUDITOR, "Administrator")


def refusals(case) -> dict:
	"""What every ceremony command answers before Start, per actor."""
	out = {}
	for label, call in (
		("open", lambda: api.open_next_bid(case.reference, case.case_version(), key())),
		("readout", lambda: api.record_readout(case.reference, "BOC-ANY", MEMBER, [1], case.case_version(), key())),
		("end", lambda: api.end_opening(case.reference, case.case_version(), key())),
		("end_no_bids", lambda: api.end_opening_with_no_bids(case.reference, case.case_version(), key())),
	):
		result = case.as_user(CHAIR, call)
		out[label] = {k: result.get(k) for k in ("ok", "code", "message", "detail")}
	return out


class TestLeakage(ApiCase):
	def secrets(self) -> list[str]:
		manifest = frappe.get_all("Bid Submission Version", filters={"tender": self.name}, fields=["name", "receipt", "tender_box_envelope", "package_digest"])
		values = ["Afya", "46,400,000", "46400000", "bidder", "envelope"]
		for row in manifest:
			values += [v for v in (row.name, row.receipt, row.tender_box_envelope, row.package_digest) if v]
		return values

	def test_bop_n01_nothing_reachable_before_start_reveals_a_bid(self):
		self.assertTrue(self.submit(self.signed())["ok"])
		self.prepared()
		self.at(self.minutes_before(0.5))
		for user in (CHAIR, MEMBER, INDEPENDENT):
			self.join(user)
		self.close_box()
		self.heartbeat_all()
		self.receive()
		seen = [self.as_user(u, api.get_opening, self.reference) for u in READERS]
		seen += [my_work_provider.my_work_rows(u) for u in READERS]
		answers = refusals(self)
		seen.append(answers)
		text = json.dumps(seen, default=str)
		for secret in self.secrets():
			with self.subTest(secret=secret[:24]):
				self.assertNotIn(secret, text)
		self.assertEqual({v["code"] for v in answers.values()}, {"BOP_VERSION_CONFLICT"})
		self.assertEqual({json.dumps(v["detail"], sort_keys=True) for v in answers.values()}, {json.dumps({"reason": "state", "state": "Ready to open"}, sort_keys=True)})
		self.__class__.nonempty_refusals = answers

	def test_bop_n01_an_empty_box_refuses_the_same_way(self):
		self.prepared()
		self.at(self.minutes_before(0.5))
		for user in (CHAIR, MEMBER, INDEPENDENT):
			self.join(user)
		self.close_box()
		self.heartbeat_all()
		self.receive()
		answers = refusals(self)
		self.assertEqual({v["code"] for v in answers.values()}, {"BOP_VERSION_CONFLICT"})
		self.assertEqual({json.dumps(v["detail"], sort_keys=True) for v in answers.values()}, {json.dumps({"reason": "state", "state": "Ready to open"}, sort_keys=True)})
