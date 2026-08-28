// KenTender module registry — context-preserving navigation (see docs/prompts/strategy/1. ken_tender…)
frappe.provide("kentender_core.module_registry");

(function () {
	const modules = {
		strategy: {
			// STR-CHG-001 v1.3 Phase 8 — updated to the 3 Phase 7 production
			// routes; the 12 pre-rebuild legacy routes were deleted. Confirmed
			// dead end-to-end for the "strategy" moduleId (kept in sync with
			// module_registry.py for consistency only, not wired into anything
			// live) — see IMPLEMENTATION_TRACKER.md Phase 8 decision log.
			id: "strategy",
			workspaceRoute: ["strategy-portfolio"],
			workspaceSlug: "strategy-portfolio",
			workbenchLabel: __("Strategy Alignment"),
			backLabel: __("Back to Strategy Alignment"),
			sidebarWorkspaceKey: "procurement",
			builderPage: "strategy-plan-workspace",
			formDoctype: "",
			stateKey: "kt_strategy_workbench_state",
			selectKey: "kt_strategy_workspace_select",
			routePrefixes: [
				"strategy-portfolio",
				"strategy-plan-workspace",
				"strategy-review-task",
			],
			taskLabels: {
				builder: __("Manage Structure"),
				form: __("Edit Plan"),
			},
		},
		budget: {
			// BUD-CHG-001 v1.2 — the 13 pre-rebuild legacy routes (and their
			// vanilla-JS Desk pages) were deleted in the UI teardown. This
			// block is a placeholder pending the Phase 5 Vue-in-Desk rebuild,
			// which will follow kentender_strategy's confirmed pattern: its
			// own production pages are NOT wired into this legacy
			// context-preserving navigation registry at all (each owns its
			// own PageRail.vue chrome instead — see kt_cl_surface_registry.js).
			// routePrefixes is intentionally empty until the new routes are
			// live and their final Frappe Page-name/route-collision behaviour
			// against the "Budget" DocType list view has been verified live.
			id: "budget",
			workspaceRoute: ["Workspaces", "Budget Management"],
			workspaceSlug: "budget-management",
			workbenchLabel: __("Budget & Funding"),
			backLabel: __("Back to Budget & Funding"),
			sidebarWorkspaceKey: "budget management",
			builderPage: "",
			deskPage: "",
			formDoctype: "Budget",
			stateKey: "kt_budget_workbench_state",
			selectKey: "kt_budget_workspace_select",
			routePrefixes: [],
			taskLabels: {
				builder: __("Budget & Funding"),
				form: __("Register approved budget"),
			},
		},
		departmental_needs: {
			id: "departmental_needs",
			workspaceRoute: ["departmental-needs"],
			workspaceSlug: "departmental-needs",
			workbenchLabel: __("Departmental Needs"),
			backLabel: __("Back to Departmental Needs"),
			sidebarWorkspaceKey: "procurement",
			builderPage: "",
			deskPage: "departmental-needs",
			formDoctype: "Departmental Need",
			stateKey: "kt_departmental_needs_state",
			selectKey: "kt_departmental_needs_select",
			routePrefixes: ["departmental-needs"],
			taskLabels: {
				form: __("Departmental Need"),
			},
		},
		procurement_planning: {
			id: "procurement_planning",
			workspaceSlug: "planning-workspace",
			builderPage: "procurement-plan-builder",
			workbenchLabel: __("Procurement Planning"),
			backLabel: __("Back to Procurement Planning"),
			sidebarWorkspaceKey: "procurement planning",
			formDoctype: "Procurement Plan",
			stateKey: "kt_pp_workbench_state",
			selectKey: "kt_pp_workspace_select",
			routePrefixes: ["planning-workspace", "procurement-plan-register", "procurement-plan-builder", "Form/Procurement Plan"],
			taskLabels: {
				form: __("Edit Plan"),
			},
		},
		ktsm: {
			id: "ktsm",
			workspaceRoute: ["Workspaces", "KTSM Supplier Registry"],
			workbenchLabel: __("KTSM Supplier Registry"),
			backLabel: __("Back to Supplier Workbench"),
			sidebarWorkspaceKey: "ktsm supplier registry",
			formDoctype: "KTSM Supplier Profile",
			stateKey: "kt_ktsm_workbench_state",
			selectKey: "kt_ktsm_workspace_select",
			routePrefixes: ["Form/KTSM Supplier Profile"],
			taskLabels: {
				form: __("Edit Supplier Profile"),
			},
		},
	};

	function routeKey(route) {
		const r = route || (typeof frappe !== "undefined" && frappe.get_route ? frappe.get_route() : []) || [];
		if (!r.length) return "";
		if (r[0] === "Form" && r.length >= 2) {
			return "Form/" + r[1];
		}
		return String(r[0] || "");
	}

	kentender_core.module_registry = {
		modules: modules,
		get(moduleId) {
			return modules[moduleId] || null;
		},
		resolveFromRoute(route) {
			const key = routeKey(route).toLowerCase();
			if (!key) return null;
			for (const id of Object.keys(modules)) {
				const m = modules[id];
				const prefixes = (m.routePrefixes || []).map((p) => String(p).toLowerCase());
				if (prefixes.indexOf(key) >= 0) return m;
				if (m.builderPage && String(m.builderPage).toLowerCase() === key) return m;
			}
			return null;
		},
		resolveFromDoctype(doctype) {
			if (!doctype) return null;
			for (const id of Object.keys(modules)) {
				const m = modules[id];
				if (m.formDoctype === doctype) return m;
			}
			return null;
		},
	};
})();
