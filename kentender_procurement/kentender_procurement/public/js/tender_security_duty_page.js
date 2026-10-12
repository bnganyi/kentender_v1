// One Page ("tender-security-duty") for the Head of Procurement Function's
// assignment of the tender-security intake duty (Project Owner, 10 October
// 2026). Access is decided on the server for every read (inline Forbidden
// state); the page CSS loads here, never globally (AGENTS.md §6.9). Not
// registered in cl_surface_registry (AGENTS.md §6.5).
kentender_core.desk_page.register("tender-security-duty", {
	title: __("Tender-security intake duty"),
	bundles: ["kt_industry_page_rail.bundle.js", "tender_security_duty.bundle.js", "tender_security_receipts.bundle.css"],
	mount: (el) => frappe.kt_mount_tender_security_duty(el),
	sidebarWorkspaceKey: "procurement",
});
