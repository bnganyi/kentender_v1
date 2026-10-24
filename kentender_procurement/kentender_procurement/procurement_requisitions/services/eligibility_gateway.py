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
	# REQ-CHG-001 v1.20 §11.1 — a source held by a cancellation recovery: say which of the two states it is in
	if code == "PLN_CANCELLATION_RECOVERY_PENDING":
		fail("REQ_CANCELLATION_RECOVERY_PENDING", detail=detail)
	if code == "PLN_CANCELLATION_RECOVERY_CONFLICT":
		fail("REQ_CANCELLATION_RECOVERY_INVALID", detail=detail)
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


# --------------------------------------------------------------------------
# REQ-CHG-001 v1.20 §9.1D / §10.3 — whole-Tender cancellation recovery
# --------------------------------------------------------------------------


def _recovery(recovery_id: str):
	"""Planning authenticates the Requisitions recovery coordinator, naming the one recovery it acts for. Only this gateway mints it
	(`test_cancellation_recovery.TestOnlyTheRequisitionsGatewayMintsACaller`)."""
	from kentender_procurement.procurement_planning.services.recovery_principal import recovery_caller

	return recovery_caller(recovery_id)


def _owner_refusal(exc) -> None:
	from kentender_procurement.procurement_requisitions.services.owner_refusal import OwnerRefusal

	code = getattr(exc, "code", "")
	if code in ("PLN_CANCELLATION_RECOVERY_CONFLICT", "PLN_CANCELLATION_RECOVERY_PENDING"):
		raise OwnerRefusal("Planning", "conflict", code, getattr(exc, "detail", None)) from exc
	raise exc


def register_cancellation_recovery_hold(*, recovery_id: str, cancellation_id: str, plan_item_id: str, requisition_reference: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import cancellation_recovery

	try:
		return cancellation_recovery.register_cancellation_recovery_hold(
			caller=_recovery(recovery_id), recovery_id=recovery_id, cancellation_id=cancellation_id, plan_item_id=plan_item_id,
			requisition_reference=requisition_reference, sources=sources,
		)
	except Exception as exc:  # noqa: BLE001 — only Planning's typed refusal is mapped
		_owner_refusal(exc)
	return {}


def reverse_requisition_drawdowns_for_cancellation(*, recovery_id: str, cancellation_id: str, plan_item_id: str, requisition_reference: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
	"""The cancellation mode of `ReverseRequisitionDrawdown`: the exact originating draws, once, in the recovery transaction. Never commits."""
	from kentender_procurement.procurement_planning.services import cancellation_recovery

	try:
		return cancellation_recovery.reverse_requisition_drawdowns_for_cancellation(
			caller=_recovery(recovery_id), recovery_id=recovery_id, cancellation_id=cancellation_id, plan_item_id=plan_item_id,
			requisition_reference=requisition_reference, sources=sources,
		)
	except Exception as exc:  # noqa: BLE001
		_owner_refusal(exc)
	return {}


def drawdown_facts(*, recovery_id: str, drawdown_references: list[str]) -> list[dict[str, Any]]:
	"""Planning's account of the originating drawdowns (existence, state, why and by which recovery reversed, exact quantity and value, held or not).
	Read-only; used to classify a Tender cancelled before the recovery existed."""
	from kentender_procurement.procurement_planning.services import recovery_facts

	return recovery_facts.drawdown_facts(caller=_recovery(recovery_id), recovery_id=recovery_id, drawdown_references=drawdown_references)


def set_cancellation_recovery_status(*, recovery_id: str, plan_item_id: str, status: str, reason: str = "") -> dict[str, Any]:
	"""Tell Planning which unresolved state the recovery is in, so a refused authorisation can say Pending or Needs attention."""
	from kentender_procurement.procurement_planning.services import cancellation_recovery

	return cancellation_recovery.set_cancellation_recovery_status(
		caller=_recovery(recovery_id), recovery_id=recovery_id, plan_item_id=plan_item_id, status=status, reason=reason,
	)
