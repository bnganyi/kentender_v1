# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The business profile in a bid (release 1.4): each entity of the bid (the lead
organisation of a single bid, every member of a joint venture) shows its own
standing business facts, copied from that entity's own Account into the bid's
snapshot. The bidder never types them; one that is missing from an Account is
a Must fix that says whose Account must be completed."""

from __future__ import annotations

import copy
from types import SimpleNamespace

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_submission.services import bid_context, definition_model, product_profile, readiness, snapshot
from kentender_procurement.bid_submission.tests.support import FakeAccounts
from kentender_procurement.std_templates.tests.test_row_group_vocabulary import V, compile_with, entity_rule, extended, rule

PEOPLE_COLUMNS = [
	{"key": "name", "label": "Name", "type": "text"}, {"key": "nationality", "label": "Nationality", "type": "text"},
	{"key": "citizenship", "label": "Citizenship", "type": "text"}, {"key": "shares", "label": "Shares owned (%)", "type": "decimal", "scale": 2},
]
DIRECTORS = [{"name": "Mary Wanjiku", "nationality": "Kenyan", "citizenship": "Kenyan", "shares": "100.00"}]
COMPANY = {"business_structure": "Registered company", "directors": DIRECTORS, "partners": []}


def profile_rule(docs):
	"""The entity rule with the standing facts a company needs: structure, and directors when a company."""
	entity_rule(docs)
	fields = rule(docs, "RR-ENTITY-PROFILE")["field_definitions"]
	fields[0]["supplied_value"] = {"source_id": "SV-ENTITY-PROFILE", "fact": "business_structure"}
	fields.append({
		"field_key": "directors", "label": "Directors", "control_id": "CTL-ROW-GROUP", "required_rule": {"rule_id": "RQ-WHEN-FIELD-EQUALS", "field_key": "business_structure", "value": "Registered company"},
		"visibility_rule": {"rule_id": "VS-WHEN-FIELD-EQUALS", "field_key": "business_structure", "value": "Registered company"}, "validation_id": "VAL-ROW-GROUP",
		"validation_parameters": {"columns": PEOPLE_COLUMNS, "minimum_rows": 1, "maximum_rows": 10, "totals": [{"column": "shares", "equals": "100"}]}, "evidence_rule": None, "help_text": "",
		"supplied_value": {"source_id": "SV-ENTITY-PROFILE", "fact": "directors"},
	})
	profile = docs["product_profile"]
	profile["supplied_value_sources"][-1]["facts"] = ["business_structure", "directors"]


def definition():
	return compile_with(extended(profile_rule), version=V)


def context(model, profiles, *, members=()):
	arrangement = SimpleNamespace(arrangement_type="Joint venture" if members else "Single organisation", members=[SimpleNamespace(organisation_id=m, legal_name=m) for m in members])
	return bid_context.BidContext(
		workspace=SimpleNamespace(), arrangement=arrangement, model=model, values={}, sections={}, snapshot={"organisation": {"organisation_id": "ORG-A"}, "members": [], "profiles": profiles},
		evidence={}, signatory=None, actor="x", assignment={},
	)


def fields_of(model, key="business_structure"):
	return [f for f in model.fields_of("company") if f.group.rule_id == "RR-ENTITY-PROFILE" and f.field_key == key]


class TestEntityGroups(IntegrationTestCase):
	def test_a_single_bid_has_one_profile_for_its_lead_and_a_joint_venture_one_per_member(self):
		single = definition_model.DefinitionModel(definition(), entities=["ORG-A"])
		self.assertEqual([f.member for f in fields_of(single)], ["ORG-A"])
		joint = definition_model.DefinitionModel(definition(), members=["ORG-A", "ORG-B"], entities=["ORG-A", "ORG-B"])
		self.assertEqual([f.member for f in fields_of(joint)], ["ORG-A", "ORG-B"])
		self.assertEqual(len({f.handle for f in fields_of(joint)}), 2)
		self.assertEqual(fields_of(definition_model.DefinitionModel(definition())), [])  # no entities, no groups

	def test_the_profile_is_never_editable_by_the_bidder(self):
		model = definition_model.DefinitionModel(definition(), entities=["ORG-A"])
		self.assertEqual({f.editable for f in model.fields_of("company") if f.group.rule_id == "RR-ENTITY-PROFILE"}, {False})

	def test_the_release_1_4_renderer_is_supported(self):
		self.assertEqual(product_profile.resolve({**definition(), "template_family": "IT-EQUIPMENT-OPEN-V1"})["supported_renderer_version"], V)


class TestEntityValues(IntegrationTestCase):
	def test_each_entity_reads_its_own_copied_facts(self):
		model = definition_model.DefinitionModel(definition(), members=["ORG-A", "ORG-B"], entities=["ORG-A", "ORG-B"])
		ctx = context(model, {"ORG-A": COMPANY, "ORG-B": {"business_structure": "Sole proprietor", "directors": [], "partners": []}}, members=["ORG-A", "ORG-B"])
		self.assertEqual([ctx.value(f) for f in fields_of(model)], ["Registered company", "Sole proprietor"])
		directors = fields_of(model, "directors")
		self.assertEqual(ctx.value(directors[0]), DIRECTORS)
		self.assertIsNone(ctx.value(directors[1]))

	def test_a_complete_profile_is_ready_and_a_directors_table_hides_for_a_sole_proprietor(self):
		model = definition_model.DefinitionModel(definition(), members=["ORG-A", "ORG-B"], entities=["ORG-A", "ORG-B"])
		ctx = context(model, {"ORG-A": COMPANY, "ORG-B": {"business_structure": "Sole proprietor", "directors": []}}, members=["ORG-A", "ORG-B"])
		states = readiness.evaluate(ctx)["company"].fields
		own = [s for s in states if s.field.group.rule_id == "RR-ENTITY-PROFILE"]
		self.assertEqual([s.issue for s in own], [None] * 4)
		self.assertEqual([s.visible for s in own if s.field.field_key == "directors"], [True, False])

	def test_a_missing_profile_is_a_must_fix_that_names_whose_account_to_complete(self):
		model = definition_model.DefinitionModel(definition(), members=["ORG-A", "ORG-B"], entities=["ORG-A", "ORG-B"])
		ctx = context(model, {"ORG-A": COMPANY}, members=["ORG-A", "ORG-B"])
		issues = {s.field.member: s.issue for s in readiness.evaluate(ctx)["company"].fields if s.field.group.rule_id == "RR-ENTITY-PROFILE" and s.field.field_key == "business_structure"}
		self.assertIsNone(issues["ORG-A"])
		self.assertEqual(issues["ORG-B"]["severity"], "Must fix")
		self.assertIn("ORG-B", issues["ORG-B"]["text"])
		self.assertIn("business profile", issues["ORG-B"]["text"])


class TestSnapshotCopiesEveryEntitysProfile(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.accounts = FakeAccounts()
		self.accounts.add_org("ORG-A", "Afya Digital Supplies Limited", "PVT-1")
		self.accounts.add_org("ORG-B", "Kisiwa Tech Limited", "PVT-2")
		self.accounts.set_profile("ORG-A", COMPANY)
		self.previous = frappe.flags.get("kt_supplier_account_provider")
		frappe.flags.kt_supplier_account_provider = self.accounts
		self.addCleanup(setattr, frappe.flags, "kt_supplier_account_provider", self.previous)

	def test_the_snapshot_holds_the_lead_and_each_members_profile(self):
		value = snapshot.facts("ORG-A", [])
		self.assertEqual(sorted(value["profiles"]), ["ORG-A"])
		self.assertEqual(value["profiles"]["ORG-A"]["business_structure"], "Registered company")
		self.assertNotIn("record_version", value["profiles"]["ORG-A"])
		joint = snapshot.facts("ORG-A", ["ORG-A", "ORG-B"])
		self.assertEqual(sorted(joint["profiles"]), ["ORG-A", "ORG-B"])
		self.assertEqual(joint["profiles"]["ORG-B"]["business_structure"], "")  # nothing saved on that Account yet

	def test_a_change_to_the_account_profile_changes_the_digest(self):
		before = snapshot.digest(snapshot.facts("ORG-A", []))
		self.accounts.set_profile("ORG-A", {**COMPANY, "directors": [{**DIRECTORS[0], "shares": "99.00"}]})
		self.assertNotEqual(snapshot.digest(snapshot.facts("ORG-A", [])), before)


class TestCompanyRow(IntegrationTestCase):
	def test_a_profile_with_nothing_to_answer_is_complete_or_needs_the_account_completed(self):
		from kentender_procurement.bid_submission.services import company_view

		model = definition_model.DefinitionModel(definition(), members=["ORG-A", "ORG-B"], entities=["ORG-A", "ORG-B"])
		ctx = context(model, {"ORG-A": COMPANY}, members=["ORG-A", "ORG-B"])
		states = {s.field.key: s for s in readiness.evaluate(ctx)["company"].fields}
		groups = [g for g in model.groups_of("company") if g.rule_id == "RR-ENTITY-PROFILE"]
		self.assertEqual([company_view._group_status(g, states) for g in groups], ["Complete", "Needs attention"])
