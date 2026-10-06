// OVS-CHG-001 v0.6 §11 / PRC-CHG-001 v0.11 §9 — one Page ("procurement-meetings") for the
// read-only Procurement meetings register. It adds no scheduling, agenda or meeting
// administration: every meeting's record stays on its own Tender
// (/app/tenders/{ref}/opening, /app/tenders/{ref}/evaluation). Not registered in
// cl_surface_registry (AGENTS.md §6.5).
kentender_core.desk_page.register("procurement-meetings", {
	title: __("Procurement meetings"),
	bundles: ["kt_industry_page_rail.bundle.js", "kt_industry_guidance.bundle.js", "kt_industry_pager.bundle.js", "procurement_meetings.bundle.js", "procurement_meetings_page.bundle.css"],
	mount: (el) => frappe.kt_mount_procurement_meetings(el),
	sidebarWorkspaceKey: "procurement",
});
