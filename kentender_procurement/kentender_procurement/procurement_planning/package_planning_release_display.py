# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-006 / LV-R5-006-01 — Planning Release Package handoff summary for Procurement Planning UI."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.handoff_freshness import (
	validate_handoff_card_freshness,
)

_PLANNING_RELEASE_TITLE = "Planning Release Package"


def pkgrel_handoff_code_from_journey_code(journey_business_code: str) -> str:
	"""``JRN-MOH-2026-001`` → ``PKGREL-MOH-2026-001`` (same rule as ``planning_release_handoff._handoff_code``)."""
	jc = (journey_business_code or "").strip()
	if not jc:
		return ""
	suffix = jc[4:] if jc.upper().startswith("JRN-") else jc
	return f"PKGREL-{suffix}"


def _safe_pf_dict(raw: Any) -> dict[str, Any]:
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			parsed = json.loads(raw)
			return parsed if isinstance(parsed, dict) else {}
		except json.JSONDecodeError:
			pass
	return {}


def _desk_form_relative_path(doctype: str, name: str) -> str:
	from frappe.utils.data import quoted as fquoted
	from frappe.utils.data import slug as fslug

	return f"/desk/{fquoted(fslug(doctype))}/{fquoted(name)}"


def _tm2_name_and_title(tender_business_code: str) -> tuple[str | None, str]:
	"""Resolve TM2 Tender document name + ``tender_title`` from business ``tender_code``."""
	tc = (tender_business_code or "").strip()
	if not tc:
		return None, ""

	name = frappe.db.get_value("TM2 Tender", {"tender_code": tc}, "name")
	if name:
		ttl = (frappe.db.get_value("TM2 Tender", name, "tender_title") or "").strip()
		return str(name), ttl

	if frappe.db.exists("TM2 Tender", tc):
		ttl = (frappe.db.get_value("TM2 Tender", tc, "tender_title") or "").strip()
		return str(tc), ttl

	return None, ""


def _can_read_handoff_cards() -> bool:
	if not frappe.db.exists("DocType", "Procurement Handoff Card"):
		return False
	try:
		return bool(frappe.has_permission("Procurement Handoff Card", "read"))
	except frappe.PermissionError:
		return False


def batch_planning_release_handoff_hints_for_packages(
	package_codes: list[str],
	package_code_to_journey_payload: dict[str, dict[str, Any] | None],
) -> dict[str, dict[str, Any] | None]:
	"""Attach slim PKGREL payloads for PP **list rows** keyed by ``package_code``."""
	out: dict[str, dict[str, Any] | None] = {}
	codes = [str(c or "").strip() for c in (package_codes or []) if str(c or "").strip()]
	for pc in codes:
		out[pc] = None
	if not codes or not _can_read_handoff_cards():
		return out

	handoff_codes: list[str] = []
	ho_for_pc: dict[str, str] = {}
	for pc in codes:
		pj = package_code_to_journey_payload.get(pc) or {}
		jc = str(pj.get("journey_code") or "").strip()
		if not jc:
			continue
		ho = pkgrel_handoff_code_from_journey_code(jc)
		if ho:
			handoff_codes.append(ho)
			ho_for_pc[ho] = pc

	if not handoff_codes:
		return out

	uniq = sorted(set(handoff_codes))
	try:
		rows = frappe.get_all(
			"Procurement Handoff Card",
			filters={
				"handoff_code": ("in", uniq),
				"handoff_title": _PLANNING_RELEASE_TITLE,
			},
			fields=[
				"handoff_code",
				"status",
				"target_object_type",
				"target_object_code",
				"consumed_at",
			],
			limit=min(len(uniq) * 2, 500),
		)
	except frappe.PermissionError:
		for pc in codes:
			out[pc] = None
		return out

	row_by_code = {r.handoff_code: r for r in rows}
	for ho, pc in ho_for_pc.items():
		rec = row_by_code.get(ho)
		if not rec:
			out[pc] = None
			continue
		tc = str(rec.target_object_code or "").strip()
		_, ttl = _tm2_name_and_title(tc) if tc else (None, "")
		out[pc] = {
			"handoff_code": str(rec.handoff_code or ""),
			"status": str(rec.status or ""),
			"target_object_type": str(rec.target_object_type or ""),
			"tender_code": tc,
			"tender_title": ttl,
			"consumed_at": rec.consumed_at,
		}
	return out


def summarize_planning_release_handoff_for_package_detail(package_business_code: str) -> dict[str, Any] | None:
	"""Full read-model for PP **detail** pane (PLC navigation aggregate — ADR-PLC-002)."""
	pc = (package_business_code or "").strip()
	if not pc or not _can_read_handoff_cards():
		return None

	from kentender_procurement.procurement_lifecycle.journey_object_lookup import (
		resolve_journey_code_for_object,
	)

	j_pk = resolve_journey_code_for_object("Procurement Package", pc)
	if not j_pk:
		return None

	journey_business = (
		frappe.db.get_value("Procurement Journey", j_pk, "journey_code") or ""
	).strip() or str(j_pk)
	handoff_code = pkgrel_handoff_code_from_journey_code(journey_business)
	if not handoff_code:
		return None
	if not frappe.db.exists("Procurement Handoff Card", handoff_code):
		return None

	try:
		if not frappe.has_permission("Procurement Handoff Card", "read", handoff_code):
			return None
	except frappe.PermissionError:
		return None

	card = frappe.db.get_value(
		"Procurement Handoff Card",
		handoff_code,
		[
			"handoff_code",
			"handoff_title",
			"status",
			"target_object_type",
			"target_object_code",
			"journey_code",
			"next_action",
			"locked_summary",
			"passed_forward_summary",
			"generated_at",
			"consumed_at",
		],
		as_dict=True,
	)
	if not card:
		return None
	if (card.handoff_title or "").strip() != _PLANNING_RELEASE_TITLE:
		return None

	pf = _safe_pf_dict(card.get("passed_forward_summary"))
	ls = _safe_pf_dict(card.get("locked_summary"))
	tender_bc = str(card.target_object_code or "").strip()
	tnd_name, tnd_title_db = _tm2_name_and_title(tender_bc)
	title_guess = (pf.get("tender_title") or ls.get("package_title") or tnd_title_db or "").strip()
	t_route = ""
	if tnd_name and frappe.db.exists("TM2 Tender", tnd_name):
		t_route = _desk_form_relative_path("TM2 Tender", str(tnd_name))

	try:
		fres = validate_handoff_card_freshness(str(handoff_code))
	except Exception:
		fres = {"fresh": True, "stale_reason": None}

	return {
		"handoff_code": str(card.handoff_code or ""),
		"handoff_title": str(card.handoff_title or ""),
		"status": str(card.status or ""),
		"journey_code": journey_business,
		"next_action": str(card.next_action or ""),
		"generated_at": card.generated_at,
		"consumed_at": card.consumed_at,
		"tender_code": tender_bc,
		"tender_title": title_guess,
		"tender_open_route": t_route,
		"fresh": bool(fres.get("fresh", True)),
		"stale_reason": fres.get("stale_reason"),
	}
