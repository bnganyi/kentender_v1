# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The order of a bid's tasks and where each button leads (owner request, 2 Oct
2026). Five tasks in a fixed order; a bidder may work out of order, so "next" is
the next task still to do, not the next one in the list. Pure logic: no database."""

from __future__ import annotations

from unittest import TestCase

from kentender_procurement.bid_submission.services import task_flow

BASE = "/tenders/TND-1/bid"


def nav(*statuses):
	keys = ("documents", "company", "requirements", "price", "review")
	labels = ("Tender documents, clarifications and addenda", "Company, declarations and tender security", "Requirements and supporting evidence", "Price", "Review and submit")
	return [{"key": k, "label": l, "status": s} for k, l, s in zip(keys, labels, statuses)]


# the screenshot that prompted this: later tasks done, an earlier one still in progress
OUT_OF_ORDER = nav("Complete", "In progress", "Complete", "Complete", "Not started")


class TestTaskFlow(TestCase):
	def test_progress_counts_the_preparation_tasks_only(self):
		self.assertEqual(task_flow.progress(OUT_OF_ORDER), {"done": 3, "of": 4, "text": "3 of 4 tasks done", "next": "Company and declarations"})
		self.assertEqual(task_flow.progress(nav("Not started", "Not started", "Not started", "Not started", "Not started"))["text"], "0 of 4 tasks done")
		finished = task_flow.progress(nav("Complete", "Complete", "Complete", "Complete", "Complete"))
		self.assertEqual((finished["text"], finished["next"]), ("4 of 4 tasks done", "Review and submit"))

	def test_next_is_the_task_still_to_do_after_the_current_one_then_any_earlier_then_review(self):
		self.assertEqual(task_flow.next_key(OUT_OF_ORDER), "company")  # from the bid page: the first unfinished
		self.assertEqual(task_flow.next_key(OUT_OF_ORDER, after="price"), "company")  # nothing after Price to do: back to the unfinished one, not through finished tasks
		self.assertEqual(task_flow.next_key(OUT_OF_ORDER, after="documents"), "company")
		fresh = nav("Complete", "Not started", "Not started", "Not started", "Not started")
		self.assertEqual(task_flow.next_key(fresh, after="company"), "requirements")  # in order when nothing is out of order
		partly = nav("Complete", "Complete", "Not started", "Complete", "Not started")
		self.assertEqual(task_flow.next_key(partly, after="company"), "requirements")
		self.assertEqual(task_flow.next_key(partly, after="requirements"), "review")  # the other tasks are done: Review
		done = nav("Complete", "Complete", "Complete", "Complete", "Not started")
		self.assertEqual(task_flow.next_key(done), "review")
		self.assertEqual(task_flow.next_key(done, after="price"), "review")

	def test_a_button_names_where_it_leads(self):
		footer = task_flow.footer(OUT_OF_ORDER, "price", BASE)
		self.assertEqual(footer, {"save_label": "Save and continue to Company and declarations", "next_href": f"{BASE}/company"})
		self.assertEqual(task_flow.footer(nav("Complete", "Complete", "Complete", "Not started", "Not started"), "requirements", BASE), {"save_label": "Save and continue to Price", "next_href": f"{BASE}/price"})
		self.assertEqual(task_flow.footer(nav("Complete", "Complete", "Complete", "Complete", "Not started"), "price", BASE)["save_label"], "Save and continue to Review and submit")

	def test_a_button_never_promises_review_while_its_own_task_is_unfinished(self):
		"""The task being worked on is the only one left: Review would only send the
		bidder back ("Your turn: continue Requirements"), so the button says Save and
		stays here, and the page shows what is missing."""
		for status in ("Not started", "In progress", "Needs attention"):
			footer = task_flow.footer(nav("Complete", "Complete", status, "Complete", "Not started"), "requirements", BASE)
			self.assertEqual(footer, {"save_label": "Save", "next_href": f"{BASE}/requirements", "stays": True}, status)
		# once this task is done, the button leads on; and a task that is done is never "stayed on"
		done = task_flow.footer(nav("Complete", "Complete", "Complete", "Complete", "Not started"), "requirements", BASE)
		self.assertEqual(done, {"save_label": "Save and continue to Review and submit", "next_href": f"{BASE}/review"})
		self.assertNotIn("stays", done)
		# another unfinished task still wins over staying
		other = task_flow.footer(nav("Complete", "In progress", "In progress", "Complete", "Not started"), "requirements", BASE)
		self.assertEqual((other["save_label"], other["next_href"]), ("Save and continue to Company and declarations", f"{BASE}/company"))

	def test_the_review_step_says_why_it_is_not_ready(self):
		blocked = task_flow.step(nav("Complete", "Complete", "In progress", "Complete", "Not started"), "requirements", BASE)
		self.assertEqual(blocked["tasks"][4]["hint"], "Not ready: finish the other tasks first")
		self.assertEqual(blocked["tasks"][0]["hint"], "Complete")
		ready = task_flow.step(nav("Complete", "Complete", "Complete", "Complete", "Complete"), "requirements", BASE)
		self.assertEqual(ready["tasks"][4]["hint"], "Complete")

	def test_each_task_page_says_which_step_it_is_with_its_neighbours_and_the_whole_row(self):
		step = task_flow.step(OUT_OF_ORDER, "requirements", BASE)
		self.assertEqual((step["number"], step["of"], step["label"]), (3, 5, "Requirements and supporting evidence"))
		self.assertEqual(step["previous"], {"label": "Company and declarations", "href": f"{BASE}/company"})
		self.assertEqual(step["next"], {"label": "Price", "href": f"{BASE}/price"})
		self.assertEqual([(t["number"], t["short"], t["status"], t["current"]) for t in step["tasks"]], [
			(1, "Tender documents", "Complete", False), (2, "Company and declarations", "In progress", False), (3, "Requirements", "Complete", True),
			(4, "Price", "Complete", False), (5, "Review and submit", "Not started", False)])
		self.assertEqual(step["tasks"][1]["href"], f"{BASE}/company")
		first, last = task_flow.step(OUT_OF_ORDER, "documents", BASE), task_flow.step(OUT_OF_ORDER, "review", BASE)
		self.assertIsNone(first["previous"])
		self.assertIsNone(last["next"])

	def test_the_bid_page_marks_one_task_next_and_words_each_action_by_state(self):
		rows = task_flow.rows(OUT_OF_ORDER, BASE)
		self.assertEqual([(r["number"], r["next"], {k: r["action"][k] for k in ("label", "primary")}) for r in rows], [
			(1, False, {"label": "Review", "primary": False}), (2, True, {"label": "Continue", "primary": True}), (3, False, {"label": "Review", "primary": False}),
			(4, False, {"label": "Review", "primary": False}), (5, False, {"label": "View", "primary": False})])
		fresh = task_flow.rows(nav("Not started", "Not started", "Not started", "Not started", "Not started"), BASE)
		self.assertEqual((fresh[0]["next"], fresh[0]["action"]["label"], fresh[0]["action"]["primary"], fresh[0]["action"]["href"]), (True, "Start", True, f"{BASE}/documents"))
		ready = task_flow.rows(nav("Complete", "Complete", "Complete", "Complete", "Complete"), BASE)
		self.assertEqual((ready[4]["next"], ready[4]["action"]["label"], ready[4]["action"]["primary"]), (True, "Review bid", True))


# the bid is prepared (David); only the Authorised Signatory (Mary) can sign and submit it
PREPARED = nav("Complete", "Complete", "Complete", "Complete", "Complete")
MARY = ["Mary Wanjiku"]


class TestHandOver(TestCase):
	"""When the preparer has finished and someone else must sign, nothing offers
	the preparer a "next" step that leads nowhere (owner report, 2 Oct 2026:
	"Review and submit" took David to a page he could do nothing on)."""

	def test_progress_says_who_signs_instead_of_naming_a_next_task(self):
		out = task_flow.progress(PREPARED, hand_over=MARY)
		self.assertEqual((out["text"], out["next"], out["waiting"]), ("4 of 4 tasks done", "", "Mary Wanjiku signs and submits"))
		self.assertEqual(task_flow.progress(PREPARED)["next"], "Review and submit")  # the signatory still has a next step

	def test_no_task_is_marked_next_and_review_is_only_a_view(self):
		rows = task_flow.rows(PREPARED, BASE, hand_over=MARY)
		self.assertEqual([r["next"] for r in rows], [False] * 5)
		self.assertEqual({k: rows[4]["action"][k] for k in ("label", "primary")}, {"label": "View", "primary": False})
		self.assertEqual(rows[4]["note"], "Mary Wanjiku signs and submits")
		self.assertFalse(any(r["action"]["primary"] for r in rows))

	def test_a_preparer_with_work_left_is_not_handed_over(self):
		unfinished = nav("Complete", "In progress", "Complete", "Complete", "Not started")
		self.assertEqual(task_flow.progress(unfinished, hand_over=MARY)["next"], "Company and declarations")
		rows = task_flow.rows(unfinished, BASE, hand_over=MARY)
		self.assertEqual([r["next"] for r in rows], [False, True, False, False, False])
		self.assertNotIn("note", rows[4])

	def test_the_last_task_finishes_the_preparation_instead_of_leading_to_review(self):
		footer = task_flow.footer(PREPARED, "price", BASE, hand_over=MARY)
		self.assertEqual(footer, {"save_label": "Save and finish", "next_href": BASE})
		self.assertEqual(task_flow.footer(PREPARED, "price", BASE)["save_label"], "Save and continue to Review and submit")  # the signatory
		# an earlier unfinished task still wins
		self.assertEqual(task_flow.footer(nav("Complete", "In progress", "Complete", "Complete", "Not started"), "price", BASE, hand_over=MARY)["next_href"], f"{BASE}/company")

	def test_the_review_step_says_who_signs(self):
		step = task_flow.step(PREPARED, "price", BASE, hand_over=MARY)
		self.assertEqual(step["tasks"][4]["hint"], "Mary Wanjiku signs and submits")
		self.assertEqual(task_flow.step(PREPARED, "price", BASE)["tasks"][4]["hint"], "Complete")

