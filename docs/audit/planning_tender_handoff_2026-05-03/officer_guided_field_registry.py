# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Officer guided field registry — single source for field_code ↔ DocType mapping.

Built from bundled ``fields.json`` (no Frappe import required for static analysis / tests).
Canonical configuration keys always match ``field_code`` in the package.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

# STD field_code → existing Procurement Tender column (synonyms).
OFFICER_FIELD_SYNONYMS: dict[str, str] = {
	"TENDER.TENDER_NAME": "tender_title",
	"TENDER.TENDER_REFERENCE": "tender_reference",
	"METHOD.PROCUREMENT_METHOD": "procurement_method",
	"METHOD.TENDER_SCOPE": "tender_scope",
	"SYSTEM.PROCUREMENT_CATEGORY": "procurement_category",
}


def _fields_json_path() -> Path:
	return (
		Path(__file__).resolve().parent.parent
		/ "std_templates"
		/ "ke_ppra_works_building_2022_04_poc"
		/ "fields.json"
	)


def load_raw_fields_document() -> dict[str, Any]:
	"""Load ``fields.json`` from the Works POC package (pure filesystem)."""
	return json.loads(_fields_json_path().read_text(encoding="utf-8"))


@dataclass(frozen=True, slots=True)
class OfficerGuidedFieldSpec:
	field_code: str
	doctype_fieldname: str
	group_code: str
	std_field_type: str
	label: str
	options: tuple[str, ...]
	help_text: str


def doctype_fieldname_for_field_code(field_code: str) -> str:
	"""Stable Procurement Tender fieldname for a package ``field_code``."""
	if field_code in OFFICER_FIELD_SYNONYMS:
		return OFFICER_FIELD_SYNONYMS[field_code]
	# ``og_`` keeps names under Frappe's 64-char limit (``offcfg_`` can exceed it).
	return "og_" + field_code.replace(".", "_").lower()


def _frappe_fieldtype(std_type: str) -> str:
	m = {
		"TEXT": "Data",
		"LONG_TEXT": "Long Text",
		"SELECT": "Select",
		"BOOLEAN": "Check",
		"INTEGER": "Int",
		"DECIMAL": "Float",
		"MONEY": "Float",
		"PERCENT": "Percent",
		"DATE": "Date",
		"DATETIME": "Datetime",
		"DURATION_DAYS": "Int",
		"DURATION_MONTHS": "Int",
		"EMAIL": "Data",
		"URL": "Data",
		"ORGANIZATION_REF": "Data",
		"USER_REF": "Data",
	}
	return m.get(std_type, "Data")


def _build_specs_from_doc(fields_doc: dict[str, Any]) -> tuple[OfficerGuidedFieldSpec, ...]:
	specs: list[OfficerGuidedFieldSpec] = []
	for row in fields_doc.get("fields") or []:
		if not row.get("ordinary_user_editable", True):
			continue
		fc = row.get("field_code")
		if not fc:
			continue
		opts = row.get("options") or []
		if not isinstance(opts, list):
			opts = []
		specs.append(
			OfficerGuidedFieldSpec(
				field_code=str(fc),
				doctype_fieldname=doctype_fieldname_for_field_code(str(fc)),
				group_code=str(row.get("group_code") or ""),
				std_field_type=str(row.get("field_type") or "TEXT"),
				label=str(row.get("label") or fc),
				options=tuple(str(x) for x in opts),
				help_text=str(row.get("help_text") or ""),
			)
		)
	specs.sort(key=lambda s: (s.group_code, s.field_code))
	return tuple(specs)


@lru_cache(maxsize=1)
def get_officer_guided_field_specs() -> tuple[OfficerGuidedFieldSpec, ...]:
	return _build_specs_from_doc(load_raw_fields_document())


def get_officer_sync_field_codes() -> tuple[str, ...]:
	return tuple(s.field_code for s in get_officer_guided_field_specs())


def spec_by_field_code() -> dict[str, OfficerGuidedFieldSpec]:
	return {s.field_code: s for s in get_officer_guided_field_specs()}


def spec_by_doctype_fieldname() -> dict[str, OfficerGuidedFieldSpec]:
	out: dict[str, OfficerGuidedFieldSpec] = {}
	for s in get_officer_guided_field_specs():
		out[s.doctype_fieldname] = s
	return out


def group_label_for_code(group_code: str) -> str:
	"""Section label aligned to officer POC doc 8 §11 ordering."""
	order = {
		"TENDER_IDENTITY": "30. Tender Identity",
		"METHOD_PARTICIPATION": "40–50. Method, Scope and Participation",
		"DATES_MEETINGS": "60. Key Dates and Meetings",
		"SECURITIES": "70. Securities and Guarantees",
		"ALTERNATIVES_LOTS": "80–90. Alternatives and Lots",
		"QUALIFICATION": "100. Qualification Requirements",
		"WORKS_REQUIREMENTS": "110. Works Requirements",
		"CONTRACT_SCC": "120. Contract / SCC Parameters",
	}
	return order.get(group_code, group_code)


def officer_field_code_for_validation_row(affected_field: str | None) -> str | None:
	"""Normalize engine message keys to registry ``field_code`` if needed."""
	if not affected_field:
		return None
	if affected_field in spec_by_field_code():
		return affected_field
	return None


def enrich_validation_row_for_officer(row: dict[str, Any]) -> dict[str, Any]:
	"""Fill ``affected_section`` / ``resolution_hint`` when the engine omitted them."""
	fc = row.get("affected_field")
	if not fc:
		return row
	specs = spec_by_field_code()
	sp = specs.get(str(fc))
	if not sp:
		return row
	if not (row.get("affected_section") or "").strip():
		row = {**row, "affected_section": group_label_for_code(sp.group_code)}
	if not (row.get("resolution_hint") or "").strip():
		row = {
			**row,
			"resolution_hint": (
				f"Update “{sp.label}” in the {group_label_for_code(sp.group_code)} section "
				f"on this form, then use Sync Configuration and Validate."
			),
		}
	return row


def _truthy(v: Any) -> bool:
	if v is True or v is False:
		return bool(v)
	if isinstance(v, (int, float)):
		return v != 0
	if isinstance(v, str):
		return v.strip().lower() in ("1", "true", "yes", "y")
	return bool(v)


def coerce_doc_value_to_config(spec: OfficerGuidedFieldSpec, value: Any) -> Any:
	"""Convert a value read from a Procurement Tender field into JSON config form."""
	if value is None:
		return None
	t = spec.std_field_type
	if t == "BOOLEAN":
		return _truthy(value)
	if t in ("INTEGER", "DURATION_DAYS", "DURATION_MONTHS"):
		try:
			return int(value)
		except (TypeError, ValueError):
			return None
	if t in ("DECIMAL", "MONEY", "PERCENT"):
		try:
			return float(value)
		except (TypeError, ValueError):
			return None
	if t == "DATETIME" and hasattr(value, "isoformat"):
		return value.isoformat(sep=" ", timespec="seconds")
	if t == "DATE" and hasattr(value, "isoformat"):
		return value.isoformat()
	if isinstance(value, str):
		return value
	return value


def _tender_get(tender_doc: Any, fieldname: str) -> Any:
	getter = getattr(tender_doc, "get", None)
	if callable(getter):
		return getter(fieldname)
	return getattr(tender_doc, fieldname, None)


def _tender_set(tender_doc: Any, fieldname: str, value: Any) -> None:
	setter = getattr(tender_doc, "set", None)
	if callable(setter):
		tender_doc.set(fieldname, value)
	else:
		setattr(tender_doc, fieldname, value)


def apply_config_value_to_tender_field(
	spec: OfficerGuidedFieldSpec, tender_doc: Any, raw: Any
) -> None:
	"""Set one guided column on ``tender_doc`` from a configuration value (hydration)."""
	if raw is None:
		return
	t = spec.std_field_type
	if t == "BOOLEAN":
		_tender_set(tender_doc, spec.doctype_fieldname, 1 if _truthy(raw) else 0)
		return
	if t in ("INTEGER", "DURATION_DAYS", "DURATION_MONTHS"):
		try:
			_tender_set(tender_doc, spec.doctype_fieldname, int(raw))
		except (TypeError, ValueError):
			pass
		return
	if t in ("DECIMAL", "MONEY", "PERCENT"):
		try:
			_tender_set(tender_doc, spec.doctype_fieldname, float(raw))
		except (TypeError, ValueError):
			pass
		return
	if t in ("TEXT", "LONG_TEXT", "EMAIL", "URL", "ORGANIZATION_REF", "USER_REF", "SELECT"):
		_tender_set(tender_doc, spec.doctype_fieldname, str(raw))
		return
	if t == "DATE":
		_tender_set(tender_doc, spec.doctype_fieldname, raw)
		return
	if t == "DATETIME":
		_tender_set(tender_doc, spec.doctype_fieldname, raw)
		return
	_tender_set(tender_doc, spec.doctype_fieldname, raw)


def hydrate_officer_guided_fields_from_configuration(
	tender_doc: Any, configuration: dict[str, Any]
) -> None:
	"""Populate all guided DocType columns from a flat ``configuration`` dict."""
	for spec in get_officer_guided_field_specs():
		if spec.field_code not in configuration:
			continue
		apply_config_value_to_tender_field(spec, tender_doc, configuration.get(spec.field_code))


def build_officer_config_overlay_from_registry(tender_doc: Any) -> dict[str, Any]:
	"""Read guided Procurement Tender columns into flat STD configuration keys."""
	overlay: dict[str, Any] = {}
	for spec in get_officer_guided_field_specs():
		val = _tender_get(tender_doc, spec.doctype_fieldname)
		if spec.std_field_type == "BOOLEAN":
			overlay[spec.field_code] = bool(_truthy(val))
			continue
		coerced = coerce_doc_value_to_config(spec, val)
		if coerced is None:
			continue
		if coerced == "" and spec.std_field_type not in ("TEXT", "LONG_TEXT", "EMAIL", "URL", "SELECT"):
			continue
		overlay[spec.field_code] = coerced
	return overlay


def merge_registry_overlay_into_configuration(
	existing: dict[str, Any], tender_doc: Any
) -> dict[str, Any]:
	"""Deep-merge guided officer fields; preserve unknown ``configuration_json`` keys."""
	import copy

	merged = copy.deepcopy(existing)
	overlay = build_officer_config_overlay_from_registry(tender_doc)
	for k, v in overlay.items():
		merged[k] = v
	return merged


def frappe_field_dicts_for_new_columns() -> list[dict[str, Any]]:
	"""Produce Frappe ``fields`` entries for every non-synonym guided column."""
	existing = set(OFFICER_FIELD_SYNONYMS.values())
	out: list[dict[str, Any]] = []
	for spec in get_officer_guided_field_specs():
		if spec.doctype_fieldname in existing:
			continue
		ft = _frappe_fieldtype(spec.std_field_type)
		entry: dict[str, Any] = {
			"fieldname": spec.doctype_fieldname,
			"fieldtype": ft,
			"label": spec.label,
		}
		if spec.help_text:
			entry["description"] = spec.help_text[:140]
		if ft == "Select" and spec.options:
			entry["options"] = "\n".join(spec.options)
		out.append(entry)
	return out


def assert_registry_covers_poc_required_editable_fields() -> None:
	"""Fail if ``fields.json`` gains editable POC fields not represented in the registry."""
	doc = load_raw_fields_document()
	spec_codes = {s.field_code for s in get_officer_guided_field_specs()}
	missing: list[str] = []
	for row in doc.get("fields") or []:
		if not row.get("ordinary_user_editable", True):
			continue
		fc = row.get("field_code")
		if not fc:
			continue
		if str(fc) not in spec_codes:
			missing.append(str(fc))
	if missing:
		raise AssertionError(
			"Officer registry missing ordinary_user_editable fields: " + ", ".join(missing)
		)
