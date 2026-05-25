# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-013 — Planning Evidence timeline read API."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.package_planning_release_display import (
	_tm2_name_and_title,
)
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
)

_AUDIT_FIELDS = [
	"event_code",
	"event_type",
	"object_type",
	"object_code",
	"actor",
	"occurred_at",
	"from_state",
	"to_state",
	"reason",
	"evidence_ref",
	"journey_code",
	"is_master_seed",
]

_LIMITED_ROLES = frozenset(
	(
		"Procurement Officer",
		"Tender Manager",
		"Budget Officer",
	)
)
_TECHNICAL_ROLES = frozenset(
	(
		"Auditor",
		"Planning Authority",
		"Administrator",
		"System Manager",
	)
)
_SENSITIVE_EVENT_TYPES = frozenset(
	(
		"Returned for Correction",
		"Package Returned for Correction",
	)
)

_EVENT_LABELS: dict[str, str] = {
	"Demand Entered Planning Queue": "Demand entered planning queue",
	"Demand Included in Plan": "Demand included in procurement plan",
	"Package Created": "Package prepared",
	"Package Line Created": "Package line created",
	"Method Decision Recorded": "Procurement method decision recorded",
	"Package Submitted for Review": "Package submitted for review",
	"Package Approved": "Package approved",
	"Readiness Check Run": "Readiness checks passed",
	"Package Marked Ready for Release": "Package marked ready for release",
	"Package Released to Tender Management": "Package released to Tender Management",
	"Package Locked After Release": "Package locked after release",
	"Release Consumed by Tender Management": "Tender Management consumed release",
	"Release Returned by Tender Management": "Release returned for correction",
	"Package Superseded": "Package superseded",
	"Package Cancelled": "Package cancelled",
}


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _resolve_package_name(package_code: str) -> str | None:
	code = (package_code or "").strip()
	if not code:
		return None
	if frappe.db.exists("Procurement Package", code):
		return code
	name = frappe.db.get_value("Procurement Package", {"package_code": code}, "name")
	return str(name) if name else None


def _package_ref(doc) -> dict[str, str]:
	business_code = (doc.package_code or doc.name or "").strip()
	return {
		"id": doc.name,
		"code": business_code,
		"name": (doc.package_name or business_code).strip(),
	}


def _business_ref(object_type: str | None, object_code: str | None) -> dict[str, str]:
	code = (object_code or "").strip()
	if not code:
		return {"id": "", "code": "", "name": ""}

	if frappe.db.exists("Procurement Handoff Card", code):
		title = frappe.db.get_value("Procurement Handoff Card", code, "handoff_title") or code
		return {"id": code, "code": code, "name": str(title).strip()}

	if (object_type or "").strip() == "Demand" or frappe.db.exists("Demand", code):
		row = None
		if frappe.db.exists("Demand", code):
			row = frappe.db.get_value("Demand", code, ("name", "demand_id", "title"), as_dict=True)
		else:
			row = frappe.db.get_value(
				"Demand",
				{"demand_id": code},
				("name", "demand_id", "title"),
				as_dict=True,
			)
		if row:
			business_code = (row.get("demand_id") or row.get("name") or code).strip()
			return {
				"id": row.get("name") or code,
				"code": business_code,
				"name": (row.get("title") or business_code).strip(),
			}

	if (object_type or "").strip() == "Procurement Package" or frappe.db.exists(
		"Procurement Package", code
	):
		row = None
		if frappe.db.exists("Procurement Package", code):
			row = frappe.db.get_value(
				"Procurement Package",
				code,
				("name", "package_code", "package_name"),
				as_dict=True,
			)
		else:
			row = frappe.db.get_value(
				"Procurement Package",
				{"package_code": code},
				("name", "package_code", "package_name"),
				as_dict=True,
			)
		if row:
			business_code = (row.get("package_code") or row.get("name") or code).strip()
			return {
				"id": row.get("name") or code,
				"code": business_code,
				"name": (row.get("package_name") or business_code).strip(),
			}

	if (object_type or "").strip() in ("TM2 Tender", "Tender") or frappe.db.exists(
		"TM2 Tender", {"tender_code": code}
	):
		name, title = _tm2_name_and_title(code)
		return {"id": name or code, "code": code, "name": (title or code).strip()}

	return {"id": code, "code": code, "name": code}


def _event_display_label(event_type: str, *, to_state: str = "") -> str:
	event_type = (event_type or "").strip()
	if event_type == "Readiness Check Run" and (to_state or "").strip().lower() == "failed":
		return "Readiness checks failed"
	return _EVENT_LABELS.get(event_type, event_type or "Planning event")


def _actor_has_limited_evidence_access(actor: str) -> bool:
	roles = set(frappe.get_roles(actor or frappe.session.user))
	return bool(roles & _LIMITED_ROLES) and not bool(roles & _TECHNICAL_ROLES)


def _may_view_technical(actor: str) -> bool:
	roles = set(frappe.get_roles(actor or frappe.session.user))
	return bool(roles & _TECHNICAL_ROLES)


def _add_code(codes: set[str], value: str | None) -> None:
	code = (value or "").strip()
	if code:
		codes.add(code)


def _demand_business_code(demand_key: str | None) -> str:
	key = (demand_key or "").strip()
	if not key:
		return ""
	if frappe.db.exists("Demand", key):
		row = frappe.db.get_value("Demand", key, ("demand_id", "name"), as_dict=True) or {}
		return (row.get("demand_id") or row.get("name") or key).strip()
	row = frappe.db.get_value("Demand", {"demand_id": key}, ("demand_id", "name"), as_dict=True) or {}
	return (row.get("demand_id") or row.get("name") or key).strip()


def _package_evidence_scope_codes(doc) -> set[str]:
	codes: set[str] = set()
	_add_code(codes, doc.package_code)
	_add_code(codes, doc.name)
	_add_code(codes, doc.planning_inclusion_code)
	_add_code(codes, doc.release_code)
	_add_code(codes, doc.tender_code)
	_add_code(codes, doc.latest_readiness_code)
	_add_code(codes, doc.latest_review_code)

	demand_key = (doc.demand_id or "").strip()
	_add_code(codes, demand_key)
	demand_code = _demand_business_code(demand_key)
	_add_code(codes, demand_code)

	inclusion_code = (doc.planning_inclusion_code or "").strip()
	if inclusion_code:
		inclusion = get_planning_inclusion(inclusion_code)
		if inclusion:
			_add_code(codes, inclusion.get("demand_code"))
			_add_code(codes, inclusion.get("inclusion_code") or inclusion_code)
		else:
			_add_code(codes, inclusion_code)

	for row in frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": doc.name},
		fields=["name", "package_line_code"],
	):
		_add_code(codes, row.get("name"))
		_add_code(codes, row.get("package_line_code"))

	business_code = (doc.package_code or doc.name or "").strip()
	if business_code and frappe.db.exists("DocType", "Package Method Decision"):
		method_code = frappe.db.get_value(
			"Package Method Decision",
			{"package_code": business_code},
			"name",
		)
		_add_code(codes, method_code)

	release_code = (doc.release_code or "").strip()
	if release_code and frappe.db.exists("DocType", "Planning Release Consumption Record"):
		consumption_code = frappe.db.get_value(
			"Planning Release Consumption Record",
			{"release_code": release_code},
			"consumption_code",
		)
		_add_code(codes, consumption_code)

	return codes


def _event_in_package_scope(row: dict[str, Any], scope_codes: set[str]) -> bool:
	if not scope_codes:
		return True
	object_code = (row.get("object_code") or "").strip()
	evidence_ref = (row.get("evidence_ref") or "").strip()
	return object_code in scope_codes or evidence_ref in scope_codes


def _related_object_codes(doc) -> list[str]:
	return sorted(_package_evidence_scope_codes(doc))


def _load_audit_rows(*, journey_code: str, scope_codes: set[str]) -> list[dict[str, Any]]:
	if not frappe.db.exists("DocType", "Planning Audit Event"):
		return []

	journey_code = (journey_code or "").strip()
	if journey_code:
		rows = frappe.get_all(
			"Planning Audit Event",
			filters={"journey_code": journey_code},
			fields=_AUDIT_FIELDS,
			order_by="occurred_at asc, event_code asc",
		)
		return [row for row in rows if _event_in_package_scope(row, scope_codes)]

	if not scope_codes:
		return []

	return frappe.get_all(
		"Planning Audit Event",
		filters={"object_code": ["in", list(scope_codes)]},
		fields=_AUDIT_FIELDS,
		order_by="occurred_at asc, event_code asc",
	)


def format_planning_evidence_event(
	row: dict[str, Any],
	*,
	include_technical: bool = False,
	redact_sensitive: bool = False,
) -> dict[str, Any]:
	event_type = (row.get("event_type") or "").strip()
	to_state = (row.get("to_state") or "").strip()
	reason = (row.get("reason") or "").strip()
	if redact_sensitive and event_type in _SENSITIVE_EVENT_TYPES:
		reason = ""

	technical = None
	if include_technical:
		technical = {
			"event_code": (row.get("event_code") or "").strip(),
			"is_master_seed": bool(row.get("is_master_seed")),
		}
		if frappe.get_meta("Planning Audit Event").has_field("source_module"):
			technical["source_module"] = (row.get("source_module") or "").strip()

	object_type = (row.get("object_type") or "").strip()
	object_code = (row.get("object_code") or "").strip()
	evidence_ref = (row.get("evidence_ref") or "").strip()

	return {
		"event_code": (row.get("event_code") or "").strip(),
		"occurred_at": row.get("occurred_at"),
		"label": _event_display_label(event_type, to_state=to_state),
		"event_type": event_type,
		"object_type": object_type,
		"object_code": object_code,
		"object": _business_ref(object_type, object_code),
		"evidence_ref": evidence_ref,
		"evidence": _business_ref(None, evidence_ref),
		"actor": (row.get("actor") or "").strip(),
		"from_state": (row.get("from_state") or "").strip(),
		"to_state": to_state,
		"reason": reason or None,
		"journey_code": (row.get("journey_code") or "").strip(),
		"technical": technical,
	}


def fetch_planning_evidence_events_for_package(
	package_code: str,
	actor: str,
	*,
	limit: int | None = None,
) -> list[dict[str, Any]]:
	"""Return formatted planning evidence events in ascending chronological order."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	pkg_name = _resolve_package_name(package_code)
	if not pkg_name:
		return []

	doc = frappe.get_doc("Procurement Package", pkg_name)
	try:
		pp_scope.assert_may_act_on_procurement_package(doc, user=actor)
	except frappe.PermissionError:
		return []

	scope_codes = _package_evidence_scope_codes(doc)
	rows = _load_audit_rows(
		journey_code=(doc.journey_code or "").strip(),
		scope_codes=scope_codes,
	)
	include_technical = _may_view_technical(actor)
	redact_sensitive = _actor_has_limited_evidence_access(actor)
	events = [
		format_planning_evidence_event(
			row,
			include_technical=include_technical,
			redact_sensitive=redact_sensitive,
		)
		for row in rows
	]
	if limit is not None and limit > 0:
		return events[-limit:]
	return events


def get_planning_evidence_timeline(
	package_code: str,
	actor: str,
	*,
	limit: int | None = None,
) -> dict[str, Any]:
	"""Return ordered Planning Audit Event timeline for a procurement package."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"

	if not frappe.db.exists("DocType", "Procurement Package"):
		return _fail(
			code="PP_NOT_INSTALLED",
			message="Procurement Planning is not installed on this site.",
			role_key=role_key,
		)

	pkg_name = _resolve_package_name(package_code)
	if not pkg_name:
		return _fail(code="NOT_FOUND", message="Package not found.", role_key=role_key)

	try:
		doc = frappe.get_doc("Procurement Package", pkg_name)
		pp_scope.assert_may_act_on_procurement_package(doc, user=actor)
	except frappe.DoesNotExistError:
		return _fail(code="NOT_FOUND", message="Package not found.", role_key=role_key)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message="You do not have permission to view this package.",
			role_key=role_key,
		)

	business_code = (doc.package_code or doc.name or "").strip()
	events = fetch_planning_evidence_events_for_package(
		business_code,
		actor,
		limit=limit,
	)

	return {
		"ok": True,
		"role_key": role_key,
		"package_code": business_code,
		"package": _package_ref(doc),
		"journey_code": (doc.journey_code or "").strip(),
		"may_view_technical": _may_view_technical(actor),
		"total": len(events),
		"events": events,
	}
