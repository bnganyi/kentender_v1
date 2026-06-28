# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""Recent budget activity events for the hub timeline panel.

Event types and their icons (per W3-01 spec):
  allocation  → add_box    (Budget approved at version 1)
  revision    → history    (Budget approved at version > 1)
  reservation → lock       (Budget Reservation status = Active)
  release     → lock_open  (Budget Reservation status = Released)
"""
from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt


# ── Icon + colour palette ──────────────────────────────────────────────────────
_EVENT_ICON: dict[str, str] = {
	"allocation":  "add_box",
	"revision":    "history",
	"reservation": "lock",
	"release":     "lock_open",
}


def _fmt_kes(amount: float) -> str:
	"""KES X,XXX,XXX string for human-readable movement descriptions."""
	return f"KES {int(round(flt(amount))):,}"


@frappe.whitelist()
def get_budget_movements(limit: int = 10) -> dict:
	"""Return the most-recent budget activity events ordered newest-first.

	Each item in ``movements`` contains:
	  event_type  – canonical type key (allocation | revision | reservation | release)
	  icon        – Material Symbol name
	  title       – human label ("Funds Reserved", "Budget Allocation", …)
	  desc        – one-line human description with amounts and references
	  ref         – primary document reference (reservation_id or budget name)
	  ts          – ISO-ish datetime string (UTC, sortable)
	  entity_name – Procuring Entity display name (empty string when unavailable)
	"""
	if not frappe.has_permission("Budget", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	limit = min(int(limit or 10), 100)
	events: list[dict] = []

	# ── 1. Active reservations ─────────────────────────────────────────────────
	res_rows = frappe.db.sql(
		"""
		SELECT
			br.name         AS doc_name,
			br.reservation_id,
			br.amount,
			br.created_at   AS ts,
			br.source_doctype,
			br.source_business_id,
			br.procuring_entity,
			pe.entity_name
		FROM `tabBudget Reservation` br
		LEFT JOIN `tabProcuring Entity` pe ON pe.name = br.procuring_entity
		WHERE br.status = 'Active'
		  AND br.created_at IS NOT NULL
		ORDER BY br.created_at DESC
		LIMIT %(limit)s
		""",
		{"limit": limit},
		as_dict=True,
	)
	for r in res_rows:
		amount_str = _fmt_kes(r.amount)
		desc = f"{amount_str} reserved"
		if r.source_business_id:
			src = r.source_doctype or "source"
			desc += f" for {src} {r.source_business_id}"
		events.append({
			"event_type": "reservation",
			"icon": _EVENT_ICON["reservation"],
			"title": "Funds Reserved",
			"desc": desc,
			"ref": r.reservation_id or r.doc_name or "",
			"ts": str(r.ts or ""),
			"entity_name": r.entity_name or "",
		})

	# ── 2. Released reservations ───────────────────────────────────────────────
	rel_rows = frappe.db.sql(
		"""
		SELECT
			br.name         AS doc_name,
			br.reservation_id,
			br.amount,
			br.released_at  AS ts,
			br.source_doctype,
			br.source_business_id,
			br.procuring_entity,
			pe.entity_name
		FROM `tabBudget Reservation` br
		LEFT JOIN `tabProcuring Entity` pe ON pe.name = br.procuring_entity
		WHERE br.status = 'Released'
		  AND br.released_at IS NOT NULL
		ORDER BY br.released_at DESC
		LIMIT %(limit)s
		""",
		{"limit": limit},
		as_dict=True,
	)
	for r in rel_rows:
		amount_str = _fmt_kes(r.amount)
		desc = f"{amount_str} released"
		if r.source_business_id:
			src = r.source_doctype or "demand"
			desc += f" from {src} {r.source_business_id}"
		events.append({
			"event_type": "release",
			"icon": _EVENT_ICON["release"],
			"title": "Reservation Released",
			"desc": desc,
			"ref": r.reservation_id or r.doc_name or "",
			"ts": str(r.ts or ""),
			"entity_name": r.entity_name or "",
		})

	# ── 3. Budget allocations (version 1 approved) ────────────────────────────
	# Use COALESCE(approved_at, modified) so budgets promoted via set_value
	# (which leaves approved_at NULL) still appear as timeline events.
	alloc_rows = frappe.db.sql(
		"""
		SELECT
		    b.name,
		    b.budget_name,
		    b.total_budget_amount,
		    COALESCE(b.approved_at, b.modified) AS ts,
		    b.procuring_entity,
		    pe.entity_name
		FROM `tabBudget` b
		LEFT JOIN `tabProcuring Entity` pe ON pe.name = b.procuring_entity
		WHERE b.status IN ('Approved', 'Active')
		  AND b.version_no = 1
		ORDER BY ts DESC
		LIMIT %(limit)s
		""",
		{"limit": limit},
		as_dict=True,
	)
	for r in alloc_rows:
		amount_str = _fmt_kes(r.total_budget_amount)
		entity = r.entity_name or r.procuring_entity or ""
		desc = f"{amount_str} allocated to {r.budget_name}"
		if entity:
			desc += f" ({entity})"
		events.append({
			"event_type": "allocation",
			"icon": _EVENT_ICON["allocation"],
			"title": "Budget Allocation",
			"desc": desc,
			"ref": r.name or "",
			"ts": str(r.ts or ""),
			"entity_name": entity,
		})

	# ── 4. Budget revisions (version > 1 approved) ────────────────────────────
	rev_rows = frappe.db.sql(
		"""
		SELECT
		    b.name,
		    b.budget_name,
		    b.version_no,
		    b.total_budget_amount,
		    COALESCE(b.approved_at, b.modified) AS ts,
		    b.procuring_entity,
		    pe.entity_name
		FROM `tabBudget` b
		LEFT JOIN `tabProcuring Entity` pe ON pe.name = b.procuring_entity
		WHERE b.version_no > 1
		ORDER BY ts DESC
		LIMIT %(limit)s
		""",
		{"limit": limit},
		as_dict=True,
	)
	for r in rev_rows:
		entity = r.entity_name or r.procuring_entity or ""
		desc = f"{r.budget_name} version {r.version_no} revision approved"
		if entity:
			desc += f" ({entity})"
		events.append({
			"event_type": "revision",
			"icon": _EVENT_ICON["revision"],
			"title": "Revision Approved",
			"desc": desc,
			"ref": r.name or "",
			"ts": str(r.ts or ""),
			"entity_name": entity,
		})

	# ── Sort all events newest-first, return top limit ─────────────────────────
	events.sort(key=lambda ev: ev.get("ts") or "", reverse=True)
	return {"movements": events[:limit]}
