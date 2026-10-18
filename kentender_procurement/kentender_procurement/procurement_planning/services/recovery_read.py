# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.32 §5.4.7 / §10.19 — Planning's own account of a cancelled Tender's recovery, for its screens.

Planning does not read Requisitions' recovery record (Requisitions is downstream of it); everything here comes from Planning's own
records: the Active recovery holds (the recovery is Pending, or Needs attention when the hold says so) and the drawdowns a verified
recovery reversed (the recovery is Completed, with the exact quantity and value restored). The section carries the specification's
own local labels, the restored amounts and the permitted next step; identifiers go under Technical details; nothing offers to
restore, release or edit anything."""

from __future__ import annotations

from typing import Any, Callable

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_planning.services import money as money_boundary

TITLE = "Unused allowance and funding"
LABELS = {
	"Pending": ("Restoring unused allowance", "The unused allowance of this item is being restored after a tender was cancelled. The affected source cannot be used until restoration is complete."),
	"Completed": ("Unused allowance restored after tender cancellation", "The allowance is available again, within the original plan item and within the checks every new requisition passes."),
	"Needs attention": ("Unused allowance could not be restored", "The affected source stays held until the cause is corrected. Other sources of this item are not affected."),
}


def _label(name: str) -> str:
	return cstr(frappe.db.get_value("Plan Source Allocation", {"allocation_id": name}, "organisation_unit") or "")


def _department(unit: str) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", unit, "unit_name") or unit) if unit else "—"


def sections_for_item(plan_item_id: str, *, start_route: Callable[[], str] | None = None) -> list[dict[str, Any]]:
	"""One section per recovery that has touched this stable Plan Item, newest first. Held recoveries are Pending or Needs attention; reversed
	ones are Completed. `start_route` yields the ordinary route to a fresh Requisition, asked only for a Completed recovery, and empty unless Planning currently offers it."""
	out: list[dict[str, Any]] = []
	holds = frappe.get_all(
		"Plan Cancellation Recovery Hold", filters={"plan_item_id": cstr(plan_item_id), "state": "Active"},
		fields=["recovery_id", "cancellation_id", "allocation_id", "drawdown_reference", "quantity", "amount", "display_status", "reason", "creation"], order_by="creation desc",
	)
	by_recovery: dict[str, list] = {}
	for hold in holds:
		by_recovery.setdefault(hold.recovery_id, []).append(hold)
	for recovery_id, rows in by_recovery.items():
		status = "Needs attention" if any(r.display_status == "Needs attention" for r in rows) else "Pending"
		label, explanation = LABELS[status]
		reason = next((cstr(r.reason) for r in rows if cstr(r.reason)), "")
		out.append(_section(recovery_id, rows[0].cancellation_id, status, label, explanation, reason, [_row(r.allocation_id, r.quantity, r.amount, "", "") for r in rows], [r.drawdown_reference for r in rows], ""))
	reversed_rows = frappe.get_all(
		"Plan Drawdown Reference", filters={"plan_item_id": cstr(plan_item_id), "reversal_reason": "TenderCancelled", "drawdown_state": "Reversed"},
		fields=["name", "recovery_id", "cancellation_id", "allocation_id", "quantity", "amount", "reversed_at"], order_by="reversed_at desc",
	)
	done: dict[str, list] = {}
	for row in reversed_rows:
		done.setdefault(row.recovery_id, []).append(row)
	for recovery_id, rows in done.items():
		if recovery_id in by_recovery:
			continue
		label, explanation = LABELS["Completed"]
		out.append(
			_section(
				recovery_id, rows[0].cancellation_id, "Completed", label, explanation, "",
				[_row(r.allocation_id, r.quantity, r.amount, r.quantity, r.amount) for r in rows], [r.name for r in rows], (start_route() if start_route else ""),
			)
		)
	return out


def start_route_for(plan_item_id: str) -> str:
	"""The ordinary route to a fresh Requisition for this purchase, only when Planning currently offers it to this reader (the Requisitions
	eligibility read is scoped to the reader). Nothing starts for anyone and the old handoff is never reopened."""
	from kentender_procurement.procurement_planning.services import plan_requisition

	try:
		offered = {row["plan_item_id"] for row in plan_requisition.list_requisition_eligible_plan_items()}
	except Exception:  # noqa: BLE001 — an unreadable offer is no offer
		return ""
	return f"/app/procurement-requisitions/new/{cstr(plan_item_id)}" if cstr(plan_item_id) in offered else ""


def _segments(path: str) -> list[str]:
	"""The Desk route as the segments `frappe.set_route` takes ('/app/procurement-requisitions/new/PPI-1' -> ['procurement-requisitions', 'new', 'PPI-1'])."""
	parts = [p for p in cstr(path).split("/") if p]
	return parts[1:] if parts and parts[0] == "app" else parts


def _row(allocation_id: str, quantity, amount, restored_quantity, restored_amount) -> dict[str, Any]:
	unit = _department(_label(allocation_id))
	return {
		"key": allocation_id, "source": unit, "quantity": money_boundary.quantity_text(quantity), "value": money_boundary.money_text(amount),
		"restored": f"{money_boundary.quantity_text(restored_quantity)} · {money_boundary.money_text(restored_amount)}" if cstr(restored_amount) else "—",
	}


def _section(recovery_id: str, cancellation_id: str, status: str, label: str, explanation: str, reason: str, rows: list, drawdowns: list[str], start_route: str) -> dict[str, Any]:
	return {
		"title": TITLE, "status": status, "label": label, "explanation": explanation, "reason": reason, "rows": rows, "partial_view": False,
		"technical": [{"label": "Recovery", "value": recovery_id}, {"label": "Cancellation", "value": cancellation_id}, *({"label": "Planning drawdown", "value": d} for d in drawdowns)],
		"next_step": ({"label": "Start a new requisition for this purchase", "route": _segments(start_route)} if status == "Completed" and start_route else None), "recovery": recovery_id,
	}
