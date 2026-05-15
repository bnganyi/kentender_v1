# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §11.1 — Supplier Management **adapter** surface for TM2.

Tender services must **not** embed supplier-eligibility business rules outside this module
(doc 8 **TM2-XMOD-SUP-002**). Call :func:`evaluate_supplier_eligibility_for_tender` from
``check_supplier_tender_access`` and other §11 gates.

**Pluggability**

- Optional Frappe hook ``supplier_eligibility_evaluator`` (list of dotted paths). The
  first callable is invoked with keyword-only arguments
  ``tm2_tender``, ``tender_code``, ``supplier``, ``context`` and must return the same
  dict shape as the default implementation.
- Tests may pass ``context["supplier_eligibility_evaluator"]`` as a ``callable`` with the
  same keyword-only contract; it wins over the hook and default.

**Default (bench) behaviour**

- Supplier account flags: ``disabled`` / ``on_hold`` → not eligible (aligned to seed
  **SUP-GAMMA** suspended pattern).
- When **TM2 Tender Access Rule** ``supplier_category_restriction`` defines a non-empty
  ``categories`` list, the supplier's ``supplier_group`` must match one entry (Link name
  equals allowed category label), else category mismatch (**SUP-DELTA** pattern).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, cstr


def _parse_category_restriction(raw: Any) -> list[str]:
	if raw is None:
		return []
	if isinstance(raw, str):
		raw = raw.strip()
		if not raw:
			return []
		try:
			raw = json.loads(raw)
		except json.JSONDecodeError:
			return []
	if not isinstance(raw, dict):
		return []
	cats = raw.get("categories")
	if cats is None:
		cats = raw.get("allowed_categories")
	if not isinstance(cats, list):
		return []
	out: list[str] = []
	for c in cats:
		s = cstr(c).strip()
		if s:
			out.append(s)
	return out


def _default_evaluate_supplier_eligibility_for_tender(
	*,
	tm2_tender: str,
	tender_code: str,
	supplier: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	ctx = dict(context or {})
	checks: list[dict[str, Any]] = [
		{
			"check": "request_context",
			"tender_code": tender_code,
			"context_non_empty": bool(ctx),
			"result": "PASS",
		}
	]
	if not supplier or not frappe.db.exists("Supplier", supplier):
		return {
			"eligible": False,
			"message": _("Supplier was not found in Supplier Management."),
			"checks": checks + [{"check": "supplier_exists", "result": "FAIL"}],
		}

	row = frappe.db.get_value(
		"Supplier",
		supplier,
		["supplier_name", "disabled", "on_hold", "supplier_group"],
		as_dict=True,
	)
	if not row:
		return {
			"eligible": False,
			"message": _("Supplier was not found in Supplier Management."),
			"checks": checks + [{"check": "supplier_exists", "result": "FAIL"}],
		}

	if cint(row.get("disabled")) == 1 or cint(row.get("on_hold")) == 1:
		checks.append({"check": "supplier_operational_status", "result": "FAIL"})
		return {
			"eligible": False,
			"message": _("Supplier status suspended."),
			"checks": checks,
			"supplier_name": cstr(row.get("supplier_name") or "").strip(),
		}
	checks.append({"check": "supplier_operational_status", "result": "PASS"})

	rule = frappe.db.get_value(
		"TM2 Tender Access Rule",
		{"tm2_tender": tm2_tender},
		["supplier_category_restriction"],
		as_dict=True,
	)
	restriction = rule.get("supplier_category_restriction") if rule else None
	allowed = _parse_category_restriction(restriction)
	if allowed:
		sg = cstr(row.get("supplier_group") or "").strip()
		if sg not in allowed:
			checks.append(
				{
					"check": "supplier_category_vs_tender_access_rule",
					"result": "FAIL",
					"supplier_group": sg,
					"allowed_categories": allowed,
				}
			)
			return {
				"eligible": False,
				"message": _("Supplier category does not match tender access restrictions."),
				"checks": checks,
				"supplier_name": cstr(row.get("supplier_name") or "").strip(),
			}
		checks.append({"check": "supplier_category_vs_tender_access_rule", "result": "PASS"})

	return {
		"eligible": True,
		"message": _("Supplier is eligible for this tender."),
		"checks": checks,
		"supplier_name": cstr(row.get("supplier_name") or "").strip(),
	}


def evaluate_supplier_eligibility_for_tender(
	*,
	tm2_tender: str,
	tender_code: str,
	supplier: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Run Supplier Management eligibility for a supplier against a TM2 tender context.

	:returns: ``{"eligible": bool, "message": str, "checks": list, ...}`` — never throws
		for normal validation outcomes.
	"""
	ctx = dict(context or {})
	fn = ctx.get("supplier_eligibility_evaluator")
	if callable(fn):
		out = fn(tm2_tender=tm2_tender, tender_code=tender_code, supplier=supplier, context=ctx)
		return dict(out) if isinstance(out, dict) else {"eligible": False, "message": str(out), "checks": []}

	for path in frappe.get_hooks("supplier_eligibility_evaluator") or []:
		try:
			impl = frappe.get_attr(path)
		except Exception:
			continue
		if not callable(impl):
			continue
		out = impl(tm2_tender=tm2_tender, tender_code=tender_code, supplier=supplier, context=ctx)
		return dict(out) if isinstance(out, dict) else {"eligible": False, "message": str(out), "checks": []}

	return _default_evaluate_supplier_eligibility_for_tender(
		tm2_tender=tm2_tender,
		tender_code=tender_code,
		supplier=supplier,
		context=ctx,
	)


def evaluateSupplierEligibilityForTender(
	*,
	tm2_tender: str,
	tender_code: str,
	supplier: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`evaluate_supplier_eligibility_for_tender`."""
	return evaluate_supplier_eligibility_for_tender(
		tm2_tender=tm2_tender, tender_code=tender_code, supplier=supplier, context=context
	)
