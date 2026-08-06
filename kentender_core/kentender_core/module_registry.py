# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""KenTender module registry for context-preserving desk navigation."""

from __future__ import annotations

from typing import Any

# Canonical module definitions — keep in sync with public/js/kt_module_registry.js
KT_MODULES: dict[str, dict[str, Any]] = {
	"strategy": {
		# MVP-1 Strategy Alignment — keep in sync with kt_module_registry.js + hooks.page_js.
		"workspace_label": "Strategy Alignment",
		"sidebar_workspace_key": "procurement",
		"builder_page": "strategy-plan-structure",
		"desk_page": "strategy-alignment",
		"form_doctype": "",
		"state_key": "kt_strategy_workbench_state",
		"select_key": "kt_strategy_workspace_select",
		"route_prefixes": (
			"strategy-alignment",
			"strategy-performance",
			"strategy-plan-create",
			"strategy-plan-overview",
			"strategy-plan-structure",
			"strategy-plan-value-commitments",
			"strategy-plan-measurements",
			"strategy-plan-downstream-usage",
			"strategy-plan-review",
			"strategy-plan-audit",
			"strategy-pvo-catalogue",
			"strategy-pvo-editor",
			"strategy-measurement-submit",
			"strategy-measurement-verify",
			"strategy-corrective-actions",
		),
		"sidebar_parent": "Procurement",
	},
	"budget": {
		# MVP-1 Budget & Funding — keep in sync with kt_module_registry.js + hooks.page_js.
		"workspace_label": "Budget Management",
		"sidebar_workspace_key": "budget management",
		"builder_page": "",
		"desk_page": "budget-funding",
		"form_doctype": "Budget",
		"state_key": "kt_budget_workbench_state",
		"select_key": "kt_budget_workspace_select",
		"route_prefixes": (
			"budget-funding",
			"budget-register",
			"budget-funding-performance",
			"budget-check-reserve",
			"budget-overview",
			"budget-lines",
			"budget-funding-activity",
			"budget-revisions",
			"budget-revision-create",
			"budget-revision-review",
			"budget-downstream",
			"budget-review",
			"budget-audit",
			"Form/Budget",
		),
		"sidebar_parent": "Procurement",
	},
	"dia": {
		"workspace_label": "Demand Intake and Approval",
		"sidebar_workspace_key": "demand intake and approval",
		"desk_page": "demand-hub",
		"form_doctype": "Demand",
		"state_key": "kt_dia_workbench_state",
		"select_key": "kt_dia_workspace_select",
		"route_prefixes": ("demand-hub", "create-demand", "Form/Demand"),
		"sidebar_parent": "Procurement",
	},
	"procurement_planning": {
		"workspace_label": "Procurement Planning",
		"sidebar_workspace_key": "procurement planning",
		"desk_page": "planning-hub",
		"form_doctype": "Procurement Package",
		"state_key": "kt_pp_workbench_state",
		"select_key": "kt_pp_workspace_select",
		"route_prefixes": (
			"planning-hub",
			"procurement-planning",
			"procurement-planning/approved-demands",
			"procurement-planning/plans",
			"procurement-planning/packages",
			"procurement-planning/releases",
			"Form/Procurement Package",
		),
		"sidebar_parent": "Procurement",
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
		parent = mod.get("sidebar_parent") or _KT_SIDEBAR_PARENT
		for prefix in mod.get("route_prefixes") or ():
			key = str(prefix).lower()
			out[key] = parent
			if "/" in key:
				out[key.split("/")[0]] = parent
		builder = mod.get("builder_page")
		if builder:
			out[str(builder).lower()] = parent
		desk_page = mod.get("desk_page")
		if desk_page:
			out[str(desk_page).lower()] = parent
	return out


def get_module(module_id: str) -> dict[str, Any] | None:
	return KT_MODULES.get(module_id)
