# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import json

import frappe

from kentender_suppliers.api import smw_workflow


_OWNERSHIP_QUEUES = frozenset({"my_work", "all", "approved", "blocked"})
_STATE_QUEUES = frozenset(
	{
		"draft",
		"submitted",
		"under_review",
		"returned",
		"active",
		"suspended",
		"blacklisted",
		"expired",
	}
)
@frappe.whitelist()
def get_landing() -> dict:
	"""Workbench shell payload: KPI, queue counters, and filter metadata."""
	dt = "KTSM Supplier Profile"
	category_rows = frappe.get_all(
		"KTSM Supplier Category",
		filters={"is_active": 1},
		fields=["category_code", "category_name"],
		order_by="category_name asc",
	)
	return {
		"ok": True,
		"kpis": {
			"registered": frappe.db.count(dt),
			"pending_review": frappe.db.count(
				dt,
				{"approval_status": ("in", ("Submitted", "Under Review"))},
			),
			"active": frappe.db.count(
				dt,
				{"operational_status": "Active", "approval_status": "Approved"},
			),
			"blocked": frappe.db.count(
				dt,
				{
					"operational_status": (
						"in",
						("Suspended", "Blacklisted"),
					)
				},
			),
		},
		"queues": {
			"approval_draft": frappe.db.count(dt, {"approval_status": "Draft"}),
			"approval_submitted": frappe.db.count(dt, {"approval_status": "Submitted"}),
			"approval_in_review": frappe.db.count(
				dt, {"approval_status": "Under Review"}
			),
			"approval_returned": frappe.db.count(dt, {"approval_status": "Returned"}),
			"compliance_incomplete": frappe.db.count(
				dt, {"compliance_status": "Incomplete"}
			),
		},
		"queue_defs": {
			"ownership": list(_OWNERSHIP_QUEUES),
			"state": list(_STATE_QUEUES),
		},
		"filter_meta": {
			"category_codes": [
				{
					"id": c.get("category_code"),
					"label": f"{c.get('category_name')} ({c.get('category_code')})",
				}
				for c in (category_rows or [])
				if c.get("category_code") and c.get("category_name")
			],
			"compliance_status": ["Unknown", "Complete", "Incomplete", "Expired", "Non-Compliant"],
			"risk_level": ["Low", "Medium", "High"],
		},
	}


def _parse_filters(filters: str | dict | None) -> dict:
	if not filters:
		return {}
	if isinstance(filters, dict):
		return filters
	if isinstance(filters, str):
		try:
			obj = json.loads(filters)
			return obj if isinstance(obj, dict) else {}
		except Exception:
			return {}
	return {}


def _profile_filters(filters: dict) -> dict:
	out = {}
	kpi = (filters.get("kpi") or "").strip()
	if kpi == "pending_review":
		out["approval_status"] = ("in", ("Submitted", "Under Review"))
	elif kpi == "active":
		out["approval_status"] = "Approved"
		out["operational_status"] = "Active"
	elif kpi == "blocked":
		out["operational_status"] = ("in", ("Suspended", "Blacklisted"))

	ownership = (filters.get("ownership_queue") or "").strip()
	if ownership == "approved":
		out["approval_status"] = "Approved"
	elif ownership == "blocked":
		out["operational_status"] = ("in", ("Suspended", "Blacklisted"))
	elif ownership == "my_work":
		out["submitted_by"] = frappe.session.user

	state = (filters.get("state_queue") or "").strip()
	if state == "draft":
		out["approval_status"] = "Draft"
	elif state == "submitted":
		out["approval_status"] = "Submitted"
	elif state == "under_review":
		out["approval_status"] = "Under Review"
	elif state == "returned":
		out["approval_status"] = "Returned"
	elif state == "active":
		out["operational_status"] = "Active"
	elif state == "suspended":
		out["operational_status"] = "Suspended"
	elif state == "blacklisted":
		out["operational_status"] = "Blacklisted"
	elif state == "expired":
		out["operational_status"] = "Expired"

	compliance_status = (filters.get("compliance_status") or "").strip()
	if compliance_status:
		out["compliance_status"] = compliance_status
	risk_level = (filters.get("risk_level") or "").strip()
	if risk_level:
		out["risk_level"] = risk_level
	return out


def _code_for_profile(profile_name: str) -> str:
	erp = frappe.db.get_value("KTSM Supplier Profile", profile_name, "erpnext_supplier")
	if not erp:
		return ""
	return frappe.db.get_value("Supplier", erp, "kentender_supplier_code") or ""


@frappe.whitelist()
def get_suppliers(filters: str | dict | None = None) -> dict:
	"""Filterable list payload for left workbench panel."""
	fx = _parse_filters(filters)
	db_filters = _profile_filters(fx)
	rows = frappe.get_all(
		"KTSM Supplier Profile",
		filters=db_filters,
		fields=[
			"name",
			"identity_display",
			"approval_status",
			"operational_status",
			"compliance_status",
			"risk_level",
			"modified",
		],
		order_by="modified desc",
		limit=max(1, min(int(fx.get("limit") or 50), 200)),
	)

	profile_names = [r.get("name") for r in (rows or []) if r.get("name")]
	category_by_profile: dict[str, list[str]] = {}
	if profile_names:
		assigned = frappe.get_all(
			"KTSM Category Assignment",
			filters={"supplier_profile": ("in", profile_names)},
			fields=["supplier_profile", "category", "qualification_status"],
		)
		category_names = list({a.get("category") for a in (assigned or []) if a.get("category")})
		cat_meta = {}
		if category_names:
			for c in frappe.get_all(
				"KTSM Supplier Category",
				filters={"name": ("in", category_names)},
				fields=["name", "category_code", "category_name"],
			):
				cat_meta[c.get("name")] = c
		for a in (assigned or []):
			c = cat_meta.get(a.get("category"))
			if not c:
				continue
			item = f"{c.get('category_name')} ({c.get('category_code')})"
			category_by_profile.setdefault(a.get("supplier_profile"), []).append(item)

	q = (fx.get("q") or "").strip().lower()
	out = []
	for r in rows or []:
		supplier_code = _code_for_profile(r.get("name"))
		supplier_name = r.get("identity_display") or supplier_code or "Supplier"
		if q:
			hay = " ".join(
				[
					(supplier_code or "").lower(),
					(supplier_name or "").lower(),
					" ".join(category_by_profile.get(r.get("name"), [])).lower(),
				]
			)
			if q not in hay:
				continue
		out.append(
			{
				"supplier_code": supplier_code,
				"supplier_name": supplier_name,
				"approval_status": r.get("approval_status"),
				"operational_status": r.get("operational_status"),
				"compliance_status": r.get("compliance_status"),
				"risk_level": r.get("risk_level"),
				"categories": category_by_profile.get(r.get("name"), []),
				"last_updated": r.get("modified"),
			}
		)
	return {"ok": True, "rows": out}


def _resolve_profile_name_by_code(supplier_code: str) -> str | None:
	erp = frappe.db.get_value("Supplier", {"kentender_supplier_code": supplier_code}, "name")
	if not erp:
		return None
	return frappe.db.get_value("KTSM Supplier Profile", {"erpnext_supplier": erp}, "name")


def _supplier_group() -> str | None:
	sg = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")
	if not sg:
		sg = frappe.db.get_value("Supplier Group", {}, "name")
	return sg


def _next_supplier_code() -> str:
	yr = frappe.utils.now_datetime().strftime("%Y")
	prefix = f"SUP-KE-{yr}-"
	rows = frappe.get_all(
		"Supplier",
		filters={"kentender_supplier_code": ("like", f"{prefix}%")},
		pluck="kentender_supplier_code",
	)
	mx = 0
	for r in rows or []:
		parts = (r or "").rsplit("-", 1)
		if len(parts) == 2 and parts[-1].isdigit():
			mx = max(mx, int(parts[-1]))
	return f"{prefix}{str(mx + 1).zfill(4)}"


def _assert_registry_access() -> None:
	roles = set(frappe.get_roles())
	if roles & {
		"System Manager",
		"Administrator",
		"KenTender Supplier Registry Officer",
		"KenTender Compliance Officer",
		"KenTender Approving Authority",
		"Procurement Officer",
		"Procurement Planner",
		"Planning Authority",
	}:
		return
	frappe.throw("Not permitted for supplier builder operations.")


def _action_defs(approval_status: str, operational_status: str, compliance_status: str, docs_missing: bool) -> list[dict]:
	approval = (approval_status or "").strip()
	ops = (operational_status or "").strip()
	is_blocked = compliance_status in ("Incomplete", "Expired", "Non-Compliant") or docs_missing
	if approval == "Draft":
		return [{"id": "submit", "label": "Submit", "disabled": bool(is_blocked)}]
	if approval == "Submitted":
		return [
			{"id": "start_review", "label": "Start Review", "disabled": False},
			{"id": "approve", "label": "Approve", "disabled": bool(is_blocked)},
			{"id": "return", "label": "Return", "disabled": False},
			{"id": "reject", "label": "Reject", "disabled": False},
		]
	if approval == "Under Review":
		return [
			{"id": "approve", "label": "Approve", "disabled": bool(is_blocked)},
			{"id": "return", "label": "Return", "disabled": False},
		]
	if approval == "Returned":
		return [{"id": "edit", "label": "Edit", "disabled": False}]
	if approval == "Approved" and ops == "Active":
		return [
			{"id": "suspend", "label": "Suspend", "disabled": False},
			{"id": "blacklist", "label": "Blacklist", "disabled": False},
		]
	if ops == "Suspended":
		return [{"id": "reactivate", "label": "Reactivate", "disabled": False}]
	return []


@frappe.whitelist()
def get_supplier_detail(supplier_code: str) -> dict:
	"""Detail payload for right workbench panel."""
	pname = _resolve_profile_name_by_code((supplier_code or "").strip())
	if not pname:
		return {"ok": False, "error": "NOT_FOUND"}
	prof = frappe.get_doc("KTSM Supplier Profile", pname)
	doc_rows = frappe.get_all(
		"KTSM Supplier Document",
		filters={"supplier_profile": pname, "is_current": 1},
		fields=["name", "document_type", "document_name", "verification_status", "expiry_date", "verified_by", "verified_at"],
		order_by="modified desc",
	)
	dt_names = list({d.get("document_type") for d in (doc_rows or []) if d.get("document_type")})
	dt_meta = {}
	if dt_names:
		for d in frappe.get_all(
			"KTSM Document Type",
			filters={"name": ("in", dt_names)},
			fields=["name", "document_type_code", "document_type_name", "required_for_registration"],
		):
			dt_meta[d.get("name")] = d

	docs_missing = False
	required_dts = frappe.get_all(
		"KTSM Document Type",
		filters={"required_for_registration": 1, "is_active": 1},
		fields=["name", "document_type_code", "document_type_name"],
	)
	present_verified = {d.get("document_type") for d in (doc_rows or []) if d.get("verification_status") == "Verified"}
	missing_docs = []
	for rd in required_dts or []:
		if rd.get("name") not in present_verified:
			docs_missing = True
			missing_docs.append(f"{rd.get('document_type_name')} ({rd.get('document_type_code')})")

	assign_rows = frappe.get_all(
		"KTSM Category Assignment",
		filters={"supplier_profile": pname},
		fields=["name", "category", "qualification_status", "qualified_until", "reviewed_by", "reviewed_at"],
		order_by="modified desc",
	)
	cat_names = list({a.get("category") for a in (assign_rows or []) if a.get("category")})
	cat_meta = {}
	if cat_names:
		for c in frappe.get_all(
			"KTSM Supplier Category",
			filters={"name": ("in", cat_names)},
			fields=["name", "category_code", "category_name"],
		):
			cat_meta[c.get("name")] = c

	history_rows = frappe.get_all(
		"KTSM Status History",
		filters={"supplier_profile": pname},
		fields=["status_type", "previous_status", "new_status", "reason", "changed_by", "changed_at"],
		order_by="changed_at desc",
		limit=20,
	)
	return {
		"ok": True,
		"detail": {
			"profile_name": prof.name,
			"supplier_code": supplier_code,
			"supplier_name": prof.identity_display or supplier_code,
			"approval_status": prof.approval_status,
			"operational_status": prof.operational_status,
			"compliance_status": prof.compliance_status,
			"risk_level": prof.risk_level,
			"erpnext_supplier": prof.erpnext_supplier,
			"registration_date": prof.creation,
			"external_user": prof.external_user,
			"actions": _action_defs(
				prof.approval_status,
				prof.operational_status,
				prof.compliance_status,
				docs_missing,
			),
			"sections": {
				"profile": {
					"name": prof.identity_display or supplier_code,
					"code": supplier_code,
					"erpnext_supplier": prof.erpnext_supplier,
					"contact_info": prof.external_user,
					"registration_date": prof.creation,
				},
				"documents": [
					{
						"document_type": f"{dt_meta.get(d.get('document_type'), {}).get('document_type_name') or d.get('document_type')} ({dt_meta.get(d.get('document_type'), {}).get('document_type_code') or 'N/A'})",
						"document_name": d.get("document_name"),
						"status": d.get("verification_status"),
						"expiry": d.get("expiry_date"),
						"verified_by": d.get("verified_by"),
					}
					for d in (doc_rows or [])
				],
				"categories": [
					{
						"category": f"{cat_meta.get(a.get('category'), {}).get('category_name') or a.get('category')} ({cat_meta.get(a.get('category'), {}).get('category_code') or 'N/A'})",
						"qualification_status": a.get("qualification_status"),
						"valid_until": a.get("qualified_until"),
					}
					for a in (assign_rows or [])
				],
				"compliance": {
					"overall_status": prof.compliance_status,
					"missing_documents": missing_docs,
					"expired_documents": [
						r.get("document_name")
						for r in (doc_rows or [])
						if r.get("verification_status") == "Expired"
					],
				},
				"risk": {"risk_level": prof.risk_level, "risk_factors": []},
				"activity_log": history_rows or [],
			},
		},
	}


@frappe.whitelist()
def perform_action(action: str, supplier_code: str, reason: str | None = None) -> dict:
	"""Dispatch workbench actions by business code then return fresh detail."""
	pname = _resolve_profile_name_by_code((supplier_code or "").strip())
	if not pname:
		return {"ok": False, "error": "NOT_FOUND"}
	act = (action or "").strip().lower()
	rsn = (reason or "").strip() or "Workbench action"
	if act == "submit":
		smw_workflow.ktsm_submit_for_review(pname)
	elif act == "start_review":
		smw_workflow.ktsm_start_review(pname)
	elif act == "approve":
		smw_workflow.ktsm_approve_supplier(pname)
	elif act == "return":
		smw_workflow.ktsm_return_supplier(pname, rsn)
	elif act == "reject":
		smw_workflow.ktsm_reject_supplier(pname, rsn)
	elif act == "suspend":
		smw_workflow.ktsm_suspend(pname, rsn)
	elif act in ("reactivate", "reinstate"):
		smw_workflow.ktsm_reinstate(pname, rsn)
	elif act == "blacklist":
		smw_workflow.ktsm_blacklist(pname, rsn)
	else:
		return {"ok": False, "error": "INVALID_ACTION"}
	detail = get_supplier_detail(supplier_code)
	detail["action"] = act
	return detail


@frappe.whitelist()
def create_supplier_builder_profile(
	supplier_name: str,
	supplier_type: str = "Company",
) -> dict:
	"""Create ERP Supplier + linked KTSM profile and return builder target."""
	_assert_registry_access()
	name = (supplier_name or "").strip()
	if not name:
		return {"ok": False, "error": "SUPPLIER_NAME_REQUIRED"}
	sg = _supplier_group()
	if not sg:
		return {"ok": False, "error": "SUPPLIER_GROUP_MISSING"}
	code = _next_supplier_code()
	erp = frappe.get_doc(
		{
			"doctype": "Supplier",
			"supplier_name": name,
			"supplier_type": supplier_type or "Company",
			"supplier_group": sg,
			"kentender_supplier_code": code,
		}
	)
	erp.insert(ignore_permissions=True)
	prof = frappe.get_doc(
		{
			"doctype": "KTSM Supplier Profile",
			"erpnext_supplier": erp.name,
		}
	)
	prof.insert(ignore_permissions=True)
	return {"ok": True, "profile_name": prof.name, "supplier_code": code}


@frappe.whitelist()
def get_builder_payload(profile_name: str) -> dict:
	"""Builder payload for KTSM profile form guidance surface."""
	_assert_registry_access()
	prof = frappe.get_doc("KTSM Supplier Profile", profile_name)
	supplier = frappe.get_doc("Supplier", prof.erpnext_supplier)
	docs = frappe.get_all(
		"KTSM Supplier Document",
		filters={"supplier_profile": profile_name, "is_current": 1},
		fields=["name", "document_type", "document_name", "verification_status", "expiry_date", "modified"],
		order_by="modified desc",
	)
	assignments = frappe.get_all(
		"KTSM Category Assignment",
		filters={"supplier_profile": profile_name},
		fields=["name", "category", "qualification_status", "qualified_until", "modified"],
		order_by="modified desc",
	)
	missing_required = []
	required_types = frappe.get_all(
		"KTSM Document Type",
		filters={"required_for_registration": 1, "is_active": 1},
		fields=["name", "document_type_name", "document_type_code"],
	)
	verified = {d.get("document_type") for d in (docs or []) if d.get("verification_status") == "Verified"}
	for rt in required_types or []:
		if rt.get("name") not in verified:
			missing_required.append(f"{rt.get('document_type_name')} ({rt.get('document_type_code')})")

	return {
		"ok": True,
		"profile_name": prof.name,
		"supplier_code": frappe.db.get_value("Supplier", supplier.name, "kentender_supplier_code"),
		"identity": {
			"supplier": supplier.name,
			"supplier_name": supplier.supplier_name,
			"supplier_type": supplier.supplier_type,
		},
		"profile": {
			"approval_status": prof.approval_status,
			"operational_status": prof.operational_status,
			"compliance_status": prof.compliance_status,
			"risk_level": prof.risk_level,
			"external_user": prof.external_user,
		},
		"documents": docs or [],
		"categories": assignments or [],
		"readiness": {
			"has_identity": bool(supplier.supplier_name),
			"has_documents": bool(docs),
			"has_categories": bool(assignments),
			"missing_required_documents": missing_required,
		},
	}


@frappe.whitelist()
def update_builder_identity(
	profile_name: str,
	supplier_name: str,
	supplier_type: str = "Company",
) -> dict:
	"""Update ERPNext Supplier identity from KTSM builder with policy guard."""
	_assert_registry_access()
	prof = frappe.get_doc("KTSM Supplier Profile", profile_name)
	s = frappe.get_doc("Supplier", prof.erpnext_supplier)
	if (supplier_name or "").strip():
		s.supplier_name = supplier_name.strip()
	if (supplier_type or "").strip():
		s.supplier_type = supplier_type.strip()
	s.save(ignore_permissions=True)
	frappe.db.set_value("KTSM Supplier Profile", prof.name, "identity_display", s.supplier_name)
	return {"ok": True, "supplier": s.name, "supplier_name": s.supplier_name}
