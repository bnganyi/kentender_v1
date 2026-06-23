# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-003 — PP3 Evidence view-model adapter."""

from __future__ import annotations

import json
from typing import Any

from kentender_procurement.procurement_planning.services.planning_evidence_api import (
	get_planning_evidence_timeline,
)

_RECORD_TYPE_BY_EVENT: dict[str, str] = {
	"Demand Entered Planning Queue": "demand_approval",
	"Demand Included in Plan": "planning_inclusion",
	"Package Created": "procurement_package",
	"Package Line Created": "procurement_package",
	"Method Decision Recorded": "procurement_package",
	"Readiness Check Run": "readiness",
	"Package Submitted for Review": "review",
	"Package Approved": "review",
	"Package Marked Ready for Release": "planning_release",
	"Package Released to Tender Management": "planning_release",
	"Release Consumed by Tender Management": "tender_consumption",
	"Release Returned by Tender Management": "tender_consumption",
}

_RECORD_LABEL_BY_TYPE: dict[str, str] = {
	"demand_approval": "Demand Approval Certificate",
	"planning_inclusion": "Planning Inclusion Record",
	"procurement_package": "Procurement Package",
	"readiness": "Readiness Result",
	"review": "Review Decision",
	"planning_release": "Planning Release Package",
	"tender_consumption": "Tender Consumption Record",
}


def _timeline_status(row: dict[str, Any]) -> str:
	event_type = str(row.get("event_type") or "").strip().lower()
	to_state = str(row.get("to_state") or "").strip().lower()
	label = str(row.get("label") or "").strip().lower()
	if "failed" in to_state or "failed" in label:
		return "blocked"
	if "returned" in event_type or "returned" in label:
		return "in_progress"
	return "complete"


def _record_type(row: dict[str, Any]) -> str:
	event_type = str(row.get("event_type") or "").strip()
	return _RECORD_TYPE_BY_EVENT.get(event_type, "planning_record")


def _record_label(record_type: str) -> str:
	return _RECORD_LABEL_BY_TYPE.get(record_type, "Planning Record")


def _add_code(codes: set[str], value: str | None) -> None:
	code = str(value or "").strip()
	if code:
		codes.add(code)


def _first_matching(codes: list[str], prefix: str) -> str:
	for code in codes:
		if code.startswith(prefix):
			return code
	return ""


def _technical_codes(
	*,
	package_code: str,
	package_ref: dict[str, Any],
	events: list[dict[str, Any]],
) -> list[str]:
	codes: set[str] = set()
	_add_code(codes, package_code)
	_add_code(codes, package_ref.get("code"))
	_add_code(codes, package_ref.get("id"))
	for row in events:
		_add_code(codes, row.get("object_code"))
		_add_code(codes, row.get("evidence_ref"))
	return sorted(codes)


def _technical_fields(
	*,
	codes: list[str],
	events: list[dict[str, Any]],
	package_code: str,
) -> list[dict[str, str]]:
	source_code = _first_matching(codes, "DEM-")
	target_code = _first_matching(codes, "PKG-") or package_code
	inclusion_code = _first_matching(codes, "PLANINCL-")
	release_code = _first_matching(codes, "PKGREL-")
	consumption_code = _first_matching(codes, "PKGCONSUME-")
	audit_event_ref = ""
	for row in events:
		audit_event_ref = str(row.get("event_code") or "").strip()
		if audit_event_ref:
			break
	return [
		{"key": "source_object_code", "value": source_code},
		{"key": "target_object_code", "value": target_code},
		{
			"key": "locked_summary_json",
			"value": json.dumps({"package_code": package_code}, separators=(",", ":")),
		},
		{
			"key": "passed_forward_summary_json",
			"value": json.dumps({"release_code": release_code}, separators=(",", ":")),
		},
		{
			"key": "technical_refs_json",
			"value": json.dumps(
				{
					"inclusion": inclusion_code,
					"release": release_code,
					"consumption": consumption_code,
				},
				separators=(",", ":"),
			),
		},
		{"key": "audit_event_ref", "value": audit_event_ref},
	]


def get_evidence_view_model(
	*,
	package_code: str,
	actor: str,
) -> dict[str, Any]:
	"""Return PP3 evidence drawer contract for one package."""
	base = get_planning_evidence_timeline(package_code, actor)
	if not base.get("ok"):
		return base

	events = base.get("events") or []
	package = base.get("package") or {}
	title = str(package.get("name") or package.get("code") or package_code).strip()

	timeline: list[dict[str, Any]] = []
	for row in events:
		timeline.append(
			{
				"label": str(row.get("label") or "").strip(),
				"status": _timeline_status(row),
			}
		)

	records: list[dict[str, str]] = []
	seen: set[tuple[str, str]] = set()
	for row in events:
		r_type = _record_type(row)
		label = _record_label(r_type)
		key = (r_type, label)
		if key in seen:
			continue
		seen.add(key)
		records.append({"label": label, "type": r_type})

	may_view_technical = bool(base.get("may_view_technical"))
	technical_details: dict[str, Any] = {
		"visible_by_default": False,
		"requires_permission": True,
		"may_view_technical": may_view_technical,
	}
	if may_view_technical:
		codes = _technical_codes(
			package_code=package_code,
			package_ref=package,
			events=events,
		)
		technical_details["codes"] = codes
		technical_details["fields"] = _technical_fields(
			codes=codes,
			events=events,
			package_code=str(base.get("package_code") or package_code).strip(),
		)

	return {
		"ok": True,
		"role_key": base.get("role_key"),
		"package_code": str(base.get("package_code") or package_code).strip(),
		"title": title,
		"timeline": timeline,
		"records": records,
		"technical_details": technical_details,
	}
