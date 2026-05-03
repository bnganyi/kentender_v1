# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""F2 — Validate DIA / Budget dependencies for the locked Procurement Planning seed (6. Seed Data).

Does **not** create upstream records. Run ``seed_dia_planning_f1_prerequisites`` (or DIA basic +
extended + prerequisites) to satisfy missing demands, then re-run this check.

``bench --site kentender.midas.com execute
kentender_procurement.procurement_planning.seeds.validate_planning_seed_dependencies.run``
"""

from __future__ import annotations

import frappe
from frappe import _

# Locked: 6. Seed Data §6 — DIA reference assumptions
REQUIRED_DEMAND_IDS: tuple[str, ...] = (
	"DIA-MOH-2026-0004",
	"DIA-MOH-2026-0011",
	"DIA-MOH-2026-0020",
	"DIA-MOH-2026-0030",
)

_ALLOWED_DEMAND_STATUS = frozenset(("Approved", "Planning Ready"))

REQUIRED_BUDGET_LINE_CODES: tuple[str, ...] = (
	"BL-MOH-2026-001",
	"BL-MOH-2026-002",
	"BL-MOH-2027-001",
)


def get_validation_report() -> dict:
	"""Return a structured report (no throws)."""
	missing_demands: list[str] = []
	bad_status: list[dict] = []
	for did in REQUIRED_DEMAND_IDS:
		if not frappe.db.exists("Demand", {"demand_id": did}):
			missing_demands.append(did)
			continue
		name = frappe.db.get_value("Demand", {"demand_id": did}, "name")
		if not name:
			missing_demands.append(did)
			continue
		st = (frappe.db.get_value("Demand", name, "status") or "").strip()
		if st not in _ALLOWED_DEMAND_STATUS:
			bad_status.append({"demand_id": did, "status": st or "(empty)"})

	missing_budget_lines: list[str] = []
	for code in REQUIRED_BUDGET_LINE_CODES:
		if not frappe.db.exists("Budget Line", {"budget_line_code": code}):
			missing_budget_lines.append(code)

	ok = not missing_demands and not bad_status and not missing_budget_lines
	msg: str
	if ok:
		msg = _("All Procurement Planning seed DIA and Budget Line prerequisites are present.")
	else:
		parts: list[str] = []
		if missing_demands:
			parts.append(
				_("Missing demands (run seed_dia_planning_f1_prerequisites or DIA seed packs): {0}").format(
					", ".join(missing_demands)
				)
			)
		if bad_status:
			parts.append(
				_("Demands not in Approved / Planning Ready: {0}").format(
					", ".join(f"{x['demand_id']} ({x['status']})" for x in bad_status)
				)
			)
		if missing_budget_lines:
			parts.append(
				_(
					"Missing budget lines (run kentender_core.seeds.seed_budget_line_dia): {0}"
				).format(", ".join(missing_budget_lines))
			)
		msg = " | ".join(parts)

	return {
		"ok": bool(ok),
		"message": str(msg),
		"missing_demands": missing_demands,
		"demand_status_mismatch": bad_status,
		"missing_budget_line_codes": missing_budget_lines,
		"required_demand_ids": list(REQUIRED_DEMAND_IDS),
		"required_budget_line_codes": list(REQUIRED_BUDGET_LINE_CODES),
	}


def run() -> dict:
	"""F2 entry point: print-friendly validation (Administrator only)."""
	frappe.only_for(("System Manager", "Administrator"))
	if not frappe.db.exists("DocType", "Procurement Plan"):
		return {
			"ok": False,
			"message": str(_("Procurement Planning DocTypes are not installed.")),
		}
	out = get_validation_report()
	frappe.msgprint(
		_("Procurement planning seed — dependency check: {0}").format(
			_("OK") if out.get("ok") else _("Failed")
		)
		+ f"\n{out.get('message', '')}"
	)
	return out


def assert_prerequisites() -> None:
	"""Used by F1: throw with a clear, combined message if validation fails."""
	r = get_validation_report()
	if r.get("ok"):
		return
	frappe.throw(str(r.get("message") or _("Procurement planning seed dependencies are not satisfied.")), title=_("F2 validation failed"))
