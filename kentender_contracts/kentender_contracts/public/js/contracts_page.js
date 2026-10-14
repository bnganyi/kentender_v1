// CM-CHG-001 v0.8 §9.0 / plan Phase 3 — one Page ("contracts") for the Contracts workspace (/app/contracts) and, from Phase 4, every contract
// (/app/contracts/{contract}). The app stays mounted across them (AGENTS.md §6.1). Not registered in cl_surface_registry (AGENTS.md §6.5).
// The rail is Contract Management's own Workspace Sidebar ("Contracts"): this app does not edit the shared Procurement sidebar (follow-up FU-CM-58).
kentender_core.desk_page.register("contracts", {
	title: __("Contracts"),
	bundles: ["kt_industry_page_rail.bundle.js", "contracts.bundle.js"],
	mount: (el) => frappe.kt_mount_contracts(el),
	sidebarWorkspaceKey: "contracts",
});
