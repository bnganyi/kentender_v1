# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §18.7 — supplier portal bid submission (wraps :func:`submit_bid.submit_bid`).

**EX-07** (doc 9 §25): evaluation-stage arithmetic / correction fields are rejected before seal;
see ``test_EX_07_*`` in ``tender_management.tests.test_p10_07_supplier_portal_submit_bid``.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.check_supplier_tender_access import (
	check_supplier_tender_access,
)
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.services.supplier_portal_tender_list import (
	resolve_erpnext_supplier_for_portal_user,
)


def submit_supplier_portal_bid(
	actor: str,
	tender_code: str,
	bid_payload: dict[str, Any] | None,
) -> dict[str, Any]:
	"""Validate portal identity + tender access, then delegate to :func:`submit_bid`."""
	tc = cstr(tender_code or "").strip()
	if not tc:
		return {"ok": False, "message": _("Tender code is required.")}

	supplier = resolve_erpnext_supplier_for_portal_user(actor)
	if not supplier:
		return {"ok": False, "message": _("No supplier profile is linked to this account.")}

	gate = check_supplier_tender_access(actor, tc, supplier, context={})
	if not gate.get("ok"):
		return {
			"ok": False,
			"message": cstr(gate.get("message") or "").strip() or _("This tender is not available."),
		}

	spec = spec_for_action("BID2_SUBMIT")
	ctx: dict[str, Any] = {"acting_supplier": supplier}
	if spec:
		ctx["granted_permissions"] = [spec.required_permission]

	return submit_bid(actor, tc, supplier, dict(bid_payload or {}), context=ctx)


def submitSupplierPortalBid(
	actor: str,
	tender_code: str,
	bid_payload: dict[str, Any] | None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`submit_supplier_portal_bid`."""
	return submit_supplier_portal_bid(actor, tender_code, bid_payload)
