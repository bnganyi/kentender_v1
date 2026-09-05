// STR-CHG-001 v1.3 Phase 7 — STR-UI-05 Review Task.
kentender_core.desk_page.register("strategy-review-task", {
	title: __("Review Task"),
	bundles: ["kt_industry_page_rail.bundle.js", "strategy_review_task.bundle.js"],
	mount: (el) => frappe.kt_mount_strategy_review_task(el),
	sidebarWorkspaceKey: "procurement",
});
