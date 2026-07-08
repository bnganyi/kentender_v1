# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0230 — STD Version Configurator section service.

Reads and writes ``package_json.std_config`` sections on ``STD Template`` rows while
respecting governance lifecycle gates (``CONTROLLED_REPLACEMENT_STATES`` / ``PROTECTED_STATES``).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_config_legacy_projection import (
	effective_std_config,
	effective_std_config_section,
)
from kentender_procurement.tender_management.services.std_config_section_schema import (
	evaluate_applicability,
	expand_section,
	normalize_section,
	section_default,
)
from kentender_procurement.tender_management.services.std_library_package_projection import (
	resolve_template_title,
)
from kentender_procurement.tender_management.services.std_template_governance_lifecycle import (
	activate_std_template,
	submit_std_template_for_approval,
)

STD_CONFIG_SECTIONS: tuple[str, ...] = (
	"metadata",
	"applicability",
	"tender_fields",
	"supplier_requirements",
	"forms_and_attachments",
	"evaluation_setup",
	"contract_terms",
	"rules",
	"validations",
	"ui_schema",
	"output_mappings",
)

TAB_SLUGS: dict[str, str | tuple[str, ...]] = {
	"overview": "metadata",
	"applicability": "applicability",
	"tender-fields": "tender_fields",
	"supplier-requirements": "supplier_requirements",
	"forms-attachments": "forms_and_attachments",
	"evaluation-setup": "evaluation_setup",
	"contract-terms": "contract_terms",
	"rules-validations": ("rules", "validations"),
	"preview": "preview",
	"approval": "approval",
	"technical-json": "technical_json",
}

_TAB_LABELS: dict[str, str] = {
	"overview": "Overview",
	"applicability": "Applicability",
	"tender-fields": "Tender Fields",
	"supplier-requirements": "Supplier Requirements",
	"forms-attachments": "Forms & Attachments",
	"evaluation-setup": "Evaluation Setup",
	"contract-terms": "Contract Terms",
	"rules-validations": "Rules & Validations",
	"preview": "Preview",
	"approval": "Approval",
	"technical-json": "Technical JSON",
}

from kentender_procurement.tender_management.services.std_config_roles import (
	STD_CONFIGURATOR_WRITE_ROLES,
	can_edit_technical_json_config,
	can_view_technical_json,
)

_CONFIGURATOR_READ_ROLES: frozenset[str] = frozenset(
	{
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Importer",
		"STD Template Reviewer",
		"STD Template Approver",
		"STD Template Activator",
		"STD Template Auditor",
		"STD Technical Inspector",
	}
)

_CONFIGURATOR_WRITE_ROLES = STD_CONFIGURATOR_WRITE_ROLES


def _guest_blocked() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _has_any_role(roles: frozenset[str]) -> bool:
	return bool(roles.intersection(frappe.get_roles()))


def _assert_read_access() -> None:
	_guest_blocked()
	if frappe.session.user == "Administrator":
		return
	if _has_any_role(_CONFIGURATOR_READ_ROLES):
		return
	frappe.throw(_("Not permitted"), frappe.PermissionError)


def _assert_write_access() -> None:
	_guest_blocked()
	if frappe.session.user == "Administrator":
		return
	if _has_any_role(_CONFIGURATOR_WRITE_ROLES):
		return
	frappe.throw(_("Not permitted"), frappe.PermissionError)


def _assert_technical_json_access() -> None:
	_guest_blocked()
	if not can_view_technical_json():
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _normalize_template_code(template_code: str) -> str:
	code = (template_code or "").strip()
	if not code:
		frappe.throw(_("Template code is required."), frappe.ValidationError)
	return code


def _assert_known_section(section: str) -> str:
	key = (section or "").strip()
	if key not in STD_CONFIG_SECTIONS:
		frappe.throw(_("Unknown std_config section: {0}").format(section), frappe.ValidationError)
	return key


def resolve_template_by_code(template_code: str) -> str:
	"""Return ``STD Template`` document name for ``template_code``."""
	code = _normalize_template_code(template_code)
	name = frappe.db.get_value("STD Template", {"template_code": code}, "name")
	if not name:
		frappe.throw(_("STD Template not found for code {0}.").format(code), frappe.DoesNotExistError)
	return str(name)


def _load_doc(template_code: str) -> Any:
	name = resolve_template_by_code(template_code)
	return frappe.get_doc("STD Template", name)


def _parse_package_json(doc: Any) -> dict[str, Any]:
	raw = doc.get("package_json") or "{}"
	try:
		parsed: Any = json.loads(raw)
	except json.JSONDecodeError as exc:
		frappe.throw(_("Invalid package_json: {0}").format(str(exc)), frappe.ValidationError)
	if not isinstance(parsed, dict):
		frappe.throw(_("package_json must be a JSON object."), frappe.ValidationError)
	return parsed


def _ensure_std_config(package: dict[str, Any]) -> dict[str, Any]:
	std_config = package.setdefault("std_config", {})
	if not isinstance(std_config, dict):
		frappe.throw(_("package_json.std_config must be a JSON object."), frappe.ValidationError)
	return std_config


def _section_default(section: str) -> dict[str, Any]:
	return section_default(section)


def _coerce_section_data(section: str, data: Any) -> dict[str, Any]:
	if data is None:
		return _section_default(section)
	if isinstance(data, str):
		try:
			data = json.loads(data)
		except json.JSONDecodeError as exc:
			frappe.throw(_("Section data is not valid JSON: {0}").format(str(exc)), frappe.ValidationError)
	if not isinstance(data, dict):
		frappe.throw(_("Section data must be a JSON object."), frappe.ValidationError)
	return data


def _is_editable(doc: Any) -> bool:
	return (doc.get("lifecycle_status") or "") in gov.CONTROLLED_REPLACEMENT_STATES


def assert_can_edit(doc: Any) -> None:
	"""Raise when lifecycle is in a protected (non-editable) state."""
	status = doc.get("lifecycle_status") or ""
	if status in gov.PROTECTED_STATES:
		frappe.throw(
			_("STD Template cannot be edited in lifecycle status {0}.").format(status),
			frappe.ValidationError,
		)


def _assert_can_save_section(doc: Any) -> None:
	assert_can_edit(doc)
	if not _is_editable(doc):
		frappe.throw(
			_("Section save is not allowed in lifecycle status {0}.").format(doc.lifecycle_status),
			frappe.ValidationError,
		)


def _summarize_section(section: str, data: Any) -> dict[str, Any]:
	if not isinstance(data, dict):
		return {"present": data is not None, "count": 0}
	out: dict[str, Any] = {"present": bool(data)}
	if section == "metadata":
		out["title"] = str(data.get("title") or "").strip()
	elif section in {"applicability"}:
		out["count"] = len(data.get("rules") or [])
	elif section == "tender_fields":
		out["count"] = len(data.get("fields") or [])
	elif section == "supplier_requirements":
		out["count"] = len(data.get("requirements") or [])
	elif section == "forms_and_attachments":
		out["count"] = len(data.get("forms") or [])
	elif section == "evaluation_setup":
		out["count"] = len(data.get("criteria") or [])
	elif section == "contract_terms":
		out["count"] = len(data.get("terms") or [])
	elif section == "rules":
		out["count"] = len(data.get("rules") or [])
	elif section == "validations":
		out["count"] = len(data.get("validations") or [])
	elif section == "output_mappings":
		out["count"] = len(data.get("mappings") or [])
	else:
		out["count"] = len(data)
	return out


def _coerce_package_json(data: Any) -> dict[str, Any]:
	if data is None:
		frappe.throw(_("Package JSON is required."), frappe.ValidationError)
	if isinstance(data, str):
		try:
			data = json.loads(data)
		except json.JSONDecodeError as exc:
			frappe.throw(_("Package JSON is not valid JSON: {0}").format(str(exc)), frappe.ValidationError)
	if not isinstance(data, dict):
		frappe.throw(_("package_json must be a JSON object."), frappe.ValidationError)
	return data


def _normalize_std_config_sections(package: dict[str, Any]) -> None:
	std_config = _ensure_std_config(package)
	for section in STD_CONFIG_SECTIONS:
		raw = std_config.get(section)
		if raw is None:
			continue
		if not isinstance(raw, dict):
			frappe.throw(_("Section {0} must be stored as a JSON object.").format(section), frappe.ValidationError)
		std_config[section] = normalize_section(section, raw)
	package["std_config"] = std_config


def _technical_json_editable(doc: Any) -> bool:
	return _is_editable(doc) and can_edit_technical_json_config()


def _build_tabs(editable: bool) -> list[dict[str, Any]]:
	tabs: list[dict[str, Any]] = []
	tech_editable = editable and can_edit_technical_json_config()
	for slug, mapping in TAB_SLUGS.items():
		sections: list[str]
		if isinstance(mapping, tuple):
			sections = list(mapping)
		elif mapping in STD_CONFIG_SECTIONS:
			sections = [mapping]
		else:
			sections = []
		read_only_slugs = {"preview", "approval"}
		if slug == "technical-json":
			read_only = not tech_editable
		else:
			read_only = slug in read_only_slugs
		tabs.append(
			{
				"slug": slug,
				"label": _TAB_LABELS.get(slug, slug),
				"sections": sections,
				"editable": editable if sections else False,
				"read_only": read_only,
			}
		)
	return tabs


def get_configurator_context(template_code: str) -> dict[str, Any]:
	"""Return configurator shell context for a template version."""
	_assert_read_access()
	doc = _load_doc(template_code)
	package = _parse_package_json(doc)
	std_config = effective_std_config(package, doc)
	editable = _is_editable(doc)
	summary = {section: _summarize_section(section, std_config.get(section)) for section in STD_CONFIG_SECTIONS}
	metadata = std_config.get("metadata") if isinstance(std_config.get("metadata"), dict) else {}
	title = (
		str(metadata.get("title") or "").strip()
		or str(doc.template_title or doc.template_name or resolve_template_title(doc, package) or doc.template_code)
	)
	return {
		"ok": True,
		"template_code": doc.template_code,
		"template_name": doc.template_name,
		"title": title,
		"lifecycle_status": doc.lifecycle_status,
		"editable": editable,
		"can_view_technical_json": can_view_technical_json(),
		"can_edit_technical_json": _technical_json_editable(doc),
		"tabs": _build_tabs(editable),
		"std_config": summary,
	}


def get_section(template_code: str, section: str) -> dict[str, Any]:
	"""Return one ``std_config`` section payload."""
	_assert_read_access()
	key = _assert_known_section(section)
	doc = _load_doc(template_code)
	package = _parse_package_json(doc)
	data = effective_std_config_section(package, key, doc)
	if not isinstance(data, dict):
		frappe.throw(_("Section {0} must be stored as a JSON object.").format(key), frappe.ValidationError)
	expanded = expand_section(key, data)
	return {
		"ok": True,
		"template_code": doc.template_code,
		"section": key,
		"data": expanded,
		"editable": _is_editable(doc),
	}


def save_section(template_code: str, section: str, data: Any) -> dict[str, Any]:
	"""Merge section data into ``package_json.std_config`` and persist."""
	_assert_write_access()
	key = _assert_known_section(section)
	doc = _load_doc(template_code)
	_assert_can_save_section(doc)
	payload = normalize_section(key, _coerce_section_data(key, data))

	package = _parse_package_json(doc)
	std_config = _ensure_std_config(package)
	std_config[key] = payload
	package["std_config"] = std_config

	doc.flags.skip_std_template_guards = True
	doc.package_json = json.dumps(package, indent=2, ensure_ascii=False)
	doc.package_hash = gov.compute_std_package_hash(package)
	if int(doc.get("validation_is_current") or 0):
		doc.validation_is_current = 0
	doc.save(ignore_permissions=True)

	return {
		"ok": True,
		"template_code": doc.template_code,
		"section": key,
		"data": payload,
		"package_hash": doc.package_hash,
		"editable": _is_editable(doc),
	}


def get_technical_json(template_code: str) -> dict[str, Any]:
	"""Return full ``package_json`` for advanced / technical inspection (role gated)."""
	_assert_technical_json_access()
	doc = _load_doc(template_code)
	package = _parse_package_json(doc)
	editable = _technical_json_editable(doc)
	return {
		"ok": True,
		"template_code": doc.template_code,
		"package_json": package,
		"package_hash": doc.package_hash,
		"read_only": not editable,
		"editable": editable,
	}


def save_technical_json(template_code: str, package_json: Any) -> dict[str, Any]:
	"""Persist full ``package_json`` for privileged technical editing."""
	_assert_write_access()
	_assert_technical_json_access()
	doc = _load_doc(template_code)
	_assert_can_save_section(doc)
	package = _coerce_package_json(package_json)
	_normalize_std_config_sections(package)

	doc.flags.skip_std_template_guards = True
	doc.package_json = json.dumps(package, indent=2, ensure_ascii=False)
	doc.package_hash = gov.compute_std_package_hash(package)
	if int(doc.get("validation_is_current") or 0):
		doc.validation_is_current = 0
	doc.save(ignore_permissions=True)

	return {
		"ok": True,
		"template_code": doc.template_code,
		"package_json": package,
		"package_hash": doc.package_hash,
		"editable": _technical_json_editable(doc),
	}


def get_preview(template_code: str, mode: str | None = None) -> dict[str, Any]:
	"""Read-only preview derived from ``std_config`` sections."""
	_assert_read_access()
	doc = _load_doc(template_code)
	package = _parse_package_json(doc)
	std_config = effective_std_config(package, doc)
	preview_mode = (mode or "summary").strip().lower() or "summary"

	metadata = std_config.get("metadata") if isinstance(std_config.get("metadata"), dict) else {}
	forms = []
	forms_root = std_config.get("forms_and_attachments")
	if isinstance(forms_root, dict):
		forms = list(forms_root.get("forms") or [])
	requirements = []
	req_root = std_config.get("supplier_requirements")
	if isinstance(req_root, dict):
		requirements = list(req_root.get("requirements") or [])

	outline = [str(f.get("label") or f.get("name") or "") for f in forms if isinstance(f, dict)]
	outline = [x for x in outline if x]

	body: dict[str, Any] = {
		"mode": preview_mode,
		"title": str(metadata.get("title") or doc.template_title or doc.template_name or doc.template_code),
		"description": str(metadata.get("description") or ""),
		"form_count": len(forms),
		"requirement_count": len(requirements),
		"outline": outline,
		"read_only": True,
	}
	if preview_mode == "structure":
		body["sections"] = [
			{"key": section, "summary": _summarize_section(section, std_config.get(section))}
			for section in STD_CONFIG_SECTIONS
		]
	elif preview_mode == "raw":
		body["std_config"] = std_config
	return {
		"ok": True,
		"template_code": doc.template_code,
		"lifecycle_status": doc.lifecycle_status,
		"preview": body,
	}


def _requirement_keys(requirements: list[Any]) -> set[str]:
	keys: set[str] = set()
	for row in requirements:
		if not isinstance(row, dict):
			continue
		for field in ("id", "code", "name", "requirement_id", "requirement_code"):
			val = str(row.get(field) or "").strip()
			if val:
				keys.add(val)
	return keys


def run_cross_section_validation(template_code: str) -> dict[str, Any]:
	"""Validate cross-links between ``std_config`` sections (forms ↔ requirements, etc.)."""
	_assert_read_access()
	doc = _load_doc(template_code)
	package = _parse_package_json(doc)
	std_config = effective_std_config(package, doc)

	issues: list[dict[str, Any]] = []
	req_root = std_config.get("supplier_requirements")
	requirements = list(req_root.get("requirements") or []) if isinstance(req_root, dict) else []
	req_keys = _requirement_keys(requirements)

	forms_root = std_config.get("forms_and_attachments")
	forms = list(forms_root.get("forms") or []) if isinstance(forms_root, dict) else []
	for idx, form in enumerate(forms):
		if not isinstance(form, dict):
			continue
		ref = str(
			form.get("requirement_id")
			or form.get("requirement_code")
			or form.get("linked_requirement")
			or ""
		).strip()
		if ref and ref not in req_keys:
			issues.append(
				{
					"code": "FORM_REQUIREMENT_LINK_MISSING",
					"severity": "Warning",
					"section": "forms_and_attachments",
					"message": _("Form row {0} references unknown requirement {1}.").format(idx + 1, ref),
					"source_path": f"std_config.forms_and_attachments.forms[{idx}]",
				}
			)

	mappings_root = std_config.get("output_mappings")
	mappings = list(mappings_root.get("mappings") or []) if isinstance(mappings_root, dict) else []
	field_root = std_config.get("tender_fields")
	fields = list(field_root.get("fields") or []) if isinstance(field_root, dict) else []
	field_keys = _requirement_keys(fields)
	for idx, mapping in enumerate(mappings):
		if not isinstance(mapping, dict):
			continue
		source = str(mapping.get("source_field") or mapping.get("source") or "").strip()
		if source and field_keys and source not in field_keys:
			issues.append(
				{
					"code": "OUTPUT_MAPPING_SOURCE_MISSING",
					"severity": "Warning",
					"section": "output_mappings",
					"message": _("Mapping row {0} references unknown tender field {1}.").format(idx + 1, source),
					"source_path": f"std_config.output_mappings.mappings[{idx}]",
				}
			)

	return {
		"ok": True,
		"template_code": doc.template_code,
		"passed": len(issues) == 0,
		"issue_count": len(issues),
		"issues": issues,
	}


def run_applicability_test(template_code: str, test_case: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Evaluate applicability rules against a test package (simulator tab)."""
	_assert_read_access()
	section = get_section(template_code, "applicability")
	data = section.get("data") or {}
	result = evaluate_applicability(data, test_case)
	return {
		"ok": True,
		"template_code": template_code,
		"applies": result.get("applies"),
		"result": result,
	}


def submit_configurator_for_review(template_code: str, comment: str | None = None) -> dict[str, Any]:
	"""Delegate approval submission to governance lifecycle."""
	_assert_write_access()
	name = resolve_template_by_code(template_code)
	return submit_std_template_for_approval(name, comment)


def activate_configurator_version(
	template_code: str,
	reason: str,
	active_from: str | None = None,
	active_until: str | None = None,
	is_default_active_version: bool = True,
) -> dict[str, Any]:
	"""Delegate activation to governance lifecycle."""
	name = resolve_template_by_code(template_code)
	return activate_std_template(
		name,
		reason,
		active_from=active_from,
		active_until=active_until,
		is_default_active_version=is_default_active_version,
	)
