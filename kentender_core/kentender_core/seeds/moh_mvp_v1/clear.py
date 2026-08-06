# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reverse-dependency clear for MOH_MVP_V1 fixture records."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.moh_mvp_v1 import constants as C

_LEGACY_BUDGET_CODES = (
	"MOH-BUD-0001",
	"MOH-BUD-0002",
	"MOH-BUD-0003",
	"MOH-BUD-0004",
)
_LEGACY_LINE_CODES = tuple(f"MOH-BL-000{i}" for i in range(1, 8))


def clear_moh_mvp_v1_budget() -> dict[str, Any]:
	deleted: dict[str, int] = {}
	budget_names = frappe.get_all(
		"Budget",
		filters={"fixture_namespace": ["in", [C.FIXTURE_NS, "MOH_MVP_V1_EDGE"]]},
		pluck="name",
	)
	for code in (C.BUD_ACTIVE, C.BUD_DRAFT, C.BUD_CLOSED, *_LEGACY_BUDGET_CODES):
		name = frappe.db.get_value("Budget", {"generated_reference": code}, "name")
		if name and name not in budget_names:
			budget_names.append(name)

	for budget_name in budget_names:
		# Snapshots → commitments → reservations → revisions → lines → budget
		for doctype in (
			"Expenditure Snapshot",
			"Procurement Commitment",
			"Funding Reservation",
			"Budget Revision",
			"Budget Audit Event",
			"Budget Line",
		):
			if not frappe.db.exists("DocType", doctype):
				continue
			if doctype == "Budget Audit Event":
				frappe.flags.allow_budget_audit_purge = True
			try:
				filters: dict[str, Any] = {"budget": budget_name}
				if frappe.db.has_column(doctype, "fixture_namespace"):
					# Prefer NS when present; still delete children of fixture budgets.
					pass
				names = frappe.get_all(doctype, filters=filters, pluck="name")
				for name in names:
					frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
					deleted[doctype] = deleted.get(doctype, 0) + 1
			finally:
				if doctype == "Budget Audit Event":
					frappe.flags.allow_budget_audit_purge = False
		frappe.delete_doc("Budget", budget_name, force=1, ignore_permissions=True)
		deleted["Budget"] = deleted.get("Budget", 0) + 1

	# Orphan legacy lines by code
	for code in _LEGACY_LINE_CODES:
		name = frappe.db.get_value("Budget Line", {"generated_reference": code}, "name")
		if name:
			frappe.delete_doc("Budget Line", name, force=1, ignore_permissions=True)
			deleted["Budget Line"] = deleted.get("Budget Line", 0) + 1
	return {"ok": True, "deleted": deleted}


def clear_moh_mvp_v1(*, include_strategy: bool = True, include_budget: bool = True) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": True}
	if include_budget:
		out["budget"] = clear_moh_mvp_v1_budget()
	if include_strategy:
		from kentender_strategy.seeds.moh_mvp_v1_strategy import clear_moh_mvp_v1_strategy

		out["strategy"] = clear_moh_mvp_v1_strategy()
	return out
