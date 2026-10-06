# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The stage summaries on the Tender record (OVS-CHG-001 v0.6 §4, §4.1, §8, §13,
§15; plan D4, D9; tracker OVS6-0301 to OVS6-0309; acceptance OVS-AC-008,
OVS-AC-010, OVS-AC-011).

Each stage decides what this reader may know and how much to show: nothing
if the reader may not know the stage exists, administrative facts before the
evaluation report is delivered, the decision and its reason after, and a
department-level summary for a Head of User Department whose unit
contributed. A stage that fails to load for an authorised reader is shown as
unavailable while the others stay usable."""

from __future__ import annotations

import json
from unittest import mock

import frappe

from kentender_procurement.bid_evaluation.services import correction, oversight
from kentender_procurement.bid_evaluation.tests.support import AO, AUDITOR, CHAIR, HOP, MEMBER, OUTSIDER
from kentender_procurement.bid_evaluation.tests.test_evl_oversight import BIDDER, HOD, HOD_OTHER, OversightCase
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.tenders.services import read as tender_read


def dump(value) -> str:
	return json.dumps(value, default=str)


class StageCase(OversightCase):
	def stages(self, user) -> dict:
		"""The stage summaries the Tender record returns to this reader, by stage."""
		return {s["key"]: s for s in tender_read.get_tender(tender=self.reference, user=user)["stage_summaries"]}

	def labels(self, summary) -> list[str]:
		return [f["label"] for f in summary["facts"]]


class TestBeforeDelivery(StageCase):
	def test_the_two_offices_see_administrative_facts_and_no_bidder(self):
		for user in (AO, HOP):
			stages = self.stages(user)
			self.assertEqual(set(stages), {"bid-opening", "bid-evaluation"}, user)  # no award exists yet
			evaluation = stages["bid-evaluation"]
			self.assertEqual(evaluation["disclosure"], "status_only", user)
			self.assertEqual(evaluation["status"], "Reviewing", user)
			self.assertTrue(set(self.labels(evaluation)) <= {"Committee appointed", "Evaluation deadline", "Chair"}, self.labels(evaluation))
			self.assertEqual(evaluation["notice"], "Bid details are shared with you when the committee's report is sent.", user)
			self.assertEqual([l["key"] for l in evaluation["links"]], ["view-record"], user)
			self.assertNotIn(BIDDER, dump(evaluation), user)
			self.assertIsNone(evaluation["outcome"], user)
			self.assertEqual(evaluation["state"], "ok", user)

	def test_the_opening_shows_its_completed_facts_to_the_offices_that_read_it(self):
		opening = self.stages(AO)["bid-opening"]
		self.assertEqual(opening["status"], "Complete")
		self.assertEqual(opening["disclosure"], "full")
		self.assertIn("Opening completed", self.labels(opening))
		self.assertEqual(next(f["value"] for f in opening["facts"] if f["label"] == "Bids opened"), "1")
		self.assertEqual([l["key"] for l in opening["links"]], ["view-record"])

	def test_a_department_head_sees_progress_without_a_record_to_open(self):
		stages = self.stages(HOD)
		evaluation = stages["bid-evaluation"]
		self.assertEqual(evaluation["disclosure"], "status_only")
		self.assertNotIn(BIDDER, dump(evaluation))
		self.assertEqual(stages["bid-opening"]["disclosure"], "summary")
		self.assertEqual(stages["bid-opening"]["links"], [])  # no ceremony or opening record for a department head (OVS-P01)
		self.assertNotIn("Minutes", self.labels(stages["bid-opening"]))
		self.assertEqual([l["key"] for l in evaluation["links"]], ["view-record"])  # the department-level view (owner decision 4 Oct 2026)

	def test_a_reader_who_may_not_know_a_stage_exists_gets_nothing_for_it(self):
		from kentender_procurement.award import desk_links as award_links
		from kentender_procurement.bid_evaluation import desk_links as evaluation_links
		from kentender_procurement.bid_opening import desk_links as opening_links

		for user in (HOD_OTHER, OUTSIDER):
			for provider in (opening_links.tender_stage_summary, evaluation_links.tender_stage_summary, award_links.tender_stage_summary):
				self.assertEqual(provider(tender=self.name, user=user), [], f"{provider.__module__} {user}")


class TestAfterDelivery(StageCase):
	def setUp(self):
		super().setUp()
		self.deliver()

	def test_the_offices_see_the_decision_the_reason_and_a_way_to_the_report(self):
		for user in (AO, HOP):
			stages = self.stages(user)
			self.assertEqual(set(stages), {"bid-opening", "bid-evaluation", "award"}, user)
			evaluation = stages["bid-evaluation"]
			self.assertEqual(evaluation["disclosure"], "full", user)
			facts = {f["label"]: f["value"] for f in evaluation["facts"]}
			self.assertEqual(facts["Recommendation"], BIDDER, user)
			self.assertTrue(facts["Evaluated total"].startswith("KES"), user)
			self.assertIn("Report sent", facts)
			self.assertEqual(evaluation["outcome"], {"label": "Outcome", "value": "Recommendation"}, user)
			self.assertTrue(evaluation["reason"], user)
			self.assertEqual(evaluation["version"], "Report 1", user)
			self.assertEqual([l["key"] for l in evaluation["links"]], ["view-record", "view-report"], user)
			self.assertEqual(evaluation["links"][1]["route"][-2:], ["evaluation", "report"], user)

	def test_award_shows_its_stage_and_who_it_is_with(self):
		award = self.stages(AO)["award"]
		self.assertEqual(award["status"], "Opinion")
		self.assertEqual(award["disclosure"], "status_only")  # no decision recorded
		self.assertIn("professional opinion", award["outstanding"]["text"])
		self.assertEqual([l["key"] for l in award["links"]], ["view-record"])

	def test_a_department_head_sees_a_summary_and_neither_the_report_nor_the_award(self):
		stages = self.stages(HOD)
		evaluation = stages["bid-evaluation"]
		self.assertEqual(evaluation["disclosure"], "summary")
		self.assertEqual({f["label"]: f["value"] for f in evaluation["facts"]}["Recommendation"], BIDDER)
		self.assertEqual([l["key"] for l in evaluation["links"]], ["view-record"])  # not View report
		self.assertEqual([l["key"] for l in stages["award"]["links"]], ["view-record"])  # the department view of the Award (owner decision 4 Oct 2026)
		self.assertEqual(stages["award"]["disclosure"], "status_only")

	def award_for(self, user):
		from kentender_procurement.award.services import reads as award_reads

		return award_reads.record(award=frappe.db.get_value("Award Case", {"tender": self.name}, "name"), user=user)

	def test_a_department_head_reads_the_stage_of_the_award_and_nothing_of_the_opinion_or_the_bidders(self):
		view = self.award_for(HOD)
		self.assertTrue(view["department"])
		self.assertEqual((view["stage"], view["decision"]), ("Opinion", None))
		self.assertIn("professional opinion", view["outstanding"])
		text = dump(view)
		self.assertNotIn(BIDDER, text)
		for key_ in ("report", "opinion", "notices", "correspondence", "actions", "history", "package"):
			self.assertNotIn(key_, view)

	def test_a_department_head_reads_the_decision_and_its_reason_once_it_is_recorded(self):
		import types

		from kentender_procurement.award.services import state

		case = frappe.db.get_value("Award Case", {"tender": self.name}, "name")
		frappe.db.set_value("Award Case", case, {"outcome": "Award", "notification_status": "Notices given"})
		decided = types.SimpleNamespace(decided_by=AO, decided_at="2027-06-20 10:00:00", reason="Lowest evaluated responsive bid.")
		with mock.patch.object(state, "committed_decision", return_value=decided):
			view = self.award_for(HOD)
		self.assertEqual(view["decision"]["outcome"], "Award")
		self.assertEqual(view["decision"]["reason"], "Lowest evaluated responsive bid.")
		self.assertTrue(view["decision"]["by"] and view["decision"]["at"])

	def test_anyone_else_is_still_told_there_is_no_such_award(self):
		from kentender_procurement.award.services import reads as award_reads

		case = frappe.db.get_value("Award Case", {"tender": self.name}, "name")
		for user in (HOD_OTHER, OUTSIDER, MEMBER):
			self.not_found(award_reads.record, award=case, user=user)

	def test_the_committee_and_the_auditor_see_the_same_decision(self):
		from kentender_procurement.bid_evaluation import desk_links

		# a committee member holds no Tender responsibility, so never opens the Tender record; the provider is still asked for them
		for user in (CHAIR, MEMBER):
			self.not_found(tender_read.get_tender, tender=self.reference, user=user)
			[evaluation] = desk_links.tender_stage_summary(tender=self.name, user=user)
			self.assertEqual(evaluation["disclosure"], "full", user)
			self.assertEqual({f["label"]: f["value"] for f in evaluation["facts"]}["Recommendation"], BIDDER, user)
		evaluation = self.stages(AUDITOR)["bid-evaluation"]
		self.assertEqual(evaluation["disclosure"], "full")
		self.assertEqual({f["label"]: f["value"] for f in evaluation["facts"]}["Recommendation"], BIDDER)

	def test_a_return_shows_the_earlier_outcome_and_that_a_correction_is_coming(self):
		correction.return_report(tender=self.name, comment="Correct the service-address page reference from page 3 to page 2.", idempotency_key=key(), user=HOP)
		for user in (AO, HOP, HOD):
			evaluation = self.stages(user)["bid-evaluation"]
			self.assertEqual(evaluation["status"], "Returned for correction", user)
			self.assertEqual(evaluation["outstanding"]["text"], "A corrected report is being prepared.", user)
			self.assertEqual(evaluation["outcome"]["value"], "Recommendation", user)  # the delivered outcome stays readable

	def test_one_stage_that_fails_leaves_the_others_usable(self):
		with mock.patch.object(oversight, "delivered_report", side_effect=RuntimeError("boom")):
			stages = self.stages(AO)
		self.assertEqual(stages["bid-evaluation"]["state"], "unavailable")
		self.assertEqual(stages["bid-evaluation"]["error_key"], "OVS_STAGE_UNAVAILABLE")
		self.assertEqual(stages["bid-evaluation"]["links"], [])
		self.assertEqual(stages["bid-opening"]["state"], "ok")
		self.assertEqual(stages["award"]["state"], "ok")

	def test_reading_the_summaries_changes_nothing(self):
		before = frappe.db.count("Evaluation Source Event", {"evaluation_case": self.case}), frappe.db.count("Notification Log")
		for user in (AO, HOP, HOD):
			self.stages(user)
		self.assertEqual((frappe.db.count("Evaluation Source Event", {"evaluation_case": self.case}), frappe.db.count("Notification Log")), before)
