# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-001 v0.10 §13.5 — the four declarative runtime assets.

`load()` parses `product_profile.json`, `response_rules.json`,
`downstream_rules.json` and `addendum_identity_rules.json` from their exact
bytes, checks the shared release envelope and each asset's closed key set,
and `validate()` proves every rule references only released vocabulary:
tasks, compositions, controls, validations, named required/visibility/
applicability rules, selectors, evaluation groups and contract destinations.
There is no executable expression, arbitrary nesting or implicit default.
Pure Python: no Frappe import.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from kentender_procurement.std_templates.compiler import locked_text
from kentender_procurement.std_templates.compiler.canonical import CanonicalError, canonical_json, is_sha256, sha256_bytes
from kentender_procurement.std_templates.compiler.errors import fail

def _row_tables():
	"""The shared table checker (`kentender_core.utils.row_tables`, pure Python). The release
	tooling runs without Frappe, where importing the kentender_core package would pull
	Frappe in, so the module is then read from its file in the same repository."""
	try:
		from kentender_core.utils import row_tables

		return row_tables
	except ImportError:
		import importlib.util
		from pathlib import Path

		path = Path(__file__).resolve().parents[4] / "kentender_core" / "kentender_core" / "utils" / "row_tables.py"
		spec = importlib.util.spec_from_file_location("kt_row_tables", path)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return module


ENVELOPE: tuple[str, ...] = (
	"schema_version",
	"release_id",
	"template_key",
	"template_release",
	"product_profile_id",
	"renderer_profile_id",
	"supported_renderer_version",
)
SCHEMA_VERSION = 1

ASSET_FILES: dict[str, str] = {
	"product_profile": "06_runtime/product_profile.json",
	"response_rules": "06_runtime/response_rules.json",
	"downstream_rules": "06_runtime/downstream_rules.json",
	"addendum_identity_rules": "06_runtime/addendum_identity_rules.json",
}

ASSET_KEYS: dict[str, tuple[str, ...]] = {
	"product_profile": ENVELOPE
	+ (
		"display_name", "supported_use", "rejected_use", "tasks", "controls", "compositions", "validations",
		"required_rules", "visibility_rules", "applicability_rules", "source_selectors", "source_families",
		"evaluation_groups", "contract_destinations", "characteristic_controls", "calculations",
		"reservation_treatments", "document_constants",
	),
	"response_rules": ENVELOPE + ("rules",),
	"downstream_rules": ENVELOPE + ("mappings",),
	"addendum_identity_rules": ENVELOPE + ("classifications", "identity_rules", "prohibited_comparison_bases"),
}
#: Optional top-level keys, added by release 1.2 (STD-TPL-001 v0.13 §13.5.1).
#: A release without them (1.1) loads unchanged.
OPTIONAL_ASSET_KEYS: dict[str, tuple[str, ...]] = {
	"product_profile": ("supplied_value_sources", "label_parameters"),
	"response_rules": (),
	"downstream_rules": (),
	"addendum_identity_rules": (),
}

SOURCE_FAMILIES: tuple[str, ...] = (
	"document", "supplier", "declaration", "tender_security", "goods", "technical_requirement", "warranty_support",
	"experience", "related_service", "acceptance_requirement", "evidence_requirement", "reservation",
	"county_residents", "price_row",
)
EVALUATION_GROUPS: tuple[str, ...] = ("EVG-ELIGIBILITY", "EVG-TECHNICAL-COMPLIANCE", "EVG-FINANCIAL", "EVG-AWARD")
CLASSIFICATIONS: tuple[str, ...] = ("unchanged", "converted", "fresh_response_required", "removed", "new")
PROHIBITED_BASES: tuple[str, ...] = ("text_similarity", "row_order", "display_label", "client_identity")

RULE_KEYS: tuple[str, ...] = (
	"rule_id", "source_family", "source_selector", "identity_suffix", "task_id", "composition_id", "field_definitions",
	"applicability", "document_anchor", "evaluation_mapping_id", "contract_mapping_id", "order",
)
LOCKED_KEYS: tuple[str, ...] = ("locked_text", "source_locator", "source_text_digest", "text_version")
FIELD_KEYS: tuple[str, ...] = (
	"field_key", "label", "control_id", "required_rule", "visibility_rule", "validation_id", "validation_parameters",
	"evidence_rule", "help_text",
)
#: Optional field keys (release 1.2, STD-TPL-001 v0.13 §13.5.2): a value Bid
#: Submission supplies read-only, and named values it puts into the label.
OPTIONAL_FIELD_KEYS: tuple[str, ...] = ("supplied_value", "label_parameters")
SUPPLIED_VALUE_KEYS: tuple[str, ...] = ("source_id", "fact")
REPETITIONS: tuple[str, ...] = ("one", "per_source", "per_arrangement_member", "per_entity")
PER_MEMBER = "per_arrangement_member"
PER_ENTITY = "per_entity"
ROW_GROUP = ("CTL-ROW-GROUP", "VAL-ROW-GROUP")
ROW_GROUP_PARAMETERS = ("columns", "minimum_rows", "maximum_rows", "totals")
_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")
MAPPING_KEYS: tuple[str, ...] = (
	"mapping_id", "response_rule_id", "evaluation_treatment", "evaluation_group_id", "evaluation_result_rule",
	"contract_treatment", "contract_destination", "award_reporting_treatment", "reason",
)
EVIDENCE_RULE_KEYS: tuple[str, ...] = ("evidence_type", "minimum", "maximum", "linkage_target", "mandatory")

#: Placeholder a technical-response field uses for "the released characteristic
#: control" (STD-TPL-001 v0.10 §8.3); resolved per source row at compile time.
CHARACTERISTIC = "CHARACTERISTIC"

#: Locked-declaration compositions: every rule using one carries `LOCKED_KEYS`.
LOCKED_COMPOSITIONS: frozenset[str] = frozenset({"COMP-LOCKED-DECLARATION", "COMP-RESERVATION-ELIGIBILITY"})

_FORBIDDEN_TOKENS = ("{%", "eval(", "exec(", "lambda", "=>", "function(", "${")


@dataclass
class ReleaseAssets:
	profile: dict[str, Any]
	response_rules: dict[str, Any]
	downstream_rules: dict[str, Any]
	addendum_rules: dict[str, Any]
	digests: dict[str, str]
	official_source_digest: str
	bundle_digest: str
	extras: dict[str, Any] = field(default_factory=dict)

	@property
	def envelope(self) -> dict[str, Any]:
		return {k: self.profile[k] for k in ENVELOPE}

	@property
	def rules(self) -> list[dict[str, Any]]:
		return self.response_rules["rules"]

	@property
	def mappings(self) -> dict[str, dict[str, Any]]:
		return {m["mapping_id"]: m for m in self.downstream_rules["mappings"]}


def _parse(name: str, data: bytes) -> dict[str, Any]:
	try:
		value = json.loads(data.decode("utf-8"))
	except (UnicodeDecodeError, json.JSONDecodeError) as exc:
		fail("STD_DEFINITION_INVALID", f"{name} is not valid UTF-8 JSON: {exc}.", identity=name)
		raise
	if not isinstance(value, dict):
		fail("STD_DEFINITION_INVALID", f"{name} must be a JSON object.", identity=name)
	try:
		canonical_json(value)
	except CanonicalError as exc:
		fail("STD_DEFINITION_INVALID", f"{name}: {exc}.", identity=name)
	return value


def load(files: dict[str, bytes], *, official_source_digest: str, bundle_digest: str) -> ReleaseAssets:
	"""`files` maps each `ASSET_FILES` key to that asset's exact bytes."""
	parsed: dict[str, dict[str, Any]] = {}
	for name in ASSET_FILES:
		if name not in files:
			fail("STD_DEFINITION_INVALID", f"Release asset {name} is missing.", identity=ASSET_FILES[name])
		parsed[name] = _parse(name, files[name])
		keys = set(parsed[name])
		allowed = set(ASSET_KEYS[name])
		if keys - allowed - set(OPTIONAL_ASSET_KEYS[name]):
			fail("STD_DEFINITION_INVALID", f"{name} has unknown top-level key(s): {', '.join(sorted(keys - allowed - set(OPTIONAL_ASSET_KEYS[name])))}.", identity=name)
		if allowed - keys:
			fail("STD_DEFINITION_INVALID", f"{name} is missing key(s): {', '.join(sorted(allowed - keys))}.", identity=name)
	envelope = {k: parsed["product_profile"][k] for k in ENVELOPE}
	if envelope["schema_version"] != SCHEMA_VERSION:
		fail("STD_DEFINITION_INVALID", "Unsupported asset schema version.", identity="schema_version")
	for name, asset in parsed.items():
		for key in ENVELOPE:
			if asset[key] != envelope[key]:
				fail("STD_DEFINITION_INVALID", f"{name} envelope {key} differs from the product profile.", identity=f"{name}.{key}")
	if not is_sha256(official_source_digest) or not is_sha256(bundle_digest):
		fail("STD_DEFINITION_INVALID", "Release source or bundle digest is not a SHA-256 value.", identity="digests")
	assets = ReleaseAssets(
		profile=parsed["product_profile"],
		response_rules=parsed["response_rules"],
		downstream_rules=parsed["downstream_rules"],
		addendum_rules=parsed["addendum_identity_rules"],
		digests={name: sha256_bytes(files[name]) for name in ASSET_FILES},
		official_source_digest=official_source_digest,
		bundle_digest=bundle_digest,
	)
	validate(assets)
	return assets


# ---------------------------------------------------------------------------
# vocabulary validation
# ---------------------------------------------------------------------------


def _ids(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
	out: dict[str, dict[str, Any]] = {}
	for row in rows:
		value = row.get(key)
		if not isinstance(value, str) or not value:
			fail("STD_DEFINITION_INVALID", f"{label} row without {key}.", identity=label)
		if value in out:
			fail("STD_DEFINITION_INVALID", f"Duplicate {label} identifier.", identity=value)
		out[value] = row
	return out


def _scan_strings(value: Any, identity: str, *, allow_template: bool = False) -> None:
	if isinstance(value, str):
		for token in _FORBIDDEN_TOKENS:
			if token in value:
				fail("STD_DEFINITION_INVALID", f"Executable or template syntax {token!r} is not permitted.", identity=identity)
		if not allow_template and ("{{" in value or "}}" in value):
			fail("STD_DEFINITION_INVALID", "Template syntax is only permitted in locked declaration text.", identity=identity)
	elif isinstance(value, list):
		for item in value:
			_scan_strings(item, identity, allow_template=allow_template)
	elif isinstance(value, dict):
		for key, item in value.items():
			_scan_strings(item, identity, allow_template=allow_template and key == "locked_text")


def _check_parameters(params: Any, declared: dict[str, str], selector_facts: set[str], identity: str) -> None:
	if not isinstance(params, dict):
		fail("STD_DEFINITION_INVALID", "Validation parameters must be an object.", identity=identity)
	unknown = set(params) - set(declared)
	if unknown:
		fail("STD_DEFINITION_INVALID", f"Unknown validation parameter(s): {', '.join(sorted(unknown))}.", identity=identity)
	for name, value in params.items():
		if isinstance(value, dict):
			if set(value) != {"source_fact"}:
				fail("STD_DEFINITION_INVALID", "A parameter object may only name a source_fact.", identity=f"{identity}.{name}")
			if value["source_fact"] not in selector_facts:
				fail("STD_DEFINITION_INVALID", f"Source fact {value['source_fact']!r} is not published by this selector.", identity=f"{identity}.{name}")


def _check_row_group(control: str, validation: str, params: dict[str, Any], identity: str) -> None:
	"""A table control and its validation go together, and its definition must be usable:
	named columns of released types, at most ten rows, totals on numeric columns."""
	if (control == ROW_GROUP[0]) != (validation == ROW_GROUP[1]):
		fail("STD_DEFINITION_INVALID", f"{ROW_GROUP[0]} and {ROW_GROUP[1]} are released only together.", identity=identity)
	if control != ROW_GROUP[0]:
		return
	row_tables = _row_tables()
	problems = row_tables.check_definition(params.get("columns"), minimum_rows=params.get("minimum_rows", 0), maximum_rows=params.get("maximum_rows", row_tables.MAX_ROWS), totals=params.get("totals", []))
	if problems:
		fail("STD_DEFINITION_INVALID", f"The table definition is unusable: {problems[0]}", identity=identity)


def _check_named_rule(rule: Any, catalogue: dict[str, dict[str, Any]], identity: str, field_keys: set[str], selector_flags: set[str]) -> None:
	if not isinstance(rule, dict) or rule.get("rule_id") not in catalogue:
		fail("STD_DEFINITION_INVALID", "Unknown named rule.", identity=identity)
	declared = catalogue[rule["rule_id"]]["parameters"]
	params = {k: v for k, v in rule.items() if k != "rule_id"}
	if set(params) != set(declared):
		fail("STD_DEFINITION_INVALID", f"Named rule {rule['rule_id']} needs exactly: {', '.join(sorted(declared)) or 'no parameters'}.", identity=identity)
	if "field_key" in params and params["field_key"] not in field_keys:
		fail("STD_DEFINITION_INVALID", "Named rule refers to an unknown field.", identity=identity)
	if "field_keys" in params and (not params["field_keys"] or not set(params["field_keys"]) <= field_keys):
		fail("STD_DEFINITION_INVALID", "Named rule refers to an unknown field.", identity=identity)
	if "flag" in params and params["flag"] not in selector_flags:
		fail("STD_DEFINITION_INVALID", f"Source flag {params['flag']!r} is not published by this selector.", identity=identity)


def _check_supplied_value(fdef: dict[str, Any], sources: dict[str, dict[str, Any]], comp: dict[str, Any], is_evidence: bool, identity: str) -> None:
	if "supplied_value" not in fdef:
		return
	value = fdef["supplied_value"]
	if not isinstance(value, dict) or set(value) != set(SUPPLIED_VALUE_KEYS) or value["source_id"] not in sources:
		fail("STD_DEFINITION_INVALID", "A supplied value must name a released source and one of its facts.", identity=identity)
	source = sources[value["source_id"]]
	if value["fact"] not in source["facts"]:
		fail("STD_DEFINITION_INVALID", f"Supplied-value source {value['source_id']} does not publish {value['fact']!r}.", identity=identity)
	for repetition, noun in ((PER_MEMBER, "per-member"), (PER_ENTITY, "per-entity")):
		if source["repetition"] == repetition and comp.get("repetition") != repetition:
			fail("STD_DEFINITION_INVALID", f"A {noun} source is only released inside a {noun} composition.", identity=identity)
	if is_evidence:
		fail("STD_DEFINITION_INVALID", "An evidence reference is never a supplied value.", identity=identity)


def _check_label_parameters(fdef: dict[str, Any], catalogue: dict[str, dict[str, Any]], identity: str) -> None:
	used = set(_PLACEHOLDER.findall(fdef["label"]))
	declared = fdef.get("label_parameters")
	if declared is None:
		if used:
			fail("STD_DEFINITION_INVALID", "A label placeholder must be declared in label_parameters.", identity=identity)
		return
	if not isinstance(declared, list) or not declared or len(set(declared)) != len(declared):
		fail("STD_DEFINITION_INVALID", "label_parameters must list distinct released parameters.", identity=identity)
	if not set(declared) <= set(catalogue):
		fail("STD_DEFINITION_INVALID", "A label parameter is not released.", identity=identity)
	if set(declared) != used:
		fail("STD_DEFINITION_INVALID", "label_parameters must match the placeholders in the label exactly.", identity=identity)


def validate(assets: ReleaseAssets) -> None:
	from kentender_procurement.std_templates.compiler import selectors

	profile = assets.profile
	_scan_strings(profile, "product_profile")
	_scan_strings(assets.downstream_rules, "downstream_rules")
	_scan_strings(assets.addendum_rules, "addendum_identity_rules")

	if tuple(profile["source_families"]) != SOURCE_FAMILIES:
		fail("STD_DEFINITION_INVALID", "The source-family vocabulary differs from the released contract.", identity="source_families")
	groups = _ids(profile["evaluation_groups"], "evaluation_group_id", "evaluation group")
	if tuple(groups) != EVALUATION_GROUPS:
		fail("STD_DEFINITION_INVALID", "Exactly the four released evaluation groups are required.", identity="evaluation_groups")
	destinations = _ids(profile["contract_destinations"], "contract_destination_id", "contract destination")
	tasks = _ids(profile["tasks"], "task_id", "task")
	if sorted(t["order"] for t in tasks.values()) != [1, 2, 3, 4, 5]:
		fail("STD_DEFINITION_INVALID", "Exactly five ordered supplier tasks are required.", identity="tasks")
	controls = _ids(profile["controls"], "control_id", "control")
	compositions = _ids(profile["compositions"], "composition_id", "composition")
	for comp_id, comp in compositions.items():
		if comp["task_id"] not in tasks:
			fail("STD_DEFINITION_INVALID", "Composition placed in an unknown task.", identity=comp_id)
		if comp.get("repetition") not in REPETITIONS:
			fail("STD_DEFINITION_INVALID", "Composition repetition is not a released value.", identity=comp_id)
		if not set(comp["permitted_controls"]) <= set(controls):
			fail("STD_DEFINITION_INVALID", "Composition permits an unknown control.", identity=comp_id)
	validations = _ids(profile["validations"], "validation_id", "validation")
	required_rules = _ids(profile["required_rules"], "rule_id", "required rule")
	visibility_rules = _ids(profile["visibility_rules"], "rule_id", "visibility rule")
	applicability = _ids(profile["applicability_rules"], "rule_id", "applicability rule")
	selector_ids = set(profile["source_selectors"])
	missing_code = selector_ids - set(selectors.SELECTORS)
	if missing_code:
		fail("STD_DEFINITION_INVALID", "A released selector has no implementation.", identity=sorted(missing_code)[0])
	unknown_applicability = set(applicability) - set(selectors.APPLICABILITY)
	if unknown_applicability:
		fail("STD_DEFINITION_INVALID", "A released applicability rule has no implementation.", identity=sorted(unknown_applicability)[0])
	for kind, spec in profile["characteristic_controls"].items():
		if spec["control_id"] not in controls or spec["validation_id"] not in validations:
			fail("STD_DEFINITION_INVALID", "Characteristic control maps to unknown vocabulary.", identity=kind)
	supplied_sources = _ids(profile.get("supplied_value_sources", []), "source_id", "supplied-value source")
	for source_id, source in supplied_sources.items():
		if set(source) != {"source_id", "meaning", "facts", "repetition"} or not source["facts"] or source["repetition"] not in ("one", PER_MEMBER, PER_ENTITY):
			fail("STD_DEFINITION_INVALID", "Supplied-value source keys differ from the released contract.", identity=source_id)
	label_parameters = _ids(profile.get("label_parameters", []), "parameter", "label parameter")
	for name, row in label_parameters.items():
		if set(row) != {"parameter", "meaning"} or not _PLACEHOLDER.fullmatch("{" + name + "}"):
			fail("STD_DEFINITION_INVALID", "Label parameter keys differ from the released contract.", identity=name)
	calculations = _ids(profile["calculations"], "calculation_id", "calculation")
	if set(calculations) != {"CALC-LINE-TOTAL", "CALC-TENDER-TOTAL"}:
		fail("STD_DEFINITION_INVALID", "Only the released price calculations are permitted.", identity="calculations")

	rules = _ids(assets.rules, "rule_id", "response rule")
	mappings = _ids(assets.downstream_rules["mappings"], "mapping_id", "mapping")
	used_mappings: set[str] = set()
	for rule_id, rule in rules.items():
		allowed = set(RULE_KEYS) | (set(LOCKED_KEYS) if rule.get("composition_id") in LOCKED_COMPOSITIONS else set())
		if set(rule) != allowed:
			missing = allowed - set(rule)
			extra = set(rule) - allowed
			fail("STD_DEFINITION_INVALID", f"Response rule keys differ: missing {sorted(missing)}, unknown {sorted(extra)}.", identity=rule_id)
		_scan_strings(rule, rule_id, allow_template=True)
		if rule["source_family"] not in SOURCE_FAMILIES:
			fail("STD_DEFINITION_INVALID", "Unknown source family.", identity=rule_id)
		selector = rule["source_selector"]
		if not isinstance(selector, dict) or selector.get("selector") not in selector_ids:
			fail("STD_DEFINITION_INVALID", "Unknown source selector.", identity=rule_id)
		spec = selectors.SELECTORS[selector["selector"]]
		if set(selector) - {"selector"} != set(spec.parameters):
			fail("STD_DEFINITION_INVALID", "Selector parameters differ from its released contract.", identity=rule_id)
		if rule["source_family"] not in spec.families:
			fail("STD_DEFINITION_INVALID", "Selector does not supply this source family.", identity=rule_id)
		if rule["task_id"] not in tasks or rule["composition_id"] not in compositions:
			fail("STD_DEFINITION_INVALID", "Unknown task or composition.", identity=rule_id)
		comp = compositions[rule["composition_id"]]
		if comp["task_id"] != rule["task_id"]:
			fail("STD_DEFINITION_INVALID", "Composition is placed in a different task.", identity=rule_id)
		_check_named_rule(rule["applicability"], applicability, f"{rule_id}.applicability", set(), set())
		if rule["evaluation_mapping_id"] != rule["contract_mapping_id"]:
			fail("STD_DEFINITION_INVALID", "A response rule points to exactly one mapping row.", identity=rule_id)
		if rule["evaluation_mapping_id"] not in mappings:
			fail("STD_DEFINITION_INVALID", "Response rule has no mapping row.", identity=rule_id)
		if mappings[rule["evaluation_mapping_id"]]["response_rule_id"] != rule_id:
			fail("STD_DEFINITION_INVALID", "Mapping row names a different response rule.", identity=rule_id)
		used_mappings.add(rule["evaluation_mapping_id"])
		if not isinstance(rule["order"], int):
			fail("STD_DEFINITION_INVALID", "Rule order must be an integer.", identity=rule_id)
		if not isinstance(rule["document_anchor"], str) or "#" not in rule["document_anchor"]:
			fail("STD_DEFINITION_INVALID", "Rule needs a document anchor (file#id).", identity=rule_id)
		fields = rule["field_definitions"]
		if not isinstance(fields, list) or not fields:
			fail("STD_DEFINITION_INVALID", "Rule defines no fields.", identity=rule_id)
		field_keys: set[str] = set()
		for fdef in fields:
			if not set(FIELD_KEYS) <= set(fdef) <= set(FIELD_KEYS) | set(OPTIONAL_FIELD_KEYS):
				fail("STD_DEFINITION_INVALID", "Field definition keys differ from the released contract.", identity=f"{rule_id}.{fdef.get('field_key')}")
			if fdef["field_key"] in field_keys:
				fail("STD_DEFINITION_INVALID", "Duplicate field key within one rule.", identity=f"{rule_id}.{fdef['field_key']}")
			field_keys.add(fdef["field_key"])
		for fdef in fields:
			fid = f"{rule_id}.{fdef['field_key']}"
			control = fdef["control_id"]
			if control == CHARACTERISTIC:
				if spec.characteristic_kinds is None or fdef["validation_id"] != CHARACTERISTIC:
					fail("STD_DEFINITION_INVALID", "The characteristic control is only released for selectors that publish a characteristic.", identity=fid)
				kinds = list(profile["characteristic_controls"]) if spec.characteristic_kinds == selectors.ALL_KINDS else list(spec.characteristic_kinds)
				if not set(kinds) <= set(profile["characteristic_controls"]):
					fail("STD_DEFINITION_INVALID", "A characteristic kind of this selector is not released.", identity=fid)
				resolved = {profile["characteristic_controls"][k]["control_id"] for k in kinds}
				if not resolved <= set(comp["permitted_controls"]):
					fail("STD_DEFINITION_INVALID", "Composition does not permit every characteristic control.", identity=fid)
			else:
				if control not in controls:
					fail("STD_DEFINITION_INVALID", "Unknown control.", identity=fid)
				if control not in comp["permitted_controls"]:
					fail("STD_DEFINITION_INVALID", "Control not permitted by the composition.", identity=fid)
				if fdef["validation_id"] not in validations:
					fail("STD_DEFINITION_INVALID", "Unknown validation.", identity=fid)
				_check_parameters(fdef["validation_parameters"], validations[fdef["validation_id"]]["parameters"], set(spec.facts), fid)
				_check_row_group(control, fdef["validation_id"], fdef["validation_parameters"], fid)
			_check_named_rule(fdef["required_rule"], required_rules, f"{fid}.required_rule", field_keys - {fdef["field_key"]}, set(spec.flags))
			_check_named_rule(fdef["visibility_rule"], visibility_rules, f"{fid}.visibility_rule", field_keys - {fdef["field_key"]}, set(spec.flags))
			is_evidence = control == "CTL-EVIDENCE-REFERENCE"
			if is_evidence != (fdef["evidence_rule"] is not None):
				fail("STD_DEFINITION_INVALID", "Evidence references need an evidence rule, and only they may have one.", identity=fid)
			if is_evidence and set(fdef["evidence_rule"]) != set(EVIDENCE_RULE_KEYS):
				fail("STD_DEFINITION_INVALID", "Evidence rule keys differ from the released contract.", identity=fid)
			_check_supplied_value(fdef, supplied_sources, comp, is_evidence, fid)
			_check_label_parameters(fdef, label_parameters, fid)
		if rule["composition_id"] in LOCKED_COMPOSITIONS:
			text = rule["locked_text"]
			locked_text.check_template(text, rule_id)
			if locked_text.text_digest(text) != rule["source_text_digest"]:
				fail("STD_DEFINITION_INVALID", "Locked text does not match its recorded digest.", identity=rule_id)
	orphans = set(mappings) - used_mappings
	if orphans:
		fail("STD_DEFINITION_INVALID", "Mapping row is not used by any response rule.", identity=sorted(orphans)[0])
	for mapping_id, mapping in mappings.items():
		if set(mapping) != set(MAPPING_KEYS):
			fail("STD_DEFINITION_INVALID", "Mapping keys differ from the released contract.", identity=mapping_id)
		if mapping["evaluation_treatment"] == "Evaluated":
			if mapping["evaluation_group_id"] not in groups:
				fail("STD_DEFINITION_INVALID", "Evaluated mapping names no released group.", identity=mapping_id)
		elif mapping["evaluation_treatment"] == "Not evaluated":
			if mapping["evaluation_group_id"] is not None:
				fail("STD_DEFINITION_INVALID", "A Not evaluated mapping cannot name a group.", identity=mapping_id)
		else:
			fail("STD_DEFINITION_INVALID", "Evaluation treatment must be Evaluated or Not evaluated.", identity=mapping_id)
		if mapping["contract_treatment"] == "Carried forward":
			if mapping["contract_destination"] not in destinations:
				fail("STD_DEFINITION_INVALID", "Carried-forward mapping names no released destination.", identity=mapping_id)
		elif mapping["contract_treatment"] == "Not carried forward":
			if mapping["contract_destination"] is not None:
				fail("STD_DEFINITION_INVALID", "A Not carried forward mapping cannot name a destination.", identity=mapping_id)
		else:
			fail("STD_DEFINITION_INVALID", "Contract treatment must be Carried forward or Not carried forward.", identity=mapping_id)
		negative = mapping["evaluation_treatment"] == "Not evaluated" or mapping["contract_treatment"] == "Not carried forward"
		if negative and not (isinstance(mapping["reason"], str) and mapping["reason"].strip()):
			fail("STD_DEFINITION_INVALID", "A negative treatment needs a stated reason.", identity=mapping_id)
		if mapping["evaluation_group_id"] == "EVG-AWARD":
			fail("STD_DEFINITION_INVALID", "Award consumes prior results; no response maps to it directly.", identity=mapping_id)

	addendum = assets.addendum_rules
	if tuple(c["classification"] for c in addendum["classifications"]) != CLASSIFICATIONS:
		fail("STD_DEFINITION_INVALID", "Addendum classifications differ from the released five.", identity="classifications")
	if tuple(addendum["prohibited_comparison_bases"]) != PROHIBITED_BASES:
		fail("STD_DEFINITION_INVALID", "Prohibited addendum comparison bases differ from the release.", identity="prohibited_comparison_bases")
	identity_rules = _ids(addendum["identity_rules"], "source_family", "addendum identity rule")
	used_families = {r["source_family"] for r in rules.values()}
	if not used_families <= set(identity_rules):
		fail("STD_DEFINITION_INVALID", "A source family has no addendum identity rule.", identity=sorted(used_families - set(identity_rules))[0])
	for family, irule in identity_rules.items():
		if set(irule["comparison_basis"]) & set(PROHIBITED_BASES):
			fail("STD_DEFINITION_INVALID", "Addendum identity rule uses a prohibited comparison basis.", identity=family)
		spec_facts = set().union(*(set(s.facts) for s in selectors.SELECTORS.values() if family in s.families))
		if not set(irule["material_facts"]) <= spec_facts:
			fail("STD_DEFINITION_INVALID", "Addendum identity rule names an unpublished material fact.", identity=family)
