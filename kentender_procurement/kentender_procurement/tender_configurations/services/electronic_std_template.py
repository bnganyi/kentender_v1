# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Lean electronic STD template load, instantiate, and hash for publication."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.tender_configurations.electronic_std_templates import (
	CANONICAL_SECTION_KEYS,
	TEMPLATE_ID_PPRA_IT_STD,
	TEMPLATE_VERSION_V1,
)
from kentender_procurement.tender_configurations.electronic_std_templates.validator import (
	TemplateValidationError,
	assert_approved_for_ordinary_publication,
	assert_valid_ppra_it_std_v1,
	validate_template,
)


def _canonical_hash(payload: Any) -> str:
	blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
	return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _parse_json(raw: Any, default: Any = None) -> Any:
	if raw is None or raw == "":
		return default if default is not None else {}
	if isinstance(raw, (dict, list)):
		return raw
	try:
		return json.loads(raw)
	except (TypeError, ValueError):
		return default if default is not None else {}


def _throw(message: str, title: str = "KT_ELECTRONIC_TEMPLATE_ERROR") -> None:
	frappe.throw(frappe._(message), title=title)


def _truthy_flag(val: Any) -> bool:
	return cstr(val or "").strip().lower() in ("yes", "true", "1", "y")


_LINKED_SECTION_TITLES = {
	"form_of_tender": "Form of Tender",
	"statutory_declarations": "Statutory Declarations",
	"tender_security": "Tender Security",
	"confidential_business_questionnaire": "Confidential Business Questionnaire",
}

_ALLOWED_RESPONSE_METHODS = frozenset(
	{
		"upload",
		"select_or_upload",
		"verification_reference",
		"structured",
		"linked_section",
	}
)

_ALLOWED_APPLICABILITY = frozenset({"always", "jv_only", "single_bidder_only"})

# Digitised electronic owners — never default these to mandatory upload.
_DIGITIZED_PRELIM_BY_ID: dict[str, str] = {
	"PRELIM-05": "tender_security",
	"PRELIM-06": "form_of_tender",
	"PRELIM-07": "statutory_declarations",
	"PRELIM-08": "statutory_declarations",
	"prelim-form-of-tender": "form_of_tender",
	"prelim-statutory-declarations": "statutory_declarations",
	"prelim-tender-security": "tender_security",
}


def _infer_digitized_linked_section(cid: str, title: str, instruction: str) -> str:
	"""Return linked_section_key when a criterion is owned by a dedicated electronic section."""
	key = _DIGITIZED_PRELIM_BY_ID.get(cstr(cid or "").strip())
	if key:
		return key
	blob = f"{title} {instruction}".lower()
	if "form of tender" in blob:
		return "form_of_tender"
	if (
		"independent tender determination" in blob
		or "certificate of independent" in blob
		or ("fraud and corruption" in blob and "declaration" in blob)
		or "self-declaration form" in blob
	):
		return "statutory_declarations"
	if "tender security" in blob or "tender-securing" in blob:
		return "tender_security"
	# NSSF mislabel: “Professional Indemnity – KES …” with bank guarantee / insurance bond.
	if "indemnity" in blob and ("bank guarantee" in blob or "insurance bond" in blob):
		return "tender_security"
	return ""


def _slug_criterion_id(title: str, index: int) -> str:
	raw = "".join(ch.lower() if ch.isalnum() else "-" for ch in cstr(title or "").strip())
	while "--" in raw:
		raw = raw.replace("--", "-")
	raw = raw.strip("-") or f"criterion-{index + 1}"
	return f"prelim-{raw}"[:80]


def _normalize_file_types(raw: Any) -> list[str]:
	if isinstance(raw, str) and raw.strip():
		parts = [p.strip().lower() for p in raw.replace(";", ",").split(",") if p.strip()]
		return [("." + p.lstrip(".")) for p in parts]
	if isinstance(raw, list):
		out = []
		for item in raw:
			p = cstr(item).strip().lower()
			if p:
				out.append("." + p.lstrip("."))
		return out
	return [".pdf"]


def materialize_requirements_compliance(
	evaluation: dict[str, Any] | None,
	it_requirements: list[dict[str, Any]] | None = None,
	*,
	default_fixture: str = "standard",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
	"""Build section requirements[] + response field catalog for Requirements Compliance.

	Returns ``(requirements, default_response_fields, flags)``.
	"""
	from kentender_procurement.tender_configurations.seed.lean_requirements_compliance import (
		MODE_EXCLUDED,
		cstr_fixture,
		lean_requirements_compliance_rows,
	)
	from kentender_procurement.tender_configurations.services.schema_compiler import (
		RESPONSE_FIELDS_PER_REQUIREMENT,
	)

	ev = evaluation if isinstance(evaluation, dict) else {}
	raw = ev.get("requirements_compliance_rows")
	if not isinstance(raw, list) or not raw:
		# Prefer pack lean fixtures. Only consume it_requirements when they already carry
		# lean RC shape (mode + tender-facing ref) — never dump NSSF calibration rows.
		lean_like: list[dict[str, Any]] = []
		if isinstance(it_requirements, list):
			for row in it_requirements:
				if not isinstance(row, dict):
					continue
				if cstr(row.get("requirement_mode") or "").strip() and cstr(
					row.get("tender_facing_reference") or row.get("reference") or ""
				).strip():
					lean_like.append(row)
		if lean_like:
			raw = lean_like
		else:
			raw = lean_requirements_compliance_rows(
				cstr(ev.get("requirements_compliance_fixture") or default_fixture)
			)
	flags = ev.get("requirements_compliance_flags")
	if not isinstance(flags, dict):
		flags = {}

	out: list[dict[str, Any]] = []
	for idx, row in enumerate(raw):
		if not isinstance(row, dict):
			continue
		rid = cstr(row.get("requirement_id") or row.get("id") or "").strip()
		if not rid:
			continue
		mode = cstr(row.get("requirement_mode") or "").strip().lower()
		if not mode:
			# Legacy treatment_label / mandatory
			treatment = cstr(row.get("treatment_label") or "").strip().lower()
			if treatment in ("optional",):
				mode = "optional"
			elif treatment in ("informational", "info"):
				mode = "informational"
			elif row.get("mandatory") in (0, "0", False, "false"):
				mode = "optional"
			else:
				mode = "required"
		if mode == MODE_EXCLUDED or row.get("withdrawn") in (1, "1", True, "true"):
			# Keep withdrawn for history but mark excluded/not displayed in active matrix.
			if mode != MODE_EXCLUDED:
				mode = MODE_EXCLUDED
		title = cstr(row.get("requirement_title") or row.get("title") or "").strip()
		statement = cstr(
			row.get("requirement_statement") or row.get("description") or title
		).strip()
		group = cstr(
			row.get("category_label")
			or row.get("group")
			or row.get("requirement_family")
			or "General"
		).strip() or "General"
		ref = cstr(row.get("tender_facing_reference") or row.get("reference") or "").strip()
		fields = row.get("response_fields")
		if not isinstance(fields, list) or not fields:
			fields = list(RESPONSE_FIELDS_PER_REQUIREMENT)
		out.append(
			{
				"id": rid,
				"requirement_id": rid,
				"tender_facing_reference": ref or rid,
				"requirement_title": title or rid,
				"title": title or rid,
				"requirement_statement": statement,
				"description": statement,
				"category_label": group,
				"group": group,
				"display_order": int(row.get("display_order") or (idx + 1) * 10),
				"requirement_mode": mode,
				"mandatory": 1 if mode == "required" else 0,
				"renderer": cstr(row.get("renderer") or "combined"),
				"scope": cstr(row.get("scope") or "tender"),
				"condition_key": cstr(row.get("condition_key") or "always"),
				"explanation_required": 1 if row.get("explanation_required") not in (0, "0", False) else 0,
				"evidence_required": 1 if row.get("evidence_required") in (1, "1", True, "true") else 0,
				"technical_alternative_permitted": 1
				if row.get("technical_alternative_permitted") in (1, "1", True, "true")
				else 0,
				"published_revision": int(row.get("published_revision") or 1),
				"bidder_facing_change_summary": cstr(row.get("bidder_facing_change_summary") or ""),
				"updated_by_addendum": cstr(row.get("updated_by_addendum") or ""),
				"withdrawn": 1 if row.get("withdrawn") in (1, "1", True, "true") else 0,
				"response_fields": fields,
				"bidder_response_type": cstr(row.get("bidder_response_type") or ""),
				"not_applicable": 0,
			}
		)
	out.sort(key=lambda r: (int(r.get("display_order") or 0), cstr(r.get("requirement_id"))))
	default_fields = list(RESPONSE_FIELDS_PER_REQUIREMENT)
	# Prefer first required row's fields as section-level default when uniform.
	for r in out:
		if r.get("requirement_mode") == "required" and isinstance(r.get("response_fields"), list):
			default_fields = list(r["response_fields"])
			break
	_ = cstr_fixture  # keep import used for callers that pass fixture via evaluation
	return out, default_fields, flags


def _normalize_technical_proposal_subsection_rows(
	raw: list[Any],
	*,
	mode_excluded: str,
) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	structured = {
		"implementation_work_plan",
		"training_and_knowledge_transfer",
		"risks_assumptions_and_dependencies",
		"technical_alternatives",
		"integration_responsibility_confirmation",
		"project_organization_and_coordination",
		"testing_and_quality_assurance",
	}
	for idx, row in enumerate(raw or []):
		if not isinstance(row, dict):
			continue
		key = cstr(row.get("subsection_key") or "").strip()
		title = cstr(row.get("title") or "").strip()
		renderer = cstr(row.get("renderer") or "").strip()
		if not key or not title:
			continue
		mode = cstr(row.get("requirement_mode") or "required").strip().lower()
		if mode not in ("required", "optional", "conditional", "excluded"):
			mode = "required"
		questions = [q for q in (row.get("questions") or []) if isinstance(q, dict)]
		# Enabled subsection without renderer or questions (where questions expected) is skipped
		# except known structured renderers that may have empty questions.
		if mode != mode_excluded and not renderer:
			continue
		if mode != mode_excluded and not questions and renderer not in structured:
			continue
		try:
			display_order = (
				int(flt(row.get("display_order")))
				if row.get("display_order") not in (None, "")
				else (idx + 1) * 10
			)
		except (TypeError, ValueError):
			display_order = (idx + 1) * 10
		out.append(
			{
				"subsection_key": key,
				"title": title,
				"description": cstr(row.get("description") or ""),
				"renderer": renderer,
				"display_order": display_order,
				"requirement_mode": mode,
				"condition_key": cstr(row.get("condition_key") or "always"),
				"scope": cstr(row.get("scope") or "tender"),
				"questions": questions,
				"evidence_required": bool(row.get("evidence_required")),
				"min_activities": row.get("min_activities"),
				"min_test_stages": row.get("min_test_stages"),
				"min_risks": row.get("min_risks"),
				"max_completion_weeks": row.get("max_completion_weeks"),
				"audiences": row.get("audiences") if isinstance(row.get("audiences"), list) else [],
			}
		)
	out.sort(key=lambda r: int(r.get("display_order") or 0))
	return out


def materialize_technical_proposal_subsections(
	evaluation: dict[str, Any] | None,
	*,
	default_fixture: str = "full",
) -> list[dict[str, Any]]:
	"""Build section subsections[] from evaluation_setup.technical_proposal_subsections."""
	from kentender_procurement.tender_configurations.seed.lean_technical_proposal import (
		MODE_EXCLUDED,
		lean_technical_proposal_subsections,
	)

	ev = evaluation if isinstance(evaluation, dict) else {}
	fixture = cstr(ev.get("technical_proposal_fixture") or default_fixture).strip() or default_fixture
	raw = ev.get("technical_proposal_subsections")
	if not isinstance(raw, list) or not raw:
		raw = lean_technical_proposal_subsections(fixture)
	out = _normalize_technical_proposal_subsection_rows(raw, mode_excluded=MODE_EXCLUDED)
	# Junk / empty config lists must not yield a mandatory section with 0 subsections.
	if not out:
		out = _normalize_technical_proposal_subsection_rows(
			lean_technical_proposal_subsections(fixture),
			mode_excluded=MODE_EXCLUDED,
		)
	return out


def heal_technical_proposal_subsections_in_snapshot(
	snapshot: dict[str, Any],
	*,
	configuration_id: str = "",
	evaluation: dict[str, Any] | None = None,
) -> bool:
	"""Fill missing TP subsections on a published snapshot (pre-materialize pubs).

	Returns True when the snapshot was mutated.
	"""
	if not isinstance(snapshot, dict):
		return False
	sections = snapshot.get("sections")
	if not isinstance(sections, list):
		return False
	sec = next(
		(
			s
			for s in sections
			if isinstance(s, dict)
			and cstr(s.get("section_key") or "") == "technical_proposal_and_implementation_plan"
		),
		None,
	)
	if not sec:
		return False
	existing = sec.get("subsections")
	if isinstance(existing, list) and existing:
		return False
	ev = evaluation if isinstance(evaluation, dict) else None
	if ev is None and configuration_id:
		ev = _parse_json(
			frappe.db.get_value("Tender Configuration", configuration_id, "evaluation_setup"),
			{},
		)
		if not isinstance(ev, dict):
			ev = {}
	subs = materialize_technical_proposal_subsections(ev or {})
	if not subs:
		return False
	sec["subsections"] = subs
	sec["slice_status"] = "technical_proposal_implemented"
	flags = (ev or {}).get("technical_proposal_flags") if isinstance(ev, dict) else None
	if isinstance(flags, dict):
		sec["technical_proposal_flags"] = flags
	return True


def materialize_qualification_categories(
	evaluation: dict[str, Any] | None,
	*,
	default_fixture: str = "full",
) -> list[dict[str, Any]]:
	"""Build section categories[] from evaluation_setup.qualification_categories.

	Falls back to lean PE-neutral fixtures when CFG omits categories. Never hard-codes NSSF.
	"""
	from kentender_procurement.tender_configurations.seed.lean_qualification_criteria import (
		MODE_EXCLUDED,
		lean_qualification_categories,
	)

	ev = evaluation if isinstance(evaluation, dict) else {}
	raw = ev.get("qualification_categories")
	if not isinstance(raw, list) or not raw:
		raw = lean_qualification_categories(cstr(ev.get("qualification_fixture") or default_fixture))
	out: list[dict[str, Any]] = []
	for idx, row in enumerate(raw):
		if not isinstance(row, dict):
			continue
		key = cstr(row.get("category_key") or "").strip()
		label = cstr(row.get("label") or row.get("title") or "").strip()
		if not key or not label:
			continue
		mode = cstr(row.get("requirement_mode") or "required").strip().lower()
		if mode not in ("required", "optional", "conditional", "excluded"):
			mode = "required"
		criteria = [c for c in (row.get("criteria") or []) if isinstance(c, dict)]
		positions = [p for p in (row.get("positions") or []) if isinstance(p, dict)]
		items = [i for i in (row.get("items") or []) if isinstance(i, dict)]
		# Empty configured category (no criteria/positions/items) is a config error — omit from bidder UI.
		if mode != MODE_EXCLUDED and not criteria and not positions and not items:
			continue
		try:
			display_order = (
				int(flt(row.get("display_order")))
				if row.get("display_order") not in (None, "")
				else (idx + 1) * 10
			)
		except (TypeError, ValueError):
			display_order = (idx + 1) * 10
		out.append(
			{
				"category_key": key,
				"label": label,
				"renderer": cstr(row.get("renderer") or key).strip() or key,
				"display_order": display_order,
				"requirement_mode": mode,
				"condition_key": cstr(row.get("condition_key") or "always").strip() or "always",
				"requirement_summary": cstr(row.get("requirement_summary") or "").strip(),
				"scope": cstr(row.get("scope") or "tender").strip() or "tender",
				"allow_duplicate_personnel": bool(row.get("allow_duplicate_personnel")),
				"criteria": criteria,
				"positions": positions,
				"items": items,
			}
		)
	out.sort(key=lambda r: (int(r.get("display_order") or 0), cstr(r.get("label") or "")))
	return out


def materialize_preliminary_criteria(criteria: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""Build section criteria[] from CFG evaluation rows where stage == Preliminary.

	Uses fields present on each evaluation criterion (response method, linked section, etc.).
	Does not hard-code NSSF titles. Missing method defaults to upload (or linked_section when
	linked_section_key is set). Digitised FoT / declarations / tender security never remain
	as mandatory uploads even when CFG omitted response_method.
	"""
	out: list[dict[str, Any]] = []
	idx = 0
	for row in criteria or []:
		if not isinstance(row, dict):
			continue
		if cstr(row.get("stage")) != "Preliminary":
			continue
		title = cstr(row.get("criterion_name") or row.get("title") or "").strip()
		if not title:
			continue
		cid = cstr(row.get("criterion_id") or "").strip() or _slug_criterion_id(title, idx)
		method = cstr(row.get("response_method") or "").strip().lower()
		linked = cstr(row.get("linked_section_key") or "").strip()
		instruction = cstr(
			row.get("evidence_instruction")
			or row.get("pass_fail_rule")
			or row.get("bidder_evidence")
			or ""
		).strip()
		inferred = _infer_digitized_linked_section(cid, title, instruction)
		if inferred and (not linked or method in ("", "upload")):
			linked = inferred
			method = "linked_section"
		if linked and method not in _ALLOWED_RESPONSE_METHODS:
			method = "linked_section"
		if method not in _ALLOWED_RESPONSE_METHODS:
			method = "upload"
		# Hard guard: digitised electronic sections cannot stay as uploads.
		if method == "upload" and inferred:
			linked = inferred
			method = "linked_section"
		applicability = cstr(row.get("applicability") or "always").strip().lower()
		if applicability not in _ALLOWED_APPLICABILITY:
			applicability = "always"
		if not instruction and method == "linked_section" and linked:
			section_title = _LINKED_SECTION_TITLES.get(linked, linked.replace("_", " ").title())
			instruction = f"Complete the {section_title} section in the bidder workspace."
		try:
			display_order = int(flt(row.get("display_order"))) if row.get("display_order") not in (None, "") else (idx + 1) * 10
		except (TypeError, ValueError):
			display_order = (idx + 1) * 10
		try:
			max_mb = int(flt(row.get("max_file_size_mb"))) if row.get("max_file_size_mb") not in (None, "") else 5
		except (TypeError, ValueError):
			max_mb = 5
		mandatory = row.get("mandatory")
		if mandatory is None:
			be = cstr(row.get("bidder_evidence") or "").strip().lower()
			mandatory = be not in ("optional", "not required", "no", "false", "0")
		fulfilment_method = cstr(row.get("fulfilment_method") or "").strip()
		if not fulfilment_method:
			fulfilment_method = (
				"electronic_section" if method == "linked_section" else "tender_evidence"
			)
		owner = cstr(row.get("owner") or "").strip()
		if not owner:
			owner = linked if method == "linked_section" else "preliminary_requirements"
		item: dict[str, Any] = {
			"criterion_id": cid,
			"title": title,
			"evidence_instruction": instruction,
			"mandatory": bool(mandatory),
			"applicability": applicability,
			"response_method": method,
			"linked_section_key": linked if method == "linked_section" else "",
			"linked_section_title": _LINKED_SECTION_TITLES.get(linked, "") if linked else "",
			"fulfilment_method": fulfilment_method,
			"owner": owner,
			"validity_rule": cstr(row.get("validity_rule") or "").strip(),
			"accepted_file_types": _normalize_file_types(row.get("accepted_file_types")),
			"max_file_size_mb": max(1, max_mb),
			"display_order": display_order,
			"evidence_type": cstr(row.get("evidence_type") or "supporting_document").strip()
			or "supporting_document",
			"criterion_group": cstr(row.get("criterion_group") or "").strip()
			or ("linked" if method == "linked_section" else ""),
		}
		structured = row.get("structured_fields")
		if isinstance(structured, list):
			item["structured_fields"] = [s for s in structured if isinstance(s, dict)]
		else:
			item["structured_fields"] = []
		ver_fields = row.get("verification_fields")
		if isinstance(ver_fields, list):
			item["verification_fields"] = [s for s in ver_fields if isinstance(s, dict)]
		else:
			item["verification_fields"] = (
				[{"field_key": "verification_reference", "label": "Verification reference", "required": True}]
				if method == "verification_reference"
				else []
			)
		out.append(item)
		idx += 1
	out.sort(key=lambda r: (int(r.get("display_order") or 0), cstr(r.get("title") or "")))
	return out


def load_validated_template() -> dict[str, Any]:
	"""Load curated template + approval; structural checks only (Draft allowed)."""
	try:
		return assert_valid_ppra_it_std_v1(require_approved=False)
	except TemplateValidationError as exc:
		_throw("; ".join(exc.errors), title="KT_ELECTRONIC_TEMPLATE_INVALID")


def require_approved_template(
	*,
	template: dict[str, Any] | None = None,
	approval: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Return validated Approved template bundle or throw (ordinary publication)."""
	if template is None or approval is None:
		try:
			return assert_valid_ppra_it_std_v1(require_approved=True)
		except TemplateValidationError as exc:
			status = ""
			try:
				from kentender_procurement.tender_configurations.electronic_std_templates.validator import (
					load_ppra_it_std_v1_approval,
				)

				status = cstr((approval or load_ppra_it_std_v1_approval()).get("status") or "")
			except Exception:
				status = ""
			if status != "Approved" or any("Approved" in e for e in exc.errors):
				_throw(
					"Only an Approved electronic STD template may be published.",
					title="KT_ELECTRONIC_TEMPLATE_UNAPPROVED",
				)
			_throw("; ".join(exc.errors), title="KT_ELECTRONIC_TEMPLATE_INVALID")

	if str(approval.get("status") or "") != "Approved":
		_throw(
			"Only an Approved electronic STD template may be published.",
			title="KT_ELECTRONIC_TEMPLATE_UNAPPROVED",
		)
	errors = validate_template(template)
	prep = str(approval.get("prepared_by") or "").strip().lower()
	appr = str(approval.get("approved_by") or "").strip().lower()
	if prep and appr and prep == appr:
		errors.append("Preparer must not be the final approver")
	if not approval.get("template_file_hash"):
		errors.append("Approval missing template_file_hash")
	if not appr:
		errors.append("Approval missing approved_by")
	if errors:
		_throw("; ".join(errors), title="KT_ELECTRONIC_TEMPLATE_INVALID")
	return {
		"template": template,
		"approval": approval,
		"template_file_hash": cstr(approval.get("template_file_hash") or ""),
	}


def _cfg_blob(doc, field: str) -> Any:
	return _parse_json(getattr(doc, field, None), {})


def _requirements_list(raw: Any) -> list[dict[str, Any]]:
	if isinstance(raw, list):
		return [r for r in raw if isinstance(r, dict)]
	if isinstance(raw, dict):
		for key in ("requirements", "items", "rows"):
			val = raw.get(key)
			if isinstance(val, list):
				return [r for r in val if isinstance(r, dict)]
	return []


def _schedule_rows(raw: Any) -> list[dict[str, Any]]:
	if isinstance(raw, list):
		return [r for r in raw if isinstance(r, dict)]
	if isinstance(raw, dict):
		for key in ("rows", "items", "milestones", "schedule"):
			val = raw.get(key)
			if isinstance(val, list):
				return [r for r in val if isinstance(r, dict)]
	return []


def _price_lines(raw: Any) -> list[dict[str, Any]]:
	if isinstance(raw, list):
		return [r for r in raw if isinstance(r, dict)]
	if isinstance(raw, dict):
		items = raw.get("items")
		if isinstance(items, list):
			return [r for r in items if isinstance(r, dict)]
	return []


def _contract_values(raw: Any) -> list[dict[str, Any]]:
	if isinstance(raw, list):
		return [r for r in raw if isinstance(r, dict)]
	if isinstance(raw, dict):
		vals = raw.get("contract_values")
		if isinstance(vals, list):
			return [v for v in vals if isinstance(v, dict)]
	return []


def _criteria(raw: Any) -> list[dict[str, Any]]:
	if isinstance(raw, list):
		return [r for r in raw if isinstance(r, dict)]
	if isinstance(raw, dict):
		crit = raw.get("criteria")
		if isinstance(crit, list):
			return [c for c in crit if isinstance(c, dict)]
	return []


def _price_summary_from_config(price_blob: Any, tds: dict[str, Any]) -> dict[str, Any]:
	"""Read-only price summary placeholders; bidder never re-types totals."""
	lines = _price_lines(price_blob)
	summary = {
		"line_count": len(lines),
		"currency": cstr(tds.get("tender_currency") or "KES"),
		"total_excluding_vat": None,
		"vat_rate": None,
		"vat_amount": None,
		"grand_total": None,
		"amount_in_words": None,
		"source": "price_schedule_when_completed",
		"message": "Totals are derived from the Price Schedule when completed.",
	}
	if isinstance(price_blob, dict):
		for key in ("total_excluding_vat", "vat_amount", "grand_total", "vat_rate"):
			if price_blob.get(key) not in (None, ""):
				summary[key] = price_blob.get(key)
		if price_blob.get("configured_summary"):
			summary.update(price_blob.get("configured_summary") or {})
			summary["source"] = "configured_price_summary"
	nested = (price_blob or {}).get("summary") if isinstance(price_blob, dict) else None
	if isinstance(nested, dict):
		for key in ("total_excluding_vat", "vat_amount", "grand_total", "vat_rate", "amount_in_words"):
			if nested.get(key) not in (None, ""):
				summary[key] = nested.get(key)
		summary["source"] = "configured_price_summary"
	return summary


def _resolve_slot_value(binding: str, *, ctx: dict[str, Any]) -> Any:
	parts = [p for p in cstr(binding or "").split(".") if p]
	cur: Any = ctx
	for part in parts:
		if isinstance(cur, dict):
			cur = cur.get(part)
		else:
			return None
	return cur


def _controlled_decisions(tds: dict[str, Any], contract: dict[str, Any], forms: dict[str, Any]) -> list[dict[str, Any]]:
	"""Compact list of controlled tender decisions for observed counts."""
	decisions = []
	mapping = [
		("tender_security_required", tds.get("tender_security_required")),
		("tender_currency", tds.get("tender_currency")),
		("bid_validity_period", tds.get("bid_validity_period")),
		("margin_of_preference_applies", tds.get("margin_of_preference_applies")),
		("submission_channel", tds.get("submission_channel")),
		("pre_tender_meeting", tds.get("pre_tender_meeting")),
		("alternatives_permitted", tds.get("alternatives_permitted") or tds.get("alternative_tenders_permitted") or tds.get("alternative_tenders_allowed")),
		("opening_method", tds.get("opening_method")),
	]
	for key, val in mapping:
		if val not in (None, ""):
			decisions.append({"decision_key": key, "value": val})
	for row in _contract_values(contract)[:8]:
		cid = cstr(row.get("contract_value_id") or row.get("item_label") or "")
		if cid and not any(d.get("decision_key") == cid for d in decisions):
			decisions.append(
				{
					"decision_key": cid,
					"value": row.get("value_or_obligation") or row.get("value"),
				}
			)
	return decisions


def _lots_or_alternatives_configured(tds: dict[str, Any], cfg) -> bool:
	"""True when multi-lot or alternative tenders are configured for this tender."""
	lot = cstr(
		tds.get("lot_structure")
		or getattr(cfg, "lot_structure", None)
		or ""
	).strip().lower()
	if "multiple" in lot:
		return True
	if _truthy_flag(
		tds.get("alternatives_permitted")
		or tds.get("alternative_tenders_permitted")
		or tds.get("alternative_tenders_allowed")
	):
		return True
	lots_blob = _parse_json(getattr(cfg, "lots", None), None)
	if isinstance(lots_blob, list) and len(lots_blob) > 1:
		return True
	if isinstance(lots_blob, dict):
		rows = lots_blob.get("lots") or lots_blob.get("items") or []
		if isinstance(rows, list) and len(rows) > 1:
			return True
	return False


def _tender_security_required(tds: dict[str, Any]) -> bool:
	return _truthy_flag(tds.get("tender_security_required"))


def resolve_tender_security_mode(tds: dict[str, Any] | None) -> str:
	"""Map published TDS to instrument | securing_declaration | none.

	Exactly one mode. Declaration and instrument are mutually exclusive.
	"""
	tds = tds if isinstance(tds, dict) else {}
	typ = cstr(tds.get("tender_security_type") or "").strip()
	req = _tender_security_required(tds)
	if typ == "Not Required":
		return "none"
	if typ == "Tender-Securing Declaration":
		return "securing_declaration"
	if typ == "Tender Security":
		return "instrument"
	if not req:
		return "none"
	# Legacy seeds: required Yes without a canonical type → instrument.
	return "instrument"


def _tender_security_applicable(tds: dict[str, Any]) -> bool:
	return resolve_tender_security_mode(tds) != "none"


def resolve_section_applicability(
	sec: dict[str, Any],
	*,
	tds: dict[str, Any],
	cfg,
) -> bool:
	"""Resolve whether a registry section is applicable for this tender."""
	app = sec.get("applicability") or {}
	if not isinstance(app, dict):
		return True
	if app.get("always") is True:
		return True
	if app.get("always") is False:
		return False
	when = cstr(app.get("when") or "").strip()
	if not when:
		return True
	if when == "lots_or_alternatives_configured":
		return _lots_or_alternatives_configured(tds, cfg)
	if when == "tender_security_required":
		# Historic when-clause: still means "instrument-style required flag".
		# Prefer tender_security_applicable for the lean section row.
		return _tender_security_required(tds)
	if when == "tender_security_applicable":
		return _tender_security_applicable(tds)
	# Unknown condition — fail closed (omit section).
	return False


def build_electronic_submission_template(
	configuration_id: str,
	*,
	require_approved: bool = False,
) -> dict[str, Any]:
	"""Instantiate PPRA IT STD template onto a confirmed configuration.

	Returns ``{snapshot, hash, template_id, template_version}``.
	By default Draft/Reviewed templates may be instantiated (development preview).
	Ordinary bidder-visible publication must call with ``require_approved=True``.
	"""
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		_throw("Tender configuration not found.", title="KT_ELECTRONIC_TEMPLATE_CONFIG")

	if require_approved:
		bundle = require_approved_template()
	else:
		bundle = load_validated_template()
	template = bundle["template"]
	approval = bundle["approval"]

	cfg = frappe.get_doc("Tender Configuration", configuration_id)
	pkg_name = cstr(getattr(cfg, "confirmed_document_package", None) or "").strip()
	if not pkg_name or not frappe.db.exists("Confirmed Tender Document Package", pkg_name):
		_throw(
			"A confirmed tender document package is required before building the electronic template.",
			title="KT_ELECTRONIC_TEMPLATE_PACKAGE",
		)
	pkg = frappe.get_doc("Confirmed Tender Document Package", pkg_name)

	tds = _cfg_blob(cfg, "tds_values")
	if not isinstance(tds, dict):
		tds = {}
	reqs_raw = _parse_json(getattr(cfg, "it_requirements", None), [])
	requirements = _requirements_list(reqs_raw)
	evaluation = _cfg_blob(cfg, "evaluation_setup")
	criteria = _criteria(evaluation)
	schedule_raw = _parse_json(getattr(cfg, "implementation_schedule", None), {})
	schedule = _schedule_rows(schedule_raw)
	price_raw = _parse_json(getattr(cfg, "price_schedule", None), {})
	price_lines = _price_lines(price_raw)
	contract_raw = _parse_json(getattr(cfg, "contract_values", None), {})
	contract_vals = _contract_values(contract_raw)
	forms_raw = _parse_json(getattr(cfg, "forms_and_evidence", None), {})

	missing: list[str] = []
	tender_title = cstr(cfg.tender_title or "").strip()
	entity = cstr(cfg.procuring_entity_name or "").strip()
	scope = cstr(cfg.short_scope_summary or "").strip()
	currency = cstr(tds.get("tender_currency") or "").strip()
	validity = cstr(tds.get("bid_validity_period") or tds.get("tender_validity_period") or "").strip()
	if not tender_title:
		missing.append("tender_title")
	if not entity:
		missing.append("procuring_entity_name")
	if not scope:
		missing.append("short_scope_summary")
	if not currency:
		missing.append("tds.tender_currency")
	if not validity:
		missing.append("tds.bid_validity_period")
	if missing:
		_throw(
			"Missing mandatory electronic template bindings: " + ", ".join(missing),
			title="KT_ELECTRONIC_TEMPLATE_BINDINGS",
		)

	price_summary = _price_summary_from_config(price_raw, tds)
	ctx = {
		"configuration": {
			"tender_title": tender_title,
			"procuring_entity_name": entity,
			"short_scope_summary": scope,
			"configuration_ref": cstr(cfg.configuration_ref or cfg.name),
			"procurement_method": cstr(cfg.procurement_method or ""),
			"it_requirements": requirements,
			"evaluation_setup": evaluation if isinstance(evaluation, dict) else {"criteria": criteria},
			"implementation_schedule": schedule_raw,
			"price_schedule": price_raw,
			"contract_values": contract_raw,
		},
		"tds": tds,
		"package": {
			"document_hash": cstr(pkg.document_hash or ""),
			"configuration_version": cstr(getattr(pkg, "configuration_version", None) or ""),
			"package_id": pkg.name,
		},
		"publication": {
			"published_at": None,
		},
		"contract": {
			"performance_security": next(
				(
					cstr(v.get("value_or_obligation") or v.get("value") or "")
					for v in contract_vals
					if "performance" in cstr(v.get("item_label") or v.get("contract_value_id") or "").lower()
				),
				cstr(tds.get("performance_security") or ""),
			),
		},
		"price_summary": price_summary,
	}

	prelim = sum(1 for c in criteria if cstr(c.get("stage")) == "Preliminary")
	tech_pass = sum(
		1
		for c in criteria
		if cstr(c.get("stage")) == "Technical" and cstr(c.get("evaluation_basis")) == "Pass/Fail"
	)
	tech_scored = sum(
		1
		for c in criteria
		if cstr(c.get("stage")) == "Technical" and cstr(c.get("evaluation_basis")) == "Scored"
	)
	qual_count = sum(1 for c in criteria if cstr(c.get("stage")) == "Qualification")

	groups: set[str] = set()
	normalized_requirements: list[dict[str, Any]] = []
	for r in requirements:
		row = dict(r)
		g = cstr(
			row.get("group")
			or row.get("group_key")
			or row.get("requirement_family")
			or row.get("category_label")
			or row.get("category")
			or ""
		)
		if g:
			groups.add(g)
			row.setdefault("group_key", g)
			row.setdefault("group", g)
		normalized_requirements.append(row)
	requirements = normalized_requirements

	decisions = _controlled_decisions(
		tds,
		contract_raw if isinstance(contract_raw, dict) else {},
		forms_raw if isinstance(forms_raw, dict) else {},
	)

	security_required = _tender_security_required(tds)
	security_mode = resolve_tender_security_mode(tds)
	instantiated_sections: list[dict[str, Any]] = []
	for sec in copy.deepcopy(template.get("sections") or []):
		if not isinstance(sec, dict):
			continue
		key = cstr(sec.get("section_key") or "")
		applicable = resolve_section_applicability(sec, tds=tds, cfg=cfg)
		if not applicable:
			continue
		sec["applicable"] = True
		sec["not_applicable"] = False

		if key == "tender_documents_and_addenda":
			tender_owned_docs: dict[str, Any] = {}
			for slot in sec.get("tender_owned_slots") or []:
				if not isinstance(slot, dict):
					continue
				fk = cstr(slot.get("field_key") or "")
				binding = cstr(slot.get("binding") or "")
				tender_owned_docs[fk] = _resolve_slot_value(binding, ctx=ctx)
			sec["tender_owned_values"] = tender_owned_docs

		if key == "tender_security":
			tender_owned_sec: dict[str, Any] = {}
			for slot in sec.get("tender_owned_slots") or []:
				if not isinstance(slot, dict):
					continue
				fk = cstr(slot.get("field_key") or "")
				binding = cstr(slot.get("binding") or "")
				tender_owned_sec[fk] = _resolve_slot_value(binding, ctx=ctx)
			sec["tender_owned_values"] = tender_owned_sec
			sec["security_mode"] = security_mode
			if security_mode == "securing_declaration":
				sec["title"] = "Tender-Securing Declaration"
			elif security_mode == "instrument":
				sec["title"] = "Tender Security"

		if key == "form_of_tender":
			tender_owned: dict[str, Any] = {}
			for slot in sec.get("tender_owned_slots") or []:
				if not isinstance(slot, dict):
					continue
				fk = cstr(slot.get("field_key") or "")
				binding = cstr(slot.get("binding") or "")
				val = _resolve_slot_value(binding, ctx=ctx)
				tender_owned[fk] = val
			sec["tender_owned_values"] = tender_owned
			sec["price_summary"] = price_summary
			perf_required = bool(ctx["contract"].get("performance_security"))
			for d in sec.get("declarations") or []:
				if not isinstance(d, dict):
					continue
				cond = d.get("condition")
				if cond == "tender_security_required":
					d["applicable"] = security_required
					d["required"] = security_required
				elif cond == "performance_security_required":
					d["applicable"] = perf_required
					d["required"] = perf_required
				else:
					d["applicable"] = True

		if key == "preliminary_requirements_and_evidence":
			sec["criteria"] = materialize_preliminary_criteria(
				criteria if isinstance(criteria, list) else []
			)

		if key == "qualification_and_capability":
			ev_dict = evaluation if isinstance(evaluation, dict) else {}
			sec["categories"] = materialize_qualification_categories(ev_dict)

		if key == "technical_proposal_and_implementation_plan":
			ev_dict = evaluation if isinstance(evaluation, dict) else {}
			sec["subsections"] = materialize_technical_proposal_subsections(ev_dict)
			flags = ev_dict.get("technical_proposal_flags")
			if isinstance(flags, dict):
				sec["technical_proposal_flags"] = flags
			sec["slice_status"] = "technical_proposal_implemented"

		if key == "requirements_compliance":
			ev_dict = evaluation if isinstance(evaluation, dict) else {}
			rc_rows, rc_fields, rc_flags = materialize_requirements_compliance(
				ev_dict, requirements if isinstance(requirements, list) else []
			)
			# Active matrix excludes withdrawn/excluded rows from display list.
			active = [
				r
				for r in rc_rows
				if cstr(r.get("requirement_mode")) != "excluded" and not r.get("withdrawn")
			]
			sec["requirements"] = active
			sec["requirements_history"] = rc_rows
			sec["response_fields_per_requirement"] = rc_fields
			sec["section_type"] = "requirement_matrix"
			sec["requirements_compliance_flags"] = rc_flags
			sec["slice_status"] = "requirements_compliance_implemented"
			sec["bidder_instructions"] = cstr(
				sec.get("bidder_instructions")
				or "Respond to each applicable requirement and provide the requested supporting evidence."
			)

		instantiated_sections.append(sec)

	max_score = evaluation.get("technical_scoring_total") if isinstance(evaluation, dict) else None
	threshold = evaluation.get("technical_pass_mark") if isinstance(evaluation, dict) else None
	try:
		max_score_n = int(flt(max_score)) if max_score not in (None, "") else None
	except (TypeError, ValueError):
		max_score_n = None
	try:
		threshold_n = int(flt(threshold)) if threshold not in (None, "") else None
	except (TypeError, ValueError):
		threshold_n = None

	by_key = {cstr(s.get("section_key")): s for s in instantiated_sections}
	ordered = [by_key[k] for k in CANONICAL_SECTION_KEYS if k in by_key]
	if not ordered:
		_throw(
			"Instantiated snapshot contains no applicable sections.",
			title="KT_ELECTRONIC_TEMPLATE_SECTIONS",
		)
	section_keys = [cstr(s.get("section_key")) for s in ordered]

	# Prefer lean-materialized RC rows for collections when present.
	rc_pub = by_key.get("requirements_compliance") or {}
	rc_active = rc_pub.get("requirements") if isinstance(rc_pub, dict) else None
	if isinstance(rc_active, list) and rc_active:
		requirements = list(rc_active)
		groups = {
			cstr(r.get("category_label") or r.get("group") or "General")
			for r in requirements
			if isinstance(r, dict)
		}

	calibration_counts = {
		"sections": len(ordered),
		"section_keys": section_keys,
		"has_lot_and_alternative_selection": "lot_and_alternative_selection" in section_keys,
		"has_tender_security_section": "tender_security" in section_keys,
		"requirement_groups": len(groups),
		"requirements": len(requirements),
		"preliminary_criteria": prelim,
		"qualification_criteria": qual_count if qual_count else tech_pass,
		"technical_scoring_criteria": tech_scored,
		"technical_scoring_total": max_score_n,
		"technical_pass_mark": threshold_n,
		"schedule_rows": len(schedule),
		"price_lines": len(price_lines),
		"scc_values": sum(
			1 for v in contract_vals if cstr(v.get("contract_value_id") or "").startswith("SCC-")
		)
		or len(contract_vals),
		"controlled_decisions": len(decisions),
	}

	snapshot = {
		"template_id": TEMPLATE_ID_PPRA_IT_STD,
		"template_version": TEMPLATE_VERSION_V1,
		"template_file_hash": bundle["template_file_hash"],
		"approval_status": cstr(approval.get("status")),
		"approved_by": cstr(approval.get("approved_by")),
		"approved_at": cstr(approval.get("approved_at")),
		"configuration_id": cfg.name,
		"configuration_ref": cstr(cfg.configuration_ref or cfg.name),
		"confirmed_package": pkg.name,
		"document_hash": cstr(pkg.document_hash or ""),
		"std_version": cstr(getattr(pkg, "std_version", None) or cfg.std_version or ""),
		"tender_title": tender_title,
		"procuring_entity_name": entity,
		"sections": ordered,
		"collections": {
			"requirements": requirements,
			"requirement_groups": sorted(groups),
			"evaluation_criteria": criteria,
			"schedule_rows": schedule,
			"price_lines": price_lines,
			"contract_values": contract_vals,
			"controlled_decisions": decisions,
		},
		"calibration_counts": calibration_counts,
		"observed_collection_counts": dict(calibration_counts),
		"submission_policy": {
			"channel": "electronic_only",
			"review_submit_locked_in_slice": True,
		},
	}

	digest = _canonical_hash(snapshot)
	return {
		"snapshot": snapshot,
		"hash": digest,
		"template_id": TEMPLATE_ID_PPRA_IT_STD,
		"template_version": TEMPLATE_VERSION_V1,
	}


def get_published_electronic_template(publication_ref_or_id: str) -> dict[str, Any]:
	"""Load immutable snapshot from a Published IT Tender Publication Record."""
	ref = cstr(publication_ref_or_id or "").strip()
	if not ref:
		_throw("Publication reference is required.", title="KT_ELECTRONIC_TEMPLATE_PUBLICATION")

	name = None
	if frappe.db.exists("IT Tender Publication Record", ref):
		name = ref
	else:
		name = frappe.db.get_value(
			"IT Tender Publication Record", {"publication_ref": ref}, "name"
		)
	if not name:
		_throw("Publication record not found.", title="KT_ELECTRONIC_TEMPLATE_PUBLICATION")

	pub = frappe.get_doc("IT Tender Publication Record", name)
	if cstr(pub.status) != "Published":
		_throw(
			"Electronic template snapshot is only available for Published tenders.",
			title="KT_ELECTRONIC_TEMPLATE_PUBLICATION",
		)
	snapshot = _parse_json(getattr(pub, "electronic_template_snapshot", None), {})
	if not snapshot.get("sections"):
		_throw(
			"Published tender is missing electronic_template_snapshot.",
			title="KT_ELECTRONIC_TEMPLATE_SNAPSHOT_MISSING",
		)
	cfg_id = cstr(pub.configuration or "")
	# Recover pubs sealed before Technical Proposal subsections were materialized.
	if heal_technical_proposal_subsections_in_snapshot(snapshot, configuration_id=cfg_id):
		digest = _canonical_hash(snapshot)
		frappe.db.set_value(
			"IT Tender Publication Record",
			pub.name,
			{
				"electronic_template_snapshot": json.dumps(snapshot, ensure_ascii=False),
				"electronic_template_hash": digest,
			},
			update_modified=False,
		)
		frappe.db.commit()
		pub.electronic_template_hash = digest
	return {
		"publication_id": pub.name,
		"publication_ref": cstr(pub.publication_ref or ""),
		"configuration_id": cfg_id,
		"template_id": cstr(getattr(pub, "electronic_template_id", None) or snapshot.get("template_id")),
		"template_version": cstr(
			getattr(pub, "electronic_template_version", None) or snapshot.get("template_version")
		),
		"hash": cstr(getattr(pub, "electronic_template_hash", None) or ""),
		"publication_version": int(getattr(pub, "publication_version", None) or 1),
		"snapshot": snapshot,
	}


def _stamp_electronic_template(pub, built: dict[str, Any]) -> dict[str, Any]:
	pub.electronic_template_id = built["template_id"]
	pub.electronic_template_version = built["template_version"]
	pub.electronic_template_snapshot = json.dumps(built["snapshot"], ensure_ascii=False)
	pub.electronic_template_hash = built["hash"]
	if not getattr(pub, "publication_version", None):
		pub.publication_version = 1
	return built


def seal_electronic_template_on_publication(pub) -> dict[str, Any]:
	"""Build and stamp snapshot/hash for ordinary publication (Approved template only)."""
	try:
		assert_approved_for_ordinary_publication()
	except TemplateValidationError:
		_throw(
			"Only an Approved electronic STD template may be published.",
			title="KT_ELECTRONIC_TEMPLATE_UNAPPROVED",
		)
	built = build_electronic_submission_template(cstr(pub.configuration), require_approved=True)
	return _stamp_electronic_template(pub, built)


def seal_electronic_template_for_development_preview(publication_id: str) -> dict[str, Any]:
	"""Administrator-only seal allowing Draft/Reviewed template for section/checklist tests.

	Writes the same immutable snapshot/hash fields as ordinary seal. Does not change
	publication status — callers that need a Published record should use
	``publish_tender_for_development_preview``.
	"""
	if frappe.session.user != "Administrator":
		frappe.throw(
			frappe._("Development-preview electronic template seal is Administrator-only."),
			frappe.PermissionError,
		)
	publication_id = cstr(publication_id or "").strip()
	if not publication_id or not frappe.db.exists("IT Tender Publication Record", publication_id):
		_throw("Publication record not found.", title="KT_ELECTRONIC_TEMPLATE_PUBLICATION")
	pub = frappe.get_doc("IT Tender Publication Record", publication_id)
	approval = load_validated_template()["approval"]
	status = cstr(approval.get("status") or "")
	if status not in ("Draft", "Reviewed", "Approved"):
		_throw(
			f"Development preview cannot seal template in status {status!r}.",
			title="KT_ELECTRONIC_TEMPLATE_UNAPPROVED",
		)
	built = build_electronic_submission_template(cstr(pub.configuration), require_approved=False)
	pub.flags.ignore_publication_boundary = True
	pub.flags.ignore_publication_lock = True
	_stamp_electronic_template(pub, built)
	pub.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"publication_id": pub.name,
		"electronic_template_hash": built["hash"],
		"template_id": built["template_id"],
		"template_version": built["template_version"],
		"approval_status": status,
		"development_preview": True,
		"calibration_counts": (built["snapshot"] or {}).get("calibration_counts") or {},
	}
