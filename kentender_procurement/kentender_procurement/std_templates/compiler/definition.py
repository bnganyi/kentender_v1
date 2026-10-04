# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`CompilePublishedBidDefinition` — the one deterministic, side-effect-free
compiler (STD-TPL-IMP-001 v1.0 §7; STD-TPL-001 v0.10 §§8–10, 13.6–13.7).

Inputs: the exact release assets (`assets.ReleaseAssets`), one
`TenderVersionProjection v1` (which carries the publication identity and the
ordered effective addenda) and the renderer adapter's declared capabilities.
Output: the complete `PublishedBidDefinition v1` object, or a typed
`STDTemplateError`. The curation CLI adapter and the production Tenders
service both call this function; neither may keep a second algorithm.
Pure Python: no Frappe import, no clock, no randomness.
"""

from __future__ import annotations

import copy
from typing import Any

from kentender_procurement.std_templates.compiler import compatibility, locked_text
from kentender_procurement.std_templates.compiler import projection as proj
from kentender_procurement.std_templates.compiler.assets import CHARACTERISTIC, LOCKED_COMPOSITIONS, ReleaseAssets
from kentender_procurement.std_templates.compiler.canonical import sha256_hex, short_hash
from kentender_procurement.std_templates.compiler.errors import fail
from kentender_procurement.std_templates.compiler.selectors import APPLICABILITY, SELECTORS

DEFINITION_FIELDS: tuple[str, ...] = (
	"bid_definition_id",
	"definition_version",
	"tender_id",
	"tender_version_id",
	"publication_id",
	"effective_addendum_ids",
	"submission_deadline",
	"template_family",
	"template_release_id",
	"product_profile_id",
	"renderer_profile_id",
	"supported_renderer_version",
	"package_digest",
	"official_source_digest",
	"bundle_digest",
	"response_rules_digest",
	"downstream_rules_digest",
	"addendum_identity_rules_digest",
	"sections",
	"response_rows",
	"price_rows",
	"declaration_texts",
	"reservation_treatment",
	"evaluation_mappings",
	"contract_mappings",
	"definition_digest",
)

CAPABILITY_KEYS: tuple[str, ...] = (
	"renderer_profile_id",
	"supported_renderer_version",
	"controls",
	"compositions",
	"validations",
	"required_rules",
	"visibility_rules",
	"supplied_value_sources",
	"label_parameters",
	"repetitions",
)


def _check_renderer(assets: ReleaseAssets, capabilities: dict[str, Any]) -> None:
	env = assets.envelope
	if not isinstance(capabilities, dict) or set(capabilities) != set(CAPABILITY_KEYS):
		fail("STD_RENDERER_UNSUPPORTED", "The renderer adapter did not declare its capabilities.", identity=env["renderer_profile_id"])
	if (capabilities["renderer_profile_id"], capabilities["supported_renderer_version"]) != (env["renderer_profile_id"], env["supported_renderer_version"]):
		fail(
			"STD_RENDERER_UNSUPPORTED",
			"The renderer adapter is not the exact profile and version this release supports.",
			identity=f"{env['renderer_profile_id']}@{env['supported_renderer_version']}",
		)
	profile = assets.profile
	needed_controls = {c["control_id"] for c in profile["controls"]}
	needed = {
		"controls": needed_controls,
		"compositions": {c["composition_id"] for c in profile["compositions"]},
		"validations": {v["validation_id"] for v in profile["validations"]},
		"required_rules": {r["rule_id"] for r in profile["required_rules"]},
		"visibility_rules": {r["rule_id"] for r in profile["visibility_rules"]},
		# release 1.2 vocabulary; a release without it needs none of these
		"supplied_value_sources": {s["source_id"] for s in profile.get("supplied_value_sources", [])},
		"label_parameters": {p["parameter"] for p in profile.get("label_parameters", [])},
		"repetitions": {c["repetition"] for c in profile["compositions"] if c["repetition"] not in ("one", "per_source")},
	}
	for kind, ids in needed.items():
		unsupported = sorted(ids - set(capabilities[kind]))
		if unsupported:
			fail("STD_RENDERER_UNSUPPORTED", f"The renderer does not support {kind.replace('_', ' ')[:-1]} {unsupported[0]}.", identity=unsupported[0])


def _resolve_parameters(params: dict[str, Any], facts: dict[str, Any], identity: str) -> dict[str, Any]:
	out: dict[str, Any] = {}
	for name, value in sorted(params.items()):
		if isinstance(value, dict):
			fact = value["source_fact"]
			if fact not in facts:
				fail("STD_DEFINITION_INVALID", f"Source fact {fact!r} is unavailable.", identity=identity)
			out[name] = copy.deepcopy(facts[fact])
		else:
			out[name] = copy.deepcopy(value)
	return out


def _resolve_required(rule: dict[str, Any], flags: dict[str, bool], identity: str) -> dict[str, Any]:
	if rule["rule_id"] == "RQ-WHEN-SOURCE-FLAG":
		if rule["flag"] not in flags:
			fail("STD_DEFINITION_INVALID", f"Source flag {rule['flag']!r} is unavailable.", identity=identity)
		return {"rule_id": "RQ-ALWAYS" if flags[rule["flag"]] else "RQ-NEVER"}
	return copy.deepcopy(rule)


def _field_contract(fdef: dict[str, Any], facts: dict[str, Any], profile: dict[str, Any], identity: str) -> tuple[str, str, dict[str, Any]]:
	if fdef["control_id"] == CHARACTERISTIC:
		kind = facts.get("control")
		spec = profile["characteristic_controls"].get(kind)
		if not spec:
			fail("STD_INPUT_UNSUPPORTED", f"Technical characteristic control {kind!r} is not released.", identity=identity)
		return spec["control_id"], spec["validation_id"], _resolve_parameters(spec["validation_parameters"], facts, identity)
	return fdef["control_id"], fdef["validation_id"], _resolve_parameters(fdef["validation_parameters"], facts, identity)


def _field_view(fdef: dict[str, Any], control_id: str) -> dict[str, Any]:
	"""The row's field block. The release 1.2 keys appear only when a field
	declares them, so a release without them compiles byte for byte as before."""
	view: dict[str, Any] = {"field_key": fdef["field_key"], "label": fdef["label"], "control_id": control_id, "help_text": fdef["help_text"]}
	if "supplied_value" in fdef:
		view["supplied_value"] = copy.deepcopy(fdef["supplied_value"])
	if "label_parameters" in fdef:
		view["label_parameters"] = list(fdef["label_parameters"])
	return view


def _stable_key(family: str, source_id: str, rule_id: str, field_key: str) -> str:
	return f"{family}:{source_id}:{rule_id}:{field_key}"


def compile_published_bid_definition(
	assets: ReleaseAssets, projection: dict[str, Any], *, renderer_capabilities: dict[str, Any]
) -> dict[str, Any]:
	proj.validate(projection)
	env = assets.envelope
	profile = assets.profile
	if projection["template_key"] != env["template_key"]:
		fail("STD_INPUT_UNSUPPORTED", "The Tender Version was prepared for a different Tender format.", identity="template_key")
	if projection["expected_renderer_profile_id"] != env["renderer_profile_id"]:
		fail("STD_RENDERER_UNSUPPORTED", "The Tender Version expects a different renderer profile.", identity=projection["expected_renderer_profile_id"])
	_check_renderer(assets, renderer_capabilities)
	checks = compatibility.evaluate(profile, compatibility.facts_from_projection(projection))
	failed = compatibility.first_failure(checks)
	if failed:
		fail(
			"STD_INPUT_UNSUPPORTED",
			f"{failed['check']}: this Tender format supports {failed['required']}; the Tender has {failed['actual']}.",
			identity=failed["fact"],
			detail={"checks": checks},
		)

	constants = profile["document_constants"]
	context = proj.document_context(projection, constants)
	tender = projection["tender"]
	tvid = tender["tender_version_id"]
	publication = projection["publication"]
	tasks = {t["task_id"]: t for t in profile["tasks"]}
	repetitions = {c["composition_id"]: c["repetition"] for c in profile["compositions"]}
	mappings = assets.mappings
	identity_rules = {r["source_family"]: r for r in assets.addendum_rules["identity_rules"]}
	rules = sorted(assets.rules, key=lambda r: (tasks[r["task_id"]]["order"], r["order"], r["rule_id"]))

	response_rows: list[dict[str, Any]] = []
	groups_by_task: dict[str, list[dict[str, Any]]] = {task_id: [] for task_id in tasks}
	declaration_texts: list[dict[str, Any]] = []
	price_rows: list[dict[str, Any]] = []
	rule_responses: dict[str, list[str]] = {}
	seen_ids: dict[str, str] = {}
	sequence = 0

	for rule in rules:
		applies = APPLICABILITY[rule["applicability"]["rule_id"]](projection)
		if not applies:
			continue
		selector = rule["source_selector"]
		spec = SELECTORS[selector["selector"]]
		params = {k: v for k, v in selector.items() if k != "selector"}
		instances = spec.select(projection, params, constants)
		lock: dict[str, Any] | None = None
		if rule["composition_id"] in LOCKED_COMPOSITIONS:
			resolved = locked_text.resolve(rule["locked_text"], context, rule["rule_id"])
			lock = {
				"text_id": f"TXT-{rule['rule_id']}",
				"text_version": rule["text_version"],
				"source_text_digest": rule["source_text_digest"],
				"resolved_text_digest": locked_text.text_digest(resolved),
			}
			declaration_texts.append(
				{
					**lock,
					"rule_id": rule["rule_id"],
					"source_locator": rule["source_locator"],
					"document_anchor": rule["document_anchor"],
					"locked_text": rule["locked_text"],
					"resolved_text": resolved,
				}
			)
		material_facts = identity_rules[rule["source_family"]]["material_facts"]
		for instance in instances:
			facts = dict(instance["facts"])
			if lock:
				facts.update(lock)
			source_id = instance["immutable_source_id"]
			group_key = f"{rule['rule_id']}/{source_id}"
			group_ids: dict[str, str] = {}
			for fdef in rule["field_definitions"]:
				identity = f"{rule['rule_id']}.{fdef['field_key']}"
				control_id, validation_id, vparams = _field_contract(fdef, facts, profile, identity)
				required = _resolve_required(fdef["required_rule"], instance["flags"], identity)
				evidence = copy.deepcopy(fdef["evidence_rule"])
				if evidence is not None:
					evidence["mandatory"] = required["rule_id"] == "RQ-ALWAYS"
				tuple_identity = {
					"published_tender_version_id": tvid,
					"source_family": rule["source_family"],
					"immutable_source_id": source_id,
					"rule_id": rule["rule_id"],
					"field_key": fdef["field_key"],
				}
				response_id = "RSP-" + short_hash(tvid, rule["source_family"], source_id, rule["rule_id"], fdef["field_key"])
				stable = _stable_key(rule["source_family"], source_id, rule["rule_id"], fdef["field_key"])
				if response_id in seen_ids:
					fail("STD_DEFINITION_INVALID", "Two responses resolve to one identity.", identity=stable)
				seen_ids[response_id] = stable
				material = sha256_hex(
					{
						"facts": {name: facts.get(name) for name in material_facts},
						"field": {
							"control_id": control_id,
							"validation_id": validation_id,
							"validation_parameters": vparams,
							"visibility": fdef["visibility_rule"],
							"evidence_type": (evidence or {}).get("evidence_type"),
						},
					}
				)
				sequence += 1
				response_rows.append(
					{
						"response_id": response_id,
						"identity": tuple_identity,
						"stable_key": stable,
						"sequence": sequence,
						"task_id": rule["task_id"],
						"composition_id": rule["composition_id"],
						"group_key": group_key,
						"field": _field_view(fdef, control_id),
						"required": required,
						"visibility": copy.deepcopy(fdef["visibility_rule"]),
						"validation": {"validation_id": validation_id, "parameters": vparams},
						"evidence": evidence,
						"applicability": rule["applicability"]["rule_id"],
						"document_anchor": rule["document_anchor"],
						"source_lineage": copy.deepcopy(instance["lineage"]),
						"material_digest": material,
						"evaluation_mapping_id": rule["evaluation_mapping_id"],
						"contract_mapping_id": rule["contract_mapping_id"],
					}
				)
				group_ids[fdef["field_key"]] = response_id
				rule_responses.setdefault(rule["rule_id"], []).append(response_id)
			group = {
				"group_key": group_key,
				"rule_id": rule["rule_id"],
				"composition_id": rule["composition_id"],
				"source_family": rule["source_family"],
				"immutable_source_id": source_id,
				"published_facts": facts,
				"source_lineage": copy.deepcopy(instance["lineage"]),
				"response_ids": list(group_ids.values()),
			}
			if repetitions.get(rule["composition_id"]) == "per_entity":
				# Bid Submission repeats this group once per entity of the bid: the lead
				# organisation, or each member of the joint-venture arrangement.
				group["repetition"] = "per_entity"
			if repetitions.get(rule["composition_id"]) == "per_arrangement_member":
				# Bid Submission repeats this group once per member of the bidder's
				# joint-venture arrangement; each copy keeps these response ids plus
				# the member's organisation identity (STD-TPL-001 v0.13 §13.6).
				group["repetition"] = "per_arrangement_member"
			groups_by_task[rule["task_id"]].append(group)
			if rule["source_family"] == "price_row":
				price_rows.append(
					{
						"price_row_id": "PRC-" + short_hash(tvid, "price_row", source_id),
						"line": facts["line"],
						"kind": "Goods" if selector["selector"] == "SEL-GOODS-GROUPS" else "Related service",
						"immutable_source_id": source_id,
						"description": facts["description"],
						"quantity": facts["quantity"],
						"unit": facts["unit"],
						"currency": facts["currency"],
						"input_response_ids": dict(sorted(group_ids.items())),
						"calculation": {
							"calculation_id": "CALC-LINE-TOTAL",
							"inputs": {"unit_price": group_ids["unit_price"], "quantity": facts["quantity"], "tax_amount": group_ids["tax_amount"]},
						},
						"source_lineage": copy.deepcopy(instance["lineage"]),
					}
				)

	if price_rows:
		price_rows.append(
			{
				"price_row_id": "PRC-" + short_hash(tvid, "price_row", "TENDER-TOTAL"),
				"line": "Total",
				"kind": "Tender total",
				"immutable_source_id": "TENDER-TOTAL",
				"description": "Total Tender Price",
				"quantity": "1",
				"unit": "tender",
				"currency": tender["currency"],
				"input_response_ids": {},
				"calculation": {"calculation_id": "CALC-TENDER-TOTAL", "inputs": {"line_price_row_ids": [r["price_row_id"] for r in price_rows]}},
				"source_lineage": {"tender_version_id": tvid},
			}
		)

	sections = [
		{
			"section_id": task["task_id"],
			"order": task["order"],
			"label": task["label"],
			"purpose": task["purpose"],
			"groups": groups_by_task[task["task_id"]],
		}
		for task in sorted(profile["tasks"], key=lambda t: t["order"])
	]

	evaluation_mappings = []
	contract_mappings = []
	for rule in rules:
		if rule["rule_id"] not in rule_responses:
			continue
		mapping = mappings[rule["evaluation_mapping_id"]]
		ids = rule_responses[rule["rule_id"]]
		evaluation_mappings.append(
			{
				"mapping_id": mapping["mapping_id"],
				"response_rule_id": rule["rule_id"],
				"evaluation_treatment": mapping["evaluation_treatment"],
				"evaluation_group_id": mapping["evaluation_group_id"],
				"evaluation_result_rule": mapping["evaluation_result_rule"],
				"reason": mapping["reason"],
				"response_ids": ids,
			}
		)
		contract_mappings.append(
			{
				"mapping_id": mapping["mapping_id"],
				"response_rule_id": rule["rule_id"],
				"contract_treatment": mapping["contract_treatment"],
				"contract_destination": mapping["contract_destination"],
				"award_reporting_treatment": mapping["award_reporting_treatment"],
				"reason": mapping["reason"],
				"response_ids": ids,
			}
		)

	reservation = projection["reservation"]
	reservation_rules = [r for r in rules if r["source_family"] == "reservation" and r["rule_id"] in rule_responses]
	reservation_mapping = mappings[reservation_rules[0]["evaluation_mapping_id"]] if reservation_rules else None
	reservation_treatment = {
		"category": reservation["category"],
		"county_residents": reservation["county_residents"],
		"rule_snapshot_ids": list(reservation["rule_snapshot_ids"]),
		"overlap_treatment": reservation["overlap_treatment"],
		"planning_designation_is_entitlement": False,
		"eligibility_group_id": reservation_mapping["evaluation_group_id"] if reservation_mapping else None,
		"declaration_text_id": f"TXT-{reservation_rules[0]['rule_id']}" if reservation_rules else None,
		"response_ids": rule_responses.get(reservation_rules[0]["rule_id"], []) if reservation_rules else [],
		"award_reporting_treatment": reservation_mapping["award_reporting_treatment"] if reservation_mapping else "Not applicable",
	}

	definition_version = 1 + len(publication["effective_addendum_ids"])
	definition = {
		"bid_definition_id": "PBD-" + short_hash(env["template_key"], tvid, publication["publication_id"], str(definition_version)),
		"definition_version": definition_version,
		"tender_id": tender["tender_id"],
		"tender_version_id": tvid,
		"publication_id": publication["publication_id"],
		"effective_addendum_ids": list(publication["effective_addendum_ids"]),
		"submission_deadline": tender["submission_deadline"],
		"template_family": env["template_key"],
		"template_release_id": env["release_id"],
		"product_profile_id": env["product_profile_id"],
		"renderer_profile_id": env["renderer_profile_id"],
		"supported_renderer_version": env["supported_renderer_version"],
		"package_digest": tender["package_digest"],
		"official_source_digest": assets.official_source_digest,
		"bundle_digest": assets.bundle_digest,
		"response_rules_digest": assets.digests["response_rules"],
		"downstream_rules_digest": assets.digests["downstream_rules"],
		"addendum_identity_rules_digest": assets.digests["addendum_identity_rules"],
		"sections": sections,
		"response_rows": response_rows,
		"price_rows": price_rows,
		"declaration_texts": declaration_texts,
		"reservation_treatment": reservation_treatment,
		"evaluation_mappings": evaluation_mappings,
		"contract_mappings": contract_mappings,
	}
	definition["definition_digest"] = sha256_hex(definition)
	if tuple(definition) != DEFINITION_FIELDS:
		fail("STD_DEFINITION_INVALID", "Published Bid Definition fields differ from the released contract.", identity="definition")
	return definition


def verify_definition_digest(definition: dict[str, Any]) -> bool:
	body = {k: v for k, v in definition.items() if k != "definition_digest"}
	return sha256_hex(body) == definition.get("definition_digest")
