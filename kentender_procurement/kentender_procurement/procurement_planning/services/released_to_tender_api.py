# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-012 — Released to Tender list and Planning Release Package detail API."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.package_planning_release_display import (
	_PLANNING_RELEASE_TITLE,
	pkgrel_handoff_code_from_journey_code,
	summarize_planning_release_handoff_for_package_detail,
)
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_RELEASED,
)
from kentender_procurement.procurement_planning.services.package_workbench import (
	_tender_ref,
	derive_package_next_action,
)

_RELEASED_STATUSES = (PKG_RELEASED, PKG_CONSUMED)

_PACKAGE_FIELDS = [
	"name",
	"package_code",
	"package_name",
	"status",
	"release_code",
	"journey_code",
	"tender_code",
	"procuring_entity_code",
	"fiscal_year",
	"locked_after_release",
]

_NEXT_ACTION_LABELS = {
	"view_release": "View the planning release handoff.",
	"view_tender": "View tender.",
}


def _fail(
	*,
	code: str,
	message: str,
	role_key: str = "auditor",
) -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"total": 0,
		"rows": [],
		"filters_applied": {},
	}


def _detail_fail(
	*,
	code: str,
	message: str,
	role_key: str = "auditor",
) -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _safe_dict(raw: Any) -> dict[str, Any]:
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			parsed = json.loads(raw)
			return parsed if isinstance(parsed, dict) else {}
		except json.JSONDecodeError:
			pass
	return {}


def _release_code_for_package(pkg: dict[str, Any]) -> str:
	release_code = (pkg.get("release_code") or "").strip()
	if release_code:
		return release_code
	journey_code = (pkg.get("journey_code") or "").strip()
	return pkgrel_handoff_code_from_journey_code(journey_code) if journey_code else ""


def _format_consumption(row: dict[str, Any] | None, *, handoff_status: str = "") -> dict[str, Any] | None:
	if row:
		return {
			"status": (row.get("consumption_status") or "").strip() or "Consumed",
			"consumption_code": (row.get("consumption_code") or "").strip(),
			"consumed_at": row.get("consumed_at"),
			"target_object_code": (row.get("target_object_code") or "").strip(),
			"consumed_by": (row.get("consumed_by") or "").strip(),
		}
	status = (handoff_status or "").strip()
	if status == "Consumed":
		return {"status": "Consumed", "consumption_code": None, "consumed_at": None, "target_object_code": None}
	return {"status": "Not Consumed", "consumption_code": None, "consumed_at": None, "target_object_code": None}


def _batch_consumption_by_release(release_codes: list[str]) -> dict[str, dict[str, Any]]:
	codes = sorted({str(c or "").strip() for c in release_codes if str(c or "").strip()})
	out: dict[str, dict[str, Any]] = {}
	if not codes or not frappe.db.exists("DocType", "Planning Release Consumption Record"):
		return out
	rows = frappe.get_all(
		"Planning Release Consumption Record",
		filters={"release_code": ("in", codes)},
		fields=[
			"consumption_code",
			"release_code",
			"consumption_status",
			"consumed_at",
			"target_object_code",
			"consumed_by",
		],
		order_by="consumed_at desc, modified desc",
	)
	for row in rows:
		rc = (row.get("release_code") or "").strip()
		if rc and rc not in out:
			out[rc] = row
	return out


def _batch_handoff_by_release(release_codes: list[str]) -> dict[str, dict[str, Any]]:
	codes = sorted({str(c or "").strip() for c in release_codes if str(c or "").strip()})
	out: dict[str, dict[str, Any]] = {}
	if not codes or not frappe.db.exists("DocType", "Procurement Handoff Card"):
		return out
	try:
		rows = frappe.get_all(
			"Procurement Handoff Card",
			filters={
				"handoff_code": ("in", codes),
				"handoff_title": _PLANNING_RELEASE_TITLE,
			},
			fields=[
				"handoff_code",
				"status",
				"target_object_code",
				"consumed_at",
			],
			limit=min(len(codes) * 2, 500),
		)
	except frappe.PermissionError:
		return out
	for row in rows:
		ho = (row.get("handoff_code") or "").strip()
		if ho:
			out[ho] = row
	return out


def _base_filters(filters: dict[str, Any]) -> dict[str, Any]:
	clauses: dict[str, Any] = {
		"is_active": 1,
		"status": ("in", list(_RELEASED_STATUSES)),
	}

	package_status = (filters.get("package_status") or "").strip()
	if package_status:
		clauses["status"] = package_status

	fiscal_year = (filters.get("fiscal_year") or "").strip()
	if fiscal_year:
		clauses["fiscal_year"] = fiscal_year

	procuring_entity = (filters.get("procuring_entity") or "").strip()
	if procuring_entity:
		clauses["procuring_entity_code"] = procuring_entity

	return clauses


def _apply_search(rows: list[dict[str, Any]], search_text: str) -> list[dict[str, Any]]:
	q = (search_text or "").strip().lower()
	if not q:
		return rows
	out: list[dict[str, Any]] = []
	for row in rows:
		release = row.get("release") or {}
		package = row.get("package") or {}
		tender = row.get("tender") or {}
		consumption = row.get("consumption") or {}
		hay = " ".join(
			[
				str(release.get("code") or ""),
				str(release.get("name") or ""),
				str(package.get("code") or ""),
				str(package.get("name") or ""),
				str(tender.get("code") or ""),
				str(tender.get("name") or ""),
				str(consumption.get("consumption_code") or ""),
			]
		).lower()
		if q in hay:
			out.append(row)
	return out


def _apply_handoff_status_filter(rows: list[dict[str, Any]], handoff_status: str) -> list[dict[str, Any]]:
	target = (handoff_status or "").strip()
	if not target:
		return rows
	return [row for row in rows if str(row.get("handoff_status") or "").strip() == target]


def _apply_consumption_status_filter(
	rows: list[dict[str, Any]], consumption_status: str
) -> list[dict[str, Any]]:
	target = (consumption_status or "").strip()
	if not target:
		return rows
	out: list[dict[str, Any]] = []
	for row in rows:
		cons = row.get("consumption") or {}
		status = str(cons.get("status") or "").strip()
		if status == target:
			out.append(row)
	return out


def _format_list_row(
	pkg: dict[str, Any],
	*,
	role_key: str,
	handoff: dict[str, Any] | None,
	consumption: dict[str, Any] | None,
) -> dict[str, Any]:
	package_code = (pkg.get("package_code") or pkg.get("name") or "").strip()
	release_code = _release_code_for_package(pkg)
	handoff_status = str((handoff or {}).get("status") or "").strip()
	tender_code = (pkg.get("tender_code") or "").strip() or str(
		(handoff or {}).get("target_object_code") or ""
	).strip()
	tender = _tender_ref(tender_code, handoff=handoff)
	consumption_out = _format_consumption(consumption, handoff_status=handoff_status)
	next_action = derive_package_next_action(
		(pkg.get("status") or "").strip(),
		role_key,
		handoff={"status": handoff_status, "tender_code": tender_code},
	)
	if next_action.get("key") in _NEXT_ACTION_LABELS:
		next_action = {
			"key": next_action["key"],
			"label": _NEXT_ACTION_LABELS[next_action["key"]],
		}
	return {
		"release": {
			"id": release_code,
			"code": release_code,
			"name": release_code,
		},
		"handoff_status": handoff_status,
		"package": {
			"id": pkg.get("name") or "",
			"code": package_code,
			"name": (pkg.get("package_name") or package_code).strip(),
		},
		"package_status": (pkg.get("status") or "").strip(),
		"tender": tender,
		"consumption": consumption_out,
		"locked_after_release": bool(cint(pkg.get("locked_after_release"))),
		"procuring_entity_code": (pkg.get("procuring_entity_code") or "").strip(),
		"fiscal_year": (pkg.get("fiscal_year") or "").strip(),
		"next_action": next_action,
	}


def get_released_to_tender_rows(filters: dict[str, Any] | None, actor: str) -> dict[str, Any]:
	"""Return scoped Released to Tender list rows."""
	filters = dict(filters or {})
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"

	if not frappe.db.exists("DocType", "Procurement Package"):
		return _fail(
			code="PP_NOT_INSTALLED",
			message="Procurement Planning is not installed on this site.",
			role_key=role_key,
		)

	clauses = _base_filters(filters)
	try:
		pkgs = frappe.get_list(
			"Procurement Package",
			filters=clauses,
			fields=_PACKAGE_FIELDS,
			order_by="modified desc",
			limit_page_length=5000,
		)
	except frappe.PermissionError:
		return _fail(
			code="NO_PACKAGE_PERMISSION",
			message="You do not have permission to read procurement packages.",
			role_key=role_key,
		)

	scoped: list[dict[str, Any]] = []
	for pkg in pkgs:
		entity_code = (pkg.get("procuring_entity_code") or "").strip()
		if not pp_scope.entity_in_user_scope(entity_code, actor):
			continue
		scoped.append(pkg)

	release_codes = [_release_code_for_package(pkg) for pkg in scoped]
	release_codes = [rc for rc in release_codes if rc]
	handoff_by_release = _batch_handoff_by_release(release_codes)
	consumption_by_release = _batch_consumption_by_release(release_codes)

	formatted: list[dict[str, Any]] = []
	for pkg in scoped:
		release_code = _release_code_for_package(pkg)
		if not release_code:
			continue
		handoff = handoff_by_release.get(release_code)
		formatted.append(
			_format_list_row(
				pkg,
				role_key=role_key,
				handoff=handoff,
				consumption=consumption_by_release.get(release_code),
			)
		)

	formatted = _apply_search(formatted, str(filters.get("search_text") or ""))
	formatted = _apply_handoff_status_filter(formatted, str(filters.get("handoff_status") or ""))
	formatted = _apply_consumption_status_filter(
		formatted, str(filters.get("consumption_status") or "")
	)

	total = len(formatted)
	start = max(cint(filters.get("start") or 0), 0)
	limit = cint(filters.get("limit") or 50)
	if limit <= 0:
		limit = 50
	if limit > 200:
		limit = 200

	return {
		"ok": True,
		"role_key": role_key,
		"total": total,
		"rows": formatted[start : start + limit],
		"filters_applied": filters,
	}


def _load_release_handoff_card(release_code: str) -> dict[str, Any] | None:
	rc = (release_code or "").strip()
	if not rc or not frappe.db.exists("DocType", "Procurement Handoff Card"):
		return None
	if not frappe.db.exists("Procurement Handoff Card", rc):
		row = frappe.db.get_value(
			"Procurement Handoff Card",
			{"handoff_code": rc, "handoff_title": _PLANNING_RELEASE_TITLE},
			[
				"name",
				"handoff_code",
				"handoff_title",
				"status",
				"journey_code",
				"source_object_type",
				"source_object_code",
				"target_object_type",
				"target_object_code",
				"generated_at",
				"consumed_at",
				"locked_summary",
				"passed_forward_summary",
			],
			as_dict=True,
		)
		return row
	return frappe.db.get_value(
		"Procurement Handoff Card",
		rc,
		[
			"name",
			"handoff_code",
			"handoff_title",
			"status",
			"journey_code",
			"source_object_type",
			"source_object_code",
			"target_object_type",
			"target_object_code",
			"generated_at",
			"consumed_at",
			"locked_summary",
			"passed_forward_summary",
		],
		as_dict=True,
	)


def _format_handoff_detail(card: dict[str, Any]) -> dict[str, Any]:
	journey_business = str(card.get("journey_code") or "").strip()
	return {
		"handoff_code": str(card.get("handoff_code") or "").strip(),
		"status": str(card.get("status") or "").strip(),
		"journey_code": journey_business,
		"source_object_type": str(card.get("source_object_type") or "").strip(),
		"source_object_code": str(card.get("source_object_code") or "").strip(),
		"target_object_type": str(card.get("target_object_type") or "").strip(),
		"target_object_code": str(card.get("target_object_code") or "").strip(),
		"generated_at": card.get("generated_at"),
		"consumed_at": card.get("consumed_at"),
		"locked_summary": _safe_dict(card.get("locked_summary")),
		"passed_forward_summary": _safe_dict(card.get("passed_forward_summary")),
	}


def _format_consumption_detail(release_code: str) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"Planning Release Consumption Record",
		filters={"release_code": release_code},
		fields=[
			"consumption_code",
			"consumption_status",
			"consumed_at",
			"target_object_code",
			"target_object_type",
			"consumed_by",
			"consumed_by_module",
			"audit_event_ref",
		],
		order_by="consumed_at desc, modified desc",
		limit=1,
	)
	if not rows:
		return None
	row = rows[0]
	return {
		"status": (row.get("consumption_status") or "").strip() or "Consumed",
		"consumption_code": (row.get("consumption_code") or "").strip(),
		"consumed_at": row.get("consumed_at"),
		"target_object_code": (row.get("target_object_code") or "").strip(),
		"target_object_type": (row.get("target_object_type") or "").strip(),
		"consumed_by": (row.get("consumed_by") or "").strip(),
		"consumed_by_module": (row.get("consumed_by_module") or "").strip(),
		"audit_event_ref": (row.get("audit_event_ref") or "").strip(),
	}


def get_planning_release_package_context(release_code: str, actor: str) -> dict[str, Any]:
	"""Return Planning Release Package detail for Screen 19."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	release_code = (release_code or "").strip()

	if not frappe.db.exists("DocType", "Procurement Package"):
		return _detail_fail(
			code="PP_NOT_INSTALLED",
			message="Procurement Planning is not installed on this site.",
			role_key=role_key,
		)

	if not release_code:
		return _detail_fail(code="NOT_FOUND", message="Release not found.", role_key=role_key)

	card = _load_release_handoff_card(release_code)
	if not card or (card.get("handoff_title") or "").strip() != _PLANNING_RELEASE_TITLE:
		return _detail_fail(code="NOT_FOUND", message="Release not found.", role_key=role_key)

	package_code = str(card.get("source_object_code") or "").strip()
	if not package_code:
		return _detail_fail(code="NOT_FOUND", message="Release not found.", role_key=role_key)

	pkg_name = frappe.db.get_value(
		"Procurement Package",
		{"package_code": package_code},
		"name",
	)
	if not pkg_name and frappe.db.exists("Procurement Package", package_code):
		pkg_name = package_code
	if not pkg_name:
		return _detail_fail(code="NOT_FOUND", message="Release not found.", role_key=role_key)

	try:
		doc = frappe.get_doc("Procurement Package", pkg_name)
		pp_scope.assert_may_act_on_procurement_package(doc, user=actor)
	except frappe.DoesNotExistError:
		return _detail_fail(code="NOT_FOUND", message="Release not found.", role_key=role_key)
	except frappe.PermissionError:
		return _detail_fail(
			code="NO_PACKAGE_PERMISSION",
			message="You do not have permission to view this release.",
			role_key=role_key,
		)

	business_code = (doc.package_code or doc.name or "").strip()
	tender_code = (doc.tender_code or "").strip() or str(card.get("target_object_code") or "").strip()
	handoff_detail = _format_handoff_detail(card)
	consumption = _format_consumption_detail(release_code)
	if not consumption:
		consumption = _format_consumption(
			None, handoff_status=str(handoff_detail.get("status") or "")
		)

	return {
		"ok": True,
		"role_key": role_key,
		"release_code": release_code,
		"package": {
			"id": doc.name,
			"code": business_code,
			"name": (doc.package_name or business_code).strip(),
		},
		"package_status": (doc.status or "").strip(),
		"release": summarize_planning_release_handoff_for_package_detail(business_code),
		"handoff": handoff_detail,
		"consumption": consumption,
		"tender": _tender_ref(tender_code, handoff={"tender_code": tender_code}),
	}
