// KenTender module registry — context-preserving navigation (see docs/prompts/strategy/1. ken_tender…)
frappe.provide("kentender_core.module_registry");

(function () {
	const modules = {
		strategy: {
			id: "strategy",
			workspaceRoute: ["strategy-alignment"],
			workspaceSlug: "strategy-alignment",
			workbenchLabel: __("Strategy Alignment"),
			backLabel: __("Back to Strategy Alignment"),
			sidebarWorkspaceKey: "procurement",
			builderPage: "strategy-plan-structure",
			formDoctype: "",
			stateKey: "kt_strategy_workbench_state",
			selectKey: "kt_strategy_workspace_select",
			routePrefixes: [
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
			],
			taskLabels: {
				builder: __("Manage Structure"),
				form: __("Edit Plan"),
			},
		},
		budget: {
			// MVP-1 Budget & Funding — keep in sync with module_registry.py + hooks.page_js.
			id: "budget",
			workspaceRoute: ["Workspaces", "Budget Management"],
			workspaceSlug: "budget-management",
			workbenchLabel: __("Budget & Funding"),
			backLabel: __("Back to Budget & Funding"),
			sidebarWorkspaceKey: "budget management",
			builderPage: "",
			deskPage: "budget-funding",
			formDoctype: "Budget",
			stateKey: "kt_budget_workbench_state",
			selectKey: "kt_budget_workspace_select",
			routePrefixes: [
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
			],
			taskLabels: {
				builder: __("Budget & Funding"),
				form: __("Register approved budget"),
			},
		},
		demands: {
			// MVP-1 Demands — keep in sync with module_registry.py; pages land in Wave 4.
			id: "demands",
			workspaceRoute: ["demands-workspace"],
			workspaceSlug: "demands-workspace",
			workbenchLabel: __("Demands"),
			backLabel: __("Back to Demands"),
			sidebarWorkspaceKey: "procurement",
			builderPage: "",
			deskPage: "demands-workspace",
			formDoctype: "Demand",
			stateKey: "kt_demands_workbench_state",
			selectKey: "kt_demands_workspace_select",
			routePrefixes: [
				"demands-workspace",
				"demand-form",
				"demand-review",
				"demand-detail",
				"demand-performance",
				"Form/Demand",
			],
			taskLabels: {
				form: __("Edit Demand"),
			},
		},
		procurement_planning: {
			id: "procurement_planning",
			workspaceRoute: ["Workspaces", "Procurement Planning"],
			workbenchLabel: __("Procurement Planning"),
			backLabel: __("Back to Procurement Planning"),
			sidebarWorkspaceKey: "procurement planning",
			formDoctype: "Procurement Plan",
			stateKey: "kt_pp_workbench_state",
			selectKey: "kt_pp_workspace_select",
			routePrefixes: ["Form/Procurement Plan"],
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
