# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Template content quality gates (STD-TPL-001 v0.14 §13.9).

Two layers. The synthetic cases prove each gate catches its defect and accepts
the corrected form. `TestPackQuality` runs every gate over the real
IT-EQUIPMENT-OPEN-V1 pack: it is red on release 1.2 (the defects QA found)
and must be green on the release that fixes them. No database is touched.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from kentender_procurement.std_templates.release import quality

TEMPLATES = Path(__file__).resolve().parents[4] / "docs/mvp-1-r1/07_tender_templates"
PACK = TEMPLATES / "it_equipment_open_v1"


def field(key, label, control="CTL-SHORT-TEXT", help_text="", visibility="VS-ALWAYS"):
	return {"field_key": key, "label": label, "help_text": help_text, "control_id": control, "visibility_rule": {"rule_id": visibility}}


def rule(*fields, rule_id="RR-X", composition="COMP-LOCKED-DECLARATION", mapping="DM-X", **extra):
	return {"rule_id": rule_id, "composition_id": composition, "evaluation_mapping_id": mapping, "document_anchor": "complete_tender.html#x",
		"field_definitions": list(fields), **extra}


PROFILE = {"compositions": [{"composition_id": "COMP-LOCKED-DECLARATION", "repetition": "one"}, {"composition_id": "COMP-TECH", "repetition": "per_source"}]}


class TestLabels(unittest.TestCase):
	def found(self, *fields, composition="COMP-LOCKED-DECLARATION"):
		return quality.check_labels([rule(*fields, composition=composition)], PROFILE)

	def test_a_bare_ordinal_label_is_found(self):
		for label in ("Conflict of interest item 3", "Item (f)", "Paragraph 5 disclosure", "Question 7"):
			self.assertEqual([f.check for f in self.found(field("a", label))], [quality.LABEL], label)

	def test_a_label_with_wording_passes(self):
		label = "Tenderer has the same legal representative as another tenderer"
		self.assertEqual(self.found(field("a", label, help_text="Disclosure of Interest item (ii) 3.")), [])

	def test_a_wordy_label_may_carry_a_cross_reference_help(self):
		label = "Is the Tenderer a state-owned enterprise or institution?"
		self.assertEqual(self.found(field("a", label, help_text="Item (k) of the Form of Tender.")), [])

	def test_an_ordinal_help_does_not_rescue_a_wordless_label(self):
		self.assertEqual([f.check for f in self.found(field("a", "Details", help_text="Item (f) of the Form."))], [quality.LABEL])

	def test_two_always_visible_fields_may_not_read_identically(self):
		self.assertEqual([f.check for f in self.found(field("a", "Guarantee valid until"), field("b", "Guarantee valid until"))], [quality.DUPLICATE])

	def test_the_same_label_under_different_visibility_is_allowed(self):
		self.assertEqual(self.found(field("a", "Guarantee valid until", visibility="VS-WHEN-A"), field("b", "Guarantee valid until", visibility="VS-WHEN-B")), [])

	def test_a_repeated_composition_repeats_labels_by_design(self):
		self.assertEqual(self.found(field("a", "Compliance"), field("b", "Compliance"), composition="COMP-TECH"), [])

	def test_a_compound_long_text_label_is_advisory(self):
		out = self.found(field("a", "Owner details (name, nationality, citizenship and percentage of shares)", control="CTL-LONG-TEXT"))
		self.assertEqual([(f.check, f.advisory) for f in out], [(quality.COMPOUND, True)])


class TestTables(unittest.TestCase):
	RULES = [rule(field("details", "Details", control="CTL-LONG-TEXT"), rule_id="RR-A")]

	def check(self, table, release="1.3"):
		return quality.check_tables({"tables": [{"id": "TBL-1", "fields": ["RR-A.details"], **table}]}, self.RULES, release)

	def test_a_table_needs_a_recorded_treatment(self):
		self.assertEqual([f.check for f in self.check({})[0]], [quality.TABLE])

	def test_an_interim_table_passes_until_its_release_and_fails_from_it(self):
		table = {"treatment": "interim", "until_release": "1.4"}
		self.assertEqual(self.check(table, "1.3")[0], [])
		self.assertEqual(len(self.check(table, "1.4")[0]), 1)

	def test_a_row_group_table_must_use_the_row_group_control(self):
		self.assertEqual(len(self.check({"treatment": "row-group"})[0]), 1)

	def test_a_table_naming_a_missing_field_fails(self):
		out, _ = quality.check_tables({"tables": [{"id": "TBL-1", "treatment": "itemised", "fields": ["RR-A.gone"]}]}, self.RULES, "1.3")
		self.assertEqual(len(out), 1)

	def test_deferral_needs_a_reason_and_a_decision_date_and_is_reported(self):
		self.assertEqual(len(self.check({"treatment": "deferred"})[0]), 1)
		out, deferred = self.check({"treatment": "deferred", "reason": "Owner chose audit only", "decided": "2026-10-02"})
		self.assertEqual((out, len(deferred)), ([], 1))


	def test_an_open_table_is_reported_not_failed_and_must_state_its_question(self):
		self.assertEqual(len(self.check({"treatment": "open"})[0]), 1)
		out, deferred = self.check({"treatment": "open", "reason": "Owner to decide the split"})
		self.assertEqual((out, [f.message for f in deferred]), ([], ["OPEN: Owner to decide the split"]))


class TestEvaluation(unittest.TestCase):
	MAPPINGS = [{"mapping_id": "DM-A", "evaluation_treatment": "Evaluated", "evaluation_result_rule": "Pass."},
		{"mapping_id": "DM-B", "evaluation_treatment": "Not evaluated", "evaluation_result_rule": None}]

	def rules(self, *fields, mapping="DM-A"):
		return [rule(*fields, mapping=mapping)]

	def evaluation(self, *entries, not_evaluated=("DM-B",)):
		return {"not_evaluated": list(not_evaluated), "rules": [{"mapping_id": "DM-A", **e} for e in entries]}

	def run_checks(self, rules, evaluation, mappings=None):
		return quality.check_evaluation(rules, mappings or self.MAPPINGS, evaluation)

	def test_an_evaluated_field_without_a_rule_is_found(self):
		out = self.run_checks(self.rules(field("a", "Wording of the question")), self.evaluation())
		self.assertEqual([f.check for f in out], [quality.EVAL_COVERAGE])

	def test_a_rule_for_a_not_evaluated_mapping_is_a_hidden_criterion(self):
		rules = [rule(field("a", "Wording"), mapping="DM-B")]
		evaluation = {"not_evaluated": ["DM-B"], "rules": [{"mapping_id": "DM-B", "field_key": "a", "kind": "recorded"}]}
		self.assertEqual([f.check for f in self.run_checks(rules, evaluation)], [quality.EVAL_COVERAGE])

	def test_the_not_evaluated_list_must_match_the_mappings(self):
		out = self.run_checks([], self.evaluation(not_evaluated=()))
		self.assertEqual([f.where for f in out], ["not_evaluated"])

	def test_a_yes_no_field_must_declare_its_polarity(self):
		rules = self.rules(field("a", "Is there a conflict of interest?", control="CTL-YES-NO"))
		missing = self.run_checks(rules, self.evaluation({"field_key": "a", "kind": "review-if-yes"}))
		self.assertEqual([f.check for f in missing], [quality.POLARITY])
		ok = self.run_checks(rules, self.evaluation({"field_key": "a", "kind": "review-if-yes", "polarity": "yes-discloses"}))
		self.assertEqual(ok, [])

	def test_a_reassuring_yes_may_not_use_review_if_yes(self):
		rules = self.rules(field("a", "Has the conflict been resolved?", control="CTL-YES-NO"))
		out = self.run_checks(rules, self.evaluation({"field_key": "a", "kind": "review-if-yes", "polarity": "yes-reassures"}))
		self.assertEqual([f.check for f in out], [quality.POLARITY])
		fixed = self.run_checks(rules, self.evaluation({"field_key": "a", "kind": "review-unless", "accepted_value": "Yes", "polarity": "yes-reassures"}))
		self.assertEqual(fixed, [])

	def test_an_entry_for_another_release_is_not_checked_and_does_not_count(self):
		rules = self.rules(field("a", "Wording of the question"))
		old = {"field_key": "a", "kind": "recorded", "review_reason": "see item (k)", "releases": ["1.2"]}
		new = {"field_key": "a", "kind": "recorded", "releases": ["1.3"]}
		self.assertEqual(quality.check_evaluation(rules, self.MAPPINGS, self.evaluation(old, new), "1.3"), [])
		self.assertEqual([f.check for f in quality.check_evaluation(rules, self.MAPPINGS, self.evaluation(old, new), "1.2")], [quality.EVALUATOR_TEXT])
		self.assertEqual([f.check for f in quality.check_evaluation(rules, self.MAPPINGS, self.evaluation(new), "1.2")], [quality.EVAL_COVERAGE])

	def test_evaluator_text_may_not_name_an_item_by_number_only(self):
		rules = self.rules(field("a", "Wording of the question"))
		for text in ("the committee assesses item (k)", "documents listed in item 7 of the form", "otherwise fail with the item named"):
			evaluation = self.evaluation({"field_key": "a", "kind": "recorded", "review_reason": text})
			self.assertEqual([f.check for f in self.run_checks(rules, evaluation)], [quality.EVALUATOR_TEXT], text)
		mappings = [dict(self.MAPPINGS[0], evaluation_result_rule="Pass; otherwise fail with the item named."), self.MAPPINGS[1]]
		out = self.run_checks(rules, self.evaluation({"field_key": "a", "kind": "recorded"}), mappings)
		self.assertEqual([f.check for f in out], [quality.EVALUATOR_TEXT])


class TestLockedNumbering(unittest.TestCase):
	HTML = '<div id="x"><ol><li>First</li><li>Second</li></ol></div>'

	def test_an_ordered_list_must_keep_its_numbers(self):
		self.assertEqual(len(quality.check_locked_numbering([rule(field("a", "A"), locked_text="First Second")], self.HTML)), 1)
		self.assertEqual(quality.check_locked_numbering([rule(field("a", "A"), locked_text="1. First 2. Second")], self.HTML), [])

	def test_a_block_with_no_ordered_list_is_not_checked(self):
		self.assertEqual(quality.check_locked_numbering([rule(field("a", "A"), locked_text="Plain")], '<div id="x"><p>Plain</p></div>'), [])


class TestLockedTextKeepsListNumbers(unittest.TestCase):
	"""The flattener behind `locked_text` must not drop the numbers a list shows
	on the page: "paragraph (5)(b)" is unfindable without them."""

	def text(self, html):
		from kentender_procurement.std_templates.compiler import locked_text

		return locked_text.anchored_text(f'<div id="x">{html}</div>', "x")

	def test_an_ordered_list_is_numbered_from_one(self):
		self.assertEqual(self.text("<ol><li>First</li><li>Second</li></ol>"), "1. First 2. Second")

	def test_a_typed_list_uses_its_own_markers(self):
		self.assertEqual(self.text('<ol type="a"><li>One</li><li>Two</li></ol>'), "a. One b. Two")
		self.assertEqual(self.text('<ol type="i"><li>One</li><li>Two</li></ol>'), "i. One ii. Two")

	def test_a_nested_unordered_list_is_left_alone_and_numbering_continues(self):
		html = "<ol><li>A<ul><li>a) x</li><li>b) y</li></ul></li><li>B</li></ol>"
		self.assertEqual(self.text(html), "1. A a) x b) y 2. B")

	def test_an_unordered_list_gets_no_numbers(self):
		self.assertEqual(self.text("<ul><li>x</li><li>y</li></ul>"), "x y")


class TestPackQuality(unittest.TestCase):
	"""The gates over the real pack. Red on release 1.2; green when fixed."""

	@classmethod
	def setUpClass(cls):
		def load(path):
			return json.loads((TEMPLATES / path).read_text(encoding="utf-8"))

		runtime = "it_equipment_open_v1/06_runtime/"
		rules, downstream, profile = (load(runtime + n) for n in ("response_rules.json", "downstream_rules.json", "product_profile.json"))
		cls.release = rules["template_release"]
		cls.result = quality.run(rules=rules["rules"], mappings=downstream["mappings"], profile=profile,
			evaluation=load("evaluation_rules/IT-EQUIPMENT-OPEN-V1.json"), register=load("quality_register/IT-EQUIPMENT-OPEN-V1.json"),
			master_html=(PACK / "02_master/complete_tender.html").read_text(encoding="utf-8"), template_release=cls.release)

	def test_the_template_passes_every_quality_gate(self):
		failures = [f"{f.check} {f.where}: {f.message}" for f in self.result["failures"]]
		self.assertEqual(failures, [], f"release {self.release} has {len(failures)} content defects")

	def test_every_deferral_is_on_the_record(self):
		for finding in self.result["deferred"]:
			self.assertTrue(finding.message, f"{finding.where} is deferred with no reason")
