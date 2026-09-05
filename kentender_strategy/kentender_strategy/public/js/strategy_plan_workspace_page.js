// STR-CHG-001 v1.3 Phase 7 — STR-UI-03 Plan Workspace.
kentender_core.desk_page.register("strategy-plan-workspace", {
	title: __("Plan Workspace"),
	bundles: ["kt_industry_page_rail.bundle.js", "strategy_plan_workspace.bundle.js"],
	mount: (el) => frappe.kt_mount_strategy_plan_workspace(el),
	sidebarWorkspaceKey: "procurement",
});
