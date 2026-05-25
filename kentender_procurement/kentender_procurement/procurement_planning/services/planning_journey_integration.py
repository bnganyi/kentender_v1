# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-014 — Planning journey/handoff read integration with Procurement Lifecycle."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.journey_step_aggregator import (
	aggregate_procurement_journey_steps,
)
from kentender_procurement.procurement_planning.api.landing import resolve_pp_role_key
from kentender_procurement.procurement_planning.package_journey_surfaces import (
	journey_link_hints_by_package_codes,
)
from kentender_procurement.procurement_planning.package_planning_release_display import (
	pkgrel_handoff_code_from_journey_code,
)
from kentender_procurement.procurement_planning.permissions import pp_scope
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	get_planning_inclusion,
)

_PLANNING_STEP_KEYS = frozenset({"planning_inclusion", "package_release"})
_SOURCE_OF_TRUTH_NOTE = (
	"Procurement Package status is authoritative; journey/handoff is navigation/evidence only."
)

_HANDOFF_FIELDS = [
	"handoff_code",
	"handoff_title",
	"status",
	"source_module",
	"target_module",
	"source_object_type",
	"source_object_code",
	"target_object_type",
	"target_object_code",
	"journey_code",
	"locked_summary",
	"passed_forward_summary",
	"next_action",
]


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
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


def _resolve_package_name(package_code: str) -> str | None:
	code = (package_code or "").strip()
	if not code:
		return None
	if frappe.db.exists("Procurement Package", code):
		return code
	name = frappe.db.get_value("Procurement Package", {"package_code": code}, "name")
	return str(name) if name else None


def _load_handoff_card_row(handoff_code: str) -> dict[str, Any] | None:
	code = (handoff_code or "").strip()
	if not code or not frappe.db.exists("Procurement Handoff Card", code):
		return None
	row = frappe.db.get_value("Procurement Handoff Card", code, _HANDOFF_FIELDS, as_dict=True)
	if not row:
		return None
	return {
		"handoff_code": str(row.get("handoff_code") or code).strip(),
		"handoff_title": str(row.get("handoff_title") or "").strip(),
		"status": str(row.get("status") or "").strip(),
		"source_module": str(row.get("source_module") or "").strip(),
		"target_module": str(row.get("target_module") or "").strip(),
		"source_object_type": str(row.get("source_object_type") or "").strip(),
		"source_object_code": str(row.get("source_object_code") or "").strip(),
		"target_object_type": str(row.get("target_object_type") or "").strip(),
		"target_object_code": str(row.get("target_object_code") or "").strip(),
		"journey_code": str(row.get("journey_code") or "").strip(),
		"locked_summary": _safe_dict(row.get("locked_summary")),
		"passed_forward_summary": _safe_dict(row.get("passed_forward_summary")),
		"next_action": str(row.get("next_action") or "").strip(),
	}


def _format_planning_inclusion_handoff(inclusion: dict[str, Any] | None) -> dict[str, Any] | None:
	if not inclusion:
		return None
	return {
		"handoff_code": str(inclusion.get("handoff_code") or inclusion.get("inclusion_code") or "").strip(),
		"status": str(inclusion.get("handoff_status") or inclusion.get("status") or "").strip(),
		"journey_code": str(inclusion.get("journey_code") or "").strip(),
		"source_object_type": "Demand",
		"source_object_code": str(inclusion.get("source_object_code") or inclusion.get("demand_code") or "").strip(),
		"target_object_type": "Procurement Plan",
		"target_object_code": str(
			inclusion.get("target_object_code") or inclusion.get("procurement_plan_code") or ""
		).strip(),
		"locked_summary": _safe_dict(inclusion.get("locked_summary")),
		"passed_forward_summary": _safe_dict(inclusion.get("passed_forward_summary")),
	}


def _format_planning_release_handoff(card: dict[str, Any] | None) -> dict[str, Any] | None:
	if not card:
		return None
	return {
		"handoff_code": card.get("handoff_code"),
		"status": card.get("status"),
		"source_module": card.get("source_module"),
		"target_module": card.get("target_module"),
		"source_object_type": card.get("source_object_type"),
		"source_object_code": card.get("source_object_code"),
		"target_object_type": card.get("target_object_type"),
		"target_object_code": card.get("target_object_code"),
		"journey_code": card.get("journey_code"),
		"locked_summary": card.get("locked_summary") or {},
		"passed_forward_summary": card.get("passed_forward_summary") or {},
		"next_action": card.get("next_action"),
	}


def _resolve_journey_code(doc, business_code: str) -> str:
	journey_code = (doc.journey_code or "").strip()
	if journey_code:
		return journey_code
	link = journey_link_hints_by_package_codes([business_code]).get(business_code) or {}
	return str(link.get("journey_code") or "").strip()


def _load_planning_steps(journey_code: str) -> list[dict[str, Any]]:
	if not journey_code or not frappe.db.exists("Procurement Journey", journey_code):
		return []
	try:
		steps = aggregate_procurement_journey_steps(journey_code)
	except (ValueError, frappe.DoesNotExistError):
		return []
	return [step for step in steps if step.get("step_key") in _PLANNING_STEP_KEYS]


def compose_planning_journey_handoff_payload(*, doc, business_code: str) -> dict[str, Any]:
	"""Build planning journey/handoff block for an already authorized package document."""
	business_code = (business_code or doc.package_code or doc.name or "").strip()
	journey_code = _resolve_journey_code(doc, business_code)
	journey = journey_link_hints_by_package_codes([business_code]).get(business_code)
	if not journey and journey_code:
		journey = {
			"journey_code": journey_code,
			"journey_title": frappe.db.get_value("Procurement Journey", journey_code, "journey_title") or "",
			"open_route": f"/desk/plc-procurement-journey/{journey_code}",
		}

	inclusion_code = (doc.planning_inclusion_code or "").strip()
	inclusion_raw = get_planning_inclusion(inclusion_code) if inclusion_code else None
	planning_inclusion = _format_planning_inclusion_handoff(inclusion_raw)

	release_code = (doc.release_code or "").strip()
	if not release_code and journey_code:
		release_code = pkgrel_handoff_code_from_journey_code(journey_code)
	release_card = _load_handoff_card_row(release_code) if release_code else None
	planning_release = _format_planning_release_handoff(release_card)

	payload: dict[str, Any] = dict(journey or {})
	payload["planning_steps"] = _load_planning_steps(journey_code)
	payload["planning_inclusion"] = planning_inclusion
	payload["planning_release"] = planning_release
	return payload


def build_planning_journey_block(doc, business_code: str) -> dict[str, Any] | None:
	"""Return enriched journey block for workspace (link hints + planning handoff summaries)."""
	business_code = (business_code or doc.package_code or doc.name or "").strip()
	if not business_code:
		return None
	payload = compose_planning_journey_handoff_payload(doc=doc, business_code=business_code)
	if not payload.get("journey_code") and not payload.get("planning_steps"):
		return None
	return payload


def get_planning_journey_handoff_context(package_code: str, actor: str) -> dict[str, Any]:
	"""Return package-scoped planning journey steps and handoff summaries (read-only)."""
	actor = (actor or frappe.session.user or "").strip() or frappe.session.user
	role_key = resolve_pp_role_key(actor) or "auditor"
	code = (package_code or "").strip()

	if not frappe.db.exists("DocType", "Procurement Package"):
		return _fail(
			code="PP_NOT_INSTALLED",
			message="Procurement Planning is not installed on this site.",
			role_key=role_key,
		)

	if not code:
		return _fail(code="NOT_FOUND", message="Package not found.", role_key=role_key)

	pkg_name = _resolve_package_name(code)
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
	journey_block = compose_planning_journey_handoff_payload(doc=doc, business_code=business_code)
	journey = {
		"journey_code": journey_block.get("journey_code") or "",
		"journey_title": journey_block.get("journey_title") or "",
		"open_route": journey_block.get("open_route") or "",
	}

	return {
		"ok": True,
		"role_key": role_key,
		"package_code": business_code,
		"package_status": (doc.status or "").strip(),
		"journey": journey,
		"planning_steps": journey_block.get("planning_steps") or [],
		"planning_inclusion": journey_block.get("planning_inclusion"),
		"planning_release": journey_block.get("planning_release"),
		"source_of_truth_note": _SOURCE_OF_TRUTH_NOTE,
	}
