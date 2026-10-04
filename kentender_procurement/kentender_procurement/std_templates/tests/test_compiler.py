# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-IMP-001 v1.0 §7, §16 — the shared compiler: golden vectors,
determinism, typed failures without fallback, identity rules and purity
(STI10-AC-008/009; TPL08-AC-007/016/018; TPL10-AC-004)."""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.compiler import addenda, assets as release_assets
from kentender_procurement.std_templates.compiler.canonical import CanonicalError, canonical_json, pretty_json
from kentender_procurement.std_templates.compiler.definition import DEFINITION_FIELDS, compile_published_bid_definition, verify_definition_digest
from kentender_procurement.std_templates.compiler.errors import STDTemplateError
from kentender_procurement.std_templates.renderers import registry
from kentender_procurement.std_templates.tests import support

# The pack's own renderer version (release 1.2 binds 1.1.0); release 1.1's
# 1.0.0 vector is proven separately in test_release_vocabulary.
CAPS = registry.bid_workspace_capabilities("BDS-GOODS-IT-V1", support.pack_assets().envelope["supported_renderer_version"])


def compile_moh(projection=None, assets=None, caps=None):
	return compile_published_bid_definition(assets or support.pack_assets(), projection or support.moh_projection(), renderer_capabilities=caps or CAPS)


class TestGoldenVectors(IntegrationTestCase):
	def test_moh_vector_reproduces_byte_for_byte(self):
		expected = (support.PACK / "06_runtime/moh_published_bid_definition_expected.json").read_text(encoding="utf-8")
		self.assertEqual(pretty_json(compile_moh()), expected)

	def test_variant_vectors_reproduce(self):
		for name in ("none", "women", "persons_with_disabilities"):
			with self.subTest(name=name):
				expected = json.loads((support.PACK / f"04_fixture/reservation_variants/{name}_expected.json").read_text(encoding="utf-8"))
				definition = compile_moh(support.variant_projection(name))
				self.assertEqual(definition["definition_digest"], expected["definition_digest"])

	def test_compilation_is_deterministic(self):
		self.assertEqual(canonical_json(compile_moh()), canonical_json(compile_moh()))

	def test_definition_has_exactly_the_released_fields_and_a_binding_digest(self):
		definition = compile_moh()
		self.assertEqual(tuple(definition), DEFINITION_FIELDS)
		self.assertTrue(verify_definition_digest(definition))
		tampered = copy.deepcopy(definition)
		tampered["response_rows"][0]["field"]["label"] = "Changed"
		self.assertFalse(verify_definition_digest(tampered))
		self.assertEqual(definition["template_family"], definition["template_release_id"] and "IT-EQUIPMENT-OPEN-V1")

	def test_moh_fixture_counts(self):
		definition = compile_moh()
		families = {}
		for row in definition["response_rows"]:
			families.setdefault(row["identity"]["source_family"], set()).add(row["identity"]["immutable_source_id"])
		self.assertEqual(len(families["goods"]), 1)
		self.assertEqual(len(families["technical_requirement"]), 11)
		self.assertEqual(len(families["acceptance_requirement"]), 5)
		self.assertNotIn("related_service", families)
		self.assertEqual([s["section_id"] for s in definition["sections"]], ["TASK-DOCUMENTS", "TASK-COMPANY", "TASK-REQUIREMENTS", "TASK-PRICE", "TASK-REVIEW"])
		self.assertEqual(definition["reservation_treatment"]["category"], "Youth")
		self.assertEqual(definition["reservation_treatment"]["eligibility_group_id"], "EVG-ELIGIBILITY")
		self.assertFalse(definition["reservation_treatment"]["planning_designation_is_entitlement"])


class TestIdentity(IntegrationTestCase):
	def test_every_response_has_a_unique_five_part_identity(self):
		rows = compile_moh()["response_rows"]
		tuples = {json.dumps(r["identity"], sort_keys=True) for r in rows}
		self.assertEqual(len(tuples), len(rows))
		for row in rows:
			self.assertEqual(set(row["identity"]), {"published_tender_version_id", "source_family", "immutable_source_id", "rule_id", "field_key"})

	def test_grouped_goods_keep_every_contributing_item(self):
		goods = [g for s in compile_moh()["sections"] for g in s["groups"] if g["source_family"] == "goods"]
		self.assertEqual(len(goods), 1)
		lineage = goods[0]["source_lineage"]["source_lineage"]
		self.assertEqual([r["requisition_item_id"] for r in lineage], ["RQI-001", "RQI-002"])
		self.assertEqual(goods[0]["published_facts"]["quantity"], "250")
		self.assertTrue(goods[0]["immutable_source_id"].startswith("GDS-"))

	def test_labels_and_row_order_do_not_form_identity(self):
		base = {r["stable_key"]: r["response_id"] for r in compile_moh()["response_rows"]}
		projection = support.moh_projection()
		projection["technical_requirements"].reverse()
		projection["technical_requirements"][0]["label"] = "Renamed"
		moved = {r["stable_key"]: r["response_id"] for r in compile_moh(projection)["response_rows"]}
		self.assertEqual(base, moved)

	def test_addendum_classification_by_identity(self):
		assets = support.pack_assets()
		prior = compile_moh()
		successor_input = support.moh_projection()
		successor_input["publication"]["effective_addendum_ids"] = ["ADD-1"]
		successor_input["technical_requirements"][2]["required_value"] = {"value": 32}
		successor = compile_moh(successor_input)
		result = {c["stable_key"]: c for c in addenda.classify(prior, successor, assets.addendum_rules)}
		memory = [c for k, c in result.items() if ":TECH-003:" in k]
		self.assertTrue(memory and all(c["classification"] == "fresh_response_required" for c in memory))
		storage = [c for k, c in result.items() if ":TECH-004:" in k]
		self.assertTrue(storage and all(c["classification"] == "unchanged" and c["copy_prior_answer"] for c in storage))
		self.assertEqual(successor["definition_version"], 2)


class TestTypedFailures(IntegrationTestCase):
	def assertCode(self, code, fn):
		with self.assertRaises(STDTemplateError) as ctx:
			fn()
		self.assertEqual(ctx.exception.code, code, ctx.exception)
		return ctx.exception

	def test_unsupported_currency_is_rejected(self):
		projection = support.moh_projection()
		projection["tender"]["currency"] = "USD"
		exc = self.assertCode("STD_INPUT_UNSUPPORTED", lambda: compile_moh(projection))
		self.assertEqual(exc.identity, "currency")

	def test_county_residents_is_not_released_in_this_candidate(self):
		exc = self.assertCode("STD_INPUT_UNSUPPORTED", lambda: compile_moh(support.variant_projection("county_residents")))
		self.assertEqual(exc.identity, "county_residents")

	def test_unsupported_overlap_blocks(self):
		exc = self.assertCode("STD_INPUT_UNSUPPORTED", lambda: compile_moh(support.variant_projection("unsupported_overlap")))
		self.assertEqual(exc.identity, "overlap_treatment")

	def test_other_reservation_category_is_rejected(self):
		projection = support.moh_projection()
		projection["reservation"]["category"] = "Other disadvantaged group"
		self.assertCode("STD_INPUT_UNSUPPORTED", lambda: compile_moh(projection))

	def test_unknown_projection_key_is_rejected(self):
		projection = support.moh_projection()
		projection["tender"]["surprise"] = "x"
		self.assertCode("STD_INPUT_UNSUPPORTED", lambda: compile_moh(projection))

	def test_unknown_characteristic_control_is_rejected(self):
		projection = support.moh_projection()
		projection["technical_requirements"][0]["control"] = "FREE_FORM"
		self.assertCode("STD_INPUT_UNSUPPORTED", lambda: compile_moh(projection))

	def test_wrong_renderer_version_is_unsupported(self):
		caps = dict(CAPS, supported_renderer_version="2.0.0")
		self.assertCode("STD_RENDERER_UNSUPPORTED", lambda: compile_moh(caps=caps))

	def test_renderer_missing_a_control_is_unsupported(self):
		caps = dict(CAPS, controls=[c for c in CAPS["controls"] if c != "CTL-PORTS-LIST"])
		self.assertCode("STD_RENDERER_UNSUPPORTED", lambda: compile_moh(caps=caps))

	def test_unregistered_renderer_has_no_fallback(self):
		self.assertCode("STD_RENDERER_UNSUPPORTED", lambda: registry.bid_workspace_capabilities("BDS-GOODS-IT-V1", "0.9.0"))

	def _assets_with(self, mutate):
		files = support.pack_files()
		name, data = mutate(json.loads(files["response_rules"]), json.loads(files["downstream_rules"]), json.loads(files["product_profile"]))
		files[name] = json.dumps(data).encode()
		return lambda: release_assets.load(files, official_source_digest="0" * 64, bundle_digest="1" * 64)

	def test_unknown_control_in_a_rule_is_invalid(self):
		def mutate(rules, downstream, profile):
			rules["rules"][0]["field_definitions"][0]["control_id"] = "CTL-RICH-EDITOR"
			return "response_rules", rules

		self.assertCode("STD_DEFINITION_INVALID", self._assets_with(mutate))

	def test_orphan_mapping_is_invalid(self):
		def mutate(rules, downstream, profile):
			extra = dict(downstream["mappings"][0], mapping_id="DM-ORPHAN", response_rule_id="RR-NONE")
			downstream["mappings"].append(extra)
			return "downstream_rules", downstream

		self.assertCode("STD_DEFINITION_INVALID", self._assets_with(mutate))

	def test_executable_expression_is_invalid(self):
		def mutate(rules, downstream, profile):
			rules["rules"][0]["field_definitions"][0]["help_text"] = "lambda x: x"
			return "response_rules", rules

		self.assertCode("STD_DEFINITION_INVALID", self._assets_with(mutate))

	def test_unknown_top_level_key_is_invalid(self):
		def mutate(rules, downstream, profile):
			profile["weights"] = {"TECH": 10}
			return "product_profile", profile

		self.assertCode("STD_DEFINITION_INVALID", self._assets_with(mutate))

	def test_negative_treatment_needs_a_reason(self):
		def mutate(rules, downstream, profile):
			for m in downstream["mappings"]:
				if m["contract_treatment"] == "Not carried forward":
					m["reason"] = ""
					break
			return "downstream_rules", downstream

		self.assertCode("STD_DEFINITION_INVALID", self._assets_with(mutate))

	def test_floats_are_refused_by_canonical_json(self):
		with self.assertRaises(CanonicalError):
			canonical_json({"amount": 1.5})


class TestPurity(IntegrationTestCase):
	def test_compiler_and_release_packages_import_no_frappe(self):
		base = Path(__file__).resolve().parents[1]
		for package in ("compiler", "release", "renderers"):
			for path in sorted((base / package).glob("*.py")):
				for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
					names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
					self.assertFalse(any(n == "frappe" or n.startswith("frappe.") for n in names), f"{package}/{path.name} imports frappe")
