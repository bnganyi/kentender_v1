"""STD-CURSOR-1301 — cross-object evidence export package service."""

from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)
from kentender_procurement.std_engine.services.audit_service import (
	AUDIT_READ_ROLES,
	record_std_audit_event,
)
from kentender_procurement.std_engine.services.template_version_audit_evidence_service import (
	build_std_template_version_audit_evidence,
)


def _normalize_object_type(object_type: str) -> str:
	ot = str(object_type or "").strip().lower()
	if ot in {"template version", "template_version", "std template version"}:
		return "Template Version"
	if ot in {"std instance", "instance", "std_instance"}:
		return "STD Instance"
	return ""


def _audit_object_type_token(normalized_type: str) -> str:
	return "TEMPLATE_VERSION" if normalized_type == "Template Version" else "STD_INSTANCE"


def _user_can_export(user: str) -> bool:
	return bool(set(frappe.get_roles(user)) & set(AUDIT_READ_ROLES))


def _serialize_json(value: Any) -> str:
	try:
		return json.dumps(value, sort_keys=True, ensure_ascii=True)
	except Exception:
		return ""


def _safe_get_meta(doctype: str):
	if not frappe.db.table_exists(doctype):
		return None
	try:
		return frappe.get_meta(doctype)
	except Exception:
		return None


def _safe_get_doc_fields(doctype: str, name: str, candidates: list[str]) -> dict[str, Any]:
	meta = _safe_get_meta(doctype)
	if not meta:
		return {}
	fnames = [f for f in candidates if meta.has_field(f) or f == "name"]
	if not fnames:
		return {}
	row = frappe.db.get_value(doctype, name, fnames, as_dict=True) or {}
	return dict(row)


def _safe_get_all(
	doctype: str,
	filters: dict[str, Any],
	fields: list[str],
	order_by: str | None = None,
	limit: int = 200,
) -> list[dict[str, Any]]:
	meta = _safe_get_meta(doctype)
	if not meta:
		return []
	for key in filters.keys():
		if key != "name" and not meta.has_field(key):
			return []
	fnames = [f for f in fields if f == "name" or meta.has_field(f)]
	if not fnames:
		fnames = ["name"]
	return frappe.get_all(
		doctype,
		filters=filters,
		fields=fnames,
		order_by=order_by or "modified desc",
		limit=limit,
	)


def _build_template_version_package(version_code: str, user: str) -> dict[str, Any]:
	resolved = resolve_std_document("Template Version", version_code)
	if not resolved:
		return {"ok": False, "error": "not_found", "message": str(_("No document matches this version code."))}
	doctype, name, _doc = resolved
	if doctype != "STD Template Version" or not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	tv = _safe_get_doc_fields(
		"STD Template Version",
		name,
		[
			"name",
			"version_code",
			"template_code",
			"version_label",
			"version_status",
			"source_document_code",
			"procurement_category",
			"works_profile_type",
			"legal_review_status",
			"policy_review_status",
			"structure_validation_status",
			"is_current_active_version",
		],
	)
	template_code = str(tv.get("template_code") or "")
	tf_name = frappe.db.get_value("STD Template Family", {"template_code": template_code}, "name")
	tf = (
		_safe_get_doc_fields(
			"STD Template Family",
			tf_name,
			["name", "template_code", "template_title", "family_status", "issuing_authority", "procurement_category"],
		)
		if tf_name
		else {}
	)
	source_code = str(tv.get("source_document_code") or "")
	sdr_name = frappe.db.get_value("Source Document Registry", {"source_document_code": source_code}, "name")
	source = (
		_safe_get_doc_fields(
			"Source Document Registry",
			sdr_name,
			[
				"name",
				"source_document_code",
				"source_document_title",
				"issuing_authority",
				"source_revision_label",
				"source_hash",
				"status",
			],
		)
		if sdr_name
		else {}
	)
	profiles = _safe_get_all(
		"STD Applicability Profile",
		{"version_code": version_code},
		["profile_code", "profile_title", "profile_status", "works_profile_type", "allowed_methods"],
		order_by="modified desc",
		limit=120,
	)
	sections = _safe_get_all(
		"STD Section Definition",
		{"version_code": version_code},
		["section_code", "part_code", "section_number", "section_title", "source_document_code", "editability"],
		order_by="order_index asc, modified asc",
		limit=800,
	)
	clauses = _safe_get_all(
		"STD Clause Definition",
		{"version_code": version_code},
		["clause_code", "section_code", "clause_number", "clause_title", "source_hash", "is_locked"],
		order_by="order_index asc, modified asc",
		limit=2000,
	)
	audit = build_std_template_version_audit_evidence(version_code, actor=user)
	return {
		"ok": True,
		"object_type": "Template Version",
		"object_code": version_code,
		"source_document_reference": source,
		"template_family": tf,
		"template_version": tv,
		"applicability_profiles": profiles,
		"sections": sections,
		"clauses_source_hashes": clauses,
		"audit_events": (audit.get("lifecycle_timeline") or []) if audit.get("ok") else [],
	}


def _build_instance_package(instance_code: str, user: str) -> dict[str, Any]:
	resolved = resolve_std_document("STD Instance", instance_code)
	if not resolved:
		return {"ok": False, "error": "not_found", "message": str(_("No document matches this instance code."))}
	doctype, name, _inst = resolved
	if doctype != "STD Instance" or not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	inst = _safe_get_doc_fields(
		"STD Instance",
		name,
		[
			"name",
			"instance_code",
			"tender_code",
			"template_version_code",
			"profile_code",
			"instance_status",
			"readiness_status",
			"published_on",
		],
	)
	version_code = str(inst.get("template_version_code") or "")
	template_pkg = _build_template_version_package(version_code, user) if version_code else {"ok": False}
	source = template_pkg.get("source_document_reference") if template_pkg.get("ok") else {}
	family = template_pkg.get("template_family") if template_pkg.get("ok") else {}
	template = template_pkg.get("template_version") if template_pkg.get("ok") else {}
	profiles = template_pkg.get("applicability_profiles") if template_pkg.get("ok") else []
	selected_profile = next((p for p in profiles if str(p.get("profile_code") or "") == str(inst.get("profile_code") or "")), {})
	sections = template_pkg.get("sections") if template_pkg.get("ok") else []
	clauses = template_pkg.get("clauses_source_hashes") if template_pkg.get("ok") else []

	params = _safe_get_all(
		"STD Parameter Value",
		{"instance_code": instance_code},
		["parameter_code", "value_text", "value_number", "value_boolean", "is_current", "modified"],
		order_by="modified desc",
		limit=1200,
	)
	works = _safe_get_all(
		"STD Works Requirement Component",
		{"instance_code": instance_code},
		["component_code", "component_type", "completion_status", "content_text", "modified"],
		order_by="modified desc",
		limit=600,
	)
	boq = _safe_get_all(
		"STD BOQ Instance",
		{"instance_code": instance_code},
		["boq_instance_code", "boq_definition_code", "status", "validation_status", "modified"],
		order_by="modified desc",
		limit=60,
	)
	attachments = _safe_get_all(
		"STD Section Attachment",
		{"instance_code": instance_code},
		["attachment_code", "section_code", "attachment_type", "file_url", "file_hash", "modified"],
		order_by="modified desc",
		limit=600,
	)
	outputs = _safe_get_all(
		"STD Generated Output",
		{"instance_code": instance_code},
		["output_code", "output_type", "status", "version_no", "supersedes_output_code", "superseded_by_output_code", "modified"],
		order_by="modified desc",
		limit=600,
	)
	readiness_runs = _safe_get_all(
		"STD Readiness Run",
		{"object_type": "STD_INSTANCE", "object_code": instance_code},
		["readiness_run_code", "status", "run_at", "run_by", "summary_json"],
		order_by="run_at desc",
		limit=300,
	)
	addendum = _safe_get_all(
		"STD Addendum Impact Analysis",
		{"instance_code": instance_code},
		["impact_analysis_code", "addendum_code", "status", "requires_regeneration", "modified"],
		order_by="modified desc",
		limit=300,
	)
	audit = _safe_get_all(
		"STD Audit Event",
		{"object_type": "STD_INSTANCE", "object_code": instance_code},
		[
			"audit_event_code",
			"event_type",
			"object_type",
			"object_code",
			"actor",
			"timestamp",
			"previous_state",
			"new_state",
			"denial_code",
			"reason",
		],
		order_by="timestamp desc",
		limit=2000,
	)
	bindings = _safe_get_all(
		"STD Tender Binding",
		{"instance_code": instance_code},
		["name", "instance_code", "tender_code", "binding_status", "modified"],
		order_by="modified desc",
		limit=60,
	)
	return {
		"ok": True,
		"object_type": "STD Instance",
		"object_code": instance_code,
		"instance_summary": inst,
		"source_document_reference": source,
		"template_family": family,
		"template_version": template,
		"applicability_profile": selected_profile,
		"sections": sections,
		"clauses_source_hashes": clauses,
		"parameters_and_values": params,
		"works_requirements": works,
		"boq_version": boq,
		"section_bound_attachments": attachments,
		"generated_outputs": outputs,
		"generated_bundle": [x for x in outputs if str(x.get("output_type") or "") == "Bundle"],
		"dsm": [x for x in outputs if str(x.get("output_type") or "") == "DSM"],
		"dom": [x for x in outputs if str(x.get("output_type") or "") == "DOM"],
		"dem": [x for x in outputs if str(x.get("output_type") or "") == "DEM"],
		"dcm": [x for x in outputs if str(x.get("output_type") or "") == "DCM"],
		"readiness_runs": readiness_runs,
		"addendum_impact_analyses": addendum,
		"regeneration_supersession_chain": [
			{
				"output_code": o.get("output_code"),
				"output_type": o.get("output_type"),
				"version_no": o.get("version_no"),
				"supersedes_output_code": o.get("supersedes_output_code"),
				"superseded_by_output_code": o.get("superseded_by_output_code"),
			}
			for o in outputs
		],
		"audit_events": audit,
		"downstream_binding_references": bindings,
	}


def _build_export_csv_text(object_type: str, object_code: str, package: dict[str, Any]) -> str:
	buf = StringIO()
	w = csv.writer(buf)
	w.writerow(["section", "key", "value"])
	w.writerow(["metadata", "object_type", object_type])
	w.writerow(["metadata", "object_code", object_code])
	for key in sorted(package.keys()):
		val = package.get(key)
		if isinstance(val, (list, dict)):
			w.writerow(["package", key, _serialize_json(val)])
		else:
			w.writerow(["package", key, str(val or "")])
	return buf.getvalue()


def build_std_evidence_export_package(
	object_type: str,
	object_code: str,
	actor: str | None = None,
) -> dict[str, Any]:
	"""Export role-gated STD evidence package and CSV."""
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}
	if not _user_can_export(user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	normalized = _normalize_object_type(object_type)
	code = str(object_code or "").strip()
	if not normalized or not code:
		return {"ok": False, "error": "invalid", "message": str(_("Object type and code are required."))}

	if normalized == "Template Version":
		pkg = _build_template_version_package(code, user)
	else:
		pkg = _build_instance_package(code, user)
	if not pkg.get("ok"):
		return pkg

	csv_text = _build_export_csv_text(normalized, code, pkg)
	filename = f"std-evidence-{normalized.lower().replace(' ', '-')}-{code.replace('/', '-')}.csv"
	record_std_audit_event(
		"EVIDENCE_EXPORTED",
		_audit_object_type_token(normalized),
		code,
		actor=user,
		reason="Evidence package export",
		metadata={"object_type": normalized, "object_code": code, "rows": csv_text.count("\n")},
	)
	return {
		"ok": True,
		"object_type": normalized,
		"object_code": code,
		"metadata": {
			"generated_at": frappe.utils.now(),
			"generated_by": user,
		},
		"package": pkg,
		"filename": filename,
		"csv_text": csv_text,
	}

