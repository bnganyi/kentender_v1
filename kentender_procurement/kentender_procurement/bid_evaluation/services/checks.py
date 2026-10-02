# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RunEvaluationChecks (EVL-CHG-001 v0.4 §4.1–§4.2, §5.1, §7.2; plan D7, D23;
tracker EVL4-504, EVL4-505).

A check run records the source bid, definition and rule-implementation
versions, and one result per bid and evaluated response with its reason and
the inputs it compared. A rerun (after a rule correction, a resolved
finding or an opening update) is a new run with its reason; the earlier run
is kept and marked superseded, never edited. Automatic checks start once a
valid source is available: committee appointment governs human access, not
the backend comparison."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_evaluation.services import clock, records, rules, sources

RUN = "Evaluation Check Run"
RESULT = "Evaluation Check Result"
BID = "Evaluation Bid"
ENGINE_VERSION = "evl-checks/1"
PRICE_REQUIREMENT = "RR-PRICE-GOODS"


def current_run(case: str) -> str | None:
	return frappe.db.get_value(RUN, {"evaluation_case": case, "status": "Complete", "superseded_by": ("is", "not set")}, "name", order_by="run_number desc")


def _groups(definition: dict[str, Any]) -> dict[str, dict[str, Any]]:
	return {g["group_key"]: g for s in definition.get("sections") or [] for g in s.get("groups") or []}


def _inputs(body: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
	values = {r["response_id"]: r.get("value") for r in body.get("responses") or [] if not r.get("member")}
	confirmation = body.get("confirmation") or {}
	if confirmation.get("response_id"):
		values[confirmation["response_id"]] = confirmation.get("confirmed")
	files = {}
	for e in body.get("evidence") or []:
		files[e["response_id"]] = files.get(e["response_id"], 0) + len(e.get("files") or [])
	return values, files


def _label(group: dict[str, Any], rule_id: str) -> str:
	from kentender_procurement.bid_evaluation.services.aggregate import requirement_label

	return requirement_label(rule_id, group.get("published_facts") or {}, group.get("group_key", ""))


def results_for(loaded: dict[str, Any] | None, definition: dict[str, Any], body: dict[str, Any]) -> list[dict[str, Any]]:
	"""Every automatic result for one bid (pure: same inputs, same results)."""
	values, files = _inputs(body)
	groups = _groups(definition)
	evaluated = {m["mapping_id"]: m for m in definition.get("evaluation_mappings") or [] if m.get("evaluation_treatment") == "Evaluated"}
	group_values: dict[str, dict[str, Any]] = {}
	for row in definition.get("response_rows") or []:
		group_values.setdefault(row["group_key"], {})[row["field"]["field_key"]] = values.get(row["response_id"])
	out = []
	for row in definition.get("response_rows") or []:
		mapping = evaluated.get(row.get("evaluation_mapping_id"))
		if not mapping or mapping["mapping_id"] == "DM-PRICE-GOODS":
			continue
		field = row["field"]["field_key"]
		rule = rules.rule_for(loaded, mapping["mapping_id"], field) if loaded else None
		if rule and rule["kind"] in rules.NOT_CHECKS:
			continue
		group = groups.get(row["group_key"], {})
		facts = group.get("published_facts") or {}
		label = _label(group, row["identity"]["rule_id"])
		res = rules.check(loaded or {"published_comparison": {}}, rule, facts=facts, value=values.get(row["response_id"]), group_values=group_values[row["group_key"]],
			evidence_files=files.get(row["response_id"], 0), label=label, field_label=row["field"]["label"])
		out.append({"group_id": mapping["evaluation_group_id"], "mapping_id": mapping["mapping_id"], "requirement_key": row["group_key"], "requirement_label": label,
			"response_id": row["response_id"], "field_key": field, "check_kind": res["kind"], "applicable": 0 if res["result"] == rules.NOT_APPLICABLE else 1,
			"result": res["result"], "reason": res["reason"], "basis": res["basis"], "evidence_assessment_required": 1 if res.get("evidence_assessment") else 0,
			"evidence_assessment": res.get("evidence_assessment") or "", "required_display": res.get("required_display") or "", "offered_display": res.get("offered_display") or "",
			"inputs_json": json.dumps(res.get("inputs") or {}, default=str, sort_keys=True), "calculation_json": ""})
	price = rules.calculate_price(definition.get("price_rows") or [], body.get("price") or {}, values)
	out.append({"group_id": "EVG-FINANCIAL", "mapping_id": "DM-PRICE-GOODS", "requirement_key": PRICE_REQUIREMENT, "requirement_label": "Tender price",
		"response_id": "price", "field_key": "total", "check_kind": "calculation", "applicable": 1, "result": price["result"], "reason": price["reason"],
		"basis": "Calculation", "evidence_assessment_required": 0, "evidence_assessment": "", "required_display": "Published calculation",
		"offered_display": f"{price['currency']} {price['submitted_total']}", "inputs_json": "", "calculation_json": json.dumps(price, sort_keys=True)})
	return out


def run(doc, *, reason: str, idempotency_key: str, affected: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Run the checks for every bid of this case. Called inside an Evaluation command."""
	from kentender_procurement.tenders.services import evaluation_seam as tenders

	fact = tenders.publication_fact(doc.tender) or {}
	try:
		loaded = rules.load(cstr(fact.get("product_key")), template_release=cstr(fact.get("template_release")), release_id=cstr(fact.get("template_release_id")))
	except rules.RulesUnavailable:
		loaded = None
	previous = current_run(doc.name)
	number = frappe.db.count(RUN, {"evaluation_case": doc.name}) + 1
	run_doc = records.insert(frappe.get_doc({
		"doctype": RUN, "run_id": f"{doc.name}-RUN-{number:02d}", "evaluation_case": doc.name, "run_number": number, "reason": reason,
		"rules_version": cstr((loaded or {}).get("rules_version")), "rules_digest": cstr((loaded or {}).get("_digest")), "definition_id": doc.definition_id,
		"definition_version": cint(doc.definition_version), "definition_digest": doc.definition_digest, "engine_version": ENGINE_VERSION,
		"affected_json": json.dumps(affected or {}, sort_keys=True), "started_at": clock.now(), "status": "Running",
	}))
	counts: dict[str, int] = {}
	for bid in frappe.get_all(BID, filters={"evaluation_case": doc.name}, fields=["name", "entry_number", "envelope_id", "package_digest"], order_by="entry_number asc"):
		source = sources.cached_package(doc, bid)
		if source.get("outcome") != sources.VERIFIED:
			from kentender_procurement.bid_evaluation.services.errors import fail

			fail("EVL_SOURCE_INCOMPLETE", {"bid": bid.name, "outcome": source.get("outcome"), "reason": source.get("reason")})
		for seq, result in enumerate(results_for(loaded, source["definition"]["definition"], source["body"]), 1):
			result.pop("evidence_assessment", None)
			records.insert(frappe.get_doc({"doctype": RESULT, "result_id": f"{run_doc.name}-B{cint(bid.entry_number):02d}-{seq:04d}", "check_run": run_doc.name,
				"evaluation_case": doc.name, "evaluation_bid": bid.name, **result}))
			counts[result["result"]] = counts.get(result["result"], 0) + 1
	run_doc.status, run_doc.completed_at = "Complete", clock.now()
	records.save(run_doc)
	if previous:
		prior = frappe.get_doc(RUN, previous)
		prior.superseded_by = run_doc.name
		records.save(prior)
	records.bump(doc, current_run=run_doc.name)
	return {"run": run_doc.name, "counts": counts, "rules_available": loaded is not None}
