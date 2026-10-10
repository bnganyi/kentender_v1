# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Requirements task: the red "Fix N items" list holds only what is wrong (a refused file, an answer
that fails its rule); what is simply not done yet is a neutral count, per section once the bidder has
started (owner, 10 Oct 2026: a never-opened task showed a page of red items). Every row that blocks
submission is in one or the other, so the bidder is still told what is missing (owner report, 2 Oct
2026: an Experience section read "Needs attention" but nothing said what to do). Pure logic: no database."""

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


LABELS = {"goods": "Offered goods", "technical": "Technical requirements", "warranty": "Warranty and support", "experience": "Experience", "acceptance": "Acceptance terms", "evidence": "Evidence"}
ENTER = {"severity": "Must fix", "text": "Enter a value."}


class TestMustFix(TestCase):
	def test_an_experience_row_missing_its_evidence_is_to_complete_not_a_fault(self):
		by_region = regions(experience=[
			row("e1", "Contract 1", "Needs evidence", [field("Client"), field("Completion evidence", MISSING, kind="evidence")]),
			row("e2", "Contract 2", "Complete", [field("Client")]),
		])
		self.assertEqual(requirements_view.must_fix(by_region), [])
		self.assertEqual(requirements_view.to_complete(by_region, LABELS, started=True)["title"], "1 item to complete")

	def test_every_region_counts_in_the_pages_own_order(self):
		blocked = lambda key, label: row(key, label, "In progress", [field("Offered value", ENTER)])  # noqa: E731
		by_region = regions(goods=[blocked("g", "Offered goods")], technical=[blocked("t", "Memory")], warranty=[blocked("w", "Minimum warranty")],
			experience=[blocked("x", "Contract 1")], acceptance=[blocked("a", "Visual check")], evidence=[blocked("v", "Datasheet")])
		todo = requirements_view.to_complete(by_region, LABELS, started=True)
		self.assertEqual(todo["title"], "6 items to complete")
		self.assertEqual([s["key"] for s in todo["sections"]], ["goods", "technical", "warranty", "experience", "acceptance", "evidence"])
		self.assertEqual(todo["sections"][1]["text"], "Technical requirements — 1 to complete")

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

	def test_a_wrong_answer_names_the_first_problem_and_counts_the_rest(self):
		two = [field("Client", {"severity": "Must fix", "text": "Enter the client."}), field("Completion date", {"severity": "Must fix", "text": "Enter a date."})]
		by_region = regions(experience=[row("e", "Contract 1", "Needs attention", two)])
		self.assertEqual(requirements_view.must_fix(by_region)[0]["label"], "Contract 1: Client — Enter the client. (and 1 more)")
		self.assertIsNone(requirements_view.to_complete(by_region, LABELS, started=True))  # a fault is not also counted as to do

	def test_an_untouched_row_with_nothing_required_does_not_block_and_a_hidden_field_is_ignored(self):
		optional = row("o", "Brochure", "Not started", [field("Comment")])
		hidden = row("h", "Contract 3", "In progress", [field("Client", MISSING, visible=False)])
		by_region = regions(evidence=[optional], experience=[hidden])
		self.assertEqual(requirements_view.must_fix(by_region), [])
		self.assertIsNone(requirements_view.to_complete(by_region, LABELS, started=True))

	def test_an_untouched_task_is_one_neutral_count_with_no_list_and_no_fault(self):
		rows = [row(f"t{n}", f"Requirement {n}", "Not started", [field("Offered value", ENTER)]) for n in range(20)]
		by_region = regions(technical=rows)
		self.assertEqual(requirements_view.must_fix(by_region), [])
		self.assertEqual(requirements_view.to_complete(by_region, LABELS, started=False), {"title": "20 items to complete", "sections": []})

	def test_a_started_task_says_how_many_are_left_in_each_section(self):
		by_region = regions(technical=[row("t", "Memory", "Not started", [field("Offered value", ENTER)])],
			experience=[row("x", "Contract 1", "In progress", [field("Client", ENTER)]), row("y", "Contract 2", "Not started", [field("Client", ENTER)])])
		todo = requirements_view.to_complete(by_region, LABELS, started=True)
		self.assertEqual(todo, {"title": "3 items to complete", "sections": [
			{"key": "technical", "text": "Technical requirements — 1 to complete"}, {"key": "experience", "text": "Experience — 2 to complete"}]})
