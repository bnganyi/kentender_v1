# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §11.7 — ``get_bid_content`` / ``getBidContent`` (sealed bid access guard).

Before the tender reaches a post-opening lifecycle state, **desk** actors (no valid supplier
delegation for the bid) must always be denied sealed bid disclosure, including **Administrator**,
with ``AUTH_SEALED_BID_DENIED`` and an append-only **Access Denied** audit on **TM2 Tender Audit
Event** (doc 8 TM2-SMOKE-SEAL-001/002).

Supplier portal actors (``context["acting_supplier"]`` matching the bid's supplier and passing
:func:`~kentender_procurement.tender_management.services.check_supplier_tender_access.check_supplier_tender_access`)
receive a **metadata-only** envelope (hash, totals, component summaries) without sealed bodies.

After post-opening, desk access requires **BID2_VIEW_SEALED_CONTENT** via
:func:`~kentender_procurement.tender_management.security.action_availability.service.get_action_availability`
(``object_type`` **TM2 Tender**, ``object_code`` tender business code).

Tests: ``tender_management.tests.test_p6_07_get_bid_content`` (``test_EX_11_*``, ``test_EX_12_*`` / doc 9 §25 **EX-11** / **EX-12**);
``tender_management.tests.test_o09_tm2_smoke_seal_001_internal_cannot_view_sealed_bid_before_opening`` (O-09 / doc 8 TM2-SMOKE-SEAL-001);
``tender_management.tests.test_o10_tm2_smoke_seal_002_sysadmin_cannot_bypass_sealed_bid_protection`` (O-10 / doc 8 TM2-SMOKE-SEAL-002).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

from kentender_procurement.tender_management.security.action_availability.access_denied_audit import (
	audit_access_denied,
)
from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.append_tender_audit_event import (
	append_tender_audit_event,
)
from kentender_procurement.tender_management.services.check_supplier_tender_access import (
	check_supplier_tender_access,
)

_ACTION_SEALED = "BID2_VIEW_SEALED_CONTENT"
_OBJECT_TYPE = "TM2 Tender"

# TM2 Tender statuses where lawful opening has completed (§11.7 post-opening corridor).
_POST_OPENING_TM2_STATUSES: frozenset[str] = frozenset(
	{
		"Opening Completed",
		"Evaluation Ready",
		"Evaluation In Progress",
		"Awarded",
		"Contract Handoff Completed",
	}
)


def _deny(denial_code: str, message: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "denial_code": denial_code, "message": message}
	if extra:
		out.update(extra)
	return out


def _map_auth_denial(denial_code: str) -> str:
	if denial_code == DenialCode.STD_AUTH_PERMISSION_DENIED.value:
		return DenialCode.AUTH_ROLE_DENIED.value
	return denial_code


def _resolve_bid(bid_code: str) -> Document | None:
	bc = cstr(bid_code).strip()
	if not bc:
		return None
	if frappe.db.exists("TM2 Bid Submission", bc):
		return frappe.get_doc("TM2 Bid Submission", bc)
	nm = frappe.db.get_value("TM2 Bid Submission", {"bid_code": bc}, "name")
	if nm and frappe.db.exists("TM2 Bid Submission", nm):
		return frappe.get_doc("TM2 Bid Submission", nm)
	return None


def _is_supplier_portal_own_bid(actor: str, bid: Document, context: dict[str, Any]) -> bool:
	acting = cstr(context.get("acting_supplier") or "").strip()
	if not acting or acting != cstr(bid.supplier).strip():
		return False
	tc = cstr(bid.tender_code).strip() or bid.tm2_tender
	elig = check_supplier_tender_access(actor, tc, acting, context=context)
	return bool(elig.get("ok"))


def _components_summary(bid_docname: str) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for row in frappe.get_all(
		"TM2 Bid Submission Component",
		filters={"tm2_bid_submission": bid_docname},
		fields=[
			"name",
			"std_submission_requirement_code",
			"component_type",
			"component_label",
			"validation_status",
		],
	):
		out.append(
			{
				"std_submission_requirement_code": row.get("std_submission_requirement_code"),
				"component_type": row.get("component_type"),
				"component_label": row.get("component_label"),
				"validation_status": row.get("validation_status"),
			}
		)
	return out


def _metadata_envelope(bid: Document) -> dict[str, Any]:
	return {
		"bid_code": bid.bid_code,
		"tm2_tender": bid.tm2_tender,
		"tender_code": bid.tender_code,
		"supplier": bid.supplier,
		"bid_status": bid.bid_status,
		"submission_hash": bid.submission_hash,
		"total_submitted_price": bid.total_submitted_price,
		"currency": bid.currency,
		"dsm_output_code": bid.dsm_output_code,
		"tender_std_instance_code": bid.tender_std_instance_code,
		"publication_snapshot_code": bid.publication_snapshot_code,
		"components": _components_summary(bid.name),
	}


def get_bid_content(actor: str, bid_code: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
	"""§11.7 — sealed bid access guard + metadata envelope for permitted supplier portal reads."""
	ctx = dict(context or {})
	bid = _resolve_bid(bid_code)
	if not bid:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Bid Submission {0} was not found.").format(cstr(bid_code).strip()),
		)

	tc = cstr(bid.tender_code).strip() or bid.tm2_tender
	tm2_status = cstr(
		frappe.db.get_value("TM2 Tender", bid.tm2_tender, "status") or ""
	).strip()
	post_opening = tm2_status in _POST_OPENING_TM2_STATUSES

	acting = cstr(ctx.get("acting_supplier") or "").strip()
	if acting and acting != cstr(bid.supplier).strip():
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("You cannot access another supplier's bid submission."),
			extra={"bid_code": bid.bid_code},
		)

	if _is_supplier_portal_own_bid(actor, bid, ctx):
		return {
			"ok": True,
			"actor": actor,
			"access_tier": "metadata",
			"lawful_opening": post_opening,
			"bid_submission": bid.name,
			**_metadata_envelope(bid),
		}

	# Desk / non-delegated path
	if not post_opening:
		append_tender_audit_event(
			tc,
			"Access Denied",
			actor,
			{
				"bid_code": bid.bid_code,
				"reason": "Sealed bid content is not available to desk users before lawful opening.",
			},
			related_object_type="TM2 Bid Submission",
			related_object_code=bid.name,
			denial_code=DenialCode.AUTH_SEALED_BID_DENIED.value,
			enforce_section_13_2=False,
		)
		return _deny(
			DenialCode.AUTH_SEALED_BID_DENIED.value,
			_("Sealed bid content is not available before lawful opening."),
			extra={"bid_code": bid.bid_code, "tender_status": tm2_status},
		)

	avail = get_action_availability(
		_ACTION_SEALED,
		_OBJECT_TYPE,
		tc,
		actor,
		context={**ctx, "object_exists": True},
	)
	if not avail.get("allowed"):
		dc = _map_auth_denial(str(avail.get("denial_code") or ""))
		audit_access_denied(
			actor,
			tc,
			avail,
			payload={
				"object_type": _OBJECT_TYPE,
				"tender_code": tc,
				"bid_code": bid.bid_code,
			},
		)
		return _deny(
			dc,
			str(avail.get("user_message") or avail.get("message") or dc),
			extra={"availability": avail, "bid_code": bid.bid_code},
		)

	return {
		"ok": True,
		"actor": actor,
		"access_tier": "metadata",
		"lawful_opening": True,
		"bid_submission": bid.name,
		**_metadata_envelope(bid),
	}


def getBidContent(actor: str, bid_code: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
	"""CamelCase alias for :func:`get_bid_content`."""
	return get_bid_content(actor, bid_code, context=context)
