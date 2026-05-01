# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 11 — template engine service.

Deterministic, side-effect-light interpreter that bridges the imported STD
package (``STD Template.package_json``) and a tender configuration into
validation messages, required-form rows, active sections, configuration
hash, and a Jinja-ready render context.

Implements every public function required by Step 11 spec §10.1–§10.16 and
§16.1–§16.2 (18 callables in total). Operators (§10.8) and rule types
(§10.10) are limited to the declarative vocabulary defined in
``rules.json``; unknown operators / rule types / validation types / child
tables raise clear errors (§17). The engine never executes JSON content
(§19) and never carries a ``frappe.whitelist`` decorator.

Transaction discipline (§18): pure helpers and resolution functions never
write to the database; the persistence helpers (``apply_config_to_tender_doc``,
``populate_sample_tender``, ``write_validation_to_tender``,
``write_required_forms_to_tender``) mutate the in-memory ``Procurement
Tender`` document but do not call ``save()`` or ``commit()``.

See **STD-POC-012** for the slice ``services/`` placement decision (spec §4
path ``<app>/procurement/std_template_engine.py`` adapted via the same
mechanism applied to the seed loader in **STD-POC-011**, alongside
``std_template_loader.py``).
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

import frappe
from frappe.utils import get_datetime, now_datetime

VALID_TEMPLATE_COMPONENTS: frozenset[str] = frozenset(
	{
		"manifest",
		"sections",
		"fields",
		"rules",
		"forms",
		"render_map",
		"sample_tender",
	}
)

SUPPORTED_OPERATORS: frozenset[str] = frozenset(
	{
		"EQUALS",
		"NOT_EQUALS",
		"IS_TRUE",
		"IS_FALSE",
		"IS_EMPTY",
		"IS_NOT_EMPTY",
		"GREATER_THAN",
		"GREATER_THAN_OR_EQUALS",
		"LESS_THAN",
		"LESS_THAN_OR_EQUALS",
		"IN",
		"NOT_IN",
	}
)

SUPPORTED_RULE_TYPES: frozenset[str] = frozenset(
	{
		"REQUIRE_FIELD",
		"REQUIRE_CHILD_ROWS",
		"ACTIVATE_FIELD",
		"ACTIVATE_SECTION",
		"ACTIVATE_FORM",
		"DERIVE_FIELD",
		"VALIDATE_DATE_ORDER",
		"VALIDATE_NUMERIC_LIMIT",
		"VALIDATE_ALLOWED_COMBINATION",
		"WARNING_ONLY",
		"INFO_ONLY",
	}
)

SUPPORTED_DATE_ORDER_TYPES: frozenset[str] = frozenset(
	{"FIELD_BEFORE_FIELD", "FIELD_ON_OR_AFTER_FIELD"}
)
SUPPORTED_NUMERIC_LIMIT_TYPES: frozenset[str] = frozenset({"MAX_PERCENT_OF_FIELD"})
SUPPORTED_CHILD_TABLES: frozenset[str] = frozenset({"Tender Lot", "Tender BoQ Item"})

# Step 9 Tender BoQ Item Select options + OTHER (Step 15 POC validation surface).
ALLOWED_BOQ_ITEM_CATEGORIES: frozenset[str] = frozenset(
	{
		"PRELIMINARIES",
		"SUBSTRUCTURE",
		"SUPERSTRUCTURE",
		"ROOFING",
		"FINISHES",
		"EXTERNAL_WORKS",
		"DAYWORKS",
		"PROVISIONAL_SUMS",
		"GRAND_SUMMARY",
		"OTHER",
	}
)

STD_WORKS_POC_SAMPLE_BOQ_NOTE = "Generated from STD-WORKS-POC sample_tender.json"

BLOCKING_SEVERITIES: frozenset[str] = frozenset({"ERROR", "BLOCKER"})
SEVERITY_RANK: dict[str, int] = {"INFO": 0, "WARNING": 1, "ERROR": 2, "BLOCKER": 3}
SEVERITY_TO_STATUS: dict[str | None, str] = {
	None: "Passed",
	"INFO": "Passed",
	"WARNING": "Passed With Warnings",
	"ERROR": "Failed",
	"BLOCKER": "Blocked",
}

_RULE_TYPES_PRODUCING_PASSING_MESSAGE: frozenset[str] = frozenset(
	{"WARNING_ONLY", "INFO_ONLY"}
)


# ---------------------------------------------------------------------------
# §10.1 / §10.2 — template loading
# ---------------------------------------------------------------------------


def load_template(template_code_or_name: str) -> dict[str, Any]:
	"""Load an ``STD Template`` and its parsed package payload.

	Looks up by ``template_code`` first, then by Frappe document ``name``;
	raises :class:`frappe.DoesNotExistError` if neither resolves. Parses
	``package_json`` via :func:`json.loads`; raises :class:`ValueError` on
	empty or invalid payload.
	"""
	if not template_code_or_name:
		raise ValueError("template_code_or_name must be a non-empty string")

	doc = None
	if frappe.db.exists("STD Template", {"template_code": template_code_or_name}):
		doc_name = frappe.db.get_value(
			"STD Template", {"template_code": template_code_or_name}, "name"
		)
		doc = frappe.get_doc("STD Template", doc_name)
	elif frappe.db.exists("STD Template", template_code_or_name):
		doc = frappe.get_doc("STD Template", template_code_or_name)

	if doc is None:
		raise frappe.DoesNotExistError(
			f"STD Template not found by template_code or name: {template_code_or_name!r}"
		)

	raw_payload = doc.package_json
	if not raw_payload:
		raise ValueError(
			f"STD Template {doc.name!r} has empty package_json; re-run the seed loader."
		)
	try:
		package = json.loads(raw_payload)
	except json.JSONDecodeError as exc:
		raise ValueError(
			f"STD Template {doc.name!r} has invalid package_json: {exc}"
		) from exc

	template_code = doc.template_code
	package_hash = doc.package_hash
	return {
		"doc": doc,
		"package": package,
		"template_code": template_code,
		"package_hash": package_hash,
	}


def get_package_component(template: dict[str, Any], component_name: str) -> dict[str, Any]:
	"""Return ``template['package'][component_name]`` with strict validation."""
	if component_name not in VALID_TEMPLATE_COMPONENTS:
		raise ValueError(
			f"Unknown package component: {component_name!r}. "
			f"Expected one of {sorted(VALID_TEMPLATE_COMPONENTS)}"
		)
	package = template.get("package") if isinstance(template, dict) else None
	if not isinstance(package, dict):
		raise ValueError("Template dict is missing parsed 'package' payload")
	component = package.get(component_name)
	if component is None:
		raise ValueError(f"Package component {component_name!r} is missing from payload")
	return component


# ---------------------------------------------------------------------------
# §10.3..§10.6 — configuration initialization and sample loading
# ---------------------------------------------------------------------------


def initialize_config(template: dict[str, Any]) -> dict[str, Any]:
	"""Build a ``field_code -> default_value`` configuration dictionary.

	Reads ``fields.fields[*]`` from the package, then injects the four
	``SYSTEM.*`` audit fields from package metadata so downstream rules
	(e.g. ``RULE_REQUIRE_AUDIT_FIELDS``) can reference them directly.
	Pure: never writes to the database.
	"""
	fields_component = get_package_component(template, "fields")
	manifest = get_package_component(template, "manifest")
	field_definitions = fields_component.get("fields") or []

	config: dict[str, Any] = {}
	for field in field_definitions:
		if not isinstance(field, dict):
			continue
		field_code = field.get("field_code")
		if not field_code:
			continue
		config[field_code] = copy.deepcopy(field.get("default_value"))

	versioning = manifest.get("versioning") or {}
	config["SYSTEM.TEMPLATE_CODE"] = template.get("template_code") or manifest.get(
		"template_code"
	)
	config["SYSTEM.PACKAGE_VERSION"] = versioning.get("package_version")
	config["SYSTEM.PACKAGE_HASH"] = template.get("package_hash")
	config["SYSTEM.CONFIGURATION_HASH"] = None
	return config


def _get_variant(template: dict[str, Any], variant_code: str | None) -> dict[str, Any] | None:
	if not variant_code:
		return None
	sample = get_package_component(template, "sample_tender")
	for variant in sample.get("scenario_variants") or []:
		if isinstance(variant, dict) and variant.get("variant_code") == variant_code:
			return variant
	raise ValueError(
		f"Unknown variant_code: {variant_code!r}. "
		f"Expected one of "
		f"{sorted(v.get('variant_code') for v in sample.get('scenario_variants') or [] if isinstance(v, dict))}"
	)


def load_sample_config(
	template: dict[str, Any], variant_code: str | None = None
) -> dict[str, Any]:
	"""Return a deep copy of ``sample_tender.configuration`` with optional variant overrides."""
	sample = get_package_component(template, "sample_tender")
	config = copy.deepcopy(sample.get("configuration") or {})
	variant = _get_variant(template, variant_code)
	if variant:
		overrides = variant.get("configuration_overrides") or {}
		for field_code, value in overrides.items():
			config[field_code] = copy.deepcopy(value)
	return config


def load_sample_lots(
	template: dict[str, Any], variant_code: str | None = None
) -> list[dict[str, Any]]:
	"""Return the sample lot rows (variant ``lot_overrides`` if non-empty, else primary)."""
	sample = get_package_component(template, "sample_tender")
	primary = sample.get("lots") or []
	variant = _get_variant(template, variant_code)
	if variant:
		variant_lots = variant.get("lot_overrides")
		if variant_lots:
			return copy.deepcopy(variant_lots)
	return copy.deepcopy(primary)


def get_allowed_boq_categories() -> frozenset[str]:
	"""Return allowed ``Tender BoQ Item.item_category`` values for STD-WORKS-POC."""
	return ALLOWED_BOQ_ITEM_CATEGORIES


def load_sample_boq_rows(
	template: dict[str, Any], variant_code: str | None = None
) -> list[dict[str, Any]]:
	"""Return sample BoQ rows from ``sample_tender.json`` (deep copy; no DB writes).

	Uses variant ``boq_overrides.rows`` when that list is non-empty; otherwise the
	primary ``boq.rows``. Raises :class:`ValueError` when ``boq`` / ``rows`` are
	missing or not a non-empty list (Step 15 §10).
	"""
	sample = get_package_component(template, "sample_tender")
	boq = sample.get("boq")
	if boq is None:
		raise ValueError("sample_tender.boq is missing")
	if not isinstance(boq, dict):
		raise ValueError(
			f"sample_tender.boq must be an object, got {type(boq).__name__}"
		)

	variant = _get_variant(template, variant_code)
	if variant:
		variant_overrides = variant.get("boq_overrides") or {}
		variant_rows = (
			variant_overrides.get("rows") if isinstance(variant_overrides, dict) else None
		)
		if variant_rows is not None:
			if not isinstance(variant_rows, list):
				raise ValueError(
					f"scenario variant boq_overrides.rows must be a list, got {type(variant_rows).__name__}"
				)
			if len(variant_rows) == 0:
				raise ValueError("scenario variant boq_overrides.rows is empty")
			return copy.deepcopy(variant_rows)

	primary_rows = boq.get("rows")
	if primary_rows is None:
		raise ValueError("sample_tender.boq.rows is missing")
	if not isinstance(primary_rows, list):
		raise ValueError(
			f"sample_tender.boq.rows must be a list, got {type(primary_rows).__name__}"
		)
	if len(primary_rows) == 0:
		raise ValueError("sample_tender.boq.rows is empty")
	return copy.deepcopy(primary_rows)


def summarize_boq_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
	"""Return ``boq_row_count`` and sorted distinct ``categories`` (Step 15 §11)."""
	categories = sorted(
		{str(r.get("item_category")) for r in rows if r.get("item_category")}
	)
	return {"boq_row_count": len(rows), "categories": categories}


def _coerce_boq_check(value: Any) -> int:
	if value in (True, 1, "1"):
		return 1
	return 0


def validate_sample_boq_rows(
	rows: list[Any],
	allowed_categories: frozenset[str],
	*,
	existing_lot_codes: set[str] | frozenset[str] | None = None,
	strict_lot_references: bool = True,
) -> None:
	"""Validate package BoQ dicts before persisting to ``Tender BoQ Item`` (Step 15 §18–§19).

	When ``strict_lot_references`` is True and ``existing_lot_codes`` is non-empty,
	non-``GRAND_SUMMARY`` rows must carry a ``lot_code`` present in that set.
	``GRAND_SUMMARY`` may omit ``lot_code``. When lots are unknown / absent, pass
	``strict_lot_references=False`` (e.g. ``populate_sample_tender`` for variant
	scenarios where primary BoQ still references lots trimmed by a variant).
	"""
	if not isinstance(rows, list):
		raise ValueError(f"BoQ rows must be a list, got {type(rows).__name__}")

	seen_codes: set[str] = set()
	lot_set: set[str] = set(existing_lot_codes) if existing_lot_codes else set()
	check_lots = bool(strict_lot_references and lot_set)

	for i, raw in enumerate(rows):
		if not isinstance(raw, dict):
			raise ValueError(f"boq.rows[{i}] must be an object, got {type(raw).__name__}")

		for key in (
			"item_code",
			"item_category",
			"description",
			"unit",
			"quantity",
			"is_priced_by_bidder",
		):
			if key not in raw:
				raise ValueError(f"boq.rows[{i}] missing required field {key!r}")

		item_code = raw.get("item_code")
		if item_code in (None, ""):
			raise ValueError(f"boq.rows[{i}] item_code must be non-empty")

		if item_code in seen_codes:
			raise ValueError(
				f"Duplicate item_code {item_code!r} in sample BoQ rows "
				f"(first duplicate at index {i})."
			)
		seen_codes.add(str(item_code))

		category = raw.get("item_category")
		if category not in allowed_categories:
			raise ValueError(
				f"boq.rows[{i}] has unknown item_category {category!r}. "
				f"Expected one of {sorted(allowed_categories)}"
			)

		qty = raw.get("quantity")
		try:
			float(qty)
		except (TypeError, ValueError) as exc:
			raise ValueError(
				f"boq.rows[{i}] quantity must be numeric, got {qty!r}"
			) from exc

		lc = raw.get("lot_code")
		lc_norm = None if lc in (None, "") else str(lc)

		if category == "GRAND_SUMMARY":
			pass
		elif check_lots:
			if lc_norm is None:
				raise ValueError(
					f"boq.rows[{i}] ({item_code!r}) requires lot_code because the tender "
					f"has lots defined; GRAND_SUMMARY may omit lot_code."
				)
			if lc_norm not in lot_set:
				raise ValueError(
					f"boq.rows[{i}] lot_code {lc_norm!r} does not match any Tender Lot "
					f"on this tender (expected one of {sorted(lot_set)})."
				)


def build_boq_child_rows(
	rows: list[dict[str, Any]],
	*,
	notes_text: str | None = None,
) -> list[dict[str, Any]]:
	"""Map package BoQ dicts to ``Tender BoQ Item`` child payloads including notes."""
	note = notes_text if notes_text is not None else STD_WORKS_POC_SAMPLE_BOQ_NOTE
	out: list[dict[str, Any]] = []
	for raw in rows:
		child: dict[str, Any] = {
			"item_code": raw.get("item_code"),
			"item_category": raw.get("item_category"),
			"description": raw.get("description"),
			"unit": raw.get("unit"),
			"quantity": float(raw.get("quantity")),
			"is_priced_by_bidder": _coerce_boq_check(raw.get("is_priced_by_bidder")),
			"notes": note,
		}
		lc = raw.get("lot_code")
		if lc not in (None, ""):
			child["lot_code"] = lc
		if raw.get("rate") is not None:
			child["rate"] = raw.get("rate")
		if raw.get("amount") is not None:
			child["amount"] = raw.get("amount")
		out.append(child)
	return out


# ---------------------------------------------------------------------------
# §10.7 / §13 — configuration hash
# ---------------------------------------------------------------------------


def hash_config(config: dict[str, Any]) -> str:
	"""Deterministic SHA-256 hex digest over the full configuration dictionary."""
	payload = json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)
	return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# §10.8 / §10.9 — condition evaluation
# ---------------------------------------------------------------------------


def _is_empty(value: Any) -> bool:
	"""Return True for ``None``/``""``/``[]``/``{}``; False for ``False`` and ``0`` (§12.1)."""
	if value is None:
		return True
	if isinstance(value, str) and value == "":
		return True
	if isinstance(value, (list, dict, tuple, set)) and len(value) == 0:
		return True
	return False


def _get_field_value(config: dict[str, Any], field_code: str) -> Any:
	return config.get(field_code) if isinstance(config, dict) else None


def evaluate_condition(condition: dict[str, Any], config: dict[str, Any]) -> bool:
	"""Evaluate one ``rules.json`` condition against a config dictionary.

	Supports the 12 §10.8 operators. Raises :class:`ValueError` for any
	other operator. Empty-value semantics are §12.1: ``None``/``""``/``[]``
	/``{}`` only; ``False`` and ``0`` are not empty.
	"""
	if not isinstance(condition, dict):
		raise ValueError(f"Condition must be a dict, got {type(condition).__name__}")
	operator = condition.get("operator")
	if operator not in SUPPORTED_OPERATORS:
		raise ValueError(
			f"Unsupported operator: {operator!r}. Expected one of {sorted(SUPPORTED_OPERATORS)}"
		)
	field_code = condition.get("field")
	value = _get_field_value(config, field_code) if field_code else None
	expected = condition.get("value")

	if operator == "EQUALS":
		return value == expected
	if operator == "NOT_EQUALS":
		return value != expected
	if operator == "IS_TRUE":
		return value is True
	if operator == "IS_FALSE":
		return value is False
	if operator == "IS_EMPTY":
		return _is_empty(value)
	if operator == "IS_NOT_EMPTY":
		return not _is_empty(value)
	if operator == "GREATER_THAN":
		return value is not None and expected is not None and value > expected
	if operator == "GREATER_THAN_OR_EQUALS":
		return value is not None and expected is not None and value >= expected
	if operator == "LESS_THAN":
		return value is not None and expected is not None and value < expected
	if operator == "LESS_THAN_OR_EQUALS":
		return value is not None and expected is not None and value <= expected
	if operator == "IN":
		return isinstance(expected, (list, tuple, set)) and value in expected
	if operator == "NOT_IN":
		return isinstance(expected, (list, tuple, set)) and value not in expected
	raise ValueError(f"Unsupported operator: {operator!r}")  # defensive — unreachable


def rule_applies(rule: dict[str, Any], config: dict[str, Any]) -> bool:
	"""Return True when a rule should fire against the given config."""
	if rule.get("enabled") is False:
		return False
	conditions = ((rule.get("when") or {}).get("all")) or []
	if not conditions:
		return True
	return all(evaluate_condition(c, config) for c in conditions)


# ---------------------------------------------------------------------------
# Internal helpers for validate_config
# ---------------------------------------------------------------------------


def _make_message(
	severity: str,
	rule_code: str,
	message: str,
	*,
	affected_field: str | None = None,
	affected_section: str | None = None,
	affected_form: str | None = None,
	resolution_hint: str | None = None,
	details: dict[str, Any] | None = None,
) -> dict[str, Any]:
	return {
		"severity": severity,
		"rule_code": rule_code,
		"message": message,
		"affected_field": affected_field,
		"affected_section": affected_section,
		"affected_form": affected_form,
		"blocks_generation": severity in BLOCKING_SEVERITIES,
		"resolution_hint": resolution_hint or "",
		"details": details or {},
	}


def _child_rows_to_dicts(rows: list[Any] | None) -> list[dict[str, Any]]:
	if not rows:
		return []
	out: list[dict[str, Any]] = []
	for row in rows:
		if isinstance(row, dict):
			out.append(row)
			continue
		as_dict = getattr(row, "as_dict", None)
		if callable(as_dict):
			out.append(as_dict())
			continue
		try:
			out.append(dict(row))
		except Exception:  # pragma: no cover — defensive
			out.append({})
	return out


def _row_matches_filter(row: dict[str, Any], row_filter: dict[str, Any]) -> bool:
	field = row_filter.get("field")
	operator = row_filter.get("operator")
	if operator not in SUPPORTED_OPERATORS:
		raise ValueError(
			f"Unsupported child-row filter operator: {operator!r}. "
			f"Expected one of {sorted(SUPPORTED_OPERATORS)}"
		)
	expected = row_filter.get("value")
	value = row.get(field) if field else None
	pseudo_condition = {"field": "_value", "operator": operator, "value": expected}
	return evaluate_condition(pseudo_condition, {"_value": value})


def _count_matching_child_rows(
	rows: list[dict[str, Any]], row_filter: dict[str, Any] | None
) -> int:
	if not row_filter:
		return len(rows)
	return sum(1 for row in rows if _row_matches_filter(row, row_filter))


def _coerce_datetime(value: Any) -> Any:
	if value is None or value == "":
		return None
	try:
		return get_datetime(value)
	except Exception:
		return None


def _coerce_number(value: Any) -> float | None:
	if value is None or value == "":
		return None
	try:
		return float(value)
	except (TypeError, ValueError):
		return None


def _highest_severity(severities: list[str]) -> str | None:
	highest: str | None = None
	highest_rank = -1
	for sev in severities:
		rank = SEVERITY_RANK.get(sev)
		if rank is None:
			continue
		if rank > highest_rank:
			highest = sev
			highest_rank = rank
	return highest


# ---------------------------------------------------------------------------
# §10.10 — validate_config
# ---------------------------------------------------------------------------


def validate_config(
	template: dict[str, Any],
	config: dict[str, Any],
	lots: list[Any] | None = None,
	boq_items: list[Any] | None = None,
) -> dict[str, Any]:
	"""Evaluate enabled rules and return the §10.10 9-key validation result."""
	rules_component = get_package_component(template, "rules")
	rules = rules_component.get("rules") or []

	messages: list[dict[str, Any]] = []
	active_fields: set[str] = set()
	active_sections: set[str] = set()
	active_forms: dict[str, str] = {}
	required_fields: set[str] = set()

	lot_dicts = _child_rows_to_dicts(lots)
	boq_dicts = _child_rows_to_dicts(boq_items)
	child_rows_by_table = {"Tender Lot": lot_dicts, "Tender BoQ Item": boq_dicts}

	for rule in rules:
		if not isinstance(rule, dict):
			continue
		rule_type = rule.get("rule_type")
		if rule_type not in SUPPORTED_RULE_TYPES:
			raise ValueError(
				f"Unsupported rule_type: {rule_type!r} on rule "
				f"{rule.get('rule_code')!r}. Expected one of {sorted(SUPPORTED_RULE_TYPES)}"
			)
		if not rule_applies(rule, config):
			continue

		rule_code = rule.get("rule_code") or "RULE_UNKNOWN"
		severity = rule.get("severity") or "INFO"
		then = rule.get("then") or {}

		for field_code in then.get("activate_fields") or []:
			active_fields.add(field_code)
		for section_code in then.get("activate_sections") or []:
			active_sections.add(section_code)
		for form_code in then.get("activate_forms") or []:
			active_forms.setdefault(form_code, f"RULE:{rule_code}")
		for field_code in then.get("require_fields") or []:
			required_fields.add(field_code)

		if rule_type == "REQUIRE_FIELD":
			for field_code in then.get("require_fields") or []:
				if _is_empty(_get_field_value(config, field_code)):
					messages.append(
						_make_message(
							severity,
							rule_code,
							rule.get("message")
							or f"Field {field_code} is required.",
							affected_field=field_code,
							affected_section=(rule.get("affected_sections") or [None])[0],
							resolution_hint=f"Provide a value for {field_code}.",
							details={"missing_field": field_code},
						)
					)

		elif rule_type == "REQUIRE_CHILD_ROWS":
			for spec in then.get("require_child_rows") or []:
				child_table = spec.get("child_table")
				if child_table not in SUPPORTED_CHILD_TABLES:
					raise ValueError(
						f"Unsupported child_table in rule {rule_code!r}: "
						f"{child_table!r}. Expected one of {sorted(SUPPORTED_CHILD_TABLES)}"
					)
				rows_for_table = child_rows_by_table.get(child_table) or []
				row_filter = spec.get("row_filter")
				matched = _count_matching_child_rows(rows_for_table, row_filter)
				minimum = int(spec.get("minimum_rows") or 1)
				if matched < minimum:
					messages.append(
						_make_message(
							severity,
							rule_code,
							spec.get("condition_label")
							or rule.get("message")
							or f"At least {minimum} {child_table} row(s) required.",
							affected_section=(rule.get("affected_sections") or [None])[0],
							resolution_hint=f"Add at least {minimum} matching row(s) to {child_table}.",
							details={
								"child_table": child_table,
								"minimum_rows": minimum,
								"matched_rows": matched,
								"row_filter": row_filter,
							},
						)
					)

		elif rule_type == "VALIDATE_DATE_ORDER":
			for spec in then.get("validate") or []:
				validation_type = spec.get("validation_type")
				if validation_type not in SUPPORTED_DATE_ORDER_TYPES:
					raise ValueError(
						f"Unsupported date-order validation_type {validation_type!r} "
						f"on rule {rule_code!r}. "
						f"Expected one of {sorted(SUPPORTED_DATE_ORDER_TYPES)}"
					)
				if validation_type == "FIELD_BEFORE_FIELD":
					earlier_code = spec.get("earlier_field")
					later_code = spec.get("later_field")
					earlier = _coerce_datetime(_get_field_value(config, earlier_code))
					later = _coerce_datetime(_get_field_value(config, later_code))
					if earlier is None or later is None:
						continue
					if not earlier < later:
						messages.append(
							_make_message(
								severity,
								rule_code,
								rule.get("message")
								or f"{earlier_code} must be before {later_code}.",
								affected_field=earlier_code,
								affected_section=(rule.get("affected_sections") or [None])[0],
								resolution_hint=f"Adjust {earlier_code} to be strictly before {later_code}.",
								details={
									"validation_type": validation_type,
									"earlier_field": earlier_code,
									"later_field": later_code,
								},
							)
						)
				else:  # FIELD_ON_OR_AFTER_FIELD
					first_code = spec.get("first_field")
					second_code = spec.get("second_field")
					first = _coerce_datetime(_get_field_value(config, first_code))
					second = _coerce_datetime(_get_field_value(config, second_code))
					if first is None or second is None:
						continue
					if not first >= second:
						messages.append(
							_make_message(
								severity,
								rule_code,
								rule.get("message")
								or f"{first_code} must be on or after {second_code}.",
								affected_field=first_code,
								affected_section=(rule.get("affected_sections") or [None])[0],
								resolution_hint=f"Adjust {first_code} to be on or after {second_code}.",
								details={
									"validation_type": validation_type,
									"first_field": first_code,
									"second_field": second_code,
								},
							)
						)

		elif rule_type == "VALIDATE_NUMERIC_LIMIT":
			for spec in then.get("validate") or []:
				validation_type = spec.get("validation_type")
				if validation_type not in SUPPORTED_NUMERIC_LIMIT_TYPES:
					raise ValueError(
						f"Unsupported numeric-limit validation_type {validation_type!r} "
						f"on rule {rule_code!r}. "
						f"Expected one of {sorted(SUPPORTED_NUMERIC_LIMIT_TYPES)}"
					)
				field_code = spec.get("field")
				base_field_code = spec.get("base_field")
				percent = _coerce_number(spec.get("percent"))
				field_value = _coerce_number(_get_field_value(config, field_code))
				base_value = _coerce_number(_get_field_value(config, base_field_code))
				if (
					field_value is None
					or base_value is None
					or percent is None
				):
					continue
				limit = base_value * percent / 100.0
				if field_value > limit:
					messages.append(
						_make_message(
							severity,
							rule_code,
							rule.get("message")
							or f"{field_code} must not exceed {percent}% of {base_field_code}.",
							affected_field=field_code,
							affected_section=(rule.get("affected_sections") or [None])[0],
							resolution_hint=f"Reduce {field_code} so it is at most {percent}% of {base_field_code}.",
							details={
								"validation_type": validation_type,
								"field": field_code,
								"base_field": base_field_code,
								"percent": percent,
								"limit": limit,
								"field_value": field_value,
							},
						)
					)

		elif rule_type in _RULE_TYPES_PRODUCING_PASSING_MESSAGE:
			messages.append(
				_make_message(
					severity,
					rule_code,
					rule.get("message") or rule.get("description") or rule_code,
					affected_section=(rule.get("affected_sections") or [None])[0],
				)
			)
		# Pure activation / derive / allowed-combination rules: no message,
		# activations already collected above.

	highest = _highest_severity([m["severity"] for m in messages])
	status = SEVERITY_TO_STATUS.get(highest, "Passed")
	blocks_generation = any(m["blocks_generation"] for m in messages)
	configuration_hash = hash_config(config)
	return {
		"ok": not blocks_generation,
		"status": status,
		"blocks_generation": blocks_generation,
		"messages": messages,
		"active_fields": sorted(active_fields),
		"active_sections": sorted(active_sections),
		"active_forms": dict(active_forms),
		"required_fields": sorted(required_fields),
		"configuration_hash": configuration_hash,
	}


def evaluate_condition_trace(condition: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
	"""Admin Step 4 — one condition row with explainability (§16)."""
	field_code = condition.get("field") if isinstance(condition, dict) else None
	operator = condition.get("operator") if isinstance(condition, dict) else None
	expected = condition.get("value") if isinstance(condition, dict) else None
	value = _get_field_value(config, field_code) if field_code else None
	try:
		passed = bool(evaluate_condition(condition, config))
	except ValueError as exc:
		return {
			"field_code": field_code,
			"operator": operator,
			"expected_value": expected,
			"actual_value": value,
			"passed": False,
			"message": str(exc),
		}
	msg = f"{field_code} {operator} {expected!r}: {'passed' if passed else 'failed'}"
	return {
		"field_code": field_code,
		"operator": operator,
		"expected_value": expected,
		"actual_value": value,
		"passed": passed,
		"message": msg,
	}


def _summarize_rule_then(then: dict[str, Any]) -> str:
	if not then:
		return "No declarative effects."
	parts: list[str] = []
	if then.get("require_fields"):
		parts.append(f"Requires fields: {', '.join(map(str, then['require_fields']))}")
	if then.get("activate_fields"):
		parts.append(f"Activates fields: {', '.join(map(str, then['activate_fields']))}")
	if then.get("activate_sections"):
		parts.append(f"Activates sections: {', '.join(map(str, then['activate_sections']))}")
	if then.get("activate_forms"):
		parts.append(f"Activates forms: {', '.join(map(str, then['activate_forms']))}")
	if then.get("require_child_rows"):
		parts.append(f"Require child rows: {len(then['require_child_rows'])} spec(s)")
	if then.get("validate"):
		parts.append(f"Validations: {len(then['validate'])} spec(s)")
	return "; ".join(parts)


def trace_rules(
	template: dict[str, Any],
	config: dict[str, Any],
	lots: list[Any] | None = None,
	boq_items: list[Any] | None = None,
) -> dict[str, Any]:
	"""Admin Step 4 — explainable per-rule trace; reuses :func:`validate_config` aggregate (§20)."""
	validation_result = validate_config(template, config, lots=lots, boq_items=boq_items)
	rules_component = get_package_component(template, "rules")
	rules = rules_component.get("rules") or []
	vmessages = validation_result.get("messages") or []

	rule_rows: list[dict[str, Any]] = []
	enabled_n = 0
	applied_n = 0
	for rule in rules:
		if not isinstance(rule, dict):
			continue
		rule_code = rule.get("rule_code") or "RULE_UNKNOWN"
		enabled = rule.get("enabled", True) is not False
		if enabled:
			enabled_n += 1
		applies = bool(enabled and rule_applies(rule, config))
		if applies:
			applied_n += 1
		when = rule.get("when") or {}
		cond_traces = [
			evaluate_condition_trace(c, config)
			for c in (when.get("all") or [])
			if isinstance(c, dict)
		]
		condition_summary = (
			"; ".join(str(c.get("message") or "") for c in cond_traces) if cond_traces else "(no conditions)"
		)
		then = rule.get("then") or {}
		effect_summary = _summarize_rule_then(then if isinstance(then, dict) else {})
		rule_msgs = [m for m in vmessages if isinstance(m, dict) and m.get("rule_code") == rule_code]
		affected_fields = sorted(
			{str(m.get("affected_field")) for m in rule_msgs if m.get("affected_field")}
		)
		affected_sections = sorted(
			{str(m.get("affected_section")) for m in rule_msgs if m.get("affected_section")}
		)
		affected_forms = sorted({str(m.get("affected_form")) for m in rule_msgs if m.get("affected_form")})
		blocks_generation = any(m.get("blocks_generation") for m in rule_msgs if isinstance(m, dict))
		rule_rows.append(
			{
				"rule_code": rule_code,
				"label": rule.get("label") or rule.get("description") or rule_code,
				"rule_type": rule.get("rule_type"),
				"enabled": enabled,
				"applies": applies,
				"severity": rule.get("severity") or "INFO",
				"conditions": cond_traces,
				"condition_summary": condition_summary,
				"effects": then if isinstance(then, dict) else {},
				"effect_summary": effect_summary,
				"messages": rule_msgs,
				"affected_fields": affected_fields,
				"affected_sections": affected_sections,
				"affected_forms": affected_forms,
				"blocks_generation": blocks_generation,
			}
		)

	blockers = sum(1 for m in vmessages if m.get("blocks_generation"))
	errors = sum(
		1 for m in vmessages if isinstance(m, dict) and m.get("severity") == "ERROR" and not m.get("blocks_generation")
	)
	warnings = sum(1 for m in vmessages if isinstance(m, dict) and m.get("severity") == "WARNING")

	return {
		"ok": bool(validation_result.get("ok")),
		"template_code": template.get("template_code"),
		"configuration_hash": validation_result.get("configuration_hash"),
		"summary": {
			"total_rules": len(rule_rows),
			"enabled_rules": enabled_n,
			"applied_rules": applied_n,
			"non_applied_rules": enabled_n - applied_n,
			"messages": len(vmessages),
			"blockers": blockers,
			"errors": errors,
			"warnings": warnings,
			"active_fields": len(validation_result.get("active_fields") or []),
			"active_sections": len(validation_result.get("active_sections") or []),
			"active_forms": len(validation_result.get("active_forms") or {}),
		},
		"rules": rule_rows,
		"validation_result": validation_result,
	}


# ---------------------------------------------------------------------------
# §10.11 / §10.12 — section / form resolution
# ---------------------------------------------------------------------------


def resolve_active_sections(
	template: dict[str, Any],
	config: dict[str, Any],
	validation_result: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
	"""Return ``included_in_poc_render`` sections plus any rule-activated sections, sorted by ``render_order``."""
	sections_component = get_package_component(template, "sections")
	all_sections = sections_component.get("sections") or []
	active_codes: set[str] = {
		s.get("section_code")
		for s in all_sections
		if isinstance(s, dict) and s.get("included_in_poc_render")
	}
	if validation_result:
		for code in validation_result.get("active_sections") or []:
			active_codes.add(code)
	chosen = [
		s
		for s in all_sections
		if isinstance(s, dict) and s.get("section_code") in active_codes
	]
	chosen.sort(key=lambda s: s.get("render_order") or 0)
	return chosen


def resolve_required_forms(
	template: dict[str, Any],
	config: dict[str, Any],
	validation_result: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
	"""Return required-form rows shaped for ``Tender Required Form`` child table population.

	Step 14 §8 — §10 hardening:

	* §8.1 default forms always included.
	* §8.2 rule-activated forms included via ``validation_result["active_forms"]``.
	* §8.4 a form activated by multiple sources is recorded once with sources joined
	  by ``"; "`` (e.g. ``"DEFAULT; RULE:RULE_REQUIRE_WORKS_REQUIREMENTS"``).
	* §8.5 sort by ``(display_order, form_code)`` for deterministic output.
	* §16 / STEP14-AC-008 raise ``ValueError`` if any activation references a
	  ``form_code`` not defined in ``forms.json``; silent omission would create
	  legal risk.
	"""
	forms_component = get_package_component(template, "forms")
	form_definitions = {
		f.get("form_code"): f
		for f in forms_component.get("forms") or []
		if isinstance(f, dict) and f.get("form_code")
	}

	activation_sources: dict[str, list[str]] = {}

	def _add_source(form_code: str, source: str) -> None:
		bucket = activation_sources.setdefault(form_code, [])
		if source not in bucket:
			bucket.append(source)

	for form_code, form in form_definitions.items():
		if form.get("default_required"):
			_add_source(form_code, "DEFAULT")

	if validation_result:
		for form_code, source in (validation_result.get("active_forms") or {}).items():
			_add_source(form_code, source)

	rows: list[dict[str, Any]] = []
	for form_code, sources in activation_sources.items():
		form = form_definitions.get(form_code)
		if not form:
			raise ValueError(
				f"Required-form activation references unknown form_code "
				f"{form_code!r}; check forms.json and rules.json."
			)
		checklist = form.get("checklist_display") or {}
		rows.append(
			{
				"form_code": form_code,
				"form_title": form.get("title"),
				"display_group": checklist.get("display_group"),
				"workflow_stage": form.get("workflow_stage"),
				"respondent_type": form.get("respondent_type"),
				"required": 1,
				"activation_source": "; ".join(sources),
				"evidence_policy": form.get("evidence_policy"),
				"display_order": checklist.get("display_order") or 0,
				"notes": "",
			}
		)
	rows.sort(key=lambda r: (r.get("display_order") or 0, r.get("form_code") or ""))
	return rows


# ---------------------------------------------------------------------------
# §10.13 — validation message child rows
# ---------------------------------------------------------------------------


def build_validation_message_rows(
	validation_result: dict[str, Any],
) -> list[dict[str, Any]]:
	"""Convert in-memory validation messages into ``Tender Validation Message`` child rows."""
	rows: list[dict[str, Any]] = []
	for message in (validation_result or {}).get("messages") or []:
		rows.append(
			{
				"severity": message.get("severity"),
				"rule_code": message.get("rule_code"),
				"message": message.get("message"),
				"affected_field": message.get("affected_field"),
				"affected_section": message.get("affected_section"),
				"affected_form": message.get("affected_form"),
				"blocks_generation": 1 if message.get("blocks_generation") else 0,
				"resolution_hint": message.get("resolution_hint") or "",
				"details_json": json.dumps(
					message.get("details") or {}, sort_keys=True, default=str
				),
			}
		)
	return rows


# ---------------------------------------------------------------------------
# §10.14 — render context
# ---------------------------------------------------------------------------


def build_render_context(
	template: dict[str, Any],
	config: dict[str, Any],
	lots: list[Any] | None = None,
	boq_items: list[Any] | None = None,
	validation_result: dict[str, Any] | None = None,
	required_forms: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
	"""Assemble the §14 render context for later Jinja rendering. Does NOT render HTML."""
	manifest = get_package_component(template, "manifest")
	doc = template.get("doc")
	template_summary = {
		"template_code": template.get("template_code"),
		"template_name": getattr(doc, "template_name", None) if doc is not None else None,
		"template_short_name": getattr(doc, "template_short_name", None)
		if doc is not None
		else None,
		"package_hash": template.get("package_hash"),
		"package_version": (manifest.get("versioning") or {}).get("package_version"),
		"version_label": (manifest.get("versioning") or {}).get("source_version_label"),
		"status": getattr(doc, "status", None) if doc is not None else None,
	}

	active_sections = resolve_active_sections(template, config, validation_result)

	configuration_hash = (
		(validation_result or {}).get("configuration_hash") or hash_config(config)
	)
	return {
		"template": template_summary,
		"manifest": manifest,
		"configuration": config,
		"active_sections": active_sections,
		"lots": _child_rows_to_dicts(lots),
		"boq_items": _child_rows_to_dicts(boq_items),
		"required_forms": list(required_forms or []),
		"validation": {
			"status": (validation_result or {}).get("status") or "Not Validated",
			"blocks_generation": bool(
				(validation_result or {}).get("blocks_generation")
			),
			"messages": list((validation_result or {}).get("messages") or []),
		},
		"audit": {
			"template_code": template.get("template_code"),
			"package_version": (manifest.get("versioning") or {}).get("package_version"),
			"package_hash": template.get("package_hash"),
			"configuration_hash": configuration_hash,
			"generated_at": now_datetime().isoformat(),
		},
	}


# ---------------------------------------------------------------------------
# §10.15 / §10.16 — tender document mutators (no save / no commit)
# ---------------------------------------------------------------------------


def apply_config_to_tender_doc(tender_doc: Any, config: dict[str, Any]) -> None:
	"""Write configuration JSON and summary fields onto a ``Procurement Tender`` doc.

	Mutates ``tender_doc`` only; caller is responsible for ``save()``.
	"""
	tender_doc.configuration_json = json.dumps(
		config, indent=2, sort_keys=True, default=str
	)
	tender_doc.tender_title = config.get("TENDER.TENDER_NAME") or tender_doc.tender_title
	tender_doc.tender_reference = (
		config.get("TENDER.TENDER_REFERENCE") or tender_doc.tender_reference
	)
	procurement_method = config.get("METHOD.PROCUREMENT_METHOD")
	if procurement_method:
		tender_doc.procurement_method = procurement_method
	tender_scope = config.get("METHOD.TENDER_SCOPE")
	if tender_scope:
		tender_doc.tender_scope = tender_scope
	procurement_category = config.get("SYSTEM.PROCUREMENT_CATEGORY") or "WORKS"
	tender_doc.procurement_category = procurement_category
	tender_doc.template_code = config.get("SYSTEM.TEMPLATE_CODE") or tender_doc.template_code
	tender_doc.template_version = (
		config.get("SYSTEM.PACKAGE_VERSION") or tender_doc.template_version
	)
	package_hash = config.get("SYSTEM.PACKAGE_HASH")
	if package_hash:
		tender_doc.package_hash = package_hash


def populate_sample_tender(tender_doc: Any, variant_code: str | None = None) -> None:
	"""Populate a ``Procurement Tender`` doc with sample config + lots + BoQ rows.

	Reads ``tender_doc.std_template`` for the template link; mutates child
	tables but does not call ``save()`` or ``commit()``.
	"""
	template_link = getattr(tender_doc, "std_template", None)
	if not template_link:
		raise ValueError(
			"Procurement Tender is missing std_template link; populate_sample_tender requires it."
		)
	template = load_template(template_link)
	config = load_sample_config(template, variant_code=variant_code)
	apply_config_to_tender_doc(tender_doc, config)

	tender_doc.set("lots", [])
	for lot in load_sample_lots(template, variant_code=variant_code):
		tender_doc.append("lots", lot)

	tender_doc.set("boq_items", [])
	boq_raw = load_sample_boq_rows(template, variant_code=variant_code)
	validate_sample_boq_rows(
		boq_raw,
		get_allowed_boq_categories(),
		existing_lot_codes=None,
		strict_lot_references=False,
	)
	for row in build_boq_child_rows(boq_raw):
		tender_doc.append("boq_items", row)


# ---------------------------------------------------------------------------
# §16.1 / §16.2 — persistence helpers (callers commit, not the engine)
# ---------------------------------------------------------------------------


def write_validation_to_tender(
	tender_doc: Any, validation_result: dict[str, Any]
) -> None:
	"""Replace the tender's ``validation_messages`` rows and update validation summary fields."""
	tender_doc.set("validation_messages", [])
	for row in build_validation_message_rows(validation_result):
		tender_doc.append("validation_messages", row)
	tender_doc.validation_status = validation_result.get("status") or "Not Validated"
	tender_doc.configuration_hash = validation_result.get("configuration_hash")
	tender_doc.last_validated_at = now_datetime()


def write_required_forms_to_tender(
	tender_doc: Any, required_forms: list[dict[str, Any]]
) -> None:
	"""Replace the tender's ``required_forms`` rows."""
	tender_doc.set("required_forms", [])
	for row in required_forms or []:
		tender_doc.append("required_forms", row)
