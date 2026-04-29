"""STD workbench: Template Version audit & evidence (STD-CURSOR-1014)."""

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
from kentender_procurement.std_engine.services.audit_service import AUDIT_READ_ROLES

_AUDIT_FIELDS = [
	"audit_event_code",
	"event_type",
	"object_type",
	"object_code",
	"actor",
	"previous_state",
	"new_state",
	"reason",
	"denial_code",
	"metadata",
	"timestamp",
]

_SECTION_ORDER = (
	"general_evidence",
	"template_evidence",
	"source_trace_evidence",
	"configuration_evidence",
	"works_evidence",
	"generation_evidence",
	"readiness_evidence",
	"addendum_evidence",
	"downstream_evidence",
	"denied_events",
)

_DENIAL_TYPES = frozenset({"STD_TRANSITION_DENIED", "PERMISSION_DENIED", "LOCKED_EDIT_DENIED"})


def _to_bool(value) -> bool:
	try:
		return bool(int(value or 0))
	except (TypeError, ValueError):
		return False


def _user_has_audit_export_role(user: str) -> bool:
	return bool(set(frappe.get_roles(user)) & set(AUDIT_READ_ROLES))


def _evidence_bucket(event_type: str) -> str:
	et = (event_type or "").upper()
	if et in _DENIAL_TYPES or "TRANSITION_DENIED" in et:
		return "denied_events"
	if "READINESS" in et:
		return "readiness_evidence"
	if "GENERATION" in et or et.startswith("OUTPUT_") or "OUTPUT_" in et:
		return "generation_evidence"
	if "ADDENDUM" in et:
		return "addendum_evidence"
	if et == "STD_INSTANCE_CREATED" or "INSTANCE" in et:
		return "downstream_evidence"
	if "WORKS" in et or "BOQ" in et or "SECTION_ATTACHMENT" in et:
		return "works_evidence"
	if "PARAMETER" in et or "PROFILE" in et:
		return "configuration_evidence"
	if "SOURCE_DOCUMENT" in et:
		return "source_trace_evidence"
	if "TEMPLATE" in et or "FAMILY" in et:
		return "template_evidence"
	return "general_evidence"


def _normalize_metadata(raw) -> dict[str, Any]:
	if raw is None:
		return {}
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			return json.loads(raw)
		except (TypeError, ValueError):
			return {}
	return {}


def _serialize_row(row: dict[str, Any], *, scrub_sensitive: bool) -> dict[str, Any]:
	out = {
		"audit_event_code": str(row.get("audit_event_code") or ""),
		"event_type": str(row.get("event_type") or ""),
		"object_type": str(row.get("object_type") or ""),
		"object_code": str(row.get("object_code") or ""),
		"actor": str(row.get("actor") or ""),
		"previous_state": str(row.get("previous_state") or ""),
		"new_state": str(row.get("new_state") or ""),
		"timestamp": str(row.get("timestamp") or ""),
	}
	if scrub_sensitive:
		out["reason"] = ""
		out["denial_code"] = ""
		out["metadata"] = {}
	else:
		out["reason"] = str(row.get("reason") or "")
		out["denial_code"] = str(row.get("denial_code") or "")
		out["metadata"] = _normalize_metadata(row.get("metadata"))
	return out


def _gather_raw_events(version_code: str, template_code: str, limit: int = 400) -> list[dict[str, Any]]:
	rows: list[dict[str, Any]] = []
	rows.extend(
		frappe.get_all(
			"STD Audit Event",
			filters={"object_type": "TEMPLATE_VERSION", "object_code": version_code},
			fields=_AUDIT_FIELDS,
			order_by="timestamp desc",
			limit=limit,
		)
	)
	if template_code:
		rows.extend(
			frappe.get_all(
				"STD Audit Event",
				filters={"object_type": "TEMPLATE_FAMILY", "object_code": template_code},
				fields=_AUDIT_FIELDS,
				order_by="timestamp desc",
				limit=min(120, limit),
			)
		)
	instance_codes = frappe.get_all(
		"STD Instance",
		filters={"template_version_code": version_code},
		pluck="instance_code",
	)
	if instance_codes:
		chunk_size = 40
		for i in range(0, len(instance_codes), chunk_size):
			chunk = instance_codes[i : i + chunk_size]
			rows.extend(
				frappe.get_all(
					"STD Audit Event",
					filters={"object_type": "STD_INSTANCE", "object_code": ("in", chunk)},
					fields=_AUDIT_FIELDS,
					order_by="timestamp desc",
					limit=min(200, limit),
				)
			)
	by_code: dict[str, dict[str, Any]] = {}
	for r in rows:
		ac = str(r.get("audit_event_code") or "")
		if ac and ac not in by_code:
			by_code[ac] = r
	merged = list(by_code.values())
	merged.sort(key=lambda x: str(x.get("timestamp") or ""))
	return merged


def build_std_template_version_audit_evidence(version_code: str, actor: str | None = None) -> dict[str, object]:
	"""Aggregate STD Audit Event rows for a template version and derived instances."""
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (version_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Version code is required."))}

	resolved = resolve_std_document("Template Version", code)
	if not resolved:
		return {
			"ok": False,
			"error": "not_found",
			"message": str(_("No document matches this version code.")),
			"version_code": code,
		}
	doctype, name, doc = resolved
	if doctype != "STD Template Version":
		return {"ok": False, "error": "invalid", "message": str(_("Not a template version."))}
	if not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	status = str(doc.get("version_status") or "")
	read_only = status == "Active" and _to_bool(doc.get("immutable_after_activation"))

	template_code = str(doc.get("template_code") or "")
	full_audit = _user_has_audit_export_role(user)
	scrub = not full_audit

	raw = _gather_raw_events(code, template_code)
	if scrub:
		raw = [r for r in raw if _evidence_bucket(str(r.get("event_type") or "")) != "denied_events"]
	serialized = [_serialize_row(r, scrub_sensitive=scrub) for r in raw]

	sections: dict[str, list[dict[str, Any]]] = {k: [] for k in _SECTION_ORDER}
	for ev in serialized:
		bucket = _evidence_bucket(ev.get("event_type") or "")
		if bucket not in sections:
			bucket = "general_evidence"
		if len(sections[bucket]) < 40:
			sections[bucket].append(ev)

	denied = [e for e in serialized if _evidence_bucket(e.get("event_type") or "") == "denied_events"]

	return {
		"ok": True,
		"version_code": code,
		"read_only": read_only,
		"permissions": {
			"can_view_denied_events": full_audit,
			"can_export_evidence": full_audit,
		},
		"privacy_note": str(
			_(
				"Denied events, reasons, and CSV export require Auditor, System Manager, or Administrator role."
			)
		)
		if scrub
		else "",
		"lifecycle_timeline": serialized,
		"evidence_sections": sections,
		"denied_events": denied,
		"event_counts": {
			"total": len(serialized),
			"denied": len([e for e in serialized if _evidence_bucket(e.get("event_type") or "") == "denied_events"]),
		},
	}


def build_std_template_version_audit_export_csv(version_code: str, actor: str | None = None) -> dict[str, object]:
	"""Build CSV export for audit rows (role-gated)."""
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}
	if not _user_has_audit_export_role(user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (version_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Version code is required."))}

	resolved = resolve_std_document("Template Version", code)
	if not resolved:
		return {"ok": False, "error": "not_found", "message": str(_("No document matches this version code."))}
	doctype, name, _doc = resolved
	if doctype != "STD Template Version" or not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	template_code = str(frappe.db.get_value("STD Template Version", name, "template_code") or "")
	raw = _gather_raw_events(code, template_code, limit=2000)
	buf = StringIO()
	w = csv.writer(buf)
	w.writerow(["audit_event_code", "event_type", "object_type", "object_code", "actor", "timestamp", "denial_code", "reason"])
	for r in raw:
		w.writerow(
			[
				r.get("audit_event_code"),
				r.get("event_type"),
				r.get("object_type"),
				r.get("object_code"),
				r.get("actor"),
				r.get("timestamp"),
				r.get("denial_code"),
				(r.get("reason") or "").replace("\n", " ")[:2000],
			]
		)
	filename = f"std-template-version-audit-{code.replace('/', '-')}.csv"
	return {
		"ok": True,
		"version_code": code,
		"filename": filename,
		"csv_text": buf.getvalue(),
	}
