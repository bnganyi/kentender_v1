// PLN-CHG-001 v1.2 §10 — the Procurement Planning workspace and its task deep
// links, one Page ("procurement-planning") owning the /app/procurement-planning
// prefix; ProcurementPlanning.vue branches on route segments.
//
// Slug safety (decision D2): no readable DocType scrubs to
// "procurement-planning" (the v1.2 model deliberately names none that way),
// and the old public Workspace of that name was retired by
// pln_chg_001_v12_retire_planning_workspace — frappe's client router would
// otherwise resolve the bare route to the Workspace, as it did live on
// 2026-08-30 (Phase 0, PLN-006).
//
// The four Planning pages share one bundle and one live Vue app (the
// "procurement-planning" desk_page group): hopping between them moves the
// mounted app, never rebuilds it.
kentender_core.desk_page.register("procurement-planning", {
	title: __("Procurement Planning"),
	group: "procurement-planning",
	pages: ["procurement-planning", "departmental-procurement-plan", "annual-procurement-plan", "procurement-plan-item"],
	bundles: ["kt_industry_page_rail.bundle.js", "procurement_planning.bundle.js"],
	mount: (el) => frappe.kt_mount_procurement_planning(el),
	sidebarWorkspaceKey: "procurement",
});
