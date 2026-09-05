// STR-CHG-001 v1.3 Phase 7 — STR-UI-01 Strategy Portfolio.
kentender_core.desk_page.register("strategy-portfolio", {
	title: __("Strategy Portfolio"),
	bundles: ["kt_industry_page_rail.bundle.js", "strategy_portfolio.bundle.js"],
	mount: (el) => frappe.kt_mount_strategy_portfolio(el),
	sidebarWorkspaceKey: "procurement",
});
