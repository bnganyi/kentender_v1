# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""D5 — Procurement template list + preview for selector modal (workbench + Form)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.procurement_planning.api.landing import (
	_can_read_planning,
	resolve_pp_role_key,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict:
	return {"ok": False, "error_code": code, "message": str(message), "role_key": role_key, "rows": []}


def _as_list(raw: Any) -> list:
	if raw is None:
		return []
	if isinstance(raw, str):
		try:
			parsed = json.loads(raw)
		except Exception:
			return []
		return parsed if isinstance(parsed, list) else []
	if isinstance(raw, list):
		return raw
	return []


def _applicability_summary(
	applicable_requisition_types: Any,
	applicable_demand_types: Any,
) -> str:
	parts: list[str] = []
	for label, raw in (
		(_("Requisition types"), applicable_requisition_types),
		(_("Demand types"), applicable_demand_types),
	):
		items = _as_list(raw)
		if not items:
			continue
		parts.append(f"{label}: {', '.join(str(x) for x in items[:8])}")
	s = " · ".join(parts)
	if len(s) > 220:
		return s[:217] + "…"
	return s or _("All configured types (see template record).")


def _format_grouping(raw: Any) -> str:
	if raw in (None, "", {}):
		return _("No grouping (single package per application).")
	if isinstance(raw, str):
		try:
			raw = json.loads(raw)
		except Exception:
			return str(raw)[:200]
	if not isinstance(raw, dict):
		return str(raw)[:200]
	gb = raw.get("group_by")
	if isinstance(gb, list) and gb:
		return _("Group by: {0}").format(", ".join(str(x) for x in gb[:12]))
	if isinstance(gb, list) and not gb:
		return _("No grouping (empty group_by).")
	return json.dumps(raw, ensure_ascii=False)[:200]


def _label_for_doctype(doctype: str, name: str | None) -> str:
	if not name or not doctype or not frappe.db.exists(doctype, name):
		return "—"
	try:
		meta = frappe.get_meta(doctype)
		fields: list[str] = []
		for f in ("profile_name", "template_name", "profile_code", "name"):
			if meta.has_field(f) and f not in fields:
				fields.append(f)
		if not fields:
			return "—"
		row = frappe.db.get_value(doctype, name, fields, as_dict=True)
	except Exception:
		return "—"
	if not row:
		return "—"
	return (row.get("profile_name") or row.get("template_name") or row.get("profile_code") or "—") or "—"


@frappe.whitelist()
def list_pp_templates() -> dict:
	"""Return active templates for the selection modal (no free-form search)."""
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return _fail(
			code="PP_NOT_INSTALLED",
			message=_("Procurement Planning is not installed on this site (missing DocTypes)."),
		)

	role_key = resolve_pp_role_key()
	if not role_key or not _can_read_planning():
		return _fail(
			code="PP_ACCESS_DENIED",
			message=_("You do not have access to the Procurement Planning workbench."),
			role_key=role_key or "auditor",
		)

	rows = frappe.get_all(
		"Procurement Template",
		filters={"is_active": 1},
		fields=[
			"name",
			"template_code",
			"template_name",
			"default_method",
			"default_contract_type",
			"applicable_requisition_types",
			"applicable_demand_types",
		],
		order_by="template_name asc, template_code asc",
		limit_page_length=500,
	)

	out = []
	for r in rows:
		out.append(
			{
				"name": r.get("name"),
				"template_code": (r.get("template_code") or "").strip(),
				"template_name": (r.get("template_name") or "").strip(),
				"default_method": (r.get("default_method") or "").strip(),
				"default_contract_type": (r.get("default_contract_type") or "").strip(),
				"applicability_summary": _applicability_summary(
					r.get("applicable_requisition_types"),
					r.get("applicable_demand_types"),
				),
			}
		)

	return {"ok": True, "role_key": role_key, "rows": out}


def _resolve_template_id(ref: str) -> str | None:
	ref = (ref or "").strip()
	if not ref:
		return None
	if frappe.db.exists("Procurement Template", ref):
		return ref
	code = frappe.db.get_value("Procurement Template", {"template_code": ref}, "name")
	if code:
		return code
	return None


@frappe.whitelist()
def get_pp_template_preview(template: str | None = None) -> dict:
	"""Return labels + link targets for a single template (no hashes in *label* fields)."""
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return {
			"ok": False,
			"error_code": "PP_NOT_INSTALLED",
			"message": _("Procurement Planning is not installed on this site (missing DocTypes)."),
		}

	role_key = resolve_pp_role_key()
	if not role_key or not _can_read_planning():
		return {
			"ok": False,
			"error_code": "PP_ACCESS_DENIED",
			"message": _("You do not have access to the Procurement Planning workbench."),
			"role_key": role_key or "auditor",
		}

	tid = _resolve_template_id((template or "").strip())
	if not tid:
		return {"ok": False, "error_code": "NOT_FOUND", "message": _("Template not found.")}

	if not frappe.has_permission("Procurement Template", "read", tid):
		return {"ok": False, "error_code": "NO_READ", "message": _("Not permitted to read this template.")}

	full = frappe.get_doc("Procurement Template", tid)

	rp = full.risk_profile_id
	kp = full.kpi_profile_id
	dcp = full.decision_criteria_profile_id
	vp = full.vendor_management_profile_id

	labels = {
		"risk_profile": _label_for_doctype("Risk Profile", rp) if rp else "—",
		"kpi_profile": _label_for_doctype("KPI Profile", kp) if kp else "—",
		"decision_criteria_profile": _label_for_doctype("Decision Criteria Profile", dcp) if dcp else "—",
		"vendor_management_profile": _label_for_doctype("Vendor Management Profile", vp) if vp else "—",
	}

	links = {
		"template_id": full.name,
		"risk_profile_id": rp or None,
		"kpi_profile_id": kp or None,
		"decision_criteria_profile_id": dcp or None,
		"vendor_management_profile_id": vp or None,
	}

	return {
		"ok": True,
		"role_key": role_key,
		"template_code": (full.template_code or "").strip(),
		"template_name": (full.template_name or "").strip(),
		"default_method": (full.default_method or "").strip(),
		"default_contract_type": (full.default_contract_type or "").strip(),
		"applicability_summary": _applicability_summary(
			full.applicable_requisition_types, full.applicable_demand_types
		),
		"grouping_summary": _format_grouping(full.grouping_strategy),
		"profile_labels": labels,
		"profile_links": links,
		"applicable_requisition_types": _as_list(full.applicable_requisition_types),
		"applicable_demand_types": _as_list(full.applicable_demand_types),
	}
