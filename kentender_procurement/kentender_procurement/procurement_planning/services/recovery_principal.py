# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.32 §7.8 — who may register or execute a whole-Tender
cancellation recovery in Planning.

The two Planning recovery commands (`register_cancellation_recovery_hold`
and `reverse_requisition_drawdowns_for_cancellation`) are in-process calls
made by the Requisitions recovery coordinator, never web endpoints and never
a personal action: the cancelling Accounting Officer is not a Planning
reader, and the recovery worker runs as a system user. Planning therefore
authenticates the *principal* the caller presents, the way Budget does
(`kentender_budget.services.budget_service_principal`), not the session's role.

A `RecoveryCaller` is a Python object that only `recovery_caller()` can mint,
so it cannot arrive in a web request, and a human session without it is
refused. The mint function is called only from the Requisitions gateway
(`procurement_requisitions/services/eligibility_gateway.py`); a repository
test (`test_cancellation_recovery.py`) fails if any other production file
mints one.
"""

from __future__ import annotations

import frappe
from frappe import _

_MINT = object()


class RecoveryCaller:
	"""An authenticated Requisitions recovery coordinator. Immutable. It names
	the one recovery it acts for, so a coordinator cannot register or reverse
	anything under another recovery's identity."""

	__slots__ = ("recovery_id",)

	def __init__(self, recovery_id: str, _token: object = None):
		if _token is not _MINT:
			raise TypeError("A RecoveryCaller can only be created with recovery_caller()")
		object.__setattr__(self, "recovery_id", recovery_id)

	def __setattr__(self, name, value):
		raise AttributeError("RecoveryCaller is immutable")

	def __repr__(self) -> str:
		return f"RecoveryCaller({self.recovery_id!r})"


def recovery_caller(recovery_id: str) -> RecoveryCaller:
	recovery_id = (recovery_id or "").strip()
	if not recovery_id:
		raise ValueError("A recovery caller must name its recovery")
	return RecoveryCaller(recovery_id, _MINT)


def require_recovery_caller(caller, recovery_id: str) -> RecoveryCaller:
	"""Refuse unless `caller` is a minted `RecoveryCaller` acting for exactly
	`recovery_id`."""
	if not isinstance(caller, RecoveryCaller):
		frappe.throw(_("This Planning action can only be called by the Requisitions recovery service."), frappe.PermissionError)
	if caller.recovery_id != (recovery_id or "").strip():
		frappe.throw(_("This Planning action was called for a different recovery."), frappe.PermissionError)
	return caller
