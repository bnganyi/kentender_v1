// AWD-CHG-001 v0.4 §9 / plan D13 — one Page ("award") for the Award workspace
// (/app/award) and every award record (/app/award/{award_id}). The app stays
// mounted across both (AGENTS.md §6.1). Not registered in cl_surface_registry
// (AGENTS.md §6.5).
kentender_core.desk_page.register("award", {
	title: __("Award"),
	bundles: ["kt_industry_page_rail.bundle.js", "kt_industry_guidance.bundle.js", "award.bundle.js", "award_page.bundle.css"],
	mount: (el) => frappe.kt_mount_award(el),
	sidebarWorkspaceKey: "procurement",
});
