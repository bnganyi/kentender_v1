# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.32 §7.8 — what Planning knows about the originating drawdowns of a cancelled Tender, for Requisitions' read-only
classification of Tenders cancelled before the recovery existed (REQ-CHG-001 v1.20 §19.1). Planning answers for its own records: whether
each drawdown exists, its state, why and by which recovery it was reversed, its exact quantity and value, and whether a recovery hold
is on it. Authenticated by the same minted `RecoveryCaller` as the recovery commands; writes nothing."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_planning.services import cancellation_recovery
from kentender_procurement.procurement_planning.services import money as money_boundary
from kentender_procurement.procurement_planning.services.recovery_principal import require_recovery_caller


def drawdown_facts(*, caller, recovery_id: str, drawdown_references: list[str]) -> list[dict[str, Any]]:
	require_recovery_caller(caller, recovery_id)
	out = []
	for reference in drawdown_references:
		row = frappe.db.get_value(
			cancellation_recovery.DRAWDOWN, cstr(reference),
			["name", "plan_item_id", "allocation", "allocation_id", "requisition_reference", "quantity", "amount", "drawdown_state", "reversal_reason", "recovery_id"], as_dict=True,
		)
		if not row:
			out.append({"drawdown_reference": cstr(reference), "found": False})
			continue
		out.append(
			{
				"drawdown_reference": row.name, "found": True, "plan_item_id": cstr(row.plan_item_id), "state": cstr(row.drawdown_state), "reversal_reason": cstr(row.reversal_reason),
				"recovery_id": cstr(row.recovery_id), "requisition_reference": cstr(row.requisition_reference),
				"allocation_id": cstr(row.allocation_id) or cstr(frappe.db.get_value("Plan Source Allocation", row.allocation, "allocation_id")),
				"quantity": money_boundary.quantity_text(row.quantity), "amount": money_boundary.money_text(row.amount),
				"held": cancellation_recovery.drawdown_is_held(row.name),
			}
		)
	return out
