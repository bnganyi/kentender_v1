// EVL-CHG-001 v0.4 §9.2, §10 / plan D13 — one Page ("bid-evaluation") for the
// Bid evaluation workspace. Every evaluation record lives under its Tender
// (/app/tenders/{ref}/evaluation…), mounted by the Tenders page. Not
// registered in cl_surface_registry (AGENTS.md §6.5).
kentender_core.desk_page.register("bid-evaluation", {
	title: __("Bid evaluation"),
	bundles: ["kt_industry_page_rail.bundle.js", "kt_industry_guidance.bundle.js", "bid_evaluation_workspace.bundle.js", "bid_evaluation_page.bundle.css"],
	mount: (el) => frappe.kt_mount_bid_evaluation_workspace(el),
	sidebarWorkspaceKey: "procurement",
});
