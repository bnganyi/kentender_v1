# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The automatic checks (EVL-CHG-001 v0.4 §4.1–§4.2; plan D7, D23, D24).

The executable meaning of each automatic rule comes from the curated
evaluation-rules file of the template (`docs/mvp-1-r1/07_tender_templates/
evaluation_rules/<template_key>.json`, owner decision OD-C). Every comparison
value comes from the published bid definition, never from that file or from
an evaluator's setting. A response without a rule, or whose rule cannot be
applied, is Needs review with the reason that its rule is unavailable; no
default fills a missing rule. Free text and "or equivalent" are never read as
compliance. A presence check never verifies authenticity: where the rule
names an evidence assessment, the check reads Meets on presence and the
requirement stays open for a member's evidence finding.

Everything here is a pure function of (rules, definition row, published
facts, submitted values), so the same inputs always give the same results."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from frappe.utils import cstr

MEETS, FAILS, REVIEW, NOT_APPLICABLE = "Meets", "Does not meet", "Needs review", "Not applicable"
RESULTS = (MEETS, FAILS, REVIEW, NOT_APPLICABLE)
#: Kinds that describe a response without checking it: shown, never a pass/fail input.
NOT_CHECKS = ("recorded", "evidence-optional", "calculation-input")
SCHEMA = "kt-evl-rules/1"
RULES_DIR = Path(__file__).resolve().parents[3].parent / "docs/mvp-1-r1/07_tender_templates/evaluation_rules"
UNAVAILABLE = "The automatic comparison rule is unavailable."


class RulesUnavailable(Exception):
	pass


def load(template_key: str, *, template_release: str = "", release_id: str = "") -> dict[str, Any]:
	"""The rules file for this template and release, with its digest."""
	path = RULES_DIR / f"{cstr(template_key)}.json"
	if not template_key or not path.exists():
		raise RulesUnavailable(f"No evaluation rules for {template_key!r}.")
	raw = path.read_bytes()
	doc = json.loads(raw)
	if doc.get("schema") != SCHEMA or doc.get("template_key") != template_key:
		raise RulesUnavailable("The evaluation rules file does not match its template.")
	if template_release or release_id:
		if not any((not template_release or a.get("template_release") == template_release) and (not release_id or a.get("release_id") == release_id)
				for a in doc.get("applies_to") or []):
			raise RulesUnavailable("The evaluation rules do not cover this template release.")
	doc["_digest"] = hashlib.sha256(raw).hexdigest()
	# an entry with a `releases` list belongs to those template releases only: one field key may be read differently by two releases
	doc["_index"] = {(r["mapping_id"], r["field_key"]): r for r in doc.get("rules") or [] if not r.get("releases") or template_release in r["releases"]}
	return doc


def rule_for(rules: dict[str, Any], mapping_id: str, field_key: str) -> dict[str, Any] | None:
	return rules["_index"].get((mapping_id, field_key))


# -- value helpers ------------------------------------------------------------
def _decimal(value) -> Decimal | None:
	try:
		if value is None or cstr(value).strip() == "":
			return None
		return Decimal(cstr(value).strip())
	except (InvalidOperation, ValueError):
		return None


def _date(value) -> date | None:
	try:
		return date.fromisoformat(cstr(value).strip()[:10]) if value else None
	except ValueError:
		return None


def _blank(value) -> bool:
	return value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, (list, dict)) and not value)


def display(value, unit: str = "") -> str:
	if value is None or value == "":
		return "Not provided"
	if isinstance(value, bool):
		return "Yes" if value else "No"
	if isinstance(value, list):
		if value and isinstance(value[0], dict) and "port_type" in value[0]:
			return ", ".join(f"{p.get('port_type')} ×{p.get('count')}" for p in value)
		return ", ".join(cstr(v) for v in value)
	text = cstr(value)
	return f"{text} {unit}".strip() if unit else text


def _required_display(facts: dict[str, Any]) -> str:
	text = cstr(facts.get("required_value_display"))
	unit = cstr(facts.get("unit"))
	if text and unit and not text.endswith(unit):
		comparison = cstr(facts.get("comparison"))
		prefix = {"Minimum": "Minimum ", "Maximum": "Maximum "}.get(comparison, "")
		return f"{prefix}{text} {unit}"
	return text


def outcome(result: str, reason: str, **extra) -> dict[str, Any]:
	return {"result": result, "reason": reason, **extra}


# -- the kinds ----------------------------------------------------------------
def published_kind(rules: dict[str, Any], facts: dict[str, Any]) -> str | None:
	return (rules.get("published_comparison") or {}).get(cstr(facts.get("comparison")), {}).get(cstr(facts.get("control")))


def check(rules: dict[str, Any], rule: dict[str, Any] | None, *, facts: dict[str, Any], value: Any, group_values: dict[str, Any], evidence_files: int,
		label: str = "", field_label: str = "") -> dict[str, Any]:
	"""One response's automatic result: {kind, result, reason, basis,
	required_display, offered_display, evidence_assessment, inputs}."""
	if rule is None:
		return {"kind": "unavailable", "basis": "Rule unavailable", "required_display": _required_display(facts), "offered_display": display(value),
			**outcome(REVIEW, UNAVAILABLE)}
	kind = rule["kind"]
	if kind == "published-comparison":
		kind = published_kind(rules, facts) or "unavailable"
	when = rule.get("when")
	if when:
		keys = when.get("field_keys") or [when["field_key"]]  # one field, or any of several
		if not any(group_values.get(k) == when["equals"] for k in keys):
			named = " or ".join(k.replace("_", " ") for k in keys)
			return {"kind": kind, "basis": "Comparison", "required_display": "", "offered_display": display(value),
				**outcome(NOT_APPLICABLE, f"Applies only when {named} is {when['equals']}.")}
	unit = cstr(facts.get("unit"))
	base = {"kind": kind, "basis": "Comparison", "required_display": _required_display(facts), "offered_display": display(value, unit),
		"inputs": {"value": value, "facts": {k: facts.get(k) for k in ("comparison", "control", "required_value", "unit") if k in facts}}}
	name = label or "The response"
	if kind == "unavailable":
		return {**base, "basis": "Rule unavailable", **outcome(REVIEW, UNAVAILABLE)}
	if kind == "confirmed":
		base["required_display"] = "Confirmed"
		ok = value is True
		res = outcome(MEETS, "The declaration is confirmed.") if ok else outcome(FAILS, "The declaration is not confirmed.")
		if ok and rule.get("evidence_assessment"):
			res["evidence_assessment"] = rule["evidence_assessment"]
		return {**base, **res}
	if kind == "presence":
		base.update(basis="Presence", required_display="Provided")
		return {**base, **(outcome(MEETS, "Provided.") if not _blank(value) else outcome(FAILS, "Not provided."))}
	if kind == "evidence":
		base.update(basis="Presence", required_display="Supporting evidence", offered_display=f"{evidence_files} file{'s' if evidence_files != 1 else ''}")
		if evidence_files < 1:
			return {**base, **outcome(FAILS, "No supporting file was submitted.")}
		return {**base, **outcome(MEETS, "Supporting evidence was submitted; its content is reviewed separately."), "evidence_assessment": rule.get("evidence_assessment") or ""}
	if kind == "manual":
		required = cstr((facts.get("required_value") or {}).get("value")) or cstr(facts.get("required_value_display"))
		return {**base, **outcome(REVIEW, f"{name} is free text and needs a member finding against “{required}”.")}
	if kind in ("review-if-yes", "review-unless"):
		accepted = "No" if kind == "review-if-yes" else rule.get("accepted_value")
		base["required_display"] = cstr(accepted)
		if _blank(value):
			return {**base, **outcome(REVIEW, "No answer was submitted.")}
		if value == accepted:
			return {**base, **outcome(MEETS, "No matter to assess was disclosed.")}
		reason = cstr(rule.get("review_reason")) or "A disclosed matter needs committee assessment."
		return {**base, **outcome(REVIEW, reason.replace("{field_label}", cstr(field_label)))}
	if kind == "equals":
		want = rule.get("value") if "value" in rule else (facts.get("required_value") or {}).get("value")
		base["required_display"] = base["required_display"] or cstr(want)
		if _blank(value):
			return {**base, **outcome(FAILS, "Not provided.")}
		if cstr(value) == cstr(want):
			return {**base, **outcome(MEETS, f"{name} meets the requirement.")}
		# the unit belongs to a published value (16 GB); a declared answer (Comply) has none
		with_unit = "" if "value" in rule else unit
		return {**base, **outcome(FAILS, f"{display(value, with_unit)} does not meet the required {display(want, with_unit)}.")}
	if kind == "choice-in":
		allowed = facts.get(rule["fact"]) or []
		base["required_display"] = ", ".join(cstr(a) for a in allowed)
		if value in allowed:
			return {**base, **outcome(MEETS, f"{display(value)} is permitted.")}
		return {**base, **outcome(FAILS if not _blank(value) else FAILS, f"{display(value)} is not a permitted choice.")}
	if kind in ("minimum", "maximum"):
		have, want = _decimal(value), _decimal((facts.get("required_value") or {}).get("value"))
		if want is None:
			return {**base, "basis": "Rule unavailable", **outcome(REVIEW, UNAVAILABLE)}
		if have is None:
			return {**base, **outcome(REVIEW, "The offered value could not be read as a number.")}
		ok = have >= want if kind == "minimum" else have <= want
		word = "minimum" if kind == "minimum" else "maximum"
		lowered = cstr(label).strip().lower() or "the offered value"
		if ok:
			return {**base, **outcome(MEETS, f"Offered {lowered} meets the {word}.")}
		return {**base, **outcome(FAILS, f"{display(value, unit)} is {'below' if kind == 'minimum' else 'above'} the required {display(want, unit)}.")}
	if kind in ("date-not-before", "date-not-after"):
		have, want = _date(value), _date(facts.get(rule["fact"]))
		base["required_display"] = f"{'On or after' if kind == 'date-not-before' else 'On or before'} {cstr(facts.get(rule['fact']))}"
		if want is None:
			return {**base, "basis": "Rule unavailable", **outcome(REVIEW, UNAVAILABLE)}
		if have is None:
			return {**base, **outcome(FAILS if _blank(value) else REVIEW, "Not provided." if _blank(value) else "The date could not be read.")}
		ok = have >= want if kind == "date-not-before" else have <= want
		return {**base, **(outcome(MEETS, "The date meets the published condition.") if ok else outcome(FAILS, f"{have.isoformat()} does not meet the published date {want.isoformat()}."))}
	if kind == "date-in-window":
		have, start, end = _date(value), _date(facts.get(rule["fact_start"])), _date(facts.get(rule["fact_end"]))
		base["required_display"] = f"Between {cstr(facts.get(rule['fact_start']))} and {cstr(facts.get(rule['fact_end']))}"
		if start is None or end is None:
			return {**base, "basis": "Rule unavailable", **outcome(REVIEW, UNAVAILABLE)}
		if have is None:
			return {**base, **outcome(FAILS, "Not provided.")}
		return {**base, **(outcome(MEETS, "Completed within the published period.") if start <= have <= end else outcome(FAILS, "Not completed within the published period."))}
	if kind == "money-equals":
		have, want = _decimal(value), _decimal(facts.get(rule["fact"]))
		currency = cstr(facts.get(rule.get("currency_fact") or "currency"))
		base["required_display"] = f"{currency} {want:,.2f}" if want is not None else ""
		if want is None:
			return {**base, "basis": "Rule unavailable", **outcome(REVIEW, UNAVAILABLE)}
		if have is None:
			return {**base, **outcome(FAILS, "Not provided.")}
		return {**base, **(outcome(MEETS, "The amount equals the published amount.") if have == want else outcome(FAILS, f"{currency} {have:,.2f} does not equal the published {currency} {want:,.2f}."))}
	if kind == "includes-all":
		need = list((facts.get("required_value") or {}).get("values") or [])
		missing = [n for n in need if n not in (value or [])]
		return {**base, **(outcome(MEETS, "Every required option is offered.") if not missing else outcome(FAILS, f"Not offered: {', '.join(missing)}."))}
	if kind == "ports-minimum":
		need = list((facts.get("required_value") or {}).get("ports") or [])
		have = {cstr(p.get("port_type")): int(p.get("count") or 0) for p in (value or []) if isinstance(p, dict)}
		short = [f"{p['port_type']} ×{p['minimum_count']}" for p in need if have.get(p["port_type"], 0) < int(p["minimum_count"])]
		base["required_display"] = ", ".join(f"{p['port_type']} ×{p['minimum_count']}" for p in need)
		return {**base, **(outcome(MEETS, "The published port minimums are satisfied.") if not short else outcome(FAILS, f"Below the minimum: {', '.join(short)}."))}
	return {**base, "basis": "Rule unavailable", **outcome(REVIEW, UNAVAILABLE)}


def calculate_price(price_rows: list[dict[str, Any]], package_price: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
	"""The published calculations (CALC-LINE-TOTAL, CALC-TENDER-TOTAL) in exact
	decimals, compared with the submitted amounts. Nothing is written back and
	nothing is corrected: a difference is Needs review (§4.4)."""
	lines, problems = [], []
	total = Decimal("0")
	submitted_lines = {cstr(l.get("line")): l for l in package_price.get("lines") or []}
	for row in price_rows:
		calc = row.get("calculation") or {}
		if calc.get("calculation_id") != "CALC-LINE-TOTAL":
			continue
		inputs = calc.get("inputs") or {}
		quantity = _decimal(inputs.get("quantity"))
		unit_price = _decimal(values.get(inputs.get("unit_price")))
		tax = _decimal(values.get(inputs.get("tax_amount"))) or Decimal("0")
		if quantity is None or unit_price is None:
			problems.append(f"Line {row.get('line')}: a price input is missing.")
			continue
		before = (quantity * unit_price).quantize(Decimal("0.01"))
		line_total = (before + tax).quantize(Decimal("0.01"))
		total += line_total
		submitted = submitted_lines.get(cstr(row.get("line"))) or {}
		if _decimal(submitted.get("line_total")) != line_total:
			problems.append(f"Line {row.get('line')}: the submitted line total {submitted.get('line_total')} differs from the calculated {line_total:.2f}.")
		lines.append({"line": row.get("line"), "description": row.get("description"), "quantity": cstr(quantity), "unit": row.get("unit"),
			"unit_price": f"{unit_price:.2f}", "amount_before_tax": f"{before:.2f}", "tax_amount": f"{tax:.2f}", "line_total": f"{line_total:.2f}"})
	submitted_total = _decimal(package_price.get("total"))
	if submitted_total is None:
		problems.append("The submitted total is missing.")
	elif submitted_total != total:
		problems.append(f"The submitted total {submitted_total:.2f} differs from the calculated {total:.2f}.")
	return {"lines": lines, "calculated_total": f"{total:.2f}", "submitted_total": cstr(package_price.get("total")), "currency": cstr(package_price.get("currency")),
		"problems": problems, "result": REVIEW if problems else MEETS,
		"reason": " ".join(problems) if problems else "The submitted prices agree with the published calculation."}
