// NDS-CHG-001 v1.1 §10 — NDS-UI-01…08, all under one Page
// ("departmental-needs") sharing the /app/departmental-needs URL prefix; the
// root DepartmentalNeeds.vue branches on route segments to pick the screen.
//
// The slug is safe from Frappe's doctype-route collision: frappe's client
// router registers every readable doctype's own slug into `this.routes` and
// resolves a bare /app/<slug> against that map before falling back to a
// same-named Page. The doctype here is "Departmental Need", whose slug is
// "departmental-need" (singular) — "departmental-needs" is unclaimed, which is
// why §10 can specify it.
kentender_core.desk_page.register("departmental-needs", {
	title: __("Departmental Needs"),
	bundles: ["kt_industry_page_rail.bundle.js", "departmental_needs.bundle.js"],
	mount: (el) => frappe.kt_mount_departmental_needs(el),
	sidebarWorkspaceKey: "procurement",
});
