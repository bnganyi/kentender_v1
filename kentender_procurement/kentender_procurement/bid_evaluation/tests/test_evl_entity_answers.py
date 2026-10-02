# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Release 1.4: a business profile is answered once per entity of the bid. The checks keep
each entity's answer (they were dropped) and read them together: a matter disclosed by any
entity needs the committee, and the committee sees each entity's own answer."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_evaluation.services import checks, rules

DEFINITION = {
	"sections": [{"groups": [{"group_key": "G1", "published_facts": {}}]}],
	"evaluation_mappings": [{"mapping_id": "DM-X", "evaluation_treatment": "Evaluated", "evaluation_group_id": "EVG-ELIGIBILITY"}],
	"response_rows": [{"response_id": "R1", "group_key": "G1", "field": {"field_key": "state_owned", "label": "State-owned"}, "identity": {"rule_id": "RR-X"}, "evaluation_mapping_id": "DM-X"}],
	"price_rows": [],
}
LOADED = {"_index": {("DM-X", "state_owned"): {"kind": "review-if-yes", "review_reason": "{field_label}: a state-owned entity needs committee assessment."}}, "published_comparison": {}}


def body(*answers):
	return {
		"bid": {"members": [{"organisation_id": "ORG-A", "legal_name": "Afya Digital Supplies Limited"}, {"organisation_id": "ORG-B", "legal_name": "Kisiwa Tech Limited"}]},
		"organisation_snapshot": {"facts": {"organisation": {"organisation_id": "ORG-A", "legal_name": "Afya Digital Supplies Limited"}}},
		"responses": [{"response_id": "R1", "field_key": "state_owned", "task": "company", "member": org, "value": value} for org, value in answers],
		"price": {"currency": "KES", "total": "0.00", "lines": []},
	}


def result(*answers):
	return next(r for r in checks.results_for(LOADED, DEFINITION, body(*answers)) if r["response_id"] == "R1")


class TestEntityAnswers(IntegrationTestCase):
	def test_every_entity_saying_no_meets(self):
		self.assertEqual(result(("ORG-A", "No"), ("ORG-B", "No"))["result"], rules.MEETS)

	def test_a_matter_disclosed_by_any_entity_needs_the_committee_and_names_each_answer(self):
		found = result(("ORG-A", "No"), ("ORG-B", "Yes"))
		self.assertEqual(found["result"], rules.REVIEW)
		self.assertEqual(found["offered_display"], "Afya Digital Supplies Limited: No; Kisiwa Tech Limited: Yes")

	def test_a_single_bid_reads_its_one_entity_without_a_per_entity_display(self):
		found = result(("ORG-A", "No"))
		self.assertEqual(found["result"], rules.MEETS)
		self.assertEqual(found["offered_display"], "No")

	def test_a_lead_only_answer_without_a_member_still_reads_as_before(self):
		self.assertEqual(result(("", "Yes"))["result"], rules.REVIEW)
