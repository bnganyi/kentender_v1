# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 3 §28–29 — WORKS ``STDINT-WORKS-S01`` seed verification + integration smoke.

§28: structural checks after seed (strategy chain, demands, plan, package, tender linkage, roll-up).
§29: TM2-only — legacy Procurement Tender tender-stage smoke removed (TM2 STD / publication paths).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt


def _append(
	checks: list[dict[str, Any]],
	check_id: str,
	ok: bool,
	detail: str = "",
) -> None:
	checks.append({"id": check_id, "ok": bool(ok), "detail": (detail or "")[:500]})


def gather_doc3_section_28_checks(
	*,
	tender_name: str,
	package_name: str,
	plan_name: str,
	budget_line_name: str,
	demand_ids: tuple[str, ...],
	std_template_code: str,
) -> dict[str, Any]:
	"""Return §28 checklist results (no writes)."""
	checks: list[dict[str, Any]] = []

	if not frappe.db.exists("Budget Line", budget_line_name):
		_append(checks, "budget_line_exists", False, budget_line_name)
	else:
		_append(checks, "budget_line_exists", True, budget_line_name)
		bl = frappe.get_doc("Budget Line", budget_line_name)
		has_strategy = bool(
			(getattr(bl, "strategic_plan", None) or "").strip()
			or (getattr(bl, "program", None) or "").strip()
		)
		_append(checks, "strategy_link_on_budget_line", has_strategy, "strategic_plan or program")

	for did in demand_ids:
		dn = frappe.db.get_value("Demand", {"demand_id": did}, "name")
		if not dn:
			_append(checks, f"demand_{did}", False, "missing")
			continue
		bl_on_d = frappe.db.get_value("Demand", dn, "budget_line")
		ok = bool(bl_on_d) and bl_on_d == budget_line_name
		_append(checks, f"demand_{did}_links_budget_line", ok, str(bl_on_d or ""))

	if not frappe.db.exists("Procurement Plan", plan_name):
		_append(checks, "procurement_plan_exists", False, plan_name)
	else:
		st = (frappe.db.get_value("Procurement Plan", plan_name, "status") or "").strip()
		_append(checks, "procurement_plan_approved", st == "Approved", st)

	tpl_id = frappe.db.get_value("Procurement Package", package_name, "template_id")
	if tpl_id:
		dst = frappe.db.get_value("Procurement Template", tpl_id, "default_std_template")
		_append(
			checks,
			"procurement_template_resolves_std",
			(dst or "").strip() == std_template_code,
			str(dst or ""),
		)
	else:
		_append(checks, "procurement_template_resolves_std", False, "no template_id")

	line_count = frappe.db.count("Procurement Package Line", {"package_id": package_name})
	_append(checks, "package_has_lines", line_count >= 1, f"count={line_count}")

	lines = frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": package_name},
		fields=["amount"],
	)
	line_total = sum(flt(r.amount) for r in lines)
	pkg_ev = flt(frappe.db.get_value("Procurement Package", package_name, "estimated_value"))
	_append(
		checks,
		"package_estimated_equals_line_total",
		abs(pkg_ev - line_total) < 0.01 or line_total == 0,
		f"pkg={pkg_ev} lines={line_total}",
	)

	pkg_st = (frappe.db.get_value("Procurement Package", package_name, "status") or "").strip()
	_append(
		checks,
		"package_released_or_releasable",
		pkg_st == "Released to Tender",
		pkg_st,
	)

	if not frappe.db.exists("TM2 Tender", tender_name):
		_append(checks, "tender_exists", False, tender_name)
	else:
		_append(checks, "tender_exists", True, tender_name)
		t_std = (frappe.db.get_value("TM2 Tender", tender_name, "std_template") or "").strip()
		t_tpl_code = (
			(frappe.db.get_value("STD Template", t_std, "template_code") or "").strip() if t_std else ""
		)
		_append(checks, "tender_links_std", t_tpl_code == std_template_code, t_std)

		raw = frappe.db.get_value("TM2 Tender", tender_name, "configuration_json") or ""
		_append(checks, "tender_configuration_json_populated", len(raw.strip()) > 20, f"len={len(raw)}")

		src_h = frappe.db.get_value("TM2 Tender", tender_name, "planning_handoff_snapshot_sha256")
		_append(checks, "audit_planning_handoff_snapshot_hash", bool((src_h or "").strip()), "")

	_append(checks, "no_publication_records_required", True, "v1: no tender-linked publication DocType enforced")

	all_passed = all(c["ok"] for c in checks)
	return {"checks": checks, "all_passed": all_passed}


def run_doc3_section_29_smoke(tender_name: str) -> dict[str, Any]:
	"""§29 tender-stage smoke — TM2-only (legacy Procurement Tender path removed)."""
	frappe.set_user("Administrator")
	if not tender_name or not frappe.db.exists("TM2 Tender", tender_name):
		return {"ok": False, "skipped": False, "error": "missing_tm2_tender"}
	return {
		"ok": True,
		"skipped": True,
		"reason": "TM2-only: §29 legacy Procurement Tender controller smoke retired.",
		"steps": {},
	}
