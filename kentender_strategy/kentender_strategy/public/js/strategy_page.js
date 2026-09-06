// STR-CHG-001 v1.7 §10 — the one Strategy Alignment Desk Page. Every
// canonical route lives under it and the root Strategy.vue picks the screen
// from the route segments:
//   /app/strategy                                   STR-UI-01 Strategy Portfolio
//   /app/strategy/my-work · /app/strategy/new       Portfolio tab / new-plan draft
//   /app/strategy/plan/{plan_id}[/history]          STR-UI-02 Plan workspace
//   /app/strategy/plan/{plan_id}/version/{n}/structure  STR-UI-03 Structure editor
//   /app/strategy/approval/{plan_version_id}[/tab]  STR-UI-04 Approval task
kentender_core.desk_page.register("strategy", {
	title: __("Strategy Alignment"),
	bundles: ["kt_industry_page_rail.bundle.js", "strategy.bundle.js"],
	mount: (el) => frappe.kt_mount_strategy(el),
	sidebarWorkspaceKey: "procurement",
});
