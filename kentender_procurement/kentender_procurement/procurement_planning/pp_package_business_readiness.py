# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-007 / LV-R5-007-01 — Planning-phase business readiness (spec §11.5 checklist).

Derived read-only aggregates for the Procurement Planning workbench (ADR-PLC-002).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

_APPROVED_DEMAND_STATUSES = frozenset(("Approved", "Planning Ready"))

# Spec §11.5 — checklist labels must match usability pack wording.
CHECK_ORDER: tuple[tuple[str, str], ...] = (
	("scope_ready", "Scope ready"),
	("budget_linked", "Budget linked"),
	("demand_approved", "Demand approved"),
	("procurement_method_selected", "Procurement method selected"),
	("procurement_category_selected", "Procurement category selected"),
	("std_category_identified", "STD category identified"),
	("package_released", "Package released"),
	("tender_created", "Tender created"),
)


def _pf_dict(raw: Any) -> dict[str, Any]:
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			x = json.loads(raw)
			return x if isinstance(x, dict) else {}
		except json.JSONDecodeError:
			pass
	return {}


def _pkgrel_pf_for_package_business(package_business_code: str) -> dict[str, Any]:
	"""Best-effort read of PKGREL Planning Release Package ``passed_forward_summary`` only."""
	pc = (package_business_code or "").strip()
	if not pc or not frappe.db.exists("DocType", "Procurement Handoff Card"):
		return {}
	try:
		if not frappe.has_permission("Procurement Handoff Card", "read"):
			return {}
	except frappe.PermissionError:
		return {}

	from kentender_procurement.procurement_lifecycle.journey_object_lookup import (
		resolve_journey_code_for_object,
	)
	from kentender_procurement.procurement_planning.package_planning_release_display import (
		pkgrel_handoff_code_from_journey_code,
	)

	j_pk = resolve_journey_code_for_object("Procurement Package", pc)
	if not j_pk:
		return {}
	jc = (
		frappe.db.get_value("Procurement Journey", j_pk, "journey_code") or ""
	).strip() or str(j_pk)
	handoff_code = pkgrel_handoff_code_from_journey_code(jc)
	if not handoff_code or not frappe.db.exists("Procurement Handoff Card", handoff_code):
		return {}

	try:
		if not frappe.has_permission("Procurement Handoff Card", "read", handoff_code):
			return {}
	except frappe.PermissionError:
		return {}

	meta = frappe.db.get_value(
		"Procurement Handoff Card",
		handoff_code,
		["handoff_title", "passed_forward_summary"],
		as_dict=True,
	)
	if not meta:
		return {}
	if (meta.handoff_title or "").strip() != "Planning Release Package":
		return {}
	return _pf_dict(meta.passed_forward_summary)


def summarize_pp_package_business_readiness(pkg_doc) -> dict[str, Any]:
	"""Return checklist for a loaded ``Procurement Package`` doc (read-only).

	:param pkg_doc: ``frappe.model.document.Document`` for ``Procurement Package``.
	:returns: ``{ "checks": [ { id, label, ok, detail } ], "all_ready": bool }``
	"""

	pkg_name = getattr(pkg_doc, "name", "") or ""
	package_code = (getattr(pkg_doc, "package_code", "") or "").strip()

	lines = frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": pkg_name, "is_active": 1},
		fields=["name", "demand_id", "budget_line_id"],
		limit_page_length=200,
	)

	package_name_txt = (getattr(pkg_doc, "package_name", "") or "").strip()
	scope_lines_ok = len(lines) > 0
	_ok_scope = bool(package_name_txt and scope_lines_ok)

	budget_ok = bool(lines) and all(bool(l.budget_line_id) for l in lines)
	demand_link_ok = bool(lines) and all(bool(l.demand_id) for l in lines)

	demand_states_ok = True
	missing_demands: list[str] = []
	if demand_link_ok and lines:
		demand_names = list({str(l.demand_id) for l in lines if l.demand_id})
		for dn in demand_names:
			st = (frappe.db.get_value("Demand", dn, "status") or "").strip()
			if st not in _APPROVED_DEMAND_STATUSES:
				demand_states_ok = False
				missing_demands.append(f"{dn}:{st or '?'}")
		demand_states_ok = demand_states_ok and bool(demand_names)

	method_txt = (getattr(pkg_doc, "procurement_method", "") or "").strip()
	method_ok = bool(method_txt)

	contract_txt = (getattr(pkg_doc, "contract_type", "") or "").strip()
	category_txt = ""
	tpl_std = ""
	if getattr(pkg_doc, "template_id", None):
		trow = frappe.db.get_value(
			"Procurement Template",
			pkg_doc.template_id,
			["category", "default_std_template"],
			as_dict=True,
		)
		if trow:
			category_txt = ((trow.category or "") + "").strip()
			tpl_std = ((trow.default_std_template or "") + "").strip()
	category_ok = bool(contract_txt or category_txt)

	pf_pkgrel = _pkgrel_pf_for_package_business(package_code) if package_code else {}
	std_from_pf = (pf_pkgrel.get("required_std_category") or "").strip()
	std_ok = bool(tpl_std or std_from_pf)

	status_txt = (getattr(pkg_doc, "status", "") or "").strip()
	released_ok = status_txt == "Released to Tender"

	demand_detail = ""
	if not demand_link_ok:
		demand_detail = _("Each active line must link to a demand.")
	elif not demand_states_ok:
		demand_detail = ", ".join(missing_demands)[:240] or _("Demands must be Approved or Planning Ready.")

	tender_ok = False
	if package_code:
		tender_ok = bool(frappe.db.exists("TM2 Tender", {"procurement_package_code": package_code}))

	results_by_key: dict[str, tuple[bool, str]] = {
		"scope_ready": (_ok_scope, "" if _ok_scope else _("Add lines and define the package scope.")),
		"budget_linked": (
			budget_ok,
			"" if budget_ok else _("Every active demand line requires a linked budget line."),
		),
		"demand_approved": (
			demand_link_ok and demand_states_ok,
			"" if (demand_link_ok and demand_states_ok) else demand_detail,
		),
		"procurement_method_selected": (method_ok, "" if method_ok else _("Select a procurement method.")),
		"procurement_category_selected": (
			category_ok,
			"" if category_ok else _("Set contract type or template category."),
		),
		"std_category_identified": (
			std_ok,
			"" if std_ok else _("Link a default STD Template on the package template or record release details."),
		),
		"package_released": (released_ok, "" if released_ok else _("Package status is not Released to Tender.")),
		"tender_created": (
			tender_ok,
			"" if tender_ok else _("No tender is linked to this package yet."),
		),
	}

	checks_out: list[dict[str, Any]] = []
	for key, label in CHECK_ORDER:
		ok_flag, hint = results_by_key[key]
		checks_out.append({"id": key, "label": label, "ok": ok_flag, "detail": hint or ""})

	all_ready = all(c["ok"] for c in checks_out)

	return {"checks": checks_out, "all_ready": all_ready}
