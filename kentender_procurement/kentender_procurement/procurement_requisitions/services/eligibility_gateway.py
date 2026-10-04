# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §9.1 — the Procurement Planning provider contracts.

Requisitions calls only Planning's published `plan_requisition` service and
never reads Planning tables (AGENTS.md §2). Calls run as the acting user, so
Planning's own gates judge the same actor REQ already authorised. Planning's
`PLN_ITEM_AUTHORISATION_HELD` and `PLN_ITEM_SCOPE_LOCKED` pass through with
Planning's exact code and message (§11); an allowance overrun is REQ's
`REQ_BALANCE_CHANGED`; any other owner failure is
`REQ_OWNER_VALIDATION_UNAVAILABLE`, committing nothing.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_requisitions.services.errors import fail

_PASS_THROUGH = ("PLN_ITEM_AUTHORISATION_HELD", "PLN_ITEM_SCOPE_LOCKED")
_BALANCE = ("PLN_ALLOWANCE_EXCEEDED",)
_PRECISION = ("PLN_MONEY_PRECISION_INVALID",)


def _planning():
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition


def _mapped(exc: Exception) -> None:
	code = getattr(exc, "code", "")
	detail = {"planning_code": code, **(getattr(exc, "detail", None) or {})}
	if code in _PASS_THROUGH:
		fail(code, detail=detail)
	if code in _BALANCE:
		fail("REQ_BALANCE_CHANGED", detail=detail)
	if code in _PRECISION:
		fail("REQ_MONEY_PRECISION_INVALID", detail=detail)
	if isinstance(exc, frappe.DoesNotExistError):
		raise exc
	fail("REQ_OWNER_VALIDATION_UNAVAILABLE", detail={**detail, "planning_message": str(exc)})


def get_requisition_eligible_plan_item(plan_item_id: str) -> dict[str, Any]:
	return _planning().get_requisition_eligible_plan_item(plan_item_id=plan_item_id)


def list_requisition_eligible_plan_items() -> list[dict[str, Any]]:
	return _planning().list_requisition_eligible_plan_items()


def authorise_requisition_drawdown(*, plan_item_id: str, requisition_reference: str, requisition_version: str, correlation_id: str, allocations: list[dict[str, Any]], expected_record_version, idempotency_key: str) -> dict[str, Any]:
	try:
		return _planning().authorise_requisition_drawdown(
			plan_item_id=plan_item_id, requisition_reference=requisition_reference, requisition_version=requisition_version,
			correlation_id=correlation_id, allocations=allocations, expected_record_version=expected_record_version, idempotency_key=idempotency_key,
		)
	except Exception as exc:  # noqa: BLE001 — every owner failure is mapped onto §11
		_mapped(exc)
	return {}


def list_requisition_drawdowns(requisition_reference: str) -> list[dict[str, Any]]:
	return _planning().list_requisition_drawdowns(requisition_reference=requisition_reference)


def reverse_requisition_drawdown(*, drawdown_reference: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	try:
		return _planning().reverse_requisition_drawdown(drawdown_reference=drawdown_reference, expected_record_version=expected_record_version, idempotency_key=idempotency_key)
	except Exception as exc:  # noqa: BLE001
		_mapped(exc)
	return {}


def receive_plan_item_correction_request(*, plan_item_id: str, requisition_reference: str, requisition_version: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	try:
		return _planning().receive_plan_item_correction_request(
			plan_item_id=plan_item_id, requisition_reference=requisition_reference, requisition_version=requisition_version, reason=reason, idempotency_key=idempotency_key,
		)
	except frappe.DoesNotExistError:
		raise
	except Exception as exc:  # noqa: BLE001
		_mapped(exc)
	return {}


def correction_request_facts(*, correction_request: str = "", requisition_reference: str = "") -> list[dict[str, Any]]:
	return _planning().correction_request_facts(correction_request=correction_request, requisition_reference=requisition_reference)
