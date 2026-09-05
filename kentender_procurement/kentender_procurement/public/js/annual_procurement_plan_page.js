// PLN-CHG-001 v1.2 §10 — Annual Procurement Plan routes, served by the same
// live Vue app as procurement-planning (one desk_page group).
kentender_core.desk_page.register("annual-procurement-plan", {
	title: __("Annual Procurement Plan"),
	group: "procurement-planning",
	pages: ["procurement-planning", "departmental-procurement-plan", "annual-procurement-plan", "procurement-plan-item"],
	bundles: ["kt_industry_page_rail.bundle.js", "procurement_planning.bundle.js"],
	mount: (el) => frappe.kt_mount_procurement_planning(el),
	sidebarWorkspaceKey: "procurement",
});
