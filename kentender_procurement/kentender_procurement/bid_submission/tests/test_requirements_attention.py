# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Requirements task: "Fix N items" names every row that blocks submission and
says what is missing (owner report, 2 Oct 2026: an Experience section read
"Needs attention" but nothing said what to do). Pure logic: no database."""

from __future__ import annotations

from unittest import TestCase

from kentender_procurement.bid_submission.services import requirements_view

MISSING = {"severity": "Must fix", "text": "Add the required supporting evidence."}


def field(label, issue=None, *, kind="short_text", visible=True, editable=True):
	return {"label": label, "kind": kind, "issue": issue, "visible": visible, "editable": editable}


def row(key, label, status, fields=(), evidence=""):
	return {"key": key, "label": label, "status": status, "evidence": evidence, "fields": list(fields)}


def regions(**rows):
	base = {key: [] for key in ("goods", "technical", "warranty", "experience", "acceptance", "evidence")}
	base.update(rows)
	return base


class TestMustFix(TestCase):
	def test_an_experience_row_missing_its_evidence_is_listed_with_what_is_missing(self):
		by_region = regions(experience=[
			row("e1", "Contract 1", "Needs evidence", [field("Client"), field("Completion evidence", MISSING, kind="evidence")]),
			row("e2", "Contract 2", "Complete", [field("Client")]),
		])
		self.assertEqual(requirements_view.must_fix(by_region), [{"key": "e1", "label": "Contract 1: Completion evidence — Add the required supporting evidence."}])

	def test_every_region_counts_not_only_technical_warranty_and_evidence(self):
		blocked = lambda key, label: row(key, label, "In progress", [field("Offered value", {"severity": "Must fix", "text": "Enter a value."})])  # noqa: E731
		by_region = regions(goods=[blocked("g", "Offered goods")], technical=[blocked("t", "Memory")], warranty=[blocked("w", "Minimum warranty")],
			experience=[blocked("x", "Contract 1")], acceptance=[blocked("a", "Visual check")], evidence=[blocked("v", "Datasheet")])
		self.assertEqual([i["key"] for i in requirements_view.must_fix(by_region)], ["g", "t", "w", "x", "a", "v"])  # the page's own order

	def test_a_rejected_file_keeps_its_plain_wording(self):
		by_region = regions(evidence=[row("v", "Datasheet", "Needs evidence", [field("Datasheet", MISSING, kind="evidence")], evidence="Rejected file")])
		self.assertEqual(requirements_view.must_fix(by_region)[0]["label"], "Replace the rejected file for datasheet")

	def test_a_row_holding_one_good_file_and_one_refused_is_still_listed(self):
		held = row("v", "Electrical compatibility", "Needs evidence", [field("Evidence")], evidence="evidence-1.pdf")
		held["evidence_rejected"] = True
		self.assertEqual(requirements_view.must_fix(regions(technical=[held])), [{"key": "v", "label": "Replace the rejected file for electrical compatibility"}])

	def test_a_row_the_status_says_needs_attention_is_listed_even_when_no_field_names_why(self):
		unexplained = row("u", "Memory", "Needs attention", [field("Offered value")])
		self.assertEqual(requirements_view.must_fix(regions(technical=[unexplained])), [{"key": "u", "label": "Complete memory"}])

	def test_a_row_with_several_problems_names_the_first_and_counts_the_rest(self):
		two = [field("Client", {"severity": "Must fix", "text": "Enter the client."}), field("Completion date", {"severity": "Must fix", "text": "Enter a date."})]
		self.assertEqual(requirements_view.must_fix(regions(experience=[row("e", "Contract 1", "In progress", two)]))[0]["label"], "Contract 1: Client — Enter the client. (and 1 more)")

	def test_an_untouched_row_with_nothing_required_does_not_block_and_a_hidden_field_is_ignored(self):
		optional = row("o", "Brochure", "Not started", [field("Comment")])
		hidden = row("h", "Contract 3", "In progress", [field("Client", MISSING, visible=False)])
		self.assertEqual(requirements_view.must_fix(regions(evidence=[optional], experience=[hidden])), [])

	def test_an_untouched_row_with_a_required_field_says_to_complete_it(self):
		untouched = row("n", "Memory", "Not started", [field("Offered value", {"severity": "Must fix", "text": "Enter a value."})])
		self.assertEqual(requirements_view.must_fix(regions(technical=[untouched]))[0]["label"], "Memory: Offered value — Enter a value.")
