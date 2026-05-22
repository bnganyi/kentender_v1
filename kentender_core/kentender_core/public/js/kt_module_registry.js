// KenTender module registry — context-preserving navigation (see docs/prompts/strategy/1. ken_tender…)
frappe.provide("kentender_core.module_registry");

(function () {
	const modules = {
		strategy: {
			id: "strategy",
			workspaceRoute: ["Workspaces", "Strategy Management"],
			workspaceSlug: "strategy-management",
			workbenchLabel: __("Strategy Management"),
			backLabel: __("Back to Strategy Workbench"),
			sidebarWorkspaceKey: "strategy management",
			builderPage: "strategy-builder",
			formDoctype: "Strategic Plan",
			stateKey: "kt_strategy_workbench_state",
			selectKey: "kt_strategy_workspace_select",
			routePrefixes: ["strategy-builder", "Form/Strategic Plan"],
			taskLabels: {
				builder: __("Manage Structure"),
				form: __("Edit Plan"),
			},
		},
		budget: {
			id: "budget",
			workspaceRoute: ["Workspaces", "Budget Management"],
			workspaceSlug: "budget-management",
			workbenchLabel: __("Budget Management"),
			backLabel: __("Back to Budget Workbench"),
			sidebarWorkspaceKey: "budget management",
			builderPage: "budget-builder",
			formDoctype: "Budget",
			stateKey: "kt_budget_workbench_state",
			selectKey: "kt_budget_workspace_select",
			routePrefixes: ["budget-builder", "Form/Budget"],
			taskLabels: {
				builder: __("Manage Allocations"),
				form: __("Edit Budget"),
			},
		},
		dia: {
			id: "dia",
			workspaceRoute: ["Workspaces", "Demand Intake and Approval"],
			workspaceSlug: "demand-intake-and-approval",
			workbenchLabel: __("Demand Intake and Approval"),
			backLabel: __("Back to Demand Workbench"),
			sidebarWorkspaceKey: "demand intake and approval",
			formDoctype: "Demand",
			stateKey: "kt_dia_workbench_state",
			selectKey: "kt_dia_workspace_select",
			routePrefixes: ["Form/Demand"],
			taskLabels: {
				edit: __("Edit Demand"),
				review: __("Review Demand"),
			},
		},
		procurement_planning: {
			id: "procurement_planning",
			workspaceRoute: ["Workspaces", "Procurement Planning"],
			workbenchLabel: __("Procurement Planning"),
			backLabel: __("Back to Procurement Planning"),
			sidebarWorkspaceKey: "procurement planning",
			formDoctype: "Procurement Package",
			stateKey: "kt_pp_workbench_state",
			selectKey: "kt_pp_workspace_select",
			routePrefixes: ["Form/Procurement Package"],
			taskLabels: {
				form: __("Edit Package"),
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
