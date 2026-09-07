# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §9.1 — the Procurement Planning contracts, under the
spec's verbs. Requisitions calls only Planning's *published* `plan_requisition`
service module and never reads Planning's own tables directly (AGENTS.md §2:
cross-app/cross-module interaction uses the owner's published service).

Unlike Planning's own `budget_gateway.py` (which elevates to a system
principal for departmental/planner reads Budget's own gate would otherwise
refuse), no elevation happens here: Planning's read and drawdown gates are
themselves now resolved against the real acting Requisitions user (Head of
User Department / Head of Procurement Function / etc., per REQ-103's
`_authorise_requisition_reader`/`_authorise_requisition_authoriser` on the
Planning side) — the same actor Requisitions' own command layer already
authorised. Calling through as that same session, rather than as
Administrator, is what lets Planning's own gate do its job (AGENTS.md §4.3:
"never rely on ... client checks for authorization").
"""

from __future__ import annotations

from typing import Any


def get_requisition_eligible_plan_item(plan_item_id: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.get_requisition_eligible_plan_item(plan_item_id=plan_item_id)


def list_requisition_eligible_plan_items() -> list[dict[str, Any]]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.list_requisition_eligible_plan_items()


def record_requisition_drawdown(
	*,
	plan_item_id: str,
	requisition_reference: str,
	requesting_org_unit: str,
	allocations: list[dict[str, Any]],
	expected_record_version,
	idempotency_key: str,
) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.record_requisition_drawdown(
		plan_item_id=plan_item_id, requisition_reference=requisition_reference,
		requesting_org_unit=requesting_org_unit, allocations=allocations,
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


def reverse_requisition_drawdown(*, drawdown_reference: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.reverse_requisition_drawdown(
		drawdown_reference=drawdown_reference, expected_record_version=expected_record_version,
		idempotency_key=idempotency_key,
	)


def receive_plan_item_correction_request(
	*, plan_item_id: str, requisition_reference: str, requisition_version: str, reason: str, idempotency_key: str,
) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.receive_plan_item_correction_request(
		plan_item_id=plan_item_id, requisition_reference=requisition_reference,
		requisition_version=requisition_version, reason=reason, idempotency_key=idempotency_key,
	)
