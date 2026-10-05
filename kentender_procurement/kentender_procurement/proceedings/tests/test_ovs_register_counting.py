# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Procurement meetings register's counting rules (OVS-CHG-001 v0.6 §11,
§14 "Counting test", §15; plan D6 to D8; tracker OVS6-0405 to OVS6-0408;
acceptance OVS-AC-012). DB-free: the rows are synthetic, so the arithmetic
of the register is proven apart from any owner's data.

Tender A has lead department A, contributor B, one started Opening and two
started Evaluation sessions. Tender B has lead B and one Not held Opening.
Unfiltered there are four rows and three meetings held; filtering on the
contributor B returns the same four rows and three held, the three grouped
under lead A and the Not held row under lead B (zero held for B); pagination
does not change a total."""

from __future__ import annotations

import unittest
from unittest import mock

from kentender_procurement.proceedings.services import register

DEPARTMENTS = {"OU-A": "Digital Health", "OU-B": "Human Resources Management and Development"}


def candidate(n, *, type, lead, contributors=(), held=True, state="Session ended", date="2027-06-12", session=1):
	return {"n": n, "type": type, "lead": lead, "contributors": list(contributors), "held": held, "state": state, "date": date, "session": session if held else None,
		"owner_type": "Bid Opening Case" if type == register.OPENING else "Evaluation Case", "owner_id": f"CASE-{n}"}


def to_row(c):
	if c.get("boom"):
		raise RuntimeError("an owner read failed")
	return {"proceeding": f"PRC-{c['n']}", "owner_type": c["owner_type"], "owner_id": c["owner_id"], "type": c["type"], "tender": "TND-A" if c["lead"] == "OU-A" else "TND-B",
		"title": "Business laptops", "tender_name": "T", "session": c["session"], "state": c["state"], "held": c["held"], "date": c["date"], "date_label": c["date"],
		"started": c["date"] if c["held"] else "", "ended": "", "duration_minutes": 6 if c["held"] else None, "present": 4 if c["held"] else None, "department": c["lead"],
		"department_name": DEPARTMENTS[c["lead"]], "contributors": [DEPARTMENTS[u] for u in c["contributors"]], "contributor_units": c["contributors"], "route": []}


class AllowAll:
	def can_read_row(self, owner_id, user):
		return True


A_OPENING = candidate(1, type=register.OPENING, lead="OU-A", contributors=["OU-B"], state="Finalized", date="2027-06-12")
A_EVAL_1 = candidate(2, type=register.EVALUATION, lead="OU-A", contributors=["OU-B"], date="2027-06-14", session=1)
A_EVAL_2 = candidate(3, type=register.EVALUATION, lead="OU-A", contributors=["OU-B"], date="2027-06-16", session=2)
B_NOT_HELD = candidate(4, type=register.OPENING, lead="OU-B", held=False, state="Not held", date="2027-06-20")


def listed(candidates, **filters):
	adapters = {"Bid Opening Case": AllowAll(), "Evaluation Case": AllowAll()}
	with mock.patch.object(register, "_candidates", return_value=candidates), mock.patch.object(register, "_row", side_effect=to_row), \
			mock.patch.object(register.owners, "adapters", return_value=adapters), mock.patch.object(register, "_unit_name", side_effect=lambda c: DEPARTMENTS.get(c, c)), \
			mock.patch.object(register, "_page_open", return_value=True):
		return register.list_meetings(user="someone@example.test", **filters)


class TestCounting(unittest.TestCase):
	CANDIDATES = [A_OPENING, A_EVAL_1, A_EVAL_2, B_NOT_HELD]

	def test_four_rows_three_held_grouped_under_the_lead(self):
		out = listed(self.CANDIDATES)
		self.assertEqual((out["matched"], out["held_total"], len(out["rows"])), (4, 3, 4))
		self.assertEqual(out["totals"]["by_type"], {"Bid opening": 1, "Bid evaluation": 2})
		self.assertEqual(out["totals"]["grouping"], "Grouped by lead department")
		groups = {g["department"]: g for g in out["totals"]["by_department"]}
		self.assertEqual((groups["OU-A"]["Bid opening"], groups["OU-A"]["Bid evaluation"], groups["OU-A"]["total"]), (1, 2, 3))
		self.assertEqual(groups["OU-B"]["total"], 0)  # B appears with its Not held row and no meeting held

	def test_filtering_on_the_contributor_returns_the_tender_a_rows_and_the_same_grouping(self):
		out = listed(self.CANDIDATES, department="OU-B")
		self.assertEqual({r["tender"] for r in out["rows"]}, {"TND-A", "TND-B"})  # B leads Tender B and contributes to Tender A
		self.assertEqual((out["matched"], out["held_total"]), (4, 3))
		groups = {g["department"]: g["total"] for g in out["totals"]["by_department"]}
		self.assertEqual(groups, {"OU-A": 3, "OU-B": 0})

	def test_a_department_that_only_leads_tender_b_has_no_held_meeting(self):
		out = listed([B_NOT_HELD])
		self.assertEqual((out["matched"], out["held_total"]), (1, 0))
		self.assertEqual(out["rows"][0]["state"], "Not held")
		self.assertIsNone(out["rows"][0]["session"])

	def test_pagination_does_not_change_a_total(self):
		whole = listed(self.CANDIDATES)
		for start, limit in ((0, 1), (1, 2), (3, 5)):
			page = listed(self.CANDIDATES, start=start, limit=limit)
			self.assertEqual((page["matched"], page["held_total"], page["totals"]), (whole["matched"], whole["held_total"], whole["totals"]), (start, limit))
		self.assertEqual(len(listed(self.CANDIDATES, start=0, limit=1)["rows"]), 1)

	def test_the_type_state_and_search_filters_and_clear_filters(self):
		self.assertEqual(listed(self.CANDIDATES, type="Bid evaluation")["held_total"], 2)
		self.assertEqual(listed(self.CANDIDATES, state="Not held")["matched"], 1)
		self.assertEqual(listed(self.CANDIDATES, query="TND-B")["matched"], 1)
		self.assertEqual(listed(self.CANDIDATES, type="", state="", query="")["matched"], 4)

	def test_the_date_filter_is_inclusive_and_a_not_held_row_uses_its_scheduled_date(self):
		self.assertEqual(listed(self.CANDIDATES, date_from="2027-06-14", date_to="2027-06-16")["matched"], 2)  # both ends inclusive
		self.assertEqual([r["state"] for r in listed(self.CANDIDATES, date_from="2027-06-20", date_to="2027-06-20")["rows"]], ["Not held"])
		undated = dict(B_NOT_HELD, date="")
		self.assertEqual(listed([A_OPENING, undated])["matched"], 2)  # an undated row appears only with no date filter
		self.assertEqual(listed([A_OPENING, undated], date_from="2027-01-01")["matched"], 1)

	def test_an_owner_that_denies_a_row_neither_shows_it_nor_counts_it(self):
		class Denies:
			def can_read_row(self, owner_id, user):
				return False

		adapters = {"Bid Opening Case": AllowAll(), "Evaluation Case": Denies()}
		with mock.patch.object(register, "_candidates", return_value=self.CANDIDATES), mock.patch.object(register, "_row", side_effect=to_row), \
				mock.patch.object(register.owners, "adapters", return_value=adapters), mock.patch.object(register, "_unit_name", side_effect=lambda c: DEPARTMENTS.get(c, c)), \
				mock.patch.object(register, "_page_open", return_value=True):
			out = register.list_meetings(user="x@example.test")
		self.assertEqual((out["matched"], out["held_total"], out["incomplete"]), (2, 1, False))  # denial is not a failure

	def test_a_row_that_cannot_be_loaded_marks_the_totals_incomplete(self):
		broken = dict(A_EVAL_2, boom=True)
		with mock.patch.object(register.frappe, "log_error"):
			out = listed([A_OPENING, A_EVAL_1, broken])
		self.assertTrue(out["incomplete"])
		self.assertEqual(out["incomplete_message"], "Some meeting records could not be loaded. Totals are incomplete.")
		self.assertEqual(out["held_total"], 2)  # never presented as the whole

	def test_a_row_never_carries_a_subject_note_bidder_or_bid_count(self):
		row = listed(self.CANDIDATES)["rows"][0]
		for forbidden in ("subject", "notes", "note", "bidder", "bids_opened", "bid_count", "findings"):
			self.assertNotIn(forbidden, row)
