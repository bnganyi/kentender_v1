# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""KenTender module registry for context-preserving desk navigation."""

from __future__ import annotations

from typing import Any

# Canonical module definitions — keep in sync with public/js/kt_module_registry.js
KT_MODULES: dict[str, dict[str, Any]] = {
	"strategy": {
		# MVP-1 Strategy Alignment — keep in sync with kt_module_registry.js + hooks.page_js.
		# STR-CHG-001 v1.3 Phase 8: updated to the 3 Phase 7 production routes
		# after the 12 pre-rebuild legacy routes were deleted. This entry (and
		# the matching one in kt_module_registry.js) is confirmed dead code —
		# no live caller reaches kentender_core.kt_shell/kt_state/kt_nav with
		# moduleId "strategy" anywhere in the repo — so this update keeps the
		# file internally consistent without wiring it into anything live.
		# See IMPLEMENTATION_TRACKER.md Phase 8 decision log for the AGENTS.md
		# §6.5 "zero production callers" claim: true for this "strategy"
		# entry, but NOT true of kt_state generally — kentender_procurement's
		# planning_register_bind.js/planning_builder_bind.js do call
		# kentender_core.kt_state.save("procurement_planning", ...) for real.
		"workspace_label": "Strategy Alignment",
		"sidebar_workspace_key": "procurement",
		"builder_page": "strategy-plan-workspace",
		"desk_page": "strategy-portfolio",
		"form_doctype": "",
		"state_key": "kt_strategy_workbench_state",
		"select_key": "kt_strategy_workspace_select",
		"route_prefixes": (
			"strategy-portfolio",
			"strategy-plan-workspace",
			"strategy-review-task",
		),
		"sidebar_parent": "Procurement",
	},
	"budget": {
		# BUD-CHG-001 v1.2 Phase 5 — the one "budget-funding" Page
		# (BUD-UI-01..05, all sharing the /app/budget-funding prefix — not
		# "budget", which collides with the existing Budget doctype's own
		# List View route; see kentender_budget's budget_funding_page.js).
		# This entry (and the matching one in kt_module_registry.js) is
		# confirmed dead code, same as "strategy" above: kentender_budget's
		# own production page was never wired into this registry either — it
		# owns its own PageRail.vue chrome instead. Updated to stay
		# internally consistent (AGENTS.md §6.5), not because anything live
		# reads it.
		"workspace_label": "Budget Management",
		"sidebar_workspace_key": "procurement",
		"builder_page": "",
		"desk_page": "budget-funding",
		"form_doctype": "",
		"state_key": "kt_budget_workbench_state",
		"select_key": "kt_budget_workspace_select",
		"route_prefixes": ("budget-funding",),
		"sidebar_parent": "Procurement",
	},
	"departmental_needs": {
		"workspace_label": "Departmental Needs",
		"sidebar_workspace_key": "procurement",
		"builder_page": "",
		"desk_page": "departmental-needs",
		"form_doctype": "Departmental Need",
		"state_key": "kt_departmental_needs_state",
		"select_key": "kt_departmental_needs_select",
		"route_prefixes": ("departmental-needs",),
		"sidebar_parent": "Procurement",
	},
	"procurement_planning": {
		"workspace_label": "Procurement Planning",
		"sidebar_workspace_key": "procurement planning",
		"desk_page": "planning-workspace",
		"builder_page": "procurement-plan-builder",
		"form_doctype": "Procurement Plan",
		"state_key": "kt_pp_workbench_state",
		"select_key": "kt_pp_workspace_select",
		"route_prefixes": (
			"planning-workspace",
			"procurement-plan-register",
			"procurement-plan-builder",
			"Form/Procurement Plan",
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
