// REQ-CHG-001 v1.6 §12 — one Page ("procurement-requisitions") owning the
// /app/procurement-requisitions prefix; every §12 route (workspace, Start,
// editor, department task, procurement task, authorised view) is a path
// segment under it, exactly like Strategy's single-page model — not a
// multi-Page group like Procurement Planning's four routes.
kentender_core.desk_page.register("procurement-requisitions", {
	title: __("Procurement Requisitions"),
	bundles: ["kt_industry_page_rail.bundle.js", "procurement_requisitions.bundle.js"],
	mount: (el) => frappe.kt_mount_procurement_requisitions(el),
	sidebarWorkspaceKey: "procurement",
});
