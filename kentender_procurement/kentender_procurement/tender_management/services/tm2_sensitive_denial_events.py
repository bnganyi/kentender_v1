# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared §13.3 sensitive-denial extraction for ``export_tender_evidence`` and workbench Audit tab (P9-21a).

``extract_sensitive_denial_events_from_audit_rows`` must stay aligned with the filter used for
``sensitive_denial_events`` in :func:`~kentender_procurement.tender_management.services.export_tender_evidence.export_tender_evidence`.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, format_datetime


def parse_event_payload(raw: Any) -> dict[str, Any]:
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			p = frappe.parse_json(raw)
			return dict(p) if isinstance(p, dict) else {}
		except Exception:
			return {}
	return {}


def actor_display(row: dict[str, Any]) -> str:
	u = cstr(row.get("actor_user") or "").strip()
	if u:
		return u
	return cstr(row.get("actor_type") or "").strip() or _("Unknown")


def infer_sensitive_action_guess(event_type: str, payload: dict[str, Any]) -> str:
	et = cstr(event_type or "").strip()
	if et == "Access Denied":
		if cstr(payload.get("bid_code") or "").strip():
			return "BID2_VIEW_SEALED_CONTENT"
		return "Access Denied"
	if et == "Late Submission Rejected":
		return "BID2_SUBMIT"
	return et or _("Event")


def extract_sensitive_denial_events_from_audit_rows(audit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""Same membership/shape as ``export_tender_evidence`` → ``sensitive_denial_events``."""
	out: list[dict[str, Any]] = []
	for row in audit_rows or []:
		et = cstr(row.get("event_type") or "").strip()
		dc = cstr(row.get("denial_code") or "").strip()
		if et != "Access Denied" and not dc:
			continue
		out.append(
			{
				"audit_event_code": row.get("audit_event_code") or row.get("name"),
				"event_type": et,
				"occurred_at": row.get("occurred_at"),
				"actor_user": row.get("actor_user"),
				"actor_type": row.get("actor_type"),
				"denial_code": dc or None,
				"related_object_type": row.get("related_object_type"),
				"related_object_id": row.get("related_object_id"),
				"event_payload": row.get("event_payload"),
			}
		)
	return out


def denied_actions_for_audit_evidence_tab(tm2_name: str, *, max_rows: int = 80) -> list[dict[str, Any]]:
	"""Workbench Audit tab — denied / sensitive rows (newest first) with table columns + ``display_line``."""
	fields = [
		"name",
		"audit_event_code",
		"event_type",
		"occurred_at",
		"actor_user",
		"actor_type",
		"denial_code",
		"event_payload",
		"related_object_type",
		"related_object_id",
	]
	rows = frappe.get_all(
		"TM2 Tender Audit Event",
		filters={"tm2_tender": tm2_name},
		fields=fields,
		order_by="occurred_at asc, creation asc",
		limit=2000,
	)
	sens = extract_sensitive_denial_events_from_audit_rows(rows)
	sens = list(reversed(sens))[: max(1, min(int(max_rows or 80), 200))]
	out: list[dict[str, Any]] = []
	for ev in sens:
		pl = parse_event_payload(ev.get("event_payload"))
		et = cstr(ev.get("event_type") or "").strip()
		ag = infer_sensitive_action_guess(et, pl)
		ad = actor_display(ev)
		dc = cstr(ev.get("denial_code") or "").strip()
		occ = ev.get("occurred_at")
		ts = format_datetime(occ) if occ else ""
		disp = _("{0} denied {1} · {2}").format(ad, ag, dc or et)
		code = cstr(ev.get("audit_event_code") or ev.get("name") or "").strip()
		sfx = code.replace(" ", "-").lower() if code else str(len(out))
		out.append(
			{
				"audit_event_code": code,
				"occurred_at_display": ts,
				"actor_display": ad,
				"action_guess": ag,
				"denial_code": dc,
				"event_type": et,
				"display_line": str(disp),
				"row_test_suffix": sfx,
			}
		)
	return out
