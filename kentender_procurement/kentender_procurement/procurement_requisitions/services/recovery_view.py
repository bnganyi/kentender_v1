# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.20 §13.15 / TPR-CHG-001 v0.21 §10.18 — the 'Unused allowance and funding' section, in plain words.

One presenter turns the recovery Requisitions holds (`cancellation_recovery.get_cancellation_resource_recovery`) into the section every
owner screen shows, with the exact local label of that owner's own specification. Amounts and reasons are the authorised owner
projection; identifiers and digests go under Technical details; a departmental reader sees only its own department's rows and is told
so, never a total that would reveal the others. The screen never claims restoration or release before the whole owner transaction has
committed — `Completed` is read from the recovery record, which is written in that very transaction.

No button here restores or releases anything: the only action offered is the ordinary route to a fresh Requisition, and only when the
server says it is currently allowed."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_requisitions.services import precision

TITLE = "Unused allowance and funding"
PENDING, COMPLETED, NEEDS_ATTENTION = "Pending", "Completed", "Needs attention"

#: owner → status → (label, explanation). The labels are the specifications' own words (REQ §13.15, TPR §5.7A, PLN §5.4.7, BUD §8.9).
COPY: dict[str, dict[str, tuple[str, str]]] = {
	"Tenders": {
		PENDING: ("Restoring unused allowance and funding", "You can view the cancelled tender. The affected allowance cannot be used until restoration is complete."),
		COMPLETED: ("Unused allowance and funding restored", "The unused planning allowance and budget reservation of this tender have been restored."),
		NEEDS_ATTENTION: ("Unused allowance and funding need attention", "The unused allowance and funding could not be restored automatically. Nothing was changed."),
	},
	"Requisitions": {
		PENDING: ("Restoring unused allowance and funding", "The allowance and funding of this requisition are being restored after the tender was cancelled. A new requisition for the same purchase can be authorised when restoration is complete."),
		COMPLETED: ("Unused allowance and funding restored", "This requisition stays authorised and its handoff stays used. The unused allowance and funding were restored after the tender was cancelled."),
		NEEDS_ATTENTION: ("Unused allowance and funding need attention", "The unused allowance and funding could not be restored automatically. Nothing was changed."),
	},
	"Planning": {
		PENDING: ("Restoring unused allowance", "The unused allowance of this item is being restored after a tender was cancelled. It cannot be used until restoration is complete."),
		COMPLETED: ("Unused allowance restored after tender cancellation", "The allowance is available again, within the original plan item and within the checks every new requisition passes."),
		NEEDS_ATTENTION: ("Unused allowance could not be restored", "The allowance stays held until the cause is corrected. Other sources of this item are not affected."),
	},
	"Budget": {
		PENDING: ("Being released after tender cancellation", "The reservation stays held until the unused amount is released."),
		COMPLETED: ("Released after tender cancellation", "The reservation was released because its tender was cancelled before any award."),
		NEEDS_ATTENTION: ("Release after tender cancellation needs attention", "The reservation stays held until the cause is corrected."),
	},
}


def _money(value: Any, currency: str) -> str:
	"""`KES 6,000,000.00`, the form every Requisitions screen shows (`precision.display_money`); the stored currency leads when it is not KES."""
	if not cstr(value):
		return "—"
	shown = precision.display_money(Decimal(cstr(value)))
	return shown if cstr(currency) in ("", "KES") else f"{currency} {shown.split(' ', 1)[1]}"


def _quantity(value: Any, unit: str) -> str:
	text = cstr(value)
	if not text:
		return "—"
	number = flt(text)
	shown = f"{number:,.3f}".rstrip("0").rstrip(".")
	return f"{shown} {unit}".strip()


def _unit_label(name: str) -> str:
	"""The unit as the Requisition line stores it ('Each'), which is already its display name."""
	return cstr(name)


def _department(unit: str) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", unit, "unit_name") or unit)


def section(recovery: dict[str, Any] | None, *, owner: str, start_route: str = "") -> dict[str, Any] | None:
	"""The section for one owner's screen, or None when there is no recovery to show. `start_route` is the ordinary route to a fresh
	Requisition, given only when the server finds it currently allowed for this reader."""
	if not recovery:
		return None
	status = recovery["status"]
	label, explanation = COPY[owner][status]
	rows = []
	for source in recovery["sources"]:
		unit = _unit_label(source.get("unit") or "")
		currency = source.get("currency") or ""
		rows.append(
			{
				"key": source["drawdown_line_id"], "source": _department(source["contributing_org_unit"]) if source.get("contributing_org_unit") else "—",
				"quantity": _quantity(source["quantity"], unit), "value": _money(source["value"], currency),
				"restored": (f"{_quantity(source['restored_quantity'], unit)} · {_money(source['restored_value'], currency)}" if source.get("restored_value") else "—"),
				"released": _money(source["released_value"], currency) if source.get("released_value") else "—",
			}
		)
	technical = [
		{"label": "Recovery", "value": recovery["recovery"]}, {"label": "Cancellation", "value": recovery["cancellation"]}, {"label": "Requisition", "value": recovery["requisition_reference"]},
		{"label": "Status revision", "value": str(recovery["status_revision"])}, {"label": "Attempts", "value": str(recovery["attempt_count"])},
	]
	for source in recovery["sources"]:
		technical.append({"label": f"Planning drawdown ({source['allocation_id']})", "value": source.get("drawdown_reference") or "—"})
		technical.append({"label": f"Budget reservation ({source['allocation_id']})", "value": source.get("reservation_id") or "—"})
	return {
		"title": TITLE, "status": status, "label": label, "explanation": explanation, "reason": recovery.get("reason") if status != COMPLETED else "",
		"rows": rows, "partial_view": not recovery.get("all_sources_shown", True), "technical": technical,
		"next_step": ({"label": "Start a new requisition for this purchase", "route": start_route} if status == COMPLETED and start_route else None),
		"recovery": recovery["recovery"], "status_revision": recovery["status_revision"],
	}


def for_tender(tender: str, *, owner: str = "Tenders", user: str | None = None) -> dict[str, Any] | None:
	"""The section for a cancelled Tender's screen, built from what the reader is allowed to see; None when there is none or the reader may not see it."""
	from kentender_procurement.procurement_requisitions.services import cancellation_recovery

	try:
		recovery = cancellation_recovery.get_cancellation_resource_recovery(tender=tender, user=user)
	except (frappe.DoesNotExistError, frappe.PermissionError):
		return None
	return section(recovery, owner=owner, start_route=_start_route(recovery, user))


def for_requisition(requisition: str, *, user: str | None = None) -> dict[str, Any] | None:
	from kentender_procurement.procurement_requisitions.services import cancellation_recovery

	try:
		recovery = cancellation_recovery.get_cancellation_resource_recovery(requisition=requisition, user=user)
	except (frappe.DoesNotExistError, frappe.PermissionError):
		return None
	return section(recovery, owner="Requisitions", start_route=_start_route(recovery, user))


def _start_route(recovery: dict[str, Any], user: str | None) -> str:
	"""The ordinary route to a fresh Requisition, only if Planning currently offers this Plan Item to this reader. No replacement is created
	for anyone and the old handoff is never reopened."""
	if recovery["status"] != COMPLETED:
		return ""
	from kentender_procurement.procurement_requisitions.services import eligibility_gateway

	try:
		offered = {row["plan_item_id"] for row in eligibility_gateway.list_requisition_eligible_plan_items()}
	except Exception:  # noqa: BLE001 — an unreadable offer is no offer
		return ""
	return f"/app/procurement-requisitions/new/{recovery['plan_item_id']}" if recovery["plan_item_id"] in offered else ""
