# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Release-vocabulary extensions for template release 1.2 (BDS-CHG-001 v0.8
owner decisions OD-E and OD-I; STD-TPL-001 v0.12 §8.1 and the proposed
v0.13 contract):

- `supplied_value`: a response the bidder never types; Bid Submission
  copies it read-only from the organisation snapshot, the bidder
  arrangement, a joint-venture member's account or the signatory assignment;
- `label_parameters`: named values Bid Submission puts into a label at bid
  time (the bidder's name, an addendum's reference);
- the `per_arrangement_member` composition repetition (one group per
  joint-venture member, identity-stable for the arrangement);
- selectors SEL-EFFECTIVE-ADDENDA (one acknowledgement per effective
  addendum) and SEL-WARRANTY-OBLIGATIONS (one row per applicable
  warranty/support obligation, characteristic-style controls);
- renderer BDS-GOODS-IT-V1 1.1.0, which declares them.

Every extension is optional and additive: the frozen release 1.1 assets
(`vectors/release_1_1/`) must still load and compile byte for byte.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.compiler import assets as release_assets
from kentender_procurement.std_templates.compiler.canonical import pretty_json
from kentender_procurement.std_templates.compiler.definition import compile_published_bid_definition
from kentender_procurement.std_templates.compiler.errors import STDTemplateError
from kentender_procurement.std_templates.renderers import registry

VECTORS = Path(__file__).resolve().parent / "vectors" / "release_1_1"
EXPECTED = json.loads((VECTORS / "moh_published_bid_definition_expected.json").read_text(encoding="utf-8"))
CAPS_1_0 = registry.bid_workspace_capabilities("BDS-GOODS-IT-V1", "1.0.0")
SOURCES = [
	{"source_id": "SV-ORGANISATION", "meaning": "Lead organisation snapshot.", "facts": ["legal_name", "country", "registered_address"], "repetition": "one"},
	{"source_id": "SV-ARRANGEMENT", "meaning": "Bidder arrangement.", "facts": ["tenderer_name", "arrangement_type"], "repetition": "one"},
	{"source_id": "SV-ARRANGEMENT-MEMBER", "meaning": "One joint-venture member's account.", "facts": ["legal_name"], "repetition": "per_arrangement_member"},
]
PARAMETERS = [{"parameter": "bidder_name", "meaning": "Tenderer name."}, {"parameter": "addendum_reference", "meaning": "Addendum reference."}]


def raw() -> dict[str, dict]:
	return {name: json.loads((VECTORS / Path(rel).name).read_text(encoding="utf-8")) for name, rel in release_assets.ASSET_FILES.items()}


def load(docs: dict[str, dict]):
	files = {name: json.dumps(doc).encode("utf-8") for name, doc in docs.items()}
	return release_assets.load(files, official_source_digest=EXPECTED["official_source_digest"], bundle_digest=EXPECTED["bundle_digest"])


def projection(addenda=()) -> dict:
	data = json.loads((VECTORS / "moh_input.json").read_text(encoding="utf-8"))
	data["publication"]["effective_addendum_ids"] = list(addenda)
	return data


def with_version(docs: dict[str, dict], version: str = "1.1.0") -> dict[str, dict]:
	for doc in docs.values():
		doc["supported_renderer_version"] = version
	return docs


def extended(mutate) -> dict[str, dict]:
	docs = with_version(raw())
	docs["product_profile"]["supplied_value_sources"] = copy.deepcopy(SOURCES)
	docs["product_profile"]["label_parameters"] = copy.deepcopy(PARAMETERS)
	mutate(docs)
	return docs


def rule(docs, rule_id):
	return next(r for r in docs["response_rules"]["rules"] if r["rule_id"] == rule_id)


def field(docs, rule_id, key):
	return next(f for f in rule(docs, rule_id)["field_definitions"] if f["field_key"] == key)


def compile_with(docs, proj=None, version="1.1.0"):
	caps = registry.bid_workspace_capabilities("BDS-GOODS-IT-V1", version)
	return compile_published_bid_definition(load(docs), proj or projection(), renderer_capabilities=caps)


class TestRelease11Unchanged(IntegrationTestCase):
	def test_the_frozen_release_1_1_still_compiles_byte_for_byte(self):
		files = {name: (VECTORS / Path(rel).name).read_bytes() for name, rel in release_assets.ASSET_FILES.items()}  # exact bytes: the digests bind them
		assets = release_assets.load(files, official_source_digest=EXPECTED["official_source_digest"], bundle_digest=EXPECTED["bundle_digest"])
		definition = compile_published_bid_definition(assets, projection(), renderer_capabilities=CAPS_1_0)
		self.assertEqual(pretty_json(definition), (VECTORS / "moh_published_bid_definition_expected.json").read_text(encoding="utf-8"))


class TestSuppliedValuesAndLabelParameters(IntegrationTestCase):
	def assertInvalid(self, docs, code="STD_DEFINITION_INVALID"):
		with self.assertRaises(STDTemplateError) as ctx:
			load(docs)
		self.assertEqual(ctx.exception.code, code, ctx.exception)

	def test_a_supplied_value_is_carried_on_the_row_and_checked_against_the_catalogue(self):
		def mutate(docs):
			field(docs, "RR-SUPPLIER-DETAILS", "legal_name")["supplied_value"] = {"source_id": "SV-ORGANISATION", "fact": "legal_name"}

		definition = compile_with(extended(mutate))
		row = next(r for r in definition["response_rows"] if r["stable_key"].endswith(":RR-SUPPLIER-DETAILS:legal_name"))
		self.assertEqual(row["field"]["supplied_value"], {"source_id": "SV-ORGANISATION", "fact": "legal_name"})
		other = next(r for r in definition["response_rows"] if r["stable_key"].endswith(":RR-SUPPLIER-DETAILS:year_of_registration"))
		self.assertNotIn("supplied_value", other["field"])
		for bad in ({"source_id": "SV-NOWHERE", "fact": "legal_name"}, {"source_id": "SV-ORGANISATION", "fact": "shoe_size"}, {"source_id": "SV-ORGANISATION"}):
			with self.subTest(bad=bad):
				self.assertInvalid(extended(lambda d, bad=bad: field(d, "RR-SUPPLIER-DETAILS", "legal_name").__setitem__("supplied_value", bad)))
		# a per-member source belongs only to a per-member composition
		self.assertInvalid(extended(lambda d: field(d, "RR-SUPPLIER-DETAILS", "legal_name").__setitem__("supplied_value", {"source_id": "SV-ARRANGEMENT-MEMBER", "fact": "legal_name"})))

	def test_label_parameters_must_match_the_placeholders_in_the_label(self):
		def mutate(docs):
			f = field(docs, "RR-SUBMISSION", "confirmed")
			f["label"] = "I confirm that the information in this bid is correct and that I am authorised to submit it for {bidder_name}."
			f["label_parameters"] = ["bidder_name"]

		definition = compile_with(extended(mutate))
		row = next(r for r in definition["response_rows"] if r["stable_key"].endswith(":RR-SUBMISSION:confirmed"))
		self.assertEqual(row["field"]["label_parameters"], ["bidder_name"])
		self.assertIn("{bidder_name}", row["field"]["label"])

		def undeclared(docs):
			field(docs, "RR-SUBMISSION", "confirmed")["label"] = "Submit for {bidder_name}."

		self.assertInvalid(extended(undeclared))

		def unused(docs):
			field(docs, "RR-SUBMISSION", "confirmed")["label_parameters"] = ["bidder_name"]

		self.assertInvalid(extended(unused))

		def unknown(docs):
			f = field(docs, "RR-SUBMISSION", "confirmed")
			f["label"], f["label_parameters"] = "Submit for {nickname}.", ["nickname"]

		self.assertInvalid(extended(unknown))

	def test_the_1_0_0_renderer_refuses_the_new_vocabulary(self):
		def mutate(docs):
			field(docs, "RR-SUPPLIER-DETAILS", "legal_name")["supplied_value"] = {"source_id": "SV-ORGANISATION", "fact": "legal_name"}

		docs = extended(mutate)
		with_version(docs, "1.0.0")
		with self.assertRaises(STDTemplateError) as ctx:
			compile_with(docs, version="1.0.0")
		self.assertEqual(ctx.exception.code, "STD_RENDERER_UNSUPPORTED")


class TestNewSelectors(IntegrationTestCase):
	def test_each_effective_addendum_gets_its_own_acknowledgement_and_none_without_one(self):
		def mutate(docs):
			docs["product_profile"]["source_selectors"].append("SEL-EFFECTIVE-ADDENDA")
			ack = rule(docs, "RR-DOC-ACK")
			ack["source_selector"] = {"selector": "SEL-EFFECTIVE-ADDENDA"}
			f = ack["field_definitions"][0]
			f["label"], f["label_parameters"] = "I have reviewed {addendum_reference} and understand how it changes this Tender.", ["addendum_reference"]

		docs = extended(mutate)
		none = compile_with(docs)
		self.assertEqual([r for r in none["response_rows"] if r["identity"]["source_family"] == "document"], [])
		self.assertEqual(next(s for s in none["sections"] if s["section_id"] == "TASK-DOCUMENTS")["groups"], [])
		two = compile_with(docs, projection(["TDA-00001", "TDA-00002"]))
		rows = [r for r in two["response_rows"] if r["identity"]["source_family"] == "document"]
		self.assertEqual([r["identity"]["immutable_source_id"] for r in rows], ["TDA-00001", "TDA-00002"])
		group = next(s for s in two["sections"] if s["section_id"] == "TASK-DOCUMENTS")["groups"][0]
		self.assertEqual(group["published_facts"], {"addendum_id": "TDA-00001"})

	def test_warranty_obligations_become_one_row_each_with_released_controls(self):
		def mutate(docs):
			docs["product_profile"]["source_selectors"].append("SEL-WARRANTY-OBLIGATIONS")
			comp = next(c for c in docs["product_profile"]["compositions"] if c["composition_id"] == "COMP-WARRANTY-SUPPORT")
			comp["permitted_controls"] = sorted(set(comp["permitted_controls"]) | {"CTL-SINGLE-CHOICE", "CTL-SHORT-TEXT"})
			ws = rule(docs, "RR-WARRANTY-SUPPORT")
			ws["source_selector"] = {"selector": "SEL-WARRANTY-OBLIGATIONS"}
			ws["field_definitions"] = [
				copy.deepcopy(field(docs, "RR-TECHNICAL", "compliance")),
				copy.deepcopy(field(docs, "RR-TECHNICAL", "offered_value")),
				copy.deepcopy(field(docs, "RR-WARRANTY-SUPPORT", "evidence")),
			]
			for irule in docs["addendum_identity_rules"]["identity_rules"]:
				if irule["source_family"] == "warranty_support":
					irule["material_facts"] = ["comparison", "control", "required_value"]

		definition = compile_with(extended(mutate))
		groups = [g for s in definition["sections"] for g in s["groups"] if g["rule_id"] == "RR-WARRANTY-SUPPORT"]
		self.assertEqual(
			[(g["immutable_source_id"], g["published_facts"]["comparison"], g["published_facts"]["required_value_display"]) for g in groups],
			[
				("WS-MINIMUM-WARRANTY", "Minimum", "36 months"), ("WS-ONSITE-SUPPORT", "Required", "Yes"), ("WS-RESPONSE-TIME", "Maximum", "8 hours"),
				("WS-MANUFACTURER-SUPPORT", "Required", "Yes"), ("WS-SERVICE-LOCATION", "Required", "Within Kenya"),
				("WS-SUPPORT-CONTACTS", "Required", "Supplier to provide escalation and warranty-contact details."),
			],
		)
		controls = {r["identity"]["immutable_source_id"]: r["field"]["control_id"] for r in definition["response_rows"] if r["stable_key"].endswith(":offered_value") and r["identity"]["source_family"] == "warranty_support"}
		self.assertEqual(controls, {"WS-MINIMUM-WARRANTY": "CTL-INTEGER", "WS-ONSITE-SUPPORT": "CTL-YES-NO", "WS-RESPONSE-TIME": "CTL-INTEGER", "WS-MANUFACTURER-SUPPORT": "CTL-YES-NO", "WS-SERVICE-LOCATION": "CTL-SHORT-TEXT", "WS-SUPPORT-CONTACTS": "CTL-SHORT-TEXT"})
		proj = projection()
		proj["warranty_support"].update({"onsite_support_required": False, "service_location_constraint": ""})
		fewer = compile_with(extended(mutate), proj)
		self.assertEqual(sorted({g["immutable_source_id"] for s in fewer["sections"] for g in s["groups"] if g["rule_id"] == "RR-WARRANTY-SUPPORT"}), ["WS-MANUFACTURER-SUPPORT", "WS-MINIMUM-WARRANTY", "WS-RESPONSE-TIME", "WS-SUPPORT-CONTACTS"])

	def test_a_per_member_composition_marks_its_group_for_repetition_by_arrangement_member(self):
		def mutate(docs):
			profile = docs["product_profile"]
			profile["source_selectors"].append("SEL-ARRANGEMENT-MEMBERS")
			profile["compositions"].append({"composition_id": "COMP-JV-MEMBER", "label": "Joint-venture member", "permitted_controls": ["CTL-SHORT-TEXT", "CTL-INTEGER"], "repetition": "per_arrangement_member", "task_id": "TASK-COMPANY"})
			base = copy.deepcopy(rule(docs, "RR-SUPPLIER-DETAILS"))
			base.update({"rule_id": "RR-JV-MEMBER", "composition_id": "COMP-JV-MEMBER", "source_selector": {"selector": "SEL-ARRANGEMENT-MEMBERS"}, "identity_suffix": "JVM", "order": 15, "evaluation_mapping_id": "DM-JV-MEMBER", "contract_mapping_id": "DM-JV-MEMBER"})
			name = copy.deepcopy(field(docs, "RR-SUPPLIER-DETAILS", "legal_name"))
			name.update({"field_key": "member_legal_name", "supplied_value": {"source_id": "SV-ARRANGEMENT-MEMBER", "fact": "legal_name"}})
			year = copy.deepcopy(field(docs, "RR-SUPPLIER-DETAILS", "year_of_registration"))
			year["field_key"] = "member_year_of_registration"
			base["field_definitions"] = [name, year]
			docs["response_rules"]["rules"].append(base)
			mapping = copy.deepcopy(next(m for m in docs["downstream_rules"]["mappings"] if m["mapping_id"] == "DM-SUPPLIER-DETAILS"))
			mapping.update({"mapping_id": "DM-JV-MEMBER", "response_rule_id": "RR-JV-MEMBER"})
			docs["downstream_rules"]["mappings"].append(mapping)

		definition = compile_with(extended(mutate))
		groups = {g["rule_id"]: g for s in definition["sections"] for g in s["groups"]}
		self.assertEqual((groups["RR-JV-MEMBER"]["repetition"], groups["RR-JV-MEMBER"]["immutable_source_id"]), ("per_arrangement_member", "JV-MEMBER"))
		self.assertNotIn("repetition", groups["RR-SUPPLIER-DETAILS"])

		def bad_repetition(docs):
			mutate(docs)
			next(c for c in docs["product_profile"]["compositions"] if c["composition_id"] == "COMP-JV-MEMBER")["repetition"] = "per_whim"

		with self.assertRaises(STDTemplateError):
			load(extended(bad_repetition))


class TestRelease12PackDecisions(IntegrationTestCase):
	"""The owner decisions release 1.2 carries, read from the pack's own
	expected definition (test_compiler proves the pack compiles to it)."""

	def setUp(self):
		from kentender_procurement.std_templates.services.installer import DEFAULT_PACKAGE

		self.definition = json.loads((DEFAULT_PACKAGE / "06_runtime/moh_published_bid_definition_expected.json").read_text(encoding="utf-8"))

	def row(self, rule_id, key):
		return next(r for r in self.definition["response_rows"] if r["stable_key"].endswith(f":{rule_id}:{key}"))

	def test_the_first_task_and_the_final_confirmation_use_the_decided_wording(self):
		self.assertEqual(self.definition["sections"][0]["label"], "Tender documents, clarifications and addenda")
		confirmed = self.row("RR-SUBMISSION", "confirmed")["field"]
		self.assertEqual(
			(confirmed["label"], confirmed["label_parameters"]),
			("I confirm that the information, declarations and evidence in this bid are correct and that I am authorised to submit it for {bidder_name}.", ["bidder_name"]),
		)

	def test_the_security_instrument_is_for_exactly_the_published_amount(self):
		# PPRA Goods STD ITT 18.1 "in the amount and currency specified in the TDS";
		# BDS-CHG-001 v0.8 §4.8 amount and currency "Must match the published requirement".
		params = self.row("RR-TENDER-SECURITY", "instrument_amount")["validation"]["parameters"]
		self.assertEqual((params["minimum"], params["maximum"], params["currency"]), ("500000.00", "500000.00", "KES"))

	def test_every_representative_fact_the_source_forms_ask_for_is_captured(self):
		# Tenderer Information Form item 6 and the JV Members Information Form item 6:
		# the authorised representative's name, address, telephone and email.
		for rule_id, prefix in (("RR-SUPPLIER-DETAILS", "representative_"), ("RR-JV-MEMBER", "member_representative_")):
			for fact in ("name", "address", "email", "telephone"):
				with self.subTest(rule=rule_id, fact=fact):
					self.assertEqual(self.row(rule_id, prefix + fact)["required"], {"rule_id": "RQ-ALWAYS"})
		# the address is typed by the bidder: no Account or arrangement holds it
		self.assertNotIn("supplied_value", self.row("RR-SUPPLIER-DETAILS", "representative_address")["field"])
		self.assertNotIn("supplied_value", self.row("RR-JV-MEMBER", "member_representative_address")["field"])
