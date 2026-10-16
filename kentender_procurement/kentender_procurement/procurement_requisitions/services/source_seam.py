# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What Requisitions says, now, about the sources an authorised Requisition Version drew on (AWD-CHG-001 v0.7 §7.1 `VerifyAwardFundingLineage`; REQ-CHG-001 v1.19 §§5.3, 5.6, 5.12).

Read-only and published. Award verifies an allocation against the authoritative Requisition, not against the copy a Tender kept: the Version must still be the authorised one for its Requisition,
its items must still name the drawdown lines they named, and each drawdown line must still hold the reservation the allocation names. Nothing here is written or inferred; a Version this owner does not
hold, or one that is no longer the authorised Version, is reported as such, never as a guess."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_requisitions.services import authorise, precision


def authorised_sources(*, requisition: str, version: str) -> dict[str, Any] | None:
	"""The current facts of `version`, or None when this owner does not hold the Requisition or the Version."""
	if not requisition or not version or not frappe.db.exists("Procurement Requisition", requisition) or not frappe.db.exists("Requisition Version", version):
		return None
	root = frappe.db.get_value("Procurement Requisition", requisition, ["name", "current_state", "authorised_version", "lead_org_unit_id"], as_dict=True)
	doc = frappe.get_doc("Requisition Version", version)
	if doc.requisition != root.name:
		return None
	package = frappe.get_doc("IT Equipment Requirement Package Version", doc.package_version)
	handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": root.name, "requisition_version": doc.name}, ["name", "handoff_digest"], as_dict=True)
	return {
		"requisition": root.name,
		"version": doc.name,
		"state": cstr(root.current_state),
		"authorised": cstr(root.current_state) == "Authorised" and cstr(root.authorised_version) == doc.name,
		"content_digest": cstr(doc.content_digest),
		"handoff_digest": cstr(handoff.handoff_digest) if handoff else "",
		"source_set_hash": authorise.source_set_hash(doc),
		"drawdown_lines": [
			{
				"drawdown_line_id": line.drawdown_line_id, "plan_item_line_id": line.plan_item_line_id, "contributing_org_unit": line.contributing_org_unit, "reservation_id": cstr(line.reservation_id),
				"requested_quantity": precision.quantity_text(precision.stored_quantity(line.requested_quantity)), "requested_value": precision.money_text(precision.stored_money(line.requested_value)),
			}
			for line in doc.drawdown_lines
		],
		"items": [{"requisition_item_id": item.requisition_item_id, "drawdown_line_id": item.drawdown_line_id, "quantity": cstr(item.quantity)} for item in package.items],
	}
