# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Release 1.4 vocabulary (renderer BDS-GOODS-IT-V1 1.2.0): the bounded
row-group control (`CTL-ROW-GROUP` with `VAL-ROW-GROUP`: named columns, at most
ten rows, optional totals), the `per_entity` repetition (the lead organisation
and each joint-venture member) and the `SV-ENTITY-PROFILE` supplied-value
source that carries each entity's standing business facts.

Every addition is optional: renderer 1.1.0 refuses all of it, and the frozen
releases (1.1, 1.2, 1.3) still load and compile byte for byte (their own
frozen tests)."""

from __future__ import annotations

import copy

from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.compiler.errors import STDTemplateError
from kentender_procurement.std_templates.renderers import registry
from kentender_procurement.std_templates.tests.test_release_vocabulary import PARAMETERS, SOURCES, compile_with, field, load, raw, rule, with_version

V = "1.2.0"
PEOPLE = {
	"columns": [
		{"key": "name", "label": "Name", "type": "text", "max_length": 120},
		{"key": "nationality", "label": "Nationality", "type": "text"},
		{"key": "shares", "label": "Shares owned (%)", "type": "decimal", "scale": 2, "minimum": "0", "maximum": "100"},
	],
	"minimum_rows": 1, "maximum_rows": 10, "totals": [{"column": "shares", "equals": "100"}],
}
ENTITY_SOURCE = {"source_id": "SV-ENTITY-PROFILE", "meaning": "One entity's standing facts from its supplier account, frozen for this bid.", "facts": ["business_structure", "directors"], "repetition": "per_entity"}


def vocabulary(docs):
	profile = docs["product_profile"]
	profile["controls"].append({"control_id": "CTL-ROW-GROUP", "label": "Table of rows", "value_type": "list of rows", "accessible_rendering": "A table whose cells are labelled by their column heading."})
	profile["validations"].append({"validation_id": "VAL-ROW-GROUP", "parameters": {"columns": "list of columns", "minimum_rows": "integer", "maximum_rows": "integer", "totals": "list of totals"}})
	comp = next(c for c in profile["compositions"] if c["composition_id"] == "COMP-SUPPLIER-DETAILS")
	comp["permitted_controls"] = sorted(set(comp["permitted_controls"]) | {"CTL-ROW-GROUP"})


def extended(mutate=lambda docs: None, version=V):
	docs = with_version(raw(), version)
	docs["product_profile"]["supplied_value_sources"] = copy.deepcopy(SOURCES) + [copy.deepcopy(ENTITY_SOURCE)]
	docs["product_profile"]["label_parameters"] = copy.deepcopy(PARAMETERS)
	vocabulary(docs)
	mutate(docs)
	return docs


def add_table(docs, parameters=None, **overrides):
	table = {
		"field_key": "owners", "label": "Owners", "control_id": "CTL-ROW-GROUP", "required_rule": {"rule_id": "RQ-ALWAYS"}, "visibility_rule": {"rule_id": "VS-ALWAYS"},
		"validation_id": "VAL-ROW-GROUP", "validation_parameters": copy.deepcopy(parameters or PEOPLE), "evidence_rule": None, "help_text": "", **overrides,
	}
	rule(docs, "RR-SUPPLIER-DETAILS")["field_definitions"].append(table)


class TestRowGroupControl(IntegrationTestCase):
	def assertInvalid(self, docs, code="STD_DEFINITION_INVALID"):
		with self.assertRaises(STDTemplateError) as ctx:
			load(docs)
		self.assertEqual(ctx.exception.code, code, ctx.exception)

	def test_a_row_group_field_compiles_with_its_columns_and_limits(self):
		definition = compile_with(extended(add_table), version=V)
		row = next(r for r in definition["response_rows"] if r["stable_key"].endswith(":RR-SUPPLIER-DETAILS:owners"))
		self.assertEqual((row["field"]["control_id"], row["validation"]["validation_id"]), ("CTL-ROW-GROUP", "VAL-ROW-GROUP"))
		self.assertEqual([c["key"] for c in row["validation"]["parameters"]["columns"]], ["name", "nationality", "shares"])
		self.assertEqual((row["validation"]["parameters"]["minimum_rows"], row["validation"]["parameters"]["maximum_rows"]), (1, 10))

	def test_an_unusable_table_definition_is_refused_when_the_release_loads(self):
		columns = PEOPLE["columns"]
		bad = {
			"no columns": {**PEOPLE, "columns": []},
			"nine columns": {**PEOPLE, "columns": [{"key": f"c{i}", "label": f"C{i}", "type": "text"} for i in range(9)]},
			"duplicate keys": {**PEOPLE, "columns": [columns[0], columns[0]]},
			"unknown type": {**PEOPLE, "columns": [{"key": "name", "label": "Name", "type": "money"}]},
			"eleven rows": {**PEOPLE, "maximum_rows": 11},
			"minimum above maximum": {**PEOPLE, "minimum_rows": 5, "maximum_rows": 2},
			"total on a text column": {**PEOPLE, "totals": [{"column": "name", "equals": "100"}]},
			"total on an unknown column": {**PEOPLE, "totals": [{"column": "nowhere", "equals": "100"}]},
			"unknown parameter": {**PEOPLE, "colour": "red"},
		}
		for name, parameters in bad.items():
			with self.subTest(name):
				self.assertInvalid(extended(lambda d, p=parameters: add_table(d, p)))

	def test_the_control_and_its_validation_go_together(self):
		self.assertInvalid(extended(lambda d: add_table(d, validation_id="VAL-NONE", validation_parameters={})))
		self.assertInvalid(extended(lambda d: add_table(d, control_id="CTL-SHORT-TEXT")))

	def test_renderer_1_1_0_refuses_the_row_group(self):
		docs = extended(add_table, version="1.1.0")
		with self.assertRaises(STDTemplateError) as ctx:
			compile_with(docs, version="1.1.0")
		self.assertEqual(ctx.exception.code, "STD_RENDERER_UNSUPPORTED")


def entity_rule(docs, fact="business_structure"):
	profile = docs["product_profile"]
	profile["source_selectors"].append("SEL-ENTITIES")
	profile["compositions"].append({"composition_id": "COMP-ENTITY-PROFILE", "label": "Entity business profile", "permitted_controls": ["CTL-SINGLE-CHOICE", "CTL-ROW-GROUP"], "repetition": "per_entity", "task_id": "TASK-COMPANY"})
	base = copy.deepcopy(rule(docs, "RR-SUPPLIER-DETAILS"))
	base.update({"rule_id": "RR-ENTITY-PROFILE", "composition_id": "COMP-ENTITY-PROFILE", "source_selector": {"selector": "SEL-ENTITIES"}, "identity_suffix": "ENT", "order": 16, "evaluation_mapping_id": "DM-ENTITY-PROFILE", "contract_mapping_id": "DM-ENTITY-PROFILE"})
	structure = {
		"field_key": "business_structure", "label": "Business structure", "control_id": "CTL-SINGLE-CHOICE", "required_rule": {"rule_id": "RQ-ALWAYS"}, "visibility_rule": {"rule_id": "VS-ALWAYS"},
		"validation_id": "VAL-OPTION-IN-LIST", "validation_parameters": {"options": ["Sole proprietor", "Partnership", "Registered company"]}, "evidence_rule": None, "help_text": "",
		"supplied_value": {"source_id": "SV-ENTITY-PROFILE", "fact": fact},
	}
	base["field_definitions"] = [structure]
	docs["response_rules"]["rules"].append(base)
	mapping = copy.deepcopy(next(m for m in docs["downstream_rules"]["mappings"] if m["mapping_id"] == "DM-SUPPLIER-DETAILS"))
	mapping.update({"mapping_id": "DM-ENTITY-PROFILE", "response_rule_id": "RR-ENTITY-PROFILE"})
	docs["downstream_rules"]["mappings"].append(mapping)


class TestPerEntityRepetition(IntegrationTestCase):
	def entity_rule(self, docs, fact="business_structure"):
		entity_rule(docs, fact)

	def test_a_per_entity_composition_marks_its_group_for_repetition_by_entity(self):
		definition = compile_with(extended(self.entity_rule), version=V)
		groups = {g["rule_id"]: g for s in definition["sections"] for g in s["groups"]}
		self.assertEqual((groups["RR-ENTITY-PROFILE"]["repetition"], groups["RR-ENTITY-PROFILE"]["immutable_source_id"]), ("per_entity", "ENTITY"))
		self.assertNotIn("repetition", groups["RR-SUPPLIER-DETAILS"])

	def test_an_entity_source_belongs_only_to_a_per_entity_composition(self):
		def outside(docs):
			field(docs, "RR-SUPPLIER-DETAILS", "legal_name")["supplied_value"] = {"source_id": "SV-ENTITY-PROFILE", "fact": "business_structure"}

		with self.assertRaises(STDTemplateError) as ctx:
			load(extended(outside))
		self.assertEqual(ctx.exception.code, "STD_DEFINITION_INVALID")
		# and a fact the source does not publish is refused
		with self.assertRaises(STDTemplateError):
			load(extended(lambda d: self.entity_rule(d, fact="shoe_size")))

	def test_renderer_1_1_0_refuses_per_entity(self):
		docs = extended(self.entity_rule, version="1.1.0")
		with self.assertRaises(STDTemplateError) as ctx:
			compile_with(docs, version="1.1.0")
		self.assertEqual(ctx.exception.code, "STD_RENDERER_UNSUPPORTED")


class TestRendererRegistry(IntegrationTestCase):
	def test_1_2_0_is_1_1_0_plus_the_release_1_4_vocabulary_and_1_1_0_is_untouched(self):
		old = registry.bid_workspace_capabilities("BDS-GOODS-IT-V1", "1.1.0")
		new = registry.bid_workspace_capabilities("BDS-GOODS-IT-V1", V)
		self.assertNotIn("CTL-ROW-GROUP", old["controls"])
		self.assertNotIn("per_entity", old["repetitions"])
		self.assertEqual(new["supported_renderer_version"], V)
		self.assertEqual(set(new["controls"]) - set(old["controls"]), {"CTL-ROW-GROUP"})
		self.assertEqual(set(new["validations"]) - set(old["validations"]), {"VAL-ROW-GROUP"})
		self.assertEqual(set(new["compositions"]) - set(old["compositions"]), {"COMP-ENTITY-PROFILE"})
		self.assertEqual(set(new["supplied_value_sources"]) - set(old["supplied_value_sources"]), {"SV-ENTITY-PROFILE"})
		self.assertEqual(set(new["repetitions"]) - set(old["repetitions"]), {"per_entity"})
		self.assertTrue(registry.is_registered("BDS-GOODS-IT-V1", V))
