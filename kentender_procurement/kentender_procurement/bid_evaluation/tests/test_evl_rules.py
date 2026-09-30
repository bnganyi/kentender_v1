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


class TestRuleCoverage(IntegrationTestCase):
	"""EVL-A03: every evaluated published response has a rule; not-evaluated
	responses never become hidden criteria."""

	def test_every_evaluated_response_of_the_published_definition_has_a_rule(self):
		source = frappe.db.get_value("Tender Bid Definition", {"status": ("in", ("Frozen", "Effective"))}, "name", order_by="creation desc")
		if not source:
			self.skipTest("No published bid definition on this site.")
		definition = frappe.parse_json(frappe.db.get_value("Tender Bid Definition", source, "definition_json"))
		loaded = rules.load("IT-EQUIPMENT-OPEN-V1", template_release="1.2")
		evaluated = {m["mapping_id"] for m in definition["evaluation_mappings"] if m["evaluation_treatment"] == "Evaluated"}
		missing = sorted({(r["evaluation_mapping_id"], r["field"]["field_key"]) for r in definition["response_rows"]
			if r["evaluation_mapping_id"] in evaluated and not rules.rule_for(loaded, r["evaluation_mapping_id"], r["field"]["field_key"])})
		self.assertEqual(missing, [])
		self.assertEqual(sorted(set(loaded["not_evaluated"])), sorted({m["mapping_id"] for m in definition["evaluation_mappings"]} - evaluated))
		self.assertFalse([r for r in loaded["rules"] if r["mapping_id"] in loaded["not_evaluated"]])
