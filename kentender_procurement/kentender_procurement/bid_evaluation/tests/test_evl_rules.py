# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The automatic checks (EVL-CHG-001 v0.4 §4.1–§4.2, §4.4; plan D7, D23, D24;
tracker EVL4-305, EVL4-505; acceptance EVL-A03, EVL-A04).

Vectors for every check kind: inclusive numeric and date boundaries, units
from the published requirement, exact decimals, explicit alternatives, free
text left to a member, presence that never verifies authenticity, a missing
rule that stays reviewable, and published calculations that preserve the
submitted total. The rules file covers every evaluated response of the
template's published definition, so nothing becomes a hidden criterion."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_evaluation.services import rules

RELEASE = {"template_release": "1.2", "release_id": "stdr-09bbfebd-0297-48c0-8ec2-7aa0c2e64495"}
MEMORY = {"comparison": "Minimum", "control": "INTEGER", "label": "Memory", "required_value": {"value": 16}, "required_value_display": "16", "unit": "GB"}
DISPLAY = {"comparison": "Minimum", "control": "DECIMAL", "label": "Display size", "required_value": {"value": "14.0"}, "required_value_display": "14.0", "unit": "inches"}
RESPONSE = {"comparison": "Maximum", "control": "INTEGER", "label": "Maximum support response time", "required_value": {"value": 8}, "required_value_display": "8 hours",
	"unit": "hours"}
STORAGE_TYPE = {"comparison": "One of", "control": "SELECT", "required_value": {"value": "NVMe SSD"}, "required_value_display": "NVMe SSD", "unit": ""}
NETWORK = {"comparison": "Required", "control": "MULTI_SELECT", "required_value": {"values": ["Wi-Fi 6", "Bluetooth 5 or later"]}, "unit": ""}
PORTS = {"comparison": "Required", "control": "PORT_LIST", "required_value": {"ports": [{"minimum_count": 2, "port_type": "USB-C"}, {"minimum_count": 1, "port_type": "HDMI"}]}}
PROCESSOR = {"comparison": "Minimum", "control": "TEXT", "required_value": {"value": "64-bit business-class processor, minimum 10 cores or equivalent benchmark"}}
SECURITY = {"amount": "500000", "currency": "KES", "permitted_forms": ["Demand Bank Guarantee", "Insurance Guarantee"], "bank_guarantee_expiry_date": "2027-11-09",
	"insurance_guarantee_expiry_date": "2027-11-07"}


class TestRuleFile(IntegrationTestCase):
	def setUp(self):
		self.rules = rules.load("IT-EQUIPMENT-OPEN-V1", **RELEASE)

	def check(self, mapping, field, facts, value, group=None, files=0, label=""):
		return rules.check(self.rules, rules.rule_for(self.rules, mapping, field), facts=facts, value=value, group_values=group or {}, evidence_files=files, label=label)

	def test_the_file_is_bound_to_its_template_and_release(self):
		self.assertEqual(len(self.rules["_digest"]), 64)
		with self.assertRaises(rules.RulesUnavailable):
			rules.load("IT-EQUIPMENT-OPEN-V1", template_release="1.1")
		with self.assertRaises(rules.RulesUnavailable):
			rules.load("WORKS-OPEN-V1")

	def test_minimum_and_maximum_are_inclusive_and_carry_the_published_unit(self):
		meets = self.check("DM-TECHNICAL", "offered_value", MEMORY, 16, label="Memory")
		self.assertEqual((meets["result"], meets["reason"], meets["required_display"], meets["offered_display"]),
			("Meets", "Offered memory meets the minimum.", "Minimum 16 GB", "16 GB"))
		below = self.check("DM-TECHNICAL", "offered_value", MEMORY, 8, label="Memory")
		self.assertEqual((below["result"], below["reason"]), ("Does not meet", "8 GB is below the required 16 GB."))  # board D04-FAIL
		self.assertEqual(self.check("DM-WARRANTY-SUPPORT", "offered_value", RESPONSE, 8)["result"], "Meets")
		self.assertEqual(self.check("DM-WARRANTY-SUPPORT", "offered_value", RESPONSE, 9)["result"], "Does not meet")

	def test_exact_decimals(self):
		self.assertEqual(self.check("DM-TECHNICAL", "offered_value", DISPLAY, "14.00")["result"], "Meets")
		self.assertEqual(self.check("DM-TECHNICAL", "offered_value", DISPLAY, "13.99")["result"], "Does not meet")
		self.assertEqual(self.check("DM-TECHNICAL", "offered_value", DISPLAY, "fourteen")["result"], "Needs review")

	def test_choices_alternatives_and_ports(self):
		self.assertEqual(self.check("DM-TECHNICAL", "offered_value", STORAGE_TYPE, "NVMe SSD")["result"], "Meets")
		self.assertEqual(self.check("DM-TECHNICAL", "offered_value", STORAGE_TYPE, "eMMC")["result"], "Does not meet")
		self.assertEqual(self.check("DM-TECHNICAL", "offered_value", NETWORK, ["Wi-Fi 6", "Bluetooth 5 or later", "Ethernet"])["result"], "Meets")
		self.assertEqual(self.check("DM-TECHNICAL", "offered_value", NETWORK, ["Ethernet"])["reason"], "Not offered: Wi-Fi 6, Bluetooth 5 or later.")
		self.assertEqual(self.check("DM-TECHNICAL", "offered_value", PORTS, [{"port_type": "USB-C", "count": 2}, {"port_type": "HDMI", "count": 1}])["result"], "Meets")
		self.assertEqual(self.check("DM-TECHNICAL", "offered_value", PORTS, [{"port_type": "USB-A", "count": 1}])["result"], "Does not meet")
		self.assertEqual(self.check("DM-TECHNICAL", "compliance", MEMORY, "Do not comply")["result"], "Does not meet")
		self.assertEqual(self.check("DM-TENDER-SECURITY", "security_form", SECURITY, "Insurance Guarantee")["result"], "Meets")
		self.assertEqual(self.check("DM-TENDER-SECURITY", "security_form", SECURITY, "Cash")["result"], "Does not meet")

	def test_free_text_or_equivalent_needs_a_member(self):
		out = self.check("DM-TECHNICAL", "offered_value", PROCESSOR, "12 cores", label="Processor requirement")
		self.assertEqual(out["result"], "Needs review")
		self.assertIn("needs a member finding", out["reason"])

	def test_dates_and_conditional_applicability(self):
		self.assertEqual(self.check("DM-TENDER-SECURITY", "bank_guarantee_valid_until", SECURITY, "2027-11-09", group={"security_form": "Demand Bank Guarantee"})["result"], "Meets")
		self.assertEqual(self.check("DM-TENDER-SECURITY", "bank_guarantee_valid_until", SECURITY, "2027-11-08", group={"security_form": "Demand Bank Guarantee"})["result"],
			"Does not meet")
		self.assertEqual(self.check("DM-TENDER-SECURITY", "bank_guarantee_valid_until", SECURITY, None, group={"security_form": "Insurance Guarantee"})["result"],
			"Not applicable")
		self.assertEqual(self.check("DM-GOODS-OFFER", "offered_delivery_date", {"latest_delivery_date": "2027-09-30"}, "2027-09-30")["result"], "Meets")
		self.assertEqual(self.check("DM-GOODS-OFFER", "offered_delivery_date", {"latest_delivery_date": "2027-09-30"}, "2027-10-01")["result"], "Does not meet")
		window = {"window_start": "2022-06-12", "window_end": "2027-06-12"}
		self.assertEqual(self.check("DM-EXPERIENCE", "completion_date", window, "2022-06-12")["result"], "Meets")
		self.assertEqual(self.check("DM-EXPERIENCE", "completion_date", window, "2022-06-11")["result"], "Does not meet")

	def test_money_is_exact(self):
		self.assertEqual(self.check("DM-TENDER-SECURITY", "instrument_amount", SECURITY, "500000.00")["result"], "Meets")
		self.assertEqual(self.check("DM-TENDER-SECURITY", "instrument_amount", SECURITY, "499999.99")["result"], "Does not meet")

	def test_presence_never_verifies_and_evidence_stays_for_a_member(self):
		out = self.check("DM-EVIDENCE-DATASHEET", "evidence", {}, None, files=1)
		self.assertEqual((out["result"], out["basis"]), ("Meets", "Presence"))
		self.assertTrue(out["evidence_assessment"])
		self.assertEqual(self.check("DM-EVIDENCE-DATASHEET", "evidence", {}, None, files=0)["result"], "Does not meet")
		self.assertEqual(self.check("DM-TENDER-SECURITY", "issuer", SECURITY, "KCB Bank Kenya")["result"], "Meets")

	def test_declarations_and_disclosures(self):
		self.assertEqual(self.check("DM-DECL-SD2", "confirmed", {}, True)["result"], "Meets")
		self.assertEqual(self.check("DM-DECL-SD2", "confirmed", {}, None)["result"], "Does not meet")
		self.assertEqual(self.check("DM-DECL-CBQ", "conflict_03", {}, "No")["result"], "Meets")
		self.assertEqual(self.check("DM-DECL-CBQ", "conflict_03", {}, "Yes")["result"], "Needs review")
		self.assertEqual(self.check("DM-DECL-CITD", "disclosure", {}, "Consulted with one or more competitors")["result"], "Needs review")
		self.assertTrue(self.check("DM-DECL-SD1", "confirmed", {}, True).get("evidence_assessment"))

	def test_a_missing_rule_stays_reviewable(self):
		out = rules.check(self.rules, None, facts=MEMORY, value=16, group_values={}, evidence_files=0)
		self.assertEqual((out["result"], out["reason"]), ("Needs review", "The automatic comparison rule is unavailable."))  # board D08-RULE

	def test_published_calculations_preserve_the_submitted_total(self):
		price_rows = [{"line": "1", "description": "Business laptops", "unit": "Each", "calculation": {"calculation_id": "CALC-LINE-TOTAL",
			"inputs": {"quantity": "250", "unit_price": "RSP-UP", "tax_amount": "RSP-TAX"}}}]
		agree = rules.calculate_price(price_rows, {"currency": "KES", "total": "46400000.00", "lines": [{"line": "1", "line_total": "46400000.00"}]},
			{"RSP-UP": "160000.00", "RSP-TAX": "6400000.00"})
		self.assertEqual((agree["result"], agree["calculated_total"], agree["submitted_total"]), ("Meets", "46400000.00", "46400000.00"))
		differs = rules.calculate_price(price_rows, {"currency": "KES", "total": "46000000.00", "lines": [{"line": "1", "line_total": "46000000.00"}]},
			{"RSP-UP": "160000.00", "RSP-TAX": "6400000.00"})
		self.assertEqual(differs["result"], "Needs review")
		self.assertEqual(differs["submitted_total"], "46000000.00")  # never corrected


RELEASE_13 = {"template_release": "1.3", "release_id": "stdr-9b953bcf-fb1e-4e85-b9c1-6ac57218d0e2"}
RELEASE_14 = {"template_release": "1.4", "release_id": "stdr-c25e6578-3700-4df8-bbaa-8c2041be2f01"}
ITEM_3 = "Tenderer has the same legal representative as another tenderer"


class TestReleaseReadings(IntegrationTestCase):
	"""One field key may be read differently by two template releases: a Tender
	keeps the rules of the release it was published on (STD-TPL-001 v0.14).
	Conflict item 9 asks whether a conflict has been RESOLVED, so Yes is the
	reassuring answer, and it applies only after item 7 or 8 is Yes."""

	def check(self, release, field, value, group=None, label=""):
		loaded = rules.load("IT-EQUIPMENT-OPEN-V1", **release)
		return rules.check(loaded, rules.rule_for(loaded, "DM-DECL-CBQ", field), facts={}, value=value, group_values=group or {}, evidence_files=0, label="Conflict of interest questionnaire",
			field_label=label)

	def test_release_1_3_item_nine_needs_review_only_when_the_conflict_is_unresolved(self):
		conflict = {"conflict_07": "Yes", "conflict_08": "No"}
		self.assertEqual(self.check(RELEASE_13, "conflict_09", "Yes", conflict)["result"], "Meets")
		unresolved = self.check(RELEASE_13, "conflict_09", "No", conflict)
		self.assertEqual(unresolved["result"], "Needs review")
		self.assertIn("not been resolved", unresolved["reason"])

	def test_release_1_3_item_nine_does_not_apply_when_neither_item_7_nor_8_is_yes(self):
		for group in ({"conflict_07": "No", "conflict_08": "No"}, {}):
			out = self.check(RELEASE_13, "conflict_09", None, group)
			self.assertEqual(out["result"], "Not applicable", group)
		both = {"conflict_07": "No", "conflict_08": "Yes"}
		self.assertEqual(self.check(RELEASE_13, "conflict_09", "No", both)["result"], "Needs review")

	def test_release_1_2_keeps_its_own_reading_of_item_nine(self):
		self.assertEqual(self.check(RELEASE, "conflict_09", "No")["result"], "Meets")
		self.assertEqual(self.check(RELEASE, "conflict_09", "Yes")["result"], "Needs review")

	def test_a_disclosed_conflict_names_the_item_in_the_committee_reason(self):
		out = self.check(RELEASE_13, "conflict_03", "Yes", label=ITEM_3)
		self.assertEqual(out["result"], "Needs review")
		self.assertEqual(out["reason"], f"A conflict of interest was disclosed: {ITEM_3}")

	def test_removed_release_1_2_fields_keep_their_rule_for_1_2_only(self):
		self.assertIsNotNone(rules.rule_for(rules.load("IT-EQUIPMENT-OPEN-V1", **RELEASE), "DM-DECL-CBQ", "ownership_details"))
		self.assertIsNone(rules.rule_for(rules.load("IT-EQUIPMENT-OPEN-V1", **RELEASE_13), "DM-DECL-CBQ", "ownership_details"))
		self.assertIsNotNone(rules.rule_for(rules.load("IT-EQUIPMENT-OPEN-V1", **RELEASE_13), "DM-DECL-CBQ", "directors_details"))


class TestRelease14Readings(IntegrationTestCase):
	"""Release 1.4: the standing business facts are each entity's profile, read for every entity; a Yes to a
	conflict item also contradicts the Form of Tender; a Tender on release 1.3 keeps its own reading."""

	def rule(self, release, mapping, field):
		return rules.rule_for(rules.load("IT-EQUIPMENT-OPEN-V1", **release), mapping, field)

	def test_a_state_owned_entity_needs_the_committee_in_release_1_4_and_the_form_field_belongs_to_1_3(self):
		state = self.rule(RELEASE_14, "DM-ENTITY-PROFILE", "state_owned")
		self.assertEqual((state["kind"], state["polarity"]), ("review-if-yes", "yes-discloses"))
		self.assertIsNone(self.rule(RELEASE_13, "DM-ENTITY-PROFILE", "state_owned"))
		self.assertIsNone(self.rule(RELEASE_14, "DM-DECL-FORM-OF-TENDER", "state_owned_enterprise"))
		self.assertIsNotNone(self.rule(RELEASE_13, "DM-DECL-FORM-OF-TENDER", "state_owned_enterprise"))

	def test_a_disclosed_conflict_also_names_the_form_of_tender_confirmation_from_1_4(self):
		for release, flagged in ((RELEASE_13, False), (RELEASE_14, True)):
			loaded = rules.load("IT-EQUIPMENT-OPEN-V1", **release)
			out = rules.check(loaded, rules.rule_for(loaded, "DM-DECL-CBQ", "conflict_03"), facts={}, value="Yes", group_values={}, evidence_files=0, label="Conflict", field_label=ITEM_3)
			self.assertEqual(out["result"], "Needs review")
			self.assertEqual("Form of Tender" in out["reason"], flagged, release)

	def test_item_nine_reads_the_same_in_1_4_and_the_moved_fields_keep_their_rules_for_1_3_only(self):
		self.assertEqual(self.rule(RELEASE_14, "DM-DECL-CBQ", "conflict_09")["kind"], "review-unless")
		for field in ("directors_details", "business_structure", "procuring_entity_interest_details"):
			self.assertIsNotNone(self.rule(RELEASE_13, "DM-DECL-CBQ", field), field)
			self.assertIsNone(self.rule(RELEASE_14, "DM-DECL-CBQ", field), field)
		self.assertEqual(self.rule(RELEASE_14, "DM-DECL-CBQ", "procuring_entity_interest_persons")["kind"], "recorded")


class TestRuleCoverage(IntegrationTestCase):
	"""EVL-A03: every evaluated published response has a rule; not-evaluated
	responses never become hidden criteria."""

	def test_every_evaluated_response_of_the_published_definition_has_a_rule(self):
		"""Each template release on this site is checked against the newest definition published on it, with that release's own rules."""
		names = frappe.get_all("Tender Bid Definition", filters={"status": ("in", ("Frozen", "Effective"))}, pluck="name", order_by="creation desc")
		newest: dict[str, dict] = {}
		for name in names:
			definition = frappe.parse_json(frappe.db.get_value("Tender Bid Definition", name, "definition_json"))
			newest.setdefault(definition["template_release_id"], definition)
		if not newest:
			self.skipTest("No published bid definition on this site.")
		for release_id, definition in newest.items():
			with self.subTest(release=release_id):
				release = frappe.db.get_value("Installed STD Release", release_id, "template_release")
				loaded = rules.load("IT-EQUIPMENT-OPEN-V1", template_release=release, release_id=release_id)
				evaluated = {m["mapping_id"] for m in definition["evaluation_mappings"] if m["evaluation_treatment"] == "Evaluated"}
				missing = sorted({(r["evaluation_mapping_id"], r["field"]["field_key"]) for r in definition["response_rows"]
					if r["evaluation_mapping_id"] in evaluated and not rules.rule_for(loaded, r["evaluation_mapping_id"], r["field"]["field_key"])})
				self.assertEqual(missing, [])
				# a definition has no addendum acknowledgement mapping until an addendum is effective, so the file may list more than the definition holds
				self.assertEqual(sorted({m["mapping_id"] for m in definition["evaluation_mappings"]} - evaluated), sorted(set(loaded["not_evaluated"]) & {m["mapping_id"] for m in definition["evaluation_mappings"]}))
				self.assertFalse(evaluated & set(loaded["not_evaluated"]))
				self.assertFalse([r for r in loaded["rules"] if r["mapping_id"] in loaded["not_evaluated"]])
