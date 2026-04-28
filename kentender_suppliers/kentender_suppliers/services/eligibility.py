# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

from __future__ import annotations

import json
import typing

import frappe
from frappe.utils import getdate, today

from kentender_suppliers.services import constants as c
from kentender_suppliers.services.compliance import recompute_compliance

if typing.TYPE_CHECKING:
	pass

import time

_CACHE: dict = {}
_TTL_S = 300


def _cache_get(key: str) -> dict | None:
	if key not in _CACHE:
		return None
	t, v = _CACHE[key]
	if time.time() - t > _TTL_S:
		del _CACHE[key]
		return None
	return v


def _cache_set(key: str, val: dict) -> None:
	_CACHE[key] = (time.time(), val)


def get_profile_name_for_supplier_code(supplier_code: str) -> str | None:
	"""Resolve KTSM Supplier Profile name from business `kentender_supplier_code` on Supplier."""
	if not (supplier_code or "").strip():
		return None
	if not frappe.db.has_column("Supplier", "kentender_supplier_code"):
		return None
	erp = frappe.db.get_value("Supplier", {"kentender_supplier_code": supplier_code}, "name")
	if not erp:
		return None
	return frappe.db.get_value("KTSM Supplier Profile", {"erpnext_supplier": erp}, "name")


def _access_blockers(profile: str) -> list[dict[str, str]]:
	"""If external access grants exist and are all revoked for primary user, block (optional in v1)."""
	out: list[dict[str, str]] = []
	rows = frappe.get_all(
		"KTSM Supplier API Access",
		filters={"supplier_profile": profile},
		fields=["access_status", "name"],
		limit=1,
	)
	if rows and rows[0].access_status in ("Revoked", "Suspended"):
		return [{"code": c.ACCESS_REVOKED, "message": c.HUMAN[c.ACCESS_REVOKED]}]
	return out


@frappe.whitelist(allow_guest=False)
def check_supplier_eligibility(
	supplier_code: str,
	category_code: str | None = None,
	context: dict | None = None,
) -> dict:
	"""D1 — eligibility with multi-reason (contract §5–9). `context` reserved."""
	return _eligibility(supplier_code, category_code)


@frappe.whitelist(allow_guest=False)
def check_multiple_suppliers(
	supplier_codes: list, category_code: str | None = None
) -> list[dict]:
	"""D2: batch; each item same shape as single call."""
	if isinstance(supplier_codes, str):
		supplier_codes = json.loads(supplier_codes)
	out: list[dict] = []
	for sc in supplier_codes:
		out.append(_eligibility(sc, category_code))
	return out


def _eligibility(supplier_code: str, category_code: str | None) -> dict:
	ck = f"{supplier_code!s}|{category_code!s}"
	cached = _cache_get(ck)
	if cached:
		return cached

	profile = get_profile_name_for_supplier_code(supplier_code)
	reasons: list[dict[str, str]] = []
	if not profile:
		return {
			"supplier_code": supplier_code,
			"eligible": False,
			"reasons": [{"code": c.NOT_ACTIVE, "message": "Unknown supplier code"}],
		}

	p = frappe.get_doc("KTSM Supplier Profile", profile)
	erp = p.erpnext_supplier
	approval = p.approval_status
	ops = p.operational_status
	comp = recompute_compliance(profile)  # recompute to avoid stale
	cat_st = _category_state(profile, category_code) if category_code else None

	if approval != "Approved":
		reasons.append({"code": c.NOT_APPROVED, "message": c.HUMAN[c.NOT_APPROVED]})
	if ops == "Pending":
		reasons.append({"code": c.NOT_ACTIVE, "message": c.HUMAN[c.NOT_ACTIVE]})
	if ops == "Suspended":
		reasons.append({"code": c.SUSPENDED, "message": c.HUMAN[c.SUSPENDED]})
	if ops == "Blacklisted":
		reasons.append({"code": c.BLACKLISTED, "message": c.HUMAN[c.BLACKLISTED]})
	if ops == "Expired":
		reasons.append({"code": c.EXPIRED, "message": c.HUMAN[c.EXPIRED]})

	if comp in ("Incomplete", "Unknown"):
		reasons.append(
			{"code": c.COMPLIANCE_INCOMPLETE, "message": c.HUMAN[c.COMPLIANCE_INCOMPLETE]}
		)
	if comp == "Expired":
		reasons.append(
			{"code": c.COMPLIANCE_EXPIRED, "message": c.HUMAN[c.COMPLIANCE_EXPIRED]}
		)
	if comp == "Non-Compliant":
		reasons.append(
			{"code": c.NON_COMPLIANT, "message": c.HUMAN[c.NON_COMPLIANT]}
		)

	if category_code and cat_st is not None:
		reasons.extend(_category_blockers(profile, category_code, cat_st))
	elif category_code and cat_st is None:
		reasons.append(
			{
				"code": c.CATEGORY_NOT_ASSIGNED,
				"message": c.HUMAN[c.CATEGORY_NOT_ASSIGNED],
			}
		)

	reasons.extend(_access_blockers(profile))

	eligible = len(reasons) == 0
	res = _finish(supplier_code, approval, ops, comp, cat_st, p.risk_level, eligible, reasons)
	_cache_set(ck, res)
	return res


def _category_state(profile: str, category_code: str) -> dict | None:
	cn = frappe.db.get_value("KTSM Supplier Category", {"category_code": category_code}, "name")
	if not cn:
		return None
	row = frappe.db.get_value(
		"KTSM Category Assignment",
		{"supplier_profile": profile, "category": cn},
		["qualification_status", "qualified_until", "name"],
		as_dict=True,
	)
	return row


def _category_blockers(
	profile: str, category_code: str, state: dict
) -> list[dict[str, str]]:
	"""State row exists; evaluate qualification and dates."""
	out: list[dict[str, str]] = []
	st = state.get("qualification_status")
	if st in (None, "Requested", "Under Review"):
		return [{"code": c.CATEGORY_NOT_QUALIFIED, "message": c.HUMAN[c.CATEGORY_NOT_QUALIFIED]}]
	if st == "Rejected":
		return [{"code": c.CATEGORY_REJECTED, "message": c.HUMAN[c.CATEGORY_REJECTED]}]
	if st == "Expired":
		return [{"code": c.CATEGORY_EXPIRED, "message": c.HUMAN[c.CATEGORY_EXPIRED]}]
	if st == "Qualified" and state.get("qualified_until"):
		if getdate(state.get("qualified_until")) < getdate(today()):
			return [{"code": c.CATEGORY_EXPIRED, "message": c.HUMAN[c.CATEGORY_EXPIRED]}]
	if st == "Qualified":
		return []
	return [{"code": c.CATEGORY_NOT_QUALIFIED, "message": c.HUMAN[c.CATEGORY_NOT_QUALIFIED]}]


def _finish(supplier_code, approval, ops, comp, cat_st, risk, eligible, reasons):
	seen: set = set()
	uniq: list[dict] = []
	for r in reasons:
		if r["code"] in seen:
			continue
		seen.add(r["code"])
		uniq.append(r)
	out = {
		"supplier_code": supplier_code,
		"eligible": bool(eligible),
		"approval_status": approval,
		"operational_status": ops,
		"compliance_status": comp,
		"risk_level": risk,
		"reasons": uniq,
	}
	if cat_st is not None:
		cn = None
		if cat_st and isinstance(cat_st, dict) and (cat_st.get("name") or ""):
			cn = frappe.db.get_value("KTSM Category Assignment", cat_st.get("name"), "category")
		if cn:
			out["category_code"] = frappe.db.get_value("KTSM Supplier Category", cn, "category_code")
		out["category_status"] = cat_st
	return out


# Call from governance when status changes
def bust_eligibility_cache(supplier_profile: str) -> None:
	_CACHE.clear()
