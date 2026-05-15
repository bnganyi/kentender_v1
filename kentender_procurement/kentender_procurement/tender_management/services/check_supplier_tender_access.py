# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §11.1 — ``check_supplier_tender_access`` (supplier eligibility gate).

Resolves the **TM2 Tender** from ``tender_code``, resolves the **Supplier** document from
``supplier_code`` (Supplier name or participation-scoped ref), then delegates eligibility
to :func:`~kentender_procurement.tender_management.services.supplier_management_adapter.evaluate_supplier_eligibility_for_tender`.

When the adapter reports **not eligible**, the service denies with ``AUTH_SUPPLIER_INELIGIBLE``
(doc 8 **TM2-XMOD-SUP-001**).

Tests: ``tender_management.tests.test_p6_01_check_supplier_tender_access``;
``tender_management.tests.test_p6_03_validate_bid_submission_against_dsm`` (resolvers).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.supplier_management_adapter import (
	evaluate_supplier_eligibility_for_tender,
)


def _resolve_tm2(tender_code: str) -> Document | None:
	tc = (tender_code or "").strip()
	if not tc:
		return None
	name = frappe.db.get_value("TM2 Tender", {"tender_code": tc}, "name")
	if name and frappe.db.exists("TM2 Tender", name):
		return frappe.get_doc("TM2 Tender", name)
	if frappe.db.exists("TM2 Tender", tc):
		return frappe.get_doc("TM2 Tender", tc)
	return None


def _resolve_supplier_name(tm2_name: str, tender_code: str, supplier_ref: str) -> str | None:
	ref = cstr(supplier_ref).strip()
	if not ref:
		return None
	if frappe.db.exists("Supplier", ref):
		return ref
	part = frappe.db.get_value(
		"TM2 Supplier Participation",
		{"tm2_tender": tm2_name, "supplier": ref},
		"supplier",
	)
	if part:
		return str(part)
	part2 = frappe.db.get_value(
		"TM2 Supplier Participation",
		{"tender_code": tender_code, "supplier_code": ref},
		"supplier",
	)
	if part2:
		return str(part2)
	return None


def check_supplier_tender_access(
	actor: str,
	tender_code: str,
	supplier_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §11.1 — supplier eligibility for TM2 tender access (adapter-backed)."""
	ctx = dict(context or ())
	ctx.setdefault("eligibility_requesting_actor", actor)
	tm2 = _resolve_tm2(tender_code)
	if not tm2:
		return {
			"ok": False,
			"denial_code": DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			"message": _("TM2 Tender {0} was not found.").format(cstr(tender_code).strip()),
			"actor": actor,
		}

	tc = cstr(tm2.tender_code).strip() or tm2.name
	supplier_name = _resolve_supplier_name(tm2.name, tc, supplier_code)
	if not supplier_name:
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_CONTEXT_DENIED.value,
			"message": _("Supplier could not be resolved for this tender."),
			"actor": actor,
		}

	eval_out = evaluate_supplier_eligibility_for_tender(
		tm2_tender=tm2.name,
		tender_code=tc,
		supplier=supplier_name,
		context=ctx,
	)
	if not bool(eval_out.get("eligible")):
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_SUPPLIER_INELIGIBLE.value,
			"message": cstr(eval_out.get("message") or _("Supplier is not eligible for this tender.")).strip()
			or _("Supplier is not eligible for this tender."),
			"supplier": supplier_name,
			"eligibility": eval_out,
			"actor": actor,
		}

	return {
		"ok": True,
		"tender_code": tc,
		"tm2_tender": tm2.name,
		"supplier": supplier_name,
		"eligibility": eval_out,
		"actor": actor,
	}


def resolve_tm2_tender_document(tender_code: str) -> Document | None:
	"""Resolve ``TM2 Tender`` by business ``tender_code`` or row name (shared §11.x helper)."""
	return _resolve_tm2(tender_code)


def resolve_supplier_for_tm2_participation(tm2_name: str, tender_code: str, supplier_ref: str) -> str | None:
	"""Resolve ``Supplier`` document name for ``supplier_ref`` on ``tm2_name`` (shared §11.x helper)."""
	return _resolve_supplier_name(tm2_name, tender_code, supplier_ref)


def checkSupplierTenderAccess(
	actor: str,
	tender_code: str,
	supplier_code: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`check_supplier_tender_access`."""
	return check_supplier_tender_access(actor, tender_code, supplier_code, context=context)
