# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.4.2–4.4.5 and plan D11 (plan Phase 6, BDS8-601): the
runtime reads the exact Published Bid Definition, implements every control,
validation and named rule the product profile declares, and gives the portal
opaque field handles instead of published identities. Built on the installed
release 1.2 MOH definition (no database world)."""

from __future__ import annotations

import json
from decimal import Decimal

from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_submission.services import controls, definition_model, validation
from kentender_procurement.std_templates.services.installer import DEFAULT_PACKAGE

RUNTIME = DEFAULT_PACKAGE / "06_runtime"
DEFINITION = json.loads((RUNTIME / "moh_published_bid_definition_expected.json").read_text(encoding="utf-8"))
PROFILE = json.loads((RUNTIME / "product_profile.json").read_text(encoding="utf-8"))


def model(members=()):
	return definition_model.DefinitionModel(DEFINITION, members=list(members))


class TestEveryDeclaredCapabilityIsImplemented(IntegrationTestCase):
	def test_every_control_validation_and_rule_of_the_profile_has_an_implementation(self):
		self.assertEqual({c["control_id"] for c in PROFILE["controls"]} - set(controls.CANONICALISERS), set())
		self.assertEqual({v["validation_id"] for v in PROFILE["validations"]} - set(validation.VALIDATIONS), set())
		runtime_rules = {r["rule_id"] for r in PROFILE["required_rules"] + PROFILE["visibility_rules"]} - {"RQ-WHEN-SOURCE-FLAG"}  # resolved at publication
		self.assertEqual(runtime_rules - set(validation.RULES), set())


class TestControls(IntegrationTestCase):
	def test_values_are_canonicalised_or_named_as_wrong(self):
		cases = [
			("CTL-CONFIRMATION", True, True), ("CTL-CONFIRMATION", "true", True), ("CTL-CONFIRMATION", "", None),
			("CTL-YES-NO", "Yes", "Yes"), ("CTL-SINGLE-CHOICE", " Joint venture ", "Joint venture"),
			("CTL-MULTI-SELECT", ["Wi-Fi 6", "Ethernet", "Wi-Fi 6"], ["Wi-Fi 6", "Ethernet"]),
			("CTL-SHORT-TEXT", "  ApexBook Pro 14 ", "ApexBook Pro 14"), ("CTL-LONG-TEXT", "Line one\nLine two", "Line one\nLine two"),
			("CTL-INTEGER", "36", 36), ("CTL-DECIMAL", "1.5", "1.50"), ("CTL-MONEY", "160000", "160000.00"), ("CTL-DATE", "2027-09-15", "2027-09-15"),
			("CTL-PORTS-LIST", [{"port_type": "USB-C", "count": "2"}], [{"port_type": "USB-C", "count": 2}]),
		]
		params = {"CTL-DECIMAL": {"scale": 2}, "CTL-MONEY": {"scale": 2}}
		for control, raw, expected in cases:
			with self.subTest(control=control, raw=raw):
				self.assertEqual(controls.canonical(control, raw, params.get(control, {})), (expected, None))
		for control, raw in (("CTL-YES-NO", "Maybe"), ("CTL-SHORT-TEXT", "two\nlines"), ("CTL-INTEGER", "3.5"), ("CTL-MONEY", "12.345"), ("CTL-DATE", "15/09/2027"), ("CTL-PORTS-LIST", [{"port_type": "USB-C", "count": 0}]), ("CTL-CONFIRMATION", "no")):
			with self.subTest(control=control, raw=raw):
				value, error = controls.canonical(control, raw, params.get(control, {}))
				self.assertIsNone(value)
				self.assertTrue(error)


class TestValidations(IntegrationTestCase):
	def test_each_named_validation_checks_its_published_parameters(self):
		ok, bad = validation.check, lambda *a: validation.check(*a) is not None
		self.assertIsNone(ok("VAL-TEXT-LENGTH", {"min_length": 3, "max_length": 5}, "abcd"))
		self.assertTrue(bad("VAL-TEXT-LENGTH", {"min_length": 3, "max_length": 5}, "ab"))
		self.assertTrue(bad("VAL-INTEGER-RANGE", {"minimum": 1800, "maximum": 2100}, 1700))
		self.assertTrue(bad("VAL-DECIMAL-RANGE", {"minimum": "0", "maximum": "10", "scale": 2}, "10.01"))
		self.assertIsNone(ok("VAL-MONEY", {"currency": "KES", "minimum": "500000.00", "maximum": "500000.00", "scale": 2}, "500000.00"))
		self.assertTrue(bad("VAL-MONEY", {"currency": "KES", "minimum": "500000.00", "maximum": "500000.00", "scale": 2}, "600000.00"))
		self.assertTrue(bad("VAL-DATE-RANGE", {"not_before": "2027-11-02"}, "2027-11-01"))
		self.assertTrue(bad("VAL-OPTION-IN-LIST", {"options": ["Yes", "No"]}, "Perhaps"))
		self.assertTrue(bad("VAL-OPTIONS-SUBSET", {"options": ["Ethernet", "5G"]}, ["Ethernet", "6G"]))
		self.assertTrue(bad("VAL-PORTS", {"port_options": ["USB-A", "HDMI"]}, [{"port_type": "USB-A", "count": 2}, {"port_type": "USB-A", "count": 1}]))
		# a row left half-filled is named, not saved as an answer
		self.assertTrue(bad("VAL-PORTS", {"port_options": ["USB-A", "HDMI"]}, [{"port_type": "", "count": None}]))
		self.assertTrue(bad("VAL-PORTS", {"port_options": ["USB-A", "HDMI"]}, [{"port_type": "USB-A", "count": None}]))
		self.assertTrue(bad("VAL-PORTS", {"port_options": ["USB-A", "HDMI"]}, [{"port_type": "USB-A", "count": 0}]))
		self.assertIsNone(ok("VAL-PORTS", {"port_options": ["USB-A", "HDMI"]}, [{"port_type": "USB-A", "count": 2}, {"port_type": "HDMI", "count": 1}]))
		self.assertTrue(bad("VAL-EVIDENCE-COUNT", {"minimum": 1, "maximum": 1}, ["a", "b"]))
		self.assertIsNone(ok("VAL-CONFIRMED", {}, True))

	def test_required_and_visibility_rules_read_the_same_group(self):
		rule = {"rule_id": "RQ-WHEN-FIELD-EQUALS", "field_key": "security_form", "value": "Demand Bank Guarantee"}
		self.assertTrue(validation.rule_holds(rule, {"security_form": "Demand Bank Guarantee"}))
		self.assertFalse(validation.rule_holds(rule, {"security_form": "Insurance Guarantee"}))
		anyone = {"rule_id": "VS-WHEN-ANY-FIELD-EQUALS", "field_keys": ["conflict_01", "conflict_02"], "value": "Yes"}
		self.assertTrue(validation.rule_holds(anyone, {"conflict_02": "Yes"}))
		self.assertFalse(validation.rule_holds({"rule_id": "RQ-NEVER"}, {}))


class TestDefinitionModel(IntegrationTestCase):
	def test_tasks_and_groups_follow_the_published_order(self):
		m = model()
		self.assertEqual([t.key for t in m.tasks], ["documents", "company", "requirements", "price", "review"])
		self.assertEqual(m.task("documents").label, "Tender documents, clarifications and addenda")
		self.assertEqual(len([g for g in m.groups_of("requirements") if g.rule_id == "RR-TECHNICAL"]), 11)

	def test_handles_are_opaque_and_map_back_only_within_the_definition(self):
		m = model()
		field = m.fields_of("company")[0]
		self.assertRegex(field.handle, r"^f[0-9a-f]{20}$")
		self.assertNotIn("RSP-", field.handle)
		self.assertEqual(m.by_handle(field.handle).key, field.key)
		self.assertIsNone(m.by_handle("f" + "0" * 20))

	def test_a_per_member_group_repeats_for_each_member_with_its_own_identity(self):
		none = [f for f in model().fields_of("company") if f.group.rule_id == "RR-JV-MEMBER"]
		self.assertEqual(none, [])
		two = [f for f in model(["ORG-A", "ORG-B"]).fields_of("company") if f.group.rule_id == "RR-JV-MEMBER"]
		self.assertEqual(len(two), 16)  # eight member fields, twice
		self.assertEqual({f.member for f in two}, {"ORG-A", "ORG-B"})
		self.assertEqual(len({f.key for f in two}), 16)
		self.assertEqual(len({f.handle for f in two}), 16)

	def test_a_supplied_field_is_never_bidder_editable(self):
		legal = next(f for f in model().fields_of("company") if f.field_key == "legal_name")
		self.assertEqual((legal.supplied, legal.editable), ({"source_id": "SV-ARRANGEMENT", "fact": "tenderer_name"}, False))
		year = next(f for f in model().fields_of("company") if f.field_key == "representative_address")
		self.assertEqual((year.supplied, year.editable), (None, True))

	def test_the_price_rows_name_their_money_inputs(self):
		line = model().price_rows[0]
		self.assertEqual((line["description"], line["quantity"], sorted(line["input_response_ids"])), ("Business laptops", "250", ["tax_amount", "unit_price"]))
		self.assertEqual(Decimal(line["quantity"]), Decimal("250"))
