# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""KenTender module registry for context-preserving desk navigation."""

from __future__ import annotations

from typing import Any

# Canonical module definitions — keep in sync with public/js/kt_module_registry.js
KT_MODULES: dict[str, dict[str, Any]] = {
	"strategy": {
		"workspace_label": "Strategy Management",
		"sidebar_workspace_key": "strategy management",
		"builder_page": "strategy-builder",
		"form_doctype": "Strategic Plan",
		"state_key": "kt_strategy_workbench_state",
		"select_key": "kt_strategy_workspace_select",
		"route_prefixes": ("strategy-builder", "Form/Strategic Plan"),
	},
	"budget": {
		"workspace_label": "Budget Management",
		"sidebar_workspace_key": "budget management",
		"builder_page": "budget-builder",
		"form_doctype": "Budget",
		"state_key": "kt_budget_workbench_state",
		"select_key": "kt_budget_workspace_select",
		"route_prefixes": ("budget-builder", "Form/Budget"),
	},
	"dia": {
		"workspace_label": "Demand Intake and Approval",
		"sidebar_workspace_key": "demand intake and approval",
		"form_doctype": "Demand",
		"state_key": "kt_dia_workbench_state",
		"select_key": "kt_dia_workspace_select",
		"route_prefixes": ("Form/Demand",),
	},
	"procurement_planning": {
		"workspace_label": "Procurement Planning",
		"sidebar_workspace_key": "procurement planning",
		"form_doctype": "Procurement Package",
		"state_key": "kt_pp_workbench_state",
		"select_key": "kt_pp_workspace_select",
		"route_prefixes": ("Form/Procurement Package",),
	},
	"ktsm": {
		"workspace_label": "KTSM Supplier Registry",
		"sidebar_workspace_key": "ktsm supplier registry",
		"form_doctype": "KTSM Supplier Profile",
		"state_key": "kt_ktsm_workbench_state",
		"select_key": "kt_ktsm_workspace_select",
		"route_prefixes": ("Form/KTSM Supplier Profile",),
	},
}

# Parent sidebar record on boot (Procurement rail hosts cross-app workspaces).
_KT_SIDEBAR_PARENT = "Procurement"


def get_route_sidebar_keys() -> dict[str, str]:
	"""Map desk route prefix (lower) → sidebar name for boot fast-path."""
	out: dict[str, str] = {}
	for mod in KT_MODULES.values():
		for prefix in mod.get("route_prefixes") or ():
			out[str(prefix).lower()] = _KT_SIDEBAR_PARENT
		builder = mod.get("builder_page")
		if builder:
			out[str(builder).lower()] = _KT_SIDEBAR_PARENT
	return out


def get_module(module_id: str) -> dict[str, Any] | None:
	return KT_MODULES.get(module_id)
