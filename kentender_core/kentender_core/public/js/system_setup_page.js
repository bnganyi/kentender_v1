// CFG-CHG-002 v0.6 §9 / AUTH-ADR-001 v1.6 §12 — the one System setup page.

/* global frappe */

kentender_core.desk_page.register("system-setup", {
	title: __("System setup"),
	bundles: ["system_setup.bundle.js"],
	mount: (el) => frappe.kt_mount_system_setup(el),
	sidebarWorkspaceKey: "procurement",
});
