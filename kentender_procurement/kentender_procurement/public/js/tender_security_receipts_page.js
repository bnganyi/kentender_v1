// BDS-CHG-001 v0.8 owner decisions OD-G/OD-H — one Page
// ("tender-security-receipts") for the Head of Procurement Function's blind
// physical tender-security intake. Access is decided on the server for every
// read (inline Forbidden state); the page CSS loads here, never globally
// (AGENTS.md §6.9). Not registered in cl_surface_registry (AGENTS.md §6.5).
kentender_core.desk_page.register("tender-security-receipts", {
	title: __("Tender-security receipts"),
	bundles: ["kt_industry_page_rail.bundle.js", "kt_industry_pager.bundle.js", "tender_security_receipts.bundle.js", "tender_security_receipts.bundle.css"],
	mount: (el) => frappe.kt_mount_tender_security_receipts(el),
	sidebarWorkspaceKey: "procurement",
});
