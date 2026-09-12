// AUTH-ADR-001 §10/§12 — the Technical record search page. Roles gate empty
// in the Page doctype (KT-STD-001 §3A.3); the screen resolves the technical
// verdict itself and shows the Forbidden state in place for anyone else.

/* global frappe */

kentender_core.desk_page.register("technical-search", {
	title: __("Technical record search"),
	bundles: ["technical_search.bundle.js"],
	mount: (el) => frappe.kt_mount_technical_search(el),
	sidebarWorkspaceKey: "procurement",
});
