# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-004 / LV-R5-004-02 — read-only demand → planning handoff aggregation.

Surfaces Demand ``planning_status`` plus **Demand Approval Certificate** and
**Planning Inclusion Record** handoff cards tied to the demand's Procurement
Journey (when the demand is **Approved**).  Navigation aggregate only
(ADR-PLC-002).
"""

from __future__ import annotations

import json
from typing import Any

import frappe


_DEMAND_APPROVAL_CERT_TITLE = "Demand Approval Certificate"
_PLANNING_INCLUSION_TITLE = "Planning Inclusion Record"


def _safe_json(raw: Any) -> Any:
	if raw is None:
		return None
	if isinstance(raw, (dict, list)):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			return json.loads(raw)
		except (json.JSONDecodeError, ValueError):
			pass
	return None


def _parse_evidence_links(raw: Any) -> list[dict[str, Any]]:
	parsed = _safe_json(raw)
	if parsed is None:
		return []
	if isinstance(parsed, dict):
		inner = parsed.get("links", [])
		return inner if isinstance(inner, list) else []
	if isinstance(parsed, list):
		return parsed
	return []


def _plc_journey_route(journey_code: str | None) -> str:
	jc = (journey_code or "").strip()
	if not jc:
		return "/desk/plc-procurement-journey"
	return f"/desk/plc-procurement-journey/{jc}"


def _summarize_handoff_card(card: dict[str, Any]) -> dict[str, Any]:
	"""Normalize a Procurement Handoff Card row into a compact API dict."""
	evidence = _parse_evidence_links(card.get("evidence_links_json"))
	demand_route = ""
	demand_approval_route = ""
	demand_approval_code = ""
	demand_approval_label = ""

	for lk in evidence:
		ot = str(lk.get("object_type") or "").strip()
		if ot == "Demand":
			demand_route = str(lk.get("route") or "").strip()
		elif ot == "Demand Approval":
			demand_approval_route = str(lk.get("route") or "").strip()
			demand_approval_code = str(lk.get("object_code") or "").strip()
			demand_approval_label = str(lk.get("label") or "Demand Approval Record").strip()

	locked_raw = _safe_json(card.get("locked_summary"))
	locked = locked_raw if isinstance(locked_raw, dict) else {}

	pfs_raw = _safe_json(card.get("passed_forward_summary"))
	pfs_dict: dict[str, Any] = pfs_raw if isinstance(pfs_raw, dict) else {}

	return {
		"handoff_code": str(card.get("handoff_code") or "").strip(),
		"handoff_title": str(card.get("handoff_title") or "").strip(),
		"status": str(card.get("status") or "").strip(),
		"target_module": str(card.get("target_module") or "").strip(),
		"next_action": str(card.get("next_action") or "").strip() or None,
		"generated_at": str(card["generated_at"]) if card.get("generated_at") else None,
		"consumed_at": str(card["consumed_at"]) if card.get("consumed_at") else None,
		"locked_summary": locked,
		"passed_forward_summary": pfs_dict,
		"evidence_links": evidence,
		"demand_form_route": demand_route,
		"demand_approval_record_route": demand_approval_route or demand_route,
		"demand_approval_record_code": demand_approval_code,
		"demand_approval_record_label": demand_approval_label or "Demand Approval Record",
	}


def _summarize_planning_inclusion(card: dict[str, Any]) -> dict[str, Any]:
	locked_raw = _safe_json(card.get("locked_summary"))
	tc = ""
	if isinstance(locked_raw, dict):
		tc = str(
			locked_raw.get("procurement_plan") or locked_raw.get("plan_code") or ""
		).strip()

	return {
		"handoff_code": str(card.get("handoff_code") or "").strip(),
		"handoff_title": str(card.get("handoff_title") or "").strip(),
		"status": str(card.get("status") or "").strip(),
		"target_object_type": card.get("target_object_type"),
		"target_object_code": str(card.get("target_object_code") or "").strip() or None,
		"next_action": str(card.get("next_action") or "").strip() or None,
		"generated_at": str(card["generated_at"]) if card.get("generated_at") else None,
		"consumed_at": str(card["consumed_at"]) if card.get("consumed_at") else None,
		"plan_code_hint": tc,
	}


def build_demand_planning_status_payload(demand_name: str) -> dict[str, Any]:
	"""Aggregate planning-handoff surfaces for one Demand doc (``name`` = primary key).

	Caller enforces authentication / journey read permission.
	"""
	from kentender_procurement.procurement_lifecycle.demand_module_gate import (
		demand_consumers_live,
		RETIRED_MESSAGE,
		demand_doctype_available,
	)

	nm = (demand_name or "").strip()
	if not nm:
		return {
			"ok": False,
			"error": "MISSING_PARAMS",
			"message": "demand_name is required.",
		}
	if not demand_consumers_live():
		return {
			"ok": False,
			"error": "DEMAND_MODULE_RETIRED",
			"message": RETIRED_MESSAGE,
			"skipped": True,
		}

	fields = ["name", "demand_id", "title", "status", "planning_status"]
	demand = frappe.db.get_value("Demand", nm, fields, as_dict=True)
	if not demand:
		return {"ok": False, "error": "NOT_FOUND", "message": "Demand not found."}

	demand_id = str(demand.get("demand_id") or "").strip()
	status = str(demand.get("status") or "").strip()
	planning_status = str(demand.get("planning_status") or "").strip()

	out: dict[str, Any] = {
		"ok": True,
		"demand_name": str(demand.get("name") or ""),
		"demand_id": demand_id,
		"demand_title": str(demand.get("title") or "").strip(),
		"demand_status": status,
		"planning_status_label": planning_status,
		"journey": None,
		"demand_approval_certificate": None,
		"planning_inclusion": None,
		"eligible_for_certificate": status == "Approved",
	}

	if status != "Approved":
		out["hint"] = (
			"When this demand is Approved, the Demand Approval Certificate and planning "
			"inclusion artefacts appear here if a Procurement Journey is linked."
		)
		return out

	if not demand_id:
		out["hint"] = "Demand has no Demand ID yet; journeys cannot resolve."
		return out

	jr_rows = frappe.get_all(
		"Procurement Journey",
		filters={"demand_ref": demand_id},
		fields=[
			"name",
			"journey_code",
			"journey_title",
			"current_stage_label",
			"current_status_category",
		],
		order_by="modified desc",
		limit=5,
	)
	if not jr_rows:
		out["hint"] = "No Procurement Journey references this Demand yet."
		return out

	# Deterministic primary journey: newest `modified`.
	j_head = jr_rows[0]
	jc = str(j_head.get("journey_code") or j_head.get("name") or "").strip()
	out["journey"] = {
		"journey_code": jc,
		"journey_title": str(j_head.get("journey_title") or "").strip(),
		"current_stage_label": str(j_head.get("current_stage_label") or "").strip(),
		"current_status_category": str(j_head.get("current_status_category") or "").strip(),
		"open_route": _plc_journey_route(jc),
	}

	card_fields = (
		"handoff_code",
		"handoff_title",
		"status",
		"target_module",
		"target_object_type",
		"target_object_code",
		"source_module",
		"generated_at",
		"consumed_at",
		"next_action",
		"locked_summary",
		"passed_forward_summary",
		"evidence_links_json",
	)

	raw_cards = frappe.get_all(
		"Procurement Handoff Card",
		filters={"journey_code": jc},
		fields=list(card_fields),
		order_by="generated_at asc",
		limit=500,
	)

	for cr in raw_cards:
		title = str(cr.get("handoff_title") or "").strip()
		if title == _DEMAND_APPROVAL_CERT_TITLE:
			out["demand_approval_certificate"] = _summarize_handoff_card(cr)
		elif title == _PLANNING_INCLUSION_TITLE:
			out["planning_inclusion"] = _summarize_planning_inclusion(cr)

	return out
